import { cellRefFromIndex, parseCellRef } from "./sheetFormula.js";

const MAX_ROWS = 500;
const MAX_COLS = 100;
const MAX_RANGE_ITEMS = 20000;
const MAX_RULES = 100;

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value) || 0));
}

function normalizedBounds(bounds) {
  if (!bounds) return null;
  return {
    colFrom: clamp(Math.min(bounds.colFrom, bounds.colTo), 0, MAX_COLS - 1),
    colTo: clamp(Math.max(bounds.colFrom, bounds.colTo), 0, MAX_COLS - 1),
    rowFrom: clamp(Math.min(bounds.rowFrom, bounds.rowTo), 0, MAX_ROWS - 1),
    rowTo: clamp(Math.max(bounds.rowFrom, bounds.rowTo), 0, MAX_ROWS - 1),
  };
}

function boundsFromRange(start, end = start) {
  const a = parseCellRef(start);
  const b = parseCellRef(end);
  if (!a || !b) return null;
  return normalizedBounds({ colFrom: a.col, colTo: b.col, rowFrom: a.row, rowTo: b.row });
}

function rangeForBounds(bounds) {
  const safe = normalizedBounds(bounds);
  if (!safe) return null;
  return {
    start: cellRefFromIndex(safe.colFrom, safe.rowFrom),
    end: cellRefFromIndex(safe.colTo, safe.rowTo),
  };
}

function rangesOverlap(a, b) {
  if (!a || !b) return false;
  return a.colFrom <= b.colTo && a.colTo >= b.colFrom && a.rowFrom <= b.rowTo && a.rowTo >= b.rowFrom;
}

export function refInsideBounds(ref, bounds) {
  const point = parseCellRef(ref);
  const safe = normalizedBounds(bounds);
  if (!point || !safe) return false;
  return point.col >= safe.colFrom && point.col <= safe.colTo && point.row >= safe.rowFrom && point.row <= safe.rowTo;
}

export function rangeRefs(bounds) {
  const safe = normalizedBounds(bounds);
  if (!safe) return [];
  const refs = [];
  for (let row = safe.rowFrom; row <= safe.rowTo && refs.length < MAX_RANGE_ITEMS; row += 1) {
    for (let col = safe.colFrom; col <= safe.colTo && refs.length < MAX_RANGE_ITEMS; col += 1) {
      refs.push(cellRefFromIndex(col, row));
    }
  }
  return refs;
}

export function mergedRangeForRef(sheet, ref) {
  const point = parseCellRef(ref);
  if (!sheet || !point) return null;
  for (const merge of sheet.merges || []) {
    const bounds = boundsFromRange(merge.start, merge.end);
    if (bounds && refInsideBounds(ref, bounds)) return { ...merge, bounds };
  }
  return null;
}

export function mergeSpan(merge) {
  const bounds = merge?.bounds || boundsFromRange(merge?.start, merge?.end);
  if (!bounds) return { rowSpan: 1, colSpan: 1 };
  return { rowSpan: bounds.rowTo - bounds.rowFrom + 1, colSpan: bounds.colTo - bounds.colFrom + 1 };
}

export function mergeSelection(sheet, bounds) {
  const safe = normalizedBounds(bounds);
  if (!sheet || !safe) return sheet;
  if (safe.colFrom === safe.colTo && safe.rowFrom === safe.rowTo) return sheet;
  const merges = [...(sheet.merges || [])];
  if (merges.some((merge) => rangesOverlap(boundsFromRange(merge.start, merge.end), safe))) return sheet;

  const range = rangeForBounds(safe);
  const anchor = range.start;
  const cells = { ...(sheet.cells || {}) };
  const anchorValue = cells[anchor];
  for (const ref of rangeRefs(safe)) {
    if (ref !== anchor) delete cells[ref];
  }
  if (anchorValue) cells[anchor] = anchorValue;
  merges.push({ id: `merge_${Date.now()}_${merges.length}`, ...range });
  return { ...sheet, cells, merges: merges.slice(0, MAX_RULES) };
}

export function unmergeSelection(sheet, bounds) {
  const safe = normalizedBounds(bounds);
  if (!sheet || !safe) return sheet;
  return {
    ...sheet,
    merges: (sheet.merges || []).filter((merge) => !rangesOverlap(boundsFromRange(merge.start, merge.end), safe)),
  };
}

