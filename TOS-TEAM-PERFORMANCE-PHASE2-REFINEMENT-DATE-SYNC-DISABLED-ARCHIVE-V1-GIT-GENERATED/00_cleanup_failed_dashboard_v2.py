#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path('/var/www/TOS')
EXPECTED_HEAD = '495201cfa490f643d9e28252eb523a4e278f385c'
MAIN = Path('frontend/src/main.jsx')
STYLE_DIR = ROOT / 'frontend/src/styles'
STYLE_FILE = STYLE_DIR / 'dashboard-github-reference.css'


def run(*args):
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


def fail(msg):
    print(f'PHASE2_REFINEMENT_CLEANUP_ERROR={msg}')
    raise SystemExit(1)


head = run('git', 'rev-parse', 'HEAD')
if head != EXPECTED_HEAD:
    fail(f'UNEXPECTED_HEAD:{head}')

status_lines = [line for line in run('git', 'status', '--short').splitlines() if line.strip()]
if not status_lines:
    print('FAILED_DASHBOARD_V2_RESIDUE=NOT_PRESENT')
    print('CLEANUP_RESULT=CLEAN')
    raise SystemExit(0)

allowed_status = {
    ' M frontend/src/main.jsx',
    '?? frontend/src/styles/',
}
if set(status_lines) != allowed_status:
    print('ACTUAL_STATUS_BEGIN')
    print('\n'.join(status_lines))
    print('ACTUAL_STATUS_END')
    fail('UNEXPECTED_WORKING_TREE')

# Validate main.jsx contains ONLY the failed Dashboard V2 stylesheet import.
diff = run('git', 'diff', '--', str(MAIN))
added = []
deleted = []
for line in diff.splitlines():
    if line.startswith('+++') or line.startswith('---'):
        continue
    if line.startswith('+'):
        added.append(line[1:].strip())
    elif line.startswith('-'):
        deleted.append(line[1:].strip())

expected_import = re.compile(r'''^import\s+["']\./styles/dashboard-github-reference\.css["'];?$''')
if deleted or len(added) != 1 or not expected_import.match(added[0]):
    print('MAIN_DIFF_BEGIN')
    print(diff)
    print('MAIN_DIFF_END')
    fail('MAIN_JSX_DIFF_NOT_EXACT_FAILED_PATCH_IMPORT')

# Validate the untracked styles directory contains only the known failed-patch file.
files = sorted(path for path in STYLE_DIR.rglob('*') if path.is_file()) if STYLE_DIR.exists() else []
if files != [STYLE_FILE]:
    print('STYLE_FILES_BEGIN')
    for path in files:
        print(path.relative_to(ROOT))
    print('STYLE_FILES_END')
    fail('UNTRACKED_STYLES_NOT_EXACT_FAILED_PATCH_FILE')

subprocess.check_call(['git', 'restore', '--source=HEAD', '--', str(MAIN)], cwd=ROOT)
STYLE_FILE.unlink()
try:
    STYLE_DIR.rmdir()
except OSError:
    pass

remaining = [line for line in run('git', 'status', '--short').splitlines() if line.strip()]
if remaining:
    print('REMAINING_STATUS_BEGIN')
    print('\n'.join(remaining))
    print('REMAINING_STATUS_END')
    fail('CLEANUP_DID_NOT_RESTORE_CLEAN_TREE')

print('FAILED_DASHBOARD_V2_RESIDUE=CONFIRMED_EXACT')
print('FAILED_DASHBOARD_V2_RESIDUE_REMOVED=YES')
print('CLEANUP_RESULT=CLEAN')
