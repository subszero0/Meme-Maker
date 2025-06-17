# Meme Maker

A modern, responsive tool to download and trim video clips from social media platforms with a beautiful, intuitive interface.

## Features
- **Multi-Platform Support**: YouTube, Instagram, Facebook, Threads, and Reddit
- **Smart Video Trimming**: Precise clip selection up to 3 minutes
- **Modern UI**: Fully integrated React interface with beautiful design (frontend-new) ✅
- **Legacy UI**: Original Next.js interface (frontend) - backup available
- **Real-time Processing**: Live progress tracking with job status updates
- **Anonymous Usage**: No signup required, privacy-focused
- **Self-destructing Links**: Secure, temporary download URLs
- **Comprehensive Monitoring**: Prometheus and Grafana dashboards

## Architecture
- **Frontend (New)**: React 18 + Vite + TypeScript + Tailwind CSS + ShadCN UI (frontend-new/)
- **Frontend (Legacy)**: Next.js with TypeScript and Tailwind CSS (frontend/)
- **Backend**: FastAPI with Python 3.12
- **Queue**: Redis with RQ for async processing
- **Storage**: AWS S3 with presigned URLs
- **Processing**: yt-dlp + FFmpeg for video handling
- **Monitoring**: Prometheus + Grafana with custom metrics

## Development

This is a monorepo with the following structure:
- **frontend-new/** - Modern React application (recommended for new development)
- **frontend/** - Legacy Next.js application (still functional)
- **backend/** - FastAPI server
- **worker/** - Video processing worker
- **infra/** - Infrastructure as code

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Git

### Quick Start Options

#### Option 1: New Frontend (Recommended)
```bash
# Start backend services
docker-compose -f docker-compose.dev.yaml up redis backend worker

# Run new frontend locally
cd frontend-new
npm install
npm run dev

# Access at http://localhost:3000
```

#### Option 2: Legacy Frontend
```bash
# Use existing development setup
./scripts/dev-up.sh

# Access at http://localhost:3000 (Next.js)
```

#### Option 3: Full Docker Development
```bash
# All services including new frontend
docker-compose -f docker-compose.dev.yaml up --build

# Services available:
# - New Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - Monitoring: http://localhost:9090 (Prometheus)
```

### Local Development

Start the local development stack with Docker Compose:

```bash
# Start all services (Redis, Backend, Worker, Prometheus, Grafana)
./scripts/dev-up.sh

# For new frontend development
cd frontend-new && npm run dev

# Check health
curl http://localhost:8000/health

# Stop and clean up
./scripts/dev-down.sh
```

### Services Available
- **New Frontend**: http://localhost:3000 - Modern React interface
- **Legacy Frontend**: http://localhost:3001 - Original Next.js interface
- **Backend API**: http://localhost:8000/health - API endpoints
- **API Documentation**: http://localhost:8000/docs - Interactive API docs
- **Metrics**: http://localhost:8000/metrics - Prometheus metrics
- **Redis**: localhost:6379 - Queue and cache
- **Prometheus**: http://localhost:9090 - Metrics collection
- **Grafana**: http://localhost:3002 - Monitoring dashboards (admin/grafana)

### Frontend Development

#### New Frontend (frontend-new/)
```bash
cd frontend-new

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test
npm run test:coverage

# Build for production
npm run build
```

#### Legacy Frontend (frontend/)
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

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

## Frontend Comparison

| Feature | New Frontend (frontend-new) | Legacy Frontend (frontend) |
|---------|----------------------------|---------------------------|
| **Framework** | React 18 + Vite | Next.js |
| **UI Library** | ShadCN UI + Tailwind | Tailwind CSS |
| **State Management** | React Query + Zustand | React hooks |
| **Testing** | Vitest + Cypress | Jest |
| **Build Tool** | Vite | Next.js |
| **API Integration** | Axios + React Query | Fetch API |
| **Development** | ✅ Active | 🔄 Maintenance |

### Recommended Usage
- **New Projects**: Use `frontend-new/` for modern development experience
- **Existing Projects**: Continue with `frontend/` or migrate gradually
- **Production**: Both are production-ready

## Project Documentation

- [Frontend Integration Guide](Todo%20-%20Frontend.md) - Detailed integration process
- [Wireframes](docs/wireframes/README.md) - UI/UX design
- [API Documentation](http://localhost:8000/docs) - Interactive API docs

## License

MIT License - see LICENSE file for details.
