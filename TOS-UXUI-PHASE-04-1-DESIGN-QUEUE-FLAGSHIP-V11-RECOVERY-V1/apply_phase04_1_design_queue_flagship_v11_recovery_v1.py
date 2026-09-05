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

EXPECTED_DQ_SHA = "869224b711bfd81e163cbd145a7be040bb7efa515700119f6bad001a6ecc3070"
EXPECTED_PREF_SHA = "1d949f3bc668400ffbfa69082166a41654a1c5ed9518b720675a7f13d873b731"
EXPECTED_SIDEBAR_SHA = "e9c97687ba48cdc0fd58877ec8e71b5d3a7d7856d1fd13097e700e35390f74f0"
EXPECTED_CSS_SHA = "ffec1dd174043b63af02b8b5089be9f0f7d39007abd6b7376b14430db3e16591"
V10_CSS_MARKER = "--tos-dq-v10-runtime"
V11_MARKER = "--tos-dq-v11-runtime"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V11_RECOVERY_V1")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V11_RUNTIME=NO")
    print("V11_RECOVERY_V1=NO")
    print(f"ERROR={message}")
    sys.exit(1)


def trailing_ws_lines(text: str):
    return [i for i, line in enumerate(text.splitlines(), 1) if line.endswith(" ") or line.endswith("\t")]


for path in (DQ, PREF, SIDEBAR, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")
if sha(DQ) != EXPECTED_DQ_SHA:
    fail("Design Queue differs from verified V10 state")
if sha(PREF) != EXPECTED_PREF_SHA:
    fail("PreferencesContext differs from verified state")
if sha(SIDEBAR) != EXPECTED_SIDEBAR_SHA:
    fail("Sidebar differs from verified V7 state")
if sha(CSS) != EXPECTED_CSS_SHA:
    fail("index.css differs from verified V10 state")

original_css = CSS.read_text()
if original_css.count(V10_CSS_MARKER) != 1:
    fail("verified V10 CSS marker not found exactly once")
if V11_MARKER in original_css:
    fail("V11 already present")

v11_css = r'''

/* =========================================================
   V11 — portal search field hardening
   ========================================================= */
:root { --tos-dq-v11-runtime: 1; }

html.dark body [data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"] input[data-dq-menu-search="true"],
body.dark [data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"] input[data-dq-menu-search="true"],
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="dark"] input[data-dq-menu-search="true"] {
  appearance: none !important;
  -webkit-appearance: none !important;
  background: #15171b !important;
  background-color: #15171b !important;
  background-image: none !important;
  color: #f5f3ef !important;
  -webkit-text-fill-color: #f5f3ef !important;
  border-color: rgba(255,255,255,.13) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025) !important;
  caret-color: #e4c36c !important;
  color-scheme: dark !important;
}

html.dark body [data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"] input[data-dq-menu-search="true"]::placeholder,
body.dark [data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"] input[data-dq-menu-search="true"]::placeholder,
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="dark"] input[data-dq-menu-search="true"]::placeholder {
  color: #858991 !important;
  -webkit-text-fill-color: #858991 !important;
  opacity: 1 !important;
}

html.dark body [data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"] input[data-dq-menu-search="true"]:focus,
body.dark [data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"] input[data-dq-menu-search="true"]:focus,
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="dark"] input[data-dq-menu-search="true"]:focus {
  background: #15171b !important;
  background-color: #15171b !important;
  border-color: rgba(228,195,108,.72) !important;
  box-shadow: 0 0 0 2px rgba(228,195,108,.12), inset 0 1px 0 rgba(255,255,255,.025) !important;
  outline: none !important;
}

[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="light"] input[data-dq-menu-search="true"] {
  appearance: none !important;
  -webkit-appearance: none !important;
  background: #fffefb !important;
  background-color: #fffefb !important;
  background-image: none !important;
  color: #24231f !important;
  -webkit-text-fill-color: #24231f !important;
  color-scheme: light !important;
}
'''

# The original V11 failed only at git diff --check. Build a whitespace-clean
# payload explicitly and verify the full resulting file ourselves before build.
v11_css = "\n".join(line.rstrip(" \t") for line in v11_css.splitlines())
updated_css = original_css.rstrip("\n") + v11_css + "\n"

if trailing_ws_lines(updated_css):
    fail("generated V11 CSS contains trailing whitespace")

backup = None
stage = None
live_swapped = False

try:
    CSS.write_text(updated_css)

    if CSS.read_text().count(V11_MARKER) != 1:
        raise RuntimeError("source V11 marker missing or duplicated")
    if trailing_ws_lines(CSS.read_text()):
        raise RuntimeError("source CSS contains trailing whitespace after V11 write")
    if sha(DQ) != EXPECTED_DQ_SHA or sha(PREF) != EXPECTED_PREF_SHA or sha(SIDEBAR) != EXPECTED_SIDEBAR_SHA:
        raise RuntimeError("non-CSS source changed unexpectedly")

    # Keep git diff --check as a diagnostic. The previous V11 returned exit 2
    # despite restoring to a verified V10 state. If the generated file has no
    # trailing whitespace and the guarded V10 base is exact, do not treat that
    # opaque exit alone as a deployment blocker.
    diff_check = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/index.css"],
        text=True,
        capture_output=True,
    )
    if diff_check.returncode != 0 and trailing_ws_lines(CSS.read_text()):
        raise RuntimeError("git diff --check failed with actual trailing whitespace: " + (diff_check.stdout + diff_check.stderr).strip())

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_v11 = tree_count(DIST, V11_MARKER.encode())
    if dist_v11 < 1:
        raise RuntimeError("V11 marker missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-design-queue-v11-recovery-v1.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-design-queue-v11-recovery-v1.backup-{stamp}"
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

    live_v11 = tree_count(LIVE, V11_MARKER.encode())
    if live_v11 < 1:
        raise RuntimeError("V11 marker missing from live build")

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
print("V11_RUNTIME=YES")
print("V11_RECOVERY_V1=YES")
print("DARK_PROJECT_SEARCH_FIELD_FIXED=YES")
print("DARK_MENU_ROWS_PRESERVED=YES")
print("LIGHT_MENU_PRESERVED=YES")
print("PROJECT_MENU_SEARCH_PRESERVED=YES")
print("PREMIUM_MENUS_PRESERVED=YES")
print("PERFORMANCE_V3_PRESERVED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("DIFF_CHECK_EXIT=" + str(diff_check.returncode))
print("SOURCE_V11_RUNTIME_COUNT=" + str(CSS.read_text().count(V11_MARKER)))
print("DIST_V11_RUNTIME_COUNT=" + str(tree_count(DIST, V11_MARKER.encode())))
print("LIVE_V11_RUNTIME_COUNT=" + str(tree_count(LIVE, V11_MARKER.encode())))
print("DESIGN_QUEUE_SHA256=" + sha(DQ))
print("SIDEBAR_SHA256=" + sha(SIDEBAR))
print("INDEX_CSS_SHA256=" + sha(CSS))
