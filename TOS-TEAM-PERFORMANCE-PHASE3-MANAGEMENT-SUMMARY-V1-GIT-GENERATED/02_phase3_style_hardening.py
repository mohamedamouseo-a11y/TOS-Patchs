#!/usr/bin/env python3
from pathlib import Path

path = Path('/var/www/TOS/frontend/src/components/performance/ManagementSummary.jsx')
if not path.exists():
    raise SystemExit('PHASE3 STYLE HARDENING ERROR: ManagementSummary.jsx missing')

text = path.read_text(encoding='utf-8')
text = text.replace('dark:border-white/8', 'dark:border-white/10')
path.write_text(text, encoding='utf-8')

if 'dark:border-white/8' in text:
    raise SystemExit('PHASE3 STYLE HARDENING ERROR: unsupported border opacity remains')

print('PHASE3_STYLE_HARDENING=PASS')
