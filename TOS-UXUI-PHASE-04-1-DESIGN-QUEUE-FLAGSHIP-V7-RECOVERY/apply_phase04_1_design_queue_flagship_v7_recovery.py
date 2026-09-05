from pathlib import Path
import hashlib
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_REPO = Path(__file__).resolve().parent.parent
V7_SCRIPT = PATCH_REPO / "TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-FLAGSHIP-V7" / "apply_phase04_1_design_queue_flagship_v7.py"
TMP_SCRIPT = Path(__file__).resolve().parent / ".v7_recovery_runtime.py"

DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
PREF = ROOT / "frontend/src/contexts/PreferencesContext.jsx"
SIDEBAR = ROOT / "frontend/src/components/layout/Sidebar.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE = Path("/opt/apps/tamiyouz-front/build")

EXPECTED_DQ_SHA = "f71c66b26a5cd7bb06ca849ce82afef897ed58d288c9fcfa198168a1d2d0eb59"
EXPECTED_PREF_SHA = "1d949f3bc668400ffbfa69082166a41654a1c5ed9518b720675a7f13d873b731"
EXPECTED_CSS_SHA = "2fa061485f20af185aeae3df1fe99033cbf12d2babe31f87c0f2e776e31fcb13"
EXPECTED_SIDEBAR_SHA = "8e62b2753e1c44e5bd580a4c301a0b41443508ab732cd8a579ab80368433c5e8"
V7_RUNTIME = b"--tos-dq-v7-runtime"
SIDEBAR_MARKER = b'data-sidebar-premium="v7"'

print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V7_RECOVERY")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str):
    if TMP_SCRIPT.exists():
        TMP_SCRIPT.unlink()
    print("PASS/FAIL=FAIL")
    print(f"ERROR={message}")
    sys.exit(1)


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.read_bytes().count(needle)
        except OSError:
            pass
    return total


required = [DQ, PREF, SIDEBAR, CSS, V7_SCRIPT]
if not all(path.exists() for path in required):
    fail("required source or V7 patch file missing")

# Exact verified clean pre-V7 state from the user's verify-only report.
pre_hashes = {
    "dq": sha(DQ),
    "pref": sha(PREF),
    "css": sha(CSS),
    "sidebar": sha(SIDEBAR),
}
if pre_hashes["dq"] != EXPECTED_DQ_SHA:
    fail("Design Queue is not the verified Performance V3 state")
if pre_hashes["pref"] != EXPECTED_PREF_SHA:
    fail("PreferencesContext is not the verified Performance V1 state")
if pre_hashes["css"] != EXPECTED_CSS_SHA:
    fail("index.css is not the verified V6 state")
if pre_hashes["sidebar"] != EXPECTED_SIDEBAR_SHA:
    fail("Sidebar differs from the verified clean pre-V7 state")
if CSS.read_bytes().count(V7_RUNTIME) != 0:
    fail("V7 CSS marker already present before recovery")
if SIDEBAR.read_bytes().count(SIDEBAR_MARKER) != 0:
    fail("V7 sidebar marker already present before recovery")

# Reuse the already-reviewed V7 transformation, but sanitize generated text BEFORE
# its built-in git diff --check. The original attempt reached diff-check with trailing
# whitespace, raised, then restored source; this recovery fixes that exact failure mode.
source = V7_SCRIPT.read_text()
old_css_write = "    CSS.write_text(updated_css)"
new_css_write = (
    "    updated_css = \\\"\\n\\\".join(line.rstrip() for line in updated_css.splitlines()) + \\\"\\n\\\"\n"
    "    CSS.write_text(updated_css)"
)
old_sidebar_write = "    SIDEBAR.write_text(sidebar)"
new_sidebar_write = (
    "    sidebar = \\\"\\n\\\".join(line.rstrip() for line in sidebar.splitlines()) + \\\"\\n\\\"\n"
    "    SIDEBAR.write_text(sidebar)"
)

if source.count(old_css_write) != 1:
    fail("could not patch V7 CSS write step exactly once")
if source.count(old_sidebar_write) != 1:
    fail("could not patch V7 Sidebar write step exactly once")

source = source.replace(old_css_write, new_css_write, 1)
source = source.replace(old_sidebar_write, new_sidebar_write, 1)
TMP_SCRIPT.write_text(source)

try:
    result = subprocess.run(
        [sys.executable, str(TMP_SCRIPT), str(ROOT)],
        cwd=PATCH_REPO,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    if result.returncode != 0:
        fail(f"repaired V7 installer exited {result.returncode}")
finally:
    if TMP_SCRIPT.exists():
        TMP_SCRIPT.unlink()

# Strong post-apply verification: source, built dist, and live must all carry V7.
source_runtime_count = CSS.read_bytes().count(V7_RUNTIME)
source_sidebar_count = SIDEBAR.read_bytes().count(SIDEBAR_MARKER)
dist_runtime_count = tree_count(DIST, V7_RUNTIME)
dist_sidebar_count = tree_count(DIST, SIDEBAR_MARKER)
live_runtime_count = tree_count(LIVE, V7_RUNTIME)
live_sidebar_count = tree_count(LIVE, SIDEBAR_MARKER)

if source_runtime_count != 1:
    fail(f"source V7 runtime count is {source_runtime_count}, expected 1")
if source_sidebar_count != 1:
    fail(f"source sidebar marker count is {source_sidebar_count}, expected 1")
if dist_runtime_count < 1 or live_runtime_count < 1:
    fail("V7 CSS runtime marker missing from dist or live build")
if dist_sidebar_count < 1 or live_sidebar_count < 1:
    fail("V7 sidebar marker missing from dist or live build")
if sha(DQ) != EXPECTED_DQ_SHA or sha(PREF) != EXPECTED_PREF_SHA:
    fail("Performance V3 / Preferences state changed unexpectedly")

subprocess.run(
    ["git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/index.css", "frontend/src/components/layout/Sidebar.jsx"],
    check=True,
)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("V7_RECOVERY=YES")
print(f"SOURCE_V7_RUNTIME_COUNT={source_runtime_count}")
print(f"SOURCE_SIDEBAR_MARKER_COUNT={source_sidebar_count}")
print(f"DIST_V7_RUNTIME_COUNT={dist_runtime_count}")
print(f"DIST_SIDEBAR_MARKER_COUNT={dist_sidebar_count}")
print(f"LIVE_V7_RUNTIME_COUNT={live_runtime_count}")
print(f"LIVE_SIDEBAR_MARKER_COUNT={live_sidebar_count}")
print("PERFORMANCE_V3_PRESERVED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("DESIGN_QUEUE_SHA256=" + sha(DQ))
print("PREFERENCES_CONTEXT_SHA256=" + sha(PREF))
print("SIDEBAR_SHA256=" + sha(SIDEBAR))
print("INDEX_CSS_SHA256=" + sha(CSS))
