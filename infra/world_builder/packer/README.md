# World Builder AMI Builder

This directory contains Packer configuration to build an Amazon Machine Image (AMI) for the World Builder application.

## Overview

This Packer setup automates the creation of a pre-configured AMI that contains your entire World Builder application stack. Instead of using user data scripts that run every time an instance boots (which is slow and can fail), this approach "bakes" everything into a reusable AMI that boots instantly with all dependencies pre-installed.

**Build Process:**
1. Launches a temporary EC2 instance with Amazon Linux 2023
2. Runs your existing `user_data.sh` script to install and configure everything
3. Creates a snapshot (AMI) of the fully configured instance
4. Cleans up the temporary instance

**Result:** A production-ready AMI that can launch instances with your application already installed and running.

## What the AMI Includes

When the build completes, your AMI will contain:

1. **Fresh Amazon Linux 2023** base image with latest updates
2. **Your World Builder application** fully installed at `/opt/world-builder/data-worldgen`
3. **Python 3.11** virtual environment with all project dependencies installed
4. **systemd service** (`world-builder.service`) configured to auto-start your application
5. **CloudWatch Agent** installed and configured for monitoring
6. **Log rotation** configured for application logs in `/var/log/world-builder/`
7. **Proper permissions** and user accounts set up
8. **Clean state** - temporary files removed, cloud-init cleaned

## Prerequisites

1. Install [Packer](https://developer.hashicorp.com/packer/downloads)
2. Configure AWS credentials (either through environment variables or AWS CLI configuration)
3. Ensure you have appropriate AWS permissions to create AMIs, EC2 instances, and manage security groups

## Configuration

The Packer configuration uses variables to customize the build process. These variables are defined in `variables.pkr.hcl` and can be set in two ways:

1. Using a `world-builder.auto.pkrvars.hcl` file (recommended)
2. Passing variables on the command line

### Required Variables

The following variables must be set either in your `.auto.pkrvars.hcl` file or via command line:

- `vpc_id`: ID of the VPC to use for building
- `subnet_id`: ID of the subnet to use for building (must have internet access for package downloads)
- `security_group_id`: ID of the security group to use (must allow SSH inbound on port 22 and outbound internet access)

### Optional Variables with Defaults

- `aws_region`: AWS region to build in (default: "us-east-2")
- `instance_type`: EC2 instance type to use (default: "t3.micro")
- `project_name`: Name of the project (default: "world-builder")
- `environment`: Environment name (default: "dev")

### Setting Up Variables

1. Copy the example variables file:
   ```bash
   cp world-builder.auto.pkrvars.example world-builder.auto.pkrvars.hcl
   ```

2. Edit `world-builder.auto.pkrvars.hcl` with your actual values
   - This file should not be committed to version control
   - Add `*.auto.pkrvars.hcl` to your `.gitignore`

## Connection Method

This configuration uses **regular SSH over a public IP** for connecting to the build instance during the AMI creation process. Here's how it works:

- **Public IP**: Assigns a temporary public IP to the build instance (`associate_public_ip_address = true`)
- **SSH Keys**: Uses automatically generated SSH key pairs (managed by Packer)
- **Connection**: Connects directly via SSH over the internet on port 22
- **Security**: Uses your specified security group (must allow SSH inbound from your IP)
- **Cleanup**: All temporary resources (instance, keys, etc.) are automatically cleaned up after the build

**Requirements:**
- Your subnet must have internet access (public subnet or private subnet with NAT gateway)
- Your security group must allow inbound SSH (port 22) from your IP address
- Your security group must allow outbound internet access for package downloads

**Note:** The build instance is temporary and only exists during the AMI creation process (~15 minutes).

## Building the AMI

To build the AMI, run:

```bash
packer init .
packer build .
```

To build with custom variables on the command line:

```bash
packer build -var="aws_region=us-west-2" -var="instance_type=t3.small" .
```

**Build time:** Approximately 15 minutes (depending on instance type and network speed)

## AMI Naming and Tagging

The AMI will be named using the format: `${project_name}-${environment}-${timestamp}`

Example: `world-builder-dev-20250616145046`

The AMI will be tagged with:
- Name: `${project_name}-${environment}`
- Project: `${project_name}`
- Environment: `${environment}`
- ManagedBy: "packer"
- Timestamp: Build timestamp

## Using the AMI

After building, you can use the AMI ID in your Terraform configuration. When you launch instances with this AMI:

1. **Instant startup** - No waiting for user data scripts
2. **Reliable deployment** - Everything is pre-tested and baked in
3. **Consistent environment** - All instances start with identical configuration
4. **Auto-starting service** - Your application starts automatically on boot

Simply replace your current AMI ID in your Terraform configuration with the new one from the build output.

## Troubleshooting

### Common Issues

1. **Build fails with network errors**: Ensure your subnet has internet access (either public subnet or NAT gateway)
2. **SSH connection timeout**: Verify your security group allows SSH (port 22) inbound from your IP
3. **Permission errors**: Verify your AWS credentials have EC2 and IAM permissions
4. **Package download failures**: Ensure outbound internet access is allowed

### Build Logs

Monitor the build progress in the terminal output. All installation steps from your `user_data.sh` script will be visible, making it easy to debug any issues.

## Maintenance

- **Rebuild periodically** to include security updates and application changes
- **Test new AMIs** in a staging environment before using in production
- **Clean up old AMIs** when they're no longer needed to reduce costs
- **Consider implementing a CI/CD pipeline** to automate the AMI build process
- **Update dependencies** in your `user_data.sh` script as needed

## Next Steps

1. Use the new AMI ID in your Terraform configuration
2. Test launching instances with the new AMI
3. Set up automated AMI building in your CI/CD pipeline
4. Consider creating AMIs for different environments (dev, staging, prod) 