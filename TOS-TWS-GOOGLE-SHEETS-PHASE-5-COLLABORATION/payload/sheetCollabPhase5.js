// TWS T-Sheets — Phase 5 collaboration patch helpers.
// Shared byte-for-byte between backend and frontend.

const CELL_REF_PATTERN = /^[A-Z]{1,3}[1-9][0-9]{0,3}$/;
const MAX_PATCH_ENTRIES = 5000;
const REPLACE_KEYS = [
  "rows", "cols", "merges", "dataValidations", "conditionalFormats", "filter",
  "protectedRanges", "freeze", "rowHeights", "colWidths",
];

function cloneJson(value) {
  if (value === undefined) return undefined;
  return JSON.parse(JSON.stringify(value));
}

function jsonEqual(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function normalizeMapPatch(value, kind) {
  const input = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const output = {};
  let count = 0;
  for (const [rawRef, rawValue] of Object.entries(input)) {
    if (count >= MAX_PATCH_ENTRIES) break;
    const ref = String(rawRef || "").trim().toUpperCase();
    if (!CELL_REF_PATTERN.test(ref)) continue;
    if (rawValue === null) output[ref] = null;
    else if (kind === "cell" && rawValue && typeof rawValue === "object" && Object.prototype.hasOwnProperty.call(rawValue, "v")) output[ref] = { v: cloneJson(rawValue.v) };
    else if (kind === "format" && rawValue && typeof rawValue === "object" && !Array.isArray(rawValue)) output[ref] = cloneJson(rawValue);
    else continue;
    count += 1;
  }
  return output;
}

export function normalizeSheetCollabPatch(input = {}) {
  const sheetId = String(input?.sheetId || "").trim().slice(0, 80);
  if (!sheetId) return null;
  const mutationId = String(input?.mutationId || "").trim().slice(0, 120);
  const cells = normalizeMapPatch(input?.cells, "cell");
  const formats = normalizeMapPatch(input?.formats, "format");
  const replace = {};
  const incomingReplace = input?.replace && typeof input.replace === "object" && !Array.isArray(input.replace) ? input.replace : {};
  for (const key of REPLACE_KEYS) {
    if (Object.prototype.hasOwnProperty.call(incomingReplace, key)) replace[key] = cloneJson(incomingReplace[key]);
  }
  return { sheetId, mutationId, cells, formats, replace };
}

function diffMap(before = {}, after = {}) {
  const output = {};
  const refs = new Set([...Object.keys(before || {}), ...Object.keys(after || {})]);
  for (const ref of refs) {
    const a = before?.[ref];
    const b = after?.[ref];
    if (jsonEqual(a, b)) continue;
    output[ref] = b === undefined ? null : cloneJson(b);
  }
  return output;
}

export function sheetCollabPatchHasChanges(patch) {
  const normalized = normalizeSheetCollabPatch(patch);
  if (!normalized) return false;
  return Object.keys(normalized.cells).length > 0 || Object.keys(normalized.formats).length > 0 || Object.keys(normalized.replace).length > 0;
}

export function buildSheetCollabPatch(beforeSheet, afterSheet, options = {}) {
  if (!beforeSheet || !afterSheet) return null;
  const beforeId = String(beforeSheet.id || "");
  const afterId = String(afterSheet.id || "");
  if (!beforeId || beforeId !== afterId) return null;
  const replace = {};
  for (const key of REPLACE_KEYS) {
    if (!jsonEqual(beforeSheet?.[key], afterSheet?.[key])) replace[key] = cloneJson(afterSheet?.[key]);
  }
  return normalizeSheetCollabPatch({
    sheetId: afterId,
    mutationId: options.mutationId || "",
    cells: diffMap(beforeSheet.cells || {}, afterSheet.cells || {}),
    formats: diffMap(beforeSheet.formats || {}, afterSheet.formats || {}),
    replace,
  });
}

export function applySheetCollabPatch(contentJson, patchInput) {
  const patch = normalizeSheetCollabPatch(patchInput);
  if (!patch) return contentJson;
  const sheets = Array.isArray(contentJson?.sheets) ? contentJson.sheets : [];
  const index = sheets.findIndex((sheet) => String(sheet?.id || "") === patch.sheetId);
  if (index < 0) return contentJson;

  const current = sheets[index] || {};
  const cells = { ...(current.cells || {}) };
  const formats = { ...(current.formats || {}) };
  for (const [ref, value] of Object.entries(patch.cells)) {
    if (value === null) delete cells[ref];
    else cells[ref] = cloneJson(value);
  }
  for (const [ref, value] of Object.entries(patch.formats)) {
    if (value === null) delete formats[ref];
    else formats[ref] = cloneJson(value);
  }

  const nextSheet = { ...current, cells, formats };
  for (const [key, value] of Object.entries(patch.replace)) nextSheet[key] = cloneJson(value);
  const nextSheets = sheets.slice();
  nextSheets[index] = nextSheet;
  return { ...(contentJson || {}), sheets: nextSheets };
}

function parseSimpleRef(ref) {
  const match = /^([A-Z]{1,3})([1-9][0-9]{0,3})$/.exec(String(ref || "").toUpperCase());
  if (!match) return null;
  let col = 0;
  for (const char of match[1]) col = col * 26 + char.charCodeAt(0) - 64;
  return { col: col - 1, row: Number(match[2]) - 1 };
}

export function selectionContainsRef(selection, ref) {
  if (!selection || !ref) return false;
  const point = parseSimpleRef(ref);
  const anchor = parseSimpleRef(selection.anchorRef || selection.focusRef);
  const focus = parseSimpleRef(selection.focusRef || selection.anchorRef);
  if (!point || !anchor || !focus) return false;
  return point.col >= Math.min(anchor.col, focus.col)
    && point.col <= Math.max(anchor.col, focus.col)
    && point.row >= Math.min(anchor.row, focus.row)
    && point.row <= Math.max(anchor.row, focus.row);
}

export function collaborationPeerColor(seed = "peer") {
  let hash = 0;
  for (const ch of String(seed)) hash = ((hash << 5) - hash + ch.charCodeAt(0)) | 0;
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue} 72% 45%)`;
}
