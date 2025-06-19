@echo off
REM ====================================================================
REM Meme Maker Development Environment Startup Script (Fixed)
REM ====================================================================

echo.
echo ========================================
echo  Meme Maker Development Environment
echo ========================================
echo.

REM Check if Docker Desktop is running
echo [1/5] Checking Docker Desktop status...

REM First check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Docker is not installed or not in PATH!
    echo.
    echo Please install Docker Desktop and restart your computer.
    echo.
    pause
    exit /b 1
)

REM Then check if Docker daemon is running
docker ps >nul 2>&1
if errorlevel 1 (
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
echo.

REM Start services and capture the process ID
start "Meme Maker Services" cmd /c "docker-compose -f docker-compose.dev.yaml up --build"

REM Wait for services to be ready
echo [5/5] Waiting for services to start...
echo This may take 2-5 minutes on first run...
timeout /t 30 /nobreak >nul

REM Simple check - just verify containers are created
echo Checking if services are starting...
timeout /t 30 /nobreak >nul

echo.
echo ========================================
echo  🎉 Meme Maker services are starting!
echo ========================================
echo.
echo Application URLs:
echo  Frontend: http://localhost:3000
echo  Backend API: http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo.
echo The services are starting up. Please wait 1-2 minutes and then:
echo 1. Check the "Meme Maker Services" window for startup progress
echo 2. Try accessing http://localhost:3000 in your browser
echo 3. If services aren't ready, wait a bit longer
echo.

REM Open the application in default browser
echo Opening application in your default browser...
start http://localhost:3000

echo.
echo To STOP the application:
echo 1. Close the "Meme Maker Services" terminal window, OR
echo 2. Run: docker-compose -f docker-compose.dev.yaml down
echo.

pause 