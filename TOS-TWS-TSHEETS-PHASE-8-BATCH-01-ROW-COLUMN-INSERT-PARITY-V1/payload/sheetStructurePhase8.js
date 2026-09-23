const DEFAULT_MAX_ROWS = 500;
const DEFAULT_MAX_COLS = 100;

function colLettersToIndex(letters) {
  let value = 0;
  for (const char of String(letters || "").toUpperCase()) {
    if (char < "A" || char > "Z") return -1;
    value = value * 26 + char.charCodeAt(0) - 64;
  }
  return value - 1;
}

function colIndexToLetters(index) {
  let value = Number(index) + 1;
  let output = "";
  while (value > 0) {
    const mod = (value - 1) % 26;
    output = String.fromCharCode(65 + mod) + output;
    value = Math.floor((value - 1) / 26);
  }
  return output || "A";
}

function parseRef(ref) {
  const match = /^(\$?)([A-Z]{1,3})(\$?)([1-9][0-9]{0,6})$/i.exec(String(ref || "").trim());
  if (!match) return null;
  const col = colLettersToIndex(match[2]);
  const row = Number(match[4]) - 1;
  if (col < 0 || row < 0) return null;
  return { col, row, absCol: Boolean(match[1]), absRow: Boolean(match[3]) };
}

function makeRef(point) {
  return `${point.absCol ? "$" : ""}${colIndexToLetters(point.col)}${point.absRow ? "$" : ""}${point.row + 1}`;
}

function clampCount(value) {
  return Math.max(1, Math.floor(Number(value) || 1));
}

function shiftPointForInsert(point, axis, index, count) {
  const next = { ...point };
  if (axis === "row" && next.row >= index) next.row += count;
  if (axis === "col" && next.col >= index) next.col += count;
  return next;
}

function shiftRefForInsert(ref, axis, index, count) {
  const point = parseRef(ref);
  return point ? makeRef(shiftPointForInsert(point, axis, index, count)) : ref;
}

