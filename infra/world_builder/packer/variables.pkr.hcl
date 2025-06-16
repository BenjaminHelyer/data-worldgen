variable "aws_region" {
  description = "AWS region to build the AMI in"
  type        = string
  default     = "us-east-2"  # Matching Terraform default
}

variable "instance_type" {
  description = "EC2 instance type to use for building the AMI"
  type        = string
  default     = "t3.micro"
}

variable "vpc_id" {
  description = "ID of the VPC to use for building the AMI"
  type        = string
}

variable "subnet_id" {
  description = "ID of the subnet to use for building the AMI"
  type        = string
}

variable "security_group_id" {
  description = "ID of the security group to use for building the AMI"
  type        = string
}

variable "project_name" {
  description = "Name of the project for resource tagging"
  type        = string
  default     = "world-builder"  # Matching Terraform default
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"  # Matching Terraform default
} 