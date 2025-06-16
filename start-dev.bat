@echo off
echo Starting Meme Maker Development Environment...
echo.

echo Checking Docker Desktop status...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Desktop is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Docker Desktop is running.
echo.

echo Stopping any existing containers...
docker-compose down >nul 2>&1

echo.
echo Starting backend services with Docker Compose...
docker-compose -f docker-compose.dev.yaml up -d --build redis backend worker

echo.
echo Waiting for services to become healthy...
:wait_for_health
timeout /t 5 /nobreak >nul

REM Check if backend is healthy
docker ps --filter "name=meme-maker-backend-dev" --filter "health=healthy" | findstr "healthy" >nul
if errorlevel 1 (
    echo Waiting for backend to become healthy...
    goto wait_for_health
)

echo.
echo Backend services are healthy!

echo.
echo Starting frontend development server...
cd frontend
start "Frontend Dev Server" cmd /k "npm run dev"

echo.
echo Development environment started successfully!
echo.
echo Services:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - Backend Health: http://localhost:8000/health
echo - Redis: localhost:6379
echo.
echo Health Check Commands:
echo - docker ps (check container health)
echo - docker-compose -f docker-compose.dev.yaml logs backend
echo - docker-compose -f docker-compose.dev.yaml logs worker
echo.
echo To stop services, run: docker-compose -f docker-compose.dev.yaml down
echo.
pause 