variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Short name for resource tagging and naming"
  type        = string
  default     = "world-builder"
}

variable "environment" {
  description = "Environment name (e.g. dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "lambda_image_uri" {
  description = "ECR image URI for the Lambda container (must implement the Lambda Runtime Interface Client)"
  type        = string
}

variable "ecr_repository_arn" {
  description = "ARN of the ECR repository that holds lambda_image_uri (for Lambda pull permissions)"
  type        = string
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds (max 900)"
  type        = number
  default     = 900
}

variable "lambda_memory_size" {
  description = "Lambda memory in MB"
  type        = number
  default     = 3008
}

variable "lambda_architectures" {
  description = "Instruction set architecture for the container image (must match the image)"
  type        = list(string)
  default     = ["x86_64"]
}

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrent executions for this function; null leaves the function in the account-wide unreserved pool"
  type        = number
  default     = null
  nullable    = true
}

variable "config_object_prefix" {
  description = "S3 key prefix for config uploads that trigger notifications (empty = entire bucket)"
  type        = string
  default     = "configs/"
}

variable "config_object_suffix" {
  description = "S3 key suffix filter for notifications (empty = any suffix)"
  type        = string
  default     = ".json"
}

variable "output_object_prefix" {
  description = "Default key prefix for generated Parquet objects (passed to Lambda as OUTPUT_KEY_PREFIX)"
  type        = string
  default     = "outputs/"
}

variable "default_worldgen_mode" {
  description = "Default WORLDGEN_MODE env var on Lambda (ecosystem or population)"
  type        = string
  default     = "population"
}

variable "default_entity_count" {
  description = "Default ENTITY_COUNT env var on Lambda"
  type        = number
  default     = 100
}

variable "sqs_batch_size" {
  description = "Max SQS messages per Lambda invocation"
  type        = number
  default     = 1
}

variable "sqs_maximum_batching_window_seconds" {
  description = "Maximum batching window in seconds for the Lambda event source mapping"
  type        = number
  default     = 0
}

variable "sqs_max_receive_count" {
  description = "Receive attempts before a message goes to the DLQ"
  type        = number
  default     = 5
}

variable "log_retention_days" {
  description = "CloudWatch log retention for the Lambda log group"
  type        = number
  default     = 14
}

variable "seeds_per_chunk" {
  description = "Number of global seed indices per worker invocation; dispatcher uses ceil(total_count / seeds_per_chunk) messages"
  type        = number
  default     = 25000
}

variable "dispatcher_lambda_timeout" {
  description = "Dispatcher Lambda timeout in seconds (S3 read + many SQS SendMessage batches)"
  type        = number
  default     = 300
}

variable "dispatcher_lambda_memory_size" {
  description = "Dispatcher Lambda memory in MB"
  type        = number
  default     = 256
}
