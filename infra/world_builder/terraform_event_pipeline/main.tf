locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "event-pipeline"
  }

  synthetic_generator_function_name = "${local.name_prefix}-synthetic-generator"
  dispatcher_function_name          = "${local.name_prefix}-synthetic-generator-dispatcher"

  # AWS recommends visibility timeout >= 6 * Lambda timeout + batching window.
  sqs_visibility_timeout = max(
    30,
    var.lambda_timeout * 6 + var.sqs_maximum_batching_window_seconds
  )

  config_objects_arn = var.config_object_prefix == "" ? "${aws_s3_bucket.config.arn}/*" : "${aws_s3_bucket.config.arn}/${trimsuffix(var.config_object_prefix, "/")}/*"

  synthetic_records_objects_arn = var.output_object_prefix == "" ? "${aws_s3_bucket.synthetic_records.arn}/*" : "${aws_s3_bucket.synthetic_records.arn}/${trimsuffix(var.output_object_prefix, "/")}/*"
}

# ---------------------------------------------------------------------------
# S3 buckets
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "config" {
  bucket_prefix = "${local.name_prefix}-config-"
  force_destroy = true
  tags          = merge(local.common_tags, { Name = "config" })
}

resource "aws_s3_bucket" "synthetic_records" {
  bucket_prefix = "${local.name_prefix}-synthetic-records-"
  force_destroy = true
  tags          = merge(local.common_tags, { Name = "synthetic-records" })
}

