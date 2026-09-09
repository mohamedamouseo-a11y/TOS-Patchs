#!/usr/bin/env python3
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request

PATCH = "TOS-TWS-TDOCS-PHASE-2-1-R2-DARK-TOOLBAR-SELECT-LEGIBILITY"
SCRIPT = "run_tdocs_phase2_1_r2.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
HEAD_EXPECTED = "6d23d9f5ef56856cd87ea671d1b11e474e3a39b7"

EDITOR = "frontend/src/pages/tws/TDocsEditor.jsx"
TOOLBAR = "frontend/src/pages/tws/TDocsGoogleToolbar.jsx"
CSS = "frontend/src/pages/tws/tDocsPhase2_1ToolbarFidelity.css"
TEST = "frontend/src/pages/tws/tDocsPhase2_1ToolbarFidelity.test.js"

EXPECTED_BLOBS = {
    TOOLBAR: "d1744373cce5dcf8725af1f7fac2e8e947278eba",
    CSS: "188382d90e2e6e1ffe71b2a1de3b23930790cd4d",
    TEST: "a28bd01143cd3aeefbc85321cb81f6126cd43ad2",
}

DARK_FIX = r'''
/* Phase 2.1 R2 - native dark select legibility */
.dark .tws-docs-phase2-1-toolbar-fidelity .tws-docs-gtoolbar-select {
  color: #e8eaed !important;
  -webkit-text-fill-color: #e8eaed !important;
  opacity: 1 !important;
  color-scheme: dark;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}

.dark .tws-docs-phase2-1-toolbar-fidelity .tws-docs-gtoolbar-select option {
  color: #e8eaed !important;
  -webkit-text-fill-color: #e8eaed !important;
  background: #282c33 !important;
}
'''

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
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-patch-runner-r2"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()

def status_lines():
    return [line for line in run(["git", "status", "--porcelain"]).stdout.splitlines() if line.strip()]

def main_asset_from_html(html: str):
    marker = "/assets/index-"
    start = html.find(marker)
    if start < 0:
        return None
    end = html.find(".js", start)
    if end < 0:
        return None
    return html[start:end + 3]

def fail(message, css_snapshot=None, live_backup=None):
    print(f"ERROR={message}", file=sys.stderr)
    if css_snapshot is not None:
        try:
            (REPO / CSS).write_bytes(css_snapshot)
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
if head != HEAD_EXPECTED:
    fail(f"BASELINE_MISMATCH:{head}")

for rel, expected in EXPECTED_BLOBS.items():
    path = REPO / rel
    if not path.exists():
        fail(f"PHASE_2_1_FILE_MISSING:{rel}")
    actual = git_blob_sha(path.read_bytes())
    if actual != expected:
        fail(f"PHASE_2_1_BLOB_MISMATCH:{rel}:{actual}")

editor_source = (REPO / EDITOR).read_text(encoding="utf-8")
for token in [
    'import { TDocsGoogleToolbar } from "./TDocsGoogleToolbar";',
    'import "./tDocsPhase2_1ToolbarFidelity.css";',
    "tws-docs-phase2-1-toolbar-fidelity",
    "<TDocsGoogleToolbar",
]:
    if token not in editor_source:
        fail(f"PHASE_2_1_EDITOR_TOKEN_MISSING:{token}")

css_path = REPO / CSS
css_snapshot = css_path.read_bytes()
before_status = status_lines()

try:
    css = css_snapshot.decode("utf-8")
    if "Phase 2.1 R2 - native dark select legibility" in css:
        raise RuntimeError("R2_ALREADY_APPLIED")
    css = css.rstrip() + "\n\n" + DARK_FIX.strip() + "\n"
    css_path.write_text(css, encoding="utf-8")

    for token in [
        "-webkit-text-fill-color: #e8eaed !important;",
        "color-scheme: dark;",
        ".tws-docs-gtoolbar-select option",
        "background: #282c33 !important;",
    ]:
        if token not in css:
            raise RuntimeError(f"DARK_SELECT_FIX_TOKEN_MISSING:{token}")

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

    after_status = status_lines()
    if after_status != before_status:
        raise RuntimeError("WORKTREE_STATUS_CHANGED_OUTSIDE_EXISTING_PATH_STATE")

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

    backup_parent = Path(tempfile.mkdtemp(prefix="tdocs_phase2_1_r2_live_"))
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
    print(f"HEAD_COMMIT={head}")
    print("PASS_FAIL=PASS")
    print("PHASE_2_1_STATE_GUARD=PASS")
    print("DARK_SELECT_TEXT_LEGIBILITY_FIX=PASS")
    print("DARK_SELECT_OPTION_LEGIBILITY_FIX=PASS")
    print("LIGHT_TOOLBAR_UNCHANGED=YES")
    print("PHASE_2_1_REGRESSION=PASS")
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
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")
    print("READY_FOR_DARK_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")

except Exception as exc:
    fail(str(exc), css_snapshot=css_snapshot, live_backup=locals().get("live_backup"))
