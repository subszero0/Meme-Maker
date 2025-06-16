@echo off
echo =================================================
echo Health Check for Meme Maker Services
echo =================================================
echo.

echo Checking Docker Desktop...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Desktop is NOT running
    echo Please start Docker Desktop and try again.
    goto end
)
echo ✅ Docker Desktop is running

echo.
echo Checking container status...
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" --filter "name=meme-maker"

echo.
echo Checking health status in detail...
for /f "tokens=1,2" %%i in ('docker ps --format "{{.Names}} {{.Status}}" --filter "name=meme-maker"') do (
    echo %%i: %%j
)

echo.
echo Testing backend health endpoint...
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend health endpoint failed
    echo Checking backend logs:
    docker-compose -f docker-compose.dev.yaml logs --tail=10 backend
) else (
    echo ✅ Backend health endpoint is working
)

echo.
echo Testing Redis connection...
docker exec meme-maker-redis-dev redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ❌ Redis connection failed
) else (
    echo ✅ Redis is responding to ping
)

echo.
echo =================================================
echo Quick Commands:
echo.
echo View logs:
echo   docker-compose -f docker-compose.dev.yaml logs backend
echo   docker-compose -f docker-compose.dev.yaml logs worker
echo   docker-compose -f docker-compose.dev.yaml logs redis
echo.
echo Restart services:
echo   docker-compose -f docker-compose.dev.yaml restart backend
echo   docker-compose -f docker-compose.dev.yaml restart worker
echo.
echo Rebuild services:
echo   docker-compose -f docker-compose.dev.yaml up -d --build
echo =================================================

:end
pause 