resource "aws_s3_bucket_public_access_block" "config" {
  bucket                  = aws_s3_bucket.config.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "synthetic_records" {
  bucket                  = aws_s3_bucket.synthetic_records.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "config" {
  bucket = aws_s3_bucket.config.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_ownership_controls" "synthetic_records" {
  bucket = aws_s3_bucket.synthetic_records.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "config" {
  bucket = aws_s3_bucket.config.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "synthetic_records" {
  bucket = aws_s3_bucket.synthetic_records.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ---------------------------------------------------------------------------
# SNS (config object events)
# ---------------------------------------------------------------------------

resource "aws_sns_topic" "config_events" {
  name         = "${local.name_prefix}-config-events"
  display_name = "Config bucket object events"
  tags         = merge(local.common_tags, { Name = "config-events" })
}

data "aws_iam_policy_document" "sns_config_bucket_publish" {
  statement {
    sid    = "AllowConfigBucketPublish"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.config_events.arn]
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.config.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "config_events" {
  arn    = aws_sns_topic.config_events.arn
  policy = data.aws_iam_policy_document.sns_config_bucket_publish.json
}

resource "aws_s3_bucket_notification" "config_to_sns" {
  bucket = aws_s3_bucket.config.id

  topic {
    topic_arn     = aws_sns_topic.config_events.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = var.config_object_prefix != "" ? var.config_object_prefix : null
    filter_suffix = var.config_object_suffix != "" ? var.config_object_suffix : null
  }

  depends_on = [aws_sns_topic_policy.config_events]
}

# ---------------------------------------------------------------------------
# SQS (synthetic generator job queue + DLQ)
# ---------------------------------------------------------------------------

resource "aws_sqs_queue" "synthetic_generator_job_dlq" {
  name                      = "${local.name_prefix}-synthetic-generator-job-dlq"
  message_retention_seconds = 1209600
  tags                      = merge(local.common_tags, { Name = "synthetic-generator-job-dlq" })
}

resource "aws_sqs_queue" "synthetic_generator_job" {
  name                       = "${local.name_prefix}-synthetic-generator-job"
  visibility_timeout_seconds = local.sqs_visibility_timeout
  receive_wait_time_seconds  = 20
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.synthetic_generator_job_dlq.arn
    maxReceiveCount     = var.sqs_max_receive_count
  })
  tags = merge(local.common_tags, { Name = "synthetic-generator-job" })
}

# ---------------------------------------------------------------------------
# Dispatcher Lambda (zip): SNS -> read config -> chunked SQS messages
# ---------------------------------------------------------------------------

data "archive_file" "dispatcher_zip" {
  type        = "zip"
  source_dir  = "${path.module}/dispatcher_lambda"
  output_path = "${path.module}/.terraform/dispatcher_lambda.zip"
}

resource "aws_cloudwatch_log_group" "dispatcher_logs" {
  name              = "/aws/lambda/${local.dispatcher_function_name}"
  retention_in_days = var.log_retention_days
  tags              = merge(local.common_tags, { Name = "synthetic-generator-dispatcher" })
}

data "aws_iam_policy_document" "dispatcher_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "dispatcher_role" {
  name               = "${local.name_prefix}-synthetic-generator-dispatcher"
  assume_role_policy = data.aws_iam_policy_document.dispatcher_assume_role.json
  tags               = merge(local.common_tags, { Name = "synthetic-generator-dispatcher" })
}

data "aws_iam_policy_document" "dispatcher_inline_policy" {
  statement {
    sid    = "DispatcherLambdaLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.dispatcher_logs.arn}:*"]
  }

  statement {
    sid       = "DispatcherS3ConfigRead"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:GetObjectVersion"]
    resources = [local.config_objects_arn]
  }

  statement {
    sid    = "DispatcherSqsSend"
    effect = "Allow"
    actions = [
      "sqs:SendMessage",
      "sqs:GetQueueAttributes",
    ]
    resources = [aws_sqs_queue.synthetic_generator_job.arn]
  }
}

resource "aws_iam_role_policy" "dispatcher_inline" {
  name   = "synthetic-generator-dispatcher"
  role   = aws_iam_role.dispatcher_role.id
  policy = data.aws_iam_policy_document.dispatcher_inline_policy.json
}

resource "aws_lambda_function" "dispatcher_lambda" {
  function_name    = local.dispatcher_function_name
  role             = aws_iam_role.dispatcher_role.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.dispatcher_zip.output_path
  source_code_hash = data.archive_file.dispatcher_zip.output_base64sha256

  timeout     = var.dispatcher_lambda_timeout
  memory_size = var.dispatcher_lambda_memory_size

  environment {
    variables = {
      JOB_QUEUE_URL         = aws_sqs_queue.synthetic_generator_job.url
      SEEDS_PER_CHUNK       = tostring(var.seeds_per_chunk)
      DEFAULT_ENTITY_COUNT  = tostring(var.default_entity_count)
      DEFAULT_WORLDGEN_MODE = var.default_worldgen_mode
    }
  }

  tags       = merge(local.common_tags, { Name = "synthetic-generator-dispatcher" })
  depends_on = [aws_cloudwatch_log_group.dispatcher_logs]
}

resource "aws_lambda_permission" "dispatcher_sns_invoke" {
  statement_id  = "AllowConfigEventsTopicInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dispatcher_lambda.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.config_events.arn
}

resource "aws_sns_topic_subscription" "config_events_to_dispatcher" {
  topic_arn = aws_sns_topic.config_events.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.dispatcher_lambda.arn

  depends_on = [aws_lambda_permission.dispatcher_sns_invoke]
}

# ---------------------------------------------------------------------------
# Lambda (synthetic generator container image)
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "synthetic_generator" {
  name              = "/aws/lambda/${local.synthetic_generator_function_name}"
  retention_in_days = var.log_retention_days
  tags              = merge(local.common_tags, { Name = "synthetic-generator" })
}

data "aws_iam_policy_document" "synthetic_generator_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "synthetic_generator" {
  name               = "${local.name_prefix}-synthetic-generator"
  assume_role_policy = data.aws_iam_policy_document.synthetic_generator_assume_role.json
  tags               = merge(local.common_tags, { Name = "synthetic-generator" })
}

data "aws_iam_policy_document" "synthetic_generator" {
  statement {
    sid    = "SyntheticGeneratorLambdaLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.synthetic_generator.arn}:*"]
  }

  statement {
    sid    = "SyntheticGeneratorJobConsume"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
    ]
    resources = [aws_sqs_queue.synthetic_generator_job.arn]
  }

  statement {
    sid       = "S3ConfigRead"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:GetObjectVersion"]
    resources = [local.config_objects_arn]
  }

  statement {
    sid       = "S3SyntheticRecordsPut"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = [local.synthetic_records_objects_arn]
  }

  statement {
    sid    = "EcrPull"
    effect = "Allow"
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability",
    ]
    resources = [var.ecr_repository_arn]
  }

  statement {
    sid       = "EcrAuth"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "synthetic_generator" {
  name   = "synthetic-generator"
  role   = aws_iam_role.synthetic_generator.id
  policy = data.aws_iam_policy_document.synthetic_generator.json
}

resource "aws_lambda_function" "synthetic_generator" {
  function_name = local.synthetic_generator_function_name
  role          = aws_iam_role.synthetic_generator.arn
  package_type  = "Image"
  image_uri     = var.lambda_image_uri

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  architectures = var.lambda_architectures

  reserved_concurrent_executions = var.lambda_reserved_concurrency

  tags = merge(local.common_tags, { Name = "synthetic-generator" })

  environment {
    variables = {
      OUTPUT_BUCKET        = aws_s3_bucket.synthetic_records.bucket
      OUTPUT_KEY_PREFIX    = var.output_object_prefix
      WORLDGEN_MODE        = var.default_worldgen_mode
      CONFIG_OBJECT_PREFIX = var.config_object_prefix
    }
  }

  depends_on = [aws_cloudwatch_log_group.synthetic_generator]
}

resource "aws_lambda_event_source_mapping" "synthetic_generator_job_to_lambda" {
  event_source_arn = aws_sqs_queue.synthetic_generator_job.arn
  function_name    = aws_lambda_function.synthetic_generator.arn
  batch_size       = var.sqs_batch_size

  maximum_batching_window_in_seconds = var.sqs_maximum_batching_window_seconds > 0 ? var.sqs_maximum_batching_window_seconds : null

  function_response_types = ["ReportBatchItemFailures"]
}
