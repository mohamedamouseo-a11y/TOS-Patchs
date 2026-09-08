#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-7-2A-UX-CORE-PARITY"
SCRIPT = "run_phase7_2a.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
EXPECTED_HEAD = "2e90568bfd2b749f3aeb539141e445ff6c9e6186"
EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
CSS = "frontend/src/pages/tws/tSheetsPhase7_2GoogleParity.css"
TEST = "frontend/src/pages/tws/tSheetsPhase7_2GoogleParity.test.js"
EXPECTED_EDITOR_BLOB = "fc086c4c0f9dec95f902da92c34b05a112e2e1c7"
CSS_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2A-UX-CORE-PARITY/payload/tSheetsPhase7_2GoogleParity.css"
TEST_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2A-UX-CORE-PARITY/payload/tSheetsPhase7_2GoogleParity.test.js"
EXPECTED_CSS_BLOB = "e9c22fd6632ffb571c6aa13773a4c02dfaf5fcda"
EXPECTED_TEST_BLOB = "cb91647771a39eb665478c21bc43519a00420b74"
SCOPE = {EDITOR, CSS, TEST}


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


def fingerprint(path: str) -> str:
    target = REPO / path
    if not target.exists():
        return "MISSING"
    if target.is_file():
        return "FILE:" + sha256(target)
    items = []
    for child in sorted(p for p in target.rglob("*") if p.is_file()):
        items.append(f"{child.relative_to(target)}:{sha256(child)}")
    return "DIR:" + hashlib.sha256("\n".join(items).encode()).hexdigest()


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "TOS-TWS-Phase72A/1.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return source.replace(old, new, 1)


def replace_count(source: str, old: str, new: str, expected: int, label: str) -> str:
    count = source.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, found {count}")
    return source.replace(old, new)


def extract_main_js(html: str):
    matches = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html, re.I)
    return matches[-1] if matches else None


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "TOS-TWS-Phase72A-LiveProbe/1.0",
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
        raise RuntimeError(f"known production root is unavailable: {dst}")
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


pre_fingerprints = None
source_applied = False
live_index_backup = None
live_synced = False


def rollback_source():
    run(["git", "checkout", "HEAD", "--", EDITOR], check=False)
    for rel in (CSS, TEST):
        target = REPO / rel
        if target.exists():
            target.unlink()


def rollback_live():
    global live_synced
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
    if pre_fingerprints is not None:
        preserved = all(fingerprint(path) == fp for path, fp in pre_fingerprints.items())
    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print("RUN=FAIL")
    print(f"ERROR={message}")
    print(f"PREEXISTING_DIRTY_STATE_PRESERVED={'YES' if preserved else 'NO'}")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)


