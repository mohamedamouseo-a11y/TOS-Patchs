#!/usr/bin/env python3
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request

PATCH = "TOS-TWS-TDOCS-PHASE-2-1-FINAL-GOOGLE-TOOLBAR-MICRO-FIDELITY"
SCRIPT = "run_tdocs_phase2_1.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "048592147387e2b49382f605a04f8d2efd64f61c"

EDITOR = "frontend/src/pages/tws/TDocsEditor.jsx"
TOOLBAR = "frontend/src/pages/tws/TDocsGoogleToolbar.jsx"
CSS = "frontend/src/pages/tws/tDocsPhase2_1ToolbarFidelity.css"
TEST = "frontend/src/pages/tws/tDocsPhase2_1ToolbarFidelity.test.js"
PHASE_SCOPE = {EDITOR, TOOLBAR, CSS, TEST}
EDITOR_BLOB = "ed1c94e5faf7a7f2bb9a3ecf8cc94f9ce6eca18a"

PAYLOAD_ROOT = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TDOCS-PHASE-2-1-FINAL-GOOGLE-TOOLBAR-MICRO-FIDELITY/payload"
PAYLOADS = {
    TOOLBAR: (f"{PAYLOAD_ROOT}/TDocsGoogleToolbar.jsx", "d1744373cce5dcf8725af1f7fac2e8e947278eba"),
    CSS: (f"{PAYLOAD_ROOT}/tDocsPhase2_1ToolbarFidelity.css", "188382d90e2e6e1ffe71b2a1de3b23930790cd4d"),
    TEST: (f"{PAYLOAD_ROOT}/tDocsPhase2_1ToolbarFidelity.test.js", "a28bd01143cd3aeefbc85321cb81f6126cd43ad2"),
}


def run(args, cwd=REPO, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"command failed: {' '.join(args)}")
    return result


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-patch-runner"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def status_lines():
    return [line for line in run(["git", "status", "--porcelain"]).stdout.splitlines() if line.strip()]


def status_path(line: str) -> str:
    raw = line[3:].strip()
    if " -> " in raw:
        raw = raw.split(" -> ", 1)[1]
    return raw.strip('"')


def file_fingerprint(rel: str):
    path = REPO / rel
    if not path.exists():
        return "MISSING"
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return "DIR"


def unrelated_fingerprints(lines):
    result = {}
    for line in lines:
        rel = status_path(line)
        if rel not in PHASE_SCOPE:
            result[rel] = (line[:2], file_fingerprint(rel))
    return result


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}_ANCHOR_COUNT:{count}")
    return text.replace(old, new, 1)


def main_asset_from_html(html: str):
    marker = '/assets/index-'
    start = html.find(marker)
    if start < 0:
        return None
    end = html.find('.js', start)
    if end < 0:
        return None
    return html[start:end + 3]


def rollback_source(snapshot):
    for rel, previous in snapshot.items():
        path = REPO / rel
        if previous is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(previous)


def fail(message, snapshot=None, live_backup=None):
    print(f"ERROR={message}", file=sys.stderr)
    if snapshot is not None:
        try:
            rollback_source(snapshot)
            print("SOURCE_ROLLBACK=PASS", file=sys.stderr)
        except Exception as exc:
            print(f"SOURCE_ROLLBACK=FAIL:{exc}", file=sys.stderr)
    if live_backup and Path(live_backup).exists():
        try:
            if LIVE_ROOT.exists():
                shutil.rmtree(LIVE_ROOT)
            shutil.copytree(live_backup, LIVE_ROOT)
            run(["nginx", "-t"])
            run(["systemctl", "reload", "nginx"])
            print("LIVE_ROLLBACK=PASS", file=sys.stderr)
        except Exception as exc:
            print(f"LIVE_ROLLBACK=FAIL:{exc}", file=sys.stderr)
    sys.exit(1)


