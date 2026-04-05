"""
Render the serverless world-builder pipeline using the diagrams library.

Requires:
  - Graphviz (`dot` on PATH)
  - pip install diagrams

Example:
  python architecture_event_driven_s3_sns_sqs_fanout.py
"""

from __future__ import annotations

from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import SNS, SQS
from diagrams.aws.storage import S3


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    base = str(out_dir / "architecture_serverless_pipeline")

    with Diagram(
        "World Builder Serverless Pipeline",
        filename=base,
        show=False,
        direction="LR",
        outformat="png",
    ):
        with Cluster("Ingest"):
            config_bucket = S3("Config bucket\n(JSON)")

        topic = SNS("SNS topic\n(config object events)")

        dispatcher = Lambda(
            "Dispatcher Lambda\n(seed partitioning)"
        )

        with Cluster("Chunked jobs"):
            job_queue = SQS("SQS queue\n(chunked seed-range jobs)")

        worker = Lambda("Worker Lambda\n(synthetic generator\ncontainer)")

        with Cluster("Outputs"):
            out_bucket = S3("Output bucket\n(Parquet chunks)")

        config_bucket >> Edge(label="S3 Event Notification") >> topic
        topic >> Edge(label="subscription") >> dispatcher
        config_bucket >> Edge(label="GetObject", style="dashed") >> dispatcher
        dispatcher >> Edge(
            label="SendMessage batch\n(fan-out: N chunks)",
            color="darkgreen",
        ) >> job_queue
        job_queue >> Edge(label="event source mapping") >> worker
        config_bucket >> Edge(label="GetObject", style="dashed") >> worker
        worker >> Edge(label="PutObject") >> out_bucket


if __name__ == "__main__":
    main()
