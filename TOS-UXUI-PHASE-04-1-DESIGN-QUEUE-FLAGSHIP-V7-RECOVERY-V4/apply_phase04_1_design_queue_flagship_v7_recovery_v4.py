from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
HERE = Path(__file__).resolve().parent
V3_NAME = "apply_phase04_1_design_queue_flagship_v7_recovery_v3.py"
V3_DIR = "TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-FLAGSHIP-V7-RECOVERY-V3"
TMP = HERE / ".v7_recovery_v4_runtime.py"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V7_RECOVERY_V4")


def fail(message: str):
    if TMP.exists():
        TMP.unlink()
    print("PASS/FAIL=FAIL")
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V7_RECOVERY_V4=NO")
    print(f"ERROR={message}")
    sys.exit(1)


def replace_exact(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        fail(f"{label}: expected {expected} matches, found {count}")
    return text.replace(old, new)


# V3 was already executed on this same target, so prefer its exact local patch path.
# Fallbacks cover execution from a checked-out patch repo without relying on cwd.
candidates = [
    ROOT / V3_DIR / V3_NAME,
    HERE.parent / V3_DIR / V3_NAME,
]
try:
    candidates.extend(ROOT.rglob(V3_NAME))
except OSError:
    pass

v3_path = next((path for path in candidates if path.exists() and path.is_file()), None)
if not v3_path:
    fail("verified V3 installer not found on target")

source = v3_path.read_text()

# Root cause of V3 failure:
# JSX source contains data-sidebar-premium="v7", but the compiled React bundle does
# not contain the literal HTML form data-sidebar-premium="v7". Verifying that exact
# source token inside dist is therefore invalid. V4 adds a unique attribute VALUE that
# survives bundling/minification and verifies that value in dist/live instead.
source = replace_exact(
    source,
    'SIDEBAR_MARKER = \'data-sidebar-premium="v7"\'\n',
    'SIDEBAR_MARKER = \'data-sidebar-premium="v7"\'\nSIDEBAR_BUILD_MARKER = "TOS_SIDEBAR_PREMIUM_V7_BUILD"\n',
    1,
    "build marker constant",
)

anchor = '''    sidebar = replace_count(\n        sidebar,\n        '<span className="truncate">{item.label}</span>',\n'''
injection = '''    sidebar = replace_once(\n        sidebar,\n        '      data-sidebar-premium="v7"\\n      data-collapsed=',\n        '      data-sidebar-premium="v7"\\n      data-sidebar-build="TOS_SIDEBAR_PREMIUM_V7_BUILD"\\n      data-collapsed=',\n        "sidebar compiled build marker",\n    )\n\n    sidebar = replace_count(\n        sidebar,\n        '<span className="truncate">{item.label}</span>',\n'''
source = replace_exact(source, anchor, injection, 1, "sidebar build marker injection")

source = replace_exact(
    source,
    '    dist_sidebar = tree_count(DIST, SIDEBAR_MARKER.encode())',
    '    dist_sidebar = tree_count(DIST, SIDEBAR_BUILD_MARKER.encode())',
    1,
    "dist sidebar verification",
)
source = replace_exact(
    source,
    '    live_sidebar = tree_count(LIVE, SIDEBAR_MARKER.encode())',
    '    live_sidebar = tree_count(LIVE, SIDEBAR_BUILD_MARKER.encode())',
    1,
    "live sidebar verification",
)
source = replace_exact(
    source,
    'print("DIST_SIDEBAR_MARKER_COUNT=" + str(tree_count(DIST, SIDEBAR_MARKER.encode())))',
    'print("DIST_SIDEBAR_MARKER_COUNT=" + str(tree_count(DIST, SIDEBAR_BUILD_MARKER.encode())))',
    1,
    "dist output marker",
)
source = replace_exact(
    source,
    'print("LIVE_SIDEBAR_MARKER_COUNT=" + str(tree_count(LIVE, SIDEBAR_MARKER.encode())))',
    'print("LIVE_SIDEBAR_MARKER_COUNT=" + str(tree_count(LIVE, SIDEBAR_BUILD_MARKER.encode())))',
    1,
    "live output marker",
)

# Make reporting unambiguous for this recovery version.
source = source.replace("PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V7_RECOVERY_V3", "PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V7_RECOVERY_V4")
source = source.replace("V7_RECOVERY_V3", "V7_RECOVERY_V4")

# Require the unique build marker in source before build as an additional safety guard.
source_guard = '''    if SIDEBAR.read_text().count(SIDEBAR_MARKER) != 1:\n        raise RuntimeError("source Sidebar marker count is not 1")\n'''
source_guard_v4 = source_guard + '''    if SIDEBAR.read_text().count(SIDEBAR_BUILD_MARKER) != 1:\n        raise RuntimeError("source Sidebar build marker count is not 1")\n'''
source = replace_exact(source, source_guard, source_guard_v4, 1, "source build marker guard")

TMP.write_text(source)
try:
    result = subprocess.run(
        [sys.executable, str(TMP), str(ROOT)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    code = result.returncode
finally:
    if TMP.exists():
        TMP.unlink()

if code != 0:
    sys.exit(code)
