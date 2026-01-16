# How to Visually See Your C++ HFT Backend Running

## Option 1: Docker Desktop GUI (Recommended)

### Opening Docker Desktop:

**Method 1 - Start Menu:**
1. Click Windows Start button
2. Search for "Docker Desktop"
3. Click the Docker Desktop app

**Method 2 - System Tray:**
1. Look at bottom-right of your screen (system tray)
2. Find the Docker whale icon 🐋
3. Right-click on it
4. Select "Open Dashboard"

**Method 3 - Direct Path:**
- Run: `C:\Program Files\Docker\Docker\Docker Desktop.exe`

### What You'll See in Docker Desktop:

Once open, navigate to:
1. **Containers** tab (left sidebar)
2. Look for: **`klda-hft-cpp-backend`**
3. You'll see:
   - ✅ Status: Running (green indicator)
   - 🔄 Restarting status (if continuously testing)
   - Port: 8081:8081
   - Image: cpp-backend-cpp-backend

### Container Actions in Docker Desktop:

- **📊 View Logs**: Click container → "Logs" tab → See live C++ output
- **⏸️ Stop**: Click "Stop" button
- **▶️ Start**: Click "Start" button
- **🔄 Restart**: Click "Restart" button
- **📈 Stats**: See CPU, Memory, Network usage in real-time
- **🖥️ Terminal**: Click "Exec" tab to open shell inside container

---

## Option 2: Command Line - Live Logs (Fastest)

**Double-click this file:**
```
C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend\watch_cpp_backend.bat
```

This will show:
```
======================================
KLDA-HFT C++ Backend Engine
======================================

[1] Loading configuration...
[OK] Configuration loaded
[OK] Connection string built

[2] Connecting to PostgreSQL...
[OK] Connected to PostgreSQL database

[3] Querying CURRENT table...
[OK] Found 17 assets

Symbol     | Bid       | Ask       | Last Updated
-------------------------------------------------------------
AAPL       | 258.08    | 258.11    | 2026-01-14 19:39:09
AMD        | 223.67    | 223.80    | 2026-01-14 19:39:09
NVDA       | 181.95    | 181.96    | 2026-01-14 19:39:09
TSLA       | 437.56    | 437.75    | 2026-01-14 19:39:06
...

[SUCCESS] Database connection test passed!
```

**Press Ctrl+C to stop watching**

---

## Option 3: Command Line - Container Status

Open PowerShell or CMD and run:

```bash
# See all running containers
docker ps

# See just KLDA-HFT container
docker ps --filter "name=klda-hft-cpp-backend"

# See detailed stats (CPU, Memory, Network)
docker stats klda-hft-cpp-backend
```

---

## Option 4: Command Line - One-Time Log Check

```bash
# See last 50 lines of logs
docker logs --tail 50 klda-hft-cpp-backend

# See logs from last 5 minutes
docker logs --since 5m klda-hft-cpp-backend

# Follow logs in real-time
docker logs -f klda-hft-cpp-backend
```

---

## Visual Layout - Where Everything Is

```
┌─────────────────────────────────────────────────────────────┐
│                      YOUR DESKTOP                           │
│                                                             │
│  [Docker Desktop Icon] ← Click this to open Docker GUI     │
│                                                             │
│  Desktop/KLDAFinTech/KLDA-HFT/cpp-backend/                 │
│     ├── watch_cpp_backend.bat ← Double-click for live logs │
│     ├── docker-compose.yml                                  │
│     └── src/main.cpp                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            DOCKER DESKTOP GUI (When Opened)                 │
│  ┌───────────┬────────────────────────────────────────────┐ │
│  │ Containers│  klda-hft-cpp-backend     [Running 🟢]    │ │
│  │ Images    │  Port: 0.0.0.0:8081 → 8081               │ │
│  │ Volumes   │  ┌─────────────────────────────────────┐  │ │
│  │ Networks  │  │ LOGS TAB (Click here)               │  │ │
│  └───────────┤  │                                     │  │ │
│              │  │ ==============================      │  │ │
│              │  │ KLDA-HFT C++ Backend Engine        │  │ │
│              │  │ ==============================      │  │ │
│              │  │ [OK] Connected to PostgreSQL       │  │ │
│              │  │ [OK] Found 17 assets               │  │ │
│              │  │ AAPL | 258.08 | 258.11            │  │ │
│              │  │ NVDA | 181.95 | 181.96            │  │ │
│              │  │ ...                                │  │ │
│              │  └─────────────────────────────────────┘  │ │
│              └──────────────────────────────────────────── │
└─────────────────────────────────────────────────────────────┘
```

---

## System Tray (Bottom-Right Corner)

Look for the Docker whale icon:
```
┌──────────────────────────────────────┐
│  [🔔] [🔊] [🌐] [🔋] [🐋]  [⏰]     │  ← Your taskbar
└──────────────────────────────────────┘
                    ↑
              Docker icon
         (Right-click → Dashboard)
```

---

## Current Architecture - What You're Seeing

```
┌──────────────────────────────────────────────────────────────┐
│                    WINDOWS HOST (Your PC)                    │
│                                                              │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │ PostgreSQL  │   │ Python Bridge│   │ Flask API       │  │
│  │ Port: 5432  │◄──│ Task b796f34 │──►│ Task bd8a243    │  │
│  │ LIVE DATA   │   │ (MT5 Capture)│   │ (Tick Storage)  │  │
│  └──────┬──────┘   └──────────────┘   └─────────────────┘  │
│         │                                                    │
│         │ host.docker.internal                              │
│         │                                                    │
│  ┌──────▼──────────────────────────────────────────────┐   │
│  │  DOCKER CONTAINER (klda-hft-cpp-backend)            │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │  C++ HFT Engine (Ubuntu 22.04)               │   │   │
│  │  │  ✅ Connected to Windows PostgreSQL          │   │   │
│  │  │  📊 Reading CURRENT table (17 assets)        │   │   │
│  │  │  📈 Real-time price data                     │   │   │
│  │  │  🔁 Test running continuously                │   │   │
│  │  │  Port: 8081 (for future REST API)           │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  YOU CAN SEE THIS CONTAINER IN:                             │
│  - Docker Desktop GUI → Containers tab                      │
│  - watch_cpp_backend.bat (live logs)                        │
│  - docker ps (command line)                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Commands

**Start the C++ backend:**
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend
docker-compose up -d
```

**Stop the C++ backend:**
```bash
cd C:\Users\PC\Desktop\KLDAFinTech\KLDA-HFT\cpp-backend
docker-compose down
```

**Watch live logs:**
```bash
docker logs -f klda-hft-cpp-backend
```

**Check if container is running:**
```bash
docker ps | findstr klda-hft
```

---

## Troubleshooting

**Docker Desktop not opening?**
- The backend may still be running even if GUI doesn't show
- Check with: `docker ps`
- Use command line as alternative

**Container restarting constantly?**
- This is normal for the test program
- It completes the test, exits, then Docker restarts it
- Future version will run continuously as a service

**Can't see logs?**
- Run: `docker logs klda-hft-cpp-backend`
- Or use the watch_cpp_backend.bat script

---

## What You Should See (Success Indicators)

✅ Container status: "Running" or "Restarting"
✅ Logs show: "[OK] Connected to PostgreSQL database"
✅ Logs show: "[OK] Found 17 assets"
✅ Price data appearing: AAPL, AMD, NVDA, TSLA, etc.
✅ Last updated timestamps are recent (within seconds)

---

**Created:** 2026-01-14
**Project:** KLDA-HFT C++ Backend
**Container:** klda-hft-cpp-backend
