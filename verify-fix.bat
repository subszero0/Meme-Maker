@echo off
echo ===============================================
echo    API FIX VERIFICATION SCRIPT
echo ===============================================
echo.

echo 🔍 Checking backend health...
curl -s http://localhost:8000/health
echo.
echo.

echo 🔍 Testing metadata endpoint...
echo Request: POST http://localhost:8000/api/v1/metadata
echo.
timeout /t 2 /nobreak >nul

echo ===============================================
echo    VERIFICATION STEPS FOR USER:
echo ===============================================
echo.
echo 1. ✅ Backend is running (if you see {"status":"ok"} above)
echo 2. 🌐 Frontend is running at: http://localhost:3000/
echo 3. 🔄 HARD REFRESH your browser (Ctrl+Shift+R)
echo 4. 📝 Open Developer Console (F12)
echo 5. 🎯 Input a YouTube URL and click "Let's Go!"
echo 6. 👀 Watch console - should show /api/v1/metadata (NOT /api/metadata)
echo.
echo If you still see /api/metadata errors, the browser cache needs clearing.
echo.
echo ===============================================

pause 