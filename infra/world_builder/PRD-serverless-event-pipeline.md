# PRD: Serverless World Builder Event Pipeline

## Summary

When a JSON configuration object lands in the **config** S3 bucket, S3 notifies an **SNS** topic. A **dispatcher Lambda** (Python 3.12, zip) reads the config from S3, reads the total entity count, partitions work into **seed ranges**, and enqueues **N** JSON messages on the **synthetic-generator-job** SQS queue (`N = ceil(total_count / seeds_per_chunk)`). **Worker Lambda** invocations (container image) consume those messages, each generating only rows for its inclusive global seed range `[seed_start, seed_end]`, and write **one Parquet file per chunk** to the **synthetic-records** bucket.

## Goals

- **Parallel serverless workers**: Many worker invocations run concurrently (bounded by Lambda concurrency and SQS polling), each processing a bounded chunk of seeds.
- **Deterministic seeds**: Global seed index `i` uses `random.seed(i)` before entity creation so chunks are reproducible and disjoint.
- **Dispatcher as control plane**: SNS does not write to SQS directly; the dispatcher owns fan-out and chunk sizing.
- **Worker container**: Same application dependencies as batch jobs; handler `world_builder.lambda_synthetic_worker.lambda_handler` (see `Dockerfile.synthetic_generator_lambda`).

## Non-goals (initial release)

- Merging Parquet chunks into a single file (downstream can union externally).
- Replacing the existing EC2 Terraform stack entirely.
- Step Functions orchestration beyond SNS + Lambda + SQS.

## Personas

- **Data engineer**: Uploads configs (optionally with `entity_count` in JSON) and expects Parquet chunks under a stable prefix.
- **Platform owner**: Owns Terraform, `seeds_per_chunk`, and Lambda limits.
- **Downstream consumer**: Reads many Parquet objects keyed by config stem and `chunk_XXXX`.

## User-facing flow

1. Client uploads `s3://config-bucket/<prefix>/<name>.json`.
2. S3 publishes `ObjectCreated` to the SNS topic.
3. SNS invokes the **dispatcher Lambda** (not SQS).
4. Dispatcher downloads the JSON, determines `total_count` (see below), computes chunks, sends `send_message_batch` to the job queue (10 messages per API call).
5. Worker Lambdas pull messages; each runs `run_batch_for_seed_range` and uploads  
   `{OUTPUT_KEY_PREFIX}/{config_stem}/chunk_{chunk_index:04d}.parquet`.
6. Failures retry via SQS visibility; poison messages go to the DLQ. Workers use **partial batch response** (`ReportBatchItemFailures`) where applicable.

## Seed partitioning

- **`seeds_per_chunk`** (Terraform variable, default **25000**): maximum number of global seed indices per worker message.
- **Chunk count**: `total_chunks = ceil(total_count / seeds_per_chunk)`.
- **Ranges**: Chunk `k` (0-based) covers  
  `seed_start = k * seeds_per_chunk`,  
  `seed_end = min(total_count - 1, seed_start + seeds_per_chunk - 1)`  
  (both **inclusive**). Example: `total_count = 1_000_000`, `seeds_per_chunk = 25_000` yields **40** chunks; first chunk `[0, 24999]`.
- **Parallelism**: Up to `total_chunks` concurrent worker executions (subject to account concurrency, reserved concurrency, and SQS/Lambda scaling).

## Total entity count (dispatcher)

The dispatcher loads the config as JSON and resolves `total_count` in order:

1. First defined among top-level keys: `entity_count`, `ENTITY_COUNT`, `entityCount`.
2. Else **`DEFAULT_ENTITY_COUNT`** from the dispatcher environment (Terraform `default_entity_count`, default 100).

`worldgen_mode` for each SQS message is taken from top-level `worldgen_mode` or `WORLDGEN_MODE` in JSON, else dispatcher env **`DEFAULT_WORLDGEN_MODE`**.

## Message contract: dispatcher → worker (SQS body)

JSON object:

