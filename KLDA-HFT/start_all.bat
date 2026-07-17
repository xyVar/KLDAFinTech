@echo off
echo ============================================================
echo KLDA-HFT System Startup — Renaissance Trading Engine
echo ============================================================
echo.

echo [1/6] Checking PostgreSQL...
sc query postgresql-x64-16 | find "RUNNING" >nul
if %errorlevel% == 0 (
    echo   PostgreSQL is running
) else (
    echo   Starting PostgreSQL...
    net start postgresql-x64-16
    timeout /t 5 /nobreak >nul
)

echo.
echo [2/6] Starting MT5 Tick Bridge (all symbols)...
start "KLDA MT5 Bridge" /MIN cmd /c "cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge && python mt5_tick_capture_ALL_TICKS.py"
timeout /t 6 /nobreak >nul

echo [3/6] Starting C++ Reasoning Engine (Docker)...
powershell -Command "wsl bash -c 'docker start klda-hft-cpp-backend 2>/dev/null || docker run -d --name klda-hft-cpp-backend klda-hft-engine:latest'" >nul 2>&1
timeout /t 4 /nobreak >nul

echo [4/6] Starting Trading API (port 5002)...
start "KLDA Trading API" /MIN cmd /c "cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api && python trading_api.py"
timeout /t 4 /nobreak >nul

echo [5/6] Starting Signal Generator + Order Router + Reconciler (paper chain)...
start "KLDA SignalGen" /MIN cmd /c "cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\trading-engine && python signal_generator.py"
start "KLDA Router" /MIN cmd /c "cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\trading-engine && python order_router.py"
start "KLDA Reconciler" /MIN cmd /c "cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\trading-engine && python reconciler.py"
timeout /t 3 /nobreak >nul

echo [6/6] Opening Trading Terminal...
start "" "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api\trading_terminal.html"

echo.
echo ============================================================
echo KLDA-HFT Renaissance System Running
echo ============================================================
echo.
echo   MT5 Bridge:       Capturing ticks (all 64 symbols)
echo   C++ Engine:       Reasoning / pattern detection
echo   Trading API:      http://localhost:5002
echo   Trading Engine:   Watching signals, auto-executing
echo   Terminal:         trading_terminal.html (browser)
echo.
echo API Endpoints:
echo   /api/account       - Balance, equity, P&L
echo   /api/positions     - Open positions
echo   /api/trades        - Trade history
echo   /api/daily_pnl     - Daily performance
echo   /api/transactions  - Deposits/withdrawals
echo   /api/signals       - Signal log
echo   /api/symbols       - Live prices (all 64)
echo   /api/ticks/SYMBOL  - Raw tick stream
echo.
pause
