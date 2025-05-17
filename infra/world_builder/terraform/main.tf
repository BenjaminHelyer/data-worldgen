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


# EC2 instance
resource "aws_instance" "world_builder" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  key_name              = var.key_name
  iam_instance_profile  = aws_iam_instance_profile.world_builder_ec2_role.name

  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data.sh", {
    project_name = var.project_name
    environment  = var.environment
  })

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-instance"
    }
  )
}

# Common tags for all resources
locals {
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