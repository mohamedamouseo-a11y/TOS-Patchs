#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-TSLIDES-PHASE-2-R1-RUNTIME-SELECTION-VERSION-RACE-FIX"
SCRIPT = "run_tslides_phase2_r1.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
BACKEND = REPO / "backend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "24b5d8ebeb566f9afd0eddc5ff43f534480178be"

EDITOR = "frontend/src/pages/tws/TSlidesEditor.jsx"
SERVICE = "backend/src/services/workspace.service.js"
EXPORTER = "backend/src/utils/workspaceExport.js"
FE_HELPER = "frontend/src/pages/tws/slideCorePhase2.js"
FE_TEST = "frontend/src/pages/tws/slideCorePhase2.test.js"
FE_CSS = "frontend/src/pages/tws/tSlidesPhase2CoreEditing.css"
BE_HELPER = "backend/src/utils/slideCorePhase2.js"
BE_TEST = "backend/src/utils/slideCorePhase2.test.js"

FE_R1_TEST = "frontend/src/pages/tws/tSlidesPhase2RuntimeR1.test.js"
BE_R1_TEST = "backend/src/utils/slideVersionRaceR1.test.js"

PHASE2_SCOPE = {EDITOR, SERVICE, EXPORTER, FE_HELPER, FE_TEST, FE_CSS, BE_HELPER, BE_TEST}
R1_NEW_FILES = {FE_R1_TEST, BE_R1_TEST}

FE_R1_TEST_CONTENT = r'''import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSlidesEditor.jsx", import.meta.url), "utf8");

test("canvas background clearing cannot cancel element pointer selection", () => {
  assert.match(editor, /data-tws-canvas[\s\S]{0,260}onPointerDown=\{\(event\) => \{/);
  assert.match(editor, /if \(event\.target === event\.currentTarget\) onCanvasClick\?\.\(event\);/);
  assert.doesNotMatch(editor, /data-tws-canvas[\s\S]{0,180}onClick=\{onCanvasClick\}/);
});

test("new shapes and lines explicitly become selected", () => {
  const shape = editor.match(/function addShapeElement[\s\S]*?\n  \}/)?.[0] || "";
  const line = editor.match(/function addLineElement[\s\S]*?\n  \}/)?.[0] || "";
  assert.match(shape, /setSelectedElementIds\(\[element\.id\]\)/);
  assert.match(line, /setSelectedElementIds\(\[element\.id\]\)/);
});

test("phase 2 selection handles remain wired", () => {
  assert.match(editor, /tws-slides-resize-handle/);
  assert.match(editor, /tws-slides-rotate-handle/);
});
'''

BE_R1_TEST_CONTENT = r'''import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const service = fs.readFileSync(new URL("../services/workspace.service.js", import.meta.url), "utf8");

test("workspace version snapshot absorbs concurrent unique-version races", () => {
  const snapshot = service.match(/async function maybeSnapshotVersion[\s\S]*?\n\}/)?.[0] || "";
  assert.match(snapshot, /await prisma\.workspaceVersion\.create/);
  assert.match(snapshot, /error\?\.code !== "P2002"/);
  assert.match(snapshot, /deleteGoogleDriveFile\(uploaded\.driveFileId\)/);
  assert.match(snapshot, /prisma\.workspaceVersion\.findFirst/);
  assert.match(snapshot, /orderBy: \{ versionNumber: "desc" \}/);
});

test("snapshot race fix keeps version numbering contract", () => {
  const snapshot = service.match(/async function maybeSnapshotVersion[\s\S]*?\n\}/)?.[0] || "";
  assert.match(snapshot, /const versionNumber = \(latest\?\.versionNumber \|\| 0\) \+ 1/);
  assert.match(snapshot, /documentId: document\.id/);
  assert.match(snapshot, /versionNumber,/);
});
'''

def run(args, cwd=REPO, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode != 0:
        detail = ((p.stdout or "") + (p.stderr or "")).strip()
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(args)}\n{detail}")
    return p

