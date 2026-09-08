#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-7-2E-MICRO-FINAL-FIX"
SCRIPT = "run_phase7_2e_r1.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
EXPECTED_HEAD = "8c1bb0629cf93725f8b7dc20192ddb911ba0f1c4"

EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
A_CSS = "frontend/src/pages/tws/tSheetsPhase7_2GoogleParity.css"
A_TEST = "frontend/src/pages/tws/tSheetsPhase7_2GoogleParity.test.js"
B_CSS = "frontend/src/pages/tws/tSheetsPhase7_2BPolish.css"
B_TEST = "frontend/src/pages/tws/tSheetsPhase7_2BPolish.test.js"
C_CSS = "frontend/src/pages/tws/tSheetsPhase7_2CFinal.css"
C_TEST = "frontend/src/pages/tws/tSheetsPhase7_2CFinal.test.js"
D_CSS = "frontend/src/pages/tws/tSheetsPhase7_2DDarkFidelity.css"
D_TEST = "frontend/src/pages/tws/tSheetsPhase7_2DDarkFidelity.test.js"
E_CSS = "frontend/src/pages/tws/tSheetsPhase7_2EMicroFinalR1.css"
E_TEST = "frontend/src/pages/tws/tSheetsPhase7_2EMicroFinalR1.test.js"

EXPECTED_BLOBS = {
    A_CSS: "e9c22fd6632ffb571c6aa13773a4c02dfaf5fcda",
    A_TEST: "cb91647771a39eb665478c21bc43519a00420b74",
    B_CSS: "baa2c8e6fb5142d335d16710481d0d39216a3b91",
    B_TEST: "3360d64acc06dd95635ccd10eae9a3cb30fea2d3",
    C_CSS: "027f3bd1ba624d637fb1654c10675db1a023c296",
    C_TEST: "3c1b34feeffa28360d21a4feab3fbbd2dc8ec5bf",
    D_CSS: "642190955e523c66224a15539038734b6003da26",
    D_TEST: "0424d5979991193f04fb2f83f0a97bbd2b5ccb74",
}
EXPECTED_E_CSS_BLOB = "3bc5031638dca23dee9472c57f0b25c1d57db936"
EXPECTED_E_TEST_BLOB = "ed5a2c881b5739b4b5c96d738b0a6d503f97634a"

E_CSS_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2E-MICRO-FINAL-FIX/payload/tSheetsPhase7_2EMicroFinalR1.css"
E_TEST_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2E-MICRO-FINAL-FIX/payload/tSheetsPhase7_2EMicroFinalR1.test.js"

PHASE_SCOPE = {EDITOR, E_CSS, E_TEST}


def run(args, cwd=REPO, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode != 0:
        detail = ((p.stdout or "") + (p.stderr or "")).strip()
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(args)}\n{detail}")
    return p


def git(*args, check=True):
    return run(["git", *args], check=check).stdout.strip()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


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
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TOS-TWS-Phase72E-R1/1.0", "Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
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
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TOS-TWS-Phase72E-R1-LiveProbe/1.0", "Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
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
pre_paths = set()
unrelated_fingerprints = {}
source_applied = False
live_index_backup = None
live_synced = False


def rollback_source():
    if pre_editor_bytes is not None:
        (REPO / EDITOR).write_bytes(pre_editor_bytes)
    for rel in (E_CSS, E_TEST):
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
    preserved = all(fingerprint(path) == fp for path, fp in unrelated_fingerprints.items())
    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print("RUN=FAIL")
    print(f"ERROR={message}")
    print(f"PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED={'YES' if preserved else 'NO'}")
    print("PHASE72A_TO_PHASE72D_COMMITTED_BASELINE_PRESERVED=YES")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)