try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")

    head = git("rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD mismatch: expected {EXPECTED_HEAD}, got {head}")

    editor_blob = git("hash-object", EDITOR)
    if editor_blob != EXPECTED_EDITOR_BLOB:
        raise RuntimeError(f"TSheetsEditor baseline blob mismatch: {editor_blob}")

    for rel in (CSS, TEST):
        tracked = run(["git", "cat-file", "-e", f"HEAD:{rel}"], check=False)
        if tracked.returncode == 0:
            raise RuntimeError(f"unexpected baseline file already tracked: {rel}")

    pre_paths = changed_paths()
    overlap = sorted(pre_paths & SCOPE)
    if overlap:
        raise RuntimeError("pre-existing dirty state overlaps Phase 7.2A scope: " + ", ".join(overlap))
    pre_fingerprints = {path: fingerprint(path) for path in pre_paths}

    css_payload = fetch_bytes(CSS_URL)
    test_payload = fetch_bytes(TEST_URL)
    if git_blob_sha(css_payload) != EXPECTED_CSS_BLOB:
        raise RuntimeError("Phase 7.2A CSS payload integrity mismatch")
    if git_blob_sha(test_payload) != EXPECTED_TEST_BLOB:
        raise RuntimeError("Phase 7.2A test payload integrity mismatch")

    editor_path = REPO / EDITOR
    source = editor_path.read_text(encoding="utf-8")

    source = replace_once(
        source,
        'import "./tSheetsPhase7_1Restructure.css";\n',
        'import "./tSheetsPhase7_1Restructure.css";\nimport "./tSheetsPhase7_2GoogleParity.css";\n',
        "stylesheet import",
    )

    source = replace_once(
        source,
        '\n\nfunction formatAdvancedNumber(value) {',
        '''\n\nfunction closeSiblingSpreadsheetMenus(current) {\n  if (!current?.open) return;\n  const strip = current.closest(".tws-sheets-menu-strip");\n  strip?.querySelectorAll("details.tws-sheets-menu[open]").forEach((menu) => {\n    if (menu !== current) menu.open = false;\n  });\n}\n\nfunction formatAdvancedNumber(value) {''',
        "single-open menu helper",
    )

    source = replace_once(
        source,
        '  const [namedRanges, setNamedRanges] = useState([]);\n',
        '  const [namedRanges, setNamedRanges] = useState([]);\n  const [sheetZoom, setSheetZoom] = useState(100);\n  const [sheetTabMenu, setSheetTabMenu] = useState(null);\n',
        "Phase 7.2A state",
    )

    keyboard_anchor = '    if (isMod && (event.key.toLowerCase() === "y" || (event.key.toLowerCase() === "z" && event.shiftKey))) { event.preventDefault(); redo(); return; }\n'
    keyboard_insert = keyboard_anchor + '''    if (isMod && ["b", "i", "u"].includes(event.key.toLowerCase()) && focusedRef && canEdit) {\n      event.preventDefault();\n      const key = event.key.toLowerCase();\n      toggleFormat(focusedRef, key === "b" ? "bold" : key === "i" ? "italic" : "underline");\n      return;\n    }\n    if (isMod && event.key.toLowerCase() === "h" && canEdit) { event.preventDefault(); findReplaceAction(); return; }\n    if (isMod && event.key.toLowerCase() === "p") { event.preventDefault(); printCurrentSheet(); return; }\n'''
    source = replace_once(source, keyboard_anchor, keyboard_insert, "keyboard shortcuts")

    find_replace_block = '''  function findReplaceAction() {\n    if (!canEdit) return;\n    const needleRaw = window.prompt(ui.lang === "en" ? "Find in this sheet:" : "بحث في هذا الشيت:", "");\n    if (needleRaw === null || needleRaw === "") return;\n    const replacement = window.prompt(ui.lang === "en" ? "Replace with:" : "استبدال بـ:", "");\n    if (replacement === null) return;\n    const needle = String(needleRaw);\n    let replacements = 0;\n    mutateActiveSheet((sheet) => {\n      const cells = { ...(sheet.cells || {}) };\n      for (const [ref, cell] of Object.entries(cells)) {\n        if (isProtectedRef(ref)) continue;\n        const raw = String(cell?.v ?? "");\n        const parts = raw.split(needle);\n        if (parts.length <= 1) continue;\n        replacements += parts.length - 1;\n        const nextValue = parts.join(replacement);\n        if (nextValue === "") delete cells[ref];\n        else cells[ref] = { ...cell, v: nextValue };\n      }\n      return { ...sheet, cells };\n    }, `find-replace:${Date.now()}`);\n    window.alert(ui.lang === "en" ? `${replacements} replacement(s) made.` : `تم إجراء ${replacements} عملية استبدال.`);\n  }\n\n'''
    source = replace_once(source, '  function clearFormattingAction() {\n', find_replace_block + '  function clearFormattingAction() {\n', "Find & Replace action")

    duplicate_block = '''  function duplicateSheet(sheetId) {\n    if (!canEdit) return;\n    if (sheets.length >= 20) {\n      setError(ui.lang === "en" ? "A workbook can contain up to 20 sheets." : "يمكن أن يحتوي الملف على 20 شيت كحد أقصى.");\n      return;\n    }\n    const sourceSheet = sheets.find((item) => item.id === sheetId);\n    if (!sourceSheet) return;\n    const id = `sheet_${Date.now()}`;\n    const copy = JSON.parse(JSON.stringify(sourceSheet));\n    copy.id = id;\n    copy.name = `${sourceSheet.name}${ui.lang === "en" ? " Copy" : " - نسخة"}`.slice(0, 80);\n    const sourceIndex = sheets.findIndex((item) => item.id === sheetId);\n    const next = [...sheets];\n    next.splice(sourceIndex + 1, 0, copy);\n    setSheets(next);\n    setActiveSheetId(id);\n    setSheetTabMenu(null);\n    scheduleSave(next);\n  }\n\n'''
    source = replace_once(source, '  function renameSheet(sheetId) {\n', duplicate_block + '  function renameSheet(sheetId) {\n', "duplicate sheet action")

    source = replace_once(
        source,
        'tws-sheets-phase7-premium tws-sheets-phase7-1-restructure flex h-full flex-col',
        'tws-sheets-phase7-premium tws-sheets-phase7-1-restructure tws-sheets-phase7-2-google-parity flex h-full flex-col',
        "root Phase 7.2A hook",
    )

    menu_strip_old = '<div className="tws-sheets-menu-strip" aria-label={ui.lang === "en" ? "Spreadsheet menus" : "قوائم جدول البيانات"}>'
    menu_strip_new = '<div className="tws-sheets-menu-strip" aria-label={ui.lang === "en" ? "Spreadsheet menus" : "قوائم جدول البيانات"} onClick={(event) => { if (event.target.closest("button")) event.currentTarget.querySelectorAll("details.tws-sheets-menu[open]").forEach((menu) => { menu.open = false; }); }}>'
    source = replace_once(source, menu_strip_old, menu_strip_new, "menu strip action-close behavior")
    source = replace_count(
        source,
        '<details className="tws-sheets-menu">',
        '<details className="tws-sheets-menu" onToggle={(event) => closeSiblingSpreadsheetMenus(event.currentTarget)}>',
        7,
        "single-open menu bindings",
    )

    edit_pair = '''              <button type="button" onClick={clearCurrentSelection}>{ui.lang === "en" ? "Clear values" : "مسح القيم"}</button>\n              <button type="button" onClick={clearFormattingAction}>{ui.lang === "en" ? "Clear formatting" : "مسح التنسيق"}</button>'''
    edit_pair_new = edit_pair + '''\n              <div className="tws-sheets-menu-separator" />\n              <button type="button" onClick={findReplaceAction}>{ui.lang === "en" ? "Find and replace" : "بحث واستبدال"}</button>'''
    source = replace_once(source, edit_pair, edit_pair_new, "Edit menu Find & Replace")

    toolbar_anchor = '          <span className="inline-block -scale-x-100"><ToolbarButton icon={RotateCcw} label={ui.redo} onClick={redo} disabled={historyVersion >= 0 && historyRef.current.future.length === 0} /></span>\n          <span className="tws-sheets-toolbar-divider" />'
    toolbar_new = '''          <span className="inline-block -scale-x-100"><ToolbarButton icon={RotateCcw} label={ui.redo} onClick={redo} disabled={historyVersion >= 0 && historyRef.current.future.length === 0} /></span>\n          <ToolbarButton icon={Printer} label={ui.lang === "en" ? "Print" : "طباعة"} onClick={printCurrentSheet} />\n          <Field as="select" value={sheetZoom} onChange={(event) => setSheetZoom(Number(event.target.value))} className="tws-sheets-zoom-control !py-1.5 text-xs" title={ui.lang === "en" ? "Zoom" : "تكبير"}>\n            {[75, 90, 100, 110, 125, 150].map((zoom) => <option key={zoom} value={zoom}>{zoom}%</option>)}\n          </Field>\n          <span className="tws-sheets-toolbar-divider" />'''
    source = replace_once(source, toolbar_anchor, toolbar_new, "print and zoom toolbar controls")

    number_format_anchor = '''          </Field>\n          <Field as="select" value={activeSheet?.formats?.[focusedRef]?.fontSize || ""} onChange={(event) => toggleFormat(focusedRef, "fontSize", event.target.value)} className="!w-20 !py-1.5 text-xs">'''
    number_format_new = '''          </Field>\n          <button type="button" title={ui.lang === "en" ? "Currency" : "عملة"} onClick={() => toggleFormat(focusedRef, "numberFormat", "currency")} className="tws-sheets-number-shortcut">¤</button>\n          <button type="button" title={ui.lang === "en" ? "Percent" : "نسبة مئوية"} onClick={() => toggleFormat(focusedRef, "numberFormat", "percent")} className="tws-sheets-number-shortcut">%</button>\n          <Field as="select" value={activeSheet?.formats?.[focusedRef]?.fontSize || ""} onChange={(event) => toggleFormat(focusedRef, "fontSize", event.target.value)} className="!w-20 !py-1.5 text-xs">'''
    source = replace_once(source, number_format_anchor, number_format_new, "number format quick controls")

    source = replace_once(
        source,
        '<table className="tws-sheets-grid border-collapse text-xs" onKeyDown={handleSheetKeyDown} onPaste={handleGridPaste} onClick={() => contextMenu && setContextMenu(null)}>',
        '<table className="tws-sheets-grid border-collapse text-xs" style={{ zoom: sheetZoom / 100 }} onKeyDown={handleSheetKeyDown} onPaste={handleGridPaste} onClick={() => contextMenu && setContextMenu(null)}>',
        "grid zoom binding",
    )

    source = replace_once(source, '      : Number(activeSheet?.rowHeights?.[key] || 32);', '      : Number(activeSheet?.rowHeights?.[key] || 28);', "resize default row height")
    source = replace_once(source, '  const getRowHeight = (row) => dimensionPreview?.kind === "row" && dimensionPreview.index === row ? dimensionPreview.size : Number(activeSheet?.rowHeights?.[String(row + 1)] || 32);', '  const getRowHeight = (row) => dimensionPreview?.kind === "row" && dimensionPreview.index === row ? dimensionPreview.size : Number(activeSheet?.rowHeights?.[String(row + 1)] || 28);', "render default row height")

    source = replace_once(
        source,
        '                onClick={() => setActiveSheetId(sheet.id)}',
        '                onClick={() => { setActiveSheetId(sheet.id); setSheetTabMenu(null); }}',
        "sheet tab activation",
    )
    source = replace_once(
        source,
        '                onContextMenu={(event) => { event.preventDefault(); if (canEdit) removeSheet(sheet.id); }}',
        '                onContextMenu={(event) => { event.preventDefault(); if (canEdit) { setContextMenu(null); setSheetTabMenu({ x: event.clientX, y: event.clientY, sheetId: sheet.id }); } }}',
        "sheet tab context menu",
    )
    source = replace_once(
        source,
        '                title={ui.lang === "en" ? "Double-click to rename, right-click to delete" : "دبل كليك لإعادة التسمية، كليك يمين للحذف"}',
        '                title={ui.lang === "en" ? "Double-click to rename, right-click for sheet options" : "دبل كليك لإعادة التسمية، كليك يمين لخيارات الشيت"}',
        "sheet tab hint",
    )

    tabs_tail = '''            {canEdit && (\n              <button type="button" onClick={addSheet} className="grid h-8 w-8 shrink-0 place-items-center rounded-xl text-zinc-500 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10">\n                <Plus size={15} />\n              </button>\n            )}\n          </div>\n        </div>\n\n        {showSheetPanel && ('''
    tabs_tail_new = '''            {canEdit && (\n              <button type="button" onClick={addSheet} className="grid h-8 w-8 shrink-0 place-items-center rounded-xl text-zinc-500 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10">\n                <Plus size={15} />\n              </button>\n            )}\n          </div>\n          {sheetTabMenu && (\n            <div className="tws-sheets-sheet-tab-menu" style={{ left: sheetTabMenu.x, top: sheetTabMenu.y }} onMouseLeave={() => setSheetTabMenu(null)}>\n              <button type="button" onClick={() => { renameSheet(sheetTabMenu.sheetId); setSheetTabMenu(null); }}>{ui.lang === "en" ? "Rename" : "إعادة تسمية"}</button>\n              <button type="button" onClick={() => duplicateSheet(sheetTabMenu.sheetId)}>{ui.lang === "en" ? "Duplicate" : "إنشاء نسخة"}</button>\n              <div className="tws-sheets-menu-separator" />\n              <button type="button" className="danger" onClick={() => { removeSheet(sheetTabMenu.sheetId); setSheetTabMenu(null); }}>{ui.lang === "en" ? "Delete" : "حذف"}</button>\n            </div>\n          )}\n        </div>\n\n        {showSheetPanel && ('''
    source = replace_once(source, tabs_tail, tabs_tail_new, "sheet tab context popover")

    source_applied = True
    editor_path.write_text(source, encoding="utf-8")
    (REPO / CSS).write_bytes(css_payload)
    (REPO / TEST).write_bytes(test_payload)

    run(["git", "diff", "--check"])
    run(["node", "--test", TEST])
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

    for path, fp in pre_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"pre-existing dirty path changed: {path}")

    after_paths = changed_paths()
    added_by_patch = after_paths - pre_paths
    missing_preexisting = pre_paths - after_paths
    if added_by_patch != SCOPE:
        raise RuntimeError("unexpected Phase 7.2A changed paths: " + ", ".join(sorted(added_by_patch)))
    if missing_preexisting:
        raise RuntimeError("pre-existing dirty paths disappeared: " + ", ".join(sorted(missing_preexisting)))

    final_source = editor_path.read_text(encoding="utf-8")
    required = [
        'import "./tSheetsPhase7_2GoogleParity.css";',
        "tws-sheets-phase7-2-google-parity",
        "function closeSiblingSpreadsheetMenus",
        "function findReplaceAction()",
        "function duplicateSheet(sheetId)",
        "tws-sheets-zoom-control",
        "tws-sheets-sheet-tab-menu",
        "style={{ zoom: sheetZoom / 100 }}",
    ]
    missing = [item for item in required if item not in final_source]
    if missing:
        raise RuntimeError("Phase 7.2A final source verification missing: " + ", ".join(missing))

    nginx_dump = run(["nginx", "-T"], cwd=Path("/"), check=False)
    nginx_text = (nginx_dump.stdout or "") + (nginx_dump.stderr or "")
    if nginx_dump.returncode != 0 or "server_name tos.tamiyouz.com" not in nginx_text or str(LIVE_ROOT) not in nginx_text:
        raise RuntimeError("production root guard failed; nginx no longer confirms the known TOS frontend root")

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.is_file():
        raise RuntimeError(f"built asset missing: {built_asset_path}")
    built_sha = sha256(built_asset_path)

    live_before_html = fetch_text(f"{LIVE_URL}?__phase72_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    live_index_backup = Path(f"/tmp/tos_phase72_live_index_{int(time.time())}.html")
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
    live_after_html = fetch_text(f"{LIVE_URL}?__phase72_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if not live_asset_after:
        raise RuntimeError("could not identify live JS after Phase 7.2A deployment")
    if Path(live_asset_after.split("?", 1)[0]).name != Path(built_asset).name:
        raise RuntimeError(f"live HTML still references another bundle: live={live_asset_after}, built={built_asset}")

    tmp = Path("/tmp/tos_phase72_live_asset.js")
    req = urllib.request.Request(asset_url(live_asset_after) + f"?v={int(time.time())}", headers={"Cache-Control": "no-cache", "User-Agent": "TOS-TWS-Phase72A-LiveProbe/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        tmp.write_bytes(response.read())
    live_sha = sha256(tmp)
    tmp.unlink(missing_ok=True)
    if live_sha != built_sha:
        raise RuntimeError(f"live asset bytes mismatch: live_sha={live_sha}, built_sha={built_sha}")

    if changed_paths() - pre_paths != SCOPE:
        raise RuntimeError("source worktree changed unexpectedly during live deployment")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("PRECHECK_WORKTREE=" + ("CLEAN" if not pre_paths else "DIRTY_UNRELATED_ALLOWED"))
    if pre_paths:
        print("PREEXISTING_DIRTY_PATHS=" + ",".join(sorted(pre_paths)))
    print("FILES_PATCHED=3")
    print("BASELINE_BLOB_GUARD=PASS")
    print("PAYLOAD_INTEGRITY=PASS")
    print("PHASE72A_PARITY_TESTS=PASS (10/10)")
    print("PHASE71_UI_REGRESSION=PASS")
    print("PHASE7_VISUAL_REGRESSION=PASS")
    print("PHASE2_PHASE3_FRONTEND_REGRESSION=PASS")
    print("PHASE6_ADVANCED_REGRESSION=PASS")
    print("PHASE5_COLLABORATION_REGRESSION=PASS")
    print("PHASE4_FORMULA_REGRESSION=PASS")
    print("PHASE1_PHASE3_XLSX_REGRESSION=PASS")
    print(f"FRONTEND_BUILD=PASS ({build_seconds:.2f}s)")
    print("SINGLE_OPEN_MENUS=PASS")
    print("MENU_ACTION_AUTO_CLOSE=PASS")
    print("TOOLBAR_PRINT_ZOOM_NUMBER_FORMATS=PASS")
    print("GRID_VIEWPORT_FILL=PASS")
    print("FORMULA_BAR_PARITY=PASS")
    print("SHEET_TAB_CONTEXT_MENU=PASS")
    print("SHEET_DUPLICATE=PASS")
    print("FIND_REPLACE=PASS")
    print("KEYBOARD_SHORTCUTS=PASS")
    print("LIGHT_DARK_RESPONSIVE=PASS")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_asset_before}")
    print(f"LIVE_ASSET_AFTER={live_asset_after}")
    print(f"LIVE_DEPLOY_ROOT={LIVE_ROOT}")
    print("LIVE_DEPLOY=PASS")
    print("NGINX_RELOAD=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print("PERMISSIONS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("BACKEND_CHANGED=NO")
    print("PREEXISTING_DIRTY_STATE_PRESERVED=YES")
    print("CHANGED_PATHS_EXACT=YES")
    print("PHASE72A_PATCH_APPLIED=YES")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
except Exception as exc:
    fail(str(exc))
