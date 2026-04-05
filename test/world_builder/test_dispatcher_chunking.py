"""
Tier 2: dispatcher seed partitioning (moto S3/SQS) + pure chunk arithmetic.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

REPO_ROOT = Path(__file__).resolve().parents[2]
DISPATCHER_HANDLER = (
    REPO_ROOT
    / "infra/world_builder/terraform_event_pipeline/dispatcher_lambda/handler.py"
)


def _load_dispatcher_module():
    """Load dispatcher handler.py from infra (not installed as a package)."""
    spec = importlib.util.spec_from_file_location(
        "dispatcher_handler",
        DISPATCHER_HANDLER,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["dispatcher_handler"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def dispatcher():
    assert DISPATCHER_HANDLER.is_file(), f"missing {DISPATCHER_HANDLER}"
    return _load_dispatcher_module()


def test_chunk_job_bodies_one_million_over_25k(dispatcher) -> None:
    bodies = dispatcher.chunk_job_bodies(
        config_bucket="cfg-bucket",
        config_key="configs/job.json",
        total=1_000_000,
        seeds_per_chunk=25_000,
        worldgen_mode="population",
    )
    assert len(bodies) == 40
    assert bodies[0]["seed_start"] == 0 and bodies[0]["seed_end"] == 24_999
    assert bodies[0]["chunk_index"] == 0 and bodies[0]["total_chunks"] == 40
    assert bodies[-1]["seed_start"] == 975_000
    assert bodies[-1]["seed_end"] == 999_999
    assert bodies[-1]["chunk_index"] == 39
    for b in bodies:
        assert b["config_bucket"] == "cfg-bucket"
        assert b["config_key"] == "configs/job.json"
        assert b["worldgen_mode"] == "population"
        span = b["seed_end"] - b["seed_start"] + 1
        assert 1 <= span <= 25_000


def test_chunk_job_bodies_25001_splits_last_chunk_small(dispatcher) -> None:
    bodies = dispatcher.chunk_job_bodies(
        config_bucket="b",
        config_key="k.json",
        total=25_001,
        seeds_per_chunk=25_000,
        worldgen_mode="ecosystem",
    )
    assert len(bodies) == 2
    assert bodies[0]["seed_end"] == 24_999
    assert bodies[1]["seed_start"] == 25_000
    assert bodies[1]["seed_end"] == 25_000


def test_chunk_job_bodies_single_entity(dispatcher) -> None:
    bodies = dispatcher.chunk_job_bodies(
        config_bucket="b",
        config_key="k.json",
        total=1,
        seeds_per_chunk=25_000,
        worldgen_mode="population",
    )
    assert len(bodies) == 1
    assert bodies[0]["seed_start"] == 0 and bodies[0]["seed_end"] == 0


@mock_aws
def test_handler_sends_correct_batches_to_sqs(dispatcher, monkeypatch) -> None:
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    region = "us-east-1"
    bucket = "test-config-bucket"
    key = "configs/wb.json"
    cfg = {"entity_count": 25, "worldgen_mode": "population"}

    conn = boto3.client("s3", region_name=region)
    conn.create_bucket(Bucket=bucket)
    conn.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(cfg).encode("utf-8"),
    )

    sqs = boto3.client("sqs", region_name=region)
    qurl = sqs.create_queue(QueueName="job-q")["QueueUrl"]

    monkeypatch.setenv("JOB_QUEUE_URL", qurl)
    monkeypatch.setenv("SEEDS_PER_CHUNK", "10")
    monkeypatch.setenv("DEFAULT_ENTITY_COUNT", "100")
    monkeypatch.setenv("DEFAULT_WORLDGEN_MODE", "population")

    s3_inner = {"Records": [{"s3": {"bucket": {"name": bucket}, "object": {"key": key}}}]}
    event = {"Records": [{"Sns": {"Message": json.dumps(s3_inner)}}]}

    dispatcher.handler(event, None)

    bodies: list[dict] = []
    while True:
        resp = sqs.receive_message(
            QueueUrl=qurl,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=0,
        )
        msgs = resp.get("Messages") or []
        if not msgs:
            break
        for m in msgs:
            bodies.append(json.loads(m["Body"]))
            sqs.delete_message(QueueUrl=qurl, ReceiptHandle=m["ReceiptHandle"])

    assert len(bodies) == 3
    assert bodies[0]["seed_start"] == 0 and bodies[0]["seed_end"] == 9
    assert bodies[1]["seed_start"] == 10 and bodies[1]["seed_end"] == 19
    assert bodies[2]["seed_start"] == 20 and bodies[2]["seed_end"] == 24
    assert bodies[2]["total_chunks"] == 3
