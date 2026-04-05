"""
Tier 3: SNS -> SQS wiring against LocalStack (optional).

Set LOCALSTACK_ENDPOINT (e.g. http://localhost:4566) and run docker-compose.localstack.yml.
"""

from __future__ import annotations

import json
import os
import uuid

import boto3
import pytest

pytestmark = pytest.mark.integration


def _endpoint() -> str | None:
    raw = os.environ.get("LOCALSTACK_ENDPOINT", "").strip()
    return raw or None


def _client(service: str):
    ep = _endpoint()
    if not ep:
        pytest.skip("Set LOCALSTACK_ENDPOINT (e.g. http://localhost:4566)")
    return boto3.client(
        service,
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        endpoint_url=ep,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    )


def test_sns_to_sqs_subscription_delivers_message() -> None:
    sns = _client("sns")
    sqs = _client("sqs")

    suffix = uuid.uuid4().hex[:8]
    topic_arn = sns.create_topic(Name=f"tier3-topic-{suffix}")["TopicArn"]
    qurl = sqs.create_queue(QueueName=f"tier3-queue-{suffix}")["QueueUrl"]
    qattrs = sqs.get_queue_attributes(QueueUrl=qurl, AttributeNames=["QueueArn"])
    qarn = qattrs["Attributes"]["QueueArn"]

    sns.subscribe(
        TopicArn=topic_arn,
        Protocol="sqs",
        Endpoint=qarn,
    )

    body = {"hello": "localstack"}
    sns.publish(TopicArn=topic_arn, Message=json.dumps(body))

    messages = []
    for _ in range(50):
        resp = sqs.receive_message(
            QueueUrl=qurl,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=1,
        )
        found = resp.get("Messages") or []
        if found:
            messages.extend(found)
            break

    assert len(messages) >= 1
    raw = json.loads(messages[0]["Body"])
    # SNS->SQS envelope wraps the published string in "Message"
    inner = raw.get("Message") or raw
    if isinstance(inner, str):
        inner = json.loads(inner)
    assert inner == body
