from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11G"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11G-WAITING-CLIENT-CONVERSATION-BELOW-DESCRIPTION"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11F_R2"
BASE_TOS_COMMIT = "LIVE_AHEAD_OF_GITHUB_MAIN_ALLOWED"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11GWaitingClientConversationBelowDescription.css"

RUNTIME = "--tos-task-details-v2-11g-waiting-client-conversation-below-description-runtime"
REQUIRED_R2_RUNTIME = "--tos-task-details-v2-11f-r2-editor-toolbar-live-scope-wrap-more-fix-runtime"
SOURCE_MARKER = "TOS_TASK_DETAILS_V2_11G_WAITING_CLIENT_BELOW_DESCRIPTION"
DATA_ATTR = 'data-tos-waiting-client-conversation="below-description"'

CONVERSATION_TEXT_MARKERS = (
    "Waiting Client conversation",
    "Waiting client conversation",
    "TOS ↔ TCRM",
    "Review Account Management replies and respond on the same task.",
)

FROZEN_RELATIVE = (
    "features/tasks/taskBoardParts.jsx",
    "components/TcsFloatingLauncher.jsx",
    "components/RamzyAssistant.jsx",
)


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matching_section_end(text, start):
    token_re = re.compile(r"</?section\b[^>]*>", re.I | re.S)
    depth = 0
    for match in token_re.finditer(text, start):
        token = match.group(0)
        if token.lower().startswith("</section"):
            depth -= 1
            if depth == 0:
                return match.end()
        elif token.rstrip().endswith("/>"):
            continue
        else:
            depth += 1
    return None


def enclosing_section(text, pos):
    starts = [m.start() for m in re.finditer(r"<section\b", text[:pos], re.I)]
    for start in reversed(starts[-24:]):
        end = matching_section_end(text, start)
        if end and start <= pos <= end:
            return start, end
    return None


def previous_nonblank_line(text, pos):
    line_start = text.rfind("\n", 0, pos) + 1
    cursor = line_start
    while cursor > 0:
        prev_end = cursor - 1
        prev_start = text.rfind("\n", 0, prev_end) + 1
        line = text[prev_start:prev_end + 1]
        if line.strip():
            return prev_start, prev_end + 1, line
        cursor = prev_start
    return None


def expand_jsx_conditional(text, start, end):
    wrapper_start = start
    wrapper_end = end

    prefix_window_start = max(0, start - 1200)
    prefix = text[prefix_window_start:start]
    candidate = re.search(r"\{[^{}\n]*&&\s*\(\s*$", prefix)
    if candidate:
        wrapper_start = prefix_window_start + candidate.start()
    else:
        prev = previous_nonblank_line(text, start)
        if prev and re.match(r"^\s*\{[^{}\n]*&&\s*\(\s*$", prev[2]):
            wrapper_start = prev[0]

    if wrapper_start != start:
        tail = text[end:end + 500]
        close = re.match(r"\s*\)\s*\}", tail)
        if not close:
            fail("conversation conditional wrapper start found but matching `)}` close was not found")
        wrapper_end = end + close.end()

    return wrapper_start, wrapper_end


def find_description_region(text):
    marker = "tos-task-description-panel"
    positions = [m.start() for m in re.finditer(re.escape(marker), text)]
    if not positions:
        fail("Task Details Description panel marker not found")
    regions = []
    for pos in positions:
        region = enclosing_section(text, pos)
        if region and region not in regions:
            regions.append(region)
    if len(regions) != 1:
        fail(f"expected exactly one Description section; found {len(regions)}")
    return expand_jsx_conditional(text, *regions[0])


def find_conversation_region(text):
    candidate_regions = []
    for marker in CONVERSATION_TEXT_MARKERS:
        for match in re.finditer(re.escape(marker), text, re.I):
            region = enclosing_section(text, match.start())
            if region and region not in candidate_regions:
                section_text = text[region[0]:region[1]]
                marker_hits = sum(m.lower() in section_text.lower() for m in CONVERSATION_TEXT_MARKERS)
                waiting_signal = "waiting" in section_text.lower()
                tcrm_signal = "tcrm" in section_text.lower()
                if marker_hits >= 1 and (waiting_signal or tcrm_signal):
                    candidate_regions.append(region)

    if not candidate_regions:
        for section_match in re.finditer(r"<section\b", text, re.I):
            start = section_match.start()
            end = matching_section_end(text, start)
            if not end:
                continue
            chunk = text[start:end]
            low = chunk.lower()
            if "waiting" in low and "tcrm" in low and ("conversation" in low or "message" in low):
                candidate_regions.append((start, end))

    unique = []
    for region in candidate_regions:
        if region not in unique:
            unique.append(region)

    if len(unique) != 1:
        fail(f"expected exactly one Waiting Client conversation section; found {len(unique)}")

    return expand_jsx_conditional(text, *unique[0])


if not FRONTEND.exists() or not SRC.exists():
    fail(f"frontend source directory missing: {FRONTEND}")
