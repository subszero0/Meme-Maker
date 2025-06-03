#!/bin/bash
# AWS Production Environment Provisioning Script
# Creates S3 bucket, Route 53 records, and IAM user for Meme Maker production deployment

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

# AWS Configuration
AWS_REGION="${AWS_REGION:-ap-south-1}"
S3_BUCKET_NAME="${S3_BUCKET_NAME:-memeit-prod-bucket}"
DOMAIN_NAME="${DOMAIN_NAME:-memeit.pro}"
IAM_USER_NAME="${IAM_USER_NAME:-memeit-prod-app}"

# Get Lightsail IP from user input
if [ -z "${LIGHTSAIL_IP:-}" ]; then
    echo "Please enter your Lightsail static IP address:"
    read -r LIGHTSAIL_IP
fi

# CloudFront Distribution ID (will be created separately)
if [ -z "${CLOUDFRONT_DIST_ID:-}" ]; then
    echo "Please enter your CloudFront Distribution ID (or 'skip' to create policies without it):"
    read -r CLOUDFRONT_DIST_ID
fi

echo "============================================================================"
echo "AWS Production Provisioning for Meme Maker"
echo "============================================================================"
echo "Region: $AWS_REGION"
echo "S3 Bucket: $S3_BUCKET_NAME"
echo "Domain: $DOMAIN_NAME"
echo "Lightsail IP: $LIGHTSAIL_IP"
echo "IAM User: $IAM_USER_NAME"
echo "============================================================================"

# ============================================================================
# STEP 1: CREATE S3 BUCKET
# ============================================================================

echo "📦 Creating S3 bucket: $S3_BUCKET_NAME"

# Create the bucket
aws s3api create-bucket \
    --bucket "$S3_BUCKET_NAME" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION"

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket "$S3_BUCKET_NAME" \
    --versioning-configuration Status=Enabled

# Block all public access (private bucket)
aws s3api put-public-access-block \
    --bucket "$S3_BUCKET_NAME" \
    --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Enable server-side encryption
aws s3api put-bucket-encryption \
    --bucket "$S3_BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }'

# Create lifecycle policy for 30-day deletion of old objects
aws s3api put-bucket-lifecycle-configuration \
    --bucket "$S3_BUCKET_NAME" \
    --lifecycle-configuration '{
        "Rules": [
            {
                "ID": "DeleteOldObjects",
                "Status": "Enabled",
                "Filter": {},
                "Expiration": {
                    "Days": 30
                },
                "NoncurrentVersionExpiration": {
                    "NoncurrentDays": 7
                }
            }
        ]
    }'

echo "✅ S3 bucket created and configured"

# ============================================================================
# STEP 2: CREATE IAM POLICY AND USER
# ============================================================================

echo "👤 Creating IAM user: $IAM_USER_NAME"

# Create IAM policy document
POLICY_DOC='{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3BucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::'$S3_BUCKET_NAME'"
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
            "Resource": "arn:aws:s3:::'$S3_BUCKET_NAME'/*"
        }'

# Add CloudFront permissions if distribution ID provided
if [ "$CLOUDFRONT_DIST_ID" != "skip" ]; then
    POLICY_DOC+=',
        {
            "Sid": "CloudFrontInvalidation",
            "Effect": "Allow",
            "Action": [
                "cloudfront:CreateInvalidation"
            ],
            "Resource": "arn:aws:cloudfront::*:distribution/'$CLOUDFRONT_DIST_ID'"
        }'
fi

POLICY_DOC+='
    ]
}'

# Create IAM policy
POLICY_ARN=$(aws iam create-policy \
    --policy-name "MemeIt-Prod-S3-CloudFront-Policy" \
    --policy-document "$POLICY_DOC" \
    --description "Production policy for Meme Maker S3 and CloudFront access" \
    --query 'Policy.Arn' \
    --output text)

echo "✅ IAM policy created: $POLICY_ARN"

