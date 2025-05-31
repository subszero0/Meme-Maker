# IAM Role and Policy for Meme Maker Worker/Backend
# Provides S3 access permissions for video processing

# IAM Role for the worker and backend services
resource "aws_iam_role" "worker_backend" {
  name = "${var.project_name}-worker-backend-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "ecs-tasks.amazonaws.com",
            "ec2.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-worker-backend-role"
    Environment = var.env
    Project     = var.project_name
    Purpose     = "S3AccessForVideoProcessing"
  }
}

# Inline policy for S3 access to the clips bucket
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project_name}-s3-access-${var.env}"
  role = aws_iam_role.worker_backend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject", 
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.clips.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.clips.arn
      }
    ]
  })
}

# Optional: Instance profile for EC2-based deployments
resource "aws_iam_instance_profile" "worker_backend" {
  name = "${var.project_name}-worker-backend-${var.env}"
  role = aws_iam_role.worker_backend.name

  tags = {
    Name        = "${var.project_name}-worker-backend-profile"
    Environment = var.env
    Project     = var.project_name
  }
} 