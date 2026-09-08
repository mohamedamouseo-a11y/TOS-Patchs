// TWS T-Sheets — Phase 6 advanced sheets helpers.
// Shared byte-for-byte between backend and frontend.

const CELL_REF_PATTERN = /^([A-Z]{1,3})([1-9][0-9]{0,3})$/;
const CHART_TYPES = new Set(["bar", "line", "pie"]);
const PIVOT_AGGREGATES = new Set(["sum", "count", "average"]);
const PAGE_ORIENTATIONS = new Set(["portrait", "landscape"]);
const PAPER_SIZES = new Set(["A4", "LETTER"]);
const PAGE_SCALES = new Set(["fitWidth", "actual"]);

function stripText(value, max = 160) {
  return String(value ?? "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
}

function colLettersToIndex(letters) {
  let value = 0;
  for (const char of String(letters || "").toUpperCase()) value = value * 26 + char.charCodeAt(0) - 64;
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

export function parseAdvancedCellRef(ref) {
  const match = CELL_REF_PATTERN.exec(String(ref || "").trim().toUpperCase());
  if (!match) return null;
  return { col: colLettersToIndex(match[1]), row: Number(match[2]) - 1 };
}

export function advancedCellRefFromIndex(col, row) {
  return `${colIndexToLetters(col)}${Number(row) + 1}`;
}

function normalizeRange(input) {
  const start = String(input?.start || "").trim().toUpperCase();
  const end = String(input?.end || input?.start || "").trim().toUpperCase();
  const a = parseAdvancedCellRef(start);
  const b = parseAdvancedCellRef(end);
  if (!a || !b) return null;
  return {
    start: advancedCellRefFromIndex(Math.min(a.col, b.col), Math.min(a.row, b.row)),
    end: advancedCellRefFromIndex(Math.max(a.col, b.col), Math.max(a.row, b.row)),
  };
}

export function advancedRangeFromBounds(bounds) {
  if (!bounds) return null;
  const colFrom = Math.max(0, Math.floor(Number(bounds.colFrom)));
  const colTo = Math.max(colFrom, Math.floor(Number(bounds.colTo)));
  const rowFrom = Math.max(0, Math.floor(Number(bounds.rowFrom)));
  const rowTo = Math.max(rowFrom, Math.floor(Number(bounds.rowTo)));
  if (![colFrom, colTo, rowFrom, rowTo].every(Number.isFinite)) return null;
  return { start: advancedCellRefFromIndex(colFrom, rowFrom), end: advancedCellRefFromIndex(colTo, rowTo) };
}

function rangeBounds(range) {
  const normalized = normalizeRange(range);
  if (!normalized) return null;
  const start = parseAdvancedCellRef(normalized.start);
  const end = parseAdvancedCellRef(normalized.end);
  return { ...normalized, colFrom: start.col, colTo: end.col, rowFrom: start.row, rowTo: end.row };
}

function cellDisplayValue(sheet, ref, computedValues = {}) {
  if (Object.prototype.hasOwnProperty.call(computedValues || {}, ref)) return computedValues[ref];
  return sheet?.cells?.[ref]?.v ?? "";
}

function numericValue(value) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  const normalized = String(value ?? "").trim().replace(/,/g, "");
  if (!normalized) return null;
  const number = Number(normalized);
  return Number.isFinite(number) ? number : null;
}

export function normalizePageSetup(input = {}) {
  const orientation = PAGE_ORIENTATIONS.has(input?.orientation) ? input.orientation : "portrait";
  const paperSize = PAPER_SIZES.has(String(input?.paperSize || "").toUpperCase()) ? String(input.paperSize).toUpperCase() : "A4";
  const scale = PAGE_SCALES.has(input?.scale) ? input.scale : "fitWidth";
  return { orientation, paperSize, scale, gridlines: input?.gridlines !== false };
}

export function normalizeAdvancedSheetState(sheet = {}) {
  const charts = [];
  for (const [index, chart] of (Array.isArray(sheet?.charts) ? sheet.charts : []).slice(0, 20).entries()) {
    const range = normalizeRange(chart);
    const type = CHART_TYPES.has(chart?.type) ? chart.type : null;
    if (!range || !type) continue;
    charts.push({
      id: stripText(chart?.id || `chart_${index + 1}`, 80),
      title: stripText(chart?.title || "Chart", 120) || "Chart",
      type,
      ...range,
      showLegend: chart?.showLegend !== false,
    });
  }

  const pivots = [];
  for (const [index, pivot] of (Array.isArray(sheet?.pivots) ? sheet.pivots : []).slice(0, 20).entries()) {
    const range = normalizeRange(pivot);
    const aggregate = PIVOT_AGGREGATES.has(pivot?.aggregate) ? pivot.aggregate : null;
    const rowField = Number(pivot?.rowField);
    const valueField = Number(pivot?.valueField);
    const bounds = rangeBounds(range);
    const width = bounds ? bounds.colTo - bounds.colFrom + 1 : 0;
    if (!range || !aggregate || !Number.isInteger(rowField) || !Number.isInteger(valueField) || rowField < 0 || valueField < 0 || rowField >= width || valueField >= width) continue;
    pivots.push({
      id: stripText(pivot?.id || `pivot_${index + 1}`, 80),
      title: stripText(pivot?.title || "Pivot table", 120) || "Pivot table",
      ...range,
      rowField,
      valueField,
      aggregate,
    });
  }

  return { charts, pivots, pageSetup: normalizePageSetup(sheet?.pageSetup || {}) };
}

export function createChartConfig(bounds, options = {}) {
  const range = advancedRangeFromBounds(bounds);
  if (!range) return null;
  const parsed = rangeBounds(range);
  if (!parsed || parsed.rowTo <= parsed.rowFrom || parsed.colTo <= parsed.colFrom) return null;
  const type = CHART_TYPES.has(options.type) ? options.type : "bar";
  return {
    id: stripText(options.id || `chart_${Date.now()}`, 80),
    title: stripText(options.title || "Chart", 120) || "Chart",
    type,
    ...range,
    showLegend: options.showLegend !== false,
  };
}

export function createPivotConfig(bounds, options = {}) {
  const range = advancedRangeFromBounds(bounds);
  const parsed = rangeBounds(range);
  if (!parsed || parsed.rowTo <= parsed.rowFrom || parsed.colTo <= parsed.colFrom) return null;
  const width = parsed.colTo - parsed.colFrom + 1;
  const rowField = Number(options.rowField ?? 0);
  const valueField = Number(options.valueField ?? 1);
  const aggregate = PIVOT_AGGREGATES.has(options.aggregate) ? options.aggregate : "sum";
  if (!Number.isInteger(rowField) || !Number.isInteger(valueField) || rowField < 0 || valueField < 0 || rowField >= width || valueField >= width) return null;
  return {
    id: stripText(options.id || `pivot_${Date.now()}`, 80),
    title: stripText(options.title || "Pivot table", 120) || "Pivot table",
    ...range,
    rowField,
    valueField,
    aggregate,
  };
}

export function rangeHeaders(sheet, rangeOrBounds, computedValues = {}) {
  const range = rangeOrBounds?.start ? normalizeRange(rangeOrBounds) : advancedRangeFromBounds(rangeOrBounds);
  const bounds = rangeBounds(range);
  if (!bounds) return [];
  const headers = [];
  for (let col = bounds.colFrom; col <= bounds.colTo; col += 1) {
    const ref = advancedCellRefFromIndex(col, bounds.rowFrom);
    const value = stripText(cellDisplayValue(sheet, ref, computedValues), 80);
    headers.push(value || colIndexToLetters(col));
  }
  return headers;
}

export function chartModel(sheet, chartInput, computedValues = {}) {
  const chart = normalizeAdvancedSheetState({ charts: [chartInput] }).charts[0];
  const bounds = rangeBounds(chart);
  if (!chart || !bounds) return null;
  const headers = rangeHeaders(sheet, chart, computedValues);
  const labels = [];
  const series = [];
  for (let col = bounds.colFrom + 1; col <= bounds.colTo; col += 1) {
    series.push({ name: headers[col - bounds.colFrom] || colIndexToLetters(col), values: [] });
  }
  for (let row = bounds.rowFrom + 1; row <= bounds.rowTo; row += 1) {
    labels.push(String(cellDisplayValue(sheet, advancedCellRefFromIndex(bounds.colFrom, row), computedValues) ?? ""));
    for (let col = bounds.colFrom + 1; col <= bounds.colTo; col += 1) {
      const ref = advancedCellRefFromIndex(col, row);
      series[col - bounds.colFrom - 1].values.push(numericValue(cellDisplayValue(sheet, ref, computedValues)) ?? 0);
    }
  }
  return { id: chart.id, title: chart.title, type: chart.type, labels, series, showLegend: chart.showLegend };
}

function aggregateValues(values, aggregate) {
  if (aggregate === "count") return values.length;
  const numeric = values.map(numericValue).filter((value) => value !== null);
  if (aggregate === "average") return numeric.length ? numeric.reduce((sum, value) => sum + value, 0) / numeric.length : 0;
  return numeric.reduce((sum, value) => sum + value, 0);
}

export function pivotModel(sheet, pivotInput, computedValues = {}) {
  const pivot = normalizeAdvancedSheetState({ pivots: [pivotInput] }).pivots[0];
  const bounds = rangeBounds(pivot);
  if (!pivot || !bounds) return null;
  const headers = rangeHeaders(sheet, pivot, computedValues);
  const groups = new Map();
  for (let row = bounds.rowFrom + 1; row <= bounds.rowTo; row += 1) {
    const rowRef = advancedCellRefFromIndex(bounds.colFrom + pivot.rowField, row);
    const valueRef = advancedCellRefFromIndex(bounds.colFrom + pivot.valueField, row);
    const key = String(cellDisplayValue(sheet, rowRef, computedValues) ?? "").trim() || "(blank)";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(cellDisplayValue(sheet, valueRef, computedValues));
  }
  const rows = Array.from(groups.entries()).map(([label, values]) => ({
    label,
    value: aggregateValues(values, pivot.aggregate),
    count: values.length,
  }));
  const grandValues = Array.from(groups.values()).flat();
  return {
    id: pivot.id,
    title: pivot.title,
    aggregate: pivot.aggregate,
    rowHeader: headers[pivot.rowField] || "Row",
    valueHeader: `${pivot.aggregate.toUpperCase()} ${headers[pivot.valueField] || "Value"}`,
    rows,
    grandTotal: aggregateValues(grandValues, pivot.aggregate),
  };
}

function htmlEscape(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function usedBounds(sheet, computedValues = {}) {
  let maxRow = 0;
  let maxCol = 0;
  const refs = new Set([...Object.keys(sheet?.cells || {}), ...Object.keys(computedValues || {})]);
  for (const ref of refs) {
    const value = cellDisplayValue(sheet, ref, computedValues);
    if (value === "" || value === null || value === undefined) continue;
    const parsed = parseAdvancedCellRef(ref);
    if (!parsed) continue;
    maxRow = Math.max(maxRow, parsed.row);
    maxCol = Math.max(maxCol, parsed.col);
  }
  return { rowTo: Math.min(maxRow, 499), colTo: Math.min(maxCol, 99) };
}

export function buildPrintableSheetHtml(sheet, computedValues = {}, options = {}) {
  const pageSetup = normalizePageSetup(sheet?.pageSetup || {});
  const bounds = usedBounds(sheet, computedValues);
  const border = pageSetup.gridlines ? "1px solid #d4d4d8" : "0";
  const paper = pageSetup.paperSize === "LETTER" ? "letter" : "A4";
  const scaleCss = pageSetup.scale === "fitWidth" ? "width:100%;table-layout:fixed;" : "";
  let rows = "";
  for (let row = 0; row <= bounds.rowTo; row += 1) {
    let cells = "";
    for (let col = 0; col <= bounds.colTo; col += 1) {
      const ref = advancedCellRefFromIndex(col, row);
      cells += `<td style="border:${border};padding:4px 6px;vertical-align:top;overflow-wrap:anywhere">${htmlEscape(cellDisplayValue(sheet, ref, computedValues))}</td>`;
    }
    rows += `<tr>${cells}</tr>`;
  }
  const title = htmlEscape(options.title || sheet?.name || "Sheet");
  return `<!doctype html><html><head><meta charset="utf-8"><title>${title}</title><style>@page{size:${paper} ${pageSetup.orientation};margin:10mm}body{font-family:Arial,sans-serif;color:#18181b}h1{font-size:16px;margin:0 0 10px}table{border-collapse:collapse;${scaleCss}}td{font-size:10px}</style></head><body><h1>${title}</h1><table>${rows}</table></body></html>`;
}
