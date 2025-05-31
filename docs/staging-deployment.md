# 🚀 Staging Deployment Guide

This guide covers the complete staging deployment system for the Meme Maker application, including Docker image building, GHCR publishing, and automated deployment via GitHub Actions.

## Overview

The staging deployment system provides:
- **Versioned Docker Images**: Built and pushed to GitHub Container Registry (GHCR)
- **Automated Deployment**: One-click deployment to staging environment
- **Health Checks**: Comprehensive health monitoring and smoke tests
- **Rollback Support**: Easy rollback to previous versions
- **HTTPS/TLS**: Automatic SSL certificates via Caddy
- **Monitoring**: Full observability with Prometheus and Grafana

## Architecture

```
GitHub Actions → GHCR → Staging VPS → Caddy → Services
     ↓              ↓         ↓          ↓
   Build Images   Store    Deploy     HTTPS
   Run Tests      Images   Images     Proxy
```

### Services Overview

| Service | Purpose | External Access |
|---------|---------|-----------------|
| **Caddy** | Reverse proxy, HTTPS termination, static caching | Port 80/443 |
| **Backend** | FastAPI application serving API + SPA | Internal only |
| **Worker** | Video processing with yt-dlp + FFmpeg | Internal only |
| **Redis** | Job queue and caching | Internal only |
| **MinIO** | S3-compatible object storage | Internal only |
| **Prometheus** | Metrics collection | Via Caddy `/prometheus` |

## Quick Start

### 1. Configure Secrets

Set up the following GitHub repository secrets:

#### Required Secrets
```
STAGING_HOST=your-staging-server.com
STAGING_USER=deploy
STAGING_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...
STAGING_DOMAIN=staging.memeit.pro  # Optional, defaults to staging.memeit.pro
```

#### Optional Secrets
```
STAGING_PORT=22                    # SSH port, defaults to 22
CYPRESS_RECORD_KEY=key123         # For Cypress Dashboard
```

### 2. Set Up Staging Server

#### Server Requirements
- **OS**: Ubuntu 22.04+ or compatible
- **Resources**: 2 vCPU, 2 GB RAM minimum (t3.small equivalent)
- **Storage**: 20 GB SSD
- **Network**: Public IP with ports 80/443 open

#### Server Setup Script
```bash
#!/bin/bash
# Run on staging server as root

# Install Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker deploy

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create deploy user and setup SSH
useradd -m -s /bin/bash deploy
mkdir -p /home/deploy/.ssh
# Add your public key to /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Clone repository
su - deploy -c "git clone https://github.com/YOUR_ORG/meme-maker.git"
```

### 3. Configure DNS

Point your staging domain to the server:
```
staging.memeit.pro.    A    YOUR_SERVER_IP
```

### 4. Deploy

#### Automatic Deployment
Push to `main` branch or `release/*` branches:
```bash
git push origin main
```

#### Manual Deployment
Use GitHub Actions workflow dispatch:
1. Go to Actions → Staging Deployment
2. Click "Run workflow"
3. Select branch and options
4. Click "Run workflow"

## Configuration

### Environment Variables

The staging environment uses the following configuration:

```bash
# infra/staging/.env.staging (created automatically)
GITHUB_REPOSITORY=your-org/repo-name
IMAGE_TAG=abc123def456  # Git SHA
STAGING_DOMAIN=staging.memeit.pro
ACME_EMAIL=admin@memeit.pro
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=admin12345
S3_BUCKET=clips
ENV=staging
LOG_LEVEL=INFO
```

### Caddy Configuration

The Caddyfile provides:
- **Automatic HTTPS** with Let's Encrypt
- **Security Headers** (HSTS, CSP, etc.)
- **Compression** (zstd, gzip)
- **Caching** for static assets
- **Rate Limiting** for API endpoints

Key routes:
- `/` → Frontend SPA
- `/api/*` → Backend API
- `/health` → Health checks
- `/docs` → API documentation
- `/metrics` → Prometheus metrics
- `/prometheus/*` → Prometheus UI (optional)

## Deployment Process

### 1. Build & Push (GitHub Actions)

The `build-push` job:
1. **Checkout** repository code
2. **Setup** Docker Buildx for multi-platform builds
3. **Login** to GitHub Container Registry
4. **Extract** metadata and tags
5. **Build** backend and worker images
6. **Push** to GHCR with tags:
   - `latest` (for main branch)
   - `{git-sha}` (for all builds)
   - `{branch}-{git-sha}` (for feature branches)
   - `v{version}` (for release tags)

