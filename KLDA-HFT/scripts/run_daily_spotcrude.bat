@echo off
REM Daily SpotCrude signal evaluation + end-of-day report.
REM Invoked by the "KLDA-DailySpotCrude" scheduled task (see
REM setup_daily_spotcrude_task.bat). Safe to run manually.

cd /d C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\trading-engine
python signal_generator.py --daily --symbol SpotCrude >> ..\reports\daily_task.log 2>&1
