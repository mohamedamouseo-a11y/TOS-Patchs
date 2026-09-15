from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R23_LATE_LAYOUT_SCROLL_LOCK"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R23-LATE-LAYOUT-SCROLL-LOCK"
R19_MARKER = "--tos-task-details-v2-12-phase1-r19-reset-actual-scroll-owners-runtime"
R20_MARKER = "--tos-task-details-v2-12-phase1-r20-keyed-scroll-container-remount-runtime"
R22_MARKER = "--tos-task-details-v2-12-phase1-r22-focus-trap-no-scroll-runtime"
R23_MARKER = "--tos-task-details-v2-12-phase1-r23-late-layout-scroll-lock-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R19_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R19ResetActualScrollOwners.css"
R20_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R20KeyedScrollContainerRemount.css"
R22_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R22FocusTrapNoScroll.css"
R23_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R23LateLayoutScrollLock.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R23LateLayoutScrollLock.css"

def fail(message):
    raise RuntimeError(message)

def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R19_STYLE, R20_STYLE, R22_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r19_source = R19_STYLE.read_text()
r20_source = R20_STYLE.read_text()
r22_source = R22_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R19_MARKER not in r19_source:
    fail("required R19 marker missing")
if R20_MARKER not in r20_source:
    fail("required R20 marker missing")
if R22_MARKER not in r22_source:
    fail("required R22 marker missing")
if R23_STYLE.exists() or R23_MARKER in board_source:
    fail("Phase 1 R23 already appears to be applied")
if R23_MARKER not in payload_css:
    fail("R23 payload runtime marker missing")

old_body = '<div key={String(task?.id || "task-details")} ref={taskDetailsBodyRef} onScroll={handleTaskDetailsScroll} className="min-h-0 flex-1 overflow-y-auto p-3 dark:from-zinc-950 dark:via-zinc-950 dark:to-blue-950/20 sm:p-4">'
new_body = '<div key={String(task?.id || "task-details")} data-tos-task-scroll-owner="r23" ref={taskDetailsBodyRef} onScroll={handleTaskDetailsScroll} className="min-h-0 flex-1 overflow-y-auto p-3 dark:from-zinc-950 dark:via-zinc-950 dark:to-blue-950/20 sm:p-4">'
if board_source.count(old_body) != 1:
    fail(f"expected exactly one R20 keyed Task Details scroll container, found {board_source.count(old_body)}")
updated_board = board_source.replace(old_body, new_body, 1)

old_effect = '''  useEffect(() => {
    let frameOne = null;
    let frameTwo = null;
    let timeoutId = null;

    const resetNodeScroll = (node) => {
      if (!node) return;
      try {
        node.scrollTop = 0;
        node.scrollLeft = 0;
      } catch {
        // Non-scrollable nodes are harmless; continue to the real owner.
      }
    };

    const resetTaskDetailsScrollOwners = () => {
      if (typeof document === "undefined" || typeof window === "undefined") return;

      const scroller = taskDetailsBodyRef.current;
      resetNodeScroll(scroller);
      if (scroller) scroller.dataset.tosTaskDetailsScrollReset = "r19";

      const visited = new Set();
      let ancestor = scroller?.parentElement || null;
      while (ancestor && ancestor !== document.body && !visited.has(ancestor)) {
        visited.add(ancestor);
        const styles = window.getComputedStyle(ancestor);
        const overflowY = styles.overflowY;
        const canScroll = ancestor.scrollHeight > ancestor.clientHeight || overflowY === "auto" || overflowY === "scroll";
        if (canScroll) resetNodeScroll(ancestor);
        ancestor = ancestor.parentElement;
      }

      resetNodeScroll(modalRef.current);
      resetNodeScroll(document.querySelector(".tos-task-details-fullpage"));
      resetNodeScroll(document.querySelector(".tos-task-details-reference-v1"));
      resetNodeScroll(document.querySelector(".tos-premium-page-viewport"));
      resetNodeScroll(document.scrollingElement);

      try {
        window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      } catch {
        window.scrollTo(0, 0);
      }
    };

    resetTaskDetailsScrollOwners();
    frameOne = window.requestAnimationFrame(() => {
      resetTaskDetailsScrollOwners();
      frameTwo = window.requestAnimationFrame(resetTaskDetailsScrollOwners);
    });
    timeoutId = window.setTimeout(resetTaskDetailsScrollOwners, 120);

    return () => {
      if (frameOne !== null) window.cancelAnimationFrame(frameOne);
      if (frameTwo !== null) window.cancelAnimationFrame(frameTwo);
      if (timeoutId !== null) window.clearTimeout(timeoutId);
    };
  }, [task?.id]);'''

