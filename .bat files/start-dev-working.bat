@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Meme Maker Development Environment
echo ========================================
echo.

echo Starting Meme Maker...

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating environment file...
    copy env.template .env >nul 2>&1
)

echo.
echo Starting Docker services...
echo This may take 2-5 minutes on first run.
echo.

REM Start all services
docker-compose -f docker-compose.dev.yaml up --build

echo.
echo Services stopped. To restart, run this script again.
pause 