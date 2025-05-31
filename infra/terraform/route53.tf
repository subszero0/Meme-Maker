# Route53 DNS Records (Optional)
# Creates DNS records when domain is managed in AWS Route53

# Data source to get the hosted zone information
data "aws_route53_zone" "main" {
  count = var.create_route53_record && var.route53_zone_id != "" ? 1 : 0
  
  zone_id = var.route53_zone_id
}

# Create A record pointing to load balancer
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