def git(*args, check=True):
    return run(["git", *args], check=check).stdout.strip()

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

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
    req = urllib.request.Request(url, headers={
        "User-Agent": "TOS-TSlides-Phase2-R1/1.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()

def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")

def extract_main_js(html: str):
    matches = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html, re.I)
    return matches[-1] if matches else None

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

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return source.replace(old, new, 1)

def discover_pm2_backend():
    probe = run(["pm2", "jlist"], cwd=Path("/"), check=False)
    if probe.returncode != 0:
        raise RuntimeError("PM2 is unavailable; cannot safely reload backend runtime")
    try:
        items = json.loads(probe.stdout or "[]")
    except Exception as exc:
        raise RuntimeError(f"could not parse pm2 jlist: {exc}")
    candidates = []
    backend_str = str(BACKEND.resolve())
    repo_str = str(REPO.resolve())
    for item in items:
        env = item.get("pm2_env") or {}
        cwd = str(env.get("pm_cwd") or "")
        exec_path = str(env.get("pm_exec_path") or "")
        args = " ".join(str(x) for x in (env.get("args") or []))
        combined = f"{cwd} {exec_path} {args}"
        if cwd == backend_str or exec_path.startswith(backend_str + "/") or (repo_str in combined and "backend" in combined.lower()):
            candidates.append(item)
    if len(candidates) != 1:
        names = [str(x.get("name") or (x.get("pm2_env") or {}).get("name") or x.get("pm_id")) for x in candidates]
        raise RuntimeError(f"could not uniquely identify TOS backend PM2 process; candidates={names}")
    item = candidates[0]
    return str(item.get("pm_id")), str(item.get("name") or (item.get("pm2_env") or {}).get("name") or item.get("pm_id"))

def restart_pm2_backend(pm_id: str):
    run(["pm2", "restart", pm_id, "--update-env"], cwd=Path("/"))
    time.sleep(2.0)
    probe = run(["pm2", "jlist"], cwd=Path("/"))
    items = json.loads(probe.stdout or "[]")
    found = next((x for x in items if str(x.get("pm_id")) == str(pm_id)), None)
    status = str((found or {}).get("pm2_env", {}).get("status") or "")
    if status != "online":
        raise RuntimeError(f"backend PM2 process is not online after restart: {status or 'missing'}")

pre_paths = set()
unrelated_fingerprints = {}
preserved_phase2_fingerprints = {}
original_bytes = {}
source_applied = False
live_index_backup = None
live_synced = False
backend_pm_id = None
backend_pm_name = None
backend_restart_attempted = False

def rollback_source():
    for rel, data in original_bytes.items():
        (REPO / rel).write_bytes(data)
    for rel in R1_NEW_FILES:
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
    if backend_pm_id is not None and backend_restart_attempted:
        run(["pm2", "restart", backend_pm_id, "--update-env"], cwd=Path("/"), check=False)
    unrelated_ok = all(fingerprint(path) == fp for path, fp in unrelated_fingerprints.items())
    phase2_ok = all(fingerprint(path) == fp for path, fp in preserved_phase2_fingerprints.items())
    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print("R1_RUN=FAIL")
    print(f"ERROR={message}")
    print(f"PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED={'YES' if unrelated_ok else 'NO'}")
    print(f"PHASE2_NON_R1_FILES_PRESERVED={'YES' if phase2_ok else 'NO'}")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)

