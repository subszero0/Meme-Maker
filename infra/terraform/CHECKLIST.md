# Terraform Infrastructure Deployment Checklist

## Pre-Deployment ✅

- [ ] **AWS CLI configured** with appropriate credentials
- [ ] **Terraform >= 1.6** installed and working
- [ ] **VPC with public and private subnets** already exists
- [ ] **S3 bucket for Terraform state** created (recommended)
- [ ] **Domain name** registered (if using custom domain)

## Validation Steps ✅

- [ ] `terraform init` succeeds with no warnings
- [ ] `terraform validate` returns 0 issues
- [ ] `terraform plan` against a dummy backend shows the 7 resources above
- [ ] README contains exact `terraform apply -var-file=…` example
- [ ] CI pipeline stub (GitHub Actions) added to run `terraform fmt -check` and `terraform validate`

## Infrastructure Resources ✅

This Terraform module creates the following AWS resources:

### Core Infrastructure
- [ ] **S3 bucket** `clip-downloader-files-{env}-{suffix}`
  - [ ] Block public access enabled
  - [ ] Lifecycle policy for 1-day expiration
  - [ ] Versioning enabled
  - [ ] Proper tagging

### Networking & Security
- [ ] **Security Groups** for ALB, ECS tasks, and Redis
  - [ ] ALB allows HTTP/HTTPS from internet
  - [ ] ECS tasks allow 8000 from ALB only
  - [ ] Redis allows 6379 from ECS tasks only
- [ ] **Application Load Balancer** (public)
  - [ ] HTTP/HTTPS listeners configured
  - [ ] Target group with health checks
  - [ ] SSL certificate (if domain provided)

### Compute & Storage
- [ ] **ECS Cluster** with Container Insights
- [ ] **ECS Task Definitions** for backend and worker
  - [ ] Proper resource allocation (CPU/memory)
  - [ ] Environment variables configured
  - [ ] Health checks implemented
- [ ] **ECS Services** for backend and worker
  - [ ] Auto-scaling configuration
  - [ ] Service discovery setup

### Data & Caching
- [ ] **ElastiCache Redis cluster** (t4g.micro)
  - [ ] Subnet group in private subnets
  - [ ] Security group restrictions
  - [ ] Parameter group configuration

### Container Registry
- [ ] **ECR repositories** for backend and worker
  - [ ] Image scanning enabled
  - [ ] Proper naming convention

### Access Control
- [ ] **IAM roles** for ECS tasks
  - [ ] Task execution role with ECS permissions
  - [ ] Task role with S3 and CloudWatch access
  - [ ] Least-privilege policies
- [ ] **IAM user** for CI/CD deployments
  - [ ] ECR push/pull permissions
  - [ ] ECS service update permissions

### Monitoring
- [ ] **CloudWatch Log Groups** with 7-day retention
  - [ ] Backend application logs
  - [ ] Worker application logs

## Post-Deployment Verification ✅

### Infrastructure Health
- [ ] **ECS services** are running and healthy
- [ ] **ALB health checks** are passing
- [ ] **Redis cluster** is available
- [ ] **S3 bucket** is accessible

### Application Deployment
- [ ] **Container images** pushed to ECR
- [ ] **ECS services** updated with new images
- [ ] **Application endpoints** responding
- [ ] **Health check endpoint** (`/health`) working

### Security Verification
- [ ] **S3 bucket** is not publicly accessible
- [ ] **Redis** is only accessible from ECS tasks
- [ ] **ECS tasks** are in private subnets
- [ ] **IAM policies** follow least-privilege

### Monitoring Setup
- [ ] **CloudWatch logs** are flowing
- [ ] **ECS metrics** are available
- [ ] **Application metrics** are being collected

## Environment-Specific Configurations ✅

### Development Environment
- [ ] Resource sizing appropriate for development
- [ ] Cost optimization settings applied
- [ ] Non-production safety nets in place

### Production Environment
- [ ] **Deletion protection** enabled on critical resources
- [ ] **Multi-AZ deployment** for high availability
- [ ] **Backup and recovery** procedures documented
- [ ] **Monitoring and alerting** configured
- [ ] **SSL certificate** properly configured
- [ ] **Domain name** pointing to ALB

## Cleanup Checklist ⚠️

**Before destroying infrastructure:**

- [ ] **S3 bucket** is empty (objects manually deleted)
- [ ] **ECR repositories** cleaned up if no longer needed
- [ ] **CloudWatch logs** exported if needed for audit
- [ ] **Domain DNS** updated to remove ALB reference
- [ ] **Backup** any important configuration or data

## Troubleshooting Quick Reference ✅

### Common Issues
- [ ] **VPC/Subnet IDs** are correct and exist
- [ ] **AWS credentials** have sufficient permissions
- [ ] **Terraform state** is not corrupted
- [ ] **Resource limits** not exceeded in AWS account

### Validation Commands
```bash
# Check ECS services
aws ecs describe-services --cluster <cluster-name> --services <service-name>

# Check ALB health
curl <alb-url>/health

# View logs
aws logs tail /ecs/clip-downloader-backend-dev --follow

# Test ECR access
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <repo-url>
```

## Cost Monitoring ✅

### Expected Monthly Costs (Development)
- [ ] **ECS Fargate**: ~₹1,000 (minimal usage)
- [ ] **ElastiCache**: ~₹800 (t4g.micro)
- [ ] **ALB**: ~₹500 (minimal traffic)
- [ ] **S3/CloudWatch**: ~₹200 (low usage)
- [ ] **Total**: ~₹2,500/month

### Cost Optimization
- [ ] **Right-size resources** based on actual usage
- [ ] **Enable S3 lifecycle policies** for automatic cleanup
- [ ] **Monitor unused resources** regularly
- [ ] **Use spot instances** for development workloads (if applicable) 