```json
{
  "config_bucket": "<string>",
  "config_key": "<string>",
  "seed_start": 0,
  "seed_end": 24999,
  "chunk_index": 0,
  "total_chunks": 40,
  "worldgen_mode": "population"
}
```

- **`worldgen_mode`**: `"population"` or `"ecosystem"` (worker falls back to `WORLDGEN_MODE` env if omitted).

## Output object naming

Worker writes:

`{OUTPUT_KEY_PREFIX}/{config_stem}/chunk_{chunk_index:04d}.parquet`

- **`config_stem`**: basename of `config_key` without extension (e.g. `job42` from `configs/job42.json`).
- **`OUTPUT_KEY_PREFIX`**: worker Lambda environment (Terraform `output_object_prefix`, default `outputs/`).

## Functional requirements

| ID | Requirement |
|----|-------------|
| FR-1 | Config and output buckets use **SSE-S3** (default encryption). |
| FR-2 | S3 publishes **`s3:ObjectCreated:*`** to SNS (prefix/suffix filters supported). |
| FR-3 | SNS subscribes the **dispatcher Lambda** (`protocol = lambda`), not SQS directly. |
| FR-4 | Dispatcher reads config from S3 and enqueues chunked jobs via **`sqs:SendMessage` / `send_message_batch`** (batch size 10). |
| FR-5 | Job SQS queue has a **DLQ**; no queue policy granting SNS `SendMessage` (only the dispatcher IAM role sends to the queue). |
| FR-6 | Worker uses a **container image** with RIC (see `Dockerfile.synthetic_generator_lambda`); handler processes SQS records and calls `run_batch_for_seed_range`. |
| FR-7 | Worker event source mapping uses **`ReportBatchItemFailures`**. |
| FR-8 | Structured logging: dispatcher logs `num_chunks`; workers log chunk index and output key. |

## Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | **Least privilege**: Dispatcher — S3 GetObject on config prefix, SQS SendMessage (+ GetQueueAttributes) on job queue, logs. Worker — SQS receive/delete, S3 Get/Put on config and output prefixes, ECR pull for image, logs. |
| NFR-2 | **Worker sizing**: Timeout/memory must cover worst-case chunk (`seeds_per_chunk` rows); multiprocessing Pool is used per invocation. |
| NFR-3 | **Cost (order-of-magnitude)**: Ballpark **~USD 0.22 per 1 million seeds** on **arm64** at **3,008 MB** / **~2 vCPU** worker configuration (Lambda GB-seconds dominated; validate in your account). Add S3 requests, SQS, and dispatcher cost (small vs workers at scale). |
| NFR-4 | **Reliability**: DLQ and optional alarms on depth. |

## S3 event types

For new config objects, use **`s3:ObjectCreated:*`** with optional prefix/suffix filters (see earlier PRD revision for event subtype table).

## Dependencies

- `terraform_event_pipeline/` — S3, SNS, SQS + DLQ, dispatcher Lambda (zip), worker Lambda (image), IAM, CloudWatch.
- ECR (or registry) for **worker** image built from `Dockerfile.synthetic_generator_lambda`.
- `world_builder.batch_s3.run_batch_for_seed_range`, `world_builder.lambda_synthetic_worker.lambda_handler`.

## Risks

- **Very large `total_chunks`**: Dispatcher runtime grows with number of `send_message_batch` calls; tune `dispatcher_lambda_timeout` or `seeds_per_chunk`.
- **SNS retries**: Duplicate dispatcher runs can enqueue duplicate chunk work (idempotency: overwrite same Parquet key or add deduplication later).
- **Config JSON**: Extra keys must not break Pydantic load on workers (unknown keys ignored by default).

## Success criteria

- Upload one config with `entity_count` set → expected number of Parquet objects under `{prefix}/{stem}/chunk_*.parquet`.
- DLQ remains empty for valid configs.

## Diagram

Generated asset: `docs/architecture_serverless_pipeline.png` (run `python docs/architecture_event_driven_s3_sns_sqs_fanout.py`).
