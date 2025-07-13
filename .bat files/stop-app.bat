@echo off
title Meme Maker - Shutdown
echo.
echo ========================================
echo    MEME MAKER - SHUTDOWN
echo ========================================
echo.

echo 🛑 Stopping all services...
docker-compose -f docker-compose.dev.yaml down

echo.
echo 🧹 Cleaning up...
docker system prune -f --volumes

echo.
echo ========================================
echo    ✅ SHUTDOWN COMPLETE!
echo ========================================
echo.
echo All services have been stopped and cleaned up.
echo.
pause 