export function applyFormatPatch(sheet, bounds, patch = {}) {
  const safe = normalizedBounds(bounds);
  if (!sheet || !safe) return sheet;
  const formats = { ...(sheet.formats || {}) };
  for (const ref of rangeRefs(safe)) {
    const current = { ...(formats[ref] || {}) };
    for (const [key, value] of Object.entries(patch || {})) {
      if (value === null || value === undefined || value === "") delete current[key];
      else current[key] = value;
    }
    if (Object.keys(current).length) formats[ref] = current;
    else delete formats[ref];
  }
  return { ...sheet, formats };
}

export function clearFormatting(sheet, bounds) {
  const safe = normalizedBounds(bounds);
  if (!sheet || !safe) return sheet;
  const formats = { ...(sheet.formats || {}) };
  for (const ref of rangeRefs(safe)) delete formats[ref];
  return { ...sheet, formats };
}

function sanitizeListValues(values) {
  const unique = [];
  for (const raw of Array.isArray(values) ? values : []) {
    const value = String(raw ?? "").trim().slice(0, 80);
    if (!value || unique.includes(value)) continue;
    unique.push(value);
    if (unique.length >= 50) break;
  }
  return unique;
}

export function setListValidation(sheet, bounds, values, allowBlank = true) {
  const safe = normalizedBounds(bounds);
  const options = sanitizeListValues(values);
  if (!sheet || !safe || !options.length) return sheet;
  const range = rangeForBounds(safe);
  const next = (sheet.dataValidations || []).filter((item) => !rangesOverlap(boundsFromRange(item.start, item.end), safe));
  next.push({ id: `validation_${Date.now()}_${next.length}`, ...range, type: "list", values: options, allowBlank: Boolean(allowBlank) });
  return { ...sheet, dataValidations: next.slice(0, MAX_RULES) };
}

export function clearValidation(sheet, bounds) {
  const safe = normalizedBounds(bounds);
  if (!sheet || !safe) return sheet;
  return { ...sheet, dataValidations: (sheet.dataValidations || []).filter((item) => !rangesOverlap(boundsFromRange(item.start, item.end), safe)) };
}

export function validationForRef(sheet, ref) {
  return (sheet?.dataValidations || []).find((item) => refInsideBounds(ref, boundsFromRange(item.start, item.end))) || null;
}

export function isValidCellValue(sheet, ref, value) {
  const validation = validationForRef(sheet, ref);
  if (!validation || validation.type !== "list") return true;
  const text = String(value ?? "");
  if (!text && validation.allowBlank) return true;
  return (validation.values || []).includes(text);
}

function safeConditionalStyle(style = {}) {
  const result = {};
  if (typeof style.bg === "string") result.bg = style.bg;
  if (typeof style.color === "string") result.color = style.color;
  if (style.bold) result.bold = true;
  return result;
}

export function parseConditionalExpression(input) {
  const text = String(input || "").trim();
  if (!text) return null;
  if (/^notempty$/i.test(text)) return { type: "notEmpty" };
  if (/^empty$/i.test(text)) return { type: "empty" };
  const contains = text.match(/^contains\s*:\s*(.+)$/i);
  if (contains) return { type: "textContains", value: contains[1].trim().slice(0, 120) };
  const numeric = text.match(/^(>=|<=|>|<|=)\s*(-?\d+(?:\.\d+)?)$/);
  if (numeric) {
    const type = { ">": "greaterThan", "<": "lessThan", "=": "equal", ">=": "greaterOrEqual", "<=": "lessOrEqual" }[numeric[1]];
    return { type, value: Number(numeric[2]) };
  }
  const between = text.match(/^between\s*:\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/i);
  if (between) return { type: "between", value: Number(between[1]), value2: Number(between[2]) };
  return null;
}

export function addConditionalRule(sheet, bounds, rule, style = { bg: "#fef3c7" }) {
  const safe = normalizedBounds(bounds);
  if (!sheet || !safe || !rule?.type) return sheet;
  const range = rangeForBounds(safe);
  const conditionalFormats = [...(sheet.conditionalFormats || []), {
    id: `conditional_${Date.now()}_${(sheet.conditionalFormats || []).length}`,
    ...range,
    type: rule.type,
    ...(rule.value !== undefined ? { value: rule.value } : {}),
    ...(rule.value2 !== undefined ? { value2: rule.value2 } : {}),
    style: safeConditionalStyle(style),
  }].slice(0, MAX_RULES);
  return { ...sheet, conditionalFormats };
}

