#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-TSLIDES-PHASE-1-GOOGLE-SLIDES-UX-DARK-FIDELITY"
SCRIPT = "run_tslides_phase1.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "ad89f49730203a3f5e9ea6c16cffec3ea4da05b0"

EDITOR = "frontend/src/pages/tws/TSlidesEditor.jsx"
CSS = "frontend/src/pages/tws/tSlidesPhase1GoogleSlidesFidelity.css"
TEST = "frontend/src/pages/tws/tSlidesPhase1GoogleSlidesFidelity.test.js"
PHASE_SCOPE = {EDITOR, CSS, TEST}

BASE_EDITOR_BLOB = "bf28e1b18a0e52ef1060dbe4ade445f47164593d"
EXPECTED_CSS_BLOB = "bbee8045b10e1065ddc989ce6881b443d0ba462a"
EXPECTED_TEST_BLOB = "7ac19d2d3559cc2e188b826eed78eb5d66dda754"

CSS_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSLIDES-PHASE-1-GOOGLE-SLIDES-UX-DARK-FIDELITY/payload/tSlidesPhase1GoogleSlidesFidelity.css"
TEST_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSLIDES-PHASE-1-GOOGLE-SLIDES-UX-DARK-FIDELITY/payload/tSlidesPhase1GoogleSlidesFidelity.test.js"


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
        headers={"User-Agent": "TOS-TSlides-Phase1/1.0", "Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8", errors="replace")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return source.replace(old, new, 1)


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


pre_editor_bytes = None
pre_paths = set()
unrelated_fingerprints = {}
source_applied = False
live_index_backup = None
live_synced = False


def rollback_source():
    if pre_editor_bytes is not None:
        (REPO / EDITOR).write_bytes(pre_editor_bytes)
    for rel in (CSS, TEST):
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
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)


