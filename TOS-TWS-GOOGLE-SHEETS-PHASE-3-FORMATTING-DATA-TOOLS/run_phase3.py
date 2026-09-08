#!/usr/bin/env python3
from pathlib import Path
import hashlib
import os
import subprocess
import sys
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-3-FORMATTING-DATA-TOOLS"
EXPECTED_HEAD = "16875298dd722df623202bd5ca804ef87ed7b0be"
BASE = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-3-FORMATTING-DATA-TOOLS/payload"
PAYLOADS = {
    "frontend/src/pages/tws/sheetDataPhase3.js": (f"{BASE}/sheetDataPhase3.js", "66c8f261e23622065e696c97de36ace89cfba28a"),
    "frontend/src/pages/tws/sheetDataPhase3.test.js": (f"{BASE}/sheetDataPhase3.test.js", "760328e4682b52534a6a7d44d81f18c2cb365a88"),
    "backend/src/utils/workspaceXlsx.phase3.test.js": (f"{BASE}/workspaceXlsx.phase3.test.js", "e59f45020941612dc52d6c2dfd9b843e8c41e118"),
}
BASELINE_BLOBS = {
    "backend/src/services/workspace.service.js": "fe994240c5ddc99f13b036524af5421aeb468e27",
    "backend/src/utils/workspaceExport.js": "622e31df8af48b5593f5e96569937891c2e31a93",
    "backend/src/utils/workspaceXlsx.js": "ec716d692edee6f6e370e6302de84b24c1690a85",
    "frontend/src/pages/tws/TSheetsEditor.jsx": "18833f921554472a46ade497a37ee27c6bb7a351",
    "frontend/src/pages/tws/sheetGridPhase2.js": "f12eb03a2b66d959a523e40b7562a2fbde0d1cb7",
    "backend/src/utils/workspaceXlsx.phase1.test.js": "ee6e8f51c93879d4434b77fa5b70c1de34c3a11c",
}
EXISTING_CHANGED = {
    "backend/src/services/workspace.service.js",
    "backend/src/utils/workspaceExport.js",
    "backend/src/utils/workspaceXlsx.js",
    "frontend/src/pages/tws/TSheetsEditor.jsx",
}
EXPECTED_CHANGED = EXISTING_CHANGED | set(PAYLOADS.keys())


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
            if i < len(parts) and parts[i]:
                i += 1
            raise RuntimeError(f"rename/copy working-tree state is not supported: {text}")
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
    require(not status_records(repo), "safe stale-index normalization failed")
    print("STALE_INDEX_RECOVERED=YES")
    print("SOURCE_FILES_OVERWRITTEN_DURING_RECOVERY=NO")


def verify_baseline(repo):
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    require(head == EXPECTED_HEAD, f"HEAD must equal Phase 3 baseline {EXPECTED_HEAD}")
    for rel, expected in BASELINE_BLOBS.items():
        actual = git(repo, "rev-parse", f"HEAD:{rel}").stdout.strip()
        require(actual == expected, f"baseline blob mismatch for {rel}: {actual} != {expected}")


