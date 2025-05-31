# Meme Maker Infrastructure as Code (Terraform)

This directory contains Infrastructure-as-Code definitions using Terraform to provision and manage the core AWS resources for the Meme Maker application in a reproducible, versioned way.

## Overview

This Terraform configuration creates the essential infrastructure components:

- **S3 Bucket**: Temporary storage for processed video clips with automatic cleanup
- **IAM Role & Policy**: Permissions for worker/backend services to access S3
- **Route53 DNS Record**: Optional DNS management for custom domains

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  S3 Bucket      │    │  IAM Role       │    │  Route53 (opt)  │
│  - Clips storage│    │  - S3 access    │    │  - DNS record   │
│  - 1-day cleanup│    │  - Worker perms │    │  - memeit.domain│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Terraform** >= 1.5 installed
4. **Domain & Route53 Zone** (optional, for DNS management)

## Quick Start

### 1. Initial Setup

```bash
# Navigate to terraform directory
cd infra/terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

### 2. Bootstrap Terraform

For **local state** (development):
```bash
terraform init
```

For **remote state** (recommended for production):
```bash
# Edit main.tf and uncomment the backend "s3" block
# Update bucket name, region, and DynamoDB table

terraform init \
  -backend-config="bucket=your-terraform-state-bucket" \
  -backend-config="key=meme-maker/terraform.tfstate" \
  -backend-config="region=ap-south-1" \
  -backend-config="dynamodb_table=terraform-locks"
```

### 3. Validate and Apply

```bash
# Validate configuration
terraform validate

# Format code
terraform fmt

# Plan deployment
terraform plan -var-file="terraform.tfvars"

# Apply changes
terraform apply -var-file="terraform.tfvars"
```

## Configuration

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `project_name` | Project name for resource naming | `"meme-maker"` | `"meme-maker"` |
| `env` | Environment (dev/staging/prod) | `"dev"` | `"prod"` |
| `aws_region` | AWS region for all resources | `"ap-south-1"` | `"us-east-1"` |

### Optional DNS Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `domain` | Base domain name | `""` | `"example.com"` |
| `lb_dns` | Load balancer DNS name | `""` | `"my-lb-123.elb.amazonaws.com"` |
| `route53_zone_id` | Route53 hosted zone ID | `""` | `"Z1234567890ABC"` |
| `create_route53_record` | Create Route53 DNS record | `false` | `true` |

### Example Configurations

#### Development (Local)
```hcl
# terraform.tfvars
project_name = "meme-maker"
env          = "dev"
aws_region   = "ap-south-1"
```

#### Production with DNS
```hcl
# terraform.tfvars
project_name = "meme-maker"
env          = "prod"
aws_region   = "ap-south-1"
domain       = "yourdomain.com"
lb_dns       = "prod-alb-123456789.ap-south-1.elb.amazonaws.com"
route53_zone_id     = "Z1234567890ABC"
create_route53_record = true
```

## Outputs

After successful deployment, Terraform provides these key outputs:

| Output | Description | Usage |
|--------|-------------|-------|
| `bucket_name` | S3 bucket name | Configure backend/worker |
| `bucket_arn` | S3 bucket ARN | IAM policies |
| `role_arn` | IAM role ARN | ECS task definitions |
| `role_name` | IAM role name | EC2 instance profiles |
| `record_name` | DNS record name | Domain configuration |
| `resource_prefix` | Resource naming prefix | External integrations |

## Remote State Setup (Recommended)

For production deployments, use remote state with locking:

### 1. Create State Bucket

```bash
# Create S3 bucket for state
aws s3 mb s3://meme-maker-terraform-state-$(date +%s) --region ap-south-1

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region ap-south-1
```

### 2. Configure Backend

Uncomment and configure the backend block in `main.tf`:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket"
  key            = "meme-maker/terraform.tfstate"
  region         = "ap-south-1"
  dynamodb_table = "terraform-locks"
  encrypt        = true
}
```

### 3. Initialize with Backend

```bash
terraform init
```

## DNS Configuration

### Route53 Setup

If your domain is managed in AWS Route53:

1. **Get Hosted Zone ID**:
   ```bash
   aws route53 list-hosted-zones --query 'HostedZones[?Name==`yourdomain.com.`].Id' --output text
   ```

2. **Configure Variables**:
   ```hcl
   domain                = "yourdomain.com"
   route53_zone_id      = "Z1234567890ABC"
   create_route53_record = true
   lb_dns               = "your-load-balancer-dns-name"
   ```

