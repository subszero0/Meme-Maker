# Terraform Outputs for Meme Maker Infrastructure
# Core values for integration with other systems

output "bucket_name" {
  description = "Name of the S3 bucket for video clips"
  value       = aws_s3_bucket.clips.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 bucket for video clips"
  value       = aws_s3_bucket.clips.arn
}

output "role_arn" {
  description = "ARN of the IAM role for worker/backend services"
  value       = aws_iam_role.worker_backend.arn
}

output "role_name" {
  description = "Name of the IAM role for worker/backend services"
  value       = aws_iam_role.worker_backend.name
}

output "instance_profile_name" {
  description = "Name of the IAM instance profile for EC2 deployments"
  value       = aws_iam_instance_profile.worker_backend.name
}

output "instance_profile_arn" {
  description = "ARN of the IAM instance profile for EC2 deployments"
  value       = aws_iam_instance_profile.worker_backend.arn
}

# DNS outputs (when Route53 is used)
output "record_name" {
  description = "DNS record name created (if Route53 record was created)"
  value       = var.create_route53_record && var.route53_zone_id != "" && var.lb_dns != "" ? aws_route53_record.api[0].name : null
}

output "record_fqdn" {
  description = "Fully qualified domain name of the created DNS record"
  value       = var.create_route53_record && var.route53_zone_id != "" && var.lb_dns != "" ? aws_route53_record.api[0].fqdn : null
}

# Environment information
output "environment" {
  description = "Environment name"
  value       = var.env
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

# Resource naming outputs for external integrations
output "resource_prefix" {
  description = "Resource naming prefix used for all resources"
  value       = "${var.project_name}-${var.env}"
}

output "bucket_domain_name" {
  description = "S3 bucket domain name for direct access"
  value       = aws_s3_bucket.clips.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "S3 bucket regional domain name"
  value       = aws_s3_bucket.clips.bucket_regional_domain_name
}