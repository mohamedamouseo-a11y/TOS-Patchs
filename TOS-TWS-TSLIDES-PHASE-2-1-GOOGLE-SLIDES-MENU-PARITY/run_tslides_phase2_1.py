#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-TSLIDES-PHASE-2-1-GOOGLE-SLIDES-MENU-PARITY"
SCRIPT = "run_tslides_phase2_1.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "6970a75f19e0d1faed20ba3dc86fd607905706be"

EDITOR = "frontend/src/pages/tws/TSlidesEditor.jsx"
MENU = "frontend/src/pages/tws/TSlidesGoogleMenuBar.jsx"
CSS = "frontend/src/pages/tws/tSlidesGoogleMenuPhase2_1.css"
TEST = "frontend/src/pages/tws/tSlidesGoogleMenuPhase2_1.test.js"
PHASE_SCOPE = {EDITOR, MENU, CSS, TEST}
EDITOR_BLOB = "79fab288c3638fbef411dd774d6ec5ab38a6b6a3"

ROOT = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSLIDES-PHASE-2-1-GOOGLE-SLIDES-MENU-PARITY/payload"
PAYLOADS = {
    MENU: (f"{ROOT}/TSlidesGoogleMenuBar.jsx", "3d9a075658c51d19bdffdabcaf370cca1f9169d9"),
    CSS: (f"{ROOT}/tSlidesGoogleMenuPhase2_1.css", "188e625ce0f6e0fc70e0a30a3e7a831a68151267"),
    TEST: (f"{ROOT}/tSlidesGoogleMenuPhase2_1.test.js", "78393daed728b21a239e49eb6cc7298773845c85"),
}


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
        "User-Agent": "TOS-TSlides-Phase2.1/1.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


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


pre_paths = set()
unrelated_fingerprints = {}
original_editor = None
source_applied = False
live_index_backup = None
live_synced = False


