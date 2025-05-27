# Meme Maker

A simple tool to download and trim video clips from social media platforms.

## Features
- Support for YouTube, Instagram, Facebook, Threads, and Reddit
- Trim videos up to 3 minutes
- Anonymous usage - no signup required
- Self-destructing download links
- Comprehensive monitoring with Prometheus and Grafana

## Architecture
- Frontend: Next.js with TypeScript and Tailwind CSS
- Backend: FastAPI with Python 3.12
- Queue: Redis with RQ
- Storage: AWS S3 with presigned URLs
- Processing: yt-dlp + FFmpeg
- Monitoring: Prometheus + Grafana

## Development

This is a monorepo with the following structure:
- frontend/ - Next.js application
- backend/ - FastAPI server
- worker/ - Video processing worker
- infra/ - Infrastructure as code

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
- **Backend API**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **MinIO Console**: http://localhost:9001 (user: `clip`, password: `secret`)
- **MinIO S3 API**: http://localhost:9000
- **Redis**: localhost:6379
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3002 (user: `admin`, password: `grafana`)

### Monitoring

The application includes comprehensive monitoring:

- **Prometheus** scrapes metrics from the backend API every 10 seconds
- **Grafana** provides dashboards for visualizing job metrics
- **Custom metrics** track job latency, queue depth, and error rates

Access the **Clip Overview** dashboard at http://localhost:3002 after starting the services. The dashboard includes:
- Jobs in flight (real-time gauge)
- Job queue rate (5-minute rolling average)
- Job latency heatmap (processing time distribution)
- Error rate (percentage of failed jobs)

Environment configuration is handled through the docker-compose.yaml file. For custom settings, copy `env.template` to `.env` and modify as needed.

## Project documentation

- [Wireframes](docs/wireframes/README.md)

## License

MIT License - see LICENSE file for details.
