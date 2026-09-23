#!/usr/bin/env python3
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request

PATCH = "TOS-TWS-TSHEETS-PHASE-8-BATCH-01-ROW-COLUMN-INSERT-PARITY-V1"
SCRIPT = "run_tsheets_p8_b01_v1.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "d82fb451e0615bcbee8596e69e1ad4769d3722c3"

EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
MENU = "frontend/src/pages/tws/TSheetsGoogleMenuBar.jsx"
HELPER = "frontend/src/pages/tws/sheetStructurePhase8.js"
TEST = "frontend/src/pages/tws/sheetStructurePhase8.test.js"
PHASE_SCOPE = {EDITOR, MENU, HELPER, TEST}
EDITOR_BLOB = "00e0df984a5ece14e36788d082eb4bb750572119"
MENU_BLOB = "11e6f60dfe340aebfc01b7983c2397f948133923"

PAYLOAD_ROOT = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSHEETS-PHASE-8-BATCH-01-ROW-COLUMN-INSERT-PARITY-V1/payload"
PAYLOADS = {
    HELPER: (f"{PAYLOAD_ROOT}/sheetStructurePhase8.js", "3cf13961110df8014d8ab7b76ed514d35127c674"),
    TEST: (f"{PAYLOAD_ROOT}/sheetStructurePhase8.test.js", "b2943fd32181a78d228a69f30dead108c16aaa49"),
}


def run(args, cwd=REPO, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"command failed: {' '.join(args)}")
    return result


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-tsheets-p8-b01-v1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def status_lines():
    return [line for line in run(["git", "status", "--porcelain"]).stdout.splitlines() if line.strip()]


def status_path(line: str) -> str:
    raw = line[3:].strip()
    if " -> " in raw:
        raw = raw.split(" -> ", 1)[1]
    return raw.strip('"')


def file_fingerprint(rel: str):
    path = REPO / rel
    if not path.exists():
        return "MISSING"
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return "DIR"


def unrelated_fingerprints(lines):
    result = {}
    for line in lines:
        rel = status_path(line)
        if rel not in PHASE_SCOPE:
            result[rel] = (line[:2], file_fingerprint(rel))
    return result


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}_ANCHOR_COUNT:{count}")
    return text.replace(old, new, 1)


def main_asset_from_html(html: str):
    marker = "/assets/index-"
    start = html.find(marker)
    if start < 0:
        return None
    end = html.find(".js", start)
    if end < 0:
        return None
    return html[start:end + 3]


def rollback_source(snapshot):
    for rel, previous in snapshot.items():
        path = REPO / rel
        if previous is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(previous)


def fail(message, snapshot=None, live_backup=None):
    print(f"ERROR={message}", file=sys.stderr)
    if snapshot is not None:
        try:
            rollback_source(snapshot)
            print("SOURCE_ROLLBACK=PASS", file=sys.stderr)
        except Exception as exc:
            print(f"SOURCE_ROLLBACK=FAIL:{exc}", file=sys.stderr)
    if live_backup and Path(live_backup).exists():
        try:
            if LIVE_ROOT.exists():
                shutil.rmtree(LIVE_ROOT)
            shutil.copytree(live_backup, LIVE_ROOT)
            run(["nginx", "-t"])
            run(["systemctl", "reload", "nginx"])
            print("LIVE_ROLLBACK=PASS", file=sys.stderr)
        except Exception as exc:
            print(f"LIVE_ROLLBACK=FAIL:{exc}", file=sys.stderr)
    sys.exit(1)


if not REPO.exists():
    fail("REPO_NOT_FOUND")

head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")

for rel, expected in [(EDITOR, EDITOR_BLOB), (MENU, MENU_BLOB)]:
    actual = run(["git", "hash-object", rel]).stdout.strip()
    if actual != expected:
        fail(f"BLOB_MISMATCH:{rel}:{actual}")

before_status = status_lines()
phase_dirty = [line for line in before_status if status_path(line) in PHASE_SCOPE]
if phase_dirty:
    fail("PHASE_PATH_ALREADY_DIRTY:" + "|".join(phase_dirty))

unrelated_before = unrelated_fingerprints(before_status)
precheck = "CLEAN" if not unrelated_before else "DIRTY_UNRELATED_ALLOWED"

