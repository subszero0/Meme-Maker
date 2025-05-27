variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-south-1"
}

variable "domain_name" {
  description = "Domain name for ALB certificate (optional)"
  type        = string
  default     = ""
}

variable "vpc_id" {
  description = "VPC ID where resources will be created"
  type        = string
}

variable "public_subnets" {
  description = "List of public subnet IDs for ALB"
  type        = list(string)
}

variable "private_subnets" {
  description = "List of private subnet IDs for ECS services"
  type        = list(string)
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "backend_task_cpu" {
  description = "CPU units for backend task (256, 512, 1024, etc.)"
  type        = number
  default     = 256
}

variable "backend_task_memory" {
  description = "Memory for backend task in MB (512, 1024, 2048, etc.)"
  type        = number
  default     = 512
}

variable "worker_task_cpu" {
  description = "CPU units for worker task (256, 512, 1024, etc.)"
  type        = number
  default     = 512
}

variable "worker_task_memory" {
  description = "Memory for worker task in MB (512, 1024, 2048, etc.)"
  type        = number
  default     = 1024
}

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 1
}

variable "worker_desired_count" {
  description = "Desired number of worker tasks"
  type        = number
  default     = 1
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.micro"
}

variable "github_repository" {
  description = "GitHub repository in format 'owner/repo-name' for OIDC role"
  type        = string
  default     = ""
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for the domain"
  type        = string
  default     = ""
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token for DNS management"
  type        = string
  default     = ""
  sensitive   = true
} 