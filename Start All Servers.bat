@echo off
echo ==========================================
echo    🚀 Starting Meme Maker Local Servers
echo ==========================================
echo.

REM Check if we're in the correct directory
if not exist "backend" (
    echo ❌ Error: backend folder not found!
    echo Please run this script from the Meme-Maker root directory
    pause
    exit /b 1
)

if not exist "frontend-new" (
    echo ❌ Error: frontend-new folder not found!
    echo Please run this script from the Meme-Maker root directory
    pause
    exit /b 1
)

echo 📋 Starting services in order:
echo    1. Redis (Docker)
echo    2. Backend API (FastAPI)
echo    3. RQ Worker
echo    4. Frontend (React/Vite)
echo.

REM Start Redis in Docker
echo 🔴 Starting Redis server...
docker run -d -p 6379:6379 --name redis-meme-maker redis:alpine 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Redis container might already be running, continuing...
) else (
    echo ✅ Redis started successfully
)

REM Wait a moment for Redis to be ready
timeout /t 3 /nobreak >nul

REM Start Backend API
echo.
echo 🔵 Starting Backend API server...
start "Backend API" cmd /k "cd backend && poetry run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
echo ⏳ Waiting for backend to initialize...
timeout /t 8 /nobreak >nul

REM Start RQ Worker
echo.
echo 🟡 Starting RQ Worker...
start "RQ Worker" cmd /k "cd backend && poetry run rq worker clips --url redis://localhost:6379"

REM Wait for worker to start
timeout /t 3 /nobreak >nul

REM Start Frontend
echo.
echo 🟢 Starting Frontend development server...
start "Frontend Dev" cmd /k "cd frontend-new && npm run dev"

echo.
echo ==========================================
echo ✅ All servers are starting up!
echo ==========================================
echo.
echo 🌐 Services will be available at:
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    Health:    http://localhost:8000/health
echo.
echo 📝 Notes:
echo    - Wait ~30 seconds for all services to fully start
echo    - Check the opened terminal windows for any errors
echo    - Press Ctrl+C in any terminal to stop that service
echo    - Frontend now uses the updated interface (Facebook/Instagram/X only)
echo.
echo 🧪 Test the audio fix with:
echo    https://www.instagram.com/reel/DHAwk1mS_5I/?igsh=dW1wdTQydzF6d2F3
echo.
echo ⏹️  To stop all services:
echo    1. Close all terminal windows (Ctrl+C then close)
echo    2. Run: docker stop redis-meme-maker
echo    3. Run: docker rm redis-meme-maker
echo.
pause 