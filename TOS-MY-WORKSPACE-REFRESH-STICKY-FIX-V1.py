#!/usr/bin/env python3
# TOS-MY-WORKSPACE-REFRESH-STICKY-FIX-V1
# Keep Kanban + sticky scrollbar mounted during manual Refresh.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
MARKER = "TOS_MY_WORKSPACE_REFRESH_STICKY_FIX_V1"

def die(message):
    print(f"PATCH=FAIL\nERROR={message}")
    sys.exit(1)

if not TARGET.exists():
    die(f"missing file: {TARGET}")

source = TARGET.read_text(encoding="utf-8")

if MARKER in source:
    print("PATCH=SKIP_ALREADY_APPLIED")
    sys.exit(0)

old = '''<button type="button" onClick={() => loadWorkspace()} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-xs font-black text-zinc-700 transition hover:bg-zinc-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100">'''
new = '''{/* TOS_MY_WORKSPACE_REFRESH_STICKY_FIX_V1 */}
          <button type="button" onClick={() => loadWorkspace({ showLoading: false })} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-xs font-black text-zinc-700 transition hover:bg-zinc-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100">'''

count = source.count(old)
if count != 1:
    die(f"refresh button anchor expected 1, found {count}")

backup = TARGET.with_name(TARGET.name + f".bak-refresh-sticky-fix-v1-{int(time.time())}")
shutil.copy2(TARGET, backup)

source = source.replace(old, new, 1)
TARGET.write_text(source, encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-MY-WORKSPACE-REFRESH-STICKY-FIX-V1")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("REFRESH_MODE=NON_BLOCKING")
print("KANBAN_MOUNT=PRESERVED")
print("STICKY_SCROLLBAR=PRESERVED")
print("INITIAL_LOADING=UNCHANGED")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
