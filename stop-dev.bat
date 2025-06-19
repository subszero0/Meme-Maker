@echo off
REM ====================================================================
REM Meme Maker Development Environment Shutdown Script
REM ====================================================================
REM 
REM This script will:
REM 1. Stop all Docker containers
REM 2. Clean up Docker resources
REM 3. Close any development terminals
REM ====================================================================

echo.
echo ========================================
echo  Stopping Meme Maker Development Environment
echo ========================================
echo.

echo [1/3] Stopping all Docker services...
docker-compose -f docker-compose.dev.yaml down

if errorlevel 1 (
    echo ❌ Warning: Some services may not have stopped cleanly
) else (
    echo ✅ All Docker services stopped successfully
)

echo.
echo [2/3] Cleaning up Docker resources...
docker-compose -f docker-compose.dev.yaml down --volumes --remove-orphans >nul 2>&1
echo ✅ Docker resources cleaned up

echo.
echo [3/3] Checking for running processes...

REM Kill any remaining processes on our ports
for %%p in (3000 8000 6379) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p ^| findstr LISTENING') do (
        echo Stopping process on port %%p...
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo ✅ All processes stopped

echo.
echo ========================================
echo  🛑 Meme Maker Development Environment Stopped
echo ========================================
echo.
echo All services have been stopped and cleaned up:
echo  ✅ Redis (Database)
echo  ✅ Backend API
echo  ✅ Worker (Video Processing)  
echo  ✅ Frontend
echo  ✅ Docker volumes and networks
echo.
echo To start the development environment again:
echo  - Run: start-dev.bat
echo  - Or see StartUp.md for manual startup instructions
echo.

pause 