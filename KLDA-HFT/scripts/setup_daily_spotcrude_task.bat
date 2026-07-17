@echo off
REM One-time setup: registers a Windows Task Scheduler job that runs the
REM daily SpotCrude signal evaluation Mon-Fri at 21:30 local time
REM (= 22:30 broker server time UTC+3, ~1.5h before Friday close 23:55).
REM
REM Run this script ONCE from an elevated (Administrator) prompt.
REM Adjust /st below to change the run time.

schtasks /create ^
  /tn "KLDA-DailySpotCrude" ^
  /tr "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\scripts\run_daily_spotcrude.bat" ^
  /sc weekly ^
  /d MON,TUE,WED,THU,FRI ^
  /st 21:30 ^
  /f

if %errorlevel% == 0 (
    echo.
    echo Task "KLDA-DailySpotCrude" registered: Mon-Fri 21:30 local.
    echo Reports land in KLDA-HFT\reports\daily_YYYY-MM-DD_SpotCrude.txt
    echo Run now to test:   schtasks /run /tn "KLDA-DailySpotCrude"
    echo Remove with:       schtasks /delete /tn "KLDA-DailySpotCrude" /f
) else (
    echo.
    echo FAILED - run this script from an elevated prompt.
)
pause