### 2. Test (Parallel)

Tests run in parallel with image building:
- **Backend Tests**: Unit tests with pytest
- **Frontend Tests**: Unit tests and build verification
- **Final Review**: Performance, accessibility, and bundle audits

### 3. Deploy

The `deploy` job:
1. **SSH** into staging server
2. **Update** repository to target SHA
3. **Pull** latest images from GHCR
4. **Stop** existing services gracefully
5. **Start** new services with health checks
6. **Verify** deployment success

### 4. Smoke Tests

Post-deployment verification:
- **Health Endpoints**: `/health`, `/docs`, `/metrics`
- **Frontend Loading**: Basic page load tests
- **API Functionality**: End-to-end workflow tests
- **Cypress E2E**: Full user journey tests

## Monitoring & Health Checks

### Health Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Application health | `{"status": "healthy"}` |
| `/metrics` | Prometheus metrics | Metrics in Prometheus format |
| `/docs` | API documentation | OpenAPI documentation |

### Service Health Checks

Each service has Docker health checks:

```yaml
# Example: Backend health check
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health', timeout=5)"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### Prometheus Monitoring

Metrics collected:
- **Request Rate**: HTTP requests per second
- **Response Time**: API latency percentiles
- **Error Rate**: HTTP 4xx/5xx responses
- **Queue Depth**: Jobs waiting for processing
- **System Metrics**: CPU, memory, disk usage

Access Prometheus at: `https://staging.memeit.pro/prometheus`

## Rollback Procedures

### Automatic Rollback

If health checks fail after deployment, the system maintains the previous version:
- Health check timeout: 5 minutes
- Automatic failure detection
- Previous containers remain running

### Manual Rollback

#### Option 1: GitHub Actions (Recommended)
1. Go to Actions → Staging Deployment
2. Select a previous successful run
3. Click "Re-run jobs"

#### Option 2: SSH to Server
```bash
# SSH to staging server
ssh deploy@staging.memeit.pro

# View deployment history
cat ~/meme-maker/logs/deployments.log

# Rollback to specific SHA
cd ~/meme-maker
./scripts/deploy_staging.sh PREVIOUS_SHA
```

#### Option 3: Docker Tags
```bash
# Set specific image tag in environment
echo "IMAGE_TAG=previous-sha" >> .env.staging

# Redeploy
docker compose -f infra/staging/docker-compose.staging.yml --env-file=.env.staging up -d
```

## Testing Locally

Test the staging setup locally before deploying:

```bash
# Run local staging test
./scripts/test-staging-local.sh

# This will:
# 1. Build images locally
# 2. Start all services
# 3. Run health checks
# 4. Test all endpoints
# 5. Clean up automatically
```

## Troubleshooting

### Common Issues

#### 1. Images Not Found
**Symptoms**: `pull access denied` or `image not found`
**Solution**: 
- Check GHCR permissions
- Verify image tags in environment file
- Ensure GITHUB_TOKEN has packages:read permission

#### 2. SSL Certificate Issues
**Symptoms**: SSL/TLS errors, certificate warnings
**Solution**:
- Check DNS configuration
- Verify domain points to correct IP
- Check Caddy logs: `docker compose logs caddy`
- Ensure ports 80/443 are open

#### 3. Health Checks Failing
**Symptoms**: Services marked as unhealthy
**Solution**:
- Check service logs: `docker compose logs [service]`
- Verify dependencies (Redis, MinIO)
- Check resource constraints (CPU, memory)
- Increase health check timeouts if needed

#### 4. Frontend Not Loading
**Symptoms**: 404 errors, blank pages
**Solution**:
- Verify frontend build is included in backend image
- Check Caddy routing configuration
- Verify static files are present: `docker exec backend ls -la /app/static`

### Debug Commands

```bash
# SSH to staging server
ssh deploy@staging.memeit.pro

# Check service status
cd ~/meme-maker
docker compose -f infra/staging/docker-compose.staging.yml ps

# View logs
docker compose -f infra/staging/docker-compose.staging.yml logs [service]

# Check container health
docker inspect [container] | jq '.[0].State.Health'

# Test connectivity
curl -v http://localhost/health
curl -v https://staging.memeit.pro/health

# Check resource usage
docker stats

# View deployment history
cat logs/deployments.log
```

