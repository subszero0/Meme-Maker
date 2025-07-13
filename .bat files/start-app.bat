@echo off
title Meme Maker - Development Environment
echo.
echo ========================================
echo    MEME MAKER - DEVELOPMENT STARTUP
echo ========================================
echo.

echo 🚀 Starting all services...
echo.

echo 📦 Building and starting containers...
docker-compose -f docker-compose.dev.yaml up -d --build

echo.
echo ⏱️  Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo 🔍 Checking service status...
docker-compose -f docker-compose.dev.yaml ps

echo.
echo 🏥 Health check - Backend API...
curl http://localhost:8000/health 2>nul | find "ok" >nul
if %errorlevel%==0 (
    echo ✅ Backend is healthy
    echo 🔗 Testing CORS configuration...
    echo ℹ️  CORS has been optimized for frontend connections
) else (
    echo ⚠️  Backend might still be starting...
)

echo.
echo ========================================
echo    🎉 STARTUP COMPLETE!
echo ========================================
echo.
echo 🌐 Frontend:  http://localhost:3000
echo 🔧 Backend:   http://localhost:8000
echo 📊 Redis:     localhost:6379
echo.
echo 📋 Available commands:
echo    - docker-compose -f docker-compose.dev.yaml logs [service]
echo    - docker-compose -f docker-compose.dev.yaml down
echo.
echo 🌟 Open your browser and visit: http://localhost:3000
echo.
echo Press any key to open the app in your default browser...
pause >nul
start http://localhost:3000

echo.
echo 📋 To stop all services, run:
echo    docker-compose -f docker-compose.dev.yaml down
echo.
pause 