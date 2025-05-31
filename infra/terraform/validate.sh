#!/bin/bash
# Terraform Validation Script for Meme Maker Infrastructure
# Validates Terraform configuration and checks deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TERRAFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_VAR_FILE="${TERRAFORM_DIR}/terraform.tfvars"

echo -e "${BLUE}🔍 Meme Maker Infrastructure Validation${NC}"
echo "========================================"
echo

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    else
        echo -e "${RED}❌ $message${NC}"
    fi
}

# Check if running in correct directory
echo -e "${BLUE}1. Environment Check${NC}"
if [ ! -f "main.tf" ]; then
    print_status "ERROR" "Not in terraform directory. Please run from infra/terraform/"
    exit 1
fi
print_status "OK" "Running from correct directory"

# Check Terraform installation
if ! command -v terraform &> /dev/null; then
    print_status "ERROR" "Terraform not installed"
    exit 1
fi

TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version')
print_status "OK" "Terraform installed (version: $TERRAFORM_VERSION)"

# Check minimum version
REQUIRED_VERSION="1.5.0"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$TERRAFORM_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_status "ERROR" "Terraform version $TERRAFORM_VERSION < required $REQUIRED_VERSION"
    exit 1
fi
print_status "OK" "Terraform version meets requirements"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_status "WARN" "AWS CLI not installed (optional for validation)"
else
    AWS_IDENTITY=$(aws sts get-caller-identity 2>/dev/null || echo "")
    if [ -n "$AWS_IDENTITY" ]; then
        AWS_ACCOUNT=$(echo "$AWS_IDENTITY" | jq -r '.Account')
        AWS_USER=$(echo "$AWS_IDENTITY" | jq -r '.Arn')
        print_status "OK" "AWS credentials configured (Account: $AWS_ACCOUNT)"
    else
        print_status "WARN" "AWS credentials not configured"
    fi
fi

echo

# Check Terraform configuration files
echo -e "${BLUE}2. Configuration Files${NC}"

required_files=("main.tf" "variables.tf" "outputs.tf" "s3.tf" "iam.tf" "route53.tf" "versions.tf")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_status "OK" "$file exists"
    else
        print_status "ERROR" "$file missing"
    fi
done

# Check for terraform.tfvars
if [ -f "$TERRAFORM_VAR_FILE" ]; then
    print_status "OK" "terraform.tfvars exists"
else
    print_status "WARN" "terraform.tfvars not found (using defaults)"
fi

echo

# Terraform validation
echo -e "${BLUE}3. Terraform Validation${NC}"

# Initialize if needed
if [ ! -d ".terraform" ]; then
    echo "Initializing Terraform..."
    terraform init -backend=false > /dev/null 2>&1
fi

# Format check
echo "Checking formatting..."
if terraform fmt -check > /dev/null 2>&1; then
    print_status "OK" "Code formatting is correct"
else
    print_status "WARN" "Code needs formatting (run: terraform fmt)"
fi

# Validate configuration
echo "Validating configuration..."
if terraform validate > /dev/null 2>&1; then
    print_status "OK" "Configuration is valid"
else
    print_status "ERROR" "Configuration validation failed"
    terraform validate
    exit 1
fi

# Plan check (if variables exist)
if [ -f "$TERRAFORM_VAR_FILE" ]; then
    echo "Running terraform plan..."
    if terraform plan -var-file="$TERRAFORM_VAR_FILE" -out=validation.tfplan > /dev/null 2>&1; then
        print_status "OK" "Plan generation successful"
        
        # Show plan summary
        PLAN_SUMMARY=$(terraform show -json validation.tfplan 2>/dev/null | jq -r '.resource_changes | length')
        if [ "$PLAN_SUMMARY" != "null" ] && [ "$PLAN_SUMMARY" -gt 0 ]; then
            print_status "OK" "Plan shows $PLAN_SUMMARY resource changes"
        else
            print_status "OK" "No resource changes planned"
        fi
        
        # Clean up plan file
        rm -f validation.tfplan
    else
        print_status "ERROR" "Plan generation failed"
        terraform plan -var-file="$TERRAFORM_VAR_FILE"
        exit 1
    fi
else
    print_status "WARN" "Skipping plan check (no terraform.tfvars)"