export function clearConditionalRules(sheet, bounds) {
  const safe = normalizedBounds(bounds);
  if (!sheet || !safe) return sheet;
  return { ...sheet, conditionalFormats: (sheet.conditionalFormats || []).filter((item) => !rangesOverlap(boundsFromRange(item.start, item.end), safe)) };
}

function conditionalMatches(rule, value) {
  const text = String(value ?? "");
  const number = Number(value);
  if (rule.type === "empty") return text === "";
  if (rule.type === "notEmpty") return text !== "";
  if (rule.type === "textContains") return text.toLowerCase().includes(String(rule.value ?? "").toLowerCase());
  if (!Number.isFinite(number)) return false;
  if (rule.type === "greaterThan") return number > Number(rule.value);
  if (rule.type === "lessThan") return number < Number(rule.value);
  if (rule.type === "greaterOrEqual") return number >= Number(rule.value);
  if (rule.type === "lessOrEqual") return number <= Number(rule.value);
  if (rule.type === "equal") return number === Number(rule.value);
  if (rule.type === "between") return number >= Math.min(Number(rule.value), Number(rule.value2)) && number <= Math.max(Number(rule.value), Number(rule.value2));
  return false;
}

export function conditionalStyleForRef(sheet, ref, value) {
  const style = {};
  for (const rule of sheet?.conditionalFormats || []) {
    const bounds = boundsFromRange(rule.start, rule.end);
    if (!bounds || !refInsideBounds(ref, bounds) || !conditionalMatches(rule, value)) continue;
    Object.assign(style, safeConditionalStyle(rule.style || {}));
  }
  return style;
}

export function setFilterRange(sheet, bounds) {
  const safe = normalizedBounds(bounds);
  if (!sheet || !safe) return sheet;
  const range = rangeForBounds(safe);
  return { ...sheet, filter: { ...range, criteria: {} } };
}

export function setFilterColumnValues(sheet, colIndex, values) {
  const filterBounds = boundsFromRange(sheet?.filter?.start, sheet?.filter?.end);
  const col = Number(colIndex);
  const options = sanitizeListValues(values);
  if (!sheet || !filterBounds || !Number.isInteger(col) || col < filterBounds.colFrom || col > filterBounds.colTo) return sheet;
  const criteria = { ...(sheet.filter?.criteria || {}) };
  if (options.length) criteria[String(col)] = { values: options };
  else delete criteria[String(col)];
  return { ...sheet, filter: { ...sheet.filter, criteria } };
}

export function clearFilter(sheet) {
  if (!sheet) return sheet;
  const next = { ...sheet };
  delete next.filter;
  return next;
}

export function filterUniqueValues(sheet, colIndex, computedValues = {}) {
  const bounds = boundsFromRange(sheet?.filter?.start, sheet?.filter?.end);
  const col = Number(colIndex);
  if (!bounds || !Number.isInteger(col) || col < bounds.colFrom || col > bounds.colTo) return [];
  const values = [];
  for (let row = bounds.rowFrom + 1; row <= bounds.rowTo; row += 1) {
    const ref = cellRefFromIndex(col, row);
    const value = String(computedValues[ref] ?? sheet?.cells?.[ref]?.v ?? "");
    if (!values.includes(value)) values.push(value);
    if (values.length >= 100) break;
  }
  return values;
}

export function rowMatchesFilter(sheet, rowIndex, computedValues = {}) {
  const bounds = boundsFromRange(sheet?.filter?.start, sheet?.filter?.end);
  if (!bounds) return true;
  const row = Number(rowIndex);
  if (row < bounds.rowFrom || row > bounds.rowTo || row === bounds.rowFrom) return true;
  const criteria = sheet.filter?.criteria || {};
  for (const [colKey, criterion] of Object.entries(criteria)) {
    const col = Number(colKey);
    if (!Number.isInteger(col) || col < bounds.colFrom || col > bounds.colTo) continue;
    const allowed = Array.isArray(criterion?.values) ? criterion.values.map(String) : [];
    if (!allowed.length) continue;
    const ref = cellRefFromIndex(col, row);
    const value = String(computedValues[ref] ?? sheet?.cells?.[ref]?.v ?? "");
    if (!allowed.includes(value)) return false;
  }
  return true;
}
