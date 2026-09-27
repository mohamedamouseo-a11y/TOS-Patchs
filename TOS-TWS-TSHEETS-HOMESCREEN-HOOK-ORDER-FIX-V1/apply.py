#!/usr/bin/env python3
from pathlib import Path

PATCH = "TOS-TWS-TSHEETS-HOMESCREEN-HOOK-ORDER-FIX-V1"
ROOT = Path.cwd()
TARGET = ROOT / "vendor" / "tsheets-casual-upstream" / "apps" / "web" / "src" / "home" / "HomeScreen.tsx"
MARKER = "TOS_TSHEETS_HOMESCREEN_HOOK_ORDER_FIX_V1"

def fail(msg):
    raise SystemExit("ERROR: " + msg)

if not TARGET.exists():
    fail(f"missing target: {TARGET}")

src = TARGET.read_text(encoding="utf-8")

if MARKER in src:
    print(f"PATCH={PATCH}")
    print("APPLY=ALREADY_PRESENT")
    print("FILE=vendor/tsheets-casual-upstream/apps/web/src/home/HomeScreen.tsx")
    raise SystemExit(0)

early = "  if (!visible) return null;\n"
memo = """  const mergedRecents = useMemo(() => {
    const local = recents.filter((r) => !r.id.startsWith('tos:'));
    return [...tosRecents, ...local].sort((a, b) => b.modifiedAt - a.modifiedAt);
  }, [tosRecents, recents]);
"""

if src.count(early) != 1:
    fail(f"expected early return once, found {src.count(early)}")
if src.count(memo) != 1:
    fail(f"expected mergedRecents memo once, found {src.count(memo)}")

early_pos = src.index(early)
memo_pos = src.index(memo)
if memo_pos < early_pos:
    fail("mergedRecents useMemo is already before the conditional return")

src = src.replace(memo, "", 1)
replacement = f"""  // {MARKER}
  // Keep every hook above the visibility early return so render paths
  // always execute hooks in the same order.
{memo}
{early}"""
src = src.replace(early, replacement, 1)

TARGET.write_text(src, encoding="utf-8")
verify = TARGET.read_text(encoding="utf-8")

marker_pos = verify.index(MARKER)
memo_pos = verify.index("const mergedRecents = useMemo")
return_pos = verify.index("if (!visible) return null")

if not (marker_pos < memo_pos < return_pos):
    fail("hook order verification failed")
if verify.count("const mergedRecents = useMemo") != 1:
    fail("mergedRecents memo count changed unexpectedly")

print(f"PATCH={PATCH}")
print("APPLY=PASS")
print("FILE=vendor/tsheets-casual-upstream/apps/web/src/home/HomeScreen.tsx")
print("HOOK_ORDER=FIXED")
print("MERGED_RECENTS_BEFORE_EARLY_RETURN=YES")
print("OTHER_HOOKS_TOUCHED=NO")
print("AUTOSAVE_TOUCHED=NO")
print("RECENTS_LOGIC_TOUCHED=NO")
print("DRIVE_SYNC_TOUCHED=NO")
print("BACK_HOME_TOUCHED=NO")
print("FRAME_FIT_TOUCHED=NO")
