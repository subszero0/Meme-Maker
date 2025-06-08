# Meme Maker E2E Tests

This directory contains comprehensive end-to-end tests for the complete Meme Maker stack infrastructure, worker functionality, data validation, API testing, TLS configuration, and frontend UI flows.

## Overview

The E2E tests verify the entire system through multiple test suites:

### Core Infrastructure & Worker Tests
1. **Building & Starting Services**: Build all Docker images and start the full stack
2. **Health Checks**: Verify all services (Redis, MinIO, Backend, Worker) are healthy
3. **Backend Tests**: Run the complete backend test suite
4. **Frontend Build**: Build and deploy the frontend static files
5. **Worker Smoke Test**: Process a real 5-second video clip end-to-end
6. **Auto-deletion Test**: Verify files are deleted after first download

### Additional Verification & UI Tests *(NEW)*
1. **Redis & MinIO Data Validation**: Verify data consistency and TTL settings
2. **API Endpoint Testing**: Metadata, CORS, and rate limiting validation
3. **Caddy TLS Configuration**: HTTP→HTTPS redirect and certificate validation
4. **Cypress Frontend E2E**: Complete user workflow testing in browser
5. **Comprehensive Teardown**: Clean resource management with failure diagnostics

## Files

### Core Tests
- `core_infra_and_worker_test.yml` - GitHub Actions CI workflow for infrastructure
- `run_local_test.sh` - Local development script for core tests

### Additional Verification *(NEW)*
- `additional_verification_and_ui_test.yml` - GitHub Actions workflow for comprehensive validation
- `run_additional_verification.sh` - Standalone script for advanced testing

### Documentation
- `README.md` - This comprehensive documentation

## GitHub Actions Workflows

### Core Infrastructure Workflow

The primary workflow (`core_infra_and_worker_test.yml`) runs automatically on:
- Pull requests to `main` branch
- Pushes to `main` branch  
- Manual trigger with optional debug mode

#### Core Workflow Steps

1. **Environment Setup**
   - Checkout code
   - Set up Docker Buildx and Node.js
   - Create test environment configuration
   - Install required tools (jq)

2. **Build & Start Infrastructure**
   - Build all Docker images in parallel
   - Start Redis and MinIO first
   - Create S3 bucket for clips
   - Start backend and worker services

3. **Health Verification**
   - Wait for Redis PING/PONG response
   - Wait for MinIO health endpoint (HTTP 200)
   - Wait for backend `/health` endpoint with `{"status":"ok"}`

4. **Backend Testing**
   - Run full pytest suite inside backend container
   - Auto-recovery: upgrade dependencies and restart on failure
   - Retry tests once after recovery

5. **Frontend Build & Deploy**
   - Build Next.js frontend with `npm run build`
   - Validate `out/index.html` exists
   - Copy static files to backend container
   - Test static file serving at root path

6. **Worker Smoke Test**
   - Enqueue a 5-second clip job using test video
   - Poll job status until completion (max 2 minutes)
   - Download the processed clip and verify file size > 0
   - Verify file is auto-deleted after first download
   - Worker restart/retry on failure

7. **Final Checks & Cleanup**
   - Verify all services still healthy
   - Collect diagnostics on failure
   - Clean up containers and volumes

### Additional Verification Workflow *(NEW)*

The comprehensive workflow (`additional_verification_and_ui_test.yml`) provides deep validation:

#### Job Flow & Dependencies
```
setup_services → data_and_api_checks → caddy_setup_and_tls_check → cypress_ui_tests → teardown_and_cleanup
```

#### Detailed Steps

**1. Setup Services**
- Build and start all core services
- Run worker smoke test and capture job_id
- Pass job_id to subsequent jobs for validation

**2. Data & API Checks**
- **Redis Validation**: Check job key existence, TTL settings
- **MinIO Validation**: Verify object storage and bucket lifecycle
- **Metadata API**: Test video metadata extraction endpoint
- **CORS Testing**: Validate cross-origin preflight requests
- **Rate Limiting**: Verify API rate limiting enforcement

**3. Caddy TLS Setup & Validation**
- Deploy Caddy with self-signed certificates
- Test HTTP→HTTPS redirect (301/308 responses)
- Validate TLS handshake and certificate serving
- Check Caddy logs for certificate acquisition

**4. Cypress UI Tests**
- Create dynamic E2E test specification
- Test complete user workflow: URL → metadata → trim → download
- Validate error handling for invalid URLs
- Capture screenshots/videos on failure
- Upload artifacts for debugging

**5. Teardown & Cleanup**
- Collect final data summary (Redis keys, MinIO objects)
- Capture container logs on failure
- Perform full cleanup on success, basic cleanup on failure
- Generate comprehensive test report

#### Auto-Fix Mechanisms

The workflow includes intelligent auto-fix capabilities:

- **Redis Issues**: Recreate keyspace, scan for alternative patterns
- **MinIO Issues**: Ensure bucket existence, reset aliases
- **Backend Issues**: Health check restart, dependency upgrades
- **Caddy Issues**: Configuration validation, service restart
- **Cypress Issues**: Chrome security workarounds, endpoint retries

