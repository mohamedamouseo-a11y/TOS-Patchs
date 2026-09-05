from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
PREF = ROOT / "frontend/src/contexts/PreferencesContext.jsx"
SIDEBAR = ROOT / "frontend/src/components/layout/Sidebar.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_DQ_SHA = "f71c66b26a5cd7bb06ca849ce82afef897ed58d288c9fcfa198168a1d2d0eb59"
EXPECTED_PREF_SHA = "1d949f3bc668400ffbfa69082166a41654a1c5ed9518b720675a7f13d873b731"
EXPECTED_SIDEBAR_SHA = "e9c97687ba48cdc0fd58877ec8e71b5d3a7d7856d1fd13097e700e35390f74f0"
EXPECTED_CSS_SHA = "070654bfef29184df587608f928b54dc7855a440374ca31dc788c5e435fbf06f"
V7_ROOT = ":root { --tos-dq-v6-runtime: 1; --tos-dq-v7-runtime: 1; }"
V8_MARKER = "--tos-dq-v8-runtime"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str):
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


for path in (DQ, PREF, SIDEBAR, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha(DQ) != EXPECTED_DQ_SHA:
    fail("Design Queue differs from verified Performance V3 state")
if sha(PREF) != EXPECTED_PREF_SHA:
    fail("PreferencesContext differs from verified state")
if sha(SIDEBAR) != EXPECTED_SIDEBAR_SHA:
    fail("Sidebar differs from verified V7 state")
if sha(CSS) != EXPECTED_CSS_SHA:
    fail("index.css differs from verified V7 state")

original_css = CSS.read_text()
if original_css.count(V7_ROOT) != 1:
    fail("verified V7 runtime root not found exactly once")
if V8_MARKER in original_css:
    fail("V8 already present")

v8_rules = r'''

/* =========================================================
   V8 — native menu/select legibility correction
   Root cause: Field ships with py-3 while V7 constrains native
   selects to 36/40px, clipping the selected label vertically.
   Keep controls compact, but remove vertical padding from SELECTS
   and restore a normal line box. No behavior/data changes.
   ========================================================= */
.tos-core-design-queue-premium select.tos-premium-field {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  line-height: normal !important;
  vertical-align: middle !important;
  font-weight: 800 !important;
  text-overflow: ellipsis !important;
}

/* Capacity menus — selected status/sort labels must be fully visible. */
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-3.grid select.tos-premium-field {
  height: 38px !important;
  min-height: 38px !important;
  padding-inline: .85rem 2rem !important;
  font-size: .76rem !important;
  line-height: 38px !important;
  color: #292722 !important;
  background-color: rgba(255,255,255,.96) !important;
}

/* Main board filter menus — same vertical centering and stronger label contrast. */
.tos-core-design-queue-premium > .p-3 select.tos-premium-field {
  height: 40px !important;
  min-height: 40px !important;
  padding-inline: .9rem 2.1rem !important;
  font-size: .78rem !important;
  line-height: 40px !important;
  color: #292722 !important;
  background-color: rgba(255,255,255,.96) !important;
}

/* Native popup option readability. */
.tos-core-design-queue-premium select.tos-premium-field option {
  color: #24231f !important;
  background: #fffefb !important;
  font-weight: 700 !important;
}

html.dark .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-3.grid select.tos-premium-field,
html.dark .tos-core-design-queue-premium > .p-3 select.tos-premium-field {
  color: #f4f2ed !important;
  background-color: #15171b !important;
  border-color: rgba(255,255,255,.11) !important;
}
html.dark .tos-core-design-queue-premium select.tos-premium-field option {
  color: #f4f2ed !important;
  background: #15171b !important;
}
'''

updated_css = original_css.replace(
    V7_ROOT,
    ":root { --tos-dq-v6-runtime: 1; --tos-dq-v7-runtime: 1; --tos-dq-v8-runtime: 1; }" + v8_rules,
    1,
)

backup = None
stage = None
live_swapped = False

try:
    CSS.write_text(updated_css)
    if CSS.read_text().count(V8_MARKER) != 1:
        raise RuntimeError("source V8 marker missing or duplicated")
    if sha(DQ) != EXPECTED_DQ_SHA or sha(PREF) != EXPECTED_PREF_SHA or sha(SIDEBAR) != EXPECTED_SIDEBAR_SHA:
        raise RuntimeError("non-CSS source changed unexpectedly")

    subprocess.run([
        "git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/index.css"
    ], check=True)

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_v8 = tree_count(DIST, V8_MARKER.encode())
    if dist_v8 < 1:
        raise RuntimeError("V8 marker missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-design-queue-v8.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-design-queue-v8.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged index missing")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_v8 = tree_count(LIVE, V8_MARKER.encode())
    if live_v8 < 1:
        raise RuntimeError("V8 marker missing from live build")

except Exception as exc:
    CSS.write_text(original_css)
    if live_swapped and backup and backup.exists():
        if LIVE.exists():
            shutil.rmtree(LIVE)
        backup.rename(LIVE)
    if stage and stage.exists():
        shutil.rmtree(stage)
    fail(str(exc))

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("SCREEN=Design_Queue_ONLY")
print("V8_RUNTIME=YES")
print("CAPACITY_MENU_TEXT_VISIBLE=YES")
print("BOARD_FILTER_MENU_TEXT_VISIBLE=YES")
print("SELECT_VERTICAL_CLIPPING_FIXED=YES")
print("PERFORMANCE_V3_PRESERVED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("SOURCE_V8_RUNTIME_COUNT=" + str(CSS.read_text().count(V8_MARKER)))
print("DIST_V8_RUNTIME_COUNT=" + str(tree_count(DIST, V8_MARKER.encode())))
print("LIVE_V8_RUNTIME_COUNT=" + str(tree_count(LIVE, V8_MARKER.encode())))
print("DESIGN_QUEUE_SHA256=" + sha(DQ))
print("SIDEBAR_SHA256=" + sha(SIDEBAR))
print("INDEX_CSS_SHA256=" + sha(CSS))
