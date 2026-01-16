@echo off
title KLDA-HFT C++ Backend - Live Monitor
color 0A
echo ========================================
echo    KLDA-HFT C++ Backend Live Monitor
echo ========================================
echo.
echo Container: klda-hft-cpp-backend
echo Status: RUNNING
echo Port: 8081
echo Database: Windows PostgreSQL via host.docker.internal
echo.
echo Press Ctrl+C to stop monitoring
echo ========================================
echo.

REM Follow logs in real-time
docker logs -f klda-hft-cpp-backend
