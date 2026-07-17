@echo off
echo ============================================================
echo KLDA-HFT System Shutdown (surgical — KLDA processes only)
echo ============================================================
echo.

REM Kill ONLY python processes whose command line matches a KLDA script,
REM same WMI approach as python-bridge/watchdog.py. NEVER use a blanket
REM "taskkill /F /IM python.exe" — it kills MCP servers, running backtests,
REM and any other Python on the machine.

echo [1/3] Stopping watchdog first (so it cannot respawn the bridge)...
powershell -NoProfile -Command ^
  "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*watchdog.py*' } | ForEach-Object { Write-Host ('  killing PID ' + $_.ProcessId + ' (watchdog.py)'); Stop-Process -Id $_.ProcessId -Force }"

echo [2/3] Stopping KLDA bridge, signal generator, router, reconciler, engine, APIs...
powershell -NoProfile -Command ^
  "$scripts = @('mt5_tick_capture_ALL_TICKS.py','mt5_tick_capture.py','signal_generator.py','order_router.py','reconciler.py','klda_engine.py','trading_api.py','tick_receiver.py','positions_api.py','tick_api.py'); Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ForEach-Object { $p = $_; foreach ($s in $scripts) { if ($p.CommandLine -like ('*' + $s + '*')) { Write-Host ('  killing PID ' + $p.ProcessId + ' (' + $s + ')'); Stop-Process -Id $p.ProcessId -Force; break } } }"

echo [3/3] Stopping Docker container...
docker stop klda-hft-cpp-backend >nul 2>&1

echo.
echo ============================================================
echo KLDA-HFT System Stopped
echo ============================================================
echo Only KLDA-matched processes were terminated.
echo.
pause
