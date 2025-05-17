# World Builder Infrastructure

This directory contains the infrastructure as code (IaC) for deploying the World Builder application to AWS EC2.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0.0
- An SSH key pair registered in AWS EC2
- Access to the specified VPC and subnet

## Directory Structure

```
infra/
└── world_builder/
    └── terraform/
        ├── main.tf          # Main Terraform configuration
        ├── variables.tf     # Variable definitions
        ├── outputs.tf       # Output definitions
        ├── user_data.sh     # EC2 instance initialization script
        └── terraform.tfvars # Variable values (not in git)
```

## Configuration

1. Copy the example tfvars file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your specific values:
   - AWS region
   - VPC and subnet IDs
   - Security group ID
   - SSH key name
   - Instance type and AMI ID

## Usage

1. Initialize Terraform:
   ```bash
   cd terraform
   terraform init
   ```

2. Review the planned changes:
   ```bash
   terraform plan
   ```

3. Apply the changes:
   ```bash
   terraform apply
   ```

4. To destroy the infrastructure:
   ```bash
   terraform destroy
   ```

## Security Notes

- Never commit `terraform.tfvars` or any files containing secrets
- Use AWS IAM roles for EC2 instance permissions
- Keep your SSH private key secure
- Review security group rules regularly

## Maintenance

- Update AMI IDs periodically for security patches
- Review and update instance types as needed
- Monitor CloudWatch logs and metrics
- Regularly update Terraform providers

## Troubleshooting

1. Check instance logs:
   ```bash
   ssh ec2-user@<instance-ip> 'sudo journalctl -u world-builder'
   ```

2. View application logs:
   ```bash
   ssh ec2-user@<instance-ip> 'sudo tail -f /var/log/world-builder/app.log'
   ```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## Notes

- The EC2 instance runs as a systemd service
- Logs are automatically rotated daily
- The application runs under a dedicated service user
- Instance storage is encrypted by default 