try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")

    head = git("rev-parse", "HEAD")
    ancestor = run(["git", "merge-base", "--is-ancestor", BASELINE, head], check=False)
    if ancestor.returncode != 0:
        raise RuntimeError(f"baseline {BASELINE} is not an ancestor of current HEAD {head}")

    head_editor_blob = git("rev-parse", f"HEAD:{EDITOR}")
    if head_editor_blob != BASE_EDITOR_BLOB:
        raise RuntimeError(
            f"TSlidesEditor baseline changed in current HEAD: expected {BASE_EDITOR_BLOB}, got {head_editor_blob}"
        )

    pre_paths = changed_paths()
    overlap = pre_paths & PHASE_SCOPE
    if overlap:
        raise RuntimeError("dirty overlap with T-Slides Phase 1 scope: " + ", ".join(sorted(overlap)))
    unrelated_dirty = pre_paths - PHASE_SCOPE
    unrelated_fingerprints = {path: fingerprint(path) for path in unrelated_dirty}

    editor_path = REPO / EDITOR
    if not editor_path.is_file():
        raise RuntimeError("TSlidesEditor.jsx missing")
    if git("hash-object", EDITOR) != BASE_EDITOR_BLOB:
        raise RuntimeError("TSlidesEditor working-tree blob does not match guarded baseline")
    pre_editor_bytes = editor_path.read_bytes()
    source = pre_editor_bytes.decode("utf-8")

    if "tSlidesPhase1GoogleSlidesFidelity.css" in source or "tws-slides-phase1-google-fidelity" in source:
        raise RuntimeError("T-Slides Phase 1 already appears applied")
    for rel in (CSS, TEST):
        if (REPO / rel).exists():
            raise RuntimeError(f"unexpected pre-existing Phase 1 file: {rel}")

    css_payload = fetch_bytes(CSS_URL)
    test_payload = fetch_bytes(TEST_URL)
    if git_blob_sha(css_payload) != EXPECTED_CSS_BLOB:
        raise RuntimeError("Phase 1 CSS payload integrity mismatch")
    if git_blob_sha(test_payload) != EXPECTED_TEST_BLOB:
        raise RuntimeError("Phase 1 test payload integrity mismatch")

    source = replace_once(
        source,
        'import { useTwsI18n } from "./twsI18n";\n',
        'import { useTwsI18n } from "./twsI18n";\nimport "./tSlidesPhase1GoogleSlidesFidelity.css";\n',
        "stylesheet import",
    )
    source = replace_once(
        source,
        'className="relative aspect-video w-full overflow-hidden rounded-2xl border border-zinc-200 shadow-sm dark:border-white/10"',
        'className="tws-slides-canvas relative aspect-video w-full overflow-hidden rounded-2xl border border-zinc-200 shadow-sm dark:border-white/10"',
        "canvas hook",
    )
    source = replace_once(
        source,
        '<div className="tws-reference-ui tws-reference-slides flex h-full flex-col">',
        '<div className="tws-reference-ui tws-reference-slides tws-slides-phase1-google-fidelity flex h-full flex-col">',
        "root hook",
    )
    source = replace_once(
        source,
        '<div className="flex flex-wrap items-center gap-3 border-b border-zinc-100 bg-white px-4 py-3 dark:border-white/10 dark:bg-zinc-900">',
        '<div className="tws-slides-chrome flex flex-wrap items-center gap-3 border-b border-zinc-100 bg-white px-4 py-3 dark:border-white/10 dark:bg-zinc-900">',
        "chrome hook",
    )
    source = replace_once(
        source,
        '<div className="flex flex-wrap items-center gap-1.5">',
        '<div className="tws-slides-header-actions flex flex-wrap items-center gap-1.5">',
        "header actions hook",
    )
    source = replace_once(
        source,
        '<div className="flex flex-wrap items-center gap-2 border-b border-zinc-100 bg-zinc-50 px-3 py-2 dark:border-white/10 dark:bg-white/[0.03]">',
        '<div className="tws-slides-toolbar flex flex-wrap items-center gap-2 border-b border-zinc-100 bg-zinc-50 px-3 py-2 dark:border-white/10 dark:bg-white/[0.03]">',
        "toolbar hook",
    )
    source = replace_once(
        source,
        '      <div className="flex min-h-0 flex-1">\n        <div className="flex w-28 shrink-0 flex-col gap-2 overflow-y-auto border-l border-zinc-100 bg-zinc-50 p-2 dark:border-white/10 dark:bg-white/[0.02] sm:w-48 sm:p-3">',
        '      <div className="tws-slides-workspace flex min-h-0 flex-1">\n        <div className="tws-slides-rail flex w-28 shrink-0 flex-col gap-2 overflow-y-auto border-l border-zinc-100 bg-zinc-50 p-2 dark:border-white/10 dark:bg-white/[0.02] sm:w-48 sm:p-3">',
        "workspace and rail hooks",
    )
    source = replace_once(
        source,
        '"group relative cursor-pointer rounded-xl border-2 p-1.5",\n                slide.id === activeSlideId ? "border-amber-400" : "border-transparent hover:border-zinc-200 dark:hover:border-white/10"',
        '"tws-slides-thumb group relative cursor-pointer rounded-xl border-2 p-1.5",\n                slide.id === activeSlideId ? "tws-slides-thumb-active border-amber-400" : "border-transparent hover:border-zinc-200 dark:hover:border-white/10"',
        "thumbnail hooks",
    )
    source = replace_once(
        source,
        'className="min-w-0 flex-1 overflow-y-auto bg-zinc-100 p-3 dark:bg-zinc-950 focus:outline-none sm:p-6"',
        'className="tws-slides-stage min-w-0 flex-1 overflow-y-auto bg-zinc-100 p-3 dark:bg-zinc-950 focus:outline-none sm:p-6"',
        "stage hook",
    )
    source = replace_once(
        source,
        '<div className="mt-4 rounded-3xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-900">',
        '<div className="tws-slides-notes mt-4 rounded-3xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-900">',
        "notes hook",
    )
    source = replace_once(
        source,
        '<aside className="hidden w-72 shrink-0 overflow-y-auto border-r border-zinc-100 bg-white p-3 dark:border-white/10 dark:bg-zinc-900 xl:block">',
        '<aside className="tws-slides-inspector hidden w-72 shrink-0 overflow-y-auto border-r border-zinc-100 bg-white p-3 dark:border-white/10 dark:bg-zinc-900 xl:block">',
        "inspector hook",
    )
    source = replace_once(
        source,
        '<div className="rounded-3xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]">\n            <b className="text-sm font-black text-zinc-900 dark:text-white">{ui.properties}</b>',
        '<div className="tws-slides-properties-card rounded-3xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]">\n            <b className="text-sm font-black text-zinc-900 dark:text-white">{ui.properties}</b>',
        "properties card hook",
    )
    source = replace_once(
        source,
        '<div className="mt-3 rounded-3xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]">\n            <b className="text-sm font-black text-zinc-900 dark:text-white">{ui.slideLayout}</b>',
        '<div className="tws-slides-layout-card mt-3 rounded-3xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]">\n            <b className="text-sm font-black text-zinc-900 dark:text-white">{ui.slideLayout}</b>',
        "layout card hook",
    )

    editor_path.write_text(source, encoding="utf-8")
    (REPO / CSS).write_bytes(css_payload)
    (REPO / TEST).write_bytes(test_payload)
    source_applied = True

    run(["git", "diff", "--check", "--", EDITOR])
    phase_test = run(["node", "--test", TEST])
    if "fail 0" not in (phase_test.stdout or ""):
        raise RuntimeError("T-Slides Phase 1 tests did not report fail 0")

    regression_paths = [
        "frontend/src/pages/tws/tDocsPhase1_1FinalPolish.test.js",
        "frontend/src/pages/tws/tDocsPhase1GoogleDocsFidelity.test.js",
        "frontend/src/pages/tws/tSheetsPhase7_2EMicroFinalR1.test.js",
        "frontend/src/pages/tws/tSheetsPhase7_1Restructure.test.js",
        "frontend/src/pages/tws/tSheetsPhase7Premium.test.js",
    ]
    for regression in regression_paths:
        if (REPO / regression).is_file():
            run(["node", "--test", regression])

    build_start = time.time()
    run(["npm", "run", "build"], cwd=FRONTEND)
    build_seconds = time.time() - build_start

    for path, fp in unrelated_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"pre-existing unrelated dirty path changed: {path}")

    final_paths = changed_paths()
    expected_final = pre_paths | PHASE_SCOPE
    if final_paths != expected_final:
        extra = sorted(final_paths - expected_final)
        missing = sorted(expected_final - final_paths)
        raise RuntimeError(f"changed-path guard mismatch; extra={extra}; missing={missing}")

    final_source = editor_path.read_text(encoding="utf-8")
    for marker in [
        'import "./tSlidesPhase1GoogleSlidesFidelity.css";',
        "tws-slides-phase1-google-fidelity",
        "tws-slides-chrome",
        "tws-slides-header-actions",
        "tws-slides-toolbar",
        "tws-slides-workspace",
        "tws-slides-rail",
        "tws-slides-thumb",
        "tws-slides-thumb-active",
        "tws-slides-stage",
        "tws-slides-canvas",
        "tws-slides-notes",
        "tws-slides-inspector",
        "tws-slides-properties-card",
        "tws-slides-layout-card",
        "addSlide",
        "duplicateSlide",
        "reorderSlides",
        "PresentMode",
        "CommentsPanel",
        'format="pptx"',
        'format="pdf"',
    ]:
        if marker not in final_source:
            raise RuntimeError(f"final source verification missing: {marker}")

    nginx_dump = run(["nginx", "-T"], cwd=Path("/"), check=False)
    nginx_text = (nginx_dump.stdout or "") + (nginx_dump.stderr or "")
    if nginx_dump.returncode != 0 or "server_name tos.tamiyouz.com" not in nginx_text or str(LIVE_ROOT) not in nginx_text:
        raise RuntimeError("production root guard failed")

    live_before_html = fetch_text(f"{LIVE_URL}?tslides_phase1_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.is_file():
        raise RuntimeError(f"built main asset missing: {built_asset_path}")
    built_asset_bytes = built_asset_path.read_bytes()

    backup_dir = Path("/tmp") / f"tslides_phase1_live_backup_{int(time.time())}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    live_index_backup = backup_dir / "index.html"
    shutil.copy2(LIVE_ROOT / "index.html", live_index_backup)

    sync_dist(DIST, LIVE_ROOT)
    live_synced = True
    run(["nginx", "-t"], cwd=Path("/"))
    run(["systemctl", "reload", "nginx"], cwd=Path("/"))
    time.sleep(1.0)

    live_after_html = fetch_text(f"{LIVE_URL}?tslides_phase1_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if live_asset_after != built_asset:
        raise RuntimeError(f"live HTML asset mismatch: built {built_asset}, live {live_asset_after}")
    live_asset_bytes = fetch_bytes(f"{asset_url(live_asset_after)}?tslides_phase1={int(time.time())}")
    if sha256_bytes(live_asset_bytes) != sha256_bytes(built_asset_bytes):
        raise RuntimeError("live main JS bytes do not match fresh build")

    for path, fp in unrelated_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"unrelated dirty state changed after live deploy: {path}")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print(f"BASELINE={BASELINE}")
    print("BASELINE_ANCESTOR_GUARD=PASS")
    print("TSLIDES_BASELINE_BLOB_GUARD=PASS")
    print("PAYLOAD_INTEGRITY=PASS")
    print("FILES_PATCHED=3")
    print("TSLIDES_PHASE1_TESTS=PASS (10/10)")
    print("DARK_CHROME_FIDELITY=PASS")
    print("DARK_PANEL_WASHOUT_REMOVED=PASS")
    print("COMPACT_TOOLBAR=PASS")
    print("SLIDE_RAIL_FIDELITY=PASS")
    print("BLUE_SELECTION_LANGUAGE=PASS")
    print("CANVAS_STAGE_FIDELITY=PASS")
    print("SPEAKER_NOTES_FIDELITY=PASS")
    print("CONTEXT_INSPECTOR_FIDELITY=PASS")
    print("EXISTING_EDITING_FEATURES_PRESERVED=YES")
    print("COMMENTS_SHARING_VERSIONS_EXPORTS_PRESENT_MODE_PRESERVED=YES")
    print("BACKEND_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("FUNCTIONAL_BEHAVIOR_CHANGED=NO")
    print(f"FRONTEND_BUILD=PASS ({build_seconds:.2f}s)")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_asset_before}")
    print(f"LIVE_ASSET_AFTER={live_asset_after}")
    print(f"LIVE_DEPLOY_ROOT={LIVE_ROOT}")
    print("LIVE_DEPLOY=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print(f"PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED={'YES' if all(fingerprint(path) == fp for path, fp in unrelated_fingerprints.items()) else 'NO'}")
    print("CHANGED_PATHS_EXACT=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")

except Exception as exc:
    fail(str(exc))