## Local Testing

### Core Infrastructure Tests

Run the complete infrastructure test suite locally:

#### Prerequisites

- Docker and Docker Compose
- Node.js and npm (for frontend builds)
- curl and jq utilities

#### Linux/macOS/WSL

```bash
./infra/tests/e2e/run_local_test.sh
```

#### Windows (PowerShell)

```powershell
bash infra/tests/e2e/run_local_test.sh
```

### Additional Verification Tests *(NEW)*

Run comprehensive validation including TLS and UI tests:

#### Prerequisites

Same as core tests, plus:
- Node.js (for Cypress E2E tests)
- Chrome/Chromium browser (for Cypress)

#### Linux/macOS/WSL

```bash
./infra/tests/e2e/run_additional_verification.sh
```

#### Windows (PowerShell)

```powershell
bash infra/tests/e2e/run_additional_verification.sh
```

#### Configuration Options

Control test execution with environment variables:

```bash
# Skip Cypress tests (faster execution)
SKIP_CYPRESS=true ./run_additional_verification.sh

# Enable debug output
DEBUG=true ./run_additional_verification.sh

# Perform full cleanup after tests
FULL_CLEANUP=true ./run_additional_verification.sh

# Combined options
DEBUG=true SKIP_CYPRESS=true FULL_CLEANUP=true ./run_additional_verification.sh
```

#### What the Additional Verification Script Does

1. ✅ **Prerequisites Check** - Verifies Docker, jq, curl, Node.js
2. 🔨 **Service Setup** - Builds and starts all services
3. 🔧 **Worker Smoke Test** - Processes test video and captures job_id
4. 🔍 **Data Validation** - Checks Redis keys and MinIO objects
5. 🧪 **API Testing** - Tests metadata, CORS, rate limiting endpoints
6. 🔒 **TLS Setup** - Configures Caddy with self-signed certificates
7. 🌐 **HTTP/HTTPS Testing** - Validates redirects and TLS handshake
8. 🎭 **Cypress E2E** - Runs browser-based user workflow tests
9. 📊 **Data Summary** - Reports final state of Redis/MinIO
10. 🧹 **Cleanup** - Intelligent cleanup based on test results

### Output Format

Both scripts provide rich, colored output:
- 🔵 **Info messages** - General information and progress
- ✅ **Success messages** - Completed steps and validations
- ⚠️ **Warning messages** - Non-critical issues or skipped steps
- ❌ **Error messages** - Failures requiring attention

## Test Configuration

### Environment Variables

The tests use a comprehensive `.env.test` file:

```env
DEBUG=true
REDIS_URL=redis://redis:6379/0
REDIS_DB=0
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=admin12345
AWS_REGION=us-east-1
AWS_ENDPOINT_URL=http://minio:9000
AWS_ALLOW_HTTP=true
S3_BUCKET=clips
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost","https://localhost"]
MAX_CONCURRENT_JOBS=20
JOB_TIMEOUT=300
RATE_LIMIT=off
MAX_CLIP_SECONDS=180
ENV=test
```

### Test Videos

**Primary Test Video**: Public 10-second Big Buck Bunny clip
`https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/10s.mp4`

**Test Scenarios**:
- **Valid clip**: 5 seconds (00:00:00 to 00:00:05)
- **Metadata test**: Full video for duration/title extraction
- **Error test**: Invalid URLs for error handling validation

### Cypress Test Specifications

The additional verification tests dynamically create Cypress specifications:

```typescript
// Generated test file: cypress/e2e/user_workflow.cy.ts
describe('Complete User Workflow', () => {
  it('should complete the full trim and download workflow', () => {
    // 1. Visit homepage
    // 2. Paste video URL  
    // 3. Wait for metadata loading
    // 4. Verify timeline/slider components
    // 5. Set trim points
    // 6. Click trim/download button
    // 7. Wait for processing completion
    // 8. Verify download link availability
  });
  
  it('should handle errors gracefully', () => {
    // Test invalid URL error handling
  });
});
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check for conflicting services
   docker ps
   # Stop conflicting containers
   docker stop <container_name>
   ```

2. **Docker Build Failures**
   ```bash
   # Clean Docker cache
   docker system prune -f
   # Rebuild with no cache
   docker-compose build --no-cache
   ```

3. **Backend Tests Failing**
   - Check backend logs: `docker logs meme-maker-backend`
   - Verify Redis connection: `docker exec meme-maker-redis redis-cli ping`
   - Check MinIO access: `curl http://localhost:9003/minio/health/ready`

4. **Worker Jobs Failing**
   - Check worker logs: `docker logs meme-maker-worker`
   - Verify test URL is accessible: `curl -I <test_url>`
   - Check S3 bucket exists: `docker exec meme-maker-minio mc ls myminio/clips`

5. **Frontend Build Errors**
   ```bash
   cd frontend
   npm ci
   npm run build
   ```

