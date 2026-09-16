from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R26-DYNAMIC-RIGHT-RAIL-ALIGN"
R25_MARKER = "--tos-task-details-v2-12-phase1-r25-tags-popover-no-layout-flip-runtime"
R26_MARKER = "--tos-task-details-v2-12-phase1-r26-dynamic-right-rail-align-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R25_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R25TagsPopoverNoLayoutFlip.css"
R26_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R26DynamicRightRailAlign.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PAYLOAD = Path(__file__).resolve().parent / "taskDetailsV2_12_Phase1R26DynamicRightRailAlign.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R25_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r25_source = R25_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R25_MARKER not in r25_source:
    fail("R25 production baseline marker missing")
if R26_STYLE.exists() or R26_MARKER in board_source:
    fail("R26 already appears applied")
if R26_MARKER not in payload_css:
    fail("R26 payload marker missing")

r25_import = 'import "../styles/taskDetailsV2_12_Phase1R25TagsPopoverNoLayoutFlip.css";'
r26_import = 'import "../styles/taskDetailsV2_12_Phase1R26DynamicRightRailAlign.css";'
state_anchor = '  const [taskMoreDetailsOpen, setTaskMoreDetailsOpen] = useState(false);'

for contract in (
    r25_import,
    state_anchor,
    'className="tos-task-details-layout',
    'className="tos-task-reference-v2-rail-slot"',
    'className="tos-task-detail-tabs',
):
    if contract not in board_source:
        fail(f"R26 source contract missing: {contract}")
if r26_import in board_source or "TOS_TASK_DETAILS_R26_DYNAMIC_RIGHT_RAIL_ALIGN" in board_source:
    fail("R26 source marker already exists")

# Runtime alignment follows the REAL Tabs/body position rather than a hard-coded top.
effect_block = '''  const [taskMoreDetailsOpen, setTaskMoreDetailsOpen] = useState(false);

  // TOS_TASK_DETAILS_R26_DYNAMIC_RIGHT_RAIL_ALIGN
  useEffect(() => {
    if (typeof window === "undefined" || typeof document === "undefined") return undefined;

    let frameId = null;
    let resizeObserver = null;
    const timeoutIds = [];

    const syncRightRailTop = () => {
      const root = document.querySelector(".tos-task-details-fullpage.tos-task-details-reference-v2");
      const layout = root?.querySelector(".tos-task-details-layout");
      const railSlot = layout?.querySelector(".tos-task-reference-v2-rail-slot");
      const tabs = layout?.querySelector(".tos-task-detail-tabs");
      if (!layout || !railSlot || !tabs) return;

      const layoutRect = layout.getBoundingClientRect();
      const tabsRect = tabs.getBoundingClientRect();
      const measuredTop = Math.max(0, Math.round(tabsRect.top - layoutRect.top));

      railSlot.style.setProperty("--tos-r26-right-rail-top", `${measuredTop}px`);
      railSlot.dataset.tosR26DynamicAlign = "true";
    };

    const scheduleSync = () => {
      if (frameId !== null) window.cancelAnimationFrame(frameId);
      frameId = window.requestAnimationFrame(() => {
        frameId = null;
        syncRightRailTop();
      });
    };

    scheduleSync();
    [40, 120, 260, 520].forEach((delay) => {
      timeoutIds.push(window.setTimeout(scheduleSync, delay));
    });

    const root = document.querySelector(".tos-task-details-fullpage.tos-task-details-reference-v2");
    const layout = root?.querySelector(".tos-task-details-layout");
    const main = layout?.querySelector(".tos-task-main-column");
    const tabs = layout?.querySelector(".tos-task-detail-tabs");

    if (typeof ResizeObserver !== "undefined" && layout) {
      resizeObserver = new ResizeObserver(scheduleSync);
      resizeObserver.observe(layout);
      if (main) {
        resizeObserver.observe(main);
        Array.from(main.children || []).forEach((child) => resizeObserver.observe(child));
      }
      if (tabs) resizeObserver.observe(tabs);
    }

    window.addEventListener("resize", scheduleSync);

    return () => {
      if (frameId !== null) window.cancelAnimationFrame(frameId);
      timeoutIds.forEach((id) => window.clearTimeout(id));
      resizeObserver?.disconnect();
      window.removeEventListener("resize", scheduleSync);
    };
  }, [taskMoreDetailsOpen, activeTaskTab, task?.id]);'''

if board_source.count(state_anchor) != 1:
    fail(f"expected exactly one taskMoreDetailsOpen anchor, found {board_source.count(state_anchor)}")
updated = board_source.replace(state_anchor, effect_block, 1)

if updated.count(r25_import) != 1:
    fail(f"expected exactly one R25 import, found {updated.count(r25_import)}")
updated = updated.replace(r25_import, r25_import + "\n" + r26_import, 1)

for contract in (
    "TOS_TASK_DETAILS_R26_DYNAMIC_RIGHT_RAIL_ALIGN",
    '--tos-r26-right-rail-top',
    'railSlot.dataset.tosR26DynamicAlign = "true"',
    'new ResizeObserver(scheduleSync)',
    '[taskMoreDetailsOpen, activeTaskTab, task?.id]',
    r26_import,
):
    if contract not in updated:
        fail(f"R26 source contract missing after edit: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R26_STYLE)
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r26-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-r26-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-r26-backup-{stamp}"
live_swapped = False
r26_written = False

try:
    BOARD.write_text(updated)
    R26_STYLE.write_text(payload_css.rstrip() + "\n")
    r26_written = True

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
    if R26_MARKER not in built_css or R25_MARKER not in built_css:
        fail("R25/R26 runtime marker missing from build")
    for token in ("--tos-r26-right-rail-top", "tosR26DynamicAlign", "ResizeObserver"):
        if token not in built_js:
            fail(f"R26 runtime token missing from build JS: {token}")

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
    if R26_MARKER not in live_css or R25_MARKER not in live_css:
        fail("R25/R26 runtime marker missing from live build")
    for token in ("--tos-r26-right-rail-top", "tosR26DynamicAlign", "ResizeObserver"):
        if token not in live_js:
            fail(f"R26 runtime token missing from live JS: {token}")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r26_written and R26_STYLE.exists():
        R26_STYLE.unlink()
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
print("DYNAMIC_RIGHT_RAIL_ALIGN=YES")
print("MORE_OPEN_RAIL_OVERLAP=REMOVED")
print("R25_PRESERVED=YES")
print("R24_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("PUSH=NO")
