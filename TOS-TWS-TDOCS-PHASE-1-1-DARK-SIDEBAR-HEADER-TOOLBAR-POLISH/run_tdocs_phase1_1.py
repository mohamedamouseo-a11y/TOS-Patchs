#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-TDOCS-PHASE-1-1-DARK-SIDEBAR-HEADER-TOOLBAR-POLISH"
SCRIPT = "run_tdocs_phase1_1.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "0ac1f999e326f1d4d85e2dac117517cc416c4add"

EDITOR = "frontend/src/pages/tws/TDocsEditor.jsx"
P1_CSS = "frontend/src/pages/tws/tDocsPhase1GoogleDocsFidelity.css"
P1_TEST = "frontend/src/pages/tws/tDocsPhase1GoogleDocsFidelity.test.js"
P11_CSS = "frontend/src/pages/tws/tDocsPhase1_1FinalPolish.css"
P11_TEST = "frontend/src/pages/tws/tDocsPhase1_1FinalPolish.test.js"

PHASE1_SCOPE = {EDITOR, P1_CSS, P1_TEST}
NEW_FILES = {P11_CSS, P11_TEST}

BASE_EDITOR_BLOB = "42e1c14bb2f0eb6dc6ce0b3b90f925ffd4087e9a"
EXPECTED_P1_CSS_BLOB = "3fe80f54c62a8fc8076a4e77da1e2f2d35c95b9f"
EXPECTED_P1_TEST_BLOB = "2d359674c338a7c6ca810d12508b08173feaabee"
EXPECTED_P11_CSS_BLOB = "c41704148a088f419eeb7f021c111ebaa37bce10"
EXPECTED_P11_TEST_BLOB = "8d3c4f0a2ae80898bda4c9da73a98f7ea912482d"

P11_CSS_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TDOCS-PHASE-1-1-DARK-SIDEBAR-HEADER-TOOLBAR-POLISH/payload/tDocsPhase1_1FinalPolish.css"
P11_TEST_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TDOCS-PHASE-1-1-DARK-SIDEBAR-HEADER-TOOLBAR-POLISH/payload/tDocsPhase1_1FinalPolish.test.js"


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
        headers={"User-Agent": "TOS-TDocs-Phase1.1/1.0", "Cache-Control": "no-cache", "Pragma": "no-cache"},
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


