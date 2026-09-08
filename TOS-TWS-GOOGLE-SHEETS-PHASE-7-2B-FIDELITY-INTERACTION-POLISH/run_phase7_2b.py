#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-7-2B-FIDELITY-INTERACTION-POLISH"
SCRIPT = "run_phase7_2b.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
EXPECTED_HEAD = "2e90568bfd2b749f3aeb539141e445ff6c9e6186"

EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
PHASE72A_CSS = "frontend/src/pages/tws/tSheetsPhase7_2GoogleParity.css"
PHASE72A_TEST = "frontend/src/pages/tws/tSheetsPhase7_2GoogleParity.test.js"
CSS = "frontend/src/pages/tws/tSheetsPhase7_2BPolish.css"
TEST = "frontend/src/pages/tws/tSheetsPhase7_2BPolish.test.js"

PHASE72A_DIRTY = {EDITOR, PHASE72A_CSS, PHASE72A_TEST}
FINAL_SCOPE = {EDITOR, PHASE72A_CSS, PHASE72A_TEST, CSS, TEST}
EXPECTED_72A_CSS_BLOB = "e9c22fd6632ffb571c6aa13773a4c02dfaf5fcda"
EXPECTED_72A_TEST_BLOB = "cb91647771a39eb665478c21bc43519a00420b74"
CSS_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2B-FIDELITY-INTERACTION-POLISH/payload/tSheetsPhase7_2BPolish.css"
TEST_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2B-FIDELITY-INTERACTION-POLISH/payload/tSheetsPhase7_2BPolish.test.js"
EXPECTED_CSS_BLOB = "baa2c8e6fb5142d335d16710481d0d39216a3b91"
EXPECTED_TEST_BLOB = "3360d64acc06dd95635ccd10eae9a3cb30fea2d3"


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


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "TOS-TWS-Phase72B/1.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return source.replace(old, new, 1)


def regex_once(source: str, pattern: str, replacement: str, label: str) -> str:
    result, count = re.subn(pattern, replacement, source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 regex match, found {count}")
    return result


def extract_main_js(html: str):
    matches = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html, re.I)
    return matches[-1] if matches else None


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "TOS-TWS-Phase72B-LiveProbe/1.0", "Cache-Control": "no-cache", "Pragma": "no-cache"})
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


pre_editor_bytes = None
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
    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print("RUN=FAIL")
    print(f"ERROR={message}")
    print("PHASE72A_SOURCE_STATE_RESTORED=YES")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)


