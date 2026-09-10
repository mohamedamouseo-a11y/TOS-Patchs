from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsPremiumSaasReferenceV1.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"

EXPECTED_STYLE_BLOB = "eac2c8de879a670962509fd884da360b4a779840"
RUNTIME = "--tos-task-details-shell-geometry-v1-2-runtime"

OLD_DESKTOP_GEOMETRY = '''@media (min-width:1024px){
  .tos-task-details-reference-v1[dir="ltr"]{top:72px!important;right:0!important;bottom:0!important;left:272px!important}
  .tos-task-details-reference-v1[dir="rtl"]{top:72px!important;right:272px!important;bottom:0!important;left:0!important}
  body:has(.tos-premium-sidebar[data-collapsed="true"]) .tos-task-details-reference-v1[dir="ltr"]{left:88px!important}
  body:has(.tos-premium-sidebar[data-collapsed="true"]) .tos-task-details-reference-v1[dir="rtl"]{right:88px!important}
}'''

NEW_DESKTOP_GEOMETRY = '''@media (min-width:1024px){
  /* The modal is rendered inside the Tasks app-content containing block, which already
     starts after the global sidebar. Re-applying 272px/88px here double-offsets the
     Task Details canvas. Keep the global topbar offset, but consume the full available
     Tasks content width for both LTR and RTL. */
  .tos-task-details-reference-v1[dir="ltr"],
  .tos-task-details-reference-v1[dir="rtl"]{
    top:72px!important;
    right:0!important;
    bottom:0!important;
    left:0!important;
    width:auto!important;
    max-width:none!important;
  }
  body:has(.tos-premium-sidebar[data-collapsed="true"]) .tos-task-details-reference-v1[dir="ltr"],
  body:has(.tos-premium-sidebar[data-collapsed="true"]) .tos-task-details-reference-v1[dir="rtl"]{
    right:0!important;
    left:0!important;
  }
}'''


def fail(message):
    raise RuntimeError(message)


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


for path in (BOARD, STYLE, MANIFEST):
    if not path.exists():
        fail(f"required file missing: {path}")

if git_blob_sha(STYLE) != EXPECTED_STYLE_BLOB:
    fail(f"Task Details V1 stylesheet baseline changed: expected={EXPECTED_STYLE_BLOB} actual={git_blob_sha(STYLE)}")

board_source = BOARD.read_text()
style_source = STYLE.read_text()

required_board_markers = [
    'import "../styles/taskDetailsPremiumSaasReferenceV1.css";',
    "tos-task-details-reference-v1",
    "tos-task-reference-header",
    'className="tos-task-reference-tab"',
    '["checklist", "subtasks"].includes(activeTaskTab)',
    'handleTaskStatusChange("DONE")',
]
for marker in required_board_markers:
    if marker not in board_source:
        fail(f"Task Details V1/R1 source marker missing: {marker}")

if style_source.count(OLD_DESKTOP_GEOMETRY) != 1:
    fail(f"desktop shell geometry baseline marker count unexpected: {style_source.count(OLD_DESKTOP_GEOMETRY)}")
if RUNTIME in style_source:
    fail("Task Details V1.2 shell geometry fix is already present")

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
live = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if live != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {live}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-shell-geometry-v1-2-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-shell-geometry-v1-2-staging-{stamp}"
live_backup = live.parent / f"build.task-details-shell-geometry-v1-2-backup-{stamp}"
live_swapped = False

try:
    updated_style = style_source.replace(OLD_DESKTOP_GEOMETRY, NEW_DESKTOP_GEOMETRY, 1)
    updated_style += f'\n\n:root {{ {RUNTIME}: 1; }}\n'

    if 'left:272px!important' in updated_style or 'right:272px!important' in updated_style:
        fail("legacy expanded-sidebar double offset still present after transform")
    if 'left:88px!important' in updated_style or 'right:88px!important' in updated_style:
        fail("legacy collapsed-sidebar double offset still present after transform")
    if RUNTIME not in updated_style:
        fail("V1.2 runtime marker missing after transform")

    STYLE.write_text(updated_style)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    if RUNTIME not in built_css:
        fail("V1.2 shell geometry runtime marker missing from built CSS")
    if "tos-task-details-reference-v1" not in built_js:
        fail("Task Details V1 root marker missing from built JS")
    if "Mark as complete" not in built_js and "إكمال المهمة" not in built_js:
        fail("Task Details completion action missing from built JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css:
        fail("V1.2 shell geometry runtime marker missing from live CSS")
    if "tos-task-details-reference-v1" not in live_js:
        fail("Task Details V1 root marker missing from live JS")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TASK_DETAILS_PREMIUM_SAAS_REFERENCE_V1_2_RUNTIME=YES")
    print("SHELL_GEOMETRY_FIX=FULL_TASKS_CONTENT_WIDTH")
    print("EXPANDED_SIDEBAR_DOUBLE_OFFSET=REMOVED")
    print("COLLAPSED_SIDEBAR_DOUBLE_OFFSET=REMOVED")
    print("LTR_GEOMETRY=LEFT_0_RIGHT_0")
    print("RTL_GEOMETRY=LEFT_0_RIGHT_0")
    print("TOPBAR_OFFSET_72=PRESERVED")
    print("REFERENCE_VIEWPORT=1664x936")
    print("TASK_APIS_CHANGED=NO")
    print("TASK_DATA_CONTRACT_CHANGED=NO")
    print("TASK_PERMISSIONS_CHANGED=NO")
    print("TASK_BUSINESS_LOGIC_CHANGED=NO")
    print("TWS_INTERNALS_CHANGED=NO")
    print("RAMZY_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"SOURCE_BACKUP={backup_root}")
    print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
    print("STATUS=READY_FOR_VISUAL_QA")
except Exception as exc:
    try:
        if style_backup.exists():
            shutil.copy2(style_backup, STYLE)
        if live_swapped and live.exists() and live_backup.exists():
            shutil.rmtree(live)
            live_backup.rename(live)
        elif live_backup.exists() and not live.exists():
            live_backup.rename(live)
        if staging.exists():
            shutil.rmtree(staging)
    except Exception:
        pass
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
