output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for clips"
  value       = aws_s3_bucket.clips.bucket
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecr_backend_repository_url" {
  description = "URL of the backend ECR repository"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_worker_repository_url" {
  description = "URL of the worker ECR repository"
  value       = aws_ecr_repository.worker.repository_url
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "ci_user_name" {
  description = "Name of the CI/CD IAM user"
  value       = aws_iam_user.ci_deploy.name
}

output "backend_service_name" {
  description = "Name of the backend ECS service"
  value       = aws_ecs_service.backend.name
}

output "worker_service_name" {
  description = "Name of the worker ECS service"
  value       = aws_ecs_service.worker.name
}

output "alb_url" {
  description = "Full URL to access the application"
  value       = var.domain_name != "" && var.cloudflare_zone_id != "" ? "https://api.${var.domain_name}" : "http://${aws_lb.main.dns_name}"
}

output "ci_deploy_role_arn" {
  description = "ARN of the GitHub Actions OIDC role for CI/CD"
  value       = aws_iam_role.github_actions.arn
}

output "api_fqdn" {
  description = "Fully qualified domain name for the API endpoint"
  value       = var.domain_name != "" && var.cloudflare_zone_id != "" ? "api.${var.domain_name}" : aws_lb.main.dns_name
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = var.domain_name != "" && var.cloudflare_zone_id != "" ? aws_wafv2_web_acl.main[0].arn : null
} 