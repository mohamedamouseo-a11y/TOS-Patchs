from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R22_FOCUS_TRAP_NO_SCROLL"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R22-FOCUS-TRAP-NO-SCROLL"
R20_MARKER = "--tos-task-details-v2-12-phase1-r20-keyed-scroll-container-remount-runtime"
R22_MARKER = "--tos-task-details-v2-12-phase1-r22-focus-trap-no-scroll-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R20_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R20KeyedScrollContainerRemount.css"
R22_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R22FocusTrapNoScroll.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R22FocusTrapNoScroll.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, APP, SIDEBAR, R20_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
parts_source = PARTS.read_text()
r20_source = R20_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R20_MARKER not in r20_source:
    fail("required R20 baseline marker missing")
if R22_STYLE.exists() or R22_MARKER in board_source or R22_MARKER in parts_source:
    fail("Phase 1 R22 already appears to be applied")
if R22_MARKER not in payload_css:
    fail("R22 payload runtime marker missing")

old_trap_call = '  useModalFocusTrap(modalRef, closeButtonRef, onClose, task.id);'
new_trap_call = '  useModalFocusTrap(modalRef, closeButtonRef, onClose, "task-details-modal");'
if board_source.count(old_trap_call) != 1:
    fail(f"expected exactly one Task Details focus trap call, found {board_source.count(old_trap_call)}")
updated_board = board_source.replace(old_trap_call, new_trap_call, 1)

old_initial_focus = '      (initialFocusRef.current || focusable[0] || modal).focus();'
new_initial_focus = '''      const focusTarget = initialFocusRef.current || focusable[0] || modal;
      try { focusTarget.focus({ preventScroll: true }); } catch { focusTarget.focus(); }'''
if parts_source.count(old_initial_focus) != 1:
    fail(f"expected exactly one modal initial focus contract, found {parts_source.count(old_initial_focus)}")
updated_parts = parts_source.replace(old_initial_focus, new_initial_focus, 1)

old_restore_focus = '        previousActiveElement.focus();'
new_restore_focus = '        try { previousActiveElement.focus({ preventScroll: true }); } catch { previousActiveElement.focus(); }'
if updated_parts.count(old_restore_focus) != 1:
    fail(f"expected exactly one modal restore focus contract, found {updated_parts.count(old_restore_focus)}")
updated_parts = updated_parts.replace(old_restore_focus, new_restore_focus, 1)

r20_import = 'import "../styles/taskDetailsV2_12_Phase1R20KeyedScrollContainerRemount.css";'
r22_import = 'import "../styles/taskDetailsV2_12_Phase1R22FocusTrapNoScroll.css";'
if r20_import not in updated_board:
    fail("R20 stylesheet import missing")
if r22_import in updated_board:
    fail("R22 stylesheet import already exists")
updated_board = updated_board.replace(r20_import, r20_import + "\n" + r22_import, 1)

for contract in (
    'useModalFocusTrap(modalRef, closeButtonRef, onClose, "task-details-modal")',
    r22_import,
):
    if contract not in updated_board:
        fail(f"R22 board contract missing after edit: {contract}")
for contract in (
    'focusTarget.focus({ preventScroll: true })',
    'previousActiveElement.focus({ preventScroll: true })',
):
    if contract not in updated_parts:
        fail(f"R22 focus contract missing after edit: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R22_STYLE)
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r22-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
parts_backup = backup_root / PARTS.name
shutil.copy2(BOARD, board_backup)
shutil.copy2(PARTS, parts_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r22-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r22-backup-{stamp}"
live_swapped = False
r22_written = False

try:
    BOARD.write_text(updated_board)
    PARTS.write_text(updated_parts)
    R22_STYLE.write_text(payload_css.rstrip() + "\n")
    r22_written = True

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
    if R22_MARKER not in built_css or R20_MARKER not in built_css:
        fail("required R20/R22 runtime marker missing from built CSS")
    if "task-details-modal" not in built_js or "preventScroll" not in built_js:
        fail("R22 focus behavior missing from built JS")

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
    if R22_MARKER not in live_css or R20_MARKER not in live_css:
        fail("required R20/R22 runtime marker missing from live CSS")
    if "task-details-modal" not in live_js or "preventScroll" not in live_js:
        fail("R22 focus behavior missing from live JS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    shutil.copy2(parts_backup, PARTS)
    if r22_written and R22_STYLE.exists():
        R22_STYLE.unlink()
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
print("TASK_DETAILS_FOCUS_TRAP_STABLE_ACROSS_TASK_CHANGE=YES")
print("MODAL_INITIAL_FOCUS_PREVENT_SCROLL=YES")
print("MODAL_RESTORE_FOCUS_PREVENT_SCROLL=YES")
print("R20_BASELINE_PRESERVED=YES")
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
