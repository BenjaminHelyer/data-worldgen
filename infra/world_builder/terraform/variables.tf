variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-2"
}

variable "vpc_id" {
  description = "ID of the VPC to deploy into"
  type        = string
}

variable "subnet_id" {
  description = "ID of the subnet to deploy into"
  type        = string
}

variable "security_group_id" {
  description = "ID of the security group to use"
  type        = string
}

variable "key_name" {
  description = "Name of the SSH key pair to use for EC2 instances"
  type        = string
}

variable "ami_map" {
  description = "Map of architecture to AMI IDs"
  type        = map(string)
}

variable "benchmark_instance_types" {
  description = "List of EC2 instance types to benchmark."
  type        = list(string)
  default     = ["t4g.nano", "t4g.medium", "t4g.xlarge", "t4g.2xlarge", "m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge", "m5.8xlarge", "m5.12xlarge", "m5.24xlarge", "m8g.medium", "m8g.large", "m8g.xlarge", "m8g.2xlarge", "m8g.4xlarge", "m8g.8xlarge", "m8g.16xlarge", "m8g.24xlarge", "m8g.48xlarge", "c8g.medium", "c8g.large", "c8g.xlarge", "c8g.2xlarge", "c8g.4xlarge", "c8g.8xlarge", "c8g.16xlarge", "c8g.24xlarge", "c8g.48xlarge"]
}

variable "project_name" {
  description = "Name of the project for resource tagging"
  type        = string
  default     = "world-builder"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
} 