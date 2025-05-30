# Meme Maker

[![Smoke Test](https://github.com/YOUR_USERNAME/Meme%20Maker/workflows/Smoke%20Test/badge.svg)](https://github.com/YOUR_USERNAME/Meme%20Maker/actions/workflows/smoke-test.yml)

A simple tool to download and trim video clips from social media platforms with a modern web interface.

## Features
- 🎬 **Web UI**: Modern, mobile-first interface for easy video trimming
- ✂️ **Precision Trimming**: Dual-handle slider + timestamp inputs (max 3 minutes)
- 📱 **Mobile Optimized**: Works on devices as small as 360px width
- 📋 **Auto-Copy**: Automatically copies download links to clipboard
- 🎯 **Real-Time Preview**: Live video preview during trimming
- ⚡ **Fast Processing**: Efficient video processing with yt-dlp + FFmpeg
- 🔒 **Anonymous**: No signup required, files self-destruct after download
- 🚦 **Rate Limited**: Guests can submit up to 40 clips per day per IP
- 📊 **Monitoring**: Comprehensive monitoring with Prometheus and Grafana

## Supported Platforms
YouTube, Instagram, Facebook, Threads, and Reddit

## Architecture
- **Frontend**: Next.js with TypeScript and Tailwind CSS (served by backend)
- **Backend**: FastAPI with Python 3.12
- **Queue**: Redis with RQ
- **Storage**: AWS S3 with presigned URLs
- **Processing**: yt-dlp + FFmpeg
- **Monitoring**: Prometheus + Grafana

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

## 🔁 One-Command VPS Deploy

For production deployment to VPS:

```bash
export DEPLOY_SSH="ubuntu@13.127.249.36 -i ~/.ssh/meme_vps"
./scripts/deploy_to_vps.sh
```

**Best practice**: Keep production deploys idempotent, scriptable, and environment-driven to avoid human error.

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

### Monitoring

The application includes comprehensive monitoring:

- **Prometheus** scrapes metrics from the backend API every 10 seconds
- **Grafana** provides dashboards for visualizing job metrics
- **Custom metrics** track job latency, queue depth, and error rates

Access the **Clip Overview** dashboard at http://localhost:3000 after starting the services. The dashboard includes:
- Jobs in flight (real-time gauge)
- Job queue rate (5-minute rolling average)
- Job latency heatmap (processing time distribution)
- Error rate (percentage of failed jobs)

Environment configuration is handled through the docker-compose.yaml file. For custom settings, copy `env.template` to `.env` and modify as needed.

## API Usage

While the web interface is the primary way to use the service, you can also interact directly with the API:

```bash
# Get video metadata
curl -X POST http://localhost:8000/api/v1/metadata \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Create a clip job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "in": 5, "out": 15, "rights": true}'

# Check job status
curl http://localhost:8000/api/v1/jobs/{job_id}
```

## Project documentation

- [Wireframes](docs/wireframes/README.md)
- [Frontend Documentation](frontend/README.md)

## License

MIT License - see LICENSE file for details.
