# Meme Maker

[![Smoke Test](https://github.com/YOUR_USERNAME/Meme%20Maker/workflows/Smoke%20Test/badge.svg)](https://github.com/YOUR_USERNAME/Meme%20Maker/actions/workflows/smoke-test.yml)

A simple tool to download and trim video clips from social media platforms with a modern web interface.

## 🚀 Quick Start for End Users

**Want to get started immediately? Use our one-click setup scripts:**

### Windows Users
```powershell
# Download this repository, then run:
.\scripts\quick-start.ps1
```

### macOS/Linux Users
```bash
# Download this repository, then run:
chmod +x scripts/quick-start.sh
./scripts/quick-start.sh
```

### Manual Setup
If you prefer step-by-step instructions, see our **[Complete Getting Started Guide](docs/getting-started.md)** which covers:
- ✅ Installing all prerequisites (Git, Docker, etc.)
- ✅ Setting up the application from scratch
- ✅ Using the app to clip videos
- ✅ Troubleshooting common issues
- ✅ Optional production deployment

**Already have Docker?** Jump straight to:
```bash
# Clone and start
git clone https://github.com/YOUR_USERNAME/Meme-Maker.git
cd Meme-Maker
docker-compose up --build

# Access at http://localhost:3000
```

## Features
- 🎬 **Web UI**: Modern, mobile-first interface for easy video trimming
- ✂️ **Precision Trimming**: Dual-handle slider + timestamp inputs (max 3 minutes)
- 📱 **Mobile Optimized**: Works on devices as small as 360px width
- 📋 **Auto-Copy**: Automatically copies download links to clipboard
- 🎯 **Real-Time Preview**: Live video preview during trimming
- ⚡ **Fast Processing**: Efficient video processing with yt-dlp + FFmpeg
- 🔒 **Anonymous**: No signup required, files self-destruct after download
- 🚦 **Rate Limited**: IP-based rate limiting with user-friendly notifications
- 📊 **Monitoring**: Comprehensive monitoring with Prometheus and Grafana
- 🚨 **Alerting**: Robust alerting for uptime and error rate monitoring
- ⚖️ **Legal Compliance**: Terms of Use and Privacy Policy with mandatory acceptance

## Supported Platforms
YouTube, Instagram, Facebook, Threads, and Reddit

## Architecture
- **Frontend**: Next.js with TypeScript and Tailwind CSS (served by backend)
- **Backend**: FastAPI with Python 3.12
- **Queue**: Redis with RQ
- **Storage**: AWS S3 with presigned URLs
- **Processing**: yt-dlp + FFmpeg
- **Monitoring**: Prometheus + Grafana
- **Alerting**: Alertmanager with Slack and Email notifications

## Quick Start

### Production Mode (Integrated Frontend + Backend)

```bash
# Start the complete stack
docker-compose up -d

# Access the web interface
open http://localhost:8000
```

### Development Mode (Separate Frontend + Backend)

```bash
# Start backend services
docker-compose -f docker-compose.dev.yaml up -d

# Frontend will be available at http://localhost:3000
# Backend API at http://localhost:8000
```

## 🚀 Deployment

### VPS Deployment with Caddy

The application uses a hybrid approach where FastAPI serves the frontend SPA while Caddy handles reverse proxying and caching:

1. **Frontend**: Static Next.js build served by FastAPI from `/app/static`
2. **Backend**: FastAPI container with API routes at `/api/v1/*`
3. **Caddy**: Reverse proxy with caching and security headers

#### Quick Deploy

```bash
# Build and deploy to VPS
make deploy
```

#### Manual Deployment Steps

1. **Build Frontend Locally**:
   ```bash
   cd frontend
   npm run build  # Creates frontend/out/ directory
   ```

2. **Deploy to VPS**:
   ```bash
   # The deployment script handles everything:
   # - Pulls latest code (including Caddyfile)
   # - Builds Docker containers (includes frontend build)
   # - Restarts services
   # - Restarts Caddy with new configuration
   ./scripts/deploy_to_vps.sh
   ```

#### Architecture Overview

```
Internet → Caddy (memeit.pro) → FastAPI Container
           ├── Cache static assets (/_next/*, *.js, *.css)
           ├── Proxy API routes (/api/*, /health, /docs)
           └── Proxy SPA routes (/, client-side routes)
```

**FastAPI Static Serving**:
- Mounts `/app/static` directory (contains frontend build)
- Serves `index.html` for SPA routes
- Serves static assets directly
- API routes take precedence

**Caddy Configuration**:
- **API Routes**: `/api/*`, `/health`, `/metrics`, `/docs` → Proxy to FastAPI
- **Static Assets**: `/_next/*`, `*.js`, `*.css` → Cache 1 year
- **HTML/SPA**: `/`, client routes → No cache, proxy to FastAPI
- **Security**: HSTS, CSP, X-Frame-Options headers

#### Environment Variables

Create `.env` file:

```bash
# API Configuration
CORS_ORIGINS=https://memeit.pro

# For development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Health Check

After deployment, verify the setup:

```bash
# Check backend health
curl -f https://memeit.pro/health

# Check frontend (should return HTML)
curl -f https://memeit.pro/

# Check API
curl -f https://memeit.pro/api/v1/jobs
```

## Development

This is a monorepo with the following structure:
- **frontend/** - Next.js application with video trimming UI
- **backend/** - FastAPI server (serves frontend in production)
- **worker/** - Video processing worker
- **infra/** - Infrastructure as code

### Local Development

Start the local development stack with Docker Compose:

```bash
# Start all services (Redis, MinIO, Backend, Worker, Prometheus, Grafana)
./scripts/dev-up.sh

# Check health
curl http://localhost:8000/health

# Stop and clean up
./scripts/dev-down.sh
```

Services available:
- **Web Interface**: http://localhost:8000 (main app)
- **Backend API**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics
- **MinIO Console**: http://localhost:9003 (user: `admin`, password: `admin12345`)
- **MinIO S3 API**: http://localhost:9002
- **Redis**: localhost:6379
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Grafana**: http://localhost:3000 (user: `admin`, password: `admin`)

### Frontend Development

For frontend-specific development:

```bash
cd frontend
npm install
npm run dev  # Requires backend running on port 8000
```

The frontend includes:
- **Mobile-first design** with 360px minimum width support
- **44px touch targets** for mobile slider handles
- **3-second polling** for job status updates
- **Auto-copy functionality** for download links
- **Bundle size < 250kB** gzipped

### Monitoring & Alerting

The application includes comprehensive monitoring and alerting:

#### Monitoring Stack
- **Prometheus** scrapes metrics from the backend API every 10 seconds
- **Grafana** provides dashboards for visualizing job metrics
- **Alertmanager** handles alert routing and notifications
- **Custom metrics** track job latency, queue depth, and error rates

#### Alerting Rules
- **API_Uptime_Failure**: Triggers when `/health` fails for 3+ minutes
- **API_Error_Rate_High**: Triggers when error rate exceeds 5% over 5 minutes
- **Worker_Not_Processing**: Triggers when no jobs complete for 10+ minutes
- **Job_Queue_High**: Warning when queue depth exceeds 15 jobs for 5+ minutes

#### Quick Setup
```bash
# Set up monitoring with alerting
./scripts/setup-monitoring.sh

# Test alert conditions
./scripts/test-alerts.sh
```

#### Alert Configuration
Configure notifications in `.env`:
```bash
# Slack notifications (required)
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Email notifications (optional)
ALERT_EMAIL_USER=your-smtp-username
ALERT_EMAIL_PASS=your-smtp-password
ALERT_EMAIL_RECIPIENT=admin@yourdomain.com
```

Access the **Clip Overview** dashboard at http://localhost:3000 after starting the services. The dashboard includes:
- Jobs in flight (real-time gauge)
- Job queue rate (5-minute rolling average)
- Job latency heatmap (processing time distribution)
- Error rate (percentage of failed jobs)

Environment configuration is handled through the docker-compose.yaml file. For custom settings, copy `env.template` to `.env` and modify as needed.

### Key Environment Variables

#### Rate Limiting Configuration
- `MAX_JOBS_PER_HOUR` - Maximum job creations per IP per hour (default: 20)
- `RATE_LIMIT` - Enable/disable rate limiting: "on" or "off" (default: "on")
- `GLOBAL_RATE_LIMIT_REQUESTS` - Global API requests per minute (default: 10)

#### Clip Configuration  
- `MAX_CLIP_SECONDS` - Maximum clip duration in seconds (default: 1800 = 30 minutes)

#### Development Settings
- `DEBUG` - Enable debug mode to disable rate limiting (default: false)

For a complete list of environment variables, see `env.template`.

## API Usage

While the web interface is the primary way to use the service, you can also interact directly with the API:

```bash
# Get video metadata
curl -X POST http://localhost:8000/api/v1/metadata \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Create a clip job (requires terms acceptance)
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "start": "00:00:05", "end": "00:00:15", "accepted_terms": true}'

# Check job status
curl http://localhost:8000/api/v1/jobs/{job_id}
```

**Note**: All job creation requests require `accepted_terms: true` to comply with Terms of Use.

## 🚀 Staging Deployment

The project includes a comprehensive staging deployment system with versioned Docker images and automated deployment via GitHub Actions.

### Quick Deploy to Staging

```bash
# Automatic deployment on push to main
git push origin main

# Manual deployment via GitHub Actions
# Go to Actions → Staging Deployment → Run workflow
```

### Staging Environment

- **URL**: https://staging.memeit.pro
- **Health**: https://staging.memeit.pro/health
- **API Docs**: https://staging.memeit.pro/docs
- **Prometheus**: https://staging.memeit.pro/prometheus

### Features

- **Versioned Images**: Built and pushed to GitHub Container Registry (GHCR)
- **Automated Deployment**: One-click deployment to staging VPS
- **Health Checks**: Comprehensive monitoring and smoke tests
- **HTTPS/TLS**: Automatic SSL certificates via Caddy
- **Rollback Support**: Easy rollback to previous versions
- **Local Testing**: Test staging setup locally before deploying

### Test Staging Locally

```bash
# Test the complete staging stack locally
./scripts/test-staging-local.sh
```

### Configuration

Required GitHub secrets for staging deployment:
- `STAGING_HOST` - Staging server hostname/IP
- `STAGING_USER` - SSH user for deployment
- `STAGING_SSH_KEY` - Private SSH key for server access
- `STAGING_DOMAIN` - Staging domain (optional, defaults to staging.memeit.pro)

For detailed setup instructions, see [Staging Deployment Guide](docs/staging-deployment.md).

## 🏭 Production Deployment

The production environment features enterprise-grade security with wildcard SSL certificates, modern TLS configuration, and comprehensive monitoring.

### Production Infrastructure

- **Main Application**: https://app.memeit.pro
- **WWW Redirect**: https://www.memeit.pro → https://app.memeit.pro
- **Monitoring**: https://monitoring.memeit.pro (basic auth protected)
- **SSL/TLS**: Let's Encrypt wildcard certificates with DNS-01 validation
- **DNS**: AWS Route 53 with automated DNS management
- **Security**: A+ SSL Labs grade, HSTS preload, modern cipher suites only

### Key Features

- **🔒 Wildcard SSL**: Automatic certificate issuance and renewal via Route 53
- **⚡ Modern TLS**: TLS 1.2+ only with strong cipher suites and PFS
- **🛡️ Security Headers**: HSTS preload, CSP, XSS protection, and more
- **📊 Full Monitoring**: Prometheus metrics with Grafana dashboards
- **🚨 SSL Monitoring**: Certificate expiry alerts and renewal automation
- **🏗️ Infrastructure as Code**: Terraform for Route 53 and AWS resources

### Quick Deploy to Production

```bash
# Tag a release to trigger production deployment
git tag v1.0.0
git push origin v1.0.0

# Or manually trigger via GitHub Actions
# Go to Actions → Production Deployment → Run workflow
```

### Production Setup Requirements

#### AWS Resources
- Route 53 hosted zone for `memeit.pro`
- S3 bucket for clip storage
- IAM user with Route 53 and S3 permissions

#### GitHub Secrets
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
S3_BUCKET, ROUTE53_ZONE_ID

# Production Server
PRODUCTION_SERVER_IP, PRODUCTION_HOST, PRODUCTION_USER, PRODUCTION_SSH_KEY

# Security
GRAFANA_ADMIN_PASSWORD, PROMETHEUS_PASS_HASH, GRAFANA_PASS_HASH
```

### DNS & SSL Configuration

The production deployment automatically:

1. **Provisions DNS Records**: Creates A/CNAME records for all subdomains
2. **Obtains SSL Certificates**: Wildcard `*.memeit.pro` via DNS-01 challenge
3. **Configures Security**: Modern TLS settings and comprehensive headers
4. **Sets Up Monitoring**: SSL expiry alerts and certificate renewal tracking

### Security & Compliance

- **SSL Labs Grade**: Target A+ rating with modern TLS configuration
- **HSTS Preload**: 2-year max-age with includeSubDomains and preload
- **Perfect Forward Secrecy**: All cipher suites provide PFS
- **Certificate Transparency**: Automatic monitoring of certificate logs
- **Security Headers**: Comprehensive CSP, XSS protection, and CSRF prevention

### Production Verification

```bash
# Health checks
curl -f https://app.memeit.pro/health
curl -f https://app.memeit.pro/docs

# SSL verification
echo | openssl s_client -servername app.memeit.pro -connect app.memeit.pro:443

# Security testing
curl -I https://app.memeit.pro | grep -E "(Strict-Transport-Security|Content-Security-Policy)"
```

### Monitoring & Operations

- **Application Metrics**: Performance, error rates, and resource usage
- **SSL Monitoring**: Certificate expiry tracking and renewal alerts
- **Infrastructure**: Server health, DNS resolution, and network connectivity
- **Automated Alerts**: Slack/email notifications for critical issues

For detailed production setup instructions, see [Production Deployment Guide](docs/production-deployment.md).

## Project documentation

- [Production Deployment Guide](docs/production-deployment.md)
- [Security Guide](docs/security.md)
- [Staging Deployment Guide](docs/staging-deployment.md)
- [Wireframes](docs/wireframes/README.md)
- [Frontend Documentation](frontend/README.md)
- [Visual Regression Testing](frontend/cypress/VISUAL_TESTING.md)
- [Accessibility Guide](docs/accessibility.md)
- [Legal Compliance Guide](docs/legal.md)
- [Monitoring & Alerting Guide](docs/monitoring.md)
- [Rate Limiting & Abuse Protection](docs/rate-limiting.md)

## License

MIT License - see LICENSE file for details.
