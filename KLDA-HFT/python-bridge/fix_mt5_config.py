#!/usr/bin/env python3
"""
Fix MT5 WebRequest Configuration
Edits the common.ini file to add http://localhost:5000 to allowed URLs
"""

import os
import shutil

CONFIG_FILE = r"C:\Users\PC\AppData\Roaming\MetaQuotes\Terminal\73B7A2420D6397DFF9014A20F1201F97\config\common.ini"
BACKUP_FILE = CONFIG_FILE + ".backup"

print("=" * 60)
print("MT5 WebRequest Configuration Fix")
print("=" * 60)

# Check if file exists
if not os.path.exists(CONFIG_FILE):
    print(f"[ERROR] Config file not found: {CONFIG_FILE}")
    exit(1)

# Create backup
print(f"[1] Creating backup: {BACKUP_FILE}")
shutil.copy2(CONFIG_FILE, BACKUP_FILE)
print("[OK] Backup created")

# Read the file with proper encoding (UTF-16 LE)
print("[2] Reading config file...")
with open(CONFIG_FILE, 'r', encoding='utf-16-le') as f:
    content = f.read()

# Check current WebRequest URL
if 'WebRequestUrl=' in content:
    # Find and update the line
    lines = content.split('\n')
    updated = False

    for i, line in enumerate(lines):
        if 'WebRequestUrl=' in line:
            old_line = line
            # Replace the line with the new URL
            lines[i] = 'WebRequestUrl=http://localhost:5000'
            updated = True
            print(f"[3] Found WebRequestUrl line:")
            print(f"    OLD: {old_line.strip()}")
            print(f"    NEW: {lines[i]}")
            break

    if updated:
        # Write back to file
        print("[4] Writing updated config...")
        with open(CONFIG_FILE, 'w', encoding='utf-16-le') as f:
            f.write('\n'.join(lines))

        print("[OK] Config file updated successfully!")
        print("")
        print("=" * 60)
        print("NEXT STEPS:")
        print("1. CLOSE MetaTrader 5 completely")
        print("2. RESTART MetaTrader 5")
        print("3. Load the KLDA_TickCapture_EA on any chart")
        print("4. EA will now connect successfully!")
        print("=" * 60)
    else:
        print("[ERROR] Could not find WebRequestUrl line to update")
else:
    print("[ERROR] WebRequestUrl not found in config")

print("\nIf MT5 is running, close it now before restarting.")
