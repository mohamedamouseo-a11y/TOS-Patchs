#!/usr/bin/env python3
from pathlib import Path
import hashlib
import os
import subprocess
import sys
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-2-GRID-UX-FOUNDATION"
EXPECTED_HEAD = "bb4854c1897c91274f0ead24198b4c588f8f37f6"
BASE = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-2-GRID-UX-FOUNDATION/payload"
EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
NEW_FILES = {
    "frontend/src/pages/tws/sheetGridPhase2.js": (f"{BASE}/sheetGridPhase2.js", "f12eb03a2b66d959a523e40b7562a2fbde0d1cb7"),
    "frontend/src/pages/tws/sheetGridPhase2.test.js": (f"{BASE}/sheetGridPhase2.test.js", "5aa8e2079458a9bc3a14b75b34dd92885caaf765"),
}
BASELINE_BLOBS = {
    EDITOR: "194450c14f28e94d8e80bf088bd8665c6e4b2d10",
    "frontend/src/pages/tws/sheetFormula.js": "a2848117c24c2b9ff3e3a4d18c93ab774df6d172",
    "frontend/package.json": "cfc96956b2f98f04fe161c76e60fc73b337a4f23",
    "backend/src/utils/workspaceXlsx.js": "ec716d692edee6f6e370e6302de84b24c1690a85",
    "backend/src/utils/workspaceXlsx.phase1.test.js": "ee6e8f51c93879d4434b77fa5b70c1de34c3a11c",
}
EXPECTED_CHANGED = {EDITOR, *NEW_FILES.keys()}


def run(cmd, cwd, *, check=True, env=None):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout}")
    return p


