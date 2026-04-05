output "worldgen_config_bucket_id" {
  description = "Name of the config S3 bucket (JSON configs; includes unique suffix)"
  value       = aws_s3_bucket.config.id
}

output "worldgen_config_bucket_arn" {
  description = "ARN of the config S3 bucket"
  value       = aws_s3_bucket.config.arn
}

output "worldgen_synthetic_records_bucket_id" {
  description = "Name of the synthetic-records S3 bucket (Parquet; includes unique suffix)"
  value       = aws_s3_bucket.synthetic_records.id
}

output "worldgen_synthetic_records_bucket_arn" {
  description = "ARN of the synthetic-records S3 bucket"
  value       = aws_s3_bucket.synthetic_records.arn
}

output "worldgen_config_events_topic_arn" {
  description = "SNS topic (<project>-<env>-config-events) for S3 ObjectCreated notifications from the config bucket"
  value       = aws_sns_topic.config_events.arn
}

output "synthetic_generator_dispatcher_lambda_arn" {
  description = "Dispatcher Lambda ARN (SNS subscription target; enqueues chunked SQS jobs)"
  value       = aws_lambda_function.dispatcher_lambda.arn
}

output "synthetic_generator_dispatcher_lambda_name" {
  description = "Dispatcher Lambda function name"
  value       = aws_lambda_function.dispatcher_lambda.function_name
}

output "worldgen_synthetic_generator_job_queue_arn" {
  description = "SQS synthetic-generator-job queue consumed by the synthetic generator Lambda"
  value       = aws_sqs_queue.synthetic_generator_job.arn
}

output "worldgen_synthetic_generator_job_queue_url" {
  description = "URL of the synthetic-generator-job SQS queue"
  value       = aws_sqs_queue.synthetic_generator_job.url
}

output "worldgen_synthetic_generator_job_dlq_arn" {
  description = "Dead-letter queue for synthetic-generator-job"
  value       = aws_sqs_queue.synthetic_generator_job_dlq.arn
}

output "worldgen_synthetic_generator_lambda_function_arn" {
  description = "ARN of the <project>-<env>-synthetic-generator Lambda function"
  value       = aws_lambda_function.synthetic_generator.arn
}

output "worldgen_synthetic_generator_lambda_function_name" {
  description = "Name of the <project>-<env>-synthetic-generator Lambda function"
  value       = aws_lambda_function.synthetic_generator.function_name
}

output "worldgen_synthetic_generator_lambda_role_arn" {
  description = "IAM role assumed by the synthetic-generator Lambda"
  value       = aws_iam_role.synthetic_generator.arn
}
