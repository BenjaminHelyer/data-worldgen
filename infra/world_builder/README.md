# World Builder Infrastructure

This directory contains infrastructure as code (IaC) for the World Builder on AWS: an **EC2 benchmark stack** and an **event-driven Lambda pipeline** (S3 to SNS to SQS to Lambda container).

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0.0
- For EC2: an SSH key pair, VPC, subnet, and security group
- For the event pipeline: an ECR image URI that implements the **Lambda container interface** (Runtime Interface Client); the image must parse SQS messages and drive `world_builder.batch_s3` (application code is not wired in this repo yet)

## Directory Structure

```
infra/
└── world_builder/
    ├── terraform/                 # EC2 benchmark instances
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   ├── user_data.sh
    │   └── terraform.tfvars       # not in git
    ├── terraform_event_pipeline/  # S3 -> SNS -> SQS -> Lambda (container)
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   ├── versions.tf
    │   └── terraform.tfvars.example
    ├── docs/
    └── PRD-serverless-event-pipeline.md
```

## Configuration (EC2 stack)

1. Copy the example tfvars file:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your specific values:
   - AWS region
   - VPC and subnet IDs
   - Security group ID
   - SSH key name
   - Instance type and AMI ID

## Usage (EC2 stack)

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

## Event pipeline (Lambda)

Flow: **S3 config upload → SNS → dispatcher Lambda (zip) → SQS chunked jobs → worker Lambda (container)**. See `PRD-serverless-event-pipeline.md` and `docs/architecture_serverless_pipeline.png`.

1. Build and push the **worker** image from the repo root (implements `lambda_synthetic_worker.lambda_handler`):

   ```bash
   docker build -f Dockerfile.synthetic_generator_lambda -t <account>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag> .
   docker push ...
   ```

2. In `terraform_event_pipeline`, copy tfvars and set `lambda_image_uri` and `ecr_repository_arn`:

   ```bash
   cd terraform_event_pipeline
   cp terraform.tfvars.example terraform.tfvars
   ```

3. Run `terraform init` (pulls `hashicorp/archive` for the dispatcher zip), `terraform plan`, and `terraform apply`.

4. Optional: set `seeds_per_chunk` (default 25000), `dispatcher_lambda_timeout`, and `dispatcher_lambda_memory_size` in `terraform.tfvars`.

5. Outputs include bucket IDs, `synthetic_generator_dispatcher_lambda_*`, `worldgen_synthetic_generator_job_queue_url`, `worldgen_synthetic_generator_lambda_function_name`, and related ARNs. Upload a JSON config under the configured prefix (default `configs/`); include top-level `entity_count` (or rely on `default_entity_count`). Parquet chunks appear under `{output_object_prefix}/<config_stem>/chunk_XXXX.parquet`.

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

## Debugging & Monitoring

### Check User Data Script Output
After launching an instance, SSH in and run:

```bash
sudo cat /var/log/user-data.log
```
This will show the output and any errors from the user data script that runs at boot.

### Monitor the world-builder systemd Service

- **Check service status:**
  ```bash
  sudo systemctl status world-builder
  ```
- **View service logs:**
  ```bash
  sudo journalctl -u world-builder
  ```
- **Follow logs in real time:**
  ```bash
  sudo journalctl -u world-builder -f
  ```
- **Restart the service:**
  ```bash
  sudo systemctl restart world-builder
  ```
- **Reload systemd after editing the service file:**
  ```bash
  sudo systemctl daemon-reload
  ```