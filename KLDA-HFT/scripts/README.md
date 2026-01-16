# Utility Scripts - Testing & Verification

**Role:** Tools for testing and verifying the system
**Status:** ✅ AVAILABLE

---

## Files

### check_current_table.py
**Purpose:** Verify CURRENT table updates
**Usage:**
```bash
cd KLDA-HFT/scripts
python check_current_table.py
```

**Output:**
```
[CURRENT TABLE] - Latest tick for each asset:
  TSLA   | Bid:   448.67 | Ask:   449.00 | Buy:      0 | Sell:      0
  NVDA   | Bid:   184.43 | Ask:   184.46 | Buy:      0 | Sell:      0
  ...
```

**What it checks:**
- Latest tick for all 17 assets
- Bid/ask prices
- Buy/sell volume separation
- Last update timestamp

---

### check_database_ticks.py
**Purpose:** Comprehensive database verification
**Usage:**
```bash
cd KLDA-HFT/scripts
python check_database_ticks.py
```

**Output:**
```
============================================================
DATABASE TICK VERIFICATION
============================================================

[CURRENT TABLE] - Latest tick for each asset:
  TSLA   | Bid:   448.67 | Ask:   449.00 | Buy:      0 | Sell:      0

[HISTORY TABLES] - Tick counts (last 5 minutes):
  TSLA   |  464 ticks | 2026-01-13 17:31:03 -> 2026-01-13 17:54:43
  NVDA   |  464 ticks | 2026-01-13 17:31:00 -> 2026-01-13 17:54:43
  ...

[TOTAL TICKS] - All time:
  TSLA   | 466 ticks
  NVDA   | 465 ticks
  ...
```

**What it checks:**
- CURRENT table (latest ticks)
- HISTORY tables (tick counts and date ranges)
- Total ticks per asset (all time)

---

### test_manual_tick.py
**Purpose:** Send test tick to API server
**Usage:**
```bash
cd KLDA-HFT/scripts
python test_manual_tick.py
```

**What it does:**
1. Sends a manual test tick to API (POST /tick/batch)
2. Waits 2 seconds
3. Verifies tick was stored in database:
   - Checks CURRENT table
   - Checks HISTORY table (last 3 ticks)

**Output:**
```
Sending manual test tick...
Timestamp: 2026-01-13 18:00:00.123456
Response: 200
Body: {"status":"success","received":1}

[CURRENT] TSLA: Bid=449.99, Ask=450.01, BuyVol=0, Updated=2026-01-13 18:00:00

[HISTORY] TSLA last 3 ticks:
  2026-01-13 18:00:00.123456 | Bid=449.99 | Ask=450.01 | BuyVol=0
  2026-01-13 17:54:43.205000 | Bid=448.67 | Ask=449.00 | BuyVol=0
  2026-01-13 17:54:42.123000 | Bid=448.65 | Ask=448.98 | BuyVol=0
```

**Use cases:**
- Test API connectivity
- Verify database writes
- Debug tick storage issues

---

## Requirements

All scripts require:
```bash
pip install psycopg2
pip install requests  # Only for test_manual_tick.py
```

---

## Database Connection

All scripts use the same connection:
```python
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='KLDA-HFT_Database',
    user='postgres',
    password='MyKldaTechnologies2025!'
)
```

---

## Common Issues

### Error: "connection refused"
**Cause:** PostgreSQL not running
**Solution:**
```bash
# Windows
net start postgresql-x64-16

# Or check service:
sc query postgresql-x64-16
```

### Error: "password authentication failed"
**Cause:** Wrong database credentials
**Solution:**
- Check password in script matches PostgreSQL password
- Verify user `postgres` exists

### Error: "database does not exist"
**Cause:** Database not created yet
**Solution:**
```bash
cd KLDA-HFT/database
python setup_database.py
```

---

## Usage Examples

### Quick Health Check
```bash
# Check if data is flowing
python check_database_ticks.py

# Expected: Tick counts increasing over time
```

### Verify API Working
```bash
# Send test tick
python test_manual_tick.py

# Should see: Response 200, tick in database
```

### Monitor Live Updates
```bash
# Run repeatedly
watch -n 5 python check_current_table.py

# See prices update in real-time
```

---

**Last Updated:** 2026-01-13
