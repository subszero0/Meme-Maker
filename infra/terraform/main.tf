# Data sources
data "aws_caller_identity" "current" {}

# S3 bucket for clip files
resource "aws_s3_bucket" "clips" {
  bucket = "clip-downloader-files-${var.environment}-${random_string.bucket_suffix.result}"

  tags = {
    Name = "clip-downloader-files"
    Environment = var.environment
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_public_access_block" "clips" {
  bucket = aws_s3_bucket.clips.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "clips" {
  bucket = aws_s3_bucket.clips.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "clips" {
  bucket = aws_s3_bucket.clips.id

  rule {
    id     = "cleanup-clips"
    status = "Enabled"

    expiration {
      days = 1
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }
  }
}

# ElastiCache subnet group
resource "aws_elasticache_subnet_group" "redis" {
  name       = "clip-downloader-redis-${var.environment}"
  subnet_ids = var.private_subnets

  tags = {
    Name = "clip-downloader-redis-subnet-group"
    Environment = var.environment
  }
}

# Security group for Redis
resource "aws_security_group" "redis" {
  name_prefix = "clip-downloader-redis-${var.environment}-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "clip-downloader-redis"
    Environment = var.environment
  }
}

# ElastiCache Redis cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "clip-downloader-${var.environment}"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = {
    Name = "clip-downloader-redis"
    Environment = var.environment
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "clip-downloader-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "clip-downloader-cluster"
    Environment = var.environment
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/clip-downloader-backend-${var.environment}"
  retention_in_days = 7

  tags = {
    Name = "clip-downloader-backend-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/clip-downloader-worker-${var.environment}"
  retention_in_days = 7

  tags = {
    Name = "clip-downloader-worker-logs"
    Environment = var.environment
  }
}

# IAM Role for ECS Tasks
resource "aws_iam_role" "ecs_task_execution" {
  name = "clip-downloader-ecs-task-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Tasks (application permissions)
resource "aws_iam_role" "ecs_task" {
  name = "clip-downloader-ecs-task-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for S3 access
resource "aws_iam_role_policy" "ecs_task_s3" {
  name = "clip-downloader-s3-access-${var.environment}"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectVersion"
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

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy" "ecs_task_logs" {
  name = "clip-downloader-logs-access-${var.environment}"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          aws_cloudwatch_log_group.backend.arn,
          aws_cloudwatch_log_group.worker.arn
        ]
      }
    ]
  })
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name_prefix = "clip-downloader-alb-${var.environment}-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "clip-downloader-alb"
    Environment = var.environment
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "clip-downloader-ecs-${var.environment}-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "clip-downloader-ecs-tasks"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "clip-downloader-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnets

  enable_deletion_protection = var.environment == "prod" ? true : false

  tags = {
    Name = "clip-downloader-alb"
    Environment = var.environment
  }
}

# Target Group for Backend Service
resource "aws_lb_target_group" "backend" {
  name        = "clip-downloader-backend-${var.environment}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = {
    Name = "clip-downloader-backend-tg"
    Environment = var.environment
    Project = "clip-downloader"
  }
}

# ACM Certificate in us-east-1 (required for ALB)
resource "aws_acm_certificate" "main" {
  count           = var.domain_name != "" && var.cloudflare_zone_id != "" ? 1 : 0
  provider        = aws.us_east_1
  domain_name     = "api.${var.domain_name}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "clip-downloader-cert"
    Environment = var.environment
    Project = "clip-downloader"
  }
}

# Cloudflare DNS record for ACM certificate validation
resource "cloudflare_record" "cert_validation" {
  for_each = var.domain_name != "" && var.cloudflare_zone_id != "" ? {
    for dvo in aws_acm_certificate.main[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  zone_id = var.cloudflare_zone_id
  name    = trimsuffix(each.value.name, ".${var.domain_name}.")
  value   = trimsuffix(each.value.record, ".")
  type    = each.value.type
  ttl     = 60

  comment = "ACM certificate validation for ${var.domain_name}"

  depends_on = [aws_acm_certificate.main]
}

# ACM Certificate validation
resource "aws_acm_certificate_validation" "main" {
  count           = var.domain_name != "" && var.cloudflare_zone_id != "" ? 1 : 0
  provider        = aws.us_east_1
  certificate_arn = aws_acm_certificate.main[0].arn
  validation_record_fqdns = [for record in cloudflare_record.cert_validation : record.hostname]

  timeouts {
    create = "5m"
  }

  depends_on = [cloudflare_record.cert_validation]
}

# Cloudflare DNS record for API subdomain
resource "cloudflare_record" "api" {
  count   = var.domain_name != "" && var.cloudflare_zone_id != "" ? 1 : 0
  zone_id = var.cloudflare_zone_id
  name    = "api"
  value   = aws_lb.main.dns_name
  type    = "CNAME"
  ttl     = 300
  proxied = false

  comment = "API subdomain for clip-downloader"

  depends_on = [aws_lb.main]
}

# HTTPS ALB Listener (port 443)
resource "aws_lb_listener" "https" {
  count             = var.domain_name != "" && var.cloudflare_zone_id != "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.main[0].certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  tags = {
    Name = "clip-downloader-https-listener"
    Environment = var.environment
    Project = "clip-downloader"
  }
}

# HTTP ALB Listener (port 80) - Redirect to HTTPS
resource "aws_lb_listener" "http_redirect" {
  count             = var.domain_name != "" && var.cloudflare_zone_id != "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  tags = {
    Name = "clip-downloader-http-redirect"
    Environment = var.environment
    Project = "clip-downloader"
  }
}

