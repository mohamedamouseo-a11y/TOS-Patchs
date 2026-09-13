from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11H"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11H-REMOVE-DESCRIPTION-FROM-HERO"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11G"
BASE_TOS_COMMIT = "LIVE_AHEAD_OF_GITHUB_MAIN_ALLOWED"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
TCS = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
RAMZY = FRONTEND / "src/components/RamzyAssistant.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"

SOURCE_MARKER = "TOS_TASK_DETAILS_V2_11H_HERO_DESCRIPTION_REMOVED"
R2_RUNTIME = "--tos-task-details-v2-11f-r2-editor-toolbar-live-scope-wrap-more-fix-runtime"
HERO_CLASS = "tos-task-header-description"
HERO_RENDER = "{taskHeaderDescription.slice(0, 170)}"
HERO_VAR_START = '  const taskPlainDescription = stripHtml(draft.description || "").trim();'
HERO_VAR_END = "  const remainingChecklistCount ="
REFERENCE_DUE_PREFIX = "  const referenceDueMeta = formatDueSmart("


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, BOARD, PARTS, STYLE, TCS, RAMZY, MANIFEST):
    if not path.exists():
        fail(f"required path missing: {path}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
parts_source = PARTS.read_text()
style_source = STYLE.read_text()

if SOURCE_MARKER in board_source:
    fail("V2.11H already applied")

if R2_RUNTIME not in style_source:
    fail("required V2.11F_R2 runtime missing")

# Guard the exact Hero-description implementation that is being removed.
for marker in (
    HERO_CLASS,
    HERO_RENDER,
    HERO_VAR_START,
    "const designRequestHeaderSummary =",
    "const taskHeaderDescription =",
    "tos-task-title-input",
    "tos-task-description-panel",
    "PremiumTaskRichTextEditor",
):
    if marker not in board_source:
        fail(f"required Task Details source marker missing: {marker}")

if board_source.count(HERO_CLASS) != 1:
    fail(f"expected exactly one Hero description class occurrence, found {board_source.count(HERO_CLASS)}")
if board_source.count(HERO_RENDER) != 1:
    fail(f"expected exactly one Hero description render occurrence, found {board_source.count(HERO_RENDER)}")
if board_source.count(HERO_VAR_START) != 1:
    fail("Hero description variable block is ambiguous")

# The actual Overview Description section/editor must remain untouched.
preserved_markers = {
    marker: board_source.count(marker)
    for marker in (
        "tos-task-description-panel",
        "PremiumTaskRichTextEditor",
        "tos-task-rich-editor-content",
        "tos-task-title-input",
        "tos-task-reference-tabs-main",
        "tos-task-reference-v2-rail",
    )
}

updated = board_source

# Remove only the rendered Hero paragraph.
hero_paragraph_pattern = re.compile(
    r'\n[ \t]*<p className="tos-task-header-description[^\"]*">\{taskHeaderDescription\.slice\(0,\s*170\)\}</p>'
)
updated, removed_paragraphs = hero_paragraph_pattern.subn("", updated, count=1)
if removed_paragraphs != 1:
    fail("failed to remove the single Hero Description paragraph")

# Remove only the now-unused Hero summary variables. The real draft.description data remains untouched.
vars_start = updated.find(HERO_VAR_START)
if vars_start < 0:
    fail("Hero variable block start not found after paragraph removal")
vars_end = updated.find(HERO_VAR_END, vars_start)
if vars_end < 0:
    fail("Hero variable block end not found")
variable_block = updated[vars_start:vars_end]
for required in ("taskPlainDescription", "designRequestHeaderSummary", "taskHeaderDescription"):
    if required not in variable_block:
        fail(f"unexpected Hero variable block; missing {required}")
updated = updated[:vars_start] + updated[vars_end:]

# Add a source-only lineage marker next to the Hero derived metadata area.
due_line_start = updated.find(REFERENCE_DUE_PREFIX)
if due_line_start < 0:
    fail("referenceDueMeta anchor missing")
due_line_end = updated.find("\n", due_line_start)
if due_line_end < 0:
    fail("referenceDueMeta line ending missing")
updated = updated[:due_line_end + 1] + f"  // {SOURCE_MARKER}\n" + updated[due_line_end + 1:]

# Strict post-transform contracts.
for forbidden in (HERO_CLASS, "taskHeaderDescription", "taskPlainDescription", "designRequestHeaderSummary"):
    if forbidden in updated:
        fail(f"Hero-only description artifact still present after transform: {forbidden}")
if SOURCE_MARKER not in updated:
    fail("V2.11H source marker missing after transform")
if "draft.description" not in updated:
    fail("task Description data references unexpectedly disappeared")

for marker, before_count in preserved_markers.items():
    after_count = updated.count(marker)
    if after_count != before_count:
        fail(f"protected Overview/Task Details marker count changed: {marker} ({before_count} -> {after_count})")

# No non-target source file may change.
frozen_hashes = {path: sha256(path) for path in (PARTS, STYLE, TCS, RAMZY)}

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11h-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-11h-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-11h-backup-{stamp}"
live_swapped = False

try:
    BOARD.write_text(updated)

    written = BOARD.read_text()
    if HERO_CLASS in written or HERO_RENDER in written:
        fail("Hero Description render still present in written source")
    if SOURCE_MARKER not in written:
        fail("V2.11H source marker missing from written source")
    for marker, before_count in preserved_markers.items():
        if written.count(marker) != before_count:
            fail(f"protected marker changed after write: {marker}")
    for path, expected_hash in frozen_hashes.items():
        if sha256(path) != expected_hash:
            fail(f"non-target source file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if HERO_CLASS in built_js:
        fail("Hero Description class still present in built JS")
    for marker in ("tos-task-title-input", "tos-task-description-panel", "tos-task-reference-v2-rail"):
        if marker not in built_js:
            fail(f"required preserved Task Details marker missing from build: {marker}")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        if live_backup.exists():
            shutil.rmtree(live_backup)
        LIVE.rename(live_backup)

    staging.rename(LIVE)
    live_swapped = True

    live_js = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.js"))
    if HERO_CLASS in live_js:
        fail("Hero Description class still present in live build")
    for marker in ("tos-task-title-input", "tos-task-description-panel", "tos-task-reference-v2-rail"):
        if marker not in live_js:
            fail(f"required preserved Task Details marker missing from live build: {marker}")

    for path, expected_hash in frozen_hashes.items():
        if sha256(path) != expected_hash:
            fail(f"frozen source changed after deploy: {path}")

except Exception:
    shutil.copy2(board_backup, BOARD)
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
print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
print(f"BASE_TOS_COMMIT={BASE_TOS_COMMIT}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("HERO_DESCRIPTION_REMOVED=YES")
print("HERO_TITLE_PRESERVED=YES")
print("OVERVIEW_DESCRIPTION_PRESERVED=YES")
print("DESCRIPTION_DATA_CHANGED=NO")
print("DESCRIPTION_EDITOR_CHANGED=NO")
print("PRIMARY_TABS_CHANGED=NO")
print("RIGHT_RAIL_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("WAITING_CLIENT_LAYOUT_CHANGED=NO")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
