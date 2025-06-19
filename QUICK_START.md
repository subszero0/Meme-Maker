# Quick Start Guide

## Easy One-Click Startup (Recommended)

**Prerequisites**: Docker Desktop must be running

### Windows Users
1. Double-click `start-dev.bat`
2. Wait for services to start
3. Application opens automatically at `http://localhost:3000`

### To Stop
- Double-click `stop-dev.bat`, OR
- Close the "Meme Maker Services" terminal window

## Alternative Startup Options

### Full Docker (All Platforms)
```bash
# Copy environment template
cp env.template .env

# Start all services
docker-compose -f docker-compose.dev.yaml up --build

# Access: http://localhost:3000
```

### Local Development (Faster rebuilds)
See detailed instructions in `StartUp.md`

## Quick Health Check

After starting, verify services:
```bash
# Check containers
docker ps

# Check endpoints
curl http://localhost:8000/health  # Backend
curl http://localhost:3000         # Frontend
```

## Troubleshooting

- **"Docker not running"**: Open Docker Desktop first
- **"Port in use"**: Run `stop-dev.bat` or stop conflicting services
- **Services won't start**: Check Docker Desktop has enough resources (4GB RAM recommended)

For detailed troubleshooting, see `StartUp.md` 