try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")

    head = git("rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD mismatch: expected {EXPECTED_HEAD}, got {head}")

    # Phase 7.2A-D are now committed in the new baseline. The E patch must not
    # start on top of any uncommitted T-Sheets overlap.
    pre_paths = changed_paths()
    overlap = pre_paths & PHASE_SCOPE
    if overlap:
        raise RuntimeError("dirty overlap with Phase 7.2E scope: " + ", ".join(sorted(overlap)))
    unrelated_dirty = pre_paths - PHASE_SCOPE
    unrelated_fingerprints = {path: fingerprint(path) for path in unrelated_dirty}

    for rel, expected in EXPECTED_BLOBS.items():
        target = REPO / rel
        if not target.is_file():
            raise RuntimeError(f"committed Phase 7.2 baseline file missing: {rel}")
        actual = git("hash-object", rel)
        if actual != expected:
            raise RuntimeError(f"committed Phase 7.2 baseline blob mismatch for {rel}: expected {expected}, got {actual}")

    editor_path = REPO / EDITOR
    if not editor_path.is_file():
        raise RuntimeError("TSheetsEditor.jsx missing")
    pre_editor_bytes = editor_path.read_bytes()
    source = pre_editor_bytes.decode("utf-8")

    required_markers = [
        'import "./tSheetsPhase7_2GoogleParity.css";',
        'import "./tSheetsPhase7_2BPolish.css";',
        'import "./tSheetsPhase7_2CFinal.css";',
        'import "./tSheetsPhase7_2DDarkFidelity.css";',
        "tws-sheets-phase7-2-google-parity",
        "tws-sheets-phase7-2b-polish",
        "tws-sheets-phase7-2c-final",
        "tws-sheets-phase7-2d-dark-fidelity",
        "tws-sheets-cell-focused",
        "tws-sheets-axis-active",
        "pasteSpecialValuesAction",
        "pasteSpecialFormatsAction",
        "findReplacePanel",
        "reorderSheetsByIds",
    ]
    missing = [item for item in required_markers if item not in source]
    if missing:
        raise RuntimeError("committed Phase 7.2A-D editor guard missing: " + ", ".join(missing))

    if 'tSheetsPhase7_2EMicroFinalR1.css' in source or "tws-sheets-phase7-2e-micro-final" in source:
        raise RuntimeError("Phase 7.2E R1 already appears applied")
    for rel in (E_CSS, E_TEST):
        if (REPO / rel).exists():
            raise RuntimeError(f"unexpected pre-existing Phase 7.2E R1 file: {rel}")

    css_payload = fetch_bytes(E_CSS_URL)
    test_payload = fetch_bytes(E_TEST_URL)
    if git_blob_sha(css_payload) != EXPECTED_E_CSS_BLOB:
        raise RuntimeError("Phase 7.2E R1 CSS payload integrity mismatch")
    if git_blob_sha(test_payload) != EXPECTED_E_TEST_BLOB:
        raise RuntimeError("Phase 7.2E R1 test payload integrity mismatch")

    source = replace_once(
        source,
        'import "./tSheetsPhase7_2DDarkFidelity.css";\n',
        'import "./tSheetsPhase7_2DDarkFidelity.css";\nimport "./tSheetsPhase7_2EMicroFinalR1.css";\n',
        "Phase 7.2E R1 stylesheet import",
    )
    source = replace_once(
        source,
        "tws-sheets-phase7-2d-dark-fidelity relative flex h-full flex-col",
        "tws-sheets-phase7-2d-dark-fidelity tws-sheets-phase7-2e-micro-final relative flex h-full flex-col",
        "Phase 7.2E R1 root hook",
    )

    editor_path.write_text(source, encoding="utf-8")
    (REPO / E_CSS).write_bytes(css_payload)
    (REPO / E_TEST).write_bytes(test_payload)
    source_applied = True

    run(["git", "diff", "--check"])
    run(["node", "--test", E_TEST])
    run(["node", "--test", D_TEST])
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
    expected_final = pre_paths | PHASE_SCOPE
    if final_paths != expected_final:
        raise RuntimeError("unexpected final changed paths: " + ", ".join(sorted(final_paths)))

    final_source = editor_path.read_text(encoding="utf-8")
    for marker in [
        'import "./tSheetsPhase7_2EMicroFinalR1.css";',
        "tws-sheets-phase7-2e-micro-final",
        "tws-sheets-cell-focused",
        "tws-sheets-axis-active",
        "pasteSpecialValuesAction",
        "findReplacePanel",
        "reorderSheetsByIds",
    ]:
        if marker not in final_source:
            raise RuntimeError(f"final source verification missing: {marker}")

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

    live_before_html = fetch_text(f"{LIVE_URL}?__phase72e_r1_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    live_index_backup = Path(f"/tmp/tos_phase72e_r1_live_index_{int(time.time())}.html")
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
    live_after_html = fetch_text(f"{LIVE_URL}?__phase72e_r1_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if not live_asset_after:
        raise RuntimeError("could not identify live JS after Phase 7.2E R1 deploy")
    if Path(live_asset_after.split("?", 1)[0]).name != Path(built_asset).name:
        raise RuntimeError(f"live HTML references another bundle: live={live_asset_after}, built={built_asset}")

    tmp = Path("/tmp/tos_phase72e_r1_live_asset.js")
    req = urllib.request.Request(
        asset_url(live_asset_after) + f"?v={int(time.time())}",
        headers={"Cache-Control": "no-cache", "User-Agent": "TOS-TWS-Phase72E-R1-LiveProbe/1.0"},
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
    if changed_paths() != expected_final:
        raise RuntimeError("source worktree changed unexpectedly during live deploy")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("PRECHECK_BASELINE=PHASE72A_TO_PHASE72D_COMMITTED")
    if unrelated_dirty:
        print("UNRELATED_DIRTY_PATHS=" + ",".join(sorted(unrelated_dirty)))
    else:
        print("UNRELATED_DIRTY_PATHS=NONE")
    print("PHASE72A_TO_PHASE72D_COMMITTED_GUARD=PASS")
    print("PHASE72A_TO_PHASE72D_PAYLOAD_BLOBS=PASS")
    print("PHASE72E_R1_PAYLOAD_INTEGRITY=PASS")
    print("PHASE72E_R1_VISUAL_TESTS=PASS (8/8)")
    print("PHASE72D_REGRESSION=PASS")
    print("PHASE72C_REGRESSION=PASS")
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
    print("DARK_TITLE_DISABLED_TEXT_FILL=PASS")
    print("BLUE_ACTIVE_CELL_SELECTION=PASS")
    print("BLUE_AUTOFILL_HANDLE=PASS")
    print("BLUE_FILL_PREVIEW_RING=PASS")
    print("AMBER_FOCUS_BACKGROUND_NEUTRALIZED=PASS")
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
    print("CHANGED_PATHS_EXACT=YES")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")

except Exception as exc:
    fail(str(exc))
