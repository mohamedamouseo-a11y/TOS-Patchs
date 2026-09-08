import { cellRefFromIndex, parseCellRef } from "./sheetFormula.js";

const MAX_ROWS = 500;
const MAX_COLS = 100;

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value) || 0));
}

export function normalizeSelectionBounds(anchorRef, focusRef) {
  const a = parseCellRef(anchorRef);
  const b = parseCellRef(focusRef);
  if (!a || !b) return null;
  return {
    colFrom: Math.min(a.col, b.col),
    colTo: Math.max(a.col, b.col),
    rowFrom: Math.min(a.row, b.row),
    rowTo: Math.max(a.row, b.row),
  };
}

export function selectionLabel(bounds) {
  if (!bounds) return "";
  const start = cellRefFromIndex(bounds.colFrom, bounds.rowFrom);
  const end = cellRefFromIndex(bounds.colTo, bounds.rowTo);
  return start === end ? start : `${start}:${end}`;
}

export function parseNameBox(value) {
  const text = String(value || "").trim().toUpperCase();
  if (!text) return null;
  const parts = text.split(":");
  if (parts.length > 2) return null;
  const a = parseCellRef(parts[0]);
  const b = parseCellRef(parts[1] || parts[0]);
  if (!a || !b) return null;
  if (a.row >= MAX_ROWS || b.row >= MAX_ROWS || a.col >= MAX_COLS || b.col >= MAX_COLS) return null;
  return {
    anchorRef: cellRefFromIndex(a.col, a.row),
    focusRef: cellRefFromIndex(b.col, b.row),
    bounds: {
      colFrom: Math.min(a.col, b.col), colTo: Math.max(a.col, b.col),
      rowFrom: Math.min(a.row, b.row), rowTo: Math.max(a.row, b.row),
    },
  };
}

