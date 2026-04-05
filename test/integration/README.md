# Integration tests (Tier 3: LocalStack)

## Quick wiring check

1. Start LocalStack:

   ```bash
   docker compose -f docker-compose.localstack.yml up -d
   ```

2. Point boto3 at the emulator (credentials are dummy values LocalStack accepts):

   ```bash
   export AWS_ACCESS_KEY_ID=test
   export AWS_SECRET_ACCESS_KEY=test
   export AWS_DEFAULT_REGION=us-east-1
   export LOCALSTACK_ENDPOINT=http://localhost:4566
   ```

3. Run integration tests:

   ```bash
   pytest test/integration/test_localstack_sns_sqs.py -v
   ```

If `LOCALSTACK_ENDPOINT` is unset, those tests skip so default `pytest test/` stays local-only (Tier 1 and Tier 2 use moto).

## Full pipeline (Lambdas)

End-to-end S3 upload to SNS to dispatcher zip-Lambda to SQS to container worker-Lambda is **not** fully automated here: LocalStack Lambda behavior (especially **container images**) differs by edition and is often flaky. Use AWS for that validation, or extend this folder with `awslocal` scripts once your team settles on a LocalStack Pro feature set.

Tier 1 (`run_seed_range_to_local_parquet` / `batch_local --seed-start/--seed-end`) plus Tier 2 (moto + `handler`) cover generation and partitioning; Tier 3 confirms SNS/SQS connectivity against a local endpoint.
