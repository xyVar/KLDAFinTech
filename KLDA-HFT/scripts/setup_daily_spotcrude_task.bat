@echo off
REM One-time setup: registers a Windows Task Scheduler job for the daily
REM SpotCrude signal evaluation at 22:30 BROKER time (Mon-Fri).
REM
REM The task fires every 15 min; run_daily_spotcrude.bat passes
REM --at-broker 22:30, so the scan runs once, in the 22:30-22:45 broker-time
REM window, regardless of the PC's timezone or daylight-saving changes.
REM (Previously a fixed /st 21:30 PC time, which drifted by an hour with DST.)
REM
REM Run this script ONCE from an elevated (Administrator) prompt; re-running
REM it replaces the old task (/f). Change the time in run_daily_spotcrude.bat.

schtasks /create ^
  /tn "KLDA-DailySpotCrude" ^
  /tr "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\scripts\run_daily_spotcrude.bat" ^
  /sc weekly ^
  /d MON,TUE,WED,THU,FRI ^
  /st 00:00 ^
  /ri 15 ^
  /du 24:00 ^
  /f

if %errorlevel% == 0 (
    echo.
    echo Task "KLDA-DailySpotCrude" registered: Mon-Fri every 15 min, scans once at 22:30 broker time.
    echo Reports land in KLDA-HFT\reports\daily_YYYY-MM-DD_SpotCrude.txt
    echo Run now to test:   schtasks /run /tn "KLDA-DailySpotCrude"
    echo Remove with:       schtasks /delete /tn "KLDA-DailySpotCrude" /f
) else (
    echo.
    echo FAILED - run this script from an elevated prompt.
)
pause