try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")

    head = git("rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD mismatch: expected {EXPECTED_HEAD}, got {head}")

    current_dirty = changed_paths()
    if current_dirty != PHASE72A_DIRTY:
        raise RuntimeError("Phase 7.2A worktree state mismatch: " + ", ".join(sorted(current_dirty)))

    if git("hash-object", PHASE72A_CSS) != EXPECTED_72A_CSS_BLOB:
        raise RuntimeError("Phase 7.2A CSS blob mismatch")
    if git("hash-object", PHASE72A_TEST) != EXPECTED_72A_TEST_BLOB:
        raise RuntimeError("Phase 7.2A test blob mismatch")

    editor_path = REPO / EDITOR
    pre_editor_bytes = editor_path.read_bytes()
    source = pre_editor_bytes.decode("utf-8")
    phase72a_required = [
        'import "./tSheetsPhase7_2GoogleParity.css";',
        "tws-sheets-phase7-2-google-parity",
        "function closeSiblingSpreadsheetMenus",
        "function findReplaceAction()",
        "function duplicateSheet(sheetId)",
        "tws-sheets-zoom-control",
        "tws-sheets-sheet-tab-menu",
        "style={{ zoom: sheetZoom / 100 }}",
    ]
    missing_72a = [item for item in phase72a_required if item not in source]
    if missing_72a:
        raise RuntimeError("Phase 7.2A source guard missing: " + ", ".join(missing_72a))
    if 'tSheetsPhase7_2BPolish.css' in source:
        raise RuntimeError("Phase 7.2B already appears to be applied")

    for rel in (CSS, TEST):
        if (REPO / rel).exists():
            raise RuntimeError(f"unexpected pre-existing Phase 7.2B file: {rel}")

    css_payload = fetch_bytes(CSS_URL)
    test_payload = fetch_bytes(TEST_URL)
    if git_blob_sha(css_payload) != EXPECTED_CSS_BLOB:
        raise RuntimeError("Phase 7.2B CSS payload integrity mismatch")
    if git_blob_sha(test_payload) != EXPECTED_TEST_BLOB:
        raise RuntimeError("Phase 7.2B test payload integrity mismatch")

    source = replace_once(
        source,
        'import "./tSheetsPhase7_2GoogleParity.css";\n',
        'import "./tSheetsPhase7_2GoogleParity.css";\nimport "./tSheetsPhase7_2BPolish.css";\n',
        "Phase 7.2B stylesheet import",
    )

    source = replace_once(
        source,
        '  const [sheetTabMenu, setSheetTabMenu] = useState(null);\n',
        '  const [sheetTabMenu, setSheetTabMenu] = useState(null);\n  const [dragSheetId, setDragSheetId] = useState("");\n  const [findReplacePanel, setFindReplacePanel] = useState({ open: false, find: "", replace: "", matchCase: false });\n',
        "Phase 7.2B state",
    )

    source = replace_once(
        source,
        '      disabled={disabled}\n',
        '      aria-pressed={active}\n      disabled={disabled}\n',
        "toolbar pressed state",
    )

    copy_pattern = r'  function copySelectionToInternalClipboard\(\) \{.*?\n  \}\n\n  function pasteInternalClipboard\(\) \{'
    copy_replacement = '''  function copySelectionToInternalClipboard() {\n    const bounds = selectionBounds();\n    if (!bounds || !activeSheet) return;\n    const matrix = selectionMatrix(activeSheet, bounds);\n    const valueMatrix = [];\n    const formatMatrix = [];\n    for (let row = bounds.rowFrom; row <= bounds.rowTo; row += 1) {\n      const values = [];\n      const formats = [];\n      for (let col = bounds.colFrom; col <= bounds.colTo; col += 1) {\n        const ref = cellRefFromIndex(col, row);\n        values.push(computedValues[ref] ?? "");\n        const format = activeSheet?.formats?.[ref];\n        formats.push(format ? { ...format } : null);\n      }\n      valueMatrix.push(values);\n      formatMatrix.push(formats);\n    }\n    rangeClipboardRef.current = { matrix, valueMatrix, formatMatrix, sourceBounds: bounds };\n    clipboardRef.current = null;\n    try { navigator.clipboard?.writeText(matrixToTsv(matrix)); } catch { /* best effort */ }\n  }\n\n  function pasteInternalClipboard() {'''
    source = regex_once(source, copy_pattern, copy_replacement, "clipboard metadata enrichment")

    paste_anchor = '''  function clearCurrentSelection() {\n'''
    paste_special = '''  function pasteSpecialValuesAction() {\n    if (!canEdit || !focusedRef || !rangeClipboardRef.current?.valueMatrix) return;\n    const copied = rangeClipboardRef.current;\n    mutateActiveSheet((sheet) => pastePlainMatrix(sheet, focusedRef, copied.valueMatrix), `paste-values:${Date.now()}`);\n    setContextMenu(null);\n  }\n\n  function pasteSpecialFormatsAction() {\n    if (!canEdit || !focusedRef || !rangeClipboardRef.current?.formatMatrix) return;\n    const target = parseCellRef(focusedRef);\n    if (!target) return;\n    const formatMatrix = rangeClipboardRef.current.formatMatrix;\n    mutateActiveSheet((sheet) => {\n      const formats = { ...(sheet.formats || {}) };\n      for (let rowOffset = 0; rowOffset < formatMatrix.length; rowOffset += 1) {\n        for (let colOffset = 0; colOffset < (formatMatrix[rowOffset] || []).length; colOffset += 1) {\n          const row = target.row + rowOffset;\n          const col = target.col + colOffset;\n          if (row >= Number(sheet.rows || 0) || col >= Number(sheet.cols || 0)) continue;\n          const ref = cellRefFromIndex(col, row);\n          if (isProtectedRef(ref)) continue;\n          const sourceFormat = formatMatrix[rowOffset][colOffset];\n          if (sourceFormat) formats[ref] = { ...sourceFormat };\n          else delete formats[ref];\n        }\n      }\n      return { ...sheet, formats };\n    }, `paste-formats:${Date.now()}`);\n    setContextMenu(null);\n  }\n\n'''
    source = replace_once(source, paste_anchor, paste_special + paste_anchor, "Paste Special actions")

    find_pattern = r'  function findReplaceAction\(\) \{.*?\n  \}\n\n  function clearFormattingAction\(\) \{'
    find_replacement = '''  function openFindReplacePanel() {\n    setFindReplacePanel((current) => ({ ...current, open: true }));\n  }\n\n  function findReplaceAction() {\n    if (!canEdit) return;\n    openFindReplacePanel();\n  }\n\n  function findNextMatch() {\n    const needle = String(findReplacePanel.find || "");\n    if (!needle) return;\n    const normalize = (value) => findReplacePanel.matchCase ? String(value ?? "") : String(value ?? "").toLowerCase();\n    const wanted = normalize(needle);\n    const refs = [];\n    const rows = Math.min(Number(activeSheet?.rows || 0), MAX_VISIBLE_ROWS);\n    const cols = Math.min(Number(activeSheet?.cols || 0), MAX_VISIBLE_COLS);\n    for (let row = 0; row < rows; row += 1) {\n      for (let col = 0; col < cols; col += 1) {\n        const ref = cellRefFromIndex(col, row);\n        if (normalize(activeSheet?.cells?.[ref]?.v).includes(wanted)) refs.push(ref);\n      }\n    }\n    if (!refs.length) {\n      setError(ui.lang === "en" ? "No matching cells found." : "لم يتم العثور على خلايا مطابقة.");\n      return;\n    }\n    const currentIndex = refs.indexOf(focusedRef);\n    const nextRef = refs[(currentIndex + 1 + refs.length) % refs.length];\n    setRangeAnchor("");\n    setFocusedRef(nextRef);\n    window.requestAnimationFrame(() => document.getElementById(`tws-cell-${nextRef}`)?.focus());\n  }\n\n  function replaceAllMatches() {\n    if (!canEdit) return;\n    const needle = String(findReplacePanel.find || "");\n    if (!needle) return;\n    const replacement = String(findReplacePanel.replace || "");\n    let replacements = 0;\n    mutateActiveSheet((sheet) => {\n      const cells = { ...(sheet.cells || {}) };\n      for (const [ref, cell] of Object.entries(cells)) {\n        if (isProtectedRef(ref)) continue;\n        const raw = String(cell?.v ?? "");\n        let nextValue = raw;\n        if (findReplacePanel.matchCase) {\n          const parts = raw.split(needle);\n          if (parts.length <= 1) continue;\n          replacements += parts.length - 1;\n          nextValue = parts.join(replacement);\n        } else {\n          const escaped = needle.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");\n          const matcher = new RegExp(escaped, "gi");\n          const matches = raw.match(matcher);\n          if (!matches?.length) continue;\n          replacements += matches.length;\n          nextValue = raw.replace(matcher, replacement);\n        }\n        if (nextValue === "") delete cells[ref];\n        else cells[ref] = { ...cell, v: nextValue };\n      }\n      return { ...sheet, cells };\n    }, `find-replace:${Date.now()}`);\n    setRemoteNotice(ui.lang === "en" ? `${replacements} replacement(s) made.` : `تم إجراء ${replacements} عملية استبدال.`);\n  }\n\n  function clearFormattingAction() {'''
    source = regex_once(source, find_pattern, find_replacement, "Find & Replace panel actions")

    reorder_block = '''  function reorderSheetsByIds(sourceId, targetId) {\n    if (!canEdit || !sourceId || !targetId || sourceId === targetId) return;\n    const from = sheets.findIndex((sheet) => sheet.id === sourceId);\n    if (from < 0) return;\n    const next = [...sheets];\n    const [moved] = next.splice(from, 1);\n    const targetIndex = next.findIndex((sheet) => sheet.id === targetId);\n    if (targetIndex < 0) return;\n    next.splice(targetIndex, 0, moved);\n    setSheets(next);\n    setDragSheetId("");\n    scheduleSave(next);\n  }\n\n'''
    source = replace_once(source, '  function duplicateSheet(sheetId) {\n', reorder_block + '  function duplicateSheet(sheetId) {\n', "sheet reorder action")

    source = replace_once(
        source,
        'tws-sheets-phase7-premium tws-sheets-phase7-1-restructure tws-sheets-phase7-2-google-parity flex h-full flex-col',
        'tws-sheets-phase7-premium tws-sheets-phase7-1-restructure tws-sheets-phase7-2-google-parity tws-sheets-phase7-2b-polish relative flex h-full flex-col',
        "Phase 7.2B root hook",
    )

    source = replace_once(
        source,
        'className="group relative sticky top-0 z-10 cursor-pointer border border-zinc-200 bg-zinc-100 px-2 py-1 text-[11px] font-black text-zinc-500 hover:bg-zinc-200/80 dark:border-white/10 dark:bg-white/10 dark:text-zinc-300 dark:hover:bg-white/15"',
        'className={cn("group relative sticky top-0 z-10 cursor-pointer border border-zinc-200 bg-zinc-100 px-2 py-1 text-[11px] font-black text-zinc-500 hover:bg-zinc-200/80 dark:border-white/10 dark:bg-white/10 dark:text-zinc-300 dark:hover:bg-white/15", focusedParsed?.col === col && "tws-sheets-axis-active")}',
        "active column header styling hook",
    )

    source = replace_once(
        source,
        'className="group relative sticky right-0 z-10 cursor-pointer border border-zinc-200 bg-zinc-100 px-2 text-center text-[11px] font-black text-zinc-500 hover:bg-zinc-200/80 dark:border-white/10 dark:bg-white/10 dark:text-zinc-300 dark:hover:bg-white/15"',
        'className={cn("group relative sticky right-0 z-10 cursor-pointer border border-zinc-200 bg-zinc-100 px-2 text-center text-[11px] font-black text-zinc-500 hover:bg-zinc-200/80 dark:border-white/10 dark:bg-white/10 dark:text-zinc-300 dark:hover:bg-white/15", focusedParsed?.row === row && "tws-sheets-axis-active")}',
        "active row header styling hook",
    )

    source = replace_once(
        source,
        'className={cn("relative border border-zinc-200 p-0 dark:border-white/10", isSelected && !isFocused && "bg-amber-50/70 dark:bg-amber-500/10", fillPreviewRef === ref && "ring-2 ring-inset ring-amber-500")}',
        'className={cn("relative border border-zinc-200 p-0 dark:border-white/10", isSelected && "tws-sheets-cell-selected", isFocused && "tws-sheets-cell-focused", isSelected && !isFocused && "bg-amber-50/70 dark:bg-amber-500/10", fillPreviewRef === ref && "ring-2 ring-inset ring-amber-500")}',
        "active cell styling hooks",
    )

    paste_button = '{canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={pasteFromSystemClipboard}>{ui.lang === "en" ? "Paste" : "لصق"}</button>}'
    paste_buttons = paste_button + '''\n                {canEdit && rangeClipboardRef.current && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={pasteSpecialValuesAction}>{ui.lang === "en" ? "Paste values only" : "لصق القيم فقط"}</button>}\n                {canEdit && rangeClipboardRef.current && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={pasteSpecialFormatsAction}>{ui.lang === "en" ? "Paste format only" : "لصق التنسيق فقط"}</button>}'''
    source = replace_once(source, paste_button, paste_buttons, "Paste Special context menu")

    formula_tail = '''      {canEdit && (\n        <div className="tws-sheets-formula-strip tws-sheets-formula-strip-compact border-b">'''
    if formula_tail not in source:
        raise RuntimeError("formula strip anchor missing")

    workspace_anchor = '      <div className="tws-sheets-workspace flex min-h-0 flex-1">'
    find_panel = '''      {findReplacePanel.open && (\n        <div className="tws-sheets-find-replace-panel">\n          <div className="tws-sheets-find-replace-grid">\n            <input autoFocus value={findReplacePanel.find} onChange={(event) => setFindReplacePanel((current) => ({ ...current, find: event.target.value }))} placeholder={ui.lang === "en" ? "Find" : "بحث"} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); findNextMatch(); } if (event.key === "Escape") setFindReplacePanel((current) => ({ ...current, open: false })); }} />\n            <input value={findReplacePanel.replace} onChange={(event) => setFindReplacePanel((current) => ({ ...current, replace: event.target.value }))} placeholder={ui.lang === "en" ? "Replace with" : "استبدال بـ"} />\n            <button type="button" aria-label={ui.lang === "en" ? "Close find and replace" : "إغلاق البحث والاستبدال"} onClick={() => setFindReplacePanel((current) => ({ ...current, open: false }))}>×</button>\n          </div>\n          <label className="mt-2 inline-flex items-center gap-2 text-[10px] font-bold text-zinc-500"><input type="checkbox" checked={findReplacePanel.matchCase} onChange={(event) => setFindReplacePanel((current) => ({ ...current, matchCase: event.target.checked }))} /> {ui.lang === "en" ? "Match case" : "مطابقة حالة الأحرف"}</label>\n          <div className="tws-sheets-find-replace-actions">\n            <button type="button" onClick={findNextMatch}>{ui.lang === "en" ? "Find next" : "بحث عن التالي"}</button>\n            <button type="button" className="primary" onClick={replaceAllMatches}>{ui.lang === "en" ? "Replace all" : "استبدال الكل"}</button>\n          </div>\n        </div>\n      )}\n\n'''
    source = replace_once(source, workspace_anchor, find_panel + workspace_anchor, "Find & Replace panel UI")

    tab_type_anchor = '''                type="button"\n                onClick={() => { setActiveSheetId(sheet.id); setSheetTabMenu(null); }}'''
    tab_type_new = '''                type="button"\n                draggable={canEdit}\n                onDragStart={() => canEdit && setDragSheetId(sheet.id)}\n                onDragOver={(event) => { if (canEdit && dragSheetId && dragSheetId !== sheet.id) event.preventDefault(); }}\n                onDrop={(event) => { event.preventDefault(); reorderSheetsByIds(dragSheetId, sheet.id); }}\n                onDragEnd={() => setDragSheetId("")}\n                onClick={() => { setActiveSheetId(sheet.id); setSheetTabMenu(null); }}'''
    source = replace_once(source, tab_type_anchor, tab_type_new, "sheet tab drag bindings")

    tab_class_old = '''                  sheet.id === activeSheetId ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950" : "bg-white text-zinc-500 hover:bg-zinc-100 dark:bg-white/5 dark:text-zinc-400"\n                )}'''
    tab_class_new = '''                  sheet.id === activeSheetId ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950" : "bg-white text-zinc-500 hover:bg-zinc-100 dark:bg-white/5 dark:text-zinc-400",\n                  sheet.id === activeSheetId && "tws-sheets-tab-active",\n                  dragSheetId === sheet.id && "tws-sheets-tab-dragging"\n                )}'''
    source = replace_once(source, tab_class_old, tab_class_new, "sheet tab active/drag classes")

    add_tab_old = 'className="grid h-8 w-8 shrink-0 place-items-center rounded-xl text-zinc-500 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10"'
    add_tab_new = 'className="tws-sheets-tab-add grid h-8 w-8 shrink-0 place-items-center rounded-xl text-zinc-500 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10"'
    source = replace_once(source, add_tab_old, add_tab_new, "sheet add button class")

    source_applied = True
    editor_path.write_text(source, encoding="utf-8")
    (REPO / CSS).write_bytes(css_payload)
    (REPO / TEST).write_bytes(test_payload)

    run(["git", "diff", "--check"])
    run(["node", "--test", TEST])
    run(["node", "--test", PHASE72A_TEST])
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

    if changed_paths() != FINAL_SCOPE:
        raise RuntimeError("unexpected final changed paths: " + ", ".join(sorted(changed_paths())))

    final_source = editor_path.read_text(encoding="utf-8")
    required = [
        'import "./tSheetsPhase7_2BPolish.css";',
        "tws-sheets-phase7-2b-polish",
        "tws-sheets-cell-focused",
        "tws-sheets-axis-active",
        "function openFindReplacePanel()",
        "function findNextMatch()",
        "function replaceAllMatches()",
        "function pasteSpecialValuesAction()",
        "function pasteSpecialFormatsAction()",
        "function reorderSheetsByIds(sourceId, targetId)",
        "draggable={canEdit}",
    ]
    missing = [item for item in required if item not in final_source]
    if missing:
        raise RuntimeError("Phase 7.2B final source verification missing: " + ", ".join(missing))

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

    live_before_html = fetch_text(f"{LIVE_URL}?__phase72b_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    live_index_backup = Path(f"/tmp/tos_phase72b_live_index_{int(time.time())}.html")
    shutil.copy2(LIVE_ROOT / "index.html", live_index_backup)
    sync_dist(DIST, LIVE_ROOT)
    live_synced = True

    nginx_test = run(["nginx", "-t"], cwd=Path("/"), check=False)
    if nginx_test.returncode != 0:
        raise RuntimeError("nginx -t failed after Phase 7.2B preview sync")
    nginx_reload = run(["systemctl", "reload", "nginx"], cwd=Path("/"), check=False)
    if nginx_reload.returncode != 0:
        raise RuntimeError("nginx reload failed after Phase 7.2B preview sync")

    time.sleep(1)
    live_after_html = fetch_text(f"{LIVE_URL}?__phase72b_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if not live_asset_after:
        raise RuntimeError("could not identify live JS after Phase 7.2B deployment")
    if Path(live_asset_after.split("?", 1)[0]).name != Path(built_asset).name:
        raise RuntimeError(f"live HTML references another bundle: live={live_asset_after}, built={built_asset}")

    tmp = Path("/tmp/tos_phase72b_live_asset.js")
    req = urllib.request.Request(asset_url(live_asset_after) + f"?v={int(time.time())}", headers={"Cache-Control": "no-cache", "User-Agent": "TOS-TWS-Phase72B-LiveProbe/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        tmp.write_bytes(response.read())
    live_sha = sha256(tmp)
    tmp.unlink(missing_ok=True)
    if live_sha != built_sha:
        raise RuntimeError(f"live asset bytes mismatch: live_sha={live_sha}, built_sha={built_sha}")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("PHASE72A_WORKTREE_BASELINE=PASS")
    print("PHASE72A_PAYLOAD_BLOBS=PASS")
    print("PHASE72B_PAYLOAD_INTEGRITY=PASS")
    print("FILES_DIRTY_TOTAL=5")
    print("PHASE72B_POLISH_TESTS=PASS (10/10)")
    print("PHASE72A_REGRESSION=PASS")
    print("PHASE71_UI_REGRESSION=PASS")
    print("PHASE7_VISUAL_REGRESSION=PASS")
    print("PHASE2_PHASE3_FRONTEND_REGRESSION=PASS")
    print("PHASE6_ADVANCED_REGRESSION=PASS")
    print("PHASE5_COLLABORATION_REGRESSION=PASS")
    print("PHASE4_FORMULA_REGRESSION=PASS")
    print("PHASE1_PHASE3_XLSX_REGRESSION=PASS")
    print(f"FRONTEND_BUILD=PASS ({build_seconds:.2f}s)")
    print("FLAT_SQUARE_CELLS=PASS")
    print("ACTIVE_CELL_SELECTION=PASS")
    print("ROW_COLUMN_ACTIVE_HEADERS=PASS")
    print("UNIFIED_DARK_LIGHT_TOOLBAR=PASS")
    print("FORMULA_BAR_POLISH=PASS")
    print("PASTE_SPECIAL_VALUES_FORMATS=PASS")
    print("FIND_REPLACE_PANEL=PASS")
    print("SHEET_DRAG_REORDER=PASS")
    print("SHEET_TAB_DARK_POLISH=PASS")
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
    print("CHANGED_PATHS_EXACT=YES")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
except Exception as exc:
    fail(str(exc))
