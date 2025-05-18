terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}


data "aws_route_table" "selected" {
  subnet_id = var.subnet_id
}

output "route_table_routes" {
  value = data.aws_route_table.selected.routes
}

resource "aws_iam_role" "world_builder_ec2_role" {
  name = "${var.project_name}-${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM instance profile for EC2 instances with the World Builder functionality
resource "aws_iam_instance_profile" "world_builder_ec2_role" {
  name = "${var.project_name}-${var.environment}-world-builder-ec2-role"
  role = aws_iam_role.world_builder_ec2_role.name
}

# S3 write access policy for the above World Builder Role
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project_name}-${var.environment}-s3-access"
  role = aws_iam_role.world_builder_ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::world-builder-example/*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "cloudwatch_agent_policy" {
  name        = "${var.project_name}-${var.environment}-cloudwatch-agent-policy"
  description = "Policy for CloudWatch agent to send logs and metrics"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "cloudwatch:PutMetricData",
          "ec2:DescribeTags",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
          "logs:DescribeLogGroups",
          "logs:CreateLogStream",
          "logs:CreateLogGroup"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cloudwatch_agent_attach" {
  role       = aws_iam_role.world_builder_ec2_role.name
  policy_arn = aws_iam_policy.cloudwatch_agent_policy.arn
}

resource "aws_iam_role_policy" "ec2_terminate" {
  name = "${var.project_name}-${var.environment}-ec2-terminate"
  role = aws_iam_role.world_builder_ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ec2:TerminateInstances"
        ],
        Resource = "*" # Optionally restrict to the instance ARN if available
      }
    ]
  })
}

# EC2 instance
resource "aws_instance" "world_builder" {
  for_each               = toset(var.benchmark_instance_types)
  ami                    = var.ami_map[local.instance_architectures[each.value]]
  instance_type          = each.value
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.world_builder_ec2_role.name

  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data.sh", {
    project_name = var.project_name
    environment  = var.environment
    instance_type = each.value
  })

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-instance-${each.value}"
    }
  )
}

# Common tags for all resources
locals {
  instance_architectures = {
    "t4g.nano"    = "arm64"
    "t4g.medium"  = "arm64"
    "t4g.xlarge"  = "arm64"
    "t4g.2xlarge" = "arm64"
    "m5.large"    = "x86_64"
    "m5.xlarge"   = "x86_64"
    "m5.2xlarge"  = "x86_64"
    "m5.4xlarge"  = "x86_64"
    "m5.8xlarge"  = "x86_64"
    "m5.12xlarge" = "x86_64"
    "m5.24xlarge" = "x86_64"
    "m8g.medium"    = "arm64"
    "m8g.large"     = "arm64"
    "m8g.xlarge"    = "arm64"
    "m8g.2xlarge"   = "arm64"
    "m8g.4xlarge"   = "arm64"
    "m8g.8xlarge"   = "arm64"
    "m8g.16xlarge"  = "arm64"
    "m8g.24xlarge"  = "arm64"
    "m8g.48xlarge"  = "arm64"
    "c8g.medium"    = "arm64"
    "c8g.large"     = "arm64"
    "c8g.xlarge"    = "arm64"
    "c8g.2xlarge"   = "arm64"
    "c8g.4xlarge"   = "arm64"
    "c8g.8xlarge"   = "arm64"
    "c8g.16xlarge"  = "arm64"
    "c8g.24xlarge"  = "arm64"
    "c8g.48xlarge"  = "arm64"
  }
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

data "aws_security_group" "existing" {
  id = var.security_group_id
}

output "security_group_info" {
  value = data.aws_security_group.existing
}