# Create IAM user
aws iam create-user \
    --user-name "$IAM_USER_NAME" \
    --path "/applications/"

# Attach policy to user
aws iam attach-user-policy \
    --user-name "$IAM_USER_NAME" \
    --policy-arn "$POLICY_ARN"

# Create access keys
ACCESS_KEY_RESULT=$(aws iam create-access-key \
    --user-name "$IAM_USER_NAME" \
    --output json)

ACCESS_KEY_ID=$(echo "$ACCESS_KEY_RESULT" | jq -r '.AccessKey.AccessKeyId')
SECRET_ACCESS_KEY=$(echo "$ACCESS_KEY_RESULT" | jq -r '.AccessKey.SecretAccessKey')

echo "✅ IAM user created with programmatic access"

# ============================================================================
# STEP 3: CREATE ROUTE 53 RECORDS
# ============================================================================

echo "🌐 Setting up Route 53 DNS records"

# Get the hosted zone ID for the domain
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --dns-name "$DOMAIN_NAME" \
    --query "HostedZones[?Name=='${DOMAIN_NAME}.'].Id" \
    --output text | cut -d'/' -f3)

if [ -z "$HOSTED_ZONE_ID" ]; then
    echo "❌ Error: Hosted zone for $DOMAIN_NAME not found. Please create it first in Route 53."
    exit 1
fi

echo "Found hosted zone: $HOSTED_ZONE_ID"

# Create change batch for DNS records
CHANGE_BATCH='{
    "Changes": [
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "'$DOMAIN_NAME'",
                "Type": "A",
                "TTL": 300,
                "ResourceRecords": [
                    {
                        "Value": "'$LIGHTSAIL_IP'"
                    }
                ]
            }
        },
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "www.'$DOMAIN_NAME'",
                "Type": "A",
                "TTL": 300,
                "ResourceRecords": [
                    {
                        "Value": "'$LIGHTSAIL_IP'"
                    }
                ]
            }
        }
    ]
}'

# Apply DNS changes
CHANGE_ID=$(aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch "$CHANGE_BATCH" \
    --query 'ChangeInfo.Id' \
    --output text)

echo "✅ DNS records created. Change ID: $CHANGE_ID"

# ============================================================================
# STEP 4: OUTPUT CONFIGURATION VALUES
# ============================================================================

echo ""
echo "🎉 AWS provisioning completed successfully!"
echo ""
echo "============================================================================"
echo "CONFIGURATION VALUES FOR .env.prod"
echo "============================================================================"
echo ""
echo "# Core"
echo "DOMAIN=$DOMAIN_NAME"
echo "LIGHTSAIL_SERVER_IP=$LIGHTSAIL_IP"
echo ""
echo "# AWS/S3"
echo "AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID"
echo "AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY"
echo "AWS_REGION=$AWS_REGION"
echo "S3_BUCKET_NAME=$S3_BUCKET_NAME"
echo ""
echo "# Route 53"
echo "ROUTE53_ZONE_ID=$HOSTED_ZONE_ID"
echo ""
if [ "$CLOUDFRONT_DIST_ID" != "skip" ]; then
    echo "# CloudFront"
    echo "CLOUDFRONT_DOMAIN=<get-from-cloudfront-console>"
fi
echo ""
echo "============================================================================"
echo "SECURITY REMINDERS"
echo "============================================================================"
echo "1. Store these credentials in AWS Secrets Manager or Lightsail Environment Variables"
echo "2. Do NOT commit these values to source control"
echo "3. The IAM user has minimal permissions (least privilege principle)"
echo "4. S3 bucket is private with versioning and lifecycle rules enabled"
echo "5. DNS propagation may take up to 48 hours"
echo ""
echo "Next steps:"
echo "1. Update your .env.prod file with these values"
echo "2. Test DNS propagation: dig $DOMAIN_NAME"
echo "3. Set up CloudFront distribution if not done already"
echo "============================================================================" 