3. **Apply Configuration**:
   ```bash
   terraform apply -var-file="terraform.tfvars"
   ```

### External DNS Providers

If using Cloudflare, GoDaddy, or other DNS providers, set `create_route53_record = false` and manually create:
- **Record Type**: CNAME
- **Name**: `memeit.yourdomain.com`
- **Value**: `your-load-balancer-dns-name`

## Resource Tagging

All resources are automatically tagged with:

- `Environment`: Environment name (`dev`, `staging`, `prod`)
- `Project`: Project name (`meme-maker`)
- `ManagedBy`: `Terraform`

Additional resource-specific tags are applied for better organization.

## Security Features

### S3 Bucket Security
- ✅ **Public access blocked** completely
- ✅ **Server-side encryption** with AES256
- ✅ **Lifecycle policy** deletes objects after 1 day
- ✅ **Versioning disabled** as specified in requirements
- ✅ **Incomplete multipart uploads** cleaned up after 1 day

### IAM Role Security
- ✅ **Principle of least privilege** - only required S3 actions
- ✅ **Resource-scoped permissions** - access only to clips bucket
- ✅ **Multiple service principals** - supports ECS and EC2

## Validation and Testing

### Pre-deployment Checks

```bash
# Validate syntax
terraform validate

# Format code
terraform fmt -check

# Security scan (if using tfsec)
tfsec .

# Plan without applying
terraform plan -var-file="terraform.tfvars"
```

### Post-deployment Testing

```bash
# Verify S3 bucket exists
aws s3 ls s3://$(terraform output -raw bucket_name)

# Verify IAM role exists
aws iam get-role --role-name $(terraform output -raw role_name)

# Test S3 permissions (requires AWS CLI with role)
aws sts assume-role --role-arn $(terraform output -raw role_arn) --role-session-name test

# Verify DNS record (if created)
dig memeit.yourdomain.com
```

## Troubleshooting

### Common Issues

1. **Permission Denied**:
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   ```

2. **Bucket Name Conflict**:
   - S3 bucket names are globally unique
   - The random suffix should prevent conflicts
   - If it fails, run `terraform destroy` and `terraform apply` again

3. **DNS Validation Timeout**:
   - Ensure Route53 zone ID is correct
   - Check domain name formatting (no trailing dots)
   - DNS propagation can take up to 10 minutes

4. **State Lock Issues**:
   ```bash
   # Force unlock if needed (use carefully)
   terraform force-unlock LOCK_ID
   ```

### Getting Help

- **Terraform Validate**: `terraform validate`
- **AWS Provider Issues**: Check [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- **State Issues**: Use `terraform state list` and `terraform state show`

## Cost Estimation

### Development Environment
- **S3**: ~$0.50/month (minimal usage)
- **Route53**: $0.50/month per hosted zone (if used)
- **Total**: ~$1/month

### Production Environment
- **S3**: ~$2-5/month (depends on clip volume)
- **Route53**: $0.50/month per hosted zone
- **Data Transfer**: Minimal (files deleted after 1 day)
- **Total**: ~$3-6/month

## Maintenance

### Regular Tasks

1. **Update Terraform Providers**:
   ```bash
   terraform init -upgrade
   ```

2. **Review and Rotate Access Keys** (if using IAM users):
   ```bash
   aws iam list-access-keys --user-name terraform-user
   ```

3. **Monitor S3 Costs**:
   ```bash
   aws s3api list-objects-v2 --bucket $(terraform output -raw bucket_name) --query 'length(Contents)'
   ```

4. **Validate Lifecycle Rules**:
   ```bash
   aws s3api get-bucket-lifecycle-configuration --bucket $(terraform output -raw bucket_name)
   ```

## Integration with Application

### Backend Configuration

Use Terraform outputs to configure your application:

```bash
# Get bucket name for backend configuration
export S3_BUCKET_NAME=$(terraform output -raw bucket_name)

# Get IAM role ARN for ECS task definition
export TASK_ROLE_ARN=$(terraform output -raw role_arn)

# Get instance profile for EC2 deployment
export INSTANCE_PROFILE_NAME=$(terraform output -raw instance_profile_name)
```

### Environment Variables

Set these in your application environment:

```bash
S3_BUCKET_NAME="meme-maker-clips-prod-abc12345"
AWS_REGION="ap-south-1"
```

The IAM role provides automatic credentials when running on AWS services (ECS, EC2).

---

## License

This infrastructure code is part of the Meme Maker project and is licensed under the same terms as the main project (MIT License). 