packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.1"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
}

source "amazon-ebs" "world-builder" {
  ami_name      = "${var.project_name}-${var.environment}-${local.timestamp}"
  instance_type = var.instance_type
  region        = var.aws_region
  vpc_id        = var.vpc_id
  subnet_id     = var.subnet_id

  # AWS configuration for better reliability
  max_retries = 10

  # Use Amazon Linux 2023 as the base image
  source_ami_filter {
    filters = {
      name                = "al2023-ami-*-x86_64"
      virtualization-type = "hvm"
      root-device-type    = "ebs"
    }
    most_recent = true
    owners      = ["amazon"]
  }

  # Use specified security group
  security_group_ids = [var.security_group_id]

  # Assign public IP for SSH access
  associate_public_ip_address = true

  # Use SSH for communication
  communicator = "ssh"
  ssh_username = "ec2-user"
  ssh_timeout = "10m"

  # Add tags to the AMI
  tags = {
    Name        = "${var.project_name}-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "packer"
    Timestamp   = local.timestamp
  }
}

build {
  sources = ["source.amazon-ebs.world-builder"]

  # Copy the user data script to the instance
  provisioner "file" {
    source      = "../terraform/user_data.sh"
    destination = "/tmp/user_data.sh"
  }

  # Make the script executable and run it
  provisioner "shell" {
    inline = [
      "chmod +x /tmp/user_data.sh",
      "sudo /tmp/user_data.sh"
    ]
  }

  # Clean up
  provisioner "shell" {
    inline = [
      "sudo rm -f /tmp/user_data.sh",
      "sudo rm -f /var/log/user-data.log",
      "sudo cloud-init clean",
      "sudo rm -rf /var/lib/cloud/instances/*",
      "sudo rm -f /var/log/cloud-init*.log"
    ]
  }
} 