@echo off
ECHO "================================================================================================================"
ECHO "Starting Meme Maker Development Environment..."
ECHO "This will open four separate terminal windows for:"
ECHO "1. Redis Server (In-memory database)"
ECHO "2. Backend Server (FastAPI)"
ECHO "3. Background Worker (Celery/RQ)"
ECHO "4. Frontend Server (Vite)"
ECHO "================================================================================================================"
ECHO.
PAUSE

:: Set the project root directory
set "PROJECT_ROOT=%~dp0"
echo "Project Root: %PROJECT_ROOT%"

:: =================================
:: 1. Start Redis Server
:: =================================
ECHO "Starting Redis Server..."
cd /d "%PROJECT_ROOT%\redis"
start "Redis Server" redis-server.exe
ECHO "Waiting for Redis to initialize..."
timeout /t 5 > nul

:: =================================
:: 2. Start Backend Server (FastAPI)
:: =================================
ECHO "Starting Backend Server..."
cd /d "%PROJECT_ROOT%\backend"
start "Backend Server" cmd /k "poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
ECHO "Waiting for Backend to initialize..."
timeout /t 5 > nul

:: =================================
:: 3. Start Background Worker
:: =================================
ECHO "Starting Background Worker..."
set "PYTHONPATH=%PROJECT_ROOT%backend"
start "Background Worker" cmd /k "cd /d "%PROJECT_ROOT%\backend" && poetry run python "%PROJECT_ROOT%worker\main.py""


:: =================================
:: 4. Start Frontend Server (Vite)
:: =================================
ECHO "Starting Frontend Server..."
cd /d "%PROJECT_ROOT%\frontend-new"
start "Frontend Server" cmd /k "npm run dev"

:: =================================
:: 5. Open Application in Browser
:: =================================
ECHO.
ECHO "=============================================================================="
ECHO "✅ All services are starting up in separate windows."
ECHO "Giving the frontend a moment to build..."
timeout /t 10 > nul
ECHO "🚀 Opening the application in your default browser..."
start http://localhost:3000
ECHO "=============================================================================="
ECHO.
ECHO "You can now close this window."
ECHO.
exit 