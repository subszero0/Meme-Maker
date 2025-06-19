@echo off
REM ====================================================================
REM Meme Maker Development Environment Startup Script
REM ====================================================================

echo.
echo ========================================
echo  Meme Maker Development Environment
echo ========================================
echo.

REM Check if Docker is working
echo [1/5] Checking Docker Desktop status...

docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: Docker Desktop is not running!
    echo.
    echo Please:
    echo 1. Open Docker Desktop from your Start menu
    echo 2. Wait for it to fully start (green whale icon in system tray)
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Docker Desktop is running

REM Check if .env file exists, create if not
echo.
echo [2/5] Setting up environment configuration...
if not exist ".env" (
    echo Creating .env file from template...
    copy env.template .env >nul
    if errorlevel 1 (
        echo ❌ ERROR: Could not create .env file
        pause
        exit /b 1
    )
    echo ✅ Created .env file from template
) else (
    echo ✅ Environment file already exists
)

REM Stop any existing containers
echo.
echo [3/5] Cleaning up any existing containers...
docker-compose -f docker-compose.dev.yaml down >nul 2>&1
echo ✅ Cleaned up existing containers

REM Start all services
echo.
echo [4/5] Starting all services (this may take a few minutes)...
echo.
echo Starting:
echo - Redis (Database)
echo - Backend API (Python FastAPI)
echo - Worker (Video Processing)
echo - Frontend (React/Vite)
echo.
echo Please wait while Docker builds and starts all services...
echo (You'll see logs from all services below)
echo.

REM Start services and capture the process ID
start "Meme Maker Services" /min cmd /c "docker-compose -f docker-compose.dev.yaml up --build"

REM Wait for services to be ready
echo [5/5] Waiting for services to start...
timeout /t 10 /nobreak >nul

:wait_for_services
echo Checking if services are ready...

REM Check if backend container is healthy
docker ps --filter "name=meme-maker-backend-dev" --filter "health=healthy" | findstr "healthy" >nul 2>&1
set backend_ready=%errorlevel%

REM Check if frontend container is running
docker ps --filter "name=meme-maker-frontend-dev" | findstr "meme-maker-frontend-dev" >nul 2>&1
set frontend_ready=%errorlevel%

if %backend_ready% equ 0 if %frontend_ready% equ 0 (
    echo ✅ All services are ready!
    goto services_ready
)

echo Waiting for services to start... (this may take up to 2 minutes)
timeout /t 15 /nobreak >nul
goto wait_for_services

:services_ready
echo.
echo ========================================
echo  🎉 Meme Maker is now running!
echo ========================================
echo.
echo Application URLs:
echo  Frontend: http://localhost:3000
echo  Backend API: http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo.
echo Services Status:
echo  ✅ Redis (Database)
echo  ✅ Backend API
echo  ✅ Worker (Video Processing)
echo  ✅ Frontend
echo.

REM Open the application in default browser
echo Opening application in your default browser...
start http://localhost:3000

echo.
echo ========================================
echo  Development Environment Active
echo ========================================
echo.
echo The application is now running. You can:
echo.
echo 1. Use the web application at: http://localhost:3000
echo 2. View API documentation at: http://localhost:8000/docs
echo 3. Monitor logs in the "Meme Maker Services" window
echo.
echo To STOP the application:
echo 1. Close the "Meme Maker Services" terminal window, OR
echo 2. Run: docker-compose -f docker-compose.dev.yaml down
echo.
echo For development with local backend/frontend, see StartUp.md
echo.

echo Press any key to continue (services will keep running)...
pause >nul

echo.
echo Services are still running in the background.
echo Check the "Meme Maker Services" window for logs.
echo.
echo To stop all services, run:
echo   docker-compose -f docker-compose.dev.yaml down
echo.

exit /b 0 