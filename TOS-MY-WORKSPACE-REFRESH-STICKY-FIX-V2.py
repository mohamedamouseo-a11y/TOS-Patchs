#!/usr/bin/env python3
# TOS-MY-WORKSPACE-REFRESH-STICKY-FIX-V2
# Restore normal Refresh behavior while keeping Kanban mounted during refresh
# so the sticky horizontal scrollbar does not disappear.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
MARKER = "TOS_MY_WORKSPACE_REFRESH_STICKY_FIX_V2"
REQ_V1 = "TOS_MY_WORKSPACE_REFRESH_STICKY_FIX_V1"
REQ_STICKY = "TOS_MY_WORKSPACE_STICKY_SCROLLBAR_V1_1"

def die(message):
    print(f"PATCH=FAIL\nERROR={message}")
    sys.exit(1)

if not TARGET.exists():
    die(f"missing file: {TARGET}")

source = TARGET.read_text(encoding="utf-8")

if MARKER in source:
    print("PATCH=SKIP_ALREADY_APPLIED")
    sys.exit(0)

for required in (REQ_V1, REQ_STICKY):
    if required not in source:
        die(f"required marker missing: {required}")

old_button = '''{/* TOS_MY_WORKSPACE_REFRESH_STICKY_FIX_V1 */}
          <button type="button" onClick={() => loadWorkspace({ showLoading: false })} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-xs font-black text-zinc-700 transition hover:bg-zinc-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100">'''

new_button = '''{/* TOS_MY_WORKSPACE_REFRESH_STICKY_FIX_V1 */}
          {/* TOS_MY_WORKSPACE_REFRESH_STICKY_FIX_V2 */}
          <button type="button" onClick={() => loadWorkspace()} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-xs font-black text-zinc-700 transition hover:bg-zinc-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100">'''

button_count = source.count(old_button)
if button_count != 1:
    die(f"refresh button anchor expected 1, found {button_count}")

old_board_gate = '''      {!loading && tasks.length > 0 && ('''
new_board_gate = '''      {tasks.length > 0 && ('''

gate_count = source.count(old_board_gate)
if gate_count != 1:
    die(f"board loading gate expected 1, found {gate_count}")

backup = TARGET.with_name(TARGET.name + f".bak-refresh-sticky-fix-v2-{int(time.time())}")
shutil.copy2(TARGET, backup)

source = source.replace(old_button, new_button, 1)
source = source.replace(old_board_gate, new_board_gate, 1)
TARGET.write_text(source, encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-MY-WORKSPACE-REFRESH-STICKY-FIX-V2")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("REFRESH_BEHAVIOR=RESTORED")
print("REFRESH_LOADING_STATE=RESTORED")
print("KANBAN_STAYS_MOUNTED_WHEN_TASKS_EXIST=YES")
print("STICKY_SCROLLBAR_STAYS_MOUNTED=YES")
print("INITIAL_EMPTY_LOADING=UNCHANGED")
print("FILTERS_UNCHANGED=YES")
print("DRAG_DROP_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