new_effect = '''  useEffect(() => {
    if (typeof document === "undefined" || typeof window === "undefined") return undefined;

    let scrollLockActive = true;
    const frameIds = [];
    const timeoutIds = [];
    let resizeObserver = null;

    const resetNodeScroll = (node) => {
      if (!node) return;
      try {
        node.scrollTop = 0;
        node.scrollLeft = 0;
        if (typeof node.scrollTo === "function") node.scrollTo({ top: 0, left: 0, behavior: "auto" });
      } catch {
        // Ignore non-scrollable surfaces and continue.
      }
    };

    const resetTaskDetailsScrollOwners = () => {
      if (!scrollLockActive) return;

      const scroller = taskDetailsBodyRef.current;
      resetNodeScroll(scroller);
      if (scroller) {
        scroller.dataset.tosTaskDetailsScrollReset = "r23";
        scroller.style.overflowAnchor = "none";
      }

      const visited = new Set();
      let ancestor = scroller?.parentElement || null;
      while (ancestor && ancestor !== document.body && !visited.has(ancestor)) {
        visited.add(ancestor);
        const styles = window.getComputedStyle(ancestor);
        const overflowY = styles.overflowY;
        const canScroll = ancestor.scrollHeight > ancestor.clientHeight || overflowY === "auto" || overflowY === "scroll";
        if (canScroll) resetNodeScroll(ancestor);
        ancestor = ancestor.parentElement;
      }

      const surfaces = [
        modalRef.current,
        document.querySelector(".tos-task-details-fullpage"),
        document.querySelector(".tos-task-details-reference-v1"),
        document.querySelector(".tos-premium-page-viewport"),
        document.scrollingElement,
      ];
      surfaces.forEach(resetNodeScroll);

      try {
        window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      } catch {
        window.scrollTo(0, 0);
      }
    };

    const releaseScrollLock = () => {
      scrollLockActive = false;
      if (resizeObserver) {
        resizeObserver.disconnect();
        resizeObserver = null;
      }
    };

    const scroller = taskDetailsBodyRef.current;
    const interactionEvents = ["wheel", "touchstart", "pointerdown", "keydown"];
    interactionEvents.forEach((eventName) => scroller?.addEventListener(eventName, releaseScrollLock, { passive: true, once: true }));

    resetTaskDetailsScrollOwners();
    frameIds.push(window.requestAnimationFrame(() => {
      resetTaskDetailsScrollOwners();
      frameIds.push(window.requestAnimationFrame(resetTaskDetailsScrollOwners));
    }));

    [60, 150, 350, 700, 1200, 1800].forEach((delay) => {
      timeoutIds.push(window.setTimeout(resetTaskDetailsScrollOwners, delay));
    });

    if (typeof ResizeObserver !== "undefined" && scroller) {
      resizeObserver = new ResizeObserver(() => {
        if (!scrollLockActive) return;
        resetTaskDetailsScrollOwners();
      });
      resizeObserver.observe(scroller);
      if (scroller.firstElementChild) resizeObserver.observe(scroller.firstElementChild);
    }

    return () => {
      scrollLockActive = false;
      frameIds.forEach((id) => window.cancelAnimationFrame(id));
      timeoutIds.forEach((id) => window.clearTimeout(id));
      if (resizeObserver) resizeObserver.disconnect();
      interactionEvents.forEach((eventName) => scroller?.removeEventListener(eventName, releaseScrollLock));
    };
  }, [task?.id]);'''

if updated_board.count(old_effect) != 1:
    fail(f"expected exactly one R19 reset effect, found {updated_board.count(old_effect)}")
updated_board = updated_board.replace(old_effect, new_effect, 1)

r22_import = 'import "../styles/taskDetailsV2_12_Phase1R22FocusTrapNoScroll.css";'
r23_import = 'import "../styles/taskDetailsV2_12_Phase1R23LateLayoutScrollLock.css";'
if r22_import not in updated_board:
    fail("R22 stylesheet import missing")
if r23_import in updated_board:
    fail("R23 stylesheet import already exists")
updated_board = updated_board.replace(r22_import, r22_import + "\n" + r23_import, 1)

for contract in (
    'data-tos-task-scroll-owner="r23"',
    'scroller.dataset.tosTaskDetailsScrollReset = "r23";',
    'scroller.style.overflowAnchor = "none";',
    'new ResizeObserver',
    '[60, 150, 350, 700, 1200, 1800]',
    'releaseScrollLock',
    r23_import,
):
    if contract not in updated_board:
        fail(f"R23 source contract missing after edit: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R23_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
if manifest.get("sourceRoot") != str(ROOT):
    fail("runtime sourceRoot does not match target")
frontend_runtime = manifest.get("frontend") or {}
if Path(str(frontend_runtime.get("sourceDir") or "")) != FRONTEND:
    fail("frontend runtime sourceDir mismatch")
if str(frontend_runtime.get("buildCommand") or "") != "npm run build":
    fail("unexpected frontend build command")
DIST = Path(str(frontend_runtime.get("buildOutputDir") or ""))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if DIST != FRONTEND / "dist":
    fail(f"unexpected frontend build output: {DIST}")
if LIVE != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {LIVE}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r23-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r23-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r23-backup-{stamp}"
live_swapped = False
r23_written = False

try:
    BOARD.write_text(updated_board)
    R23_STYLE.write_text(payload_css.rstrip() + "\n")
    r23_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for marker in (R23_MARKER, R22_MARKER, R20_MARKER, R19_MARKER):
        if marker not in built_css:
            fail(f"required runtime marker missing from built CSS: {marker}")
    if "tosTaskDetailsScrollReset" not in built_js or "r23" not in built_js or "ResizeObserver" not in built_js:
        fail("R23 late-layout scroll lock missing from built JS")

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
    for marker in (R23_MARKER, R22_MARKER, R20_MARKER, R19_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")
    if "tosTaskDetailsScrollReset" not in live_js or "r23" not in live_js or "ResizeObserver" not in live_js:
        fail("R23 late-layout scroll lock missing from live JS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r23_written and R23_STYLE.exists():
        R23_STYLE.unlink()
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"VERSION={VERSION}")
print(f"PATCH={PATCH_NAME}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("R22_FOCUS_FIX_PRESERVED=YES")
print("R20_KEYED_SCROLL_CONTAINER_PRESERVED=YES")
print("TASK_SCROLL_OWNER_MARKED=YES")
print("SCROLL_ANCHOR_DISABLED=YES")
print("LATE_LAYOUT_SCROLL_LOCK=YES")
print("RESIZE_OBSERVER_GUARD=YES")
print("USER_INTERACTION_RELEASES_LOCK=YES")
print("POST_LAYOUT_RETRIES=60,150,350,700,1200,1800")
print("LAYOUT_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("SIDEBAR_JS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