# HTTP ALB Listener (port 80) - Direct forward when no domain configured
resource "aws_lb_listener" "http_direct" {
  count             = var.domain_name == "" || var.cloudflare_zone_id == "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  tags = {
    Name = "clip-downloader-http-direct"
    Environment = var.environment
    Project = "clip-downloader"
  }
}

# AWS WAFv2 Web ACL for rate limiting
resource "aws_wafv2_web_acl" "main" {
  count = var.domain_name != "" && var.cloudflare_zone_id != "" ? 1 : 0
  name  = "clip-downloader-waf-${var.environment}"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "RateLimitRule"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }

    action {
      block {}
    }
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  tags = {
    Name = "clip-downloader-waf"
    Environment = var.environment
    Project = "clip-downloader"
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "clipDownloaderWAF"
    sampled_requests_enabled   = true
  }
}

# Associate WAF with ALB
resource "aws_wafv2_web_acl_association" "main" {
  count        = var.domain_name != "" && var.cloudflare_zone_id != "" ? 1 : 0
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main[0].arn

  depends_on = [aws_lb.main, aws_wafv2_web_acl.main]
}

# ECR Repositories
resource "aws_ecr_repository" "backend" {
  name                 = "clip/backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "clip-backend-repo"
    Environment = var.environment
  }
}

resource "aws_ecr_repository" "worker" {
  name                 = "clip/worker"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "clip-worker-repo"
    Environment = var.environment
  }
}

# ECS Task Definition for Backend
resource "aws_ecs_task_definition" "backend" {
  family                   = "clip-downloader-backend-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_task_cpu
  memory                   = var.backend_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${aws_ecr_repository.backend.repository_url}:latest"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "REDIS_URL"
          value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
        },
        {
          name  = "S3_BUCKET"
          value = aws_s3_bucket.clips.bucket
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command = ["CMD-SHELL", "python -c \"import requests; requests.get('http://localhost:8000/health')\" || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 30
      }
    }
  ])

  tags = {
    Name = "clip-downloader-backend-task"
    Environment = var.environment
  }
}

# ECS Task Definition for Worker
resource "aws_ecs_task_definition" "worker" {
  family                   = "clip-downloader-worker-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.worker_task_cpu
  memory                   = var.worker_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "worker"
      image = "${aws_ecr_repository.worker.repository_url}:latest"

      environment = [
        {
          name  = "REDIS_URL"
          value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
        },
        {
          name  = "S3_BUCKET"
          value = aws_s3_bucket.clips.bucket
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command = ["CMD-SHELL", "python -c \"import redis; redis.Redis.from_url('redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379').ping()\" || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 30
      }
    }
  ])

  tags = {
    Name = "clip-downloader-worker-task"
    Environment = var.environment
  }
}

# ECS Service for Backend
resource "aws_ecs_service" "backend" {
  name            = "clip-downloader-backend-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = var.private_subnets
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.main]

  tags = {
    Name = "clip-downloader-backend-service"
    Environment = var.environment
  }
}

# ECS Service for Worker
resource "aws_ecs_service" "worker" {
  name            = "clip-downloader-worker-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = var.private_subnets
    assign_public_ip = false
  }

  tags = {
    Name = "clip-downloader-worker-service"
    Environment = var.environment
  }
}

# IAM User for CI/CD
resource "aws_iam_user" "ci_deploy" {
  name = "clip-downloader-ci-deploy-${var.environment}"

  tags = {
    Name = "clip-downloader-ci-deploy"
    Environment = var.environment
  }
}

resource "aws_iam_user_policy" "ci_deploy" {
  name = "clip-downloader-ci-deploy-policy-${var.environment}"
  user = aws_iam_user.ci_deploy.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage"
        ]
        Resource = [
          aws_ecr_repository.backend.arn,
          aws_ecr_repository.worker.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices"
        ]
        Resource = [
          aws_ecs_service.backend.id,
          aws_ecs_service.worker.id
        ]
      }
    ]
  })
}

# GitHub OIDC Identity Provider
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name = "github-actions-oidc"
    Environment = var.environment
  }
}

# GitHub Actions OIDC Role (alternative to IAM user)
resource "aws_iam_role" "github_actions" {
  name = "clip-downloader-github-actions-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name = "github-actions-role"
    Environment = var.environment
  }
}

# Attach the same policy used by CI user to the OIDC role
resource "aws_iam_role_policy" "github_actions" {
  name = "clip-downloader-github-actions-policy-${var.environment}"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage"
        ]
        Resource = [
          aws_ecr_repository.backend.arn,
          aws_ecr_repository.worker.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:RegisterTaskDefinition",
          "elbv2:DescribeLoadBalancers"
        ]
        Resource = "*"
      }
    ]
  })
} 