6. **Caddy TLS Issues** *(NEW)*
   - Check Caddy logs: `docker logs caddy-test`
   - Validate configuration: `docker exec caddy-test caddy fmt --config /etc/caddy/Caddyfile`
   - Test certificate generation: `curl -k https://localhost`

7. **Cypress Test Failures** *(NEW)*
   - Check screenshots: `frontend/cypress/screenshots/`
   - Review videos: `frontend/cypress/videos/`
   - Disable web security: Add `--config chromeWebSecurity=false`
   - Network issues: Ensure `https://localhost` is accessible

### Advanced Debugging

#### Redis Data Inspection
```bash
# List all job keys
docker exec meme-maker-redis redis-cli --scan --pattern "*job*"

# Check specific job TTL
docker exec meme-maker-redis redis-cli TTL job:YOUR_JOB_ID

# View job data
docker exec meme-maker-redis redis-cli GET job:YOUR_JOB_ID
```

#### MinIO Object Investigation
```bash
# Setup MinIO client
docker exec meme-maker-minio mc alias set local http://localhost:9000 admin admin12345

# List bucket contents
docker exec meme-maker-minio mc ls local/clips

# Get object info
docker exec meme-maker-minio mc stat local/clips/YOUR_JOB_ID.mp4
```

#### API Endpoint Testing
```bash
# Test metadata endpoint
curl -X POST http://localhost:8000/api/v1/metadata \
  -H "Content-Type: application/json" \
  -d '{"url":"https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/10s.mp4"}'

# Test CORS preflight
curl -X OPTIONS http://localhost:8000/api/v1/jobs \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Test job creation
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"url":"https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/10s.mp4","start":"00:00:00","end":"00:00:05"}'
```

### Manual Component Testing

#### Individual Service Tests
```bash
# Test backend health
curl http://localhost:8000/health

# Test Redis connectivity
docker exec meme-maker-redis redis-cli ping

# Test MinIO health
curl http://localhost:9003/minio/health/ready

# Test Caddy HTTPS redirect
curl -v http://localhost
curl -k -v https://localhost
```

## Integration with Existing Workflows

This comprehensive E2E test suite complements existing workflows:

- **smoke-tests.yml** - Basic API and frontend smoke tests
- **ci-cd.yml** - Unit tests and deployment pipelines
- **bundle-audit.yml** - Frontend bundle size and performance analysis
- **visual-regression.yml** - UI visual testing and screenshot comparison
- **security-audit.yml** - Dependency and security vulnerability scanning

### Recommended Test Order

1. **Core Infrastructure** (`core_infra_and_worker_test.yml`) - Validates basic functionality
2. **Additional Verification** (`additional_verification_and_ui_test.yml`) - Deep validation and UI testing
3. **Deployment Workflows** - Only after E2E validation passes

## Performance Expectations

### Typical Runtime

| Test Suite | CI Environment | Local Development |
|------------|----------------|-------------------|
| **Core Infrastructure** | 8-12 minutes | 5-8 minutes |
| **Additional Verification** | 15-20 minutes | 10-15 minutes |
| **Combined (Sequential)** | 25-30 minutes | 15-20 minutes |

### Resource Usage

| Component | CPU | Memory | Disk | Network |
|-----------|-----|--------|------|---------|
| **Core Services** | Moderate | ~2GB | ~1GB | ~5MB download |
| **Caddy TLS** | Low | ~100MB | ~50MB | Minimal |
| **Cypress Tests** | High | ~1GB | ~200MB | ~10MB |
| **Total Peak** | High | ~3GB | ~1.5GB | ~15MB |

## Success Criteria

### Core Infrastructure Tests

All tests pass when:

✅ Docker Compose builds all images without error  
✅ All services start and pass health checks  
✅ Backend test suite passes (with auto-recovery if needed)  
✅ Frontend builds and serves static files  
✅ Worker processes 5-second clip successfully  
✅ Download URL works once then auto-deletes  
✅ All containers remain healthy throughout test  

### Additional Verification Tests *(NEW)*

All advanced tests pass when:

✅ Redis key `job:{job_id}` exists with TTL > 0  
✅ MinIO bucket `clips` contains `{job_id}.mp4` until download  
✅ Metadata endpoint returns valid JSON with title and duration  
✅ CORS preflight on `/api/v1/jobs` returns HTTP 204  
✅ Rate limiter returns HTTP 429 on excessive requests  
✅ `curl http://localhost` returns 301/308 redirect to HTTPS  
✅ `curl -k https://localhost` reports successful TLS handshake  
✅ Caddy logs contain certificate acquisition/serving messages  
✅ Cypress E2E completes user workflow from URL → download  
✅ Error handling works for invalid URLs  
✅ All containers are cleanly torn down  
✅ Failure diagnostics are captured and logged  

### Combined Success

The complete test suite validates the core value proposition:

> **"Paste URL → fetch metadata → trim with timeline → process with worker → download via presigned URL → auto-delete after download"**

...works end-to-end with proper data consistency, API behavior, TLS security, and user experience validation. 