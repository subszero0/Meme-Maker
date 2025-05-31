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

### End-to-End Smoke Tests

The E2E smoke tests verify the complete user flow from metadata fetching to clip download. These tests can be run against any deployment (local, staging, production) to verify the entire system is working correctly.

#### Quick Start

```bash
# Run E2E tests against local development server
../scripts/run_smoke_tests.sh

# Run tests against a specific API URL
../scripts/run_smoke_tests.sh --url https://api.yourdomain.com

# Run only quick tests (skip full E2E flow)
../scripts/run_smoke_tests.sh --quick
```

#### Test Coverage

The smoke tests verify:

1. **API Availability** - Health check and docs endpoints are reachable
2. **Metadata Fetching** - POST `/api/v1/metadata` returns valid video information
3. **Job Creation** - POST `/api/v1/jobs` creates jobs and validates inputs properly
4. **Job Processing** - Polling GET `/api/v1/jobs/{id}` until completion
5. **File Download** - Download and verify the generated clip file

#### Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:8000` | API base URL for testing |
| `TEST_VIDEO_URL` | `https://www.youtube.com/watch?v=BaW_jenozKc` | Video URL for test clips |
| `MAX_WAIT_TIMEOUT_SECONDS` | `60` | Maximum time to wait for job completion |
| `PYTEST_ARGS` | - | Additional pytest arguments |

#### Running Tests Manually

```bash
# Set environment and run with pytest directly
export BASE_URL=http://localhost:8000
export TEST_VIDEO_URL=https://www.youtube.com/watch?v=BaW_jenozKc
cd backend/
python -m pytest tests/test_e2e_smoke.py -v

# Run only specific test
python -m pytest tests/test_e2e_smoke.py::TestE2EUserFlow::test_complete_user_flow -v

# Run with verbose output for debugging
python -m pytest tests/test_e2e_smoke.py -v -s
```

#### Test Examples

```bash
# Test against production deployment
BASE_URL=https://api.mememaker.com ../scripts/run_smoke_tests.sh

# Use a different test video
TEST_VIDEO_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ" ../scripts/run_smoke_tests.sh

# Quick health check only
../scripts/run_smoke_tests.sh --quick

# Verbose output for debugging
../scripts/run_smoke_tests.sh --verbose

# Custom timeout for slow connections
../scripts/run_smoke_tests.sh --wait-time 120
```

#### Continuous Integration

Add to your CI pipeline:

```yaml
# Example GitHub Actions step
- name: Run E2E Smoke Tests
  run: |
    export BASE_URL=https://staging.api.mememaker.com
    ./scripts/run_smoke_tests.sh
  env:
    TEST_VIDEO_URL: ${{ secrets.TEST_VIDEO_URL }}
```

#### Test Output

The tests provide detailed progress information:

```
🧪 Meme Maker E2E Smoke Tests
==================================

ℹ️  Configuration:
  📍 API Base URL: http://localhost:8000
  🎬 Test Video: https://www.youtube.com/watch?v=BaW_jenozKc
  📁 Backend Dir: /path/to/backend
  ⚡ Quick Mode: false

ℹ️  Checking environment...
✅ Environment check passed
✅ API is reachable at http://localhost:8000

🔍 Testing E2E flow with URL: https://www.youtube.com/watch?v=BaW_jenozKc
📡 API Base URL: http://localhost:8000

1️⃣ Fetching video metadata...
   ✅ Duration: 123.45 seconds
   ✅ Title: Sample Video Title

2️⃣ Creating clip job...
   ✅ Job created: abc123def456

3️⃣ Polling for job completion...
   📋 Status: queued (after 0.1s)
   📋 Status: working (after 2.3s)
   📊 Progress: 45%
   📋 Status: done (after 15.7s)
   ✅ Job completed successfully
   ✅ Download link: https://s3.amazonaws.com/bucket/file.mp4?presigned...

4️⃣ Downloading clip file...
   ✅ Downloaded clip: 2,547,891 bytes

🎉 Complete E2E flow successful!
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