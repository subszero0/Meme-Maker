# ⚠️ DEPRECATED - Use Lightsail Deployment Instead

## 🚨 Important Notice

**This deployment guide is for AWS ECS/ECR which is not your current setup!**

Your Meme Maker application uses:
- ✅ **Amazon Lightsail** hosting
- ✅ **Local file storage** (no S3)
- ✅ **Docker Compose** deployment

**👉 Use the correct guide**: `live-deployment-lightsail.md`

---

## Why This Guide Exists

This was created assuming AWS ECS deployment, but your application actually uses a much simpler Lightsail setup with local storage.

---

## 🎯 Immediate Solutions

### Option A: Switch to Main Branch (Recommended)
```powershell
# Create and switch to main branch
git checkout -b main

# Push to origin and set upstream
git push -u origin main

# Go to GitHub → Settings → Branches → Change default branch to 'main'
```

### Option B: Update Workflow Files
Update these files to use `master` instead of `main`:
- `.github/workflows/ci-cd.yml` (lines 4, 6)
- `.github/workflows/ci-cd-oidc.yml` (lines 4, 6)
- `.github/workflows/terraform.yml` (lines 4, 8)

---

## 📋 Complete Deployment Roadmap

### Phase 1: Repository & Branch Setup ⚡ URGENT

1. **Fix Branch Mismatch**
   ```powershell
   # Choose one approach and execute
   git checkout -b main && git push -u origin main
   ```

2. **Verify Repository Structure**
   - ✅ GitHub Actions workflows exist
   - ✅ Terraform infrastructure code ready
   - ✅ Docker configurations present
   - ✅ Application code functional

### Phase 2: AWS Infrastructure Setup

#### 2.1 Prerequisites Checklist
- [ ] AWS Account with billing enabled
- [ ] AWS CLI installed and configured
- [ ] Domain name (optional but recommended)
- [ ] Cloudflare account (for domain management)

#### 2.2 AWS Resource Requirements
```bash
# Create Terraform state bucket
BUCKET_NAME="meme-maker-terraform-state-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME
aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled
```

#### 2.3 Network Requirements
- **VPC**: Existing or new VPC with internet gateway
- **Subnets**: Minimum 2 public + 2 private subnets in different AZs
- **Security Groups**: ALB, ECS, and Redis access rules

### Phase 3: GitHub Secrets & Variables Configuration

#### 3.1 Required Secrets
Navigate to: `GitHub Repository → Settings → Secrets and variables → Actions → Secrets`

```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
CF_API_TOKEN=...  (Optional, for custom domain)
```

#### 3.2 Required Variables
Navigate to: `GitHub Repository → Settings → Secrets and variables → Actions → Variables`

```
AWS_REGION=ap-south-1
AWS_ACCOUNT_ID=123456789012
TF_STATE_BUCKET=meme-maker-terraform-state-1234567890
VPC_ID=vpc-xxxxxxxxx
PUBLIC_SUBNETS="subnet-xxx,subnet-yyy"
PRIVATE_SUBNETS="subnet-aaa,subnet-bbb"
ENVIRONMENT=prod
ECS_CLUSTER=clip-downloader-prod
BACKEND_SERVICE=clip-downloader-backend-prod
WORKER_SERVICE=clip-downloader-worker-prod

# Optional (Custom Domain)
DOMAIN_NAME=yourdomain.com
CLOUDFLARE_ZONE_ID=xxxxxxxxxx
GITHUB_REPOSITORY=subszero0/Meme-Maker
```

### Phase 4: Infrastructure Deployment

#### 4.1 Terraform State Backend Setup
Create `infra/terraform/terraform.tfvars`:
```hcl
aws_region = "ap-south-1"
environment = "prod"
vpc_id = "vpc-xxxxxxxxx"
public_subnets = ["subnet-xxx", "subnet-yyy"]
private_subnets = ["subnet-aaa", "subnet-bbb"]
domain_name = "yourdomain.com"  # Optional
cloudflare_zone_id = "xxxxxxxxxx"  # Optional
github_repository = "subszero0/Meme-Maker"
```

