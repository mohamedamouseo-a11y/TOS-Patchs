import test from "node:test";
import assert from "node:assert/strict";
import { insertSheetRows, insertSheetColumns, remapNamedRangesForInsert } from "./sheetStructurePhase8.js";

function baseSheet() {
  return {
    id: "s1", name: "Sheet1", rows: 10, cols: 8,
    cells: { A1: { v: "Header" }, A2: { v: 10 }, B2: { v: "=A2*2" }, C5: { v: "=SUM(A2:A5)" }, D2: { v: "='Other'!A2+A2" } },
    formats: { A2: { bold: true }, C5: { bg: "#fff" } },
    merges: [{ id: "m1", start: "A2", end: "B3" }],
    dataValidations: [{ id: "v1", start: "C2", end: "C4", type: "list", values: ["A", "B"] }],
    conditionalFormats: [{ id: "c1", start: "D2", end: "D6", type: "notEmpty" }],
    protectedRanges: [{ id: "p1", start: "E2", end: "E3" }],
    filter: { start: "A1", end: "D6", criteria: { "0": { values: ["Header"] }, "2": { values: ["x"] } } },
    charts: [{ id: "ch1", type: "bar", start: "A1", end: "C5" }],
    pivots: [{ id: "pv1", start: "A1", end: "D5", rowField: 0, valueField: 2, aggregate: "sum" }],
    freeze: { rows: 1, cols: 1 }, rowHeights: { "2": 44 }, colWidths: { "2": 140 },
  };
}

test("insert row above shifts content, metadata and formula refs", () => {
  const next = insertSheetRows(baseSheet(), 1, 1, { maxRows: 500 });
  assert.equal(next.rows, 11);
  assert.equal(next.cells.A3.v, 10);
  assert.equal(next.cells.B3.v, "=A3*2");
  assert.equal(next.cells.C6.v, "=SUM(A3:A6)");
  assert.equal(next.cells.D3.v, "='Other'!A2+A3");
  assert.deepEqual(next.formats.A3, { bold: true });
  assert.deepEqual(next.merges[0], { id: "m1", start: "A3", end: "B4" });
  assert.equal(next.rowHeights["3"], 44);
  assert.deepEqual(next.filter.start, "A1");
  assert.deepEqual(next.filter.end, "D7");
});

test("insert column left shifts content, filter criteria and pivot field indexes", () => {
  const next = insertSheetColumns(baseSheet(), 1, 1, { maxCols: 100 });
  assert.equal(next.cols, 9);
  assert.equal(next.cells.A2.v, 10);
  assert.equal(next.cells.C2.v, "=A2*2");
  assert.equal(next.cells.D5.v, "=SUM(A2:A5)");
  assert.equal(next.colWidths["3"], 140);
  assert.ok(next.filter.criteria["0"]);
  assert.ok(next.filter.criteria["3"]);
  assert.equal(next.pivots[0].valueField, 3);
  assert.equal(next.charts[0].end, "D5");
});

test("inserting inside a range expands the range instead of moving its start", () => {
  const next = insertSheetRows(baseSheet(), 2, 1, { maxRows: 500 });
  assert.equal(next.merges[0].start, "A2");
  assert.equal(next.merges[0].end, "B4");
  assert.equal(next.dataValidations[0].start, "C2");
  assert.equal(next.dataValidations[0].end, "C5");
});

test("named ranges on active sheet move/expand; other sheets stay untouched", () => {
  const ranges = [
    { id: "n1", sheetId: "s1", start: "A2", end: "B4" },
    { id: "n2", sheetId: "s2", start: "A2", end: "B4" },
  ];
  const next = remapNamedRangesForInsert(ranges, "s1", "row", 2, 1);
  assert.deepEqual(next[0], { id: "n1", sheetId: "s1", start: "A2", end: "B5" });
  assert.deepEqual(next[1], ranges[1]);
});

test("insert respects configured grid limit", () => {
  const sheet = { ...baseSheet(), rows: 500 };
  assert.equal(insertSheetRows(sheet, 2, 1, { maxRows: 500 }), sheet);
});
