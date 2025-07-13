@echo off
echo Testing minimal Docker check...

echo Testing docker --version check:
docker --version >nul 2>&1
if errorlevel 1 (
    echo FAILED: Docker version check
    pause
    exit /b 1
) else (
    echo PASSED: Docker version check
)

echo Testing docker ps check:
docker ps >nul 2>&1
if errorlevel 1 (
    echo FAILED: Docker ps check
    pause
    exit /b 1
) else (
    echo PASSED: Docker ps check
)

echo All checks passed!
pause 