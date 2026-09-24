#!/usr/bin/env python3
# TOS-MY-WORKSPACE-EXECUTIVE-LUXURY-V1-ROLLBACK
# Restore the exact MyTaskWorkspace.jsx snapshot created immediately before Executive Luxury V1.
# Preserves all earlier patches present in that snapshot.

from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
EXEC_MARKER = "TOS_MY_WORKSPACE_EXECUTIVE_LUXURY_V1"

def die(message):
    print(f"ROLLBACK=FAIL\nERROR={message}")
    sys.exit(1)

if not TARGET.exists():
    die(f"missing target: {TARGET}")

current = TARGET.read_text(encoding="utf-8")

if EXEC_MARKER not in current:
    print("ROLLBACK=SKIP_EXECUTIVE_LUXURY_NOT_ACTIVE")
    sys.exit(0)

backups = sorted(
    TARGET.parent.glob(TARGET.name + ".bak-executive-luxury-v1-*"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

if not backups:
    die("pre-Executive-Luxury backup not found")

backup = backups[0]
backup_text = backup.read_text(encoding="utf-8")

if EXEC_MARKER in backup_text:
    die(f"backup unexpectedly contains Executive Luxury marker: {backup.name}")

required_preserved = [
    "TOS_MY_WORKSPACE_SPACIOUS_PREMIUM_V1",
    "TOS_MY_WORKSPACE_KPI_LIVE_MOTION_V1",
    "TOS_MY_WORKSPACE_PREMIUM_FILTERS_V1",
    "TOS_MY_WORKSPACE_TRELLO_DRAG_DROP_V1",
    "TOS_MY_WORKSPACE_STICKY_SCROLLBAR_V1_1",
]

missing = [marker for marker in required_preserved if marker not in backup_text]
if missing:
    die("backup missing expected pre-luxury markers: " + ",".join(missing))

shutil.copy2(backup, TARGET)

restored = TARGET.read_text(encoding="utf-8")
if EXEC_MARKER in restored:
    die("Executive Luxury marker still present after restore")

print("ROLLBACK=PASS")
print("ROLLBACK_NAME=TOS-MY-WORKSPACE-EXECUTIVE-LUXURY-V1-ROLLBACK")
print(f"RESTORED_FROM={backup.name}")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("EXECUTIVE_LUXURY_REMOVED=YES")
print("KPI_LIVE_MOTION=PRESERVED")
print("PREMIUM_FILTERS=PRESERVED")
print("DRAG_DROP=PRESERVED")
print("STICKY_SCROLLBAR=PRESERVED")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
