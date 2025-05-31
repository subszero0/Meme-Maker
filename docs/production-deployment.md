# Production Deployment Guide - Meme Maker

This guide covers the complete production deployment process for Meme Maker, including DNS configuration, SSL certificate management, and infrastructure setup.

## 🚀 Production Overview

### **Production Domains**
- **Main Application**: `https://app.memeit.pro`
- **WWW Redirect**: `https://www.memeit.pro` → `https://app.memeit.pro`
- **Monitoring**: `https://monitoring.memeit.pro` (basic auth protected)

### **Infrastructure Components**
- **Frontend**: Next.js SPA served by FastAPI
- **Backend**: FastAPI with Redis queue
- **Worker**: Video processing with yt-dlp + FFmpeg
- **SSL Termination**: Caddy with Let's Encrypt wildcard certificates
- **Monitoring**: Prometheus + Grafana
- **DNS**: AWS Route 53 with DNS-01 challenge

## 📋 Prerequisites

### **AWS Resources Required**
1. **Route 53 Hosted Zone** for `memeit.pro`
2. **S3 Bucket** for clip storage
3. **IAM User** with Route 53 and S3 permissions
4. **Production VPS** with Docker and Docker Compose

### **GitHub Secrets Required**
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLE
AWS_REGION=ap-south-1
S3_BUCKET=meme-clips-prod
ROUTE53_ZONE_ID=Z123456789ABCDEFGHIJ

# Production Server
PRODUCTION_SERVER_IP=1.2.3.4
PRODUCTION_HOST=app.memeit.pro
PRODUCTION_USER=ubuntu
PRODUCTION_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...

# Application Security
GRAFANA_ADMIN_PASSWORD=secure_admin_password
PROMETHEUS_PASS_HASH=$2b$10$hash_here
GRAFANA_PASS_HASH=$2b$10$hash_here
```

## 🛠️ Setup Process

### **Step 1: DNS Infrastructure**

#### **1.1 Route 53 Hosted Zone**
```bash
# Create hosted zone (if not exists)
aws route53 create-hosted-zone \
  --name memeit.pro \
  --caller-reference $(date +%s)

# Get zone ID
aws route53 list-hosted-zones-by-name --dns-name memeit.pro
```

#### **1.2 DNS Records Setup**
```bash
# Run DNS provisioning script
export ROUTE53_ZONE_ID="Z123456789ABCDEFGHIJ"
export PRODUCTION_SERVER_IP="1.2.3.4"
./scripts/provision_dns.sh
```

This creates:
- `app.memeit.pro` → Production server IP
- `www.memeit.pro` → CNAME to `app.memeit.pro`
- `monitoring.memeit.pro` → Production server IP
- `_acme-challenge.memeit.pro` → TXT record for SSL validation

### **Step 2: Production Server Setup**

#### **2.1 Server Preparation**
```bash
# SSH to production server
ssh ubuntu@app.memeit.pro

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/meme-maker
sudo chown ubuntu:ubuntu /opt/meme-maker
cd /opt/meme-maker

# Clone repository
git clone https://github.com/your-org/meme-maker.git .
```

#### **2.2 Environment Configuration**
```bash
# Copy and configure environment
cp infra/production/env.prod.example .env.prod

# Edit production environment
nano .env.prod
```

### **Step 3: SSL Certificate Configuration**

#### **3.1 Caddy with Route 53 Plugin**
The production Caddyfile includes:
- **DNS-01 Challenge**: Automatic wildcard certificate issuance
- **Modern TLS**: Only TLS 1.2+ with strong cipher suites
- **Security Headers**: HSTS, CSP, and other protective headers
- **Performance**: Compression and caching optimization

#### **3.2 Certificate Management**
```bash
# Verify DNS propagation before first deployment
dig app.memeit.pro
dig www.memeit.pro
dig monitoring.memeit.pro

# Check Route 53 permissions
aws route53 list-hosted-zones
aws route53 list-resource-record-sets --hosted-zone-id Z123456789ABCDEFGHIJ
```

### **Step 4: Production Deployment**

#### **4.1 GitHub Actions Deployment**
```bash
# Tag a release to trigger production deployment
git tag v1.0.0
git push origin v1.0.0

# Or manually trigger deployment
# Go to GitHub Actions → Production Deployment → Run workflow
```

#### **4.2 Manual Deployment**
```bash
# On production server
cd /opt/meme-maker

# Update configuration
git pull origin main

# Deploy with production configuration
docker-compose -f infra/production/docker-compose.prod.yml --env-file .env.prod up -d

# Monitor deployment
docker-compose -f infra/production/docker-compose.prod.yml logs -f
```

### **Step 5: SSL Certificate Verification**

#### **5.1 Certificate Issuance**
```bash
# Check Caddy logs for certificate issuance
docker logs meme-prod-caddy

# Verify SSL certificate
echo | openssl s_client -servername app.memeit.pro -connect app.memeit.pro:443 2>/dev/null | openssl x509 -noout -dates
```

#### **5.2 SSL Labs Testing**
```bash
# Test SSL configuration (wait for propagation)
curl -s "https://api.ssllabs.com/api/v3/analyze?host=app.memeit.pro&startNew=on"

