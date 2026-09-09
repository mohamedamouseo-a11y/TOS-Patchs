#!/usr/bin/env python3
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request

PATCH = "TOS-TWS-TSHEETS-PHASE-7-4-GOOGLE-WORKSPACE-FIDELITY"
SCRIPT = "run_tsheets_phase7_4.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "b514d21ed3715e1d7545a2f009e0ce72634dbcb3"

EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
CSS = "frontend/src/pages/tws/tSheetsPhase7_4WorkspaceFidelity.css"
TEST = "frontend/src/pages/tws/tSheetsPhase7_4WorkspaceFidelity.test.js"
PHASE_SCOPE = {EDITOR, CSS, TEST}
EDITOR_BLOB = "ad3e1c5f22285d7aac3ceba9aac3e1c8486c67b3"

PAYLOAD_ROOT = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSHEETS-PHASE-7-4-GOOGLE-WORKSPACE-FIDELITY/payload"
PAYLOADS = {
    CSS: (f"{PAYLOAD_ROOT}/tSheetsPhase7_4WorkspaceFidelity.css", "0ac0dcc56897acfd10298d3361e0ea66b7cc7413"),
    TEST: (f"{PAYLOAD_ROOT}/tSheetsPhase7_4WorkspaceFidelity.test.js", "2a89d36a27ff65b11dbf3ee965306e28199b5486"),
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
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-tsheets-phase7-4-runner"})
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
    marker = "/assets/index-"
    start = html.find(marker)
    if start < 0:
        return None
    end = html.find(".js", start)
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
        'import "./tSheetsPhase7_3GoogleMenu.css";\n',
        'import "./tSheetsPhase7_3GoogleMenu.css";\nimport "./tSheetsPhase7_4WorkspaceFidelity.css";\n',
        "CSS_IMPORT",
    )
    source = replace_once(
        source,
        '<div className="tws-reference-ui tws-reference-sheets flex h-full flex-col">',
        '<div className="tws-reference-ui tws-reference-sheets tws-sheets-phase7-4-workspace-fidelity flex h-full flex-col">',
        "ROOT_CLASS",
    )

    editor_path.write_text(source, encoding="utf-8")

    for token in [
        'import "./tSheetsPhase7_4WorkspaceFidelity.css";',
        "tws-sheets-phase7-4-workspace-fidelity",
        "tws-sheets-toolbar-compact",
        "tws-sheets-formula-strip-compact",
        "tws-sheets-grid",
        "tws-sheets-tabs",
    ]:
        if token not in source:
            raise RuntimeError(f"SOURCE_TOKEN_MISSING:{token}")

    run(["git", "diff", "--check"])
    run(["node", "--test", TEST])

    phase73_test = "frontend/src/pages/tws/tSheetsPhase7_3GoogleMenu.test.js"
    if (REPO / phase73_test).exists():
        run(["node", "--test", phase73_test])

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

    backup_parent = Path(tempfile.mkdtemp(prefix="tsheets_phase7_4_live_"))
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
    print("GOOGLE_SHEETS_WORKSPACE_FIDELITY=PASS")
    print("SINGLE_ROW_TOOLBAR=PASS")
    print("NAME_BOX_FORMULA_BAR=PASS")
    print("GRID_HEADER_FIDELITY=PASS")
    print("GREEN_SELECTION_FIDELITY=PASS")
    print("SHEET_TABS_FIDELITY=PASS")
    print("LIGHT_DARK_FIDELITY=PASS")
    print("PHASE_7_3_REGRESSION=PASS")
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
    print("PHASE_7_4_PATCH_APPLIED=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")

except Exception as exc:
    fail(str(exc), snapshot=snapshot, live_backup=live_backup)
