# Meme Maker Backend

FastAPI backend service for the Meme Maker video clipping application.

## Features

- **Health Check**: Simple endpoint to verify service status
- **Job Management**: Create and track video clipping jobs
- **Metadata Extraction**: Get video information from URLs
- **Input Validation**: Pydantic models for request/response validation
- **Security Headers**: Comprehensive security headers middleware
- **CORS Support**: Configurable CORS origins with environment variable support

## Security

The application includes a comprehensive security headers middleware that adds the following headers to all responses:

| Header | Value |
|--------|-------|
| **Strict-Transport-Security** | `max-age=63072000; includeSubDomains; preload` |
| **Content-Security-Policy**   | `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'` |
| **X-Content-Type-Options**    | `nosniff` |
| **X-Frame-Options**           | `DENY` |
| **Referrer-Policy**           | `no-referrer` |
| **Permissions-Policy**        | `camera=(), microphone=(), geolocation=(), interest-cohort=()` |
| **Access-Control-Allow-Origin** | Value from `CORS_ORIGINS` environment variable |

### CORS Configuration

CORS origins can be configured using the `CORS_ORIGINS` environment variable:

- **Single origin**: `CORS_ORIGINS=https://yourdomain.com`
- **Multiple origins**: `CORS_ORIGINS=https://app.com,https://admin.app.com`
- **Development (all origins)**: `CORS_ORIGINS=*`

The middleware will log a warning if wildcard CORS is used in production mode.

## API Endpoints

### Health
- `GET /health` - Service health check

### Jobs
- `POST /api/v1/jobs` - Create a new video clipping job
- `GET /api/v1/jobs/{id}` - Get job status and download URL

### Metadata
- `POST /api/v1/metadata` - Get video metadata from URL

## Setup

### Prerequisites
- Python 3.12+
- Poetry (recommended) or pip

### Installation

Using Poetry:
```bash
poetry install
```

Using pip:
```bash
pip install -r requirements.txt
```

### Configuration

Environment variables (optional):
- `DEBUG` - Enable debug mode
- `REDIS_URL` - Redis connection URL
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `S3_BUCKET_NAME` - S3 bucket for file storage

## Running

### Development Server
```bash
# Using Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Using pip
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Testing

Run all tests:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_health.py -v
```

## Docker

Build image:
```bash
docker build -f ../Dockerfile.backend -t meme-maker-backend .
```

Run container:
```bash
docker run -p 8000:8000 meme-maker-backend
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── jobs.py          # Job management endpoints
│   │   └── metadata.py      # Metadata endpoints
│   ├── middleware/
│   │   └── security_headers.py  # Security headers middleware
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   └── config.py            # Settings and configuration
├── tests/
│   ├── test_health.py       # Health endpoint tests
│   ├── test_security_middleware.py  # Security middleware tests
│   └── test_api.py          # API endpoint tests
├── pyproject.toml           # Poetry configuration
└── requirements.txt         # Pip requirements
```

## Development

This is a placeholder implementation with stub endpoints. The actual video processing logic will be implemented in the worker service.

### Code Quality

The project uses:
- **MyPy** for static type checking
- **Black** for code formatting
- **isort** for import sorting
- **pytest** for testing

Run quality checks:
```bash
mypy app/
black app/ tests/
isort app/ tests/
pytest
``` 