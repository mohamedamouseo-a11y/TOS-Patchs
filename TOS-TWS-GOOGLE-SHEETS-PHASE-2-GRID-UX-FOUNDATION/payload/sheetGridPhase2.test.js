import test from "node:test";
import assert from "node:assert/strict";
import {
  fillSelection,
  matrixToTsv,
  normalizeSelectionBounds,
  parseClipboardMatrix,
  parseNameBox,
  pastePlainMatrix,
  pasteSelectionMatrix,
  selectionMatrix,
  translateFormulaReferences,
  unionBoundsWithRef,
} from "./sheetGridPhase2.js";

function baseSheet() {
  return {
    id: "s1", name: "Sheet1", rows: 10, cols: 8,
    cells: {
      A1: { v: 10 }, A2: { v: 20 },
      B1: { v: "=A1*2" }, B2: { v: "=SUM(A1:A2)" },
      C1: { v: "مرحبا" },
    },
    formats: { B1: { bold: true }, C1: { align: "right" } },
    protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {},
  };
}

test("name box parses cells and ranges safely", () => {
  assert.deepEqual(parseNameBox("b2:d4"), {
    anchorRef: "B2", focusRef: "D4",
    bounds: { colFrom: 1, colTo: 3, rowFrom: 1, rowTo: 3 },
  });
  assert.equal(parseNameBox("ZZZ9999"), null);
  assert.equal(parseNameBox("not-a-cell"), null);
});

test("clipboard parser and raw selection preserve formulas", () => {
  const sheet = baseSheet();
  const bounds = normalizeSelectionBounds("A1", "B2");
  const matrix = selectionMatrix(sheet, bounds);
  assert.equal(matrix[0][1].value, "=A1*2");
  assert.equal(matrix[1][1].value, "=SUM(A1:A2)");
  assert.match(matrixToTsv(matrix), /=A1\*2/);
  assert.deepEqual(parseClipboardMatrix("1\t2\n3\t4\n"), [["1", "2"], ["3", "4"]]);
});

test("internal paste translates relative formula references and preserves styles", () => {
  const sheet = baseSheet();
  const sourceBounds = normalizeSelectionBounds("A1", "B1");
  const copied = { matrix: selectionMatrix(sheet, sourceBounds), sourceBounds };
  const next = pasteSelectionMatrix(sheet, "A3", copied);
  assert.equal(next.cells.A3.v, 10);
  assert.equal(next.cells.B3.v, "=A3*2");
  assert.equal(next.formats.B3.bold, true);
});

test("external paste writes TSV matrices and grows grid safely", () => {
  const next = pastePlainMatrix(baseSheet(), "G9", [["X", "Y"], ["Z", "W"]]);
  assert.equal(next.cells.G9.v, "X");
  assert.equal(next.cells.H10.v, "W");
  assert.equal(next.rows, 10);
  assert.equal(next.cols, 8);
});

test("fill handle translates formulas and extrapolates numeric series", () => {
  const sheet = baseSheet();
  let next = fillSelection(sheet, normalizeSelectionBounds("B1", "B1"), normalizeSelectionBounds("B1", "B3"));
  assert.equal(next.cells.B2.v, "=A2*2");
  assert.equal(next.cells.B3.v, "=A3*2");

  next = fillSelection(sheet, normalizeSelectionBounds("A1", "A2"), normalizeSelectionBounds("A1", "A5"));
  assert.equal(next.cells.A3.v, 30);
  assert.equal(next.cells.A4.v, 40);
  assert.equal(next.cells.A5.v, 50);
});

test("formula translation and drag bounds stay inside T-Sheets limits", () => {
  assert.equal(translateFormulaReferences("=SUM(A1:B2)+C3", 2, 3), "=SUM(C4:D5)+E6");
  const bounds = unionBoundsWithRef(normalizeSelectionBounds("B2", "C3"), "E8");
  assert.deepEqual(bounds, { colFrom: 1, colTo: 4, rowFrom: 1, rowTo: 7 });
});
