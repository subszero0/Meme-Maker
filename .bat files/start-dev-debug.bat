@echo off
echo DEBUG: Starting batch file
echo.

echo DEBUG: Testing docker --version
docker --version
echo DEBUG: Exit code from docker --version: %errorlevel%

echo DEBUG: Testing docker --version with redirection
docker --version >nul 2>&1
echo DEBUG: Exit code from redirected docker --version: %errorlevel%

echo DEBUG: Testing docker ps
docker ps
echo DEBUG: Exit code from docker ps: %errorlevel%

echo DEBUG: Testing docker ps with redirection
docker ps >nul 2>&1
echo DEBUG: Exit code from redirected docker ps: %errorlevel%

echo.
echo DEBUG: Now testing the actual if statement logic...

docker --version >nul 2>&1
if errorlevel 1 (
    echo DEBUG: Docker version check FAILED
) else (
    echo DEBUG: Docker version check PASSED
)

docker ps >nul 2>&1
if errorlevel 1 (
    echo DEBUG: Docker ps check FAILED  
) else (
    echo DEBUG: Docker ps check PASSED
)

echo.
echo DEBUG: End of debug script
pause 