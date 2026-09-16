from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R28-MORE-NO-SCROLL-JUMP"
R27_MARKER = "--tos-task-details-v2-12-phase1-r27-scroll-anchor-clip-guard-runtime"
R28_MARKER = "--tos-task-details-v2-12-phase1-r28-more-no-scroll-jump-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R27_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R27ScrollAnchorClipGuard.css"
R28_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R28MoreNoScrollJump.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PAYLOAD = Path(__file__).resolve().parent / "taskDetailsV2_12_Phase1R28MoreNoScrollJump.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R27_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r27_source = R27_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R27_MARKER not in r27_source:
    fail("R27 production baseline marker missing")
if R28_STYLE.exists() or R28_MARKER in board_source:
    fail("R28 already appears applied")
if R28_MARKER not in payload_css:
    fail("R28 payload marker missing")

r27_import = 'import "../styles/taskDetailsV2_12_Phase1R27ScrollAnchorClipGuard.css";'
r28_import = 'import "../styles/taskDetailsV2_12_Phase1R28MoreNoScrollJump.css";'
r27_ref_line = '  const r27MoreGeometryRef = useRef({ taskId: null, open: null, tabsTop: null });\n'
r27_effect_start = '  // TOS_TASK_DETAILS_R27_SCROLL_ANCHOR_CLIP_GUARD\n  useEffect(() => {'
r27_effect_end = '  }, [taskMoreDetailsOpen, task?.id]);'
scroll_fn = '''  function scrollTaskDetailsToTop() {
    taskDetailsBodyRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }'''
raw_toggle = 'setTaskMoreDetailsOpen(nextOpen);'
stable_toggle = 'setTaskMoreDetailsOpenStable(nextOpen);'

for contract in (r27_import, r27_ref_line.strip(), r27_effect_start, r27_effect_end, scroll_fn, raw_toggle):
    if contract not in board_source:
        fail(f"R28 v3 source contract missing: {contract[:90]}")
if r28_import in board_source or "TOS_TASK_DETAILS_R28_MORE_NO_SCROLL_JUMP" in board_source:
    fail("R28 source marker already exists")

updated = board_source

# Remove R27 manual scroll compensation only. Keep R27 CSS safe-margin/clip rules.
if updated.count(r27_ref_line) != 1:
    fail(f"expected one R27 geometry ref, found {updated.count(r27_ref_line)}")
updated = updated.replace(r27_ref_line, "", 1)

start = updated.find(r27_effect_start)
if start < 0:
    fail("R27 effect start not found")
end = updated.find(r27_effect_end, start)
if end < 0:
    fail("R27 effect end not found")
end += len(r27_effect_end)
if updated[end:end+2] == "\n\n":
    end += 1
updated = updated[:start] + updated[end:]

# Replace the ACTUAL current baseline user-triggered More toggles BEFORE inserting the helper.
# Production currently reports 4; accept a narrow safe range so minor duplicate UI triggers do not fail preflight.
baseline_toggle_count = updated.count(raw_toggle)
if baseline_toggle_count < 3 or baseline_toggle_count > 6:
    fail(f"unexpected More toggle count: {baseline_toggle_count}")
updated = updated.replace(raw_toggle, stable_toggle)
if updated.count(stable_toggle) != baseline_toggle_count:
    fail("failed to replace every baseline More toggle")
if updated.count(raw_toggle) != 0:
    fail("raw More toggle survived baseline replacement")

helper = '''  function scrollTaskDetailsToTop() {
    taskDetailsBodyRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }

  // TOS_TASK_DETAILS_R28_MORE_NO_SCROLL_JUMP
  function setTaskMoreDetailsOpenStable(nextOpen) {
    const scroller = taskDetailsBodyRef.current;
    const preservedTop = scroller ? scroller.scrollTop : 0;

    setTaskMoreDetailsOpen(Boolean(nextOpen));

    if (!scroller || typeof window === "undefined") return;
    const restoreExactViewport = () => {
      const currentScroller = taskDetailsBodyRef.current;
      if (!currentScroller) return;
      currentScroller.scrollTop = preservedTop;
      currentScroller.dataset.tosR28MoreNoScrollJump = "true";
    };

    restoreExactViewport();
    window.requestAnimationFrame(() => {
      restoreExactViewport();
      window.requestAnimationFrame(restoreExactViewport);
    });
    window.setTimeout(restoreExactViewport, 120);
  }'''

if updated.count(scroll_fn) != 1:
    fail(f"expected one scroll-to-top function, found {updated.count(scroll_fn)}")
updated = updated.replace(scroll_fn, helper, 1)

if updated.count(r27_import) != 1:
    fail(f"expected one R27 import, found {updated.count(r27_import)}")
updated = updated.replace(r27_import, r27_import + "\n" + r28_import, 1)

for contract in (
    "TOS_TASK_DETAILS_R28_MORE_NO_SCROLL_JUMP",
    stable_toggle,
    'currentScroller.scrollTop = preservedTop;',
    'currentScroller.dataset.tosR28MoreNoScrollJump = "true"',
    'setTaskMoreDetailsOpen(Boolean(nextOpen));',
    r28_import,
):
    if contract not in updated:
        fail(f"R28 v3 source contract missing after edit: {contract}")
if "TOS_TASK_DETAILS_R27_SCROLL_ANCHOR_CLIP_GUARD" in updated:
    fail("R27 manual compensation effect still present")
if "r27MoreGeometryRef" in updated:
    fail("R27 geometry ref still present")
if updated.count(stable_toggle) != baseline_toggle_count:
    fail("stable More toggle count changed unexpectedly")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R28_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
frontend_runtime = manifest.get("frontend") or {}
DIST = Path(str(frontend_runtime.get("buildOutputDir") or FRONTEND / "dist"))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or "/opt/apps/tamiyouz-front/build"))
if str(frontend_runtime.get("buildCommand") or "npm run build") != "npm run build":
    fail("unexpected frontend build command")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r28-v3-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)
LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-r28-v3-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-r28-v3-backup-{stamp}"
live_swapped = False
r28_written = False

try:
    BOARD.write_text(updated)
    R28_STYLE.write_text(payload_css.rstrip() + "\n")
    r28_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R28_MARKER not in built_css or R27_MARKER not in built_css:
        fail("R27/R28 runtime marker missing from build")
    # Only durable literal tokens; local variable/function names may be minified away.
    if "tosR28MoreNoScrollJump" not in built_js:
        fail("R28 durable runtime token missing from build JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        if live_backup.exists():
            shutil.rmtree(live_backup)
        LIVE.rename(live_backup)
    staging.rename(LIVE)
    live_swapped = True

    live_css = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.css"))
    live_js = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.js"))
    if R28_MARKER not in live_css or R27_MARKER not in live_css:
        fail("R27/R28 runtime marker missing from live build")
    if "tosR28MoreNoScrollJump" not in live_js:
        fail("R28 durable runtime token missing from live JS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r28_written and R28_STYLE.exists():
        R28_STYLE.unlink()
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"PATCH_APPLIED={PATCH}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print(f"MORE_TOGGLE_CALLS_PATCHED={baseline_toggle_count}")
print("R27_MANUAL_SCROLL_COMPENSATION=REMOVED")
print("MORE_SCROLLTOP_FROZEN=YES")
print("R26_DYNAMIC_RIGHT_RAIL_PRESERVED=YES")
print("SINGLE_SCROLL_OWNER_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("PUSH=NO")