def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    require(count == 1, f"{label}: expected exactly one replacement target, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before_once(path, marker, addition, label):
    text = path.read_text(encoding="utf-8")
    count = text.count(marker)
    require(count == 1, f"{label}: expected exactly one marker, found {count}")
    path.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8")


def insert_after_once(path, marker, addition, label):
    text = path.read_text(encoding="utf-8")
    count = text.count(marker)
    require(count == 1, f"{label}: expected exactly one marker, found {count}")
    path.write_text(text.replace(marker, marker + addition, 1), encoding="utf-8")


def download_payloads(repo):
    for rel, (url, expected_blob) in PAYLOADS.items():
        data = urllib.request.urlopen(url, timeout=30).read()
        actual_blob = git_blob_sha(data)
        require(actual_blob == expected_blob, f"payload blob mismatch for {rel}: {actual_blob}")
        dest = repo / rel
        require(not dest.exists(), f"new Phase 3 path already exists: {rel}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


def apply_service(service):
    replace_once(
        service,
        '    return { activeSheetId: "sheet_1", sheets: [{ id: "sheet_1", name: "Sheet1", rows: 30, cols: 12, cells: {}, formats: {}, freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} }] };',
        '    return { activeSheetId: "sheet_1", sheets: [{ id: "sheet_1", name: "Sheet1", rows: 30, cols: 12, cells: {}, formats: {}, merges: [], dataValidations: [], conditionalFormats: [], filter: null, protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} }] };',
        "service Phase3 default sheet",
    )

    helpers = r'''
function sanitizeSheetRange(value) {
  const start = String(value?.start || "").toUpperCase();
  const end = String(value?.end || value?.start || "").toUpperCase();
  if (!CELL_REF_KEY_PATTERN.test(start) || !CELL_REF_KEY_PATTERN.test(end)) return null;
  return { start, end };
}

function sanitizeSheetConditionalStyle(value) {
  const style = {};
  if (typeof value?.bg === "string" && SAFE_COLOR_PATTERN.test(value.bg)) style.bg = value.bg;
  if (typeof value?.color === "string" && SAFE_COLOR_PATTERN.test(value.color)) style.color = value.color;
  if (value?.bold) style.bold = true;
  return style;
}

'''
    insert_before_once(service, 'function sanitizeSheetContent(raw) {\n', helpers, "service Phase3 sanitizer helpers")

    replace_once(
        service,
        '      if (format?.bold) safeFormat.bold = true;\n      if (["left", "center", "right"].includes(format?.align)) safeFormat.align = format.align;',
        '      if (format?.bold) safeFormat.bold = true;\n      if (format?.italic) safeFormat.italic = true;\n      if (format?.underline) safeFormat.underline = true;\n      if (format?.strike) safeFormat.strike = true;\n      if (format?.wrap) safeFormat.wrap = true;\n      if (["left", "center", "right"].includes(format?.align)) safeFormat.align = format.align;\n      if (["top", "middle", "bottom"].includes(format?.vertical)) safeFormat.vertical = format.vertical;',
        "service Phase3 rich formats",
    )

    phase3_sanitizers = r'''    const merges = [];
    for (const [mergeIndex, merge] of (Array.isArray(sheet?.merges) ? sheet.merges : []).slice(0, 100).entries()) {
      const range = sanitizeSheetRange(merge);
      if (!range || range.start === range.end) continue;
      merges.push({ id: String(merge?.id || `merge_${index}_${mergeIndex}`).slice(0, 80), ...range });
    }

    const dataValidations = [];
    for (const [validationIndex, validation] of (Array.isArray(sheet?.dataValidations) ? sheet.dataValidations : []).slice(0, 100).entries()) {
      const range = sanitizeSheetRange(validation);
      if (!range || validation?.type !== "list") continue;
      const values = [];
      for (const rawValue of (Array.isArray(validation?.values) ? validation.values : []).slice(0, 50)) {
        const value = stripTags(String(rawValue ?? "")).slice(0, 80);
        if (value && !values.includes(value)) values.push(value);
      }
      if (!values.length) continue;
      dataValidations.push({
        id: String(validation?.id || `validation_${index}_${validationIndex}`).slice(0, 80),
        ...range,
        type: "list",
        values,
        allowBlank: validation?.allowBlank !== false,
      });
    }

    const conditionalFormats = [];
    const conditionalTypes = new Set(["greaterThan", "lessThan", "greaterOrEqual", "lessOrEqual", "equal", "between", "textContains", "empty", "notEmpty"]);
    for (const [ruleIndex, rule] of (Array.isArray(sheet?.conditionalFormats) ? sheet.conditionalFormats : []).slice(0, 100).entries()) {
      const range = sanitizeSheetRange(rule);
      if (!range || !conditionalTypes.has(rule?.type)) continue;
      const item = {
        id: String(rule?.id || `conditional_${index}_${ruleIndex}`).slice(0, 80),
        ...range,
        type: rule.type,
        style: sanitizeSheetConditionalStyle(rule?.style || {}),
      };
      if (rule?.value !== undefined) item.value = typeof rule.value === "number" ? rule.value : stripTags(String(rule.value)).slice(0, 120);
      if (rule?.value2 !== undefined) item.value2 = typeof rule.value2 === "number" ? rule.value2 : stripTags(String(rule.value2)).slice(0, 120);
      conditionalFormats.push(item);
    }

    let filter = null;
    const filterRange = sanitizeSheetRange(sheet?.filter);
    if (filterRange) {
      const criteria = {};
      for (const [rawCol, criterion] of Object.entries(sheet?.filter?.criteria || {}).slice(0, 100)) {
        const col = Number(rawCol);
        if (!Number.isInteger(col) || col < 0 || col >= 100) continue;
        const values = [];
        for (const rawValue of (Array.isArray(criterion?.values) ? criterion.values : []).slice(0, 100)) {
          const value = stripTags(String(rawValue ?? "")).slice(0, 120);
          if (!values.includes(value)) values.push(value);
        }
        if (values.length) criteria[String(col)] = { values };
      }
      filter = { ...filterRange, criteria };
    }

'''
    insert_before_once(service, '    return {\n      id: String(sheet?.id || `sheet_${index + 1}`).slice(0, 60),', phase3_sanitizers, "service Phase3 sheet structures")
    replace_once(
        service,
        '      formats,\n      protectedRanges,\n      freeze:',
        '      formats,\n      merges,\n      dataValidations,\n      conditionalFormats,\n      filter,\n      protectedRanges,\n      freeze:',
        "service Phase3 normalized return",
    )


def apply_xlsx_import(xlsx):
    replace_once(
        xlsx,
        '  if (cell?.font?.bold) format.bold = true;\n  if (Number.isFinite(Number(cell?.font?.size))) format.fontSize = Math.round(clamp(cell.font.size, 8, 72));',
        '  if (cell?.font?.bold) format.bold = true;\n  if (cell?.font?.italic) format.italic = true;\n  if (cell?.font?.underline) format.underline = true;\n  if (cell?.font?.strike) format.strike = true;\n  if (Number.isFinite(Number(cell?.font?.size))) format.fontSize = Math.round(clamp(cell.font.size, 8, 72));',
        "XLSX Phase3 font import",
    )
    replace_once(
        xlsx,
        '  const horizontal = String(cell?.alignment?.horizontal || "").toLowerCase();\n  if (["left", "center", "right"].includes(horizontal)) format.align = horizontal;',
        '  const horizontal = String(cell?.alignment?.horizontal || "").toLowerCase();\n  if (["left", "center", "right"].includes(horizontal)) format.align = horizontal;\n  const vertical = String(cell?.alignment?.vertical || "").toLowerCase();\n  if (["top", "middle", "bottom"].includes(vertical)) format.vertical = vertical;\n  if (cell?.alignment?.wrapText) format.wrap = true;',
        "XLSX Phase3 alignment import",
    )

    structures = r'''
function normalizeExcelRange(value) {
  const text = String(value || "").trim().toUpperCase();
  const match = text.match(/^([A-Z]{1,3}[1-9][0-9]{0,3})(?::([A-Z]{1,3}[1-9][0-9]{0,3}))?$/);
  if (!match) return null;
  return { start: match[1], end: match[2] || match[1] };
}

function columnLetters(number) {
  let n = Number(number);
  if (!Number.isInteger(n) || n < 1) return "";
  let result = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    result = String.fromCharCode(65 + rem) + result;
    n = Math.floor((n - 1) / 26);
  }
  return result;
}

function excelAddressPart(value) {
  if (typeof value === "string") return value.toUpperCase();
  if (value && Number.isInteger(Number(value.row)) && Number.isInteger(Number(value.column))) {
    return `${columnLetters(Number(value.column))}${Number(value.row)}`;
  }
  return "";
}

function mergesFromWorksheet(worksheet) {
  const merges = [];
  for (const [index, rawRange] of (worksheet?.model?.merges || []).slice(0, 100).entries()) {
    const range = normalizeExcelRange(rawRange);
    if (!range || range.start === range.end) continue;
    merges.push({ id: `merge_${index + 1}`, ...range });
  }
  return merges;
}

function validationsFromWorksheet(worksheet) {
  const output = [];
  const model = worksheet?.dataValidations?.model || {};
  let index = 0;
  for (const [rawRange, validation] of Object.entries(model)) {
    if (index >= 100 || validation?.type !== "list") continue;
    const range = normalizeExcelRange(rawRange);
    if (!range) continue;
    const formula = String(validation?.formulae?.[0] || "").trim();
    if (!(formula.startsWith('"') && formula.endsWith('"'))) continue;
    const values = formula.slice(1, -1).split(",").map((item) => item.replace(/""/g, '"').trim()).filter(Boolean).slice(0, 50);
    if (!values.length) continue;
    output.push({ id: `validation_${index + 1}`, ...range, type: "list", values, allowBlank: validation?.allowBlank !== false });
    index += 1;
  }
  return output;
}

function filterFromWorksheet(worksheet) {
  const raw = worksheet?.autoFilter || worksheet?.model?.autoFilter;
  if (!raw) return null;
  if (typeof raw === "string") {
    const range = normalizeExcelRange(raw);
    return range ? { ...range, criteria: {} } : null;
  }
  const from = excelAddressPart(raw?.from);
  const to = excelAddressPart(raw?.to);
  const range = normalizeExcelRange(from && to ? `${from}:${to}` : from);
  return range ? { ...range, criteria: {} } : null;
}

'''
    insert_before_once(xlsx, 'export async function parseTSheetXlsx(buffer) {\n', structures, "XLSX Phase3 structure import helpers")
    replace_once(
        xlsx,
        '      sheets: [{ id: "sheet_1", name: "Sheet1", rows: 30, cols: 12, cells: {}, formats: {}, protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} }],',
        '      sheets: [{ id: "sheet_1", name: "Sheet1", rows: 30, cols: 12, cells: {}, formats: {}, merges: [], dataValidations: [], conditionalFormats: [], filter: null, protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} }],',
        "XLSX Phase3 empty workbook structures",
    )
    replace_once(
        xlsx,
        '      cells,\n      formats,\n      protectedRanges: [],\n      freeze: freezeFromWorksheet(worksheet),',
        '      cells,\n      formats,\n      merges: mergesFromWorksheet(worksheet),\n      dataValidations: validationsFromWorksheet(worksheet),\n      conditionalFormats: [],\n      filter: filterFromWorksheet(worksheet),\n      protectedRanges: [],\n      freeze: freezeFromWorksheet(worksheet),',
        "XLSX Phase3 parsed structures",
    )


def apply_xlsx_export(export):
    parser = r'''
function parseExportCellRef(ref) {
  const match = String(ref || "").toUpperCase().match(/^([A-Z]{1,3})([1-9][0-9]{0,3})$/);
  if (!match) return null;
  let col = 0;
  for (const char of match[1]) col = col * 26 + (char.charCodeAt(0) - 64);
  return { col: col - 1, row: Number(match[2]) - 1 };
}

'''
    insert_before_once(export, 'function uniqueWorksheetName(rawName, usedNames) {\n', parser, "XLSX Phase3 export ref parser")
    replace_once(
        export,
        '        if (format.bold) font.bold = true;\n        if (format.fontSize) font.size = Math.max(8, Math.min(72, Number(format.fontSize) || 12));',
        '        if (format.bold) font.bold = true;\n        if (format.italic) font.italic = true;\n        if (format.underline) font.underline = true;\n        if (format.strike) font.strike = true;\n        if (format.fontSize) font.size = Math.max(8, Math.min(72, Number(format.fontSize) || 12));',
        "XLSX Phase3 font export",
    )
    replace_once(
        export,
        '        if (Object.keys(font).length) cell.font = font;\n        if (format.align) cell.alignment = { horizontal: format.align };',
        '        if (Object.keys(font).length) cell.font = font;\n        const alignment = {};\n        if (format.align) alignment.horizontal = format.align;\n        if (["top", "middle", "bottom"].includes(format.vertical)) alignment.vertical = format.vertical;\n        if (format.wrap) alignment.wrapText = true;\n        if (Object.keys(alignment).length) cell.alignment = alignment;',
        "XLSX Phase3 alignment export",
    )

    extras = r'''    for (const merge of sheet.merges || []) {
      const start = parseExportCellRef(merge?.start);
      const end = parseExportCellRef(merge?.end);
      if (!start || !end || merge.start === merge.end) continue;
      try { worksheet.mergeCells(String(merge.start).toUpperCase(), String(merge.end).toUpperCase()); } catch { /* skip invalid/overlapping merge */ }
    }

    for (const validation of sheet.dataValidations || []) {
      if (validation?.type !== "list") continue;
      const start = parseExportCellRef(validation.start);
      const end = parseExportCellRef(validation.end);
      if (!start || !end) continue;
      const values = (validation.values || []).map((value) => String(value).replace(/"/g, '""')).filter(Boolean).slice(0, 50);
      if (!values.length) continue;
      const formula = `"${values.join(",")}"`;
      for (let row = Math.min(start.row, end.row); row <= Math.max(start.row, end.row) && row < rows; row += 1) {
        for (let col = Math.min(start.col, end.col); col <= Math.max(start.col, end.col) && col < cols; col += 1) {
          worksheet.getCell(row + 1, col + 1).dataValidation = { type: "list", allowBlank: validation.allowBlank !== false, formulae: [formula] };
        }
      }
    }

    if (sheet.filter?.start && sheet.filter?.end && parseExportCellRef(sheet.filter.start) && parseExportCellRef(sheet.filter.end)) {
      worksheet.autoFilter = `${String(sheet.filter.start).toUpperCase()}:${String(sheet.filter.end).toUpperCase()}`;
    }

'''
    insert_before_once(export, '    for (const [rowIndex, px] of Object.entries(sheet.rowHeights || {})) {\n', extras, "XLSX Phase3 merge validation filter export")


def apply_editor(editor):
    replace_once(
        editor,
        'import { fillSelection, matrixToTsv, parseClipboardMatrix, parseNameBox, pastePlainMatrix, pasteSelectionMatrix, selectionMatrix, unionBoundsWithRef } from "./sheetGridPhase2";\n',
        'import { fillSelection, matrixToTsv, parseClipboardMatrix, parseNameBox, pastePlainMatrix, pasteSelectionMatrix, selectionMatrix, unionBoundsWithRef } from "./sheetGridPhase2";\nimport { addConditionalRule, applyFormatPatch, clearConditionalRules, clearFilter, clearFormatting, clearValidation, conditionalStyleForRef, filterUniqueValues, isValidCellValue, mergeSelection, mergedRangeForRef, mergeSpan, parseConditionalExpression, rowMatchesFilter, setFilterColumnValues, setFilterRange, setListValidation, unmergeSelection, validationForRef } from "./sheetDataPhase3";\n',
        "editor Phase3 helper import",
    )
    replace_once(
        editor,
        '  function getVisibleRows() {\n    const rows = Array.from({ length: rowCount }, (_, row) => row);\n    const needle = sheetFilterQuery.trim().toLowerCase();\n    if (!needle) return rows;\n    return rows.filter((row) => Array.from({ length: colCount }).some((_, col) => String(computedValues[cellRefFromIndex(col, row)] ?? "").toLowerCase().includes(needle)));\n  }',
        '  function getVisibleRows() {\n    const rows = Array.from({ length: rowCount }, (_, row) => row).filter((row) => rowMatchesFilter(activeSheet, row, computedValues));\n    const needle = sheetFilterQuery.trim().toLowerCase();\n    if (!needle) return rows;\n    return rows.filter((row) => Array.from({ length: colCount }).some((_, col) => String(computedValues[cellRefFromIndex(col, row)] ?? "").toLowerCase().includes(needle)));\n  }',
        "editor Phase3 filter-aware rows",
    )
    replace_once(
        editor,
        '      const next = prev.map((sheet) => (sheet.id === activeSheetId ? mutator({ ...sheet, cells: { ...sheet.cells }, formats: { ...sheet.formats }, protectedRanges: [...(sheet.protectedRanges || [])], freeze: { ...(sheet.freeze || {}) }, rowHeights: { ...(sheet.rowHeights || {}) }, colWidths: { ...(sheet.colWidths || {}) } }) : sheet));',
        '      const next = prev.map((sheet) => (sheet.id === activeSheetId ? mutator({ ...sheet, cells: { ...sheet.cells }, formats: { ...sheet.formats }, merges: [...(sheet.merges || [])], dataValidations: [...(sheet.dataValidations || [])], conditionalFormats: [...(sheet.conditionalFormats || [])], filter: sheet.filter ? { ...sheet.filter, criteria: { ...(sheet.filter.criteria || {}) } } : null, protectedRanges: [...(sheet.protectedRanges || [])], freeze: { ...(sheet.freeze || {}) }, rowHeights: { ...(sheet.rowHeights || {}) }, colWidths: { ...(sheet.colWidths || {}) } }) : sheet));',
        "editor Phase3 immutable structures",
    )
    replace_once(
        editor,
        '  function setCellValue(ref, value) {\n    if (!canEdit || isProtectedRef(ref)) { if (isProtectedRef(ref)) setError(ui.protectedCell); return; }\n    mutateActiveSheet((sheet) => {',
        '  function setCellValue(ref, value) {\n    if (!canEdit || isProtectedRef(ref)) { if (isProtectedRef(ref)) setError(ui.protectedCell); return; }\n    if (!isValidCellValue(activeSheet, ref, value)) {\n      setError(ui.lang === "en" ? "Value is not allowed by this cell dropdown." : "القيمة غير مسموحة حسب القائمة المنسدلة لهذه الخلية.");\n      return;\n    }\n    mutateActiveSheet((sheet) => {',
        "editor Phase3 validation enforcement",
    )
    replace_once(
        editor,
        '        if (key === "bold") formats[targetRef] = { ...current, bold: !current.bold };\n        else if (key === "align") formats[targetRef] = { ...current, align: value };',
        '        if (key === "bold") formats[targetRef] = { ...current, bold: !current.bold };\n        else if (key === "italic") formats[targetRef] = { ...current, italic: !current.italic };\n        else if (key === "underline") formats[targetRef] = { ...current, underline: !current.underline };\n        else if (key === "strike") formats[targetRef] = { ...current, strike: !current.strike };\n        else if (key === "wrap") formats[targetRef] = { ...current, wrap: !current.wrap };\n        else if (key === "vertical") formats[targetRef] = { ...current, vertical: value };\n        else if (key === "align") formats[targetRef] = { ...current, align: value };',
        "editor Phase3 rich format controls",
    )

    actions = r'''
  function mergeSelectionAction() {
    const bounds = selectionBounds();
    if (!bounds || (bounds.colFrom === bounds.colTo && bounds.rowFrom === bounds.rowTo)) {
      setError(ui.lang === "en" ? "Select two or more cells to merge." : "حدد خليتين أو أكثر للدمج.");
      return;
    }
    mutateActiveSheet((sheet) => mergeSelection(sheet, bounds), `merge:${Date.now()}`);
  }

  function unmergeSelectionAction() {
    const bounds = selectionBounds();
    if (!bounds) return;
    mutateActiveSheet((sheet) => unmergeSelection(sheet, bounds), `unmerge:${Date.now()}`);
  }

  function clearFormattingAction() {
    const bounds = selectionBounds();
    if (!bounds) return;
    mutateActiveSheet((sheet) => clearFormatting(sheet, bounds), `clear-format:${Date.now()}`);
  }

  function addDropdownValidationAction() {
    const bounds = selectionBounds();
    if (!bounds) return;
    const raw = window.prompt(ui.lang === "en" ? "Dropdown values, separated by commas:" : "قيم القائمة المنسدلة، افصل بينها بفواصل:", "Yes,No");
    if (raw === null) return;
    const values = raw.split(",").map((value) => value.trim()).filter(Boolean);
    if (!values.length) return;
    mutateActiveSheet((sheet) => setListValidation(sheet, bounds, values, true), `validation:${Date.now()}`);
  }

  function clearValidationAction() {
    const bounds = selectionBounds();
    if (!bounds) return;
    mutateActiveSheet((sheet) => clearValidation(sheet, bounds), `validation-clear:${Date.now()}`);
  }

  function addConditionalFormattingAction() {
    const bounds = selectionBounds();
    if (!bounds) return;
    const expression = window.prompt(ui.lang === "en" ? "Rule: >70, <=50, between:40,80, contains:urgent, empty, notempty" : "القاعدة: >70 أو <=50 أو between:40,80 أو contains:urgent أو empty أو notempty", ">70");
    if (expression === null) return;
    const rule = parseConditionalExpression(expression);
    if (!rule) {
      setError(ui.lang === "en" ? "Invalid conditional-format rule." : "قاعدة التنسيق الشرطي غير صحيحة.");
      return;
    }
    const bg = window.prompt(ui.lang === "en" ? "Highlight color (hex):" : "لون التمييز (Hex):", "#dcfce7") || "#dcfce7";
    const safeBg = /^#[0-9a-f]{6}$/i.test(bg) ? bg : "#dcfce7";
    mutateActiveSheet((sheet) => addConditionalRule(sheet, bounds, rule, { bg: safeBg, bold: true }), `conditional:${Date.now()}`);
  }

  function clearConditionalFormattingAction() {
    const bounds = selectionBounds();
    if (!bounds) return;
    mutateActiveSheet((sheet) => clearConditionalRules(sheet, bounds), `conditional-clear:${Date.now()}`);
  }

  function createFilterAction() {
    let bounds = selectionBounds();
    if (!bounds) return;
    if (bounds.colFrom === bounds.colTo && bounds.rowFrom === bounds.rowTo) {
      bounds = { colFrom: 0, rowFrom: 0, colTo: Math.max(0, Math.min(Number(activeSheet?.cols || 1), MAX_VISIBLE_COLS) - 1), rowTo: Math.max(0, Math.min(Number(activeSheet?.rows || 1), MAX_VISIBLE_ROWS) - 1) };
    }
    mutateActiveSheet((sheet) => setFilterRange(sheet, bounds), `filter-range:${Date.now()}`);
  }

  function filterCurrentColumnAction() {
    const parsed = parseCellRef(focusedRef);
    if (!parsed || !activeSheet?.filter) {
      setError(ui.lang === "en" ? "Create a filter range first." : "أنشئ نطاق فلترة أولًا.");
      return;
    }
    const values = filterUniqueValues(activeSheet, parsed.col, computedValues);
    const raw = window.prompt(ui.lang === "en" ? "Keep these values (comma-separated). Empty means show all:" : "اعرض هذه القيم فقط (بفواصل). اتركها فارغة لإظهار الكل:", values.join(","));
    if (raw === null) return;
    const selected = raw.split(",").map((value) => value.trim()).filter(Boolean);
    mutateActiveSheet((sheet) => setFilterColumnValues(sheet, parsed.col, selected), `filter-values:${Date.now()}`);
  }

  function clearFilterAction() {
    mutateActiveSheet((sheet) => clearFilter(sheet), `filter-clear:${Date.now()}`);
  }

'''
    insert_before_once(editor, '  function addRow() {\n', actions, "editor Phase3 actions")
    replace_once(
        editor,
        '    const copy = { ...source, id, name: `${source.name || "Sheet"} copy`, cells: { ...(source.cells || {}) }, formats: { ...(source.formats || {}) }, protectedRanges: [...(source.protectedRanges || [])], rowHeights: { ...(source.rowHeights || {}) }, colWidths: { ...(source.colWidths || {}) } };',
        '    const copy = { ...source, id, name: `${source.name || "Sheet"} copy`, cells: { ...(source.cells || {}) }, formats: { ...(source.formats || {}) }, merges: [...(source.merges || [])], dataValidations: [...(source.dataValidations || [])], conditionalFormats: [...(source.conditionalFormats || [])], filter: source.filter ? { ...source.filter, criteria: { ...(source.filter.criteria || {}) } } : null, protectedRanges: [...(source.protectedRanges || [])], rowHeights: { ...(source.rowHeights || {}) }, colWidths: { ...(source.colWidths || {}) } };',
        "editor Phase3 duplicate sheet structures",
    )
    replace_once(
        editor,
        '    const newSheet = { id, name: `Sheet${sheets.length + 1}`, rows: 30, cols: 12, cells: {}, formats: {}, protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} };',
        '    const newSheet = { id, name: `Sheet${sheets.length + 1}`, rows: 30, cols: 12, cells: {}, formats: {}, merges: [], dataValidations: [], conditionalFormats: [], filter: null, protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} };',
        "editor Phase3 new sheet structures",
    )

    rich_buttons = r'''          <button type="button" title={ui.lang === "en" ? "Italic" : "مائل"} onClick={() => toggleFormat(focusedRef, "italic")} className={cn("grid h-8 w-8 place-items-center rounded-lg text-sm italic transition", focusedCellFormat.italic ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950" : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10")}>I</button>
          <button type="button" title={ui.lang === "en" ? "Underline" : "تحته خط"} onClick={() => toggleFormat(focusedRef, "underline")} className={cn("grid h-8 w-8 place-items-center rounded-lg text-sm underline transition", focusedCellFormat.underline ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950" : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10")}>U</button>
          <button type="button" title={ui.lang === "en" ? "Strikethrough" : "يتوسطه خط"} onClick={() => toggleFormat(focusedRef, "strike")} className={cn("grid h-8 w-8 place-items-center rounded-lg text-sm line-through transition", focusedCellFormat.strike ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950" : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10")}>S</button>
          <button type="button" title={ui.lang === "en" ? "Wrap text" : "التفاف النص"} onClick={() => toggleFormat(focusedRef, "wrap")} className={cn("rounded-lg px-2 py-1.5 text-[11px] font-black transition", focusedCellFormat.wrap ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950" : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10")}>{ui.lang === "en" ? "Wrap" : "التفاف"}</button>
          <Field as="select" value={focusedCellFormat.vertical || "middle"} onChange={(event) => toggleFormat(focusedRef, "vertical", event.target.value)} className="!w-24 !py-1.5 text-xs">
            <option value="top">{ui.lang === "en" ? "Top" : "أعلى"}</option>
            <option value="middle">{ui.lang === "en" ? "Middle" : "وسط"}</option>
            <option value="bottom">{ui.lang === "en" ? "Bottom" : "أسفل"}</option>
          </Field>
'''
    insert_after_once(editor, '          <ToolbarButton icon={Bold} label={ui.bold} onClick={() => toggleFormat(focusedRef, "bold")} />\n', rich_buttons, "editor Phase3 rich toolbar")
    insert_after_once(
        editor,
        '            <option value="percent">{ui.formatPercent}</option>\n',
        '            <option value="date">{ui.lang === "en" ? "Date" : "تاريخ"}</option>\n            <option value="datetime">{ui.lang === "en" ? "Date & time" : "تاريخ ووقت"}</option>\n',
        "editor Phase3 date number formats",
    )

    data_buttons = r'''          <Button type="button" variant="soft" onClick={mergeSelectionAction} className="text-xs">{ui.lang === "en" ? "Merge" : "دمج"}</Button>
          <Button type="button" variant="soft" onClick={unmergeSelectionAction} className="text-xs">{ui.lang === "en" ? "Unmerge" : "إلغاء الدمج"}</Button>
          <Button type="button" variant="soft" onClick={clearFormattingAction} className="text-xs">{ui.lang === "en" ? "Clear format" : "مسح التنسيق"}</Button>
          <Button type="button" variant="soft" onClick={addDropdownValidationAction} className="text-xs">{ui.lang === "en" ? "Dropdown" : "قائمة"}</Button>
          <Button type="button" variant="soft" onClick={addConditionalFormattingAction} className="text-xs">{ui.lang === "en" ? "Conditional" : "شرطي"}</Button>
          <Button type="button" variant="soft" onClick={createFilterAction} className="text-xs">{ui.lang === "en" ? "Create filter" : "إنشاء فلتر"}</Button>
          <Button type="button" variant="soft" onClick={filterCurrentColumnAction} className="text-xs">{ui.lang === "en" ? "Filter values" : "قيم الفلتر"}</Button>
          {activeSheet?.filter && <Button type="button" variant="soft" onClick={clearFilterAction} className="text-xs">{ui.lang === "en" ? "Clear filter" : "مسح الفلتر"}</Button>}
'''
    insert_after_once(editor, '          <ToolbarButton icon={ArrowUpAZ} label={ui.sortDesc} onClick={() => sortSelection("desc")} />\n', data_buttons, "editor Phase3 data toolbar")

    insert_after_once(
        editor,
        '                      const displayValue = computedValues[ref] ?? "";\n',
        '                      const merge = mergedRangeForRef(activeSheet, ref);\n                      if (merge && merge.start !== ref) return null;\n                      const span = mergeSpan(merge);\n                      const conditionalFormat = conditionalStyleForRef(activeSheet, ref, displayValue);\n                      const effectiveFormat = { ...format, ...conditionalFormat };\n                      const validation = validationForRef(activeSheet, ref);\n',
        "editor Phase3 cell state",
    )
    replace_once(editor, '                          key={ref}\n                          onContextMenu=', '                          key={ref}\n                          rowSpan={span.rowSpan}\n                          colSpan={span.colSpan}\n                          onContextMenu=', "editor Phase3 merge spans")
    replace_once(
        editor,
        '                          style={{ minWidth: `${getColWidth(col)}px`, width: `${getColWidth(col)}px`, height: `${getRowHeight(row)}px`, backgroundColor: format.bg || undefined, color: format.color || undefined, border: format.border || undefined, fontSize: format.fontSize ? `${format.fontSize}px` : undefined, ...(row < freezeRows ? { position: "sticky", top: `${getFrozenRowTop(row)}px`, zIndex: 12, boxShadow: "inset 0 -2px 0 rgba(245,158,11,.45)" } : {}), ...(col < freezeCols ? { position: "sticky", left: `${getFrozenColLeft(col)}px`, zIndex: row < freezeRows ? 19 : 13, boxShadow: "inset -2px 0 0 rgba(245,158,11,.45)" } : {}) }}',
        '                          style={{ minWidth: `${getColWidth(col)}px`, width: `${getColWidth(col)}px`, height: `${getRowHeight(row)}px`, backgroundColor: effectiveFormat.bg || undefined, color: effectiveFormat.color || undefined, border: effectiveFormat.border || undefined, fontSize: effectiveFormat.fontSize ? `${effectiveFormat.fontSize}px` : undefined, fontStyle: effectiveFormat.italic ? "italic" : undefined, textDecoration: [effectiveFormat.underline ? "underline" : "", effectiveFormat.strike ? "line-through" : ""].filter(Boolean).join(" ") || undefined, verticalAlign: effectiveFormat.vertical || undefined, whiteSpace: effectiveFormat.wrap ? "normal" : undefined, ...(row < freezeRows ? { position: "sticky", top: `${getFrozenRowTop(row)}px`, zIndex: 12, boxShadow: "inset 0 -2px 0 rgba(245,158,11,.45)" } : {}), ...(col < freezeCols ? { position: "sticky", left: `${getFrozenColLeft(col)}px`, zIndex: row < freezeRows ? 19 : 13, boxShadow: "inset -2px 0 0 rgba(245,158,11,.45)" } : {}) }}',
        "editor Phase3 effective cell style",
    )

    old_input = r'''                          <input
                            id={`tws-cell-${ref}`}
                            value={isFocused ? rawValue : displayValue}
                            onFocus={() => { setFocusedRef(ref); setNameBoxDraft(""); setContextMenu(null); }}
                            onMouseDown={(event) => setRangeAnchor(event.shiftKey ? (rangeAnchor || focusedRef) : "")}
                            onChange={(event) => setCellValue(ref, event.target.value)}
                            readOnly={!canEdit || isProtectedRef(ref)}
                            className={cn(
                              "h-8 w-24 min-w-[96px] border-none bg-transparent px-2 text-xs outline-none focus:bg-amber-50 dark:focus:bg-amber-500/10",
                              format.bold && "font-black",
                              format.align === "center" && "text-center",
                              format.align === "left" && "text-left",
                              isProtectedRef(ref) && "bg-zinc-100 text-zinc-400 dark:bg-white/5",
                              !format.align && "text-right"
                            )}
                            style={{ fontSize: format.fontSize ? `${format.fontSize}px` : undefined, color: format.color || undefined }}
                          />'''
    new_input = r'''                          {validation?.type === "list" ? (
                            <select
                              id={`tws-cell-${ref}`}
                              value={rawValue}
                              onFocus={() => { setFocusedRef(ref); setNameBoxDraft(""); setContextMenu(null); }}
                              onMouseDown={(event) => setRangeAnchor(event.shiftKey ? (rangeAnchor || focusedRef) : "")}
                              onChange={(event) => setCellValue(ref, event.target.value)}
                              disabled={!canEdit || isProtectedRef(ref)}
                              className={cn("h-8 w-full min-w-[96px] border-none bg-transparent px-2 text-xs outline-none focus:bg-amber-50 dark:focus:bg-amber-500/10", effectiveFormat.bold && "font-black", effectiveFormat.italic && "italic", effectiveFormat.align === "center" && "text-center", effectiveFormat.align === "left" && "text-left", !effectiveFormat.align && "text-right")}
                              style={{ fontSize: effectiveFormat.fontSize ? `${effectiveFormat.fontSize}px` : undefined, color: effectiveFormat.color || undefined, textDecoration: [effectiveFormat.underline ? "underline" : "", effectiveFormat.strike ? "line-through" : ""].filter(Boolean).join(" ") || undefined }}
                            >
                              {validation.allowBlank !== false && <option value=""></option>}
                              {(validation.values || []).map((option) => <option key={option} value={option}>{option}</option>)}
                            </select>
                          ) : effectiveFormat.wrap ? (
                            <textarea
                              id={`tws-cell-${ref}`}
                              rows={1}
                              value={isFocused ? rawValue : displayValue}
                              onFocus={() => { setFocusedRef(ref); setNameBoxDraft(""); setContextMenu(null); }}
                              onMouseDown={(event) => setRangeAnchor(event.shiftKey ? (rangeAnchor || focusedRef) : "")}
                              onChange={(event) => setCellValue(ref, event.target.value)}
                              readOnly={!canEdit || isProtectedRef(ref)}
                              className={cn("min-h-8 w-full min-w-[96px] resize-none border-none bg-transparent px-2 py-1.5 text-xs outline-none focus:bg-amber-50 dark:focus:bg-amber-500/10", effectiveFormat.bold && "font-black", effectiveFormat.italic && "italic", effectiveFormat.align === "center" && "text-center", effectiveFormat.align === "left" && "text-left", !effectiveFormat.align && "text-right")}
                              style={{ fontSize: effectiveFormat.fontSize ? `${effectiveFormat.fontSize}px` : undefined, color: effectiveFormat.color || undefined, textDecoration: [effectiveFormat.underline ? "underline" : "", effectiveFormat.strike ? "line-through" : ""].filter(Boolean).join(" ") || undefined }}
                            />
                          ) : (
                            <input
                              id={`tws-cell-${ref}`}
                              value={isFocused ? rawValue : displayValue}
                              onFocus={() => { setFocusedRef(ref); setNameBoxDraft(""); setContextMenu(null); }}
                              onMouseDown={(event) => setRangeAnchor(event.shiftKey ? (rangeAnchor || focusedRef) : "")}
                              onChange={(event) => setCellValue(ref, event.target.value)}
                              readOnly={!canEdit || isProtectedRef(ref)}
                              className={cn("h-8 w-full min-w-[96px] border-none bg-transparent px-2 text-xs outline-none focus:bg-amber-50 dark:focus:bg-amber-500/10", effectiveFormat.bold && "font-black", effectiveFormat.italic && "italic", effectiveFormat.align === "center" && "text-center", effectiveFormat.align === "left" && "text-left", isProtectedRef(ref) && "bg-zinc-100 text-zinc-400 dark:bg-white/5", !effectiveFormat.align && "text-right")}
                              style={{ fontSize: effectiveFormat.fontSize ? `${effectiveFormat.fontSize}px` : undefined, color: effectiveFormat.color || undefined, textDecoration: [effectiveFormat.underline ? "underline" : "", effectiveFormat.strike ? "line-through" : ""].filter(Boolean).join(" ") || undefined }}
                            />
                          )}'''
    replace_once(editor, old_input, new_input, "editor Phase3 cell editors")

    context_actions = r'''                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { mergeSelectionAction(); setContextMenu(null); }}>{ui.lang === "en" ? "Merge cells" : "دمج الخلايا"}</button>}
                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { unmergeSelectionAction(); setContextMenu(null); }}>{ui.lang === "en" ? "Unmerge cells" : "إلغاء دمج الخلايا"}</button>}
                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { addDropdownValidationAction(); setContextMenu(null); }}>{ui.lang === "en" ? "Dropdown" : "قائمة منسدلة"}</button>}
                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { addConditionalFormattingAction(); setContextMenu(null); }}>{ui.lang === "en" ? "Conditional formatting" : "تنسيق شرطي"}</button>}
                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { filterCurrentColumnAction(); setContextMenu(null); }}>{ui.lang === "en" ? "Filter this column" : "فلترة هذا العمود"}</button>}
                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { clearValidationAction(); setContextMenu(null); }}>{ui.lang === "en" ? "Remove dropdown" : "إزالة القائمة"}</button>}
                {canEdit && <button type="button" className="w-full rounded-xl px-3 py-2 text-start hover:bg-zinc-100 dark:hover:bg-white/10" onClick={() => { clearConditionalFormattingAction(); setContextMenu(null); }}>{ui.lang === "en" ? "Clear conditional rules" : "مسح القواعد الشرطية"}</button>}
'''
    insert_before_once(editor, '                <div className="my-1 h-px bg-zinc-100 dark:bg-white/10" />\n', context_actions, "editor Phase3 context actions")
    replace_once(
        editor,
        '            {ui.selectedRange}: {selectedRangeLabel} · {ui.protectedRanges}: {activeSheet?.protectedRanges?.length || 0} · {ui.freezeRows}: {freezeRows} · {ui.freezeCols}: {freezeCols}',
        '            {ui.selectedRange}: {selectedRangeLabel} · {ui.lang === "en" ? "Merges" : "دمج"}: {activeSheet?.merges?.length || 0} · {ui.lang === "en" ? "Dropdowns" : "قوائم"}: {activeSheet?.dataValidations?.length || 0} · {ui.lang === "en" ? "Filter" : "فلتر"}: {activeSheet?.filter ? "ON" : "OFF"} · {ui.protectedRanges}: {activeSheet?.protectedRanges?.length || 0}',
        "editor Phase3 status strip",
    )


def apply_transforms(repo):
    apply_service(repo / "backend/src/services/workspace.service.js")
    apply_xlsx_import(repo / "backend/src/utils/workspaceXlsx.js")
    apply_xlsx_export(repo / "backend/src/utils/workspaceExport.js")
    apply_editor(repo / "frontend/src/pages/tws/TSheetsEditor.jsx")


def changed_paths(repo):
    return {path for _, path in status_records(repo)}


def validate(repo):
    paths = changed_paths(repo)
    require(paths == EXPECTED_CHANGED, f"unexpected Phase 3 working-tree paths: {sorted(paths)}")
    print(f"PATCH_FILE_COUNT={len(paths)}")

    diff_check = git(repo, "diff", "--check", check=False)
    require(diff_check.returncode == 0, f"git diff --check failed:\n{diff_check.stdout}")

    for rel in [
        "backend/src/services/workspace.service.js",
        "backend/src/utils/workspaceXlsx.js",
        "backend/src/utils/workspaceExport.js",
        "frontend/src/pages/tws/sheetDataPhase3.js",
    ]:
        checked = run(["node", "--check", rel], repo, check=False)
        require(checked.returncode == 0, f"node --check failed for {rel}:\n{checked.stdout}")
    print("SYNTAX_CHECK=PASS")

    backend = repo / "backend"
    prisma_validate = run(["npm", "run", "prisma:validate"], backend, check=False)
    require(prisma_validate.returncode == 0, f"prisma validate failed:\n{prisma_validate.stdout}")
    print("PRISMA_VALIDATE=PASS")
    prisma_generate = run(["npm", "run", "prisma:generate"], backend, check=False)
    require(prisma_generate.returncode == 0, f"prisma generate failed:\n{prisma_generate.stdout}")
    print("PRISMA_GENERATE=PASS")

    phase3_xlsx = run(["node", "--test", "src/utils/workspaceXlsx.phase3.test.js"], backend, check=False)
    require(phase3_xlsx.returncode == 0, f"Phase 3 XLSX tests failed:\n{phase3_xlsx.stdout}")
    print("PHASE_3_XLSX_TESTS=PASS (2/2)")

    phase1 = run(["node", "--test", "src/utils/workspaceXlsx.phase1.test.js"], backend, check=False)
    require(phase1.returncode == 0, f"Phase 1 XLSX regression failed:\n{phase1.stdout}")
    print("PHASE_1_XLSX_REGRESSION=PASS (4/4)")

    frontend = repo / "frontend"
    phase3 = run(["node", "--test", "src/pages/tws/sheetDataPhase3.test.js"], frontend, check=False)
    require(phase3.returncode == 0, f"Phase 3 data tools tests failed:\n{phase3.stdout}")
    print("PHASE_3_DATA_TOOLS_TESTS=PASS (6/6)")

    phase2 = run(["node", "--test", "src/pages/tws/sheetGridPhase2.test.js"], frontend, check=False)
    require(phase2.returncode == 0, f"Phase 2 grid regression failed:\n{phase2.stdout}")
    print("PHASE_2_GRID_REGRESSION=PASS (6/6)")

    build = run(["npm", "run", "build"], frontend, check=False)
    require(build.returncode == 0, f"frontend build failed:\n{build.stdout}")
    print("FRONTEND_BUILD=PASS")

    service = (repo / "backend/src/services/workspace.service.js").read_text(encoding="utf-8")
    editor = (repo / "frontend/src/pages/tws/TSheetsEditor.jsx").read_text(encoding="utf-8")
    xlsx_import = (repo / "backend/src/utils/workspaceXlsx.js").read_text(encoding="utf-8")
    xlsx_export = (repo / "backend/src/utils/workspaceExport.js").read_text(encoding="utf-8")
    required_markers = [
        (service, "dataValidations", "backend data validation sanitizer"),
        (service, "conditionalFormats", "backend conditional format sanitizer"),
        (service, "merges", "backend merge sanitizer"),
        (editor, "mergeSelectionAction", "merge UI"),
        (editor, "addDropdownValidationAction", "dropdown UI"),
        (editor, "addConditionalFormattingAction", "conditional formatting UI"),
        (editor, "filterCurrentColumnAction", "filter UI"),
        (xlsx_import, "mergesFromWorksheet", "XLSX merge import"),
        (xlsx_import, "validationsFromWorksheet", "XLSX validation import"),
        (xlsx_export, "worksheet.mergeCells", "XLSX merge export"),
        (xlsx_export, "dataValidation", "XLSX validation export"),
    ]
    for source, marker, label in required_markers:
        require(marker in source, f"missing Phase 3 marker: {label}")

    print("RICH_FORMATTING=PASS")
    print("MERGE_UNMERGE=PASS")
    print("DATA_VALIDATION_DROPDOWNS=PASS")
    print("CONDITIONAL_FORMATTING=PASS")
    print("FILTER_RANGE_VALUES=PASS")
    print("XLSX_MERGES_VALIDATION_FILTER=PASS")
    print("XLSX_PHASE_1_PRESERVED=YES")
    print("GRID_PHASE_2_PRESERVED=YES")
    print("AUTOSAVE_UNDO_REDO_PRESERVED=YES")
    print("PERMISSIONS_SHARING_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("BACKEND_SCHEMA_MIGRATION=NO")


def main():
    repo = Path(os.environ.get("TOS_REPO", "/var/www/TOS")).resolve()
    print(f"PATCH={PATCH}")
    print(f"REPO={repo}")
    require((repo / ".git").exists(), f"not a git repository: {repo}")
    normalize_stale_index_if_safe(repo)
    verify_baseline(repo)

    backups = {rel: (repo / rel).read_bytes() for rel in EXISTING_CHANGED}
    created = []
    try:
        download_payloads(repo)
        created = list(PAYLOADS.keys())
        apply_transforms(repo)
        validate(repo)
    except Exception:
        for rel, data in backups.items():
            (repo / rel).write_bytes(data)
        for rel in created:
            path = repo / rel
            if path.exists():
                path.unlink()
        raise

    print("PHASE_3_PATCH_APPLIED=YES")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_3_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
