@echo off
echo ========================================
echo MT5 WebRequest Fix
echo ========================================
echo.
echo This will:
echo 1. Close MetaTrader 5
echo 2. Add WebRequest URL to config
echo 3. Restart MetaTrader 5
echo.
pause

echo Closing MT5...
taskkill /F /IM terminal64.exe 2>nul
timeout /t 2 >nul

echo Adding WebRequest URL to config...
set CONFIG_FILE=C:\Users\PC\AppData\Roaming\MetaQuotes\Terminal\73B7A2420D6397DFF9014A20F1201F97\config\common.ini

echo [WebRequest] >> "%CONFIG_FILE%"
echo AllowWebRequest=true >> "%CONFIG_FILE%"
echo URL=http://localhost:5000 >> "%CONFIG_FILE%"

echo.
echo [OK] Config updated!
echo.
echo Now restart MT5 manually and load the EA again.
echo.
pause
