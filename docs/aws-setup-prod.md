# AWS Production Setup Guide (Console)

This document provides step-by-step instructions for setting up AWS resources for Meme Maker production deployment using the AWS Console (GUI).

## Overview

You'll create:
- **S3 Bucket**: `memeit-prod-bucket` (private, versioned, with lifecycle rules)
- **Route 53 Records**: A-records for `memeit.pro` and `www.memeit.pro`
- **IAM User**: `memeit-prod-app` with least-privilege permissions

## Prerequisites

- AWS Account with administrative access
- Domain `memeit.pro` registered (can be through Route 53 or external registrar)
- Lightsail instance running with static IP assigned

---

## Step 1: Create S3 Bucket

### 1.1 Create Bucket
1. Go to **AWS Console** → **S3**
2. Click **"Create bucket"**
3. **Bucket name**: `memeit-prod-bucket`
4. **AWS Region**: Select `Asia Pacific (Mumbai) ap-south-1` (same as your Lightsail)
5. **Object Ownership**: Keep default (ACLs disabled)
6. Click **"Create bucket"**

### 1.2 Configure Security (Block Public Access)
1. Select your bucket → **Permissions** tab
2. **Block public access**: Ensure all 4 checkboxes are ✅ checked
3. If not, click **"Edit"** → Check all boxes → **"Save changes"**

### 1.3 Enable Versioning
1. In your bucket → **Properties** tab
2. Find **"Bucket Versioning"** → Click **"Edit"**
3. Select **"Enable"** → **"Save changes"**

### 1.4 Enable Encryption
1. Still in **Properties** tab
2. Find **"Default encryption"** → Click **"Edit"**
3. Select **"Server-side encryption with Amazon S3 managed keys (SSE-S3)"**
4. Click **"Save changes"**

### 1.5 Set Up Lifecycle Rules
1. In your bucket → **Management** tab
2. Click **"Create lifecycle rule"**
3. **Rule name**: `DeleteOldObjects`
4. **Rule scope**: Apply to all objects
5. **Lifecycle rule actions**: Check both:
   - ✅ Delete expired object delete markers or incomplete multipart uploads
   - ✅ Delete previous versions of objects
6. **Delete previous versions**: Set to `7 days`
7. **Delete expired delete markers**: Check this
8. **Delete incomplete multipart uploads**: Set to `1 day`
9. Click **"Create rule"**

---

## Step 2: Create IAM User and Policy

### 2.1 Create IAM Policy
1. Go to **AWS Console** → **IAM** → **Policies**
2. Click **"Create policy"**
3. Click **"JSON"** tab
4. Paste this policy (replace `CLOUDFRONT_DIST_ID` with your actual ID):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3BucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::memeit-prod-bucket"
        },
        {
            "Sid": "S3ObjectAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectVersion",
                "s3:DeleteObjectVersion"
            ],
            "Resource": "arn:aws:s3:::memeit-prod-bucket/*"
        },
        {
            "Sid": "CloudFrontInvalidation",
            "Effect": "Allow",
            "Action": [
                "cloudfront:CreateInvalidation"
            ],
            "Resource": "arn:aws:cloudfront::*:distribution/YOUR_CLOUDFRONT_DIST_ID"
        }
    ]
}
```

5. Click **"Next"**
6. **Policy name**: `MemeIt-Prod-S3-CloudFront-Policy`
7. **Description**: `Production policy for Meme Maker S3 and CloudFront access`
8. Click **"Create policy"**

### 2.2 Create IAM User
1. Go to **IAM** → **Users**
2. Click **"Create user"**
3. **User name**: `memeit-prod-app`
4. **Select AWS access type**: Check ✅ **"Programmatic access"**
5. Click **"Next: Permissions"**
6. Click **"Attach existing policies directly"**
7. Search for `MemeIt-Prod-S3-CloudFront-Policy` and select it
8. Click **"Next: Tags"** (skip tags)
9. Click **"Next: Review"**
10. Click **"Create user"**

### 2.3 Save Access Keys
⚠️ **IMPORTANT**: Copy and save these immediately (you won't see them again):
- **Access key ID**: `AKIAIOSFODNN7EXAMPLE`
- **Secret access key**: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

---

## Step 3: Set Up Route 53 DNS

### 3.1 Create Hosted Zone (if not exists)
1. Go to **AWS Console** → **Route 53** → **Hosted zones**
2. If `memeit.pro` doesn't exist:
   - Click **"Create hosted zone"**
   - **Domain name**: `memeit.pro`
   - **Type**: Public hosted zone
   - Click **"Create hosted zone"**
3. **Copy the NS records** and update your domain registrar

### 3.2 Create A Records
1. Click on your `memeit.pro` hosted zone
2. Click **"Create record"**

**For root domain (memeit.pro):**
- **Record name**: Leave blank
- **Record type**: A
- **Value**: Your Lightsail static IP (e.g., `13.126.173.223`)
- **TTL**: 300
- Click **"Create records"**

**For www subdomain:**
- Click **"Create record"** again
- **Record name**: `www`
- **Record type**: A  
- **Value**: Your Lightsail static IP (same as above)
- **TTL**: 300
- Click **"Create records"**

### 3.3 Copy Hosted Zone ID
- In the hosted zone details, copy the **Hosted zone ID** (e.g., `Z0ABCDE12345`)

---

## Step 4: Update .env.prod

Update your `.env.prod` file with these values:

```ini
# ── Core ───────────────────────────────
DOMAIN=memeit.pro
LIGHTSAIL_SERVER_IP=YOUR_LIGHTSAIL_IP

