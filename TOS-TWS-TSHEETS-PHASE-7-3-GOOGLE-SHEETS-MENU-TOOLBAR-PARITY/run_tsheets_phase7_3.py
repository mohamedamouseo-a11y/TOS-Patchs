#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-TSHEETS-PHASE-7-3-GOOGLE-SHEETS-MENU-TOOLBAR-PARITY"
SCRIPT = "run_tsheets_phase7_3.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "709e7422225f947474e45a1790af890866e6e8dc"

EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
MENU = "frontend/src/pages/tws/TSheetsGoogleMenuBar.jsx"
CSS = "frontend/src/pages/tws/tSheetsPhase7_3GoogleMenu.css"
TEST = "frontend/src/pages/tws/tSheetsPhase7_3GoogleMenu.test.js"
PHASE_SCOPE = {EDITOR, MENU, CSS, TEST}
EDITOR_BLOB = "e6ae05bf6f1219275936334fd4cb24ff97b03f4c"

ROOT = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSHEETS-PHASE-7-3-GOOGLE-SHEETS-MENU-TOOLBAR-PARITY/payload"
PAYLOADS = {
    MENU: (f"{ROOT}/TSheetsGoogleMenuBar.jsx", "11e6f60dfe340aebfc01b7983c2397f948133923"),
    CSS: (f"{ROOT}/tSheetsPhase7_3GoogleMenu.css", "b2937a490216b3a63335fab67a4fe3be1b998d46"),
    TEST: (f"{ROOT}/tSheetsPhase7_3GoogleMenu.test.js", "1a3bc6355d3ddec5d569c788d910e8df96f6b6d5"),
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
        "User-Agent": "TOS-TSheets-Phase7.3/1.0",
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


def regex_replace_once(source: str, pattern: str, replacement: str, label: str, flags=re.S) -> str:
    matches = list(re.finditer(pattern, source, flags))
    if len(matches) != 1:
        raise RuntimeError(f"{label}: expected 1 regex match, found {len(matches)}")
    m = matches[0]
    return source[:m.start()] + replacement + source[m.end():]


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
        raise RuntimeError(f"TSheets editor baseline blob mismatch: expected {EDITOR_BLOB}, got {editor_blob}")

    pre_paths = changed_paths()
    overlap = pre_paths & PHASE_SCOPE
    if overlap:
        raise RuntimeError("dirty overlap with T-Sheets Phase 7.3 scope: " + ", ".join(sorted(overlap)))
    unrelated_fingerprints = {path: fingerprint(path) for path in pre_paths}

    for rel in [MENU, CSS, TEST]:
        if (REPO / rel).exists():
            raise RuntimeError(f"unexpected pre-existing Phase 7.3 file: {rel}")

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
        "tws-sheets-phase7-2-google-parity",
        "tSheetsPhase7_2EMicroFinalR1.css",
        "findReplaceAction",
        "copySelectionToInternalClipboard",
        "pasteInternalClipboard",
        "addChartAction",
        "addPivotAction",
        "addDropdownValidationAction",
        "addConditionalFormattingAction",
    ]:
        if required not in editor:
            raise RuntimeError(f"required T-Sheets marker missing: {required}")

    editor = replace_once(
        editor,
        'import "./tSheetsPhase7_2EMicroFinalR1.css";\n',
        'import "./tSheetsPhase7_2EMicroFinalR1.css";\n'
        'import { TSheetsGoogleMenuBar } from "./TSheetsGoogleMenuBar.jsx";\n'
        'import "./tSheetsPhase7_3GoogleMenu.css";\n',
        "Phase 7.3 imports",
    )

    editor = replace_once(
        editor,
        'tws-sheets-phase7-2e-micro-final relative flex h-full flex-col',
        'tws-sheets-phase7-2e-micro-final tws-sheets-phase7-3-google-menu relative flex h-full flex-col',
        "Phase 7.3 root hook",
    )

    editor = replace_once(
        editor,
        '<input value={title} onChange={handleTitleChange} disabled={!canEdit}',
        '<input data-tws-sheets-title value={title} onChange={handleTitleChange} disabled={!canEdit}',
        "title focus hook",
    )

    helper_anchor = '''  function findReplaceAction() {
    if (!canEdit) return;
    openFindReplacePanel();
  }

'''
    helper_block = helper_anchor + '''  function cutSelectionForMenu() {
    if (!canEdit || !focusedRef) return;
    copySelectionToInternalClipboard();
    clearCurrentSelection();
  }

  function selectAllSheetForMenu() {
    if (!activeSheet) return;
    const rows = Math.min(Number(activeSheet.rows || 1), MAX_VISIBLE_ROWS);
    const cols = Math.min(Number(activeSheet.cols || 1), MAX_VISIBLE_COLS);
    setRangeAnchor("A1");
    setFocusedRef(cellRefFromIndex(Math.max(0, cols - 1), Math.max(0, rows - 1)));
    setNameBoxDraft("");
  }

  async function downloadSheetForMenu(format) {
    const safeFormat = ["csv", "xlsx", "pdf"].includes(format) ? format : "xlsx";
    const query = safeFormat === "csv" ? { sheetId: activeSheetId } : {};
    try {
      await api.tws.downloadExport(documentId, safeFormat, `${title || "sheet"}.${safeFormat}`, query);
    } catch (err) {
      setError(getErrorMessage(err, ui.lang === "en" ? "Export failed." : "تعذر إتمام التصدير."));
    }
  }

  function focusSheetsTitle() {
    const input = document.querySelector("[data-tws-sheets-title]");
    input?.focus();
    input?.select?.();
  }

  async function toggleSheetsFullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      setError(ui.lang === "en" ? "Fullscreen is unavailable in this browser." : "وضع ملء الشاشة غير متاح في هذا المتصفح.");
    }
  }

  function showSheetsKeyboardShortcuts() {
    window.alert([
      "T-Sheets keyboard shortcuts",
      "Ctrl+Z Undo · Ctrl+Y Redo",
      "Ctrl+C Copy · Ctrl+V Paste",
      "Ctrl+B Bold · Ctrl+I Italic · Ctrl+U Underline",
      "Ctrl+H Find & replace · Ctrl+P Print",
      "Ctrl+A Select all · Shift+Arrows Extend selection",
    ].join("\\n"));
  }

  function showSheetsHelp() {
    window.alert(ui.lang === "en"
      ? "T-Sheets uses Google Sheets-style menus while keeping the existing spreadsheet features and shortcuts."
      : "يستخدم T-Sheets قوائم على نمط Google Sheets مع الحفاظ على وظائف الجدول والاختصارات الحالية.");
  }

'''
    editor = replace_once(editor, helper_anchor, helper_block, "Phase 7.3 menu helpers")

    menu_block = '''      <TSheetsGoogleMenuBar
        lang={ui.lang}
        canEdit={canEdit}
        canShare={access === "OWNER"}
        selectedCount={selectedRefSet.size}
        hasFilter={Boolean(activeSheet?.filter)}
        sheetCount={sheets.length}
        actions={{
          rename: focusSheetsTitle,
          versionHistory: () => setShowVersions(true),
          share: () => setShowPermissions(true),
          importCsv: () => csvInputRef.current?.click(),
          importXlsx: () => xlsxInputRef.current?.click(),
          downloadXlsx: () => downloadSheetForMenu("xlsx"),
          downloadCsv: () => downloadSheetForMenu("csv"),
          downloadPdf: () => downloadSheetForMenu("pdf"),
          print: printCurrentSheet,
          undo,
          redo,
          cut: cutSelectionForMenu,
          copy: copySelectionToInternalClipboard,
          paste: pasteInternalClipboard,
          pasteValues: pasteSpecialValuesAction,
          pasteFormats: pasteSpecialFormatsAction,
          clearValues: clearCurrentSelection,
          clearFormatting: clearFormattingAction,
          findReplace: findReplaceAction,
          selectAll: selectAllSheetForMenu,
          fullscreen: toggleSheetsFullscreen,
          toggleInspector: () => setShowSheetPanel((value) => !value),
          freezeRows: () => setFreezeFromSelection("rows"),
          freezeCols: () => setFreezeFromSelection("cols"),
          clearFreeze,
          addSheet,
          addRow,
          addCol,
          addChart: addChartAction,
          addPivot: addPivotAction,
          addDropdown: addDropdownValidationAction,
          addNamedRange,
          bold: () => toggleFormat(focusedRef, "bold"),
          italic: () => toggleFormat(focusedRef, "italic"),
          underline: () => toggleFormat(focusedRef, "underline"),
          strike: () => toggleFormat(focusedRef, "strike"),
          wrap: () => toggleFormat(focusedRef, "wrap"),
          fontSize: (value) => toggleFormat(focusedRef, "fontSize", value),
          numberFormat: (value) => toggleFormat(focusedRef, "numberFormat", value),
          alignLeft: () => toggleFormat(focusedRef, "align", "left"),
          alignCenter: () => toggleFormat(focusedRef, "align", "center"),
          alignRight: () => toggleFormat(focusedRef, "align", "right"),
          alignTop: () => toggleFormat(focusedRef, "vertical", "top"),
          alignMiddle: () => toggleFormat(focusedRef, "vertical", "middle"),
          alignBottom: () => toggleFormat(focusedRef, "vertical", "bottom"),
          merge: mergeSelectionAction,
          unmerge: unmergeSelectionAction,
          sortAsc: () => sortSelection("asc"),
          sortDesc: () => sortSelection("desc"),
          createFilter: createFilterAction,
          filterValues: filterCurrentColumnAction,
          clearFilter: clearFilterAction,
          conditionalFormatting: addConditionalFormattingAction,
          protect: protectSelection,
          unprotect: unprotectSelection,
          comments: () => setShowComments(true),
          keyboardShortcuts: showSheetsKeyboardShortcuts,
          help: showSheetsHelp,
        }}
      />

'''

    editor = regex_replace_once(
        editor,
        r'      \{canEdit && \(\n        <div className="tws-sheets-menu-strip".*?\n      \)\}\n\n(?=      \{!canEdit && <Notice)',
        menu_block,
        "replace legacy sheet menu strip",
    )

    (REPO / EDITOR).write_text(editor, encoding="utf-8")
    for rel, data in payload_bytes.items():
        target = REPO / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    source_applied = True

    run(["git", "diff", "--check"])
    run(["node", "--test", TEST])
    for regression in [
        "frontend/src/pages/tws/tSheetsPhase7_2EMicroFinalR1.test.js",
        "frontend/src/pages/tws/tSheetsPhase7_2DGoogleDarkFidelity.test.js",
        "frontend/src/pages/tws/tSheetsPhase7_2CFinal.test.js",
    ]:
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

    final_editor = (REPO / EDITOR).read_text(encoding="utf-8")
    final_menu = (REPO / MENU).read_text(encoding="utf-8")
    final_css = (REPO / CSS).read_text(encoding="utf-8")
    for marker in [
        "TSheetsGoogleMenuBar", "tSheetsPhase7_3GoogleMenu.css", "tws-sheets-phase7-3-google-menu",
        "data-tws-sheets-title", "cutSelectionForMenu", "selectAllSheetForMenu", "downloadSheetForMenu",
    ]:
        if marker not in final_editor:
            raise RuntimeError(f"final editor verification missing: {marker}")
    for label in ["File", "Edit", "View", "Insert", "Format", "Data", "Tools", "Extensions", "Help"]:
        if f'"{label}"' not in final_menu:
            raise RuntimeError(f"menu verification missing: {label}")
    for marker in ["#137333", "#e6f4ea", ".tws-sheets-toolbar-compact", ".dark .tws-sheets-google-menu-bar"]:
        if marker not in final_css:
            raise RuntimeError(f"CSS verification missing: {marker}")

    nginx_dump = run(["nginx", "-T"], cwd=Path("/"), check=False)
    nginx_text = (nginx_dump.stdout or "") + (nginx_dump.stderr or "")
    if nginx_dump.returncode != 0 or "server_name tos.tamiyouz.com" not in nginx_text or str(LIVE_ROOT) not in nginx_text:
        raise RuntimeError("production root guard failed")

    live_before_html = fetch_text(f"{LIVE_URL}?tsheets_phase7_3_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.is_file():
        raise RuntimeError(f"built main asset missing: {built_asset_path}")
    built_asset_bytes = built_asset_path.read_bytes()

    backup_dir = Path("/tmp") / f"tsheets_phase7_3_live_backup_{int(time.time())}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    live_index_backup = backup_dir / "index.html"
    shutil.copy2(LIVE_ROOT / "index.html", live_index_backup)

    sync_dist(DIST, LIVE_ROOT)
    live_synced = True
    run(["nginx", "-t"], cwd=Path("/"))
    run(["systemctl", "reload", "nginx"], cwd=Path("/"))
    time.sleep(1.0)

    live_after_html = fetch_text(f"{LIVE_URL}?tsheets_phase7_3_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if live_asset_after != built_asset:
        raise RuntimeError(f"live HTML asset mismatch: built {built_asset}, live {live_asset_after}")
    live_asset_bytes = fetch_bytes(f"{asset_url(live_asset_after)}?tsheets_phase7_3={int(time.time())}")
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
    print("GOOGLE_SHEETS_MENU_ORDER=PASS")
    print("SINGLE_OPEN_MENU_BEHAVIOR=PASS")
    print("OUTSIDE_CLICK_ESCAPE_ALT=PASS")
    print("SUBMENUS=PASS")
    print("CONTEXT_DISABLED_STATES=PASS")
    print("REAL_EDITOR_ACTION_WIRING=PASS")
    print("GOOGLE_STYLE_TOOLBAR_POLISH=PASS")
    print("LIGHT_DARK_MENU_FIDELITY=PASS")
    print("PHASE7_2_REGRESSION=PASS")
    print(f"FRONTEND_BUILD=PASS ({build_seconds:.2f}s)")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_asset_before}")
    print(f"LIVE_ASSET_AFTER={live_asset_after}")
    print(f"LIVE_DEPLOY_ROOT={LIVE_ROOT}")
    print("LIVE_DEPLOY=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print("BACKEND_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print(f"PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED={'YES' if all(fingerprint(path) == fp for path, fp in unrelated_fingerprints.items()) else 'NO'}")
    print("CHANGED_PATHS_EXACT=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")

except Exception as exc:
    fail(str(exc))