function rewriteFormulaForInsert(value, axis, index, count) {
  if (typeof value !== "string" || !value.startsWith("=")) return value;
  return value.replace(/(^|[^A-Za-z0-9_.'!])(\$?[A-Z]{1,3}\$?[1-9][0-9]{0,6})(?![A-Za-z0-9_])/g, (full, prefix, ref) => {
    if (prefix.endsWith("!")) return full;
    return `${prefix}${shiftRefForInsert(ref, axis, index, count)}`;
  });
}

function remapCellRecord(record, axis, index, count, rewriteValues = false) {
  const output = {};
  for (const [ref, rawValue] of Object.entries(record || {})) {
    const nextRef = shiftRefForInsert(ref, axis, index, count);
    if (!rewriteValues || !rawValue || typeof rawValue !== "object") {
      output[nextRef] = rawValue;
      continue;
    }
    const nextValue = { ...rawValue };
    if (Object.prototype.hasOwnProperty.call(nextValue, "v")) {
      nextValue.v = rewriteFormulaForInsert(nextValue.v, axis, index, count);
    }
    output[nextRef] = nextValue;
  }
  return output;
}

function remapDimensionMap(map, index, count) {
  const output = {};
  for (const [key, value] of Object.entries(map || {})) {
    const zeroBased = Number(key) - 1;
    if (!Number.isInteger(zeroBased) || zeroBased < 0) continue;
    output[String((zeroBased >= index ? zeroBased + count : zeroBased) + 1)] = value;
  }
  return output;
}

function remapRange(range, axis, index, count) {
  if (!range?.start || !range?.end) return range;
  const start = parseRef(range.start);
  const end = parseRef(range.end);
  if (!start || !end) return range;
  const low = axis === "row" ? Math.min(start.row, end.row) : Math.min(start.col, end.col);
  const high = axis === "row" ? Math.max(start.row, end.row) : Math.max(start.col, end.col);
  const nextStart = { ...start };
  const nextEnd = { ...end };
  if (index <= low) {
    if (axis === "row") { nextStart.row += count; nextEnd.row += count; }
    else { nextStart.col += count; nextEnd.col += count; }
  } else if (index <= high) {
    if (axis === "row") nextEnd.row += count;
    else nextEnd.col += count;
  }
  return { ...range, start: makeRef(nextStart), end: makeRef(nextEnd) };
}

function remapRangeList(items, axis, index, count) {
  return (Array.isArray(items) ? items : []).map((item) => remapRange(item, axis, index, count));
}

function remapFilter(filter, axis, index, count) {
  if (!filter) return filter;
  const next = remapRange(filter, axis, index, count);
  if (axis !== "col") return next;
  const criteria = {};
  for (const [key, value] of Object.entries(filter.criteria || {})) {
    const col = Number(key);
    if (!Number.isInteger(col)) continue;
    criteria[String(col >= index ? col + count : col)] = value;
  }
  return { ...next, criteria };
}

function remapPivots(pivots, axis, index, count) {
  return (Array.isArray(pivots) ? pivots : []).map((pivot) => {
    const start = parseRef(pivot?.start);
    const next = remapRange(pivot, axis, index, count);
    if (axis !== "col" || !start) return next;
    const rowFieldAbs = start.col + Number(pivot.rowField || 0);
    const valueFieldAbs = start.col + Number(pivot.valueField || 0);
    const insertedInside = index > start.col && index <= (parseRef(pivot.end)?.col ?? start.col);
    if (!insertedInside) return next;
    return {
      ...next,
      rowField: Number(pivot.rowField || 0) + (index <= rowFieldAbs ? count : 0),
      valueField: Number(pivot.valueField || 0) + (index <= valueFieldAbs ? count : 0),
    };
  });
}

function insertDimension(sheet, axis, index, count, limit) {
  const sizeKey = axis === "row" ? "rows" : "cols";
  const currentSize = Math.max(1, Number(sheet?.[sizeKey] || 1));
  const safeIndex = Math.max(0, Math.min(Math.floor(Number(index) || 0), currentSize));
  const available = Math.max(0, limit - currentSize);
  const actualCount = Math.min(clampCount(count), available);
  if (!actualCount) return sheet;

  const freeze = { ...(sheet.freeze || {}) };
  if (axis === "row" && safeIndex < Number(freeze.rows || 0)) freeze.rows = Number(freeze.rows || 0) + actualCount;
  if (axis === "col" && safeIndex < Number(freeze.cols || 0)) freeze.cols = Number(freeze.cols || 0) + actualCount;

  return {
    ...sheet,
    [sizeKey]: currentSize + actualCount,
    cells: remapCellRecord(sheet.cells, axis, safeIndex, actualCount, true),
    formats: remapCellRecord(sheet.formats, axis, safeIndex, actualCount, false),
    rowHeights: axis === "row" ? remapDimensionMap(sheet.rowHeights, safeIndex, actualCount) : { ...(sheet.rowHeights || {}) },
    colWidths: axis === "col" ? remapDimensionMap(sheet.colWidths, safeIndex, actualCount) : { ...(sheet.colWidths || {}) },
    merges: remapRangeList(sheet.merges, axis, safeIndex, actualCount),
    dataValidations: remapRangeList(sheet.dataValidations, axis, safeIndex, actualCount),
    conditionalFormats: remapRangeList(sheet.conditionalFormats, axis, safeIndex, actualCount),
    protectedRanges: remapRangeList(sheet.protectedRanges, axis, safeIndex, actualCount),
    filter: remapFilter(sheet.filter, axis, safeIndex, actualCount),
    charts: remapRangeList(sheet.charts, axis, safeIndex, actualCount),
    pivots: remapPivots(sheet.pivots, axis, safeIndex, actualCount),
    freeze,
  };
}

export function insertSheetRows(sheet, index, count = 1, options = {}) {
  return insertDimension(sheet, "row", index, count, Number(options.maxRows || DEFAULT_MAX_ROWS));
}

export function insertSheetColumns(sheet, index, count = 1, options = {}) {
  return insertDimension(sheet, "col", index, count, Number(options.maxCols || DEFAULT_MAX_COLS));
}

export function remapNamedRangesForInsert(namedRanges, sheetId, axis, index, count = 1) {
  const safeCount = clampCount(count);
  return (Array.isArray(namedRanges) ? namedRanges : []).map((range) => {
    if (String(range?.sheetId || "") !== String(sheetId || "")) return range;
    return remapRange(range, axis, Math.max(0, Math.floor(Number(index) || 0)), safeCount);
  });
}
