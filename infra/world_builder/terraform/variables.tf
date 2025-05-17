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

variable "ami_id" {
  description = "ID of the AMI to use for EC2 instances"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
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