#### 4.2 Local Terraform Testing (Optional)
```powershell
cd infra/terraform
terraform init -backend-config="bucket=your-state-bucket" -backend-config="key=clip-downloader/terraform.tfstate" -backend-config="region=ap-south-1"
terraform plan -var-file="terraform.tfvars"
cd ../..
```

#### 4.3 Deploy Infrastructure
```powershell
git add .
git commit -m "Configure production infrastructure"
git push origin main  # Triggers terraform.yml workflow
```

### Phase 5: Application Deployment

#### 5.1 Environment Configuration

**Development vs Production Differences:**

| Aspect | Development | Production |
|--------|-------------|------------|
| Docker Compose | `docker-compose.dev.yaml` | `docker-compose.yaml` |
| Branch Trigger | Manual/local | `main` branch push |
| Environment | `ENVIRONMENT=development` | `ENVIRONMENT=production` |
| Debug Mode | `DEBUG=true` | `DEBUG=false` |
| CORS | `CORS_ORIGINS=*` | Specific domains |
| SSL/TLS | HTTP only | HTTPS with certificates |
| Storage | Local volumes | EFS/Local with backup |
| Monitoring | Optional | Comprehensive logging |

#### 5.2 Deploy Application
```powershell
# Ensure all changes are committed
git add .
git commit -m "Deploy application to production"
git push origin main  # Triggers ci-cd.yml or ci-cd-oidc.yml
```

#### 5.3 Monitor Deployment
1. **GitHub Actions**: Monitor workflow progress
2. **AWS ECS**: Check service health and tasks
3. **CloudWatch**: Review logs for errors
4. **ALB**: Test load balancer health

### Phase 6: Production Configuration

#### 6.1 Backend Configuration
```yaml
# Automatically set by ECS task definition
ENVIRONMENT=production
REDIS_URL=redis://elasticache-endpoint:6379
STORAGE_BACKEND=local
BASE_URL=https://api.yourdomain.com
CORS_ORIGINS=["https://yourdomain.com"]
```

#### 6.2 Frontend Configuration  
```yaml
# Built into container during CI/CD
NODE_ENV=production
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_ENVIRONMENT=production
VITE_APP_VERSION=${GITHUB_SHA}
```

#### 6.3 Worker Configuration
```yaml
# ECS task environment
REDIS_URL=redis://elasticache-endpoint:6379
STORAGE_BACKEND=local
MAX_CONCURRENT_JOBS=20
JOB_TIMEOUT=300
```

---

## 🔧 Authentication Methods

### Method A: OIDC (Recommended)
**Advantages**: No long-term credentials, better security
**Setup**: 
1. Set `GITHUB_REPOSITORY` variable
2. Ensure `ci-cd-oidc.yml` is active
3. Disable `ci-cd.yml`

### Method B: IAM User
**Advantages**: Simpler setup
**Setup**:
1. Create AWS access keys
2. Store in GitHub secrets
3. Ensure `ci-cd.yml` is active
4. Disable `ci-cd-oidc.yml`

---

## 🚦 Deployment Monitoring & Verification