def rollback_source():
    if original_editor is not None:
        (REPO / EDITOR).write_bytes(original_editor)
    for rel in [MENU, CSS, TEST]:
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
    if head != BASELINE:
        raise RuntimeError(f"HEAD mismatch: expected {BASELINE}, got {head}")

    editor_blob = git("rev-parse", f"HEAD:{EDITOR}")
    if editor_blob != EDITOR_BLOB:
        raise RuntimeError(f"TSlides editor baseline blob mismatch: expected {EDITOR_BLOB}, got {editor_blob}")

    pre_paths = changed_paths()
    overlap = pre_paths & PHASE_SCOPE
    if overlap:
        raise RuntimeError("dirty overlap with Phase 2.1 scope: " + ", ".join(sorted(overlap)))
    unrelated_fingerprints = {path: fingerprint(path) for path in pre_paths}

    for rel in [MENU, CSS, TEST]:
        if (REPO / rel).exists():
            raise RuntimeError(f"unexpected pre-existing Phase 2.1 file: {rel}")

    payload_bytes = {}
    for rel, (url, expected_blob) in PAYLOADS.items():
        data = fetch_bytes(url)
        actual_blob = git_blob_sha(data)
        if actual_blob != expected_blob:
            raise RuntimeError(f"payload integrity mismatch for {rel}: expected {expected_blob}, got {actual_blob}")
        payload_bytes[rel] = data

    original_editor = (REPO / EDITOR).read_bytes()
    editor = original_editor.decode("utf-8")

    for required in [
        "tws-slides-phase2-core",
        "tSlidesPhase2CoreEditing.css",
        "tSlidesPhase2RuntimeR1.test.js",
        "createShapeElement",
        "createLineElement",
        "duplicateSelectedElements",
    ]:
        if required == "tSlidesPhase2RuntimeR1.test.js":
            if not (REPO / "frontend/src/pages/tws/tSlidesPhase2RuntimeR1.test.js").is_file():
                raise RuntimeError("Phase 2 R1 state missing")
        elif required not in editor:
            raise RuntimeError(f"required Phase 2 marker missing from editor: {required}")

    editor = replace_once(
        editor,
        'import "./tSlidesPhase2CoreEditing.css";\n',
        'import "./tSlidesPhase2CoreEditing.css";\n'
        'import { TSlidesGoogleMenuBar } from "./TSlidesGoogleMenuBar.jsx";\n'
        'import "./tSlidesGoogleMenuPhase2_1.css";\n',
        "Phase 2.1 menu imports",
    )

    helpers_anchor = '''  function updateSelectedElementStyle(key, value) {
    if (!selectedElementIds.length) return;
    const selected = new Set(selectedElementIds);
    mutateActiveSlide((slide) => ({
      ...slide,
      elements: slide.elements.map((item) => selected.has(item.id) ? { ...item, [key]: value } : item),
    }), `style:${key}:${Date.now()}`);
  }

'''
    helpers = helpers_anchor + '''  function cutSelectedElements() {
    if (!selectedElementIds.length) return;
    copySelectedElements();
    deleteSelectedElement();
  }

  function selectAllElements() {
    setSelectedElementIds((activeSlide?.elements || []).map((element) => element.id));
  }

  async function downloadSlides(format) {
    const safeFormat = format === "pdf" ? "pdf" : "pptx";
    try {
      await api.tws.downloadExport(documentId, safeFormat, `${title || "slides"}.${safeFormat}`);
    } catch (err) {
      setError(getErrorMessage(err, ui.lang === "en" ? "Export failed." : "تعذر إتمام التصدير."));
    }
  }

  function focusSlidesTitle() {
    const input = document.querySelector("[data-tws-slides-title]");
    input?.focus();
    input?.select?.();
  }

  function focusSpeakerNotes() {
    const notes = document.querySelector("[data-tws-slides-notes]");
    notes?.scrollIntoView?.({ behavior: "smooth", block: "center" });
    notes?.focus?.();
  }

  async function toggleSlidesFullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      setError(ui.lang === "en" ? "Fullscreen is unavailable in this browser." : "وضع ملء الشاشة غير متاح في هذا المتصفح.");
    }
  }

  function showSlidesKeyboardShortcuts() {
    window.alert([
      "T-Slides keyboard shortcuts",
      "Ctrl+Z Undo · Ctrl+Y Redo",
      "Ctrl+C Copy · Ctrl+V Paste · Ctrl+D Duplicate",
      "Ctrl+G Group · Ctrl+Shift+G Ungroup",
      "Delete Remove selected element",
      "Shift+Click Multi-select",
    ].join("\\n"));
  }

  function showSlidesHelp() {
    window.alert("T-Slides uses Google Slides-style menus. Choose a menu command to work with the presentation, current slide, or selected elements.");
  }

'''
    editor = replace_once(editor, helpers_anchor, helpers, "Phase 2.1 menu action helpers")

    editor = replace_once(
        editor,
        '<input value={title} onChange={handleTitleChange} disabled={!canEdit}',
        '<input data-tws-slides-title value={title} onChange={handleTitleChange} disabled={!canEdit}',
        "title focus hook",
    )

    editor = replace_once(
        editor,
        '''              <textarea
                value={activeSlide.notes || ""}
''',
        '''              <textarea
                data-tws-slides-notes
                value={activeSlide.notes || ""}
''',
        "speaker notes focus hook",
    )

    menu_block = '''      <TSlidesGoogleMenuBar
        canEdit={canEdit}
        canShare={access === "OWNER"}
        selectedCount={selectedElementIds.length}
        selectedType={selectedElement?.type || ""}
        slideCount={slides.length}
        activeSlideIndex={activeIndex}
        actions={{
          newSlide: () => addSlide(),
          rename: focusSlidesTitle,
          versionHistory: () => setShowVersions(true),
          share: () => setShowPermissions(true),
          downloadPptx: () => downloadSlides("pptx"),
          downloadPdf: () => downloadSlides("pdf"),
          print: () => window.print(),
          present: () => setPresenting(true),
          undo,
          redo,
          cut: cutSelectedElements,
          copy: copySelectedElements,
          paste: pasteSelectedElements,
          duplicate: duplicateSelectedElements,
          deleteSelection: deleteSelectedElement,
          selectAll: selectAllElements,
          fullscreen: toggleSlidesFullscreen,
          speakerNotes: focusSpeakerNotes,
          addText: addTextElement,
          addImage: addImageElement,
          addRectangle: () => addShapeElement("rect"),
          addEllipse: () => addShapeElement("ellipse"),
          addLine: () => addLineElement("line"),
          addArrow: () => addLineElement("arrow"),
          duplicateSlide: () => duplicateSlide(activeSlide.id),
          deleteSlide: () => deleteSlide(activeSlide.id),
          layoutTitle: () => applyLayoutToCurrentSlide("title"),
          layoutTitleContent: () => applyLayoutToCurrentSlide("titleContent"),
          layoutImageText: () => applyLayoutToCurrentSlide("imageText"),
          layoutTwoColumns: () => applyLayoutToCurrentSlide("twoColumns"),
          themeLight: () => applySlideTheme("light"),
          themeDark: () => applySlideTheme("dark"),
          themeBlue: () => applySlideTheme("blue"),
          themeGold: () => applySlideTheme("gold"),
          moveSlideUp: () => moveSlideBy(activeSlide.id, -1),
          moveSlideDown: () => moveSlideBy(activeSlide.id, 1),
          bold: () => updateSelectedElementStyle("bold", !Boolean(selectedElement?.bold)),
          opacity: (value) => updateSelectedElementStyle("opacity", value),
          rotateClockwise: () => rotateSelectedElements(15),
          rotateCounterclockwise: () => rotateSelectedElements(-15),
          bringToFront: () => reorderSelectedLayer("front"),
          sendToBack: () => reorderSelectedLayer("back"),
          alignLeft: () => alignSelectedElements("left"),
          alignCenter: () => alignSelectedElements("center"),
          alignRight: () => alignSelectedElements("right"),
          alignTop: () => alignSelectedElements("top"),
          alignMiddle: () => alignSelectedElements("middle"),
          alignBottom: () => alignSelectedElements("bottom"),
          distributeHorizontal: () => distributeSelectedElements("horizontal"),
          distributeVertical: () => distributeSelectedElements("vertical"),
          group: groupSelectedElements,
          ungroup: ungroupSelectedElements,
          comments: () => setShowComments(true),
          keyboardShortcuts: showSlidesKeyboardShortcuts,
          help: showSlidesHelp,
        }}
      />

'''
    editor = replace_once(
        editor,
        '      </div>\n\n      {!canEdit && <Notice type="warning" className="m-3">',
        '      </div>\n\n' + menu_block + '      {!canEdit && <Notice type="warning" className="m-3">',
        "Google Slides menu bar render",
    )

    (REPO / EDITOR).write_text(editor, encoding="utf-8")
    for rel, data in payload_bytes.items():
        target = REPO / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    source_applied = True

    run(["git", "diff", "--check"])
    run(["node", "--test", TEST])
    run(["node", "--test", "frontend/src/pages/tws/tSlidesPhase2RuntimeR1.test.js"])
    run(["node", "--test", "frontend/src/pages/tws/slideCorePhase2.test.js"])
    run(["node", "--test", "frontend/src/pages/tws/tSlidesPhase1GoogleSlidesFidelity.test.js"])

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

    final_editor = (REPO / EDITOR).read_text(encoding="utf-8")
    final_menu = (REPO / MENU).read_text(encoding="utf-8")
    for marker in [
        "TSlidesGoogleMenuBar",
        "tSlidesGoogleMenuPhase2_1.css",
        "data-tws-slides-title",
        "data-tws-slides-notes",
        "downloadSlides",
        "cutSelectedElements",
        "selectAllElements",
    ]:
        if marker not in final_editor:
            raise RuntimeError(f"final editor verification missing: {marker}")
    for label in ["File", "Edit", "View", "Insert", "Slide", "Format", "Arrange", "Tools", "Extensions", "Help"]:
        if f'"{label}"' not in final_menu:
            raise RuntimeError(f"menu verification missing: {label}")

    nginx_dump = run(["nginx", "-T"], cwd=Path("/"), check=False)
    nginx_text = (nginx_dump.stdout or "") + (nginx_dump.stderr or "")
    if nginx_dump.returncode != 0 or "server_name tos.tamiyouz.com" not in nginx_text or str(LIVE_ROOT) not in nginx_text:
        raise RuntimeError("production root guard failed")

    live_before_html = fetch_text(f"{LIVE_URL}?tslides_phase2_1_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.is_file():
        raise RuntimeError(f"built main asset missing: {built_asset_path}")
    built_asset_bytes = built_asset_path.read_bytes()

    backup_dir = Path("/tmp") / f"tslides_phase2_1_live_backup_{int(time.time())}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    live_index_backup = backup_dir / "index.html"
    shutil.copy2(LIVE_ROOT / "index.html", live_index_backup)

    sync_dist(DIST, LIVE_ROOT)
    live_synced = True
    run(["nginx", "-t"], cwd=Path("/"))
    run(["systemctl", "reload", "nginx"], cwd=Path("/"))
    time.sleep(1.0)

    live_after_html = fetch_text(f"{LIVE_URL}?tslides_phase2_1_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if live_asset_after != built_asset:
        raise RuntimeError(f"live HTML asset mismatch: built {built_asset}, live {live_asset_after}")
    live_asset_bytes = fetch_bytes(f"{asset_url(live_asset_after)}?tslides_phase2_1={int(time.time())}")
    if sha256_bytes(live_asset_bytes) != sha256_bytes(built_asset_bytes):
        raise RuntimeError("live main JS bytes do not match fresh build")

    for path, fp in unrelated_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"unrelated dirty state changed after live deploy: {path}")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("FILES_PATCHED=4")
    print("PRECHECK_WORKTREE=" + ("CLEAN" if not pre_paths else "DIRTY_UNRELATED_ALLOWED"))
    print("BASELINE_BLOB_GUARD=PASS")
    print("PAYLOAD_INTEGRITY=PASS")
    print("GOOGLE_SLIDES_MENU_ORDER=PASS")
    print("SINGLE_OPEN_MENU_BEHAVIOR=PASS")
    print("OUTSIDE_CLICK_ESCAPE_CLOSE=PASS")
    print("ALT_MENU_SHORTCUTS=PASS")
    print("SUBMENUS=PASS")
    print("DISABLED_CONTEXT_STATES=PASS")
    print("REAL_EDITOR_ACTION_WIRING=PASS")
    print("LIGHT_DARK_MENU_FIDELITY=PASS")
    print("PHASE2_R1_REGRESSION=PASS")
    print("PHASE2_CORE_REGRESSION=PASS")
    print("PHASE1_TSLIDES_REGRESSION=PASS")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("BACKEND_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
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
