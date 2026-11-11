@echo off
REM Daily SpotCrude signal evaluation + end-of-day report.
REM Invoked every 15 min by the "KLDA-DailySpotCrude" scheduled task (see
REM setup_daily_spotcrude_task.bat); --at-broker makes it run only once, at
REM 22:30 BROKER time, whatever the PC's timezone/DST. Safe to run manually
REM (without --at-broker it runs immediately).

if not exist C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\reports mkdir C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\reports
cd /d C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\trading-engine
python signal_generator.py --daily --symbol SpotCrude --at-broker 22:30 >> ..\reports\daily_task.log 2>&1
