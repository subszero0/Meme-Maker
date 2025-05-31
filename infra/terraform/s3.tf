# S3 Bucket for Video Clips
# Temporary storage for processed video clips with automatic cleanup

resource "aws_s3_bucket" "clips" {
  bucket = "${var.project_name}-clips-${var.env}-${random_string.suffix.result}"

  tags = {
    Name        = "${var.project_name}-clips-${var.env}"
    Environment = var.env
    Project     = var.project_name
    Purpose     = "VideoClipStorage"
  }
}

# Block all public access to the bucket
resource "aws_s3_bucket_public_access_block" "clips" {
  bucket = aws_s3_bucket.clips.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Disable versioning as specified in requirements
resource "aws_s3_bucket_versioning" "clips" {
  bucket = aws_s3_bucket.clips.id
  
  versioning_configuration {
    status = "Disabled"
  }
}

# Lifecycle rule to delete objects after 1 day (backup to self-destruct)
resource "aws_s3_bucket_lifecycle_configuration" "clips" {
  bucket = aws_s3_bucket.clips.id

  rule {
    id     = "delete-clips-after-1-day"
    status = "Enabled"

    # Delete all objects after 1 day
    expiration {
      days = 1
    }

    # Also clean up any incomplete multipart uploads
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }

  depends_on = [aws_s3_bucket_versioning.clips]
}

# Server-side encryption for security
resource "aws_s3_bucket_server_side_encryption_configuration" "clips" {
  bucket = aws_s3_bucket.clips.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
} 