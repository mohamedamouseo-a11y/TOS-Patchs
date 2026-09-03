#!/usr/bin/env python3
from pathlib import Path

SERVICE = Path('/var/www/TOS/backend/src/agency-operator/services/ramzyTeamPerformance.service.js')
if not SERVICE.exists():
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_FIX_ERROR=SERVICE_NOT_FOUND')

text = SERVICE.read_text(encoding='utf-8')
old = '  for (const signal of row.signals || []) reasons.push(String(signal.message || "").trim()).filter(Boolean);\n'
new = '''  for (const signal of row.signals || []) {\n    const message = String(signal?.message || "").trim();\n    if (message) reasons.push(message);\n  }\n'''
if old not in text:
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_FIX_ERROR=WORKFORCE_SIGNAL_ANCHOR_NOT_FOUND')
text = text.replace(old, new, 1)
SERVICE.write_text(text, encoding='utf-8')
print('TEAM_PERFORMANCE_PHASE6_RAMZY_FIX=YES')
