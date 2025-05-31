# Rate Limiting & Abuse Protection

This document describes the rate limiting implementation in Meme Maker API to prevent abuse and ensure fair usage.

## Overview

The application implements a two-tier rate limiting system:

1. **Global Rate Limit**: Applies to all API endpoints
2. **Job Creation Rate Limit**: Specific limit for video clipping jobs

## Rate Limiting Rules

### Global Rate Limit
- **Limit**: 10 requests per minute per IP address
- **Applies to**: All `/api/v1/*` endpoints (metadata, jobs)
- **Purpose**: Prevent general API abuse

### Job Creation Rate Limit
- **Limit**: 3 job creations per hour per IP address
- **Applies to**: `POST /api/v1/jobs` endpoint only
- **Purpose**: Prevent video processing resource abuse

## Technical Implementation

### Backend (FastAPI)

#### Dependencies
- `fastapi-limiter==0.1.6` - Rate limiting implementation
- `aioredis==2.0.1` - Redis backend for storing rate limit counters

#### Configuration
Rate limits are configurable via environment variables:

```bash
# Global rate limiting
GLOBAL_RATE_LIMIT_REQUESTS=10  # requests per minute
GLOBAL_RATE_LIMIT_WINDOW=60    # window in seconds

# Job creation rate limiting  
JOB_RATE_LIMIT_REQUESTS=3      # requests per hour
JOB_RATE_LIMIT_WINDOW=3600     # window in seconds
```

#### IP Detection
The system extracts client IP addresses from requests with proper proxy support:

1. `X-Forwarded-For` header (first IP in chain)
2. `X-Real-IP` header
3. Direct connection IP (fallback)

#### Rate Limit Keys
- Global limits: `global_rate_limit:{client_ip}`
- Job limits: `job_rate_limit:{client_ip}`

This ensures different rate limit types operate independently.

#### Error Responses
When rate limits are exceeded, the API returns:

```json
{
  "detail": "Rate limit exceeded. You can make 10 requests per minute. Please try again in 45 seconds.",
  "retry_after": 45,
  "limit_type": "global"
}
```

**Headers:**
- `Retry-After: 45` - Standard HTTP header for retry timing

### Frontend (Next.js)

#### Error Handling
The frontend detects 429 responses and shows user-friendly notifications:

- **Rate Limit Error Class**: Custom error type with retry timing
- **Notification Component**: Visual countdown timer with progress bar
- **UI Disabling**: Buttons disabled during rate limit period
- **Auto-Recovery**: UI re-enables when limit expires

#### Notification Features
- Different styling for global vs job creation limits
- Live countdown timer showing remaining time
- Progress bar animation
- Dismissible notifications
- Automatic retry enablement

## API Documentation

### Rate Limited Endpoints

#### `POST /api/v1/metadata`
- Global rate limit: 10 requests/minute
- Returns video metadata for trimming UI

#### `POST /api/v1/jobs`
- Global rate limit: 10 requests/minute  
- Job creation limit: 3 requests/hour
- Creates video clipping jobs

#### `GET /api/v1/jobs/{id}`
- Global rate limit: 10 requests/minute
- Polls job status and retrieves download links

### Non-Rate Limited Endpoints

The following endpoints are **not** rate limited:
- `GET /health` - Health check
- `GET /docs` - API documentation
- `GET /metrics` - Prometheus metrics

## Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/test_rate_limit.py -v
```

Tests cover:
- Rate limit enforcement
- IP extraction from headers
- Error response format
- Configuration loading

### Frontend Tests
```bash
cd frontend
npm run cypress:run -- --spec cypress/e2e/rate_limiting.cy.ts
```

E2E tests cover:
- 429 error handling
- Notification display
- Countdown timer functionality
- UI state management

### Manual Testing

#### Trigger Global Rate Limit
```bash
# Make rapid requests to exceed limit
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/v1/metadata \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'
  echo
done
```

#### Trigger Job Creation Rate Limit
```bash
# Create multiple jobs quickly  
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com", "start_seconds": 0, "end_seconds": 10, "rights": true}'
  echo
done
```

## Monitoring

### Metrics
Rate limiting events are tracked in Prometheus metrics:
- `rate_limit_denied_total` - Counter of rejected requests

### Logging
Rate limit violations are logged with:
- Client IP address
- API endpoint
- Timestamp

## Production Considerations

### Redis Configuration
- Use Redis cluster for high availability
- Configure appropriate memory limits
- Set up Redis persistence for rate limit state

### Load Balancer Setup
Ensure load balancers pass real client IPs:

**Nginx:**
```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Real-IP $remote_addr;
```

**Cloudflare:**
- Automatically sets `CF-Connecting-IP` header
- Code handles standard `X-Forwarded-For` format

### Rate Limit Tuning
Monitor usage patterns and adjust limits:
- Increase global limit for legitimate high-volume users
- Decrease job creation limit during high demand
- Implement user-specific limits for authenticated users

## Security Notes

### IP Spoofing Protection
- Validate proxy headers in production
- Consider implementing additional authentication
- Monitor for suspicious patterns

### Rate Limit Bypass Prevention
- Ensure Redis is not directly accessible
- Validate all rate limit configuration
- Regular security audits of limit logic

## Troubleshooting

### Common Issues

#### Rate Limits Not Working
1. Check Redis connection: `redis-cli ping`
2. Verify environment variables loaded
3. Check FastAPI startup logs for rate limiting initialization

#### Incorrect IP Detection
1. Verify proxy headers: `X-Forwarded-For`, `X-Real-IP`
2. Check load balancer configuration
3. Test with `curl -H "X-Forwarded-For: test-ip"`

#### Frontend Not Showing Notifications
1. Check browser console for JavaScript errors
2. Verify API returns proper 429 response format
3. Test with manual 429 response in DevTools

### Debug Commands

```bash
# Check rate limit configuration
cd backend
python -c "from app.config import settings; print(f'Global: {settings.global_rate_limit_requests}/{settings.global_rate_limit_window}s, Jobs: {settings.job_rate_limit_requests}/{settings.job_rate_limit_window}s')"

# Test IP extraction
python -c "
from app.ratelimit import get_client_ip
from unittest.mock import Mock
req = Mock()
req.headers = {'X-Forwarded-For': '1.2.3.4, 5.6.7.8'}
req.client.host = '127.0.0.1'
print(f'Detected IP: {get_client_ip(req)}')
"
```

## Future Enhancements

1. **User-based Rate Limiting**: Implement per-user limits for authenticated users
2. **Dynamic Rate Limiting**: Adjust limits based on system load
3. **Geographic Rate Limiting**: Different limits by region
4. **Rate Limit Analytics**: Detailed usage patterns and abuse detection 