### 6.1 Health Checks
```bash
# Application health
curl -f https://api.yourdomain.com/health

# Without domain (using ALB DNS)
curl -f http://clip-downloader-alb-1234567890.ap-south-1.elb.amazonaws.com/health

# Test video processing
curl -X POST https://api.yourdomain.com/jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### 6.2 Monitoring Stack
- **Application Logs**: AWS CloudWatch
- **Metrics**: Prometheus (optional)
- **Dashboards**: Grafana (optional)
- **Alerts**: CloudWatch Alarms

### 6.3 Key Performance Indicators
- **Response Time**: < 2 seconds
- **Error Rate**: < 1%
- **Video Processing Success**: > 95%
- **Resource Utilization**: CPU < 70%, Memory < 80%

---

## 🛠️ Troubleshooting Guide

### Common Issues & Solutions

#### 1. CI/CD Pipeline Not Triggering
**Issue**: No GitHub Actions running after push
**Solutions**:
- Check branch name (main vs master)
- Verify workflow files are in `.github/workflows/`
- Check repository permissions

#### 2. Infrastructure Deployment Fails
**Issue**: Terraform errors during deployment
**Common Causes**:
- Incorrect VPC/subnet IDs
- AWS permission issues
- Resource limits exceeded
**Solutions**:
- Verify AWS credentials
- Check variable values
- Review CloudWatch logs

#### 3. ECS Service Fails to Start
**Issue**: Tasks keep stopping/restarting
**Common Causes**:
- Insufficient memory/CPU
- Environment variable errors
- Health check failures
**Solutions**:
- Check ECS task logs
- Increase resource allocation
- Verify environment variables

#### 4. Application Not Accessible
**Issue**: ALB health checks failing
**Common Causes**:
- Security group rules
- Target group configuration
- Application startup errors
**Solutions**:
- Check security groups allow HTTP/HTTPS
- Verify target group health
- Review application logs

---

## 🚀 Quick Start Checklist

### Immediate Actions (Next 30 minutes)

1. **Fix Branch Issue** ⚡
   ```powershell
   git checkout -b main
   git push -u origin main
   ```

2. **Set GitHub Secrets** (5 minutes)
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY  
   - CF_API_TOKEN (optional)

3. **Set GitHub Variables** (10 minutes)
   - AWS_REGION, AWS_ACCOUNT_ID
   - VPC_ID, PUBLIC_SUBNETS, PRIVATE_SUBNETS
   - TF_STATE_BUCKET
   - Service names and cluster name

4. **Trigger Deployment** (1 minute)
   ```powershell
   git push origin main
   ```

### Expected Timeline

- **Infrastructure Deployment**: 15-20 minutes
- **Application Build & Deploy**: 10-15 minutes  
- **Health Check Stabilization**: 3-5 minutes
- **Total Time**: 30-40 minutes for first deployment

---

## 🔄 Updating Production

### Code Changes
```powershell
# Make your changes
git add .
git commit -m "Feature: description of changes"
git push origin main  # Automatic deployment
```

### Infrastructure Changes
```powershell
# Modify terraform files
git add infra/
git commit -m "Infrastructure: update description"
git push origin main  # Automatic infrastructure update
```

### Emergency Rollback
```bash
# Find previous task definition
aws ecs list-task-definitions --family-prefix clip-downloader-backend-prod

# Rollback service
aws ecs update-service \
  --cluster clip-downloader-prod \
  --service clip-downloader-backend-prod \
  --task-definition arn:aws:ecs:region:account:task-definition/name:revision
```

---

## 📊 Production Operations

### Daily Monitoring
- Check ECS service health
- Review CloudWatch logs for errors
- Monitor resource utilization
- Verify application performance

### Weekly Reviews  
- Analyze usage patterns
- Review security logs
- Update dependencies
- Performance optimization

### Monthly Maintenance
- Review and rotate access keys
- Update infrastructure as needed
- Backup critical data
- Security audit

---

## 🎯 Success Criteria

Your deployment is successful when:
- ✅ GitHub Actions workflows complete without errors
- ✅ ECS services are running and healthy
- ✅ ALB health checks pass
- ✅ Application responds to API calls
- ✅ Video processing completes successfully
- ✅ Frontend loads and functions properly

**Next Steps After Successful Deployment:**
1. Test with real YouTube URLs
2. Monitor for 24 hours
3. Set up alerting
4. Document any customizations
5. Train team on operational procedures

---

## 📞 Support & Resources

- **GitHub Repository**: https://github.com/subszero0/Meme-Maker
- **AWS Documentation**: ECS, ALB, ElastiCache
- **Terraform Documentation**: AWS Provider
- **Troubleshooting**: Check CloudWatch logs first
- **Performance Issues**: Monitor ECS metrics and Redis

**Remember**: First deployment takes longer due to image builds and AWS resource creation. Subsequent deployments are much faster (5-10 minutes).
