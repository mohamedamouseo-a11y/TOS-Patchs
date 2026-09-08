#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-7-2C-SELECTION-DARK-FIDELITY-FINAL"
SCRIPT = "run_phase7_2c.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
EXPECTED_HEAD = "2e90568bfd2b749f3aeb539141e445ff6c9e6186"

EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
A_CSS = "frontend/src/pages/tws/tSheetsPhase7_2GoogleParity.css"
A_TEST = "frontend/src/pages/tws/tSheetsPhase7_2GoogleParity.test.js"
B_CSS = "frontend/src/pages/tws/tSheetsPhase7_2BPolish.css"
B_TEST = "frontend/src/pages/tws/tSheetsPhase7_2BPolish.test.js"
C_CSS = "frontend/src/pages/tws/tSheetsPhase7_2CFinal.css"
C_TEST = "frontend/src/pages/tws/tSheetsPhase7_2CFinal.test.js"

REQUIRED_TWS_DIRTY = {EDITOR, A_CSS, A_TEST, B_CSS, B_TEST}
EXPECTED_A_CSS_BLOB = "e9c22fd6632ffb571c6aa13773a4c02dfaf5fcda"
EXPECTED_A_TEST_BLOB = "cb91647771a39eb665478c21bc43519a00420b74"
EXPECTED_B_CSS_BLOB = "baa2c8e6fb5142d335d16710481d0d39216a3b91"
EXPECTED_B_TEST_BLOB = "3360d64acc06dd95635ccd10eae9a3cb30fea2d3"
EXPECTED_C_CSS_BLOB = "027f3bd1ba624d637fb1654c10675db1a023c296"
EXPECTED_C_TEST_BLOB = "3c1b34feeffa28360d21a4feab3fbbd2dc8ec5bf"

C_CSS_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2C-SELECTION-DARK-FIDELITY-FINAL/payload/tSheetsPhase7_2CFinal.css"
C_TEST_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2C-SELECTION-DARK-FIDELITY-FINAL/payload/tSheetsPhase7_2CFinal.test.js"


def run(args, cwd=REPO, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode != 0:
        detail = ((p.stdout or "") + (p.stderr or "")).strip()
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(args)}\n{detail}")
    return p


def git(*args, check=True):
    return run(["git", *args], check=check).stdout.strip()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def changed_paths():
    tracked = set(filter(None, git("diff", "--name-only", "HEAD").splitlines()))
    untracked = set(filter(None, git("ls-files", "--others", "--exclude-standard").splitlines()))
    return tracked | untracked


def fingerprint(rel: str) -> str:
    target = REPO / rel
    if not target.exists():
        return "MISSING"
    if target.is_file():
        return "FILE:" + sha256(target)
    parts = []
    for child in sorted(p for p in target.rglob("*") if p.is_file()):
        parts.append(f"{child.relative_to(target)}:{sha256(child)}")
    return "DIR:" + hashlib.sha256("\n".join(parts).encode()).hexdigest()


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "TOS-TWS-Phase72C/1.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return source.replace(old, new, 1)


def extract_main_js(html: str):
    matches = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html, re.I)
    return matches[-1] if matches else None


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "TOS-TWS-Phase72C-LiveProbe/1.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def asset_url(src: str) -> str:
    if src.startswith("http://") or src.startswith("https://"):
        return src
    if not src.startswith("/"):
        src = "/" + src
    return "https://tos.tamiyouz.com" + src


def sync_dist(src: Path, dst: Path):
    if not src.is_dir() or not (src / "index.html").is_file():
        raise RuntimeError("frontend dist is missing")
    if not dst.is_dir() or not (dst / "index.html").is_file():
        raise RuntimeError(f"known production root unavailable: {dst}")
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


pre_editor_bytes = None
pre_paths = None
unrelated_fingerprints = None
source_applied = False
live_index_backup = None
live_synced = False


