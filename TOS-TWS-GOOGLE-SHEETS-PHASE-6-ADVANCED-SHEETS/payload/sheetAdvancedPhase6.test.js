import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

import * as advanced from "./sheetAdvancedPhase6.js";
import * as frontendAdvanced from "../../../frontend/src/pages/tws/sheetAdvancedPhase6.js";
import { applySheetCollabPatch, buildSheetCollabPatch } from "./sheetCollabPhase5.js";

function baseSheet() {
  return {
    id: "sheet_1", name: "Sales", rows: 20, cols: 8,
    cells: {
      A1: { v: "Region" }, B1: { v: "Revenue" }, C1: { v: "Orders" },
      A2: { v: "Riyadh" }, B2: { v: 100 }, C2: { v: 2 },
      A3: { v: "Jeddah" }, B3: { v: 60 }, C3: { v: 3 },
      A4: { v: "Riyadh" }, B4: { v: 40 }, C4: { v: 1 },
    },
    formats: {},
    merges: [], dataValidations: [], conditionalFormats: [], filter: null,
    charts: [], pivots: [], pageSetup: {},
    protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {},
  };
}

test("Phase 6 chart model uses first column as labels and numeric series", () => {
  const sheet = baseSheet();
  const chart = advanced.createChartConfig({ colFrom: 0, colTo: 2, rowFrom: 0, rowTo: 3 }, { id: "chart_1", type: "bar", title: "Revenue" });
  const model = advanced.chartModel(sheet, chart);
  assert.deepEqual(model.labels, ["Riyadh", "Jeddah", "Riyadh"]);
  assert.equal(model.series[0].name, "Revenue");
  assert.deepEqual(model.series[0].values, [100, 60, 40]);
  assert.equal(model.series[1].name, "Orders");
});

test("Phase 6 pivot supports sum, count and average", () => {
  const sheet = baseSheet();
  const bounds = { colFrom: 0, colTo: 2, rowFrom: 0, rowTo: 3 };
  const sumPivot = advanced.createPivotConfig(bounds, { id: "p1", rowField: 0, valueField: 1, aggregate: "sum" });
  const sum = advanced.pivotModel(sheet, sumPivot);
  assert.deepEqual(sum.rows, [{ label: "Riyadh", value: 140, count: 2 }, { label: "Jeddah", value: 60, count: 1 }]);
  assert.equal(sum.grandTotal, 200);
  assert.equal(advanced.pivotModel(sheet, { ...sumPivot, id: "p2", aggregate: "count" }).grandTotal, 3);
  assert.equal(advanced.pivotModel(sheet, { ...sumPivot, id: "p3", aggregate: "average" }).rows[0].value, 70);
});

test("Phase 6 sanitizer keeps only valid advanced state and normalizes page setup", () => {
  const state = advanced.normalizeAdvancedSheetState({
    charts: [
      { id: "ok", type: "line", start: "A1", end: "C4", title: "<b>Trend</b>" },
      { id: "bad", type: "radar", start: "A1", end: "C4" },
    ],
    pivots: [
      { id: "pv", start: "A1", end: "C4", rowField: 0, valueField: 1, aggregate: "average" },
      { id: "badpv", start: "A1", end: "B2", rowField: 9, valueField: 1, aggregate: "sum" },
    ],
    pageSetup: { orientation: "landscape", paperSize: "letter", scale: "actual", gridlines: false },
  });
  assert.equal(state.charts.length, 1);
  assert.equal(state.charts[0].title, "Trend");
  assert.equal(state.pivots.length, 1);
  assert.deepEqual(state.pageSetup, { orientation: "landscape", paperSize: "LETTER", scale: "actual", gridlines: false });
});

test("Phase 6 printable HTML escapes cell content and carries page settings", () => {
  const sheet = baseSheet();
  sheet.cells.A2 = { v: "<script>alert(1)</script>" };
  sheet.pageSetup = { orientation: "landscape", paperSize: "A4", scale: "fitWidth", gridlines: true };
  const html = advanced.buildPrintableSheetHtml(sheet, {}, { title: "Quarter <1>" });
  assert.ok(html.includes("size:A4 landscape"));
  assert.ok(html.includes("Quarter &lt;1&gt;"));
  assert.ok(!html.includes("<script>alert(1)</script>"));
});

test("Phase 6 collaboration patches advanced structural state without losing remote cells", () => {
  const before = baseSheet();
  const after = {
    ...before,
    charts: [advanced.createChartConfig({ colFrom: 0, colTo: 2, rowFrom: 0, rowTo: 3 }, { id: "chart_1" })],
    pivots: [advanced.createPivotConfig({ colFrom: 0, colTo: 2, rowFrom: 0, rowTo: 3 }, { id: "pivot_1", rowField: 0, valueField: 1 })],
    pageSetup: { orientation: "landscape", paperSize: "A4", scale: "fitWidth", gridlines: false },
  };
  const patch = buildSheetCollabPatch(before, after, { mutationId: "advanced" });
  assert.ok(Object.prototype.hasOwnProperty.call(patch.replace, "charts"));
  assert.ok(Object.prototype.hasOwnProperty.call(patch.replace, "pivots"));
  assert.ok(Object.prototype.hasOwnProperty.call(patch.replace, "pageSetup"));
  const content = { sheets: [{ ...before, cells: { ...before.cells, Z1: { v: "remote" } } }] };
  const merged = applySheetCollabPatch(content, patch);
  assert.equal(merged.sheets[0].cells.Z1.v, "remote");
  assert.equal(merged.sheets[0].charts.length, 1);
});

test("Phase 6 frontend/backend advanced helper parity", () => {
  const sheet = baseSheet();
  const chart = advanced.createChartConfig({ colFrom: 0, colTo: 2, rowFrom: 0, rowTo: 3 }, { id: "same", type: "pie" });
  assert.deepEqual(frontendAdvanced.chartModel(sheet, chart), advanced.chartModel(sheet, chart));
  assert.deepEqual(frontendAdvanced.normalizeAdvancedSheetState(sheet), advanced.normalizeAdvancedSheetState(sheet));
});

test("Phase 6 wiring persists charts pivots page setup and exposes editor tools", () => {
  const service = fs.readFileSync(new URL("../services/workspace.service.js", import.meta.url), "utf8");
  const editor = fs.readFileSync(new URL("../../../frontend/src/pages/tws/TSheetsEditor.jsx", import.meta.url), "utf8");
  const backendCollab = fs.readFileSync(new URL("./sheetCollabPhase5.js", import.meta.url), "utf8");
  assert.ok(service.includes("normalizeAdvancedSheetState"));
  assert.ok(service.includes("charts: advancedState.charts"));
  assert.ok(service.includes("pivots: advancedState.pivots"));
  assert.ok(editor.includes("addChartAction"));
  assert.ok(editor.includes("addPivotAction"));
  assert.ok(editor.includes("printCurrentSheet"));
  assert.ok(editor.includes("AdvancedChartPreview"));
  assert.ok(backendCollab.includes('"charts", "pivots", "pageSetup"'));
});