### Log Locations

| Service | Log Location |
|---------|--------------|
| **Caddy** | `/var/log/caddy/staging.log` (in container) |
| **Application** | Docker logs via `docker compose logs` |
| **System** | `/var/log/syslog` (on host) |
| **Deployments** | `~/meme-maker/logs/deployments.log` |

## Security Considerations

### Network Security
- **Firewall**: Only ports 22, 80, 443 exposed
- **SSH**: Key-based authentication only
- **Internal**: All services on private Docker network

### Application Security
- **HTTPS**: Forced via Caddy with HSTS
- **Headers**: Security headers (CSP, X-Frame-Options, etc.)
- **Rate Limiting**: Per-IP rate limiting
- **Secrets**: Environment variables, not in containers

### Container Security
- **Non-root**: All services run as non-root users
- **Minimal Images**: Alpine-based images
- **Health Checks**: Prevent unhealthy containers
- **Resource Limits**: CPU/memory constraints

## Performance Optimization

### Resource Allocation
```yaml
# Example resource limits
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
```

### Caching Strategy
- **Static Assets**: 1 year cache via Caddy
- **API Responses**: No cache
- **Docker Images**: Layer caching in GitHub Actions
- **Application**: Redis caching for metadata

### Monitoring Thresholds
- **CPU**: Alert if >80% for 5 minutes
- **Memory**: Alert if >90% for 5 minutes
- **Disk**: Alert if >85% used
- **Response Time**: Alert if P95 >2 seconds

## Maintenance

### Regular Tasks

#### Weekly
- Review deployment logs
- Check disk usage
- Update base images if needed

#### Monthly
- Rotate secrets
- Review resource usage
- Update dependencies

#### Quarterly
- Security audit
- Performance review
- Disaster recovery test

### Backup Strategy

**Configuration Backup**:
```bash
# Backup environment and configs
tar -czf staging-config-$(date +%Y%m%d).tar.gz \
  .env.staging \
  infra/staging/ \
  scripts/
```

**Data Backup**:
- **MinIO**: Automated S3 sync (if configured)
- **Prometheus**: 7-day retention
- **Logs**: Rotated automatically

## Cost Management

### Resource Monitoring
- **t3.small**: ~$15/month
- **Storage**: ~$2/month for 20GB
- **Network**: Included in most plans

### Cost Optimization
- Use Spot instances for non-critical staging
- Implement auto-shutdown during off-hours
- Monitor and alert on usage spikes

## Related Documentation

- [Performance Budget Audit](performance-budget.md)
- [Final Review System](final-review.md) 
- [Monitoring & Alerting Guide](monitoring.md)
- [CI/CD Pipeline Overview](.github/workflows/README.md)

## Architecture Diagrams

### Traffic Flow
```mermaid
graph TD
    A[Internet] --> C{Caddy 📦}
    C --> |/| B[Backend :8000]
    C --> |/api/*| B
    C --> |/health| B
    C --> |/docs| B
    C --> |/metrics| B
    C --> |/prometheus/*<br/>🔐 Basic Auth| P[Prometheus :9090]
    
    B --> |API calls| R[Redis :6379]
    B --> |File storage| M[MinIO :9000]
    B --> |Job queue| R
    W[Worker] --> R
    W --> M
    
    P --> |Metrics collection| B
    P --> |Metrics collection| R
    
    style C fill:#e1f5fe
    style B fill:#f3e5f5
    style P fill:#fff3e0
    style R fill:#ffebee
    style M fill:#e8f5e8
    style W fill:#f1f8e9
```

### Deployment Pipeline
```mermaid
graph LR
    A[Push to main] --> B[GitHub Actions]
    B --> C[Build Images]
    C --> D[Push to GHCR]
    B --> E[Run Tests]
    E --> F[Final Review]
    
    D --> G[Deploy Job]
    F --> G
    G --> H[SSH to VPS]
    H --> I[Pull Images]
    I --> J[Update Containers]
    J --> K[Health Checks]
    K --> L[Smoke Tests]
    
    L --> M[✅ Success]
    K --> |Fail| N[❌ Rollback]
    
    subgraph "VPS Staging Environment"
        H
        I
        J
        K
    end
    
    subgraph "GitHub Container Registry"
        D
    end
    
    style M fill:#c8e6c9
    style N fill:#ffcdd2
    style C fill:#e1f5fe
    style G fill:#fff3e0
``` 