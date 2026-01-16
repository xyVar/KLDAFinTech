@echo off
title KLDA-HFT Quick Price Check
color 0A

echo ========================================
echo    KLDA-HFT PRICE CHECK
echo ========================================
echo.

"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -c "SELECT symbol, bid, ask, spread, last_updated, NOW() - last_updated AS seconds_ago FROM current ORDER BY symbol;"

echo.
echo ========================================
echo Press any key to exit
pause >nul
