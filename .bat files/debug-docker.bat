@echo off
echo Testing Docker commands for debugging...
echo.

echo Testing docker --version:
docker --version
echo Exit code: %errorlevel%
echo.

echo Testing docker ps:
docker ps
echo Exit code: %errorlevel%
echo.

echo Testing docker info (first few lines):
docker info | findstr "Version"
echo Exit code: %errorlevel%
echo.

echo Testing docker info redirected:
docker info >nul 2>&1
echo Exit code after redirect: %errorlevel%
echo.

echo Testing docker ps redirected:
docker ps >nul 2>&1
echo Exit code after redirect: %errorlevel%
echo.

pause 