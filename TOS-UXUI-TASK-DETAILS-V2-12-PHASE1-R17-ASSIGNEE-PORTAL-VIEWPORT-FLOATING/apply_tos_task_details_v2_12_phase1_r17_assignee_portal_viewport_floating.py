from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R17_ASSIGNEE_PORTAL_VIEWPORT_FLOATING"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R17-ASSIGNEE-PORTAL-VIEWPORT-FLOATING"
R16_MARKER = "--tos-task-details-v2-12-phase1-r16-r13-recovery-safe-bottom-flow-runtime"
R17_MARKER = "--tos-task-details-v2-12-phase1-r17-assignee-portal-viewport-floating-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R16_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R16R13RecoverySafeBottomFlow.css"
R17_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R17AssigneePortalViewportFloating.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R17AssigneePortalViewportFloating.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R16_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r16_source = R16_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R16_MARKER not in r16_source:
    fail("required R16 baseline marker missing")
if R17_STYLE.exists() or R17_MARKER in board_source:
    fail("Phase 1 R17 already appears to be applied")
if R17_MARKER not in payload_css:
    fail("R17 payload runtime marker missing")

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

new_geometry = '''      const width = Math.min(336, Math.max(240, window.innerWidth - 24));
      const desiredHeight = Math.min(420, Math.max(240, filteredMembers.length * 48 + 112));
      const padding = 12;
      const preferredLeft = direction === "rtl" ? rect.right - width : rect.left;
      const left = Math.min(Math.max(padding, preferredLeft), Math.max(padding, window.innerWidth - width - padding));
      const spaceBelow = Math.max(0, window.innerHeight - rect.bottom - padding - 8);
      const spaceAbove = Math.max(0, rect.top - padding - 8);
      const openBelow = spaceBelow >= Math.min(desiredHeight, 260) || spaceBelow >= spaceAbove;
      const availableSpace = Math.max(96, openBelow ? spaceBelow : spaceAbove);
      const availableHeight = Math.min(desiredHeight, availableSpace);
      const belowTop = rect.bottom + 8;
      const top = openBelow
        ? Math.max(padding, Math.min(belowTop, window.innerHeight - availableHeight - padding))
        : Math.max(padding, rect.top - availableHeight - 8);
      setPopoverStyle({
        top: `${Math.round(top)}px`,
        left: `${Math.round(left)}px`,
        width: `${Math.round(width)}px`,
        "--tos-assignee-available-height": `${Math.max(96, Math.floor(availableHeight))}px`,
      });'''

if board_source.count(old_geometry) != 1:
    fail(f"expected exactly one old Assignee geometry block, found {board_source.count(old_geometry)}")
updated_board = board_source.replace(old_geometry, new_geometry, 1)

r16_import = 'import "../styles/taskDetailsV2_12_Phase1R16R13RecoverySafeBottomFlow.css";'
r17_import = 'import "../styles/taskDetailsV2_12_Phase1R17AssigneePortalViewportFloating.css";'
if r16_import not in updated_board:
    fail("R16 stylesheet import missing")
if r17_import in updated_board:
    fail("R17 stylesheet import already exists")
updated_board = updated_board.replace(r16_import, r16_import + "\n" + r17_import, 1)

for contract in (
    'const desiredHeight = Math.min(420',
    'const spaceBelow = Math.max(0',
    'const spaceAbove = Math.max(0',
    '"--tos-assignee-available-height"',
    r17_import,
):
    if contract not in updated_board:
        fail(f"R17 source contract missing after edit: {contract}")

for contract in (
    'body > .tos-task-v2-assignee-popover',
    'position:fixed!important',
    'z-index:2147483000!important',
    'var(--tos-assignee-available-height',
    ':has(.tos-task-v2-assignee-picker-trigger[aria-expanded="true"])',
    'padding-bottom:0!important',
):
    if contract not in payload_css:
        fail(f"R17 CSS contract missing: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R17_STYLE)
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r17-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r17-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r17-backup-{stamp}"
live_swapped = False
r17_written = False

try:
    BOARD.write_text(updated_board)
    R17_STYLE.write_text(payload_css.rstrip() + "\n")
    r17_written = True

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
    for marker in (R17_MARKER, R16_MARKER):
        if marker not in built_css:
            fail(f"required runtime marker missing from built CSS: {marker}")
    if "--tos-assignee-available-height" not in built_js:
        fail("R17 Assignee viewport geometry missing from built JS")

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
    for marker in (R17_MARKER, R16_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")
    if "--tos-assignee-available-height" not in live_js:
        fail("R17 Assignee viewport geometry missing from live JS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r17_written and R17_STYLE.exists():
        R17_STYLE.unlink()
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
print("ASSIGNEE_PORTAL_TARGET=DOCUMENT_BODY")
print("ASSIGNEE_PORTAL_POSITION=FIXED_VIEWPORT")
print("ASSIGNEE_PORTAL_FLIP_ABOVE_BELOW=YES")
print("ASSIGNEE_VIEWPORT_HEIGHT_CLAMP=YES")
print("ASSIGNEE_HERO_SPACE_RESERVATION=REMOVED")
print("ASSIGNEE_LIST_INTERNAL_SCROLL=YES")
print("R16_LAYOUT_PRESERVED=YES")
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