export function parseClipboardMatrix(text) {
  const source = String(text ?? "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const lines = source.split("\n");
  if (lines.length && lines[lines.length - 1] === "") lines.pop();
  return lines.slice(0, MAX_ROWS).map((line) => line.split("\t").slice(0, MAX_COLS));
}

export function matrixToTsv(matrix) {
  return (matrix || []).map((row) => row.map((item) => String(item?.value ?? item ?? "")).join("\t")).join("\n");
}

export function selectionMatrix(sheet, bounds) {
  if (!sheet || !bounds) return [];
  const matrix = [];
  for (let row = bounds.rowFrom; row <= bounds.rowTo; row += 1) {
    const rowValues = [];
    for (let col = bounds.colFrom; col <= bounds.colTo; col += 1) {
      const ref = cellRefFromIndex(col, row);
      rowValues.push({
        value: sheet.cells?.[ref]?.v ?? "",
        format: sheet.formats?.[ref] ? { ...sheet.formats[ref] } : null,
        sourceRef: ref,
      });
    }
    matrix.push(rowValues);
  }
  return matrix;
}

export function translateFormulaReferences(rawValue, colDelta, rowDelta) {
  if (typeof rawValue !== "string" || !rawValue.startsWith("=")) return rawValue;
  return rawValue.replace(/\b([A-Z]{1,3})([1-9][0-9]{0,3})\b/g, (match, letters, rowText) => {
    const parsed = parseCellRef(`${letters}${rowText}`);
    if (!parsed) return match;
    const nextCol = parsed.col + colDelta;
    const nextRow = parsed.row + rowDelta;
    if (nextCol < 0 || nextRow < 0 || nextCol >= MAX_COLS || nextRow >= MAX_ROWS) return match;
    return cellRefFromIndex(nextCol, nextRow);
  });
}

export function pasteSelectionMatrix(sheet, startRef, copied) {
  const start = parseCellRef(startRef);
  const matrix = copied?.matrix || [];
  const sourceBounds = copied?.sourceBounds || null;
  if (!sheet || !start || !matrix.length) return sheet;
  const cells = { ...(sheet.cells || {}) };
  const formats = { ...(sheet.formats || {}) };
  let maxRow = Number(sheet.rows || 1) - 1;
  let maxCol = Number(sheet.cols || 1) - 1;

  matrix.forEach((rowValues, rowOffset) => {
    rowValues.forEach((item, colOffset) => {
      const row = start.row + rowOffset;
      const col = start.col + colOffset;
      if (row >= MAX_ROWS || col >= MAX_COLS) return;
      const ref = cellRefFromIndex(col, row);
      let value = item?.value ?? "";
      if (sourceBounds && item?.sourceRef && typeof value === "string" && value.startsWith("=")) {
        const source = parseCellRef(item.sourceRef);
        if (source) value = translateFormulaReferences(value, col - source.col, row - source.row);
      }
      if (value === "" || value === undefined || value === null) delete cells[ref];
      else cells[ref] = { v: value };
      if (item?.format) formats[ref] = { ...item.format };
      else delete formats[ref];
      maxRow = Math.max(maxRow, row);
      maxCol = Math.max(maxCol, col);
    });
  });

  return { ...sheet, cells, formats, rows: Math.min(MAX_ROWS, maxRow + 1), cols: Math.min(MAX_COLS, maxCol + 1) };
}

export function pastePlainMatrix(sheet, startRef, matrix) {
  const wrapped = (matrix || []).map((row) => row.map((value) => ({ value, format: null, sourceRef: null })));
  return pasteSelectionMatrix(sheet, startRef, { matrix: wrapped, sourceBounds: null });
}

function numericSeriesDescriptor(sheet, bounds) {
  const height = bounds.rowTo - bounds.rowFrom + 1;
  const width = bounds.colTo - bounds.colFrom + 1;
  if (width === 1 && height >= 2) {
    const first = Number(sheet.cells?.[cellRefFromIndex(bounds.colFrom, bounds.rowFrom)]?.v);
    const second = Number(sheet.cells?.[cellRefFromIndex(bounds.colFrom, bounds.rowFrom + 1)]?.v);
    if (Number.isFinite(first) && Number.isFinite(second)) return { axis: "row", first, step: second - first };
  }
  if (height === 1 && width >= 2) {
    const first = Number(sheet.cells?.[cellRefFromIndex(bounds.colFrom, bounds.rowFrom)]?.v);
    const second = Number(sheet.cells?.[cellRefFromIndex(bounds.colFrom + 1, bounds.rowFrom)]?.v);
    if (Number.isFinite(first) && Number.isFinite(second)) return { axis: "col", first, step: second - first };
  }
  return null;
}

export function fillSelection(sheet, sourceBounds, targetBounds) {
  if (!sheet || !sourceBounds || !targetBounds) return sheet;
  const cells = { ...(sheet.cells || {}) };
  const formats = { ...(sheet.formats || {}) };
  const srcHeight = sourceBounds.rowTo - sourceBounds.rowFrom + 1;
  const srcWidth = sourceBounds.colTo - sourceBounds.colFrom + 1;
  const series = numericSeriesDescriptor(sheet, sourceBounds);

  for (let row = targetBounds.rowFrom; row <= targetBounds.rowTo; row += 1) {
    for (let col = targetBounds.colFrom; col <= targetBounds.colTo; col += 1) {
      if (row < 0 || col < 0 || row >= MAX_ROWS || col >= MAX_COLS) continue;
      if (row >= sourceBounds.rowFrom && row <= sourceBounds.rowTo && col >= sourceBounds.colFrom && col <= sourceBounds.colTo) continue;
      const sourceRow = sourceBounds.rowFrom + ((row - sourceBounds.rowFrom) % srcHeight + srcHeight) % srcHeight;
      const sourceCol = sourceBounds.colFrom + ((col - sourceBounds.colFrom) % srcWidth + srcWidth) % srcWidth;
      const sourceRef = cellRefFromIndex(sourceCol, sourceRow);
      const targetRef = cellRefFromIndex(col, row);
      let value = sheet.cells?.[sourceRef]?.v ?? "";

      if (series?.axis === "row" && srcWidth === 1 && row > sourceBounds.rowTo) {
        value = series.first + series.step * (row - sourceBounds.rowFrom);
      } else if (series?.axis === "col" && srcHeight === 1 && col > sourceBounds.colTo) {
        value = series.first + series.step * (col - sourceBounds.colFrom);
      } else if (typeof value === "string" && value.startsWith("=")) {
        value = translateFormulaReferences(value, col - sourceCol, row - sourceRow);
      }

      if (value === "" || value === undefined || value === null) delete cells[targetRef];
      else cells[targetRef] = { v: value };
      const sourceFormat = sheet.formats?.[sourceRef];
      if (sourceFormat) formats[targetRef] = { ...sourceFormat };
      else delete formats[targetRef];
    }
  }

  return {
    ...sheet,
    cells,
    formats,
    rows: Math.min(MAX_ROWS, Math.max(Number(sheet.rows || 1), targetBounds.rowTo + 1)),
    cols: Math.min(MAX_COLS, Math.max(Number(sheet.cols || 1), targetBounds.colTo + 1)),
  };
}

export function unionBoundsWithRef(bounds, ref) {
  const point = parseCellRef(ref);
  if (!bounds || !point) return bounds;
  return {
    colFrom: clamp(Math.min(bounds.colFrom, point.col), 0, MAX_COLS - 1),
    colTo: clamp(Math.max(bounds.colTo, point.col), 0, MAX_COLS - 1),
    rowFrom: clamp(Math.min(bounds.rowFrom, point.row), 0, MAX_ROWS - 1),
    rowTo: clamp(Math.max(bounds.rowTo, point.row), 0, MAX_ROWS - 1),
  };
}