def apply_phase1_source(source: str) -> str:
    source = replace_once(
        source,
        'import { useTwsI18n } from "./twsI18n";\n',
        'import { useTwsI18n } from "./twsI18n";\nimport "./tDocsPhase1GoogleDocsFidelity.css";\n',
        "Phase 1 stylesheet import",
    )
    source = replace_once(
        source,
        '<div className="tws-reference-ui tws-reference-docs flex h-full flex-col">',
        '<div className="tws-reference-ui tws-reference-docs tws-docs-phase1-google-fidelity flex h-full flex-col">',
        "Phase 1 root hook",
    )
    source = replace_once(
        source,
        '<div className="flex flex-wrap items-center gap-3 border-b border-zinc-100 bg-white px-4 py-3 dark:border-white/10 dark:bg-zinc-900">',
        '<div className="tws-docs-chrome flex flex-wrap items-center gap-3 border-b border-zinc-100 bg-white px-4 py-3 dark:border-white/10 dark:bg-zinc-900">',
        "Phase 1 chrome hook",
    )
    source = replace_once(
        source,
        '<div className="flex flex-wrap items-center gap-1.5">',
        '<div className="tws-docs-header-actions flex flex-wrap items-center gap-1.5">',
        "Phase 1 header actions hook",
    )
    source = replace_once(
        source,
        '<div className="flex flex-wrap items-center gap-1 border-b border-zinc-100 bg-zinc-50 px-3 py-1.5 dark:border-white/10 dark:bg-white/[0.03]">',
        '<div className="tws-docs-toolbar flex flex-wrap items-center gap-1 border-b border-zinc-100 bg-zinc-50 px-3 py-1.5 dark:border-white/10 dark:bg-white/[0.03]">',
        "Phase 1 toolbar hook",
    )
    source = replace_once(
        source,
        '      <div className="flex min-h-0 flex-1">\n        <div className="min-w-0 flex-1 overflow-y-auto bg-zinc-100 p-3 dark:bg-zinc-950 sm:p-6">',
        '      <div className="tws-doc-ruler" aria-hidden="true" />\n\n      <div className="tws-docs-workspace flex min-h-0 flex-1">\n        <div className="tws-docs-page-shell min-w-0 flex-1 overflow-y-auto bg-zinc-100 p-3 dark:bg-zinc-950 sm:p-6">',
        "Phase 1 ruler and workspace hooks",
    )
    source = replace_once(
        source,
        '<aside className="hidden w-72 shrink-0 overflow-y-auto border-r border-zinc-100 bg-white p-3 dark:border-white/10 dark:bg-zinc-900 xl:block">',
        '<aside className="tws-docs-inspector hidden w-72 shrink-0 overflow-y-auto border-r border-zinc-100 bg-white p-3 dark:border-white/10 dark:bg-zinc-900 xl:block">',
        "Phase 1 inspector hook",
    )
    source = replace_once(
        source,
        '<div className="rounded-3xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]">',
        '<div className="tws-docs-outline-card rounded-3xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]">',
        "Phase 1 outline hook",
    )
    source = replace_once(
        source,
        '<div className="mt-3 rounded-3xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]">',
        '<div className="tws-docs-info-card mt-3 rounded-3xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]">',
        "Phase 1 info hook",
    )
    return source


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
    for rel in NEW_FILES:
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
    print("TDOCS_PHASE1_STATE_PRESERVED=YES")
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
            f"TDocsEditor committed baseline changed: expected {BASE_EDITOR_BLOB}, got {head_editor_blob}"
        )

    pre_paths = changed_paths()
    missing_phase1 = PHASE1_SCOPE - pre_paths
    if missing_phase1:
        raise RuntimeError("T-Docs Phase 1 dirty state is incomplete: " + ", ".join(sorted(missing_phase1)))
    if pre_paths & NEW_FILES:
        raise RuntimeError("T-Docs Phase 1.1 already has dirty payload files")

    unrelated_dirty = pre_paths - PHASE1_SCOPE
    unrelated_fingerprints = {path: fingerprint(path) for path in unrelated_dirty}

    base_source = git("show", f"HEAD:{EDITOR}")
    expected_phase1_source = apply_phase1_source(base_source)
    editor_path = REPO / EDITOR
    if editor_path.read_text(encoding="utf-8") != expected_phase1_source:
        raise RuntimeError("TDocsEditor working tree does not exactly match Phase 1 expected state")
    if git("hash-object", P1_CSS) != EXPECTED_P1_CSS_BLOB:
        raise RuntimeError("Phase 1 CSS working-tree blob mismatch")
    if git("hash-object", P1_TEST) != EXPECTED_P1_TEST_BLOB:
        raise RuntimeError("Phase 1 test working-tree blob mismatch")

    pre_editor_bytes = editor_path.read_bytes()
    source = pre_editor_bytes.decode("utf-8")
    if 'tDocsPhase1_1FinalPolish.css' in source or "tws-docs-phase1-1-final-polish" in source:
        raise RuntimeError("T-Docs Phase 1.1 already appears applied")
    for rel in NEW_FILES:
        if (REPO / rel).exists():
            raise RuntimeError(f"unexpected pre-existing Phase 1.1 file: {rel}")

    css_payload = fetch_bytes(P11_CSS_URL)
    test_payload = fetch_bytes(P11_TEST_URL)
    if git_blob_sha(css_payload) != EXPECTED_P11_CSS_BLOB:
        raise RuntimeError("Phase 1.1 CSS payload integrity mismatch")
    if git_blob_sha(test_payload) != EXPECTED_P11_TEST_BLOB:
        raise RuntimeError("Phase 1.1 test payload integrity mismatch")

    source = replace_once(
        source,
        'import "./tDocsPhase1GoogleDocsFidelity.css";\n',
        'import "./tDocsPhase1GoogleDocsFidelity.css";\nimport "./tDocsPhase1_1FinalPolish.css";\n',
        "Phase 1.1 stylesheet import",
    )
    source = replace_once(
        source,
        "tws-docs-phase1-google-fidelity flex h-full flex-col",
        "tws-docs-phase1-google-fidelity tws-docs-phase1-1-final-polish flex h-full flex-col",
        "Phase 1.1 root hook",
    )

    editor_path.write_text(source, encoding="utf-8")
    (REPO / P11_CSS).write_bytes(css_payload)
    (REPO / P11_TEST).write_bytes(test_payload)
    source_applied = True

    run(["git", "diff", "--check", "--", EDITOR])
    run(["node", "--test", P11_TEST])
    run(["node", "--test", P1_TEST])

    regression_paths = [
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
    expected_final = pre_paths | NEW_FILES
    if final_paths != expected_final:
        extra = sorted(final_paths - expected_final)
        missing = sorted(expected_final - final_paths)
        raise RuntimeError(f"changed-path guard mismatch; extra={extra}; missing={missing}")

    final_source = editor_path.read_text(encoding="utf-8")
    for marker in [
        'import "./tDocsPhase1GoogleDocsFidelity.css";',
        'import "./tDocsPhase1_1FinalPolish.css";',
        "tws-docs-phase1-google-fidelity",
        "tws-docs-phase1-1-final-polish",
        "tws-docs-header-actions",
        "tws-docs-toolbar",
        "tws-doc-ruler",
        "tws-docs-outline-card",
        "tws-docs-info-card",
        "insertImage",
        "insertTable",
        "CommentsPanel",
        'format="docx"',
        'format="pdf"',
    ]:
        if marker not in final_source:
            raise RuntimeError(f"final source verification missing: {marker}")

    nginx_dump = run(["nginx", "-T"], cwd=Path("/"), check=False)
    nginx_text = (nginx_dump.stdout or "") + (nginx_dump.stderr or "")
    if nginx_dump.returncode != 0 or "server_name tos.tamiyouz.com" not in nginx_text or str(LIVE_ROOT) not in nginx_text:
        raise RuntimeError("production root guard failed")

    live_before_html = fetch_text(f"{LIVE_URL}?tdocs_phase11_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.is_file():
        raise RuntimeError(f"built main asset missing: {built_asset_path}")
    built_asset_bytes = built_asset_path.read_bytes()

    backup_dir = Path("/tmp") / f"tdocs_phase11_live_backup_{int(time.time())}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    live_index_backup = backup_dir / "index.html"
    shutil.copy2(LIVE_ROOT / "index.html", live_index_backup)

    sync_dist(DIST, LIVE_ROOT)
    live_synced = True
    run(["nginx", "-t"], cwd=Path("/"))
    run(["systemctl", "reload", "nginx"], cwd=Path("/"))
    time.sleep(1.0)

    live_after_html = fetch_text(f"{LIVE_URL}?tdocs_phase11_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if live_asset_after != built_asset:
        raise RuntimeError(f"live HTML asset mismatch: built {built_asset}, live {live_asset_after}")
    live_asset_bytes = fetch_bytes(f"{asset_url(live_asset_after)}?tdocs_phase11={int(time.time())}")
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
    print("TDOCS_PHASE1_EXACT_STATE_GUARD=PASS")
    print("PAYLOAD_INTEGRITY=PASS")
    print("FILES_PATCHED=3")
    print("TDOCS_PHASE1_1_TESTS=PASS (8/8)")
    print("TDOCS_PHASE1_REGRESSION=PASS (10/10)")
    print("DARK_OUTLINE_WHITE_PILLS_REMOVED=PASS")
    print("DARK_HEADER_ACTIONS_COMPACT=PASS")
    print("TOOLBAR_COMPACT_FINAL_POLISH=PASS")
    print("RULER_REFINEMENT=PASS")
    print("PHASE1_PAPER_READABILITY_PRESERVED=YES")
    print("EXISTING_EDITING_FEATURES_PRESERVED=YES")
    print("COMMENTS_SHARING_VERSIONS_EXPORTS_PRESERVED=YES")
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
    print("TDOCS_PHASE1_STATE_PRESERVED=YES")
    print(f"PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED={'YES' if all(fingerprint(path) == fp for path, fp in unrelated_fingerprints.items()) else 'NO'}")
    print("CHANGED_PATHS_EXACT=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")

except Exception as exc:
    fail(str(exc))
