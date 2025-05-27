# Clip Downloader - Terraform Infrastructure

This Terraform module deploys the complete infrastructure for the Clip Downloader application on AWS, including Cloudflare DNS integration and SSL certificate management.

## Architecture

- **ECS Fargate**: Backend API and worker services
- **ALB**: Application Load Balancer with HTTPS termination
- **ElastiCache Redis**: Job queue and caching
- **S3**: Temporary file storage with lifecycle policies
- **ECR**: Container image registry
- **CloudWatch**: Logging and monitoring
- **ACM**: SSL/TLS certificates (validated via Cloudflare DNS)
- **WAF v2**: Web Application Firewall with rate limiting
- **Cloudflare**: DNS management and CDN (optional)

## Features

### SSL/TLS & DNS
- ✅ **Automatic SSL certificate** provisioning via AWS Certificate Manager
- ✅ **DNS validation** using Cloudflare DNS records
- ✅ **API subdomain** (`api.yourdomain.com`) pointing to the ALB
- ✅ **HTTP to HTTPS redirect** for secure connections
- ✅ **Modern TLS policy** (TLS 1.3 support)

### Security
- ✅ **WAF v2 protection** with rate limiting (2000 requests/5min per IP)
- ✅ **AWS Managed Rules** for common web exploits
- ✅ **Private subnets** for ECS tasks
- ✅ **Security groups** with minimal required access
- ✅ **IAM roles** with least privilege access

### Scalability & Reliability
- ✅ **Auto-scaling** ECS services based on CPU/queue depth
- ✅ **Health checks** with automatic failover
- ✅ **Multi-AZ deployment** for high availability
- ✅ **Container insights** for monitoring

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Cloudflare Account** with domain management (optional, for SSL)
3. **Terraform** >= 1.6
4. **AWS CLI** configured
5. **S3 bucket** for Terraform state storage

## Required Variables

### Core Infrastructure
```hcl
aws_region      = "ap-south-1"        # AWS region
environment     = "dev"               # Environment name
vpc_id          = "vpc-xxxxxxxxx"     # Existing VPC ID
public_subnets  = ["subnet-xxx", "subnet-yyy"]   # Public subnets for ALB
private_subnets = ["subnet-aaa", "subnet-bbb"]   # Private subnets for ECS
```

### Domain & SSL (Optional)
```hcl
domain_name         = "example.com"           # Your domain name
cloudflare_zone_id  = "xxxxxxxxxxxxxxxxxx"   # Cloudflare zone ID
cloudflare_api_token = "xxxxxxxxxxxxx"       # Cloudflare API token (sensitive)
```

### CI/CD Integration
```hcl
github_repository = "your-username/meme-maker"  # For OIDC role
```

## Deployment

### 1. Local Development

```bash
# Navigate to terraform directory
cd infra/terraform

# Initialize Terraform
terraform init -backend-config="bucket=your-state-bucket" \
               -backend-config="key=clip-downloader/terraform.tfstate" \
               -backend-config="region=ap-south-1"

# Plan deployment
terraform plan -var-file="terraform.tfvars"

# Apply changes
terraform apply -var-file="terraform.tfvars"
```

### 2. GitHub Actions (Recommended)

The included GitHub Actions workflow automatically deploys infrastructure on pushes to `main`.

#### Required Secrets
```
AWS_ACCESS_KEY_ID     # AWS access key
AWS_SECRET_ACCESS_KEY # AWS secret key
CF_API_TOKEN          # Cloudflare API token (if using domain)
```

#### Required Variables
```
AWS_REGION            # e.g., "ap-south-1"
TF_STATE_BUCKET       # Terraform state bucket name
VPC_ID                # VPC ID for deployment
PUBLIC_SUBNETS        # Comma-separated public subnet IDs
PRIVATE_SUBNETS       # Comma-separated private subnet IDs
DOMAIN_NAME           # Your domain (optional)
CLOUDFLARE_ZONE_ID    # Cloudflare zone ID (optional)
GITHUB_REPOSITORY     # Repository name for OIDC
ENVIRONMENT           # Environment name (dev/staging/prod)
```

## Cloudflare Integration

### Setup Steps

