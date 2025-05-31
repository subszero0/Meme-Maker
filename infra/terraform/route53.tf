# Route53 DNS Records (Optional)
# Creates DNS records when domain is managed in AWS Route53

# Data source to get the hosted zone information
data "aws_route53_zone" "main" {
  count = var.create_route53_record && var.route53_zone_id != "" ? 1 : 0
  
  zone_id = var.route53_zone_id
}

# Production A records for main domains
resource "aws_route53_record" "app_memeit_pro" {
  count = var.create_route53_record && var.route53_zone_id != "" && var.production_lb_dns != "" ? 1 : 0
  
  zone_id = var.route53_zone_id
  name    = "app.memeit.pro"
  type    = "A"
  ttl     = 300
  records = [var.production_server_ip]

  tags = {
    Name        = "app.memeit.pro"
    Environment = "production"
    Project     = var.project_name
    Purpose     = "ProductionAppRecord"
  }
}

resource "aws_route53_record" "www_memeit_pro" {
  count = var.create_route53_record && var.route53_zone_id != "" && var.production_lb_dns != "" ? 1 : 0
  
  zone_id = var.route53_zone_id
  name    = "www.memeit.pro"
  type    = "CNAME"
  ttl     = 300
  records = ["app.memeit.pro"]

  tags = {
    Name        = "www.memeit.pro"
    Environment = "production"
    Project     = var.project_name
    Purpose     = "ProductionWWWRedirect"
  }
}

# Monitoring subdomain for Prometheus/Grafana
resource "aws_route53_record" "monitoring_memeit_pro" {
  count = var.create_route53_record && var.route53_zone_id != "" && var.production_server_ip != "" ? 1 : 0
  
  zone_id = var.route53_zone_id
  name    = "monitoring.memeit.pro"
  type    = "A"
  ttl     = 300
  records = [var.production_server_ip]

  tags = {
    Name        = "monitoring.memeit.pro"
    Environment = "production"
    Project     = var.project_name
    Purpose     = "ProductionMonitoringRecord"
  }
}

# ACME DNS-01 challenge record for Let's Encrypt wildcard certificates
resource "aws_route53_record" "acme_dns_challenge" {
  count = var.create_route53_record && var.route53_zone_id != "" ? 1 : 0
  
  zone_id = var.route53_zone_id
  name    = "_acme-challenge.memeit.pro"
  type    = "TXT"
  ttl     = 60
  records = ["placeholder-for-acme-challenge"]

  tags = {
    Name        = "_acme-challenge.memeit.pro"
    Environment = "production"
    Project     = var.project_name
    Purpose     = "ACMEChallengeRecord"
  }
  
  lifecycle {
    ignore_changes = [records]
  }
}

# Wildcard ACME challenge for Let's Encrypt subdomains
resource "aws_route53_record" "acme_dns_challenge_wildcard" {
  count = var.create_route53_record && var.route53_zone_id != "" ? 1 : 0
  
  zone_id = var.route53_zone_id
  name    = "_acme-challenge.*.memeit.pro"
  type    = "TXT"
  ttl     = 60
  records = ["placeholder-for-acme-challenge-wildcard"]

  tags = {
    Name        = "_acme-challenge.*.memeit.pro"
    Environment = "production"
    Project     = var.project_name
    Purpose     = "ACMEChallengeWildcardRecord"
  }
  
  lifecycle {
    ignore_changes = [records]
  }
}

# Legacy API record (backwards compatibility)
resource "aws_route53_record" "api" {
  count = var.create_route53_record && var.route53_zone_id != "" && var.lb_dns != "" ? 1 : 0
  
  zone_id = var.route53_zone_id
  name    = "memeit.${var.domain}"
  type    = "CNAME"
  ttl     = 300
  records = [var.lb_dns]

  tags = {
    Name        = "memeit.${var.domain}"
    Environment = var.env
    Project     = var.project_name
    Purpose     = "APIDNSRecord"
  }
}

# Alternative: Create A record with alias (if load balancer is ALB)
# Uncomment this block and comment the CNAME above if using ALB
# data "aws_lb" "main" {
#   count = var.create_route53_record && var.route53_zone_id != "" && var.lb_dns != "" ? 1 : 0
#   arn   = var.lb_arn  # You would need to add this variable
# }
# 
# resource "aws_route53_record" "api_alias" {
#   count = var.create_route53_record && var.route53_zone_id != "" && var.lb_dns != "" ? 1 : 0
#   
#   zone_id = var.route53_zone_id
#   name    = "memeit.${var.domain}"
#   type    = "A"
# 
#   alias {
#     name                   = data.aws_lb.main[0].dns_name
#     zone_id                = data.aws_lb.main[0].zone_id
#     evaluate_target_health = true
#   }
# 
#   tags = {
#     Name        = "memeit.${var.domain}"
#     Environment = var.env
#     Project     = var.project_name
#     Purpose     = "APIDNSRecord"
#   }
# } 