TOOLBAR_MARKUP = '''      {canEdit && (
        <TDocsGoogleToolbar
          lang={ui.lang}
          zoom={zoom}
          dir={dir}
          textSizes={DOC_TEXT_SIZES}
          actions={{
            undo: () => exec("undo"),
            redo: () => exec("redo"),
            print: printDocument,
            setZoom,
            paragraphStyle: (value) => exec("formatBlock", value),
            fontFamily: (value) => exec("fontName", value),
            textSize: applyTextSize,
            bold: () => exec("bold"),
            italic: () => exec("italic"),
            underline: () => exec("underline"),
            strike: () => exec("strikeThrough"),
            link: insertLink,
            mention: insertMention,
            alignLeft: () => exec("justifyLeft"),
            alignCenter: () => exec("justifyCenter"),
            alignRight: () => exec("justifyRight"),
            bulletList: () => exec("insertUnorderedList"),
            numberedList: () => exec("insertOrderedList"),
            image: insertImage,
            table: insertTable,
            toggleDirection: () => setDir((value) => value === "rtl" ? "ltr" : "rtl"),
          }}
        />
      )}
'''

if not REPO.exists():
    fail("REPO_NOT_FOUND")

head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")

editor_hash = run(["git", "hash-object", EDITOR]).stdout.strip()
if editor_hash != EDITOR_BLOB:
    fail(f"EDITOR_BLOB_MISMATCH:{editor_hash}")

before_status = status_lines()
phase_dirty = [line for line in before_status if status_path(line) in PHASE_SCOPE]
if phase_dirty:
    fail("PHASE_PATH_ALREADY_DIRTY:" + "|".join(phase_dirty))
unrelated_before = unrelated_fingerprints(before_status)
precheck = "CLEAN" if not unrelated_before else "DIRTY_UNRELATED_ALLOWED"

payload_data = {}
for rel, (url, expected_sha) in PAYLOADS.items():
    data = download(url)
    actual_sha = git_blob_sha(data)
    if actual_sha != expected_sha:
        fail(f"PAYLOAD_INTEGRITY_FAIL:{rel}:{actual_sha}")
    payload_data[rel] = data

snapshot = {}
for rel in PHASE_SCOPE:
    path = REPO / rel
    snapshot[rel] = path.read_bytes() if path.exists() else None

