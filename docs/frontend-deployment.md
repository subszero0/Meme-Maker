# Frontend Deployment Architecture

This document explains how the Meme Maker frontend is deployed and served in production.

## Overview

The Meme Maker uses a **hybrid deployment approach** where:

1. **Frontend**: Next.js app built as static files and served by FastAPI
2. **Backend**: FastAPI serves both API routes and frontend files
3. **Reverse Proxy**: Caddy handles caching, security headers, and request routing

## Architecture Flow

```
Internet → Caddy (memeit.pro) → FastAPI Container
           ├── Cache static assets (/_next/*, *.js, *.css)
           ├── Proxy API routes (/api/*, /health, /docs)
           └── Proxy SPA routes (/, client-side routes)
```

## Components

### 1. Frontend Build Process

**Location**: `frontend/`
**Output**: `frontend/out/` (static files)

```bash
cd frontend
npm run build  # Creates frontend/out/ directory
```

**Configuration**: `next.config.ts`
```typescript
const nextConfig: NextConfig = {
  output: 'export',        // Static export
  trailingSlash: true,     // Ensure proper routing
  images: {
    unoptimized: true      // No Next.js image optimization
  }
};
```

### 2. Docker Integration

**File**: `Dockerfile.backend`

The Dockerfile uses a **multi-stage build**:

1. **Stage 1 (frontend-builder)**: Builds the Next.js app
2. **Stage 2 (backend)**: Copies frontend build to `/app/static`

```dockerfile
# Frontend build stage
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Backend stage  
FROM python:3.12-alpine
WORKDIR /app
# ... backend setup ...
COPY --from=frontend-builder /app/frontend/out ./static
```

### 3. FastAPI Static Serving

**File**: `backend/app/main.py`

FastAPI handles both API routes and frontend serving:

```python
STATIC_DIR = Path("/app/static")

if STATIC_DIR.exists():
    # Mount static files at /static
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't serve frontend for API routes
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health", "metrics", "static/")):
            raise HTTPException(status_code=404)
        
        # Try to serve the requested file directly
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # For SPA routing, serve index.html
        index_path = STATIC_DIR / "index.html"
        if index_path.is_file():
            return FileResponse(index_path, media_type="text/html")
        
        raise HTTPException(status_code=404, detail="Frontend not available")
```

### 4. Caddy Configuration

**File**: `Caddyfile`

Caddy acts as the reverse proxy with intelligent caching:

```caddy
memeit.pro {
    # API routes - no caching
    @api path /api/* /health /metrics /docs /redoc /openapi.json
    handle @api {
        reverse_proxy 127.0.0.1:8000
    }
    
    # Static assets - long cache
    @static path /_next/* /static/* *.js *.css *.ico *.png *.jpg *.jpeg *.gif *.svg *.woff *.woff2
    handle @static {
        header Cache-Control "public, max-age=31536000, immutable"
        reverse_proxy 127.0.0.1:8000
    }
    
    # HTML/SPA routes - no cache
    handle {
        header Cache-Control "no-cache, no-store, must-revalidate"
        reverse_proxy 127.0.0.1:8000
    }
}
```

## Request Routing

| Request Type | Path Examples | Caddy Behavior | FastAPI Behavior |
|-------------|---------------|----------------|------------------|
| **API** | `/api/v1/jobs`, `/health` | Proxy to FastAPI, no cache | Serve API response |
| **Static Assets** | `/_next/static/js/app.js`, `/favicon.ico` | Proxy to FastAPI, cache 1 year | Serve file from `/app/static` |
| **SPA Routes** | `/`, `/about`, `/dashboard` | Proxy to FastAPI, no cache | Serve `index.html` |
| **Backend Routes** | `/docs`, `/metrics` | Proxy to FastAPI, no cache | Serve FastAPI docs/metrics |

## Deployment Process

### 1. Local Build
```bash
cd frontend
npm run build  # Creates frontend/out/
```

### 2. Deploy to VPS
```bash
export DEPLOY_SSH="ubuntu@your-server -i ~/.ssh/key"
./scripts/deploy_to_vps.sh
```

**What happens during deployment:**
1. Pull latest code (includes new `Caddyfile`)
2. Docker builds frontend in container 
3. Frontend files copied to `/app/static` in container
4. Restart Docker containers
5. Copy `Caddyfile` to `/etc/caddy/`
6. Restart Caddy
7. Health checks

### 3. Verification

```bash
# Frontend UI
curl -f https://memeit.pro/

# API endpoints  
curl -f https://memeit.pro/api/v1/jobs
curl -f https://memeit.pro/health

# Static assets
curl -f https://memeit.pro/favicon.ico
```

## Configuration Files

| File | Purpose |
|------|---------|
| `frontend/next.config.ts` | Next.js static export config |
| `Dockerfile.backend` | Multi-stage build with frontend |
| `backend/app/main.py` | FastAPI static file serving |
| `Caddyfile` | Production reverse proxy config |
| `Caddyfile.dev` | Development reverse proxy config |

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Frontend API base URL | `https://memeit.pro` |
| `CORS_ORIGINS` | Backend CORS settings | `https://memeit.pro` |

## Benefits of This Architecture

1. **Simplicity**: Single container deployment
2. **Performance**: Caddy caches static assets
3. **SEO**: Proper HTML serving for SPA routes
4. **Security**: Caddy handles security headers
5. **Efficiency**: No separate nginx/apache needed
6. **Development**: Same container works locally and in production

## Troubleshooting

### Frontend not loading
- Check if `/app/static/index.html` exists in container
- Verify FastAPI logs for static file serving errors
- Check Caddy logs: `sudo journalctl -u caddy -f`

### API requests failing
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS configuration in backend
- Ensure API routes don't conflict with static paths

### Static assets not loading
- Check if `/_next/` paths are being served correctly
- Verify Caddy cache headers are set
- Test asset serving: `curl -I https://memeit.pro/_next/static/...`

## Testing

Run the test script to verify everything works:

```bash
./scripts/test_frontend_serving.sh
```

Manual verification:
1. Visit `https://memeit.pro` - should show Meme Maker UI
2. Visit `https://memeit.pro/docs` - should show FastAPI docs
3. Check browser dev tools - static assets should load with proper cache headers 