from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R24-ASSIGNEE-FLOATING-DROPDOWN"
R23_MARKER = "--tos-task-details-v2-12-phase1-r23-late-layout-scroll-lock-runtime"
R24_MARKER = "--tos-task-details-v2-12-phase1-r24-assignee-floating-dropdown-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R23_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R23LateLayoutScrollLock.css"
R24_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R24AssigneeFloatingDropdown.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PAYLOAD = Path(__file__).resolve().parent / "taskDetailsV2_12_Phase1R24AssigneeFloatingDropdown.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R23_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r23_source = R23_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R23_MARKER not in r23_source:
    fail("R23 production baseline marker missing")
if R24_STYLE.exists() or R24_MARKER in board_source:
    fail("R24 already appears applied")
if R24_MARKER not in payload_css:
    fail("R24 payload marker missing")

for contract in (
    'className="tos-task-v2-assignee-popover"',
    'className="tos-task-v2-assignee-picker-trigger"',
    'document.body',
    'const estimatedHeight = Math.min(300, Math.max(220, filteredMembers.length * 48 + 112));',
):
    if contract not in board_source:
        fail(f"Assignee source contract missing: {contract}")

old_geometry = '''      const width = 336;
      const estimatedHeight = Math.min(300, Math.max(220, filteredMembers.length * 48 + 112));
      const padding = 12;
      const preferredLeft = direction === "rtl" ? rect.right - width : rect.left;
      const left = Math.min(Math.max(padding, preferredLeft), Math.max(padding, window.innerWidth - width - padding));
      const belowTop = rect.bottom + 8;
      const aboveTop = rect.top - estimatedHeight - 8;
      const top = belowTop + estimatedHeight <= window.innerHeight - padding ? belowTop : Math.max(padding, aboveTop);
      setPopoverStyle({ top: `${Math.round(top)}px`, left: `${Math.round(left)}px` });'''

new_geometry = '''      const padding = 12;
      const width = Math.min(336, Math.max(240, window.innerWidth - (padding * 2)));
      const desiredHeight = Math.min(420, Math.max(220, filteredMembers.length * 48 + 112));
      const preferredLeft = direction === "rtl" ? rect.right - width : rect.left;
      const left = Math.min(Math.max(padding, preferredLeft), Math.max(padding, window.innerWidth - width - padding));
      const spaceBelow = Math.max(0, window.innerHeight - rect.bottom - padding - 8);
      const spaceAbove = Math.max(0, rect.top - padding - 8);
      const openBelow = spaceBelow >= Math.min(desiredHeight, 260) || spaceBelow >= spaceAbove;
      const availableSpace = Math.max(120, openBelow ? spaceBelow : spaceAbove);
      const availableHeight = Math.min(desiredHeight, availableSpace);
      const top = openBelow
        ? Math.max(padding, Math.min(rect.bottom + 8, window.innerHeight - availableHeight - padding))
        : Math.max(padding, rect.top - availableHeight - 8);
      setPopoverStyle({
        position: "fixed",
        zIndex: 2147483000,
        top: `${Math.round(top)}px`,
        left: `${Math.round(left)}px`,
        width: `${Math.round(width)}px`,
        maxHeight: `${Math.max(120, Math.floor(availableHeight))}px`,
        "--tos-assignee-available-height": `${Math.max(120, Math.floor(availableHeight))}px`,
      });'''

if board_source.count(old_geometry) != 1:
    fail(f"expected one Assignee geometry block, found {board_source.count(old_geometry)}")
updated_board = board_source.replace(old_geometry, new_geometry, 1)

r23_import = 'import "../styles/taskDetailsV2_12_Phase1R23LateLayoutScrollLock.css";'
r24_import = 'import "../styles/taskDetailsV2_12_Phase1R24AssigneeFloatingDropdown.css";'
if r23_import not in updated_board:
    fail("R23 stylesheet import missing")
if r24_import in updated_board:
    fail("R24 stylesheet import already exists")
updated_board = updated_board.replace(r23_import, r23_import + "\n" + r24_import, 1)

for contract in (
    'position: "fixed"',
    'zIndex: 2147483000',
    'const spaceBelow = Math.max(0',
    'const spaceAbove = Math.max(0',
    '"--tos-assignee-available-height"',
    r24_import,
):
    if contract not in updated_board:
        fail(f"R24 source contract missing after edit: {contract}")

for contract in (
    'body > .tos-task-v2-assignee-popover',
    'position:fixed!important',
    'z-index:2147483000!important',
    '.tos-task-v2-assignee-list',
    'padding-bottom:22px!important',
):
    if contract not in payload_css:
        fail(f"R24 CSS contract missing: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R24_STYLE)
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r24-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)
LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-r24-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-r24-backup-{stamp}"
live_swapped = False
r24_written = False

try:
    BOARD.write_text(updated_board)
    R24_STYLE.write_text(payload_css.rstrip() + "\n")
    r24_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R24_MARKER not in built_css or R23_MARKER not in built_css:
        fail("R23/R24 runtime marker missing from build")
    if "--tos-assignee-available-height" not in built_js:
        fail("R24 Assignee viewport geometry missing from build")

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
    if R24_MARKER not in live_css or R23_MARKER not in live_css:
        fail("R23/R24 runtime marker missing from live build")
    if "--tos-assignee-available-height" not in live_js:
        fail("R24 Assignee viewport geometry missing from live build")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r24_written and R24_STYLE.exists():
        R24_STYLE.unlink()
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
print("ASSIGNEE_FLOATING_DROPDOWN=YES")
print("ASSIGNEE_HERO_STRETCH=REMOVED")
print("ASSIGNEE_INTERNAL_SCROLL=YES")
print("R23_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("PUSH=NO")
