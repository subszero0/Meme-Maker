# Core Variables for Meme Maker Infrastructure

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "meme-maker"
  
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.project_name))
    error_message = "Project name must start with a letter, contain only lowercase letters, numbers, and hyphens, and end with a letter or number."
  }
}

variable "env" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}

# Optional DNS Configuration
variable "domain" {
  description = "Base domain name for DNS record creation (e.g., 'example.com')"
  type        = string
  default     = ""
}

variable "lb_dns" {
  description = "Load balancer DNS name to point the domain record to"
  type        = string
  default     = ""
}

# Optional Route53 Configuration
variable "route53_zone_id" {
  description = "Route53 hosted zone ID for domain management (if domain is managed in AWS)"
  type        = string
  default     = ""
}

variable "create_route53_record" {
  description = "Whether to create Route53 DNS record"
  type        = bool
  default     = false
} 