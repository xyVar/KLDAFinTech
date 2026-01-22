#!/usr/bin/env python3
"""Update dashboard HTML with improved timestamp display"""

import re

# Read the original HTML file
with open('klda_asset_surveillance.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Read the new timestamp code
with open('timestamp_fix.js', 'r', encoding='utf-8') as f:
    new_code = f.read()

# Pattern to match the old timestamp code (lines 640-651)
old_pattern = r'''                // Get latest tick time
                const latestBar = bars\[bars\.length - 1\];
                if \(latestBar\) \{
                    const lastTime = new Date\(latestBar\.time\);
                    const secondsAgo = Math\.floor\(\(Date\.now\(\) - lastTime\.getTime\(\)\) / 1000\);
                    const timeAgo = secondsAgo < 60 \? `\$\{secondsAgo\}s ago` :
                                   secondsAgo < 3600 \? `\$\{Math\.floor\(secondsAgo/60\)\}m ago` :
                                   `\$\{Math\.floor\(secondsAgo/3600\)\}h ago`;
                    document\.getElementById\('stat-updated'\)\.textContent = timeAgo;
                \} else \{
                    document\.getElementById\('stat-updated'\)\.textContent = 'Unknown';
                \}'''

# Replace
new_content = re.sub(old_pattern, new_code.strip(), content)

# Write back
with open('klda_asset_surveillance.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("[OK] Dashboard updated successfully!")
print("   - Added absolute timestamp display")
print("   - Added color coding (green=live, yellow=delayed, red=stale)")
print("   - Added MARKET CLOSED warning for old data")
