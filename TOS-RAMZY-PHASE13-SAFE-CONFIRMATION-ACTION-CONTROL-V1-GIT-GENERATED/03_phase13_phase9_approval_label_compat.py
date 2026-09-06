#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
PATH = ROOT / 'backend/src/agency-operator/tests/ramzyFinalPolishE2E.static.test.js'

text = PATH.read_text(encoding='utf-8')
old = '  assert.match(assistant, /Approve/);'
new = '  assert.match(assistant, /Approve|Confirm & execute/);'

if new in text:
    print('PHASE13_PHASE9_APPROVAL_LABEL_COMPAT=ALREADY_APPLIED')
    raise SystemExit(0)

count = text.count(old)
if count != 1:
    raise SystemExit(f'PHASE13_COMPAT_ERROR=PHASE9_APPROVE_ASSERT_COUNT_{count}')

PATH.write_text(text.replace(old, new, 1), encoding='utf-8')
print('PHASE13_PHASE9_APPROVAL_LABEL_COMPAT=PASS')
