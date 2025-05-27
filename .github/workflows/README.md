# GitHub Actions Workflows

This directory contains the GitHub Actions workflows for the Meme Maker project.

## Available Workflows

### 1. CI/CD Pipeline with IAM User (`ci-cd.yml`)
Uses IAM user credentials stored as GitHub secrets.

### 2. CI/CD Pipeline with OIDC (`ci-cd-oidc.yml`)  
Uses GitHub OIDC for secure authentication without storing long-term credentials.

## Workflow Jobs

Both workflows include the same three jobs:

1. **lint-test**: Runs linting and tests for frontend, backend, and Terraform
2. **build-push-ecr**: Builds and pushes Docker images to ECR (main branch only)
3. **deploy-ecs**: Deploys new images to ECS services (main branch only)

## Authentication Setup

### Option 1: IAM User Authentication (`ci-cd.yml`)

#### Required Secrets
- `AWS_ACCESS_KEY_ID`: Access key for the CI/CD IAM user
- `AWS_SECRET_ACCESS_KEY`: Secret key for the CI/CD IAM user

#### Setup Steps
1. Deploy your infrastructure using Terraform
2. Create access keys for the CI user:
   ```bash
   aws iam create-access-key --user-name clip-downloader-ci-deploy-dev
   ```
3. Add the access key ID and secret to GitHub secrets

### Option 2: OIDC Authentication (`ci-cd-oidc.yml`) - **Recommended**

#### Required Variables
- `CI_DEPLOY_ROLE_ARN`: ARN of the GitHub Actions OIDC role (output from Terraform)

#### Setup Steps
1. Set the `github_repository` variable in your Terraform configuration:
   ```hcl
   github_repository = "your-username/meme-maker"
   ```
2. Deploy your infrastructure using Terraform
3. Add the `CI_DEPLOY_ROLE_ARN` variable to GitHub repository variables using the output from Terraform

#### Benefits of OIDC
- ✅ No long-term credentials stored in GitHub
- ✅ Better security posture
- ✅ Automatic credential rotation
- ✅ Principle of least privilege with temporary tokens

## Required Variables (Both Workflows)

Add these variables in your GitHub repository settings (`Settings` → `Secrets and variables` → `Actions` → `Variables`):

- `AWS_REGION`: AWS region (e.g., `us-east-1`)
- `AWS_ACCOUNT_ID`: Your AWS account ID
- `ECS_CLUSTER`: ECS cluster name (e.g., `clip-downloader-dev`)
- `BACKEND_SERVICE`: Backend ECS service name (e.g., `clip-downloader-backend-dev`)
- `WORKER_SERVICE`: Worker ECS service name (e.g., `clip-downloader-worker-dev`)

## ECR Repository Naming

The workflows expect ECR repositories to be named:
- `clip/backend`
- `clip/worker`

These are created automatically by the Terraform infrastructure.

## Features

- **Caching**: Docker layer caching for faster builds
- **Parallel execution**: Linting and testing run in parallel
- **Job summaries**: Rich summaries with deployment status
- **Health checks**: Validates ALB health endpoint after deployment
- **Error handling**: Fails fast with proper error messages
- **Security**: Uses minimal AWS permissions

## Local Testing

To test the workflow locally using [act](https://github.com/nektos/act):

```bash
# Install act
# On macOS: brew install act
# On Windows: choco install act-cli

# Test the lint-test job
act pull_request -j lint-test

# Test with secrets (create .secrets file first)
act push -j lint-test --secret-file .secrets
```

## Switching Between Authentication Methods

### To use IAM User authentication:
1. Rename or disable `ci-cd-oidc.yml`
2. Ensure `ci-cd.yml` is active
3. Set up AWS access keys as secrets

### To use OIDC authentication:
1. Rename or disable `ci-cd.yml`
2. Ensure `ci-cd-oidc.yml` is active
3. Set the `github_repository` variable in Terraform
4. Redeploy infrastructure
5. Set the `CI_DEPLOY_ROLE_ARN` variable

## Troubleshooting

### Common Issues

1. **ECR login fails**: Check AWS credentials and ECR repository existence
2. **Task definition update fails**: Verify ECS service names and cluster name
3. **Health check fails**: Check ALB configuration and backend health endpoint
4. **Docker build fails**: Check Dockerfile syntax and build context
5. **OIDC authentication fails**: Verify repository name and role ARN

### Debug Steps

1. Check the job logs in GitHub Actions
2. Verify AWS credentials have correct permissions
3. Ensure ECR repositories exist and are properly named
4. Check ECS services are running and accessible
5. For OIDC: Verify the trust relationship and repository permissions

### Workflow Outputs

The workflows provide detailed summaries including:
- Lint and test results
- Built image tags
- Deployment status
- Health check results
- Service update confirmations 