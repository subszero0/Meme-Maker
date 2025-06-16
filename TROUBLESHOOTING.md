# Troubleshooting Guide

## Common Issues and Solutions

### 1. Backend Container Becomes Unhealthy

**Error**: `docker ps` shows backend container as "unhealthy"

**Root Causes & Solutions**:

#### **Problem**: Health check using missing dependencies
- **Old Issue**: Health check was using `requests` library not installed in container
- ✅ **Fixed**: Now uses `curl` which is pre-installed

#### **Problem**: Missing environment variables
- **Old Issue**: `REDIS_URL` not set causing connection failures
- ✅ **Fixed**: Added proper environment variables to all services

#### **Problem**: No automatic restart on failure
- ✅ **Fixed**: Added `restart: unless-stopped` policy to all services

**Quick Fix Commands**:
```bash
# Check health status
./health-check.bat

# Restart unhealthy service
docker-compose -f docker-compose.dev.yaml restart backend

# Rebuild if needed
docker-compose -f docker-compose.dev.yaml up -d --build backend
```

---

### 2. Difference: Docker Backend vs Direct Backend

**Docker Backend** (`docker-compose up`):
- ✅ Runs in isolated container environment
- ✅ Production-like setup with health checks
- ✅ Automatic restart on failure
- ✅ Uses container networking
- ✅ Managed dependencies and environment

**Direct Backend** (`poetry run uvicorn...`):
- ❌ Runs on host machine directly
- ❌ No health checks or automatic restart
- ❌ Uses host networking (localhost)
- ❌ Relies on local Python environment
- ✅ Faster development iteration

**Recommendation**: Use Docker for testing production-like behavior, direct backend for rapid development.

---

### 3. Hydration Mismatch Errors

**Error**: `A tree hydrated but some attributes of the server rendered HTML didn't match the client properties`

**Cause**: Browser extensions (like uBlock Origin, AdBlock Plus, privacy extensions) modify the HTML after it loads, adding attributes like `data-google-analytics-opt-out=""`.

**Solution**: ✅ **Already Fixed**
- Added `suppressHydrationWarning` to the HTML element in `layout.tsx`
- Added client-side error suppression for common browser extension errors
- These changes prevent the hydration warnings without affecting functionality

---

### 4. Jobs Stuck in "Waiting in Queue"

**Error**: Jobs remain in "Waiting in queue..." status indefinitely

**Cause**: Docker services (especially the worker) are not running

**Solutions**:

#### Option A: Use the Development Script (Recommended)
1. Ensure Docker Desktop is running
2. Run the provided batch script:
   ```bash
   ./start-dev.bat
   ```

#### Option B: Manual Setup
1. Start Docker Desktop
2. Run the backend services:
   ```bash
   docker-compose -f docker-compose.dev.yaml up -d redis backend worker
   ```
3. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

**Verification**:
```bash
# Check if services are running and healthy
./health-check.bat

# Or manually check
docker ps
```

---

### 5. RegisterClientLocalizationsError

**Error**: `RegisterClientLocalizationsError: Could not establish connection. Receiving end does not exist.`

**Cause**: Browser extension trying to communicate with its background script

**Solution**: ✅ **Already Fixed**
- Added global error handlers to suppress these extension-related errors
- These errors are harmless and don't affect the application functionality

---

### 6. Network Connection Errors

**Error**: "Cannot connect to backend" or similar network errors

**Possible Causes & Solutions**:

1. **Backend not running**:
   ```bash
   docker-compose -f docker-compose.dev.yaml up -d backend
   ```

2. **Backend unhealthy**:
   ```bash
   ./health-check.bat
   docker-compose -f docker-compose.dev.yaml restart backend
   ```

3. **Wrong API URL**:
   - Check `NEXT_PUBLIC_API_URL` in your environment
   - Default should be `http://localhost:8000`

4. **Port conflicts**:
   - Ensure ports 8000, 6379, and 3000 are not used by other applications
   - Check with: `netstat -an | findstr :8000`

---

### 7. Docker Issues

**Common Docker Problems**:

1. **Docker Desktop not running**:
   - Start Docker Desktop application
   - Wait for it to fully initialize

2. **Permission errors**:
   ```bash
   # On Windows, run PowerShell as Administrator
   docker-compose down
   docker-compose -f docker-compose.dev.yaml up -d
   ```

3. **Port conflicts**:
   ```bash
   # Check what's using the ports
   netstat -an | findstr :8000
   netstat -an | findstr :6379
   ```

4. **Container build issues**:
   ```bash
   # Rebuild containers
   docker-compose -f docker-compose.dev.yaml down
   docker-compose -f docker-compose.dev.yaml up -d --build
   ```

---

### 8. Video Processing Issues

**If videos fail to process**:

1. **Check worker logs**:
   ```bash
   docker-compose -f docker-compose.dev.yaml logs worker
   ```

2. **Check backend logs**:
   ```bash
   docker-compose -f docker-compose.dev.yaml logs backend
   ```

3. **Restart worker**:
   ```bash
   docker-compose -f docker-compose.dev.yaml restart worker
   ```

---

## Development Environment Setup

### Quick Start
1. Ensure Docker Desktop is running
2. Run: `./start-dev.bat`
3. Wait for health checks to pass
4. Access the app at http://localhost:3000

### Health Monitoring
```bash
# Quick health check
./health-check.bat

# Monitor logs in real-time
docker-compose -f docker-compose.dev.yaml logs -f backend worker
```

### Manual Setup
```bash
# Terminal 1: Backend services with health checks
docker-compose -f docker-compose.dev.yaml up -d redis backend worker

# Wait for healthy status
docker ps --filter "health=healthy"

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Stopping Services
```bash
# Stop all services
docker-compose -f docker-compose.dev.yaml down

# Stop specific service
docker-compose -f docker-compose.dev.yaml stop worker
```

---

## Health Checks & Monitoring

### New Health Check Features ✅
- **Automatic health monitoring** for all services
- **Restart policies** - containers automatically restart if they become unhealthy
- **Service dependencies** - services wait for dependencies to be healthy
- **Health check script** - `./health-check.bat` for easy status monitoring

### Verify Services are Healthy
```bash
# Quick health check (NEW!)
./health-check.bat

# Check Docker containers
docker ps

# Check backend health endpoint
curl http://localhost:8000/health

# Check Redis connection
docker exec meme-maker-redis-dev redis-cli ping
```

### Check Logs
```bash
# All services
docker-compose -f docker-compose.dev.yaml logs

# Specific service
docker-compose -f docker-compose.dev.yaml logs backend
docker-compose -f docker-compose.dev.yaml logs worker
docker-compose -f docker-compose.dev.yaml logs redis

# Follow logs in real-time
docker-compose -f docker-compose.dev.yaml logs -f backend
```

---

## Environment Variables

Ensure these are set correctly:

**Frontend (.env.local)**:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend** (now set automatically):
```
REDIS_URL=redis://redis:6379
ENVIRONMENT=development
DEBUG=true
```

---

## Still Having Issues?

1. **Run the health check script**: `./health-check.bat`
2. **Clear Docker state**:
   ```bash
   docker-compose -f docker-compose.dev.yaml down -v
   docker-compose -f docker-compose.dev.yaml up -d --build
   ```
3. **Check system resources** (CPU, Memory, Disk space)
4. **Update Docker Desktop to the latest version**
5. **Run services individually to isolate the problem**:
   ```bash
   docker-compose -f docker-compose.dev.yaml up redis
   docker-compose -f docker-compose.dev.yaml up backend
   docker-compose -f docker-compose.dev.yaml up worker
   ``` 