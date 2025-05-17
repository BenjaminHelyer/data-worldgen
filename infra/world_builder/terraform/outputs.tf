output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.world_builder.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.world_builder.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.world_builder.private_ip
}

output "iam_role_name" {
  description = "Name of the IAM role created for the EC2 instance"
  value       = aws_iam_role.world_builder_ec2_role.name
}

output "iam_role_arn" {
  description = "ARN of the IAM role created for the EC2 instance"
  value       = aws_iam_role.world_builder_ec2_role.arn
} 