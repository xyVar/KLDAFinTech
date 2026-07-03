@echo off
echo ============================================================
echo KLDA-HFT System Shutdown
echo ============================================================
echo.

echo Stopping all Python processes...
taskkill /F /IM python.exe >nul 2>&1

echo Stopping Docker containers...
docker stop klda-hft-cpp-backend >nul 2>&1

echo.
echo ============================================================
echo KLDA-HFT System Stopped
echo ============================================================
echo.
echo All services have been terminated.
echo.
pause
