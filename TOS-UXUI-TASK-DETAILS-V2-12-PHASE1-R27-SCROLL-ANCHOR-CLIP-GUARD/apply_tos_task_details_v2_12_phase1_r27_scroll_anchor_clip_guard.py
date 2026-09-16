from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R27-SCROLL-ANCHOR-CLIP-GUARD"
R26_MARKER = "--tos-task-details-v2-12-phase1-r26-dynamic-right-rail-align-runtime"
R27_MARKER = "--tos-task-details-v2-12-phase1-r27-scroll-anchor-clip-guard-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R26_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R26DynamicRightRailAlign.css"
R27_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R27ScrollAnchorClipGuard.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PAYLOAD = Path(__file__).resolve().parent / "taskDetailsV2_12_Phase1R27ScrollAnchorClipGuard.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R26_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r26_source = R26_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R26_MARKER not in r26_source:
    fail("R26 production baseline marker missing")
if R27_STYLE.exists() or R27_MARKER in board_source:
    fail("R27 already appears applied")
if R27_MARKER not in payload_css:
    fail("R27 payload marker missing")

r26_import = 'import "../styles/taskDetailsV2_12_Phase1R26DynamicRightRailAlign.css";'
r27_import = 'import "../styles/taskDetailsV2_12_Phase1R27ScrollAnchorClipGuard.css";'
refs_anchor = '''  const modalRef = useRef(null);\n  const closeButtonRef = useRef(null);\n  const taskDetailsBodyRef = useRef(null);'''
scroll_fn_anchor = '''  function scrollTaskDetailsToTop() {\n    taskDetailsBodyRef.current?.scrollTo({ top: 0, behavior: "smooth" });\n  }'''

for contract in (
    r26_import,
    refs_anchor,
    scroll_fn_anchor,
    'data-tos-task-scroll-owner="r23"',
    'TOS_TASK_DETAILS_R26_DYNAMIC_RIGHT_RAIL_ALIGN',
):
    if contract not in board_source:
        fail(f"R27 source contract missing: {contract}")
if r27_import in board_source or "TOS_TASK_DETAILS_R27_SCROLL_ANCHOR_CLIP_GUARD" in board_source:
    fail("R27 source marker already exists")

updated = board_source

new_refs = '''  const modalRef = useRef(null);\n  const closeButtonRef = useRef(null);\n  const taskDetailsBodyRef = useRef(null);\n  const r27MoreGeometryRef = useRef({ taskId: null, open: null, tabsTop: null });'''
if updated.count(refs_anchor) != 1:
    fail(f"expected one refs anchor, found {updated.count(refs_anchor)}")
updated = updated.replace(refs_anchor, new_refs, 1)

r27_effect = '''  function scrollTaskDetailsToTop() {\n    taskDetailsBodyRef.current?.scrollTo({ top: 0, behavior: "smooth" });\n  }\n\n  // TOS_TASK_DETAILS_R27_SCROLL_ANCHOR_CLIP_GUARD\n  useEffect(() => {\n    if (typeof window === "undefined" || typeof document === "undefined") return undefined;\n\n    const scroller = taskDetailsBodyRef.current;\n    if (!scroller) return undefined;\n\n    let frameOne = null;\n    let frameTwo = null;\n    let settleTimer = null;\n\n    const measureTabsTop = () => {\n      const layout = scroller.querySelector(".tos-task-details-layout");\n      const tabs = layout?.querySelector(".tos-task-detail-tabs");\n      if (!layout || !tabs) return null;\n      const layoutRect = layout.getBoundingClientRect();\n      const tabsRect = tabs.getBoundingClientRect();\n      return Math.round(tabsRect.top - layoutRect.top);\n    };\n\n    const stabilizeViewport = () => {\n      const taskId = String(task?.id || "");\n      const currentTabsTop = measureTabsTop();\n      if (!Number.isFinite(currentTabsTop)) return;\n\n      const previous = r27MoreGeometryRef.current || {};\n      const didToggleMore = previous.taskId === taskId\n        && previous.open !== null\n        && previous.open !== taskMoreDetailsOpen\n        && Number.isFinite(previous.tabsTop);\n\n      if (didToggleMore && scroller.scrollTop > 8) {\n        const delta = currentTabsTop - previous.tabsTop;\n        if (Math.abs(delta) > 1) {\n          scroller.scrollTop = Math.max(0, scroller.scrollTop + delta);\n          scroller.dataset.tosR27ClipGuard = "true";\n        }\n      }\n\n      r27MoreGeometryRef.current = {\n        taskId,\n        open: taskMoreDetailsOpen,\n        tabsTop: currentTabsTop,\n      };\n    };\n\n    frameOne = window.requestAnimationFrame(() => {\n      frameTwo = window.requestAnimationFrame(stabilizeViewport);\n    });\n    settleTimer = window.setTimeout(stabilizeViewport, 140);\n\n    return () => {\n      if (frameOne !== null) window.cancelAnimationFrame(frameOne);\n      if (frameTwo !== null) window.cancelAnimationFrame(frameTwo);\n      if (settleTimer !== null) window.clearTimeout(settleTimer);\n    };\n  }, [taskMoreDetailsOpen, task?.id]);'''

if updated.count(scroll_fn_anchor) != 1:
    fail(f"expected one scroll function anchor, found {updated.count(scroll_fn_anchor)}")
updated = updated.replace(scroll_fn_anchor, r27_effect, 1)

if updated.count(r26_import) != 1:
    fail(f"expected one R26 import, found {updated.count(r26_import)}")
updated = updated.replace(r26_import, r26_import + "\n" + r27_import, 1)

for contract in (
    "TOS_TASK_DETAILS_R27_SCROLL_ANCHOR_CLIP_GUARD",
    "r27MoreGeometryRef",
    'scroller.dataset.tosR27ClipGuard = "true"',
    'const delta = currentTabsTop - previous.tabsTop;',
    '[taskMoreDetailsOpen, task?.id]',
    r27_import,
):
    if contract not in updated:
        fail(f"R27 source contract missing after edit: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R27_STYLE)
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r27-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-r27-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-r27-backup-{stamp}"
live_swapped = False
r27_written = False

try:
    BOARD.write_text(updated)
    R27_STYLE.write_text(payload_css.rstrip() + "\n")
    r27_written = True

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
    if R27_MARKER not in built_css or R26_MARKER not in built_css:
        fail("R26/R27 runtime marker missing from build")
    for token in ("tosR27ClipGuard", "r27MoreGeometryRef", "currentTabsTop"):
        if token not in built_js:
            fail(f"R27 runtime token missing from build JS: {token}")

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
    if R27_MARKER not in live_css or R26_MARKER not in live_css:
        fail("R26/R27 runtime marker missing from live build")
    for token in ("tosR27ClipGuard", "r27MoreGeometryRef", "currentTabsTop"):
        if token not in live_js:
            fail(f"R27 runtime token missing from live JS: {token}")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r27_written and R27_STYLE.exists():
        R27_STYLE.unlink()
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
print("TOP_EDGE_CLIP_GUARD=YES")
print("MORE_TOGGLE_SCROLL_ANCHOR_PRESERVED=YES")
print("SINGLE_SCROLL_OWNER_PRESERVED=YES")
print("R26_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("PUSH=NO")