# Check results after analysis completes
curl -s "https://api.ssllabs.com/api/v3/analyze?host=app.memeit.pro" | jq '.endpoints[0].grade'
```

## 🔍 Post-Deployment Verification

### **Health Checks**
```bash
# Application health
curl -f https://app.memeit.pro/health

# API documentation
curl -f https://app.memeit.pro/docs

# Monitoring endpoints (with auth)
curl -f -u admin:password https://monitoring.memeit.pro/prometheus/-/healthy
curl -f -u admin:password https://monitoring.memeit.pro/grafana/api/health
```

### **Security Verification**
```bash
# Check security headers
curl -I https://app.memeit.pro | grep -E "(Strict-Transport-Security|Content-Security-Policy|X-Frame-Options)"

# Verify HSTS preload eligibility
curl -s "https://hstspreload.org/api/v2/status?domain=memeit.pro"

# Test SSL configuration
testssl.sh app.memeit.pro
```

### **Performance Testing**
```bash
# Basic performance test
curl -w "@curl-format.txt" -o /dev/null -s https://app.memeit.pro

# Lighthouse CI
npm install -g @lhci/cli
lhci autorun --upload.target=temporary-public-storage --collect.url=https://app.memeit.pro
```

## 🔧 Operations & Maintenance

### **Certificate Renewal**
- **Automatic**: Caddy renews certificates 30 days before expiry
- **Monitoring**: Prometheus alerts for certificate expiry
- **Manual Renewal**: `docker exec meme-prod-caddy caddy reload`

### **Backup Procedures**
```bash
# Backup certificate data
docker exec meme-prod-caddy tar -czf /tmp/caddy-certs.tar.gz /data/caddy/certificates
docker cp meme-prod-caddy:/tmp/caddy-certs.tar.gz ./backup/

# Backup application data
docker-compose -f infra/production/docker-compose.prod.yml exec backend python -m app.backup
```

### **Monitoring & Alerts**
- **Prometheus**: https://monitoring.memeit.pro/prometheus
- **Grafana**: https://monitoring.memeit.pro/grafana
- **Alerts**: Configured for SSL expiry, uptime, and performance

### **Log Management**
```bash
# View application logs
docker-compose -f infra/production/docker-compose.prod.yml logs -f backend

# View Caddy access logs
docker exec meme-prod-caddy tail -f /var/log/caddy/access.log

# Log rotation is handled automatically by Docker
```

## 🚨 Troubleshooting

### **SSL Certificate Issues**

#### **Certificate Not Issued**
```bash
# Check Caddy logs
docker logs meme-prod-caddy

# Verify DNS propagation
dig _acme-challenge.memeit.pro TXT

# Check Route 53 permissions
aws route53 list-resource-record-sets --hosted-zone-id Z123456789ABCDEFGHIJ
```

#### **Certificate Expired**
```bash
# Force renewal
docker exec meme-prod-caddy caddy reload

# Check renewal schedule
docker exec meme-prod-caddy cat /data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/*/user.json
```

### **DNS Resolution Issues**

#### **Domain Not Resolving**
```bash
# Check DNS propagation globally
dig @8.8.8.8 app.memeit.pro
dig @1.1.1.1 app.memeit.pro

# Verify Route 53 records
aws route53 list-resource-record-sets --hosted-zone-id Z123456789ABCDEFGHIJ
```

#### **SSL Handshake Failures**
```bash
# Test SSL connection
openssl s_client -connect app.memeit.pro:443 -servername app.memeit.pro

# Check cipher compatibility
nmap --script ssl-enum-ciphers -p 443 app.memeit.pro
```

### **Application Issues**

#### **502 Bad Gateway**
```bash
# Check backend health
docker-compose -f infra/production/docker-compose.prod.yml ps

# View backend logs
docker-compose -f infra/production/docker-compose.prod.yml logs backend

# Test backend directly
docker exec meme-prod-backend curl -f http://localhost:8000/health
```

#### **High Latency**
```bash
# Check resource usage
docker stats

# Monitor Prometheus metrics
curl https://monitoring.memeit.pro/prometheus/api/v1/query?query=up

# Review Grafana dashboards
open https://monitoring.memeit.pro/grafana
```

## 📊 Monitoring & Metrics

### **Key Metrics to Monitor**
- **SSL Certificate Expiry**: < 30 days warning, < 7 days critical
- **Application Uptime**: Target 99.9%
- **Response Time**: < 2s for 95% of requests
- **Error Rate**: < 1% of total requests
- **Resource Usage**: CPU < 80%, Memory < 85%

### **Alerting Rules**
```yaml
# SSL Certificate Expiry
- alert: SSLCertificateExpiringSoon
  expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 30

# Application Down
- alert: ApplicationDown
  expr: up{job="app"} == 0
  for: 5m

# High Error Rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
```

## 🔗 External Resources

### **SSL/TLS Testing**
- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)
- [HSTS Preload](https://hstspreload.org/)

### **DNS Testing**
- [DNS Propagation Checker](https://dnschecker.org/)
- [DNS Lookup](https://mxtoolbox.com/DNSLookup.aspx)

### **Performance Testing**
- [GTmetrix](https://gtmetrix.com/)
- [PageSpeed Insights](https://pagespeed.web.dev/)
- [WebPageTest](https://www.webpagetest.org/)

---

**Last Updated**: $(date)
**Next Review**: $(date -d "+1 month")
**Maintained By**: Platform Team 