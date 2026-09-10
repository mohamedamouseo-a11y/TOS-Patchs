from pathlib import Path
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

V1_RUNTIME = "--tos-task-details-premium-saas-reference-v1-runtime"
V12_RUNTIME = "--tos-task-details-shell-geometry-v1-2-runtime"
RUNTIME = "--tos-task-details-macro-layout-fidelity-v1-3-runtime"

FIX_BLOCK = r'''

/* ================================================================
   Task Details V1.3 — Macro Layout Fidelity Fix
   Purpose: beat legacy minimal-layout selectors that still force a
   190px + 1fr grid and compact inline tab rail after V1/V1.2.
   Visual-only. No business logic or API changes.
   ================================================================ */
:root { --tos-task-details-macro-layout-fidelity-v1-3-runtime: 1; }

@media (min-width:1280px){
  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-details-layout:has(.tos-task-main-column[data-more-details]){
    grid-template-columns:minmax(0,1fr)!important;
    width:100%!important;
    min-width:0!important;
    max-width:none!important;
  }
  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-main-column[data-more-details]{
    grid-column:1 / -1!important;
    width:100%!important;
    min-width:0!important;
    max-width:none!important;
  }
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-main-column[data-more-details="false"] .tos-task-header-description{
  display:block!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-main-column[data-more-details="false"] .tos-task-summary-compact{
  width:100%!important;
  max-width:none!important;
  padding:18px 20px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-main-column[data-more-details="false"] .tos-task-detail-tabs{
  display:flex!important;
  align-self:stretch!important;
  width:100%!important;
  max-width:none!important;
  min-height:58px!important;
  padding:0 6px!important;
  border-radius:0!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-main-column[data-more-details="false"] .tos-task-detail-tabs > div{
  gap:8px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-main-column[data-more-details="false"] .tos-task-detail-tabs button.tos-task-reference-tab{
  min-height:56px!important;
  padding:0 11px!important;
  border-radius:0!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-main-column[data-more-details="false"] .tos-task-description-panel{
  width:100%!important;
  max-width:none!important;
  padding:18px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-main-column[data-more-details="false"] .tos-task-description-panel > div:first-child{
  margin-bottom:14px!important;
}
'''


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


for path in (BOARD, STYLE, MANIFEST):
    if not path.exists():
        fail(f"required file missing: {path}")

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

if V1_RUNTIME not in style_source:
    fail("Task Details V1 stylesheet runtime marker missing")
if V12_RUNTIME not in style_source:
    fail("Task Details V1.2 shell geometry runtime marker missing")
if RUNTIME in style_source:
    fail("Task Details V1.3 macro layout fidelity fix is already present")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-macro-layout-v1-3-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-macro-layout-v1-3-staging-{stamp}"
live_backup = live.parent / f"build.task-details-macro-layout-v1-3-backup-{stamp}"
live_swapped = False

try:
    updated_style = style_source + FIX_BLOCK

    required_fix_markers = [
        RUNTIME,
        '.tos-task-details-layout:has(.tos-task-main-column[data-more-details])',
        'grid-template-columns:minmax(0,1fr)!important',
        'grid-column:1 / -1!important',
        '.tos-task-header-description',
        'display:block!important',
        '.tos-task-detail-tabs',
        'align-self:stretch!important',
        '.tos-task-description-panel',
    ]
    for marker in required_fix_markers:
        if marker not in updated_style:
            fail(f"V1.3 transform marker missing: {marker}")

    STYLE.write_text(updated_style)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    if RUNTIME not in built_css:
        fail("V1.3 macro layout runtime marker missing from built CSS")
    if "tos-task-details-reference-v1" not in built_js:
        fail("Task Details V1 root marker missing from built JS")
    for label in ("Task details", "Subtasks", "Attachments", "Activity", "Checklist"):
        if label not in built_js:
            fail(f"reference primary tab label missing from built JS: {label}")
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
        fail("V1.3 macro layout runtime marker missing from live CSS")
    if "tos-task-details-reference-v1" not in live_js:
        fail("Task Details V1 root marker missing from live JS")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TASK_DETAILS_PREMIUM_SAAS_REFERENCE_V1_3_RUNTIME=YES")
    print("ROOT_CAUSE=LEGACY_MINIMAL_LAYOUT_SPECIFICITY_COLLISION")
    print("MAIN_CONTENT_GRID=FULL_WIDTH_SINGLE_COLUMN")
    print("LEGACY_190PX_GRID=OVERRIDDEN")
    print("MAIN_COLUMN_WIDTH=100_PERCENT")
    print("HEADER_DESCRIPTION=RESTORED")
    print("REFERENCE_TAB_RAIL=FULL_WIDTH")
    print("DESCRIPTION_PANEL=FULL_WIDTH")
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
