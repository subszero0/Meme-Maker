# Smoke Test Documentation

## Overview

The smoke test validates the end-to-end functionality of the Meme Maker application by:

1. Creating a video clipping job with a known test video
2. Polling the job status until completion
3. Downloading the result and validating the duration with FFmpeg

## Test Configuration

- **Test Video**: https://filesamples.com/samples/video/mp4/sample_640x360.mp4
- **Clip**: 5 seconds (from 00:00:02 to 00:00:07)
- **Timeout**: 120 seconds maximum
- **Expected Duration**: 5.0 ± 0.5 seconds

## GitHub Actions Workflow

The smoke test runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

### Services

The workflow spins up a complete test environment:
- **Redis**: Message queue for job processing
- **MinIO**: S3-compatible object storage
- **Backend**: FastAPI application
- **Worker**: Video processing service

### Runtime

- **Target**: < 5 minutes total runtime
- **Timeout**: 8 minutes maximum
- **Artifacts**: None (test files are cleaned up)

## Manual Testing

You can run the smoke test locally:

```bash
# Start the development stack
docker-compose up -d

# Wait for services to be ready
curl http://localhost:8000/health

# Run the smoke test
python tools/smoke.py
```

## Build Status Badge

Add this badge to your README.md to show the current test status:

```markdown
[![Smoke Test](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Smoke%20Test/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/smoke-test.yml)
```

Replace `YOUR_USERNAME` and `YOUR_REPO` with your actual GitHub username and repository name.

## Troubleshooting

### Common Issues

1. **Service startup timeout**: Services may take longer to start on slower runners
2. **Network connectivity**: External video download may fail in restricted environments
3. **FFmpeg not found**: Ensure FFmpeg is installed for duration validation

### Debugging

View service logs when the test fails:
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs worker
```

### Test Validation

The smoke test validates:
- ✅ Job creation returns 202 status
- ✅ Job transitions: queued → working → done
- ✅ Download URL is provided
- ✅ File downloads successfully
- ✅ Clip duration matches expected value (±0.5s)

## Integration with CI/CD

The smoke test is designed to be a fast quality gate:
- Runs in parallel with other tests
- Fails fast on critical issues
- Provides detailed logs for debugging
- Cleans up resources automatically 