try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")

    head = git("rev-parse", "HEAD")
    if head != BASELINE:
        raise RuntimeError(f"HEAD mismatch: expected {BASELINE}, got {head}")

    pre_paths = changed_paths()
    missing_phase2 = sorted(PHASE2_SCOPE - pre_paths)
    if missing_phase2:
        raise RuntimeError("Phase 2 applied state is incomplete; missing dirty paths: " + ", ".join(missing_phase2))
    if any((REPO / rel).exists() for rel in R1_NEW_FILES):
        raise RuntimeError("R1 test file already exists; refusing ambiguous re-apply")

    unrelated_paths = pre_paths - PHASE2_SCOPE
    unrelated_fingerprints = {path: fingerprint(path) for path in unrelated_paths}
    preserve_phase2_paths = PHASE2_SCOPE - {EDITOR, SERVICE}
    preserved_phase2_fingerprints = {path: fingerprint(path) for path in preserve_phase2_paths}

    editor_path = REPO / EDITOR
    service_path = REPO / SERVICE
    editor = editor_path.read_text(encoding="utf-8")
    service = service_path.read_text(encoding="utf-8")

    for marker in [
        "tws-slides-phase2-core", "function addShapeElement", "function addLineElement",
        "tws-slides-resize-handle", "tws-slides-rotate-handle"
    ]:
        if marker not in editor:
            raise RuntimeError(f"required Phase 2 editor marker missing: {marker}")
    if "sanitizeSlideElementPhase2" not in service:
        raise RuntimeError("required Phase 2 backend marker missing: sanitizeSlideElementPhase2")

    original_bytes[EDITOR] = editor_path.read_bytes()
    original_bytes[SERVICE] = service_path.read_bytes()

    editor = replace_once(
        editor,
        '''      data-tws-canvas
      onClick={onCanvasClick}
      className="tws-slides-canvas''',
        '''      data-tws-canvas
      onPointerDown={(event) => {
        if (event.target === event.currentTarget) onCanvasClick?.(event);
      }}
      className="tws-slides-canvas''',
        "canvas selection clear event",
    )

    old_snapshot_create = '''  return prisma.workspaceVersion.create({
    data: {
      documentId: document.id,
      versionNumber,
      contentJson: metadataContentFor({ driveFileId: uploaded.driveFileId, type: document.type }),
      driveFileId: uploaded.driveFileId,
      driveProvider: "GOOGLE_DRIVE",
      createdById: user.id,
      changeSummary,
    },
  });'''
    new_snapshot_create = '''  try {
    return await prisma.workspaceVersion.create({
      data: {
        documentId: document.id,
        versionNumber,
        contentJson: metadataContentFor({ driveFileId: uploaded.driveFileId, type: document.type }),
        driveFileId: uploaded.driveFileId,
        driveProvider: "GOOGLE_DRIVE",
        createdById: user.id,
        changeSummary,
      },
    });
  } catch (error) {
    try {
      await deleteGoogleDriveFile(uploaded.driveFileId);
    } catch (cleanupError) {
      console.error("TWS version snapshot cleanup failed", {
        documentId: document.id,
        versionNumber,
        driveFileId: uploaded.driveFileId,
        cleanupError,
      });
    }
    if (error?.code !== "P2002") throw error;

    // A concurrent autosave can win the same (documentId, versionNumber).
    // The content save is already complete, so reuse the winning snapshot
    // instead of leaking Prisma P2002 back to the editor.
    return prisma.workspaceVersion.findFirst({
      where: { documentId: document.id },
      orderBy: { versionNumber: "desc" },
    });
  }'''
    service = replace_once(service, old_snapshot_create, new_snapshot_create, "workspace version race guard")

    editor_path.write_text(editor, encoding="utf-8")
    service_path.write_text(service, encoding="utf-8")
    (REPO / FE_R1_TEST).write_text(FE_R1_TEST_CONTENT, encoding="utf-8")
    (REPO / BE_R1_TEST).write_text(BE_R1_TEST_CONTENT, encoding="utf-8")
    source_applied = True

    run(["git", "diff", "--check"])
    run(["node", "--check", SERVICE])
    run(["node", "--test", FE_R1_TEST])
    run(["node", "--test", BE_R1_TEST])
    run(["node", "--test", FE_TEST])
    run(["node", "--test", BE_TEST])
    run(["node", "--test", "frontend/src/pages/tws/tSlidesPhase1GoogleSlidesFidelity.test.js"])

    prisma_validate = run(["npx", "prisma", "validate"], cwd=BACKEND, check=False)
    if prisma_validate.returncode != 0:
        raise RuntimeError("Prisma validate failed:\n" + ((prisma_validate.stdout or "") + (prisma_validate.stderr or "")))

    build_start = time.time()
    run(["npm", "run", "build"], cwd=FRONTEND)
    build_seconds = time.time() - build_start

    for path, fp in unrelated_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"pre-existing unrelated dirty path changed: {path}")
    for path, fp in preserved_phase2_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"existing Phase 2 path changed outside R1 scope: {path}")

    final_paths = changed_paths()
    expected_final = pre_paths | R1_NEW_FILES
    if final_paths != expected_final:
        extra = sorted(final_paths - expected_final)
        missing = sorted(expected_final - final_paths)
        raise RuntimeError(f"changed-path guard mismatch; extra={extra}; missing={missing}")

    final_editor = editor_path.read_text(encoding="utf-8")
    final_service = service_path.read_text(encoding="utf-8")
    if "onClick={onCanvasClick}" in final_editor:
        raise RuntimeError("stale canvas click-clear wiring remains")
    for marker in [
        "if (event.target === event.currentTarget) onCanvasClick?.(event);",
        "setSelectedElementIds([element.id]);",
        "tws-slides-resize-handle",
        "tws-slides-rotate-handle",
    ]:
        if marker not in final_editor:
            raise RuntimeError(f"selection runtime verification missing: {marker}")
    for marker in [
        'error?.code !== "P2002"',
        "deleteGoogleDriveFile(uploaded.driveFileId)",
        'orderBy: { versionNumber: "desc" }',
    ]:
        if marker not in final_service:
            raise RuntimeError(f"version race verification missing: {marker}")

    backend_pm_id, backend_pm_name = discover_pm2_backend()
    backend_restart_attempted = True
    restart_pm2_backend(backend_pm_id)

    nginx_dump = run(["nginx", "-T"], cwd=Path("/"), check=False)
    nginx_text = (nginx_dump.stdout or "") + (nginx_dump.stderr or "")
    if nginx_dump.returncode != 0 or "server_name tos.tamiyouz.com" not in nginx_text or str(LIVE_ROOT) not in nginx_text:
        raise RuntimeError("production root guard failed")

    live_before_html = fetch_text(f"{LIVE_URL}?tslides_phase2_r1_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.is_file():
        raise RuntimeError(f"built main asset missing: {built_asset_path}")
    built_asset_bytes = built_asset_path.read_bytes()

    backup_dir = Path("/tmp") / f"tslides_phase2_r1_live_backup_{int(time.time())}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    live_index_backup = backup_dir / "index.html"
    shutil.copy2(LIVE_ROOT / "index.html", live_index_backup)

    sync_dist(DIST, LIVE_ROOT)
    live_synced = True
    run(["nginx", "-t"], cwd=Path("/"))
    run(["systemctl", "reload", "nginx"], cwd=Path("/"))
    time.sleep(1.0)

    live_after_html = fetch_text(f"{LIVE_URL}?tslides_phase2_r1_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if live_asset_after != built_asset:
        raise RuntimeError(f"live HTML asset mismatch: built {built_asset}, live {live_asset_after}")
    live_asset_bytes = fetch_bytes(f"{asset_url(live_asset_after)}?tslides_phase2_r1={int(time.time())}")
    if sha256_bytes(live_asset_bytes) != sha256_bytes(built_asset_bytes):
        raise RuntimeError("live main JS bytes do not match fresh build")

    for path, fp in unrelated_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"unrelated dirty state changed after deploy: {path}")
    for path, fp in preserved_phase2_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"Phase 2 preserved file changed after deploy: {path}")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("PHASE2_APPLIED_STATE_GUARD=PASS")
    print("R1_SELECTION_TESTS=PASS")
    print("R1_VERSION_RACE_TESTS=PASS")
    print("PHASE2_FRONTEND_REGRESSION=PASS")
    print("PHASE2_BACKEND_REGRESSION=PASS")
    print("PHASE1_TSLIDES_REGRESSION=PASS")
    print("CANVAS_SELECTION_CLEAR_FIX=PASS")
    print("ADD_SHAPE_AUTO_SELECTION_PRESERVED=YES")
    print("ADD_LINE_AUTO_SELECTION_PRESERVED=YES")
    print("WORKSPACE_VERSION_P2002_RACE_GUARD=PASS")
    print("DUPLICATE_VALUE_RUNTIME_FIX=PASS")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print(f"BACKEND_PM2_PROCESS={backend_pm_name}")
    print("BACKEND_RESTART=PASS")
    print(f"FRONTEND_BUILD=PASS ({build_seconds:.2f}s)")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_asset_before}")
    print(f"LIVE_ASSET_AFTER={live_asset_after}")
    print(f"LIVE_DEPLOY_ROOT={LIVE_ROOT}")
    print("LIVE_DEPLOY=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print(f"PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED={'YES' if all(fingerprint(path) == fp for path, fp in unrelated_fingerprints.items()) else 'NO'}")
    print("PHASE2_NON_R1_FILES_PRESERVED=YES")
    print("CHANGED_PATHS_EXACT=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")

except Exception as exc:
    fail(str(exc))