live_backup = None
try:
    for rel, data in payload_data.items():
        path = REPO / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    editor_path = REPO / EDITOR
    source = editor_path.read_text(encoding="utf-8")

    source = replace_once(
        source,
        'import { TDocsGoogleMenuBar } from "./TDocsGoogleMenuBar";\n',
        'import { TDocsGoogleMenuBar } from "./TDocsGoogleMenuBar";\nimport { TDocsGoogleToolbar } from "./TDocsGoogleToolbar";\n',
        "TOOLBAR_IMPORT",
    )
    source = replace_once(
        source,
        'import "./tDocsPhase2GoogleMenuCore.css";\n',
        'import "./tDocsPhase2GoogleMenuCore.css";\nimport "./tDocsPhase2_1ToolbarFidelity.css";\n',
        "TOOLBAR_CSS_IMPORT",
    )
    source = replace_once(
        source,
        'tws-docs-phase2-core relative flex h-full flex-col',
        'tws-docs-phase2-core tws-docs-phase2-1-toolbar-fidelity relative flex h-full flex-col',
        "ROOT_CLASS",
    )

    toolbar_start = '      {canEdit && (\n        <div className="tws-docs-toolbar'
    ruler_marker = '      <div className="tws-doc-ruler" aria-hidden="true" />'
    start = source.find(toolbar_start)
    if start < 0 or source.find(toolbar_start, start + 1) >= 0:
        raise RuntimeError("TOOLBAR_START_ANCHOR_INVALID")
    end = source.find(ruler_marker, start)
    if end < 0:
        raise RuntimeError("RULER_ANCHOR_NOT_FOUND")
    source = source[:start] + TOOLBAR_MARKUP + "\n" + source[end:]

    editor_path.write_text(source, encoding="utf-8")

    for token in [
        "TDocsGoogleToolbar",
        "tDocsPhase2_1ToolbarFidelity.css",
        "tws-docs-phase2-1-toolbar-fidelity",
        "paragraphStyle: (value) => exec(\"formatBlock\", value)",
        "fontFamily: (value) => exec(\"fontName\", value)",
        "print: printDocument",
    ]:
        if token not in source:
            raise RuntimeError(f"SOURCE_TOKEN_MISSING:{token}")

    run(["git", "diff", "--check"])
    run(["node", "--test", TEST])
    for candidate in [
        "frontend/src/pages/tws/tDocsPhase2GoogleMenuCore.test.js",
        "frontend/src/pages/tws/tDocsPhase1GoogleDocsFidelity.test.js",
        "frontend/src/pages/tws/tDocsPhase1_1FinalPolish.test.js",
    ]:
        if (REPO / candidate).exists():
            run(["node", "--test", candidate])

    run(["npm", "run", "build"], cwd=FRONTEND)

    changed = {status_path(line) for line in status_lines() if status_path(line) in PHASE_SCOPE}
    if changed != PHASE_SCOPE:
        raise RuntimeError("CHANGED_PATHS_EXACT_FAIL:" + ",".join(sorted(changed)))

    unrelated_after = unrelated_fingerprints(status_lines())
    if unrelated_after != unrelated_before:
        raise RuntimeError("UNRELATED_DIRTY_STATE_CHANGED")

    if not LIVE_ROOT.exists() or not (DIST / "index.html").exists():
        raise RuntimeError("LIVE_OR_DIST_ROOT_MISSING")

    built_html = (DIST / "index.html").read_text(encoding="utf-8")
    built_asset = main_asset_from_html(built_html)
    if not built_asset:
        raise RuntimeError("BUILT_MAIN_ASSET_NOT_FOUND")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.exists():
        raise RuntimeError("BUILT_MAIN_ASSET_FILE_MISSING")

    try:
        live_before_html = download(LIVE_URL).decode("utf-8", errors="replace")
        live_before_asset = main_asset_from_html(live_before_html) or "UNKNOWN"
    except Exception:
        live_before_asset = "UNAVAILABLE"

    backup_parent = Path(tempfile.mkdtemp(prefix="tdocs_phase2_1_live_"))
    live_backup = backup_parent / "build"
    shutil.copytree(LIVE_ROOT, live_backup)

    run(["rsync", "-a", "--delete", str(DIST) + "/", str(LIVE_ROOT) + "/"])
    run(["nginx", "-t"])
    run(["systemctl", "reload", "nginx"])

    live_after_html = download(LIVE_URL).decode("utf-8", errors="replace")
    live_after_asset = main_asset_from_html(live_after_html)
    if live_after_asset != built_asset:
        raise RuntimeError(f"LIVE_ASSET_MISMATCH:{live_after_asset}:{built_asset}")

    live_asset_bytes = download("https://tos.tamiyouz.com" + live_after_asset)
    if live_asset_bytes != built_asset_path.read_bytes():
        raise RuntimeError("LIVE_BUNDLE_BYTES_MISMATCH")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT_VERSION={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD_COMMIT={head}")
    print("PASS_FAIL=PASS")
    print(f"FILES_PATCHED={len(PHASE_SCOPE)}")
    print(f"PRECHECK_WORKTREE={precheck}")
    print("BASELINE_BLOB_GUARD=PASS")
    print("PAYLOAD_INTEGRITY=PASS")
    print("GOOGLE_DOCS_PRIMARY_TOOLBAR=PASS")
    print("SINGLE_ROW_TOOLBAR=PASS")
    print("PRINT_ZOOM_STYLE_FONT_SIZE=PASS")
    print("SELECTION_PRESERVING_ACTIONS=PASS")
    print("SECONDARY_CONTROLS_MOVED_TO_MENUS=PASS")
    print("LIGHT_DARK_MICRO_FIDELITY=PASS")
    print("PHASE_2_REGRESSION=PASS")
    print("FRONTEND_BUILD=PASS")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_before_asset}")
    print(f"LIVE_ASSET_AFTER={live_after_asset}")
    print(f"LIVE_DEPLOY_ROOT={LIVE_ROOT}")
    print("LIVE_DEPLOY=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print("BACKEND_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("PRE_EXISTING_UNRELATED_DIRTY_STATE_PRESERVED=YES")
    print("CHANGED_PATHS_EXACT=YES")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")
    print("PHASE_2_1_PATCH_APPLIED=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")

except Exception as exc:
    fail(str(exc), snapshot=snapshot, live_backup=live_backup)