# ── AWS / S3  ─────────────────────────
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_FROM_STEP_2.3
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY_FROM_STEP_2.3
AWS_REGION=ap-south-1
S3_BUCKET_NAME=memeit-prod-bucket

# ── DNS ───────────────────────────────
ROUTE53_ZONE_ID=YOUR_HOSTED_ZONE_ID_FROM_STEP_3.3

# ── CloudFront (if using) ─────────────
CLOUDFRONT_DOMAIN=YOUR_CLOUDFRONT_DOMAIN
```

---

## Step 5: CloudFront Distribution (Optional)

If you want to use CloudFront for CDN:

### 5.1 Create Distribution
1. Go to **CloudFront** → **Distributions**
2. Click **"Create distribution"**
3. **Origin domain**: Your Lightsail static IP or domain
4. **Protocol**: HTTPS only
5. **Allowed HTTP methods**: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
6. **Cache policy**: Managed-CachingDisabled (for dynamic content)
7. **Origin request policy**: Managed-CORS-S3Origin
8. Click **"Create distribution"**

### 5.2 Update DNS (Optional)
- Create CNAME record in Route 53 pointing to CloudFront domain
- Or use CloudFront domain directly in your application

---

## Security Checklist

After completing setup:

- [ ] ✅ S3 bucket has all public access blocked
- [ ] ✅ S3 versioning is enabled
- [ ] ✅ S3 lifecycle rules are configured (30-day deletion)
- [ ] ✅ S3 encryption is enabled
- [ ] ✅ IAM user has minimal permissions (only S3 + CloudFront)
- [ ] ✅ Access keys are stored securely (not in source control)
- [ ] ✅ DNS records point to correct Lightsail IP
- [ ] ✅ `.env.prod` is excluded from Git

## Testing

1. **Test DNS propagation**:
   ```bash
   dig memeit.pro
   dig www.memeit.pro
   ```

2. **Test S3 access** (using AWS CLI with new credentials):
   ```bash
   aws s3 ls s3://memeit-prod-bucket
   ```

3. **Test domain resolution**:
   ```bash
   curl -I http://memeit.pro
   ```

## Troubleshooting

### DNS Issues
- DNS propagation can take up to 48 hours
- Check your domain registrar's NS records match Route 53
- Use online DNS checkers to verify propagation

### S3 Access Issues
- Verify IAM policy has correct bucket ARN
- Check if region matches Lightsail region
- Ensure access keys are correctly configured

### SSL/TLS Issues
- Lightsail provides automatic SSL for static IPs
- Verify domain points to correct IP
- Check Lightsail networking rules allow HTTPS (port 443)

---

## Cost Optimization

- **S3**: Pay only for storage used (lifecycle rules minimize costs)
- **Route 53**: $0.50/month per hosted zone + query costs
- **CloudFront**: Pay-as-you-go for data transfer
- **IAM**: Free

**Expected monthly cost**: < $5-10 for small traffic volumes

---

## Next Steps

1. Verify all resources are created correctly
2. Test your application deployment
3. Set up monitoring and alerts
4. Configure backup and disaster recovery
5. Review security settings periodically 