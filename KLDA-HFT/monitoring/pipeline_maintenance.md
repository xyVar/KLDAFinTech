# KLDA-HFT PIPELINE MAINTENANCE GUIDE

## Current Status (2026-01-21 14:40)

### ✅ What's Working
- **Data Flow**: SOLID - 16,768 NAS100 ticks in 5 minutes (200K/hour!)
- **Database**: PostgreSQL + TimescaleDB operational
- **Flask API**: Running on port 5000
- **MT5 Bridge**: Capturing ticks successfully
- **Schema**: 35 tables (1 current + 17 history + 17 bars)

### ⚠️ What Needs Maintenance
1. Compression DISABLED on all 17 history tables
2. Email alerts NOT configured
3. Windows Service NOT set up (manual start required)
4. Auto-reconnect NOT implemented

---

## Maintenance Tasks

### Task 1: Enable Compression (Storage Optimization)
**Status**: Script ready, needs execution
**Impact**: 10x storage reduction
**Action**:
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\database
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -f enable_compression.sql
```

### Task 2: Set Up Email Alerts
**Status**: Script ready, needs configuration
**Impact**: Get notified of data flow issues
**Action**:
1. Edit `monitoring\hourly_health_check.py`:
   - Update line 20: `'sender_email': 'YOUR_EMAIL@gmail.com'`
   - Update line 21: `'sender_password': 'YOUR_APP_PASSWORD'`
   - Update line 22: `'recipient_email': 'YOUR_EMAIL@gmail.com'`

2. Get Gmail App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Generate app password for "KLDA-HFT Monitoring"

3. Test:
```bash
python "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\monitoring\hourly_health_check.py"
```

4. Schedule hourly (Windows Task Scheduler):
```bash
schtasks /create /tn "KLDA-HFT-Monitor" /tr "python C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\monitoring\hourly_health_check.py" /sc hourly /st 00:00
```

### Task 3: Flask as Windows Service
**Status**: Needs NSSM installation
**Impact**: Auto-start on boot
**Action**:
1. Install NSSM:
```bash
winget install nssm
```

2. Create service:
```bash
nssm install KLDA-HFT-FlaskAPI "C:\Python313\python.exe" "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api\tick_receiver.py"
nssm set KLDA-HFT-FlaskAPI AppDirectory "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api"
nssm set KLDA-HFT-FlaskAPI Start SERVICE_AUTO_START
nssm start KLDA-HFT-FlaskAPI
```

### Task 4: Auto-Reconnect MT5 Bridge
**Status**: Code enhancement needed
**Impact**: Recover from broker disconnections
**Action**: Add to `mt5_tick_capture_ALL_TICKS.py` (see implementation below)

---

## Alert Thresholds

### Database Alerts
- **Min ticks/hour**: 100 (per symbol)
- **Max staleness**: 15 minutes (24/7 markets)
- **Min disk space**: 10% free

### Email Triggers
- No new ticks for 15+ minutes (VIX, NAS100, NatGas, SpotCrude)
- Database connection failed
- Flask API not responding (port 5000)
- Disk space < 10%

---

## Quick Health Check Commands

### Check Data Flow (Last 5 Minutes)
```bash
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -c "SELECT 'VIX' as symbol, COUNT(*) as ticks FROM vix_history WHERE time >= NOW() - INTERVAL '5 minutes' UNION SELECT 'NAS100', COUNT(*) FROM nas100_history WHERE time >= NOW() - INTERVAL '5 minutes';"
```

### Check Flask API Status
```bash
curl http://localhost:5000/health
curl http://localhost:5000/stats
```

### Check Database Size
```bash
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -c "SELECT pg_size_pretty(pg_database_size('KLDA-HFT_Database'));"
```

### Check Compression Status
```bash
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d KLDA-HFT_Database -c "SELECT hypertable_name, compression_enabled FROM timescaledb_information.hypertables WHERE hypertable_name LIKE '%history' LIMIT 5;"
```

---

## Expected Data Volumes

### Tick Ingestion Rates (Observed)
- **NAS100**: 200,000 ticks/hour (very high)
- **VIX**: 4,500 ticks/hour (moderate)
- **Stocks**: 0 ticks/hour (market closed)

### Storage Projections
| Period | Uncompressed | Compressed (10x) |
|--------|--------------|------------------|
| 1 Day  | 500 MB       | 50 MB            |
| 1 Week | 3.5 GB       | 350 MB           |
| 1 Month| 15 GB        | 1.5 GB           |
| 1 Year | 186 GB       | 18.6 GB          |

---

## Troubleshooting

### Issue: "No new ticks"
**Check**:
1. MT5 terminal is running
2. `mt5_tick_capture_ALL_TICKS.py` process is alive
3. Flask API `/health` endpoint responds

**Fix**:
```bash
# Restart MT5 bridge
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\python-bridge
python mt5_tick_capture_ALL_TICKS.py
```

### Issue: "Database connection failed"
**Check**:
1. PostgreSQL service running: `sc query postgresql-x64-16`
2. Port 5432 accessible: `netstat -ano | findstr :5432`

**Fix**:
```bash
net stop postgresql-x64-16
net start postgresql-x64-16
```

### Issue: "Flask API timeout"
**Check**:
1. Flask process running: `netstat -ano | findstr :5000`
2. Error logs in Flask output

**Fix**:
```bash
# Kill and restart Flask
taskkill /F /IM python.exe /FI "WINDOWTITLE eq C:\*tick_receiver.py*"
python "C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\api\tick_receiver.py"
```

---

## Next Steps (Recommended Priority)

1. **HIGH**: Enable compression (reduce storage by 10x)
2. **HIGH**: Set up email alerts (get notified of issues)
3. **MEDIUM**: Create Windows Service (auto-start)
4. **MEDIUM**: Add auto-reconnect logic (reliability)
5. **LOW**: Create continuous aggregates (faster charts)

---

**Last Updated**: 2026-01-21 14:40
**Data Flow**: SOLID (200K ticks/hour on NAS100)
**Next Review**: After enabling compression