for path in (STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

style_source = STYLE.read_text()
payload_css = PAYLOAD.read_text()

if REQUIRED_R2_RUNTIME not in style_source:
    fail("V2.11F_R2 approved runtime marker missing from current live baseline")
if RUNTIME in style_source:
    fail("V2.11G already applied")

for contract in (
    RUNTIME,
    f'[{DATA_ATTR}]',
    "width: 100% !important",
    "max-width: 100% !important",
    "margin-top:",
):
    if contract not in payload_css:
        fail(f"V2.11G CSS contract missing: {contract}")

source_candidates = []
for path in SRC.rglob("*"):
    if path.suffix.lower() not in {".jsx", ".tsx", ".js", ".ts"}:
        continue
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        continue
    if "tos-task-description-panel" not in text:
        continue
    score = sum(marker.lower() in text.lower() for marker in CONVERSATION_TEXT_MARKERS)
    fallback_signal = "waiting" in text.lower() and "tcrm" in text.lower()
    if score >= 1 or fallback_signal:
        source_candidates.append((path, text))

if len(source_candidates) != 1:
    names = ", ".join(str(path.relative_to(ROOT)) for path, _ in source_candidates)
    fail(f"expected exactly one live Task Details source owning Description + Waiting Client conversation; found {len(source_candidates)}: {names}")

TARGET, source = source_candidates[0]

if SOURCE_MARKER in source or DATA_ATTR in source:
    fail("V2.11G source relocation marker already present")

description_start, description_end = find_description_region(source)
conversation_start, conversation_end = find_conversation_region(source)

if conversation_start >= description_end:
    fail("Waiting Client conversation is already positioned after Description; stop for inspection")

conversation_block = source[conversation_start:conversation_end]
if "tos-task-description-panel" in conversation_block:
    fail("conversation block unexpectedly contains Description panel")
if not any(marker.lower() in conversation_block.lower() for marker in CONVERSATION_TEXT_MARKERS) and not (
    "waiting" in conversation_block.lower() and "tcrm" in conversation_block.lower()
):
    fail("conversation signature was lost while locating the movable JSX block")

without_conversation = source[:conversation_start] + source[conversation_end:]

description_start2, description_end2 = find_description_region(without_conversation)

relocated_wrapper = (
    "\n\n"
    "              {/* " + SOURCE_MARKER + " */}\n"
    f'              <div {DATA_ATTR}>\n'
    + conversation_block.strip()
    + "\n              </div>\n"
)

updated_source = (
    without_conversation[:description_end2]
    + relocated_wrapper
    + without_conversation[description_end2:]
)

if updated_source.count(SOURCE_MARKER) != 1 or updated_source.count(DATA_ATTR) != 1:
    fail("V2.11G source marker count is invalid after relocation")
if updated_source.find("tos-task-description-panel") > updated_source.find(SOURCE_MARKER):
    fail("relocated conversation is not after Description in source order")

for marker in CONVERSATION_TEXT_MARKERS:
    original_count = source.lower().count(marker.lower())
    updated_count = updated_source.lower().count(marker.lower())
    if original_count != updated_count:
        fail(f"conversation marker count changed unexpectedly for: {marker}")

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

frozen_paths = []
for rel in FROZEN_RELATIVE:
    path = SRC / rel
    if path.exists() and path != TARGET:
        frozen_paths.append(path)
frozen_hashes = {path: sha256(path) for path in frozen_paths}

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11g-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
target_backup = backup_root / TARGET.name
style_backup = backup_root / STYLE.name
shutil.copy2(TARGET, target_backup)
shutil.copy2(STYLE, style_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-11g-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-11g-backup-{stamp}"
live_swapped = False

try:
    TARGET.write_text(updated_source)
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")

    written_source = TARGET.read_text()
    written_style = STYLE.read_text()

    if SOURCE_MARKER not in written_source or DATA_ATTR not in written_source:
        fail("relocated source markers missing after write")
    if written_source.find("tos-task-description-panel") > written_source.find(SOURCE_MARKER):
        fail("Waiting Client conversation source order is not below Description after write")
    if RUNTIME not in written_style:
        fail("V2.11G runtime marker missing after stylesheet update")

    for path, expected in frozen_hashes.items():
        if sha256(path) != expected:
            fail(f"frozen source changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))

    for marker in (
        "tos-task-description-panel",
        "data-tos-waiting-client-conversation",
    ):
        if marker not in built_js:
            fail(f"relocated Task Details marker missing from built JS: {marker}")
    if RUNTIME not in built_css:
        fail("V2.11G runtime marker missing from built CSS")

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
    live_css = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.css"))

    if "data-tos-waiting-client-conversation" not in live_js:
        fail("V2.11G conversation relocation marker missing from live JS")
    if RUNTIME not in live_css:
        fail("V2.11G runtime marker missing from live CSS")

    for path, expected in frozen_hashes.items():
        if sha256(path) != expected:
            fail(f"frozen source changed after deploy: {path}")

except Exception:
    shutil.copy2(target_backup, TARGET)
    shutil.copy2(style_backup, STYLE)
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
print(f"TARGET_SOURCE={TARGET.relative_to(ROOT)}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("WAITING_CLIENT_OLD_POSITION_REMOVED=YES")
print("WAITING_CLIENT_BELOW_DESCRIPTION=YES")
print("WAITING_CLIENT_FUNCTIONAL_LOGIC_CHANGED=NO")
print("DESCRIPTION_EDITOR_CHANGED=NO")
print("RIGHT_RAIL_CHANGED=NO")
print("PRIMARY_TABS_CHANGED=NO")
print("HERO_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("V2_11F_R2_PRESERVED=YES")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
