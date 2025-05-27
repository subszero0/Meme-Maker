terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.1"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = ">= 4.0"
    }
  }

  backend "s3" {
    # Configure with:
    # terraform init -backend-config="bucket=your-terraform-state-bucket" \
    #                -backend-config="key=clip-downloader/terraform.tfstate" \
    #                -backend-config="region=ap-south-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project = "clip-downloader"
      ManagedBy = "terraform"
    }
  }
}

# AWS provider for us-east-1 (required for ACM certificates for ALB)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project = "clip-downloader"
      ManagedBy = "terraform"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
} 