1. **Get Zone ID**:
   ```bash
   curl -X GET "https://api.cloudflare.com/client/v4/zones" \
        -H "Authorization: Bearer YOUR_API_TOKEN" | jq '.result[] | {name: .name, id: .id}'
   ```

2. **Create API Token**:
   - Go to Cloudflare dashboard → My Profile → API Tokens
   - Create token with permissions:
     - Zone:Zone:Read
     - Zone:DNS:Edit
     - Include: Specific zone → Your domain

3. **Configure Variables**:
   ```hcl
   domain_name         = "yourdomain.com"
   cloudflare_zone_id  = "zone-id-from-step-1"
   cloudflare_api_token = "token-from-step-2"
   ```

### What Gets Created

When domain and Cloudflare are configured:

1. **DNS Records**:
   - `api.yourdomain.com` → ALB DNS name (CNAME)
   - ACM validation records (automatically managed)

2. **SSL Certificate**:
   - Domain: `api.yourdomain.com`
   - Validation: DNS (via Cloudflare)
   - Region: `us-east-1` (required for ALB)

3. **ALB Listeners**:
   - Port 443: HTTPS → Backend service
   - Port 80: HTTP → 301 redirect to HTTPS

4. **WAF Protection**:
   - Rate limiting: 2000 requests per 5 minutes per IP
   - AWS managed rules for common exploits
   - CloudWatch metrics enabled

## Outputs

After successful deployment:

```hcl
alb_dns_name          = "clip-downloader-dev-123456789.ap-south-1.elb.amazonaws.com"
alb_url               = "https://api.yourdomain.com"  # or HTTP if no domain
api_fqdn              = "api.yourdomain.com"          # or ALB DNS if no domain
s3_bucket_name        = "clip-downloader-files-dev-abc12345"
ecs_cluster_name      = "clip-downloader-dev"
ci_deploy_role_arn    = "arn:aws:iam::123456789012:role/clip-downloader-github-actions-dev"
```

## Monitoring & Troubleshooting

### Health Checks

Test the deployment:

```bash
# Without domain
curl -f http://your-alb-dns-name/health

# With domain
curl -f https://api.yourdomain.com/health
```

Expected response:
```json
{"status": "ok"}
```

### CloudWatch Logs

Monitor application logs:
- Backend: `/ecs/clip-downloader-backend-dev`
- Worker: `/ecs/clip-downloader-worker-dev`

### WAF Metrics

Monitor security events:
- WAF Web ACL: `clipDownloaderWAF`
- Rate limiting: `RateLimitRule`
- Security rules: `CommonRuleSetMetric`

## Cost Optimization

### Resource Sizing
```hcl
# Development
backend_task_cpu    = 256   # 0.25 vCPU
backend_task_memory = 512   # 512 MB
worker_task_cpu     = 512   # 0.5 vCPU
worker_task_memory  = 1024  # 1 GB

# Production
backend_task_cpu    = 1024  # 1 vCPU
backend_task_memory = 2048  # 2 GB
worker_task_cpu     = 2048  # 2 vCPU
worker_task_memory  = 4096  # 4 GB
```

### Estimated Monthly Costs (us-east-1)

| Component | Development | Production |
|-----------|-------------|------------|
| ECS Fargate | $15-30 | $60-120 |
| ALB | $20 | $20 |
| ElastiCache | $15 | $100 |
| CloudWatch | $5 | $15 |
| S3 + Transfer | $5 | $20 |
| **Total** | **~$60** | **~$275** |

*Costs are estimates and may vary based on usage patterns.*

## Security Best Practices

1. **Enable GuardDuty** for threat detection
2. **Use Secrets Manager** for sensitive configuration
3. **Enable CloudTrail** for audit logging
4. **Regular security updates** for container images
5. **Network ACLs** for additional network security
6. **Backup strategies** for critical data

## Cleanup

To destroy all resources:

```bash
terraform destroy -var-file="terraform.tfvars"
```

**⚠️ Warning**: This will permanently delete all infrastructure and data.

## Support

For issues or questions:
1. Check CloudWatch logs for application errors
2. Review Terraform plan output for infrastructure issues
3. Verify DNS propagation with `dig` or `nslookup`
4. Test connectivity with `curl` or browser developer tools 