fi

echo

# Variable validation
echo -e "${BLUE}4. Variable Validation${NC}"

if [ -f "$TERRAFORM_VAR_FILE" ]; then
    # Check required variables
    required_vars=("project_name" "env" "aws_region")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}[[:space:]]*=" "$TERRAFORM_VAR_FILE"; then
            VALUE=$(grep "^${var}[[:space:]]*=" "$TERRAFORM_VAR_FILE" | cut -d'=' -f2 | tr -d ' "')
            print_status "OK" "$var = $VALUE"
        else
            print_status "ERROR" "$var not defined in terraform.tfvars"
        fi
    done
    
    # Check optional DNS variables
    optional_vars=("domain" "lb_dns" "route53_zone_id" "create_route53_record")
    for var in "${optional_vars[@]}"; do
        if grep -q "^${var}[[:space:]]*=" "$TERRAFORM_VAR_FILE"; then
            VALUE=$(grep "^${var}[[:space:]]*=" "$TERRAFORM_VAR_FILE" | cut -d'=' -f2 | tr -d ' "')
            print_status "OK" "$var = $VALUE (optional)"
        fi
    done
else
    print_status "WARN" "No terraform.tfvars file to validate"
fi

echo

# Security validation
echo -e "${BLUE}5. Security Validation${NC}"

# Check for hardcoded secrets
if grep -r "AKIA\|aws_access_key\|aws_secret_key" . --exclude-dir=.terraform --exclude="*.md" 2>/dev/null | grep -v "example\|template"; then
    print_status "ERROR" "Hardcoded AWS credentials found in configuration"
else
    print_status "OK" "No hardcoded AWS credentials found"
fi

# Check for proper tagging
if grep -q "Environment.*var.env" *.tf && grep -q "Project.*var.project_name" *.tf; then
    print_status "OK" "Resource tagging configured properly"
else
    print_status "WARN" "Resource tagging may be incomplete"
fi

# Check S3 bucket security
if grep -q "block_public_acls.*true" s3.tf && grep -q "server_side_encryption" s3.tf; then
    print_status "OK" "S3 security settings configured"
else
    print_status "ERROR" "S3 security settings missing"
fi

echo

# Post-deployment validation (if state exists)
echo -e "${BLUE}6. Deployment Validation${NC}"

if [ -f "terraform.tfstate" ] || [ -d ".terraform" ] && terraform state list > /dev/null 2>&1; then
    echo "Checking deployed resources..."
    
    # Check if resources exist in state
    RESOURCE_COUNT=$(terraform state list 2>/dev/null | wc -l)
    if [ "$RESOURCE_COUNT" -gt 0 ]; then
        print_status "OK" "$RESOURCE_COUNT resources in state"
        
        # Test outputs
        if terraform output bucket_name > /dev/null 2>&1; then
            BUCKET_NAME=$(terraform output -raw bucket_name 2>/dev/null)
            print_status "OK" "S3 bucket: $BUCKET_NAME"
        fi
        
        if terraform output role_arn > /dev/null 2>&1; then
            ROLE_ARN=$(terraform output -raw role_arn 2>/dev/null)
            print_status "OK" "IAM role: $ROLE_ARN"
        fi
        
        # Test AWS connectivity if credentials available
        if command -v aws &> /dev/null && aws sts get-caller-identity > /dev/null 2>&1; then
            if [ -n "$BUCKET_NAME" ] && aws s3api head-bucket --bucket "$BUCKET_NAME" > /dev/null 2>&1; then
                print_status "OK" "S3 bucket accessible via AWS CLI"
            else
                print_status "WARN" "S3 bucket not accessible (may not be deployed)"
            fi
        fi
    else
        print_status "WARN" "No resources deployed yet"
    fi
else
    print_status "WARN" "No Terraform state found (not deployed yet)"
fi

echo

# Summary
echo -e "${BLUE}7. Validation Summary${NC}"
echo "Infrastructure validation completed."
echo
echo "Next steps:"
echo "1. If validation passed: terraform apply -var-file=\"terraform.tfvars\""
echo "2. If issues found: Review and fix the reported problems"
echo "3. For production: Set up remote state backend"
echo
echo "Documentation: README.md"
echo 