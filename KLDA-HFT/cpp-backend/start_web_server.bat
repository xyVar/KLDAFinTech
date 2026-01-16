@echo off
title KLDA-HFT Web Server
color 0B

echo ========================================
echo    KLDA-HFT Live Ticker Web Server
echo ========================================
echo.
echo Starting web server on http://localhost:8082
echo.
echo Open browser to: http://localhost:8082/live_ticker.html
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

cd /d "%~dp0"
python -m http.server 8082
