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
  default = ["c8g.8xlarge"]
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