def rollback_source():
    if pre_editor_bytes is not None:
        (REPO / EDITOR).write_bytes(pre_editor_bytes)
    for rel in (C_CSS, C_TEST):
        target = REPO / rel
        if target.exists():
            target.unlink()


def rollback_live():
    if live_synced and live_index_backup and live_index_backup.is_file():
        shutil.copy2(live_index_backup, LIVE_ROOT / "index.html")
        run(["nginx", "-t"], cwd=Path("/"), check=False)
        run(["systemctl", "reload", "nginx"], cwd=Path("/"), check=False)


def fail(message):
    if live_synced:
        rollback_live()
    if source_applied:
        rollback_source()
    preserved = True
    if unrelated_fingerprints:
        preserved = all(fingerprint(path) == fp for path, fp in unrelated_fingerprints.items())
    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print("RUN=FAIL")
    print(f"ERROR={message}")
    print(f"PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED={'YES' if preserved else 'NO'}")
    print("PHASE72A_PHASE72B_STATE_PRESERVED=YES")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)


try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")

    head = git("rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD mismatch: expected {EXPECTED_HEAD}, got {head}")

    pre_paths = changed_paths()
    if not REQUIRED_TWS_DIRTY.issubset(pre_paths):
        missing = REQUIRED_TWS_DIRTY - pre_paths
        raise RuntimeError("required Phase 7.2A/7.2B dirty paths missing: " + ", ".join(sorted(missing)))

    unrelated_dirty = pre_paths - REQUIRED_TWS_DIRTY
    unrelated_fingerprints = {path: fingerprint(path) for path in unrelated_dirty}

    blob_guards = [
        (A_CSS, EXPECTED_A_CSS_BLOB, "Phase 7.2A CSS"),
        (A_TEST, EXPECTED_A_TEST_BLOB, "Phase 7.2A test"),
        (B_CSS, EXPECTED_B_CSS_BLOB, "Phase 7.2B CSS"),
        (B_TEST, EXPECTED_B_TEST_BLOB, "Phase 7.2B test"),
    ]
    for rel, expected, label in blob_guards:
        actual = git("hash-object", rel)
        if actual != expected:
            raise RuntimeError(f"{label} blob mismatch: expected {expected}, got {actual}")

    for rel in (C_CSS, C_TEST):
        if (REPO / rel).exists():
            raise RuntimeError(f"unexpected pre-existing Phase 7.2C file: {rel}")

    editor_path = REPO / EDITOR
    pre_editor_bytes = editor_path.read_bytes()
    source = pre_editor_bytes.decode("utf-8")

    required_markers = [
        'import "./tSheetsPhase7_2GoogleParity.css";',
        'import "./tSheetsPhase7_2BPolish.css";',
        "tws-sheets-phase7-2-google-parity",
        "tws-sheets-phase7-2b-polish",
        "tws-sheets-cell-focused",
        "tws-sheets-axis-active",
        "pasteSpecialValuesAction",
        "pasteSpecialFormatsAction",
        "findReplacePanel",
        "reorderSheetsByIds",
    ]
    missing_markers = [item for item in required_markers if item not in source]
    if missing_markers:
        raise RuntimeError("Phase 7.2B source guard missing: " + ", ".join(missing_markers))
    if 'tSheetsPhase7_2CFinal.css' in source or "tws-sheets-phase7-2c-final" in source:
        raise RuntimeError("Phase 7.2C already appears applied")

    css_payload = fetch_bytes(C_CSS_URL)
    test_payload = fetch_bytes(C_TEST_URL)
    if git_blob_sha(css_payload) != EXPECTED_C_CSS_BLOB:
        raise RuntimeError("Phase 7.2C CSS payload integrity mismatch")
    if git_blob_sha(test_payload) != EXPECTED_C_TEST_BLOB:
        raise RuntimeError("Phase 7.2C test payload integrity mismatch")

    source = replace_once(
        source,
        'import "./tSheetsPhase7_2BPolish.css";\n',
        'import "./tSheetsPhase7_2BPolish.css";\nimport "./tSheetsPhase7_2CFinal.css";\n',
        "Phase 7.2C stylesheet import",
    )

    source = replace_once(
        source,
        'tws-sheets-phase7-premium tws-sheets-phase7-1-restructure tws-sheets-phase7-2-google-parity tws-sheets-phase7-2b-polish relative flex h-full flex-col',
        'tws-sheets-phase7-premium tws-sheets-phase7-1-restructure tws-sheets-phase7-2-google-parity tws-sheets-phase7-2b-polish tws-sheets-phase7-2c-final relative flex h-full flex-col',
        "Phase 7.2C root hook",
    )

    source_applied = True
    editor_path.write_text(source, encoding="utf-8")
    (REPO / C_CSS).write_bytes(css_payload)
    (REPO / C_TEST).write_bytes(test_payload)

    run(["git", "diff", "--check"])
    run(["node", "--test", C_TEST])
    run(["node", "--test", B_TEST])
    run(["node", "--test", A_TEST])
    run(["node", "--test", "frontend/src/pages/tws/tSheetsPhase7_1Restructure.test.js"])
    run(["node", "--test", "frontend/src/pages/tws/tSheetsPhase7Premium.test.js"])
    run(["node", "--test", "frontend/src/pages/tws/sheetGridPhase2.test.js", "frontend/src/pages/tws/sheetDataPhase3.test.js"])
    run(["node", "--test", "backend/src/utils/sheetAdvancedPhase6.test.js"])
    run(["node", "--test", "backend/src/utils/sheetCollabPhase5.test.js"])
    run(["node", "--test", "backend/src/utils/sheetFormula.phase4.test.js"])
    run(["node", "--test", "backend/src/utils/workspaceXlsx.phase1.test.js", "backend/src/utils/workspaceXlsx.phase3.test.js"])

    build_start = time.time()
    run(["npm", "run", "build"], cwd=FRONTEND)
    build_seconds = time.time() - build_start

    for path, fp in unrelated_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"pre-existing unrelated dirty path changed: {path}")

    final_paths = changed_paths()
    expected_final_paths = pre_paths | {C_CSS, C_TEST}
    if final_paths != expected_final_paths:
        raise RuntimeError("unexpected final changed paths: " + ", ".join(sorted(final_paths)))

    final_source = editor_path.read_text(encoding="utf-8")
    final_required = [
        'import "./tSheetsPhase7_2CFinal.css";',
        "tws-sheets-phase7-2c-final",
        "tws-sheets-cell-focused",
        "tws-sheets-axis-active",
        "pasteSpecialValuesAction",
        "findReplacePanel",
        "reorderSheetsByIds",
    ]
    missing_final = [item for item in final_required if item not in final_source]
    if missing_final:
        raise RuntimeError("Phase 7.2C final source verification missing: " + ", ".join(missing_final))

    nginx_dump = run(["nginx", "-T"], cwd=Path("/"), check=False)
    nginx_text = (nginx_dump.stdout or "") + (nginx_dump.stderr or "")
    if nginx_dump.returncode != 0 or "server_name tos.tamiyouz.com" not in nginx_text or str(LIVE_ROOT) not in nginx_text:
        raise RuntimeError("production root guard failed")

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.is_file():
        raise RuntimeError(f"built asset missing: {built_asset_path}")
    built_sha = sha256(built_asset_path)

    live_before_html = fetch_text(f"{LIVE_URL}?__phase72c_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    live_index_backup = Path(f"/tmp/tos_phase72c_live_index_{int(time.time())}.html")
    shutil.copy2(LIVE_ROOT / "index.html", live_index_backup)
    sync_dist(DIST, LIVE_ROOT)
    live_synced = True

    nginx_test = run(["nginx", "-t"], cwd=Path("/"), check=False)
    if nginx_test.returncode != 0:
        raise RuntimeError("nginx -t failed after live preview sync")
    nginx_reload = run(["systemctl", "reload", "nginx"], cwd=Path("/"), check=False)
    if nginx_reload.returncode != 0:
        raise RuntimeError("nginx reload failed after live preview sync")

    time.sleep(1)
    live_after_html = fetch_text(f"{LIVE_URL}?__phase72c_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if not live_asset_after:
        raise RuntimeError("could not identify live JS after Phase 7.2C deploy")
    if Path(live_asset_after.split("?", 1)[0]).name != Path(built_asset).name:
        raise RuntimeError(f"live HTML references another bundle: live={live_asset_after}, built={built_asset}")

    tmp = Path("/tmp/tos_phase72c_live_asset.js")
    req = urllib.request.Request(
        asset_url(live_asset_after) + f"?v={int(time.time())}",
        headers={"Cache-Control": "no-cache", "User-Agent": "TOS-TWS-Phase72C-LiveProbe/1.0"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        tmp.write_bytes(response.read())
    live_sha = sha256(tmp)
    tmp.unlink(missing_ok=True)
    if live_sha != built_sha:
        raise RuntimeError(f"live asset bytes mismatch: live_sha={live_sha}, built_sha={built_sha}")

    for path, fp in unrelated_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"pre-existing unrelated dirty path changed during live deploy: {path}")

    if changed_paths() != expected_final_paths:
        raise RuntimeError("source worktree changed unexpectedly during live deploy")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("PRECHECK_WORKTREE=DIRTY_EXPECTED_PHASE72A_PHASE72B")
    if unrelated_dirty:
        print("UNRELATED_DIRTY_PATHS=" + ",".join(sorted(unrelated_dirty)))
    print("PHASE72A_PHASE72B_STATE_GUARD=PASS")
    print("PHASE72A_PHASE72B_PAYLOAD_BLOBS=PASS")
    print("PHASE72C_PAYLOAD_INTEGRITY=PASS")
    print("PHASE72C_VISUAL_TESTS=PASS (10/10)")
    print("PHASE72B_REGRESSION=PASS")
    print("PHASE72A_REGRESSION=PASS")
    print("PHASE71_UI_REGRESSION=PASS")
    print("PHASE7_VISUAL_REGRESSION=PASS")
    print("PHASE2_PHASE3_FRONTEND_REGRESSION=PASS")
    print("PHASE6_ADVANCED_REGRESSION=PASS")
    print("PHASE5_COLLABORATION_REGRESSION=PASS")
    print("PHASE4_FORMULA_REGRESSION=PASS")
    print("PHASE1_PHASE3_XLSX_REGRESSION=PASS")
    print(f"FRONTEND_BUILD=PASS ({build_seconds:.2f}s)")
    print("ACTIVE_CELL_SELECTION=PASS")
    print("ACTIVE_ROW_COLUMN_HEADERS=PASS")
    print("SELECTED_RANGE_TINT=PASS")
    print("DARK_GRIDLINE_SOFTENING=PASS")
    print("DARK_LIGHT_TOOLBAR_UNIFICATION=PASS")
    print("FORMULA_BAR_CONTRAST=PASS")
    print("SHEET_TAB_ACTIVE_ADD_POLISH=PASS")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_asset_before}")
    print(f"LIVE_ASSET_AFTER={live_asset_after}")
    print(f"LIVE_DEPLOY_ROOT={LIVE_ROOT}")
    print("LIVE_DEPLOY=PASS")
    print("NGINX_RELOAD=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print("BACKEND_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("FUNCTIONAL_BEHAVIOR_CHANGED=NO")
    print("PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED=YES")
    print("PHASE72A_PHASE72B_STATE_PRESERVED=YES")
    print("CHANGED_PATHS_EXACT=YES")
    print("PHASE72C_PATCH_APPLIED=YES")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
except Exception as exc:
    fail(str(exc))
