# Meme Maker - Complete Startup Guide

This guide will walk you through starting the Meme Maker application on Windows. You'll be running multiple services: Docker containers, a Python backend, and a React frontend.

## Prerequisites

Before starting, ensure you have installed:
- **Docker Desktop** (with WSL2 enabled)
- **Node.js** (version 18 or higher)
- **Python** (version 3.12 or higher)
- **Git** (for cloning the repository)

## What You'll Be Running

The Meme Maker application consists of:
1. **Docker Services**: Redis (database), Backend API, Worker (video processing), Frontend
2. **Local Development**: Option to run backend and frontend locally for faster development

## Quick Start (Recommended for Beginners)

### Option 1: Full Docker Setup (Easiest)

1. **Open Docker Desktop**
   - Find Docker Desktop in your Start menu and click to open it
   - Wait for it to fully start (you'll see a green icon in the system tray)

2. **Open PowerShell as Administrator**
   - Press `Windows + X` keys together
   - Click "Windows PowerShell (Admin)" or "Terminal (Admin)"
   - If prompted by User Account Control, click "Yes"

3. **Navigate to Project Directory**
   ```powershell
   # Replace this path with where you downloaded/cloned the project
   cd "C:\Users\YourUsername\Desktop\Meme Maker - Local\Meme-Maker"
   ```

4. **Create Environment File**
   ```powershell
   # Copy the template to create your environment file
   Copy-Item env.template .env
   ```

5. **Start All Services with Docker**
   ```powershell
   # This command starts all services (Redis, Backend, Worker, Frontend)
   docker-compose -f docker-compose.dev.yaml up --build
   ```

6. **Access the Application**
   - Wait for all services to start (look for "Application startup complete" messages)
   - Open your web browser and go to: `http://localhost:3000`
   - The API will be available at: `http://localhost:8000`

7. **To Stop All Services**
   - Press `Ctrl + C` in the PowerShell window
   - Then run: `docker-compose -f docker-compose.dev.yaml down`

## Advanced Setup (For Development)

### Option 2: Mixed Setup (Docker + Local Development)

This option runs Redis and Worker in Docker, but Backend and Frontend locally for faster development and better debugging.

#### Terminal 1: Docker Services (Redis + Worker)

1. **Open PowerShell as Administrator**
   ```powershell
   # Navigate to project directory
   cd "C:\Users\YourUsername\Desktop\Meme Maker - Local\Meme-Maker"
   
   # Create environment file if not exists
   if (!(Test-Path .env)) {
       Copy-Item env.template .env
   }
   
   # Start only Redis and Worker services
   docker-compose -f docker-compose.dev.yaml up redis worker --build
   ```

#### Terminal 2: Backend API Server

1. **Open a NEW PowerShell Window**
   - Press `Windows + R`, type `powershell`, press Enter
   
2. **Setup Backend**
   ```powershell
   # Navigate to project directory
   cd "C:\Users\YourUsername\Desktop\Meme Maker - Local\Meme-Maker"
   
   # Navigate to backend folder
   cd backend
   
   # Install Python dependencies using Poetry (recommended)
   # If you have Poetry installed:
   poetry install
   poetry shell
   
   # OR install using pip:
   # pip install -r requirements.txt
   
   # Start the backend server
   # With Poetry:
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   
   # OR with pip:
   # uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Terminal 3: Frontend Development Server

1. **Open a THIRD PowerShell Window**
   
2. **Setup Frontend**
   ```powershell
   # Navigate to project directory
   cd "C:\Users\YourUsername\Desktop\Meme Maker - Local\Meme-Maker"
   
   # Navigate to frontend folder
   cd frontend-new
   
   # Install Node.js dependencies (only needed first time)
   npm install
   
   # Start the development server
   npm run dev
   ```

## Understanding the Terminals

### Terminal 1 (Docker Services)
- **What it does**: Runs Redis (database) and Worker (video processing)
- **You'll see**: Logs from Redis and Worker services
- **Keep it running**: Yes, other services depend on this

### Terminal 2 (Backend API)
- **What it does**: Runs the Python FastAPI server
- **You'll see**: API request logs and Python application logs
- **URL**: `http://localhost:8000`
- **Keep it running**: Yes, frontend needs this to work

### Terminal 3 (Frontend)
- **What it does**: Runs the React development server
- **You'll see**: Vite development server logs and build information
- **URL**: `http://localhost:3000`
- **Keep it running**: Yes, this is your main application interface

## Troubleshooting Common Issues

### "Docker is not running"
- Make sure Docker Desktop is open and running
- Look for the Docker whale icon in your system tray
- If it's red or orange, wait for it to turn green

### "Port already in use"
- Close any existing instances of the application
- Check if something else is using ports 3000, 6379, or 8000
- Kill processes using these ports:
  ```powershell
  # Find what's using port 8000
  netstat -ano | findstr :8000
  # Kill the process (replace PID with actual process ID)
  taskkill /PID [PID] /F
  ```

### "Module not found" or "Package not found"
- Make sure you've installed dependencies:
  ```powershell
  # For backend
  cd backend
  pip install -r requirements.txt
  
  # For frontend
  cd frontend-new
  npm install
  ```

### "Permission denied"
- Run PowerShell as Administrator
- Make sure Docker Desktop has proper permissions

### Frontend won't connect to backend
- Check that backend is running on port 8000
- Verify `.env` file exists and has correct settings
- Check firewall isn't blocking connections

## Environment Variables

The `.env` file contains important configuration. Key settings:

```env
# Debug mode for development
DEBUG=true

# Database connection
REDIS_URL=redis://localhost:6379

# Storage settings
STORAGE_BACKEND=local
CLIPS_DIR=/app/clips
BASE_URL=http://localhost:8000

# CORS settings for frontend
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

## Stopping the Application

### Full Docker Setup
```powershell
# In the terminal running docker-compose
Ctrl + C
docker-compose -f docker-compose.dev.yaml down
```

### Mixed Setup
1. **Stop Frontend**: Press `Ctrl + C` in Terminal 3
2. **Stop Backend**: Press `Ctrl + C` in Terminal 2  
3. **Stop Docker Services**: Press `Ctrl + C` in Terminal 1, then:
   ```powershell
   docker-compose -f docker-compose.dev.yaml down
   ```

## Useful Commands

### Check if services are running
```powershell
# Check Docker containers
docker ps

# Check if ports are in use
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :6379
```

### View logs
```powershell
# Docker service logs
docker-compose -f docker-compose.dev.yaml logs [service-name]

# Examples:
docker-compose -f docker-compose.dev.yaml logs backend
docker-compose -f docker-compose.dev.yaml logs frontend
docker-compose -f docker-compose.dev.yaml logs worker
```

### Reset everything
```powershell
# Stop all containers and remove volumes
docker-compose -f docker-compose.dev.yaml down -v

# Remove all unused Docker resources
docker system prune -a

# Reinstall frontend dependencies
cd frontend-new
Remove-Item -Recurse -Force node_modules
npm install
```

## Development Tips

1. **Use the Mixed Setup** for active development - it's faster to restart individual services
2. **Use Full Docker Setup** when you just want to run the app without modifications
3. **Keep all terminals open** while developing - you'll see logs from all services
4. **The frontend auto-reloads** when you make changes to React components
5. **The backend auto-reloads** when you make changes to Python files (with --reload flag)

## Next Steps

Once everything is running:
1. Open `http://localhost:3000` in your browser
2. Try uploading a video URL to create a clip
3. Check the browser developer tools (F12) if you encounter issues
4. Monitor the terminal logs for error messages

For more detailed development information, see the individual README files in the `backend/` and `frontend-new/` directories. 