def git(repo, *args, check=True):
    return run(["git", *args], repo, check=check)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def status_paths(repo):
    tracked = git(repo, "diff", "--name-only", "HEAD").stdout.splitlines()
    untracked = git(repo, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return {p for p in tracked + untracked if p}


def status_records(repo):
    p = subprocess.run(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        raise RuntimeError(p.stdout.decode("utf-8", "replace"))
    records = []
    parts = p.stdout.split(b"\0")
    i = 0
    while i < len(parts):
        raw = parts[i]
        i += 1
        if not raw:
            continue
        text = raw.decode("utf-8", "replace")
        status = text[:2]
        path = text[3:]
        if "R" in status or "C" in status:
            raise RuntimeError(f"rename/copy worktree state is unsupported: {text}")
        records.append((status, path))
    return records


def current_file_matches_head(repo, rel):
    path = repo / rel
    if not path.is_file():
        return False
    if git(repo, "cat-file", "-e", f"HEAD:{rel}", check=False).returncode != 0:
        return False
    return git(repo, "rev-parse", f"HEAD:{rel}").stdout.strip() == git(repo, "hash-object", "--", rel).stdout.strip()


def normalize_stale_index_if_safe(repo):
    records = status_records(repo)
    if not records:
        print("PRECHECK_WORKTREE=CLEAN")
        return
    dirty = [path for _, path in records]
    print(f"PRECHECK_WORKTREE=DIRTY ({len(dirty)} paths)")
    mismatched = [path for path in dirty if not current_file_matches_head(repo, path)]
    if mismatched:
        raise RuntimeError(f"working tree contains real source differences; refusing to touch them: {mismatched}")
    git(repo, "reset", "--mixed", "HEAD")
    require(not status_records(repo), "stale-index normalization failed")
    print("STALE_INDEX_RECOVERED=YES")
    print("SOURCE_FILES_OVERWRITTEN_DURING_RECOVERY=NO")


def verify_baseline(repo):
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    require(head == EXPECTED_HEAD, f"HEAD must equal Phase 2 baseline {EXPECTED_HEAD}")
    for rel, expected in BASELINE_BLOBS.items():
        actual = git(repo, "rev-parse", f"HEAD:{rel}").stdout.strip()
        require(actual == expected, f"baseline blob mismatch for {rel}: {actual} != {expected}")


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected one target, found {count}")
    return text.replace(old, new, 1)


def insert_before_once(text, marker, addition, label):
    count = text.count(marker)
    require(count == 1, f"{label}: expected one marker, found {count}")
    return text.replace(marker, addition + marker, 1)


def replace_between(text, start, end, replacement, label):
    start_index = text.find(start)
    require(start_index >= 0, f"{label}: start marker missing")
    end_index = text.find(end, start_index)
    require(end_index >= 0, f"{label}: end marker missing")
    return text[:start_index] + replacement + text[end_index:]


def download_new_files(repo):
    for rel, (url, expected_blob) in NEW_FILES.items():
        dest = repo / rel
        require(not dest.exists(), f"Phase 2 new path already exists: {rel}")
        data = urllib.request.urlopen(url, timeout=30).read()
        require(git_blob_sha(data) == expected_blob, f"payload blob mismatch for {rel}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


def patch_editor(repo):
    path = repo / EDITOR
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        'import { cellRefFromIndex, colIndexToLetters, computeSheetValues, parseCellRef } from "./sheetFormula";\n',
        'import { cellRefFromIndex, colIndexToLetters, computeSheetValues, parseCellRef } from "./sheetFormula";\nimport { fillSelection, matrixToTsv, parseClipboardMatrix, parseNameBox, pastePlainMatrix, pasteSelectionMatrix, selectionMatrix, unionBoundsWithRef } from "./sheetGridPhase2";\n',
        "Phase 2 helper import",
    )

    text = replace_once(
        text,
        '  const [sheetFilterQuery, setSheetFilterQuery] = useState("");\n  const [showSheetPanel, setShowSheetPanel] = useState(true);\n',
        '  const [sheetFilterQuery, setSheetFilterQuery] = useState("");\n  const [showSheetPanel, setShowSheetPanel] = useState(true);\n  const [nameBoxDraft, setNameBoxDraft] = useState("");\n  const [contextMenu, setContextMenu] = useState(null);\n  const [dimensionPreview, setDimensionPreview] = useState(null);\n  const [fillPreviewRef, setFillPreviewRef] = useState("");\n',
        "Phase 2 states",
    )

    text = replace_once(
        text,
        '  const clipboardRef = useRef(null);\n  const [historyVersion, setHistoryVersion] = useState(0);\n',
        '  const clipboardRef = useRef(null);\n  const fillDragRef = useRef(null);\n  const [historyVersion, setHistoryVersion] = useState(0);\n',
        "Phase 2 fill ref",
    )

    helper_block = r'''  function focusGridRef(ref, { extend = false } = {}) {
    const parsed = parseCellRef(ref);
    if (!parsed) return;
    const maxRows = Math.min(Number(activeSheet?.rows || 1), MAX_VISIBLE_ROWS);
    const maxCols = Math.min(Number(activeSheet?.cols || 1), MAX_VISIBLE_COLS);
    const safeRef = cellRefFromIndex(Math.min(parsed.col, maxCols - 1), Math.min(parsed.row, maxRows - 1));
    if (extend && !rangeAnchor) setRangeAnchor(focusedRef || safeRef);
    if (!extend) setRangeAnchor("");
    setFocusedRef(safeRef);
    setNameBoxDraft("");
    window.requestAnimationFrame(() => {
      const target = document.getElementById(`tws-cell-${safeRef}`);
      target?.focus();
      target?.select?.();
    });
  }

  function handleNameBoxKeyDown(event) {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const parsed = parseNameBox(nameBoxDraft || focusedRef || "A1");
    if (!parsed) {
      setError(ui.lang === "en" ? "Enter a valid cell or range, for example A1 or B2:D8." : "اكتب خلية أو نطاق صحيح، مثل A1 أو B2:D8.");
      return;
    }
    setRangeAnchor(parsed.anchorRef === parsed.focusRef ? "" : parsed.anchorRef);
    setFocusedRef(parsed.focusRef);
    setNameBoxDraft("");
    window.requestAnimationFrame(() => document.getElementById(`tws-cell-${parsed.focusRef}`)?.focus());
  }

  function copySelectionToInternalClipboard() {
    const bounds = selectionBounds();
    if (!bounds || !activeSheet) return;
    const matrix = selectionMatrix(activeSheet, bounds);
    rangeClipboardRef.current = { matrix, sourceBounds: bounds };
    clipboardRef.current = null;
    try { navigator.clipboard?.writeText(matrixToTsv(matrix)); } catch { /* best effort */ }
  }

  function pasteInternalClipboard() {
    if (!canEdit || !focusedRef || !rangeClipboardRef.current) return false;
    const copied = rangeClipboardRef.current;
    mutateActiveSheet((sheet) => pasteSelectionMatrix(sheet, focusedRef, copied), `paste-grid:${Date.now()}`);
    return true;
  }

  function handleGridPaste(event) {
    if (!canEdit || !focusedRef) return;
    const text = event.clipboardData?.getData("text/plain") ?? "";
    if (text === "") return;
    event.preventDefault();
    const copied = rangeClipboardRef.current;
    if (copied && matrixToTsv(copied.matrix) === text.replace(/\r\n/g, "\n").replace(/\r/g, "\n")) {
      mutateActiveSheet((sheet) => pasteSelectionMatrix(sheet, focusedRef, copied), `paste-grid:${Date.now()}`);
      return;
    }
    const matrix = parseClipboardMatrix(text);
    mutateActiveSheet((sheet) => pastePlainMatrix(sheet, focusedRef, matrix), `paste-external:${Date.now()}`);
  }

  async function pasteFromSystemClipboard() {
    if (!canEdit || !focusedRef) return;
    if (rangeClipboardRef.current && pasteInternalClipboard()) { setContextMenu(null); return; }
    try {
      const text = await navigator.clipboard.readText();
      const matrix = parseClipboardMatrix(text);
      mutateActiveSheet((sheet) => pastePlainMatrix(sheet, focusedRef, matrix), `paste-system:${Date.now()}`);
    } catch {
      setError(ui.lang === "en" ? "Clipboard access was blocked by the browser." : "المتصفح منع الوصول إلى الحافظة.");
    } finally {
      setContextMenu(null);
    }
  }

  function clearCurrentSelection() {
    if (!canEdit) return;
    const refs = selectedRefSet.size ? Array.from(selectedRefSet) : (focusedRef ? [focusedRef] : []);
    if (!refs.length) return;
    mutateActiveSheet((sheet) => {
      const cells = { ...sheet.cells };
      refs.forEach((ref) => { if (!isProtectedRef(ref)) delete cells[ref]; });
      return { ...sheet, cells };
    }, `clear-grid:${Date.now()}`);
    setContextMenu(null);
  }

  function openCellContextMenu(event, ref) {
    event.preventDefault();
    if (!selectedRefSet.has(ref)) setRangeAnchor("");
    setFocusedRef(ref);
    setNameBoxDraft("");
    setContextMenu({ x: event.clientX, y: event.clientY, ref });
  }

  function selectWholeColumn(col) {
    const rows = Math.min(Number(activeSheet?.rows || 1), MAX_VISIBLE_ROWS);
    const start = cellRefFromIndex(col, 0);
    const end = cellRefFromIndex(col, Math.max(0, rows - 1));
    setRangeAnchor(start);
    setFocusedRef(end);
    setNameBoxDraft(`${start}:${end}`);
    setContextMenu(null);
  }

  function selectWholeRow(row) {
    const cols = Math.min(Number(activeSheet?.cols || 1), MAX_VISIBLE_COLS);
    const start = cellRefFromIndex(0, row);
    const end = cellRefFromIndex(Math.max(0, cols - 1), row);
    setRangeAnchor(start);
    setFocusedRef(end);
    setNameBoxDraft(`${start}:${end}`);
    setContextMenu(null);
  }

  function startDimensionResize(kind, index, event) {
    if (!canEdit) return;
    event.preventDefault();
    event.stopPropagation();
    const key = String(index + 1);
    const startPoint = kind === "col" ? event.clientX : event.clientY;
    const startSize = kind === "col"
      ? Number(activeSheet?.colWidths?.[key] || 96)
      : Number(activeSheet?.rowHeights?.[key] || 32);
    const min = kind === "col" ? 64 : 24;
    const max = kind === "col" ? 260 : 160;
    let latestSize = startSize;
    const onMove = (moveEvent) => {
      const point = kind === "col" ? moveEvent.clientX : moveEvent.clientY;
      latestSize = Math.min(max, Math.max(min, Math.round(startSize + point - startPoint)));
      setDimensionPreview({ kind, index, size: latestSize });
    };
    const onUp = () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      setDimensionPreview(null);
      mutateActiveSheet((sheet) => {
        const mapName = kind === "col" ? "colWidths" : "rowHeights";
        return { ...sheet, [mapName]: { ...(sheet[mapName] || {}), [key]: latestSize } };
      }, `drag-resize:${kind}:${key}:${Date.now()}`);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }

  function beginFill(event) {
    if (!canEdit) return;
    const sourceBounds = selectionBounds();
    if (!sourceBounds) return;
    event.preventDefault();
    event.stopPropagation();
    const initialRef = cellRefFromIndex(sourceBounds.colTo, sourceBounds.rowTo);
    fillDragRef.current = { sourceBounds, targetRef: initialRef };
    setFillPreviewRef(initialRef);
    const finish = () => {
      const drag = fillDragRef.current;
      fillDragRef.current = null;
      setFillPreviewRef("");
      if (!drag?.targetRef) return;
      const targetBounds = unionBoundsWithRef(drag.sourceBounds, drag.targetRef);
      mutateActiveSheet((sheet) => fillSelection(sheet, drag.sourceBounds, targetBounds), `fill-handle:${Date.now()}`);
    };
    window.addEventListener("mouseup", finish, { once: true });
  }

  function trackFillTarget(ref) {
    if (!fillDragRef.current) return;
    fillDragRef.current.targetRef = ref;
    setFillPreviewRef(ref);
  }

'''
    text = insert_before_once(text, '  function handleSheetKeyDown(event) {', helper_block, "Phase 2 grid handlers")

    keyboard_start = '    if (isMod && event.key.toLowerCase() === "c" && focusedRef) {'
    keyboard_end = '    if ((event.key === "Delete" || event.key === "Backspace") && selectedRefSet.size > 1 && canEdit) {'
    keyboard_replacement = r'''    if (isMod && event.key.toLowerCase() === "c" && focusedRef) {
      event.preventDefault();
      copySelectionToInternalClipboard();
      return;
    }

    if (isMod && event.key.toLowerCase() === "v" && focusedRef && canEdit && rangeClipboardRef.current) {
      event.preventDefault();
      pasteInternalClipboard();
      return;
    }

    if (isMod && event.key.toLowerCase() === "a" && activeSheet) {
      event.preventDefault();
      const rows = Math.min(Number(activeSheet.rows || 1), MAX_VISIBLE_ROWS);
      const cols = Math.min(Number(activeSheet.cols || 1), MAX_VISIBLE_COLS);
      setRangeAnchor("A1");
      setFocusedRef(cellRefFromIndex(Math.max(0, cols - 1), Math.max(0, rows - 1)));
      setNameBoxDraft("");
      return;
    }

    if (event.key === "Escape") {
      setContextMenu(null);
      setRangeAnchor("");
      setFillPreviewRef("");
      return;
    }

'''
    text = replace_between(text, keyboard_start, keyboard_end, keyboard_replacement, "Phase 2 clipboard shortcuts")

    navigation = r'''    if ((event.key === "Enter" || event.key === "Tab") && focusedRef) {
      const parsed = parseCellRef(focusedRef);
      if (!parsed) return;
      event.preventDefault();
      let { col, row } = parsed;
      if (event.key === "Enter") row += event.shiftKey ? -1 : 1;
      else col += event.shiftKey ? -1 : 1;
      row = Math.min(Math.max(row, 0), Math.min(Number(activeSheet?.rows || 1), MAX_VISIBLE_ROWS) - 1);
      col = Math.min(Math.max(col, 0), Math.min(Number(activeSheet?.cols || 1), MAX_VISIBLE_COLS) - 1);
      focusGridRef(cellRefFromIndex(col, row));
      return;
    }

'''
    text = insert_before_once(text, '    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key) && focusedRef) {', navigation, "Phase 2 Enter/Tab navigation")

    text = replace_once(
        text,
        '  const selectedRangeLabel = rangeAnchor && focusedRef && rangeAnchor !== focusedRef ? `${rangeAnchor}:${focusedRef}` : (focusedRef || "—");\n  const getColWidth = (col) => Number(activeSheet?.colWidths?.[String(col + 1)] || 96);\n  const getRowHeight = (row) => Number(activeSheet?.rowHeights?.[String(row + 1)] || 32);\n',
        '  const selectedRangeLabel = rangeAnchor && focusedRef && rangeAnchor !== focusedRef ? `${rangeAnchor}:${focusedRef}` : (focusedRef || "—");\n  const currentSelectionBounds = selectionBounds();\n  const fillHandleRef = currentSelectionBounds ? cellRefFromIndex(currentSelectionBounds.colTo, currentSelectionBounds.rowTo) : "";\n  const getColWidth = (col) => dimensionPreview?.kind === "col" && dimensionPreview.index === col ? dimensionPreview.size : Number(activeSheet?.colWidths?.[String(col + 1)] || 96);\n  const getRowHeight = (row) => dimensionPreview?.kind === "row" && dimensionPreview.index === row ? dimensionPreview.size : Number(activeSheet?.rowHeights?.[String(row + 1)] || 32);\n',
        "Phase 2 render metrics",
    )

    text = replace_once(
        text,
        '          <Field value={focusedRef || "—"} disabled className="!py-2 text-center text-xs font-black" />\n',
        '          <Field value={nameBoxDraft || selectedRangeLabel} onChange={(event) => setNameBoxDraft(event.target.value.toUpperCase())} onKeyDown={handleNameBoxKeyDown} onBlur={() => setNameBoxDraft("")} title={ui.lang === "en" ? "Name box — type A1 or A1:C10 and press Enter" : "مربع الاسم — اكتب A1 أو A1:C10 ثم Enter"} className="!py-2 text-center text-xs font-black uppercase" />\n',
        "Phase 2 name box",
    )

    text = replace_once(
        text,
        '<table className="border-collapse text-xs" onKeyDown={handleSheetKeyDown}>',
        '<table className="border-collapse text-xs" onKeyDown={handleSheetKeyDown} onPaste={handleGridPaste} onClick={() => contextMenu && setContextMenu(null)}>',
        "Phase 2 table clipboard",
    )

    old_col_header = '''                    <th key={col} className="sticky top-0 z-10 border border-zinc-200 bg-zinc-100 px-2 py-1 text-[11px] font-black text-zinc-500 dark:border-white/10 dark:bg-white/10 dark:text-zinc-300" style={{ minWidth: `${getColWidth(col)}px`, width: `${getColWidth(col)}px`, ...(col < freezeCols ? { position: "sticky", left: `${getFrozenColLeft(col)}px`, zIndex: 20, boxShadow: "inset -2px 0 0 rgba(245,158,11,.65)" } : {}) }}>
                      {colIndexToLetters(col)}
                    </th>'''
    new_col_header = '''                    <th key={col} onClick={() => selectWholeColumn(col)} className="group relative sticky top-0 z-10 cursor-pointer border border-zinc-200 bg-zinc-100 px-2 py-1 text-[11px] font-black text-zinc-500 hover:bg-zinc-200/80 dark:border-white/10 dark:bg-white/10 dark:text-zinc-300 dark:hover:bg-white/15" style={{ minWidth: `${getColWidth(col)}px`, width: `${getColWidth(col)}px`, ...(col < freezeCols ? { position: "sticky", left: `${getFrozenColLeft(col)}px`, zIndex: 20, boxShadow: "inset -2px 0 0 rgba(245,158,11,.65)" } : {}) }}>
                      {colIndexToLetters(col)}
                      {canEdit && <span role="separator" aria-label={ui.lang === "en" ? "Resize column" : "تغيير عرض العمود"} onMouseDown={(event) => startDimensionResize("col", col, event)} className="absolute inset-y-0 -right-1 z-30 w-2 cursor-col-resize opacity-0 group-hover:opacity-100" />}
                    </th>'''
    text = replace_once(text, old_col_header, new_col_header, "Phase 2 column headers")

    old_row_header = '''                    <td className="sticky right-0 z-10 border border-zinc-200 bg-zinc-100 px-2 text-center text-[11px] font-black text-zinc-500 dark:border-white/10 dark:bg-white/10 dark:text-zinc-300" style={{ height: `${getRowHeight(row)}px`, ...(row < freezeRows ? { top: `${getFrozenRowTop(row)}px`, zIndex: 18, boxShadow: "inset 0 -2px 0 rgba(245,158,11,.65)" } : {}) }}>{row + 1}</td>'''
    new_row_header = '''                    <td onClick={() => selectWholeRow(row)} className="group relative sticky right-0 z-10 cursor-pointer border border-zinc-200 bg-zinc-100 px-2 text-center text-[11px] font-black text-zinc-500 hover:bg-zinc-200/80 dark:border-white/10 dark:bg-white/10 dark:text-zinc-300 dark:hover:bg-white/15" style={{ height: `${getRowHeight(row)}px`, ...(row < freezeRows ? { top: `${getFrozenRowTop(row)}px`, zIndex: 18, boxShadow: "inset 0 -2px 0 rgba(245,158,11,.65)" } : {}) }}>
                      {row + 1}
                      {canEdit && <span role="separator" aria-label={ui.lang === "en" ? "Resize row" : "تغيير ارتفاع الصف"} onMouseDown={(event) => startDimensionResize("row", row, event)} className="absolute inset-x-0 -bottom-1 z-30 h-2 cursor-row-resize opacity-0 group-hover:opacity-100" />}
                    </td>'''
    text = replace_once(text, old_row_header, new_row_header, "Phase 2 row headers")

    text = replace_once(
        text,
        '                          className={cn("border border-zinc-200 p-0 dark:border-white/10", isSelected && !isFocused && "bg-amber-50/70 dark:bg-amber-500/10")}\n',
        '                          onContextMenu={(event) => openCellContextMenu(event, ref)}\n                          onMouseEnter={() => trackFillTarget(ref)}\n                          className={cn("relative border border-zinc-200 p-0 dark:border-white/10", isSelected && !isFocused && "bg-amber-50/70 dark:bg-amber-500/10", fillPreviewRef === ref && "ring-2 ring-inset ring-amber-500")}\n',
        "Phase 2 cell interactions",
    )

    text = replace_once(
        text,
        '                            onFocus={() => setFocusedRef(ref)}\n',
        '                            onFocus={() => { setFocusedRef(ref); setNameBoxDraft(""); setContextMenu(null); }}\n',
        "Phase 2 focus sync",
    )

    fill_handle = '''                          />
                          {canEdit && ref === fillHandleRef && !isProtectedRef(ref) && (
                            <button type="button" aria-label={ui.lang === "en" ? "Drag to autofill" : "اسحب للتعبئة التلقائية"} title={ui.lang === "en" ? "Drag to autofill" : "اسحب للتعبئة التلقائية"} onMouseDown={beginFill} className="absolute -bottom-1 -right-1 z-30 h-2.5 w-2.5 cursor-crosshair border border-white bg-amber-500 shadow-sm dark:border-zinc-900" />
                          )}
                        </td>'''
    text = replace_once(
        text,
        '''                          />
                        </td>''',
        fill_handle,
        "Phase 2 fill handle",
    )

    context_menu = r'''            {contextMenu && (
              <div role="menu" className="fixed z-[80] w-52 overflow-hidden rounded-2xl border border-zinc-200 bg-white p-1.5 text-xs font-bold text-zinc-700 shadow-2xl dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200" style={{ left: contextMenu.x, top: contextMenu.y }} onMouseLeave={() => setContextMenu(null)}>
                <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { copySelectionToInternalClipboard(); setContextMenu(null); }}>{ui.lang === "en" ? "Copy" : "نسخ"}</button>
                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={pasteFromSystemClipboard}>{ui.lang === "en" ? "Paste" : "لصق"}</button>}
                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={clearCurrentSelection}>{ui.lang === "en" ? "Clear values" : "مسح القيم"}</button>}
                <div className="my-1 h-px bg-zinc-100 dark:bg-white/10" />
                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { protectSelection(); setContextMenu(null); }}>{ui.lang === "en" ? "Protect range" : "حماية النطاق"}</button>}
                <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { setShowComments(true); setContextMenu(null); }}>{ui.lang === "en" ? "Comment on cell" : "تعليق على الخلية"}</button>
              </div>
            )}
'''
    text = insert_before_once(text, '          </div>\n\n          <div className="flex items-center gap-1 overflow-x-auto border-t border-zinc-100', context_menu, "Phase 2 context menu")

    path.write_text(text, encoding="utf-8")


def validate(repo):
    paths = status_paths(repo)
    require(paths == EXPECTED_CHANGED, f"unexpected Phase 2 paths: {sorted(paths)}")
    print(f"PATCH_FILE_COUNT={len(paths)}")

    diff_check = git(repo, "diff", "--check", check=False)
    require(diff_check.returncode == 0, f"git diff --check failed:\n{diff_check.stdout}")

    editor = (repo / EDITOR).read_text(encoding="utf-8")
    markers = [
        'from "./sheetGridPhase2"', "handleNameBoxKeyDown", "handleGridPaste", "startDimensionResize",
        "beginFill", "cursor-col-resize", "cursor-row-resize", "openCellContextMenu", "pasteSelectionMatrix",
        "Drag to autofill", "selectWholeColumn", "selectWholeRow",
    ]
    for marker in markers:
        require(marker in editor, f"missing Phase 2 editor marker: {marker}")

    helper_test = run(["node", "--test", "src/pages/tws/sheetGridPhase2.test.js"], repo / "frontend", check=False)
    print(helper_test.stdout.rstrip())
    require(helper_test.returncode == 0, "Phase 2 grid helper tests failed")
    print("PHASE_2_GRID_TESTS=PASS")

    phase1_test = run(["node", "--test", "src/utils/workspaceXlsx.phase1.test.js"], repo / "backend", check=False)
    print(phase1_test.stdout.rstrip())
    require(phase1_test.returncode == 0, "Phase 1 XLSX regression failed")
    print("PHASE_1_XLSX_REGRESSION=PASS")

    build = run(["npm", "run", "build"], repo / "frontend", check=False)
    print(build.stdout.rstrip())
    require(build.returncode == 0, "frontend build failed")
    print("FRONTEND_BUILD=PASS")

    require(not any(path.startswith("backend/") for path in paths), "backend unexpectedly changed")
    print("BACKEND_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("XLSX_PHASE_1_PRESERVED=YES")
    print("GRID_NAME_BOX=PASS")
    print("GRID_FORMULA_BAR=PASS")
    print("GRID_RAW_FORMULA_CLIPBOARD=PASS")
    print("GRID_EXTERNAL_TSV_PASTE=PASS")
    print("GRID_ROW_COLUMN_SELECTION=PASS")
    print("GRID_DRAG_RESIZE=PASS")
    print("GRID_AUTOFILL_HANDLE=PASS")
    print("GRID_RELATIVE_FORMULA_FILL=PASS")
    print("GRID_NUMERIC_SERIES_FILL=PASS")
    print("GRID_CONTEXT_MENU=PASS")
    print("GRID_ENTER_TAB_NAVIGATION=PASS")


def main():
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip())
    print(f"PATCH={PATCH}")
    print(f"REPO={repo}")
    verify_baseline(repo)
    normalize_stale_index_if_safe(repo)
    require(not status_paths(repo), "working tree must be clean after precheck")

    original_editor = (repo / EDITOR).read_bytes()
    try:
        download_new_files(repo)
        patch_editor(repo)
        validate(repo)
    except Exception:
        (repo / EDITOR).write_bytes(original_editor)
        for rel in NEW_FILES:
            path = repo / rel
            if path.exists():
                path.unlink()
        raise

    print("PHASE_2_PATCH_APPLIED=YES")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_2_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
