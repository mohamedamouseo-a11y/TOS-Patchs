#!/usr/bin/env python3
from pathlib import Path

CONTROL = Path('/var/www/TOS/frontend/src/components/performance/PerformancePeriodControl.jsx')
if not CONTROL.exists():
    raise SystemExit('PHASE2 CONTROL HARDENING ERROR: control file missing')

text = CONTROL.read_text(encoding='utf-8')
text = text.replace(
    'setCustomStart(nextStart ?? customStart || fallbackStart);',
    'setCustomStart(nextStart ?? (customStart || fallbackStart));',
)
text = text.replace(
    'setCustomEnd(nextEnd ?? customEnd || fallbackEnd);',
    'setCustomEnd(nextEnd ?? (customEnd || fallbackEnd));',
)

required = [
    'const currentStartValue = preset === "custom" ? customStart : toInputDate(selectedRange?.start);',
    'const currentEndValue = preset === "custom" ? customEnd : toInputDate(selectedRange?.end);',
    'aria-pressed={active}',
    'Current:',
    'Compare:',
]
for marker in required:
    if marker not in text:
        raise SystemExit(f'PHASE2 CONTROL HARDENING ERROR: missing marker {marker}')

CONTROL.write_text(text, encoding='utf-8')
print('PHASE2_PERIOD_CONTROL_HARDENED=YES')