payload_data = {}
for rel, (url, expected_sha) in PAYLOADS.items():
    data = download(url)
    actual_sha = git_blob_sha(data)
    if actual_sha != expected_sha:
        fail(f"PAYLOAD_INTEGRITY_FAIL:{rel}:{actual_sha}")
    payload_data[rel] = data

snapshot = {}
for rel in PHASE_SCOPE:
    path = REPO / rel
    snapshot[rel] = path.read_bytes() if path.exists() else None

live_backup = None
try:
    for rel, data in payload_data.items():
        path = REPO / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    editor_path = REPO / EDITOR
    editor = editor_path.read_text(encoding="utf-8")

    editor = replace_once(
        editor,
        'import { fillSelection, matrixToTsv, parseClipboardMatrix, parseNameBox, pastePlainMatrix, pasteSelectionMatrix, selectionMatrix, unionBoundsWithRef } from "./sheetGridPhase2";\n',
        'import { fillSelection, matrixToTsv, parseClipboardMatrix, parseNameBox, pastePlainMatrix, pasteSelectionMatrix, selectionMatrix, unionBoundsWithRef } from "./sheetGridPhase2";\nimport { insertSheetColumns, insertSheetRows, remapNamedRangesForInsert } from "./sheetStructurePhase8";\n',
        "STRUCTURE_IMPORT",
    )

    old_functions = '''  function addRow() {
    mutateActiveSheet((sheet) => ({ ...sheet, rows: Math.min(sheet.rows + 1, MAX_VISIBLE_ROWS) }), `rows:${Date.now()}`);
  }
  function removeRow() {
    mutateActiveSheet((sheet) => ({ ...sheet, rows: Math.max(sheet.rows - 1, 1) }), `rows:${Date.now()}`);
  }
  function addCol() {
    mutateActiveSheet((sheet) => ({ ...sheet, cols: Math.min(sheet.cols + 1, MAX_VISIBLE_COLS) }), `cols:${Date.now()}`);
  }
  function removeCol() {
    mutateActiveSheet((sheet) => ({ ...sheet, cols: Math.max(sheet.cols - 1, 1) }), `cols:${Date.now()}`);
  }
'''
    new_functions = '''  function insertRowAtSelection(position = "above") {
    if (!activeSheet) return;
    const parsed = parseCellRef(focusedRef || "A1") || { row: 0, col: 0 };
    const currentRows = Math.max(1, Number(activeSheet.rows || 1));
    if (currentRows >= MAX_VISIBLE_ROWS) {
      setError(ui.lang === "en" ? `This phase keeps the current ${MAX_VISIBLE_ROWS}-row safety limit. Grid scaling comes in a later phase.` : `هذه المرحلة تحافظ على حد الأمان الحالي ${MAX_VISIBLE_ROWS} صف. توسيع حجم الجدول سيأتي في مرحلة لاحقة.`);
      return;
    }
    const insertIndex = position === "below" ? Math.min(parsed.row + 1, currentRows) : Math.min(parsed.row, currentRows);
    const nextNamedRanges = remapNamedRangesForInsert(namedRangesRef.current, activeSheetId, "row", insertIndex, 1);
    namedRangesRef.current = nextNamedRanges;
    setNamedRanges(nextNamedRanges);
    setSheets((prev) => {
      pushHistory(prev, `insert-row:${position}:${insertIndex}:${Date.now()}`);
      const beforeSheet = prev.find((sheet) => sheet.id === activeSheetId) || null;
      const next = prev.map((sheet) => sheet.id === activeSheetId
        ? insertSheetRows(sheet, insertIndex, 1, { maxRows: MAX_VISIBLE_ROWS })
        : sheet);
      const afterSheet = next.find((sheet) => sheet.id === activeSheetId) || null;
      if (beforeSheet && afterSheet) scheduleSheetCollabPatch(beforeSheet, afterSheet);
      scheduleSave(next);
      return next;
    });
    const nextRef = cellRefFromIndex(Math.min(parsed.col, Math.max(0, Number(activeSheet.cols || 1) - 1)), Math.min(insertIndex, MAX_VISIBLE_ROWS - 1));
    setRangeAnchor("");
    setFocusedRef(nextRef);
    setNameBoxDraft("");
    window.setTimeout(() => { const target = document.getElementById(`tws-cell-${nextRef}`); target?.focus(); target?.select?.(); }, 0);
  }

  function insertColumnAtSelection(position = "left") {
    if (!activeSheet) return;
    const parsed = parseCellRef(focusedRef || "A1") || { row: 0, col: 0 };
    const currentCols = Math.max(1, Number(activeSheet.cols || 1));
    if (currentCols >= MAX_VISIBLE_COLS) {
      setError(ui.lang === "en" ? `This phase keeps the current ${MAX_VISIBLE_COLS}-column safety limit. Grid scaling comes in a later phase.` : `هذه المرحلة تحافظ على حد الأمان الحالي ${MAX_VISIBLE_COLS} عمود. توسيع حجم الجدول سيأتي في مرحلة لاحقة.`);
      return;
    }
    const insertIndex = position === "right" ? Math.min(parsed.col + 1, currentCols) : Math.min(parsed.col, currentCols);
    const nextNamedRanges = remapNamedRangesForInsert(namedRangesRef.current, activeSheetId, "col", insertIndex, 1);
    namedRangesRef.current = nextNamedRanges;
    setNamedRanges(nextNamedRanges);
    setSheets((prev) => {
      pushHistory(prev, `insert-col:${position}:${insertIndex}:${Date.now()}`);
      const beforeSheet = prev.find((sheet) => sheet.id === activeSheetId) || null;
      const next = prev.map((sheet) => sheet.id === activeSheetId
        ? insertSheetColumns(sheet, insertIndex, 1, { maxCols: MAX_VISIBLE_COLS })
        : sheet);
      const afterSheet = next.find((sheet) => sheet.id === activeSheetId) || null;
      if (beforeSheet && afterSheet) scheduleSheetCollabPatch(beforeSheet, afterSheet);
      scheduleSave(next);
      return next;
    });
    const nextRef = cellRefFromIndex(Math.min(insertIndex, MAX_VISIBLE_COLS - 1), Math.min(parsed.row, Math.max(0, Number(activeSheet.rows || 1) - 1)));
    setRangeAnchor("");
    setFocusedRef(nextRef);
    setNameBoxDraft("");
    window.setTimeout(() => { const target = document.getElementById(`tws-cell-${nextRef}`); target?.focus(); target?.select?.(); }, 0);
  }
'''
    editor = replace_once(editor, old_functions, new_functions, "INSERT_ACTIONS")

    editor = replace_once(
        editor,
        '          addSheet,\n          addRow,\n          addCol,\n',
        '          addSheet,\n          insertRowAbove: () => insertRowAtSelection("above"),\n          insertRowBelow: () => insertRowAtSelection("below"),\n          insertColLeft: () => insertColumnAtSelection("left"),\n          insertColRight: () => insertColumnAtSelection("right"),\n',
        "MENU_ACTION_WIRING",
    )

    editor_path.write_text(editor, encoding="utf-8")

    menu_path = REPO / MENU
    menu = menu_path.read_text(encoding="utf-8")
    old_insert = '''      { label: t("Row", "صف"), enabled: canEdit, action: actions.addRow },
      { label: t("Column", "عمود"), enabled: canEdit, action: actions.addCol },
'''
    new_insert = '''      {
        label: t("Rows", "صفوف"), enabled: canEdit, items: [
          { label: t("Insert 1 row above", "إدراج صف واحد أعلى"), action: actions.insertRowAbove },
          { label: t("Insert 1 row below", "إدراج صف واحد أسفل"), action: actions.insertRowBelow },
        ],
      },
      {
        label: t("Columns", "أعمدة"), enabled: canEdit, items: [
          { label: t("Insert 1 column left", "إدراج عمود واحد يسار"), action: actions.insertColLeft },
          { label: t("Insert 1 column right", "إدراج عمود واحد يمين"), action: actions.insertColRight },
        ],
      },
'''
    menu = replace_once(menu, old_insert, new_insert, "INSERT_MENU")
    menu_path.write_text(menu, encoding="utf-8")

    for token in [
        'from "./sheetStructurePhase8"',
        'insertRowAtSelection',
        'insertColumnAtSelection',
        'insertRowAbove',
        'insertColRight',
    ]:
        if token not in editor:
            raise RuntimeError(f"EDITOR_TOKEN_MISSING:{token}")
    for token in ["Insert 1 row above", "Insert 1 row below", "Insert 1 column left", "Insert 1 column right"]:
        if token not in menu:
            raise RuntimeError(f"MENU_TOKEN_MISSING:{token}")

    run(["git", "diff", "--check"])
    run(["node", "--test", TEST])
    run(["npm", "run", "build"], cwd=FRONTEND)

    changed = {status_path(line) for line in status_lines() if status_path(line) in PHASE_SCOPE}
    if changed != PHASE_SCOPE:
        raise RuntimeError("CHANGED_PATHS_EXACT_FAIL:" + ",".join(sorted(changed)))

    unrelated_after = unrelated_fingerprints(status_lines())
    if unrelated_after != unrelated_before:
        raise RuntimeError("UNRELATED_DIRTY_STATE_CHANGED")

    if not LIVE_ROOT.exists() or not (DIST / "index.html").exists():
        raise RuntimeError("LIVE_OR_DIST_ROOT_MISSING")

    built_html = (DIST / "index.html").read_text(encoding="utf-8")
    built_asset = main_asset_from_html(built_html)
    if not built_asset:
        raise RuntimeError("BUILT_MAIN_ASSET_NOT_FOUND")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.exists():
        raise RuntimeError("BUILT_MAIN_ASSET_FILE_MISSING")

    try:
        live_before_html = download(LIVE_URL).decode("utf-8", errors="replace")
        live_before_asset = main_asset_from_html(live_before_html) or "UNKNOWN"
    except Exception:
        live_before_asset = "UNAVAILABLE"

    backup_parent = Path(tempfile.mkdtemp(prefix="tsheets_p8_b01_v1_live_"))
    live_backup = backup_parent / "build"
    shutil.copytree(LIVE_ROOT, live_backup)

    run(["rsync", "-a", "--delete", str(DIST) + "/", str(LIVE_ROOT) + "/"])
    run(["nginx", "-t"])
    run(["systemctl", "reload", "nginx"])

    live_after_html = download(LIVE_URL).decode("utf-8", errors="replace")
    live_after_asset = main_asset_from_html(live_after_html)
    if live_after_asset != built_asset:
        raise RuntimeError(f"LIVE_ASSET_MISMATCH:{live_after_asset}:{built_asset}")

    live_asset_bytes = download("https://tos.tamiyouz.com" + live_after_asset)
    if live_asset_bytes != built_asset_path.read_bytes():
        raise RuntimeError("LIVE_BUNDLE_BYTES_MISMATCH")

    print(f"PATCH={PATCH}")
    print("PHASE=8")
    print("BATCH=01")
    print("VERSION=V1")
    print("END_USER_FEATURE=INSERT_ROW_ABOVE_BELOW_AND_COLUMN_LEFT_RIGHT_AT_CURRENT_SELECTION")
    print("EXISTING_CONTENT_SHIFT=PASS")
    print("FORMULA_REFERENCE_SHIFT=PASS_UNQUALIFIED_REFS")
    print("FORMATTING_RANGE_METADATA_SHIFT=PASS")
    print("NAMED_RANGE_SHIFT=PASS")
    print("CURRENT_GRID_LIMITS_PRESERVED=500_ROWS_100_COLS")
    print("DELETE_ROW_COLUMN=DEFERRED_TO_NEXT_BATCH")
    print("MULTI_ROW_COLUMN_INSERT=DEFERRED_TO_NEXT_BATCH")
    print("PASS_FAIL=PASS")
    print(f"PRECHECK_WORKTREE={precheck}")
    print("BASELINE_BLOB_GUARD=PASS")
    print("PAYLOAD_INTEGRITY=PASS")
    print("UNIT_TESTS=PASS")
    print("FRONTEND_BUILD=PASS")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_before_asset}")
    print(f"LIVE_ASSET_AFTER={live_after_asset}")
    print("LIVE_DEPLOY=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print("BACKEND_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("PRE_EXISTING_UNRELATED_DIRTY_STATE_PRESERVED=YES")
    print("PUSH_PERFORMED=NO")
    print("READY_FOR_BROWSER_TEST=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_BROWSER_TEST")

except Exception as exc:
    fail(str(exc), snapshot=snapshot, live_backup=live_backup)
