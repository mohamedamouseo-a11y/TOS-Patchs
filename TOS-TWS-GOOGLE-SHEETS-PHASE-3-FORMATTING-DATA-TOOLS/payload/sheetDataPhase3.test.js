import test from "node:test";
import assert from "node:assert/strict";
import {
  addConditionalRule,
  applyFormatPatch,
  clearConditionalRules,
  clearFilter,
  clearFormatting,
  clearValidation,
  conditionalStyleForRef,
  filterUniqueValues,
  isValidCellValue,
  mergeSelection,
  mergedRangeForRef,
  mergeSpan,
  parseConditionalExpression,
  rowMatchesFilter,
  setFilterColumnValues,
  setFilterRange,
  setListValidation,
  unmergeSelection,
  validationForRef,
} from "./sheetDataPhase3.js";

function baseSheet() {
  return {
    id: "s1", name: "Sheet1", rows: 12, cols: 8,
    cells: {
      A1: { v: "Name" }, B1: { v: "Score" },
      A2: { v: "Ahmed" }, B2: { v: 90 },
      A3: { v: "Sara" }, B3: { v: 45 },
      A4: { v: "Ahmed" }, B4: { v: 70 },
      C2: { v: "keep" }, D2: { v: "remove" },
    },
    formats: { B2: { bold: true } },
    merges: [], dataValidations: [], conditionalFormats: [],
    protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {},
  };
}

const bounds = (colFrom, rowFrom, colTo = colFrom, rowTo = rowFrom) => ({ colFrom, rowFrom, colTo, rowTo });

test("merge and unmerge preserve anchor value and expose HTML span", () => {
  let sheet = mergeSelection(baseSheet(), bounds(2, 1, 3, 2));
  assert.equal(sheet.cells.C2.v, "keep");
  assert.equal(sheet.cells.D2, undefined);
  const merge = mergedRangeForRef(sheet, "D3");
  assert.equal(merge.start, "C2");
  assert.deepEqual(mergeSpan(merge), { rowSpan: 2, colSpan: 2 });
  sheet = unmergeSelection(sheet, bounds(3, 2));
  assert.equal(sheet.merges.length, 0);
});

test("format patches support rich text controls and clear formatting", () => {
  let sheet = applyFormatPatch(baseSheet(), bounds(1, 1, 1, 2), {
    italic: true, underline: true, strike: true, wrap: true, vertical: "middle", numberFormat: "percent",
  });
  assert.equal(sheet.formats.B2.italic, true);
  assert.equal(sheet.formats.B3.vertical, "middle");
  sheet = clearFormatting(sheet, bounds(1, 1, 1, 2));
  assert.equal(sheet.formats.B2, undefined);
  assert.equal(sheet.formats.B3, undefined);
});

test("dropdown validation applies to ranges and rejects unknown values", () => {
  let sheet = setListValidation(baseSheet(), bounds(0, 1, 0, 3), ["Ahmed", "Sara"], false);
  assert.deepEqual(validationForRef(sheet, "A3").values, ["Ahmed", "Sara"]);
  assert.equal(isValidCellValue(sheet, "A2", "Ahmed"), true);
  assert.equal(isValidCellValue(sheet, "A2", "Other"), false);
  assert.equal(isValidCellValue(sheet, "A2", ""), false);
  sheet = clearValidation(sheet, bounds(0, 2));
  assert.equal(validationForRef(sheet, "A3"), null);
});

test("conditional formatting parser and evaluator cover numeric and text rules", () => {
  assert.deepEqual(parseConditionalExpression(">= 70"), { type: "greaterOrEqual", value: 70 });
  assert.deepEqual(parseConditionalExpression("contains:Ahmed"), { type: "textContains", value: "Ahmed" });
  assert.deepEqual(parseConditionalExpression("between:40,80"), { type: "between", value: 40, value2: 80 });
  assert.equal(parseConditionalExpression("bad rule"), null);

  let sheet = addConditionalRule(baseSheet(), bounds(1, 1, 1, 3), parseConditionalExpression(">=70"), { bg: "#dcfce7", bold: true });
  assert.deepEqual(conditionalStyleForRef(sheet, "B2", 90), { bg: "#dcfce7", bold: true });
  assert.deepEqual(conditionalStyleForRef(sheet, "B3", 45), {});
  sheet = clearConditionalRules(sheet, bounds(1, 1, 1, 3));
  assert.equal(sheet.conditionalFormats.length, 0);
});

test("filter keeps header visible and applies per-column allowed values", () => {
  let sheet = setFilterRange(baseSheet(), bounds(0, 0, 1, 3));
  assert.deepEqual(filterUniqueValues(sheet, 0, {}), ["Ahmed", "Sara"]);
  sheet = setFilterColumnValues(sheet, 0, ["Ahmed"]);
  assert.equal(rowMatchesFilter(sheet, 0, {}), true);
  assert.equal(rowMatchesFilter(sheet, 1, {}), true);
  assert.equal(rowMatchesFilter(sheet, 2, {}), false);
  assert.equal(rowMatchesFilter(sheet, 3, {}), true);
  sheet = clearFilter(sheet);
  assert.equal(rowMatchesFilter(sheet, 2, {}), true);
});

test("overlapping merges are refused and existing merge stays intact", () => {
  let sheet = mergeSelection(baseSheet(), bounds(0, 5, 1, 6));
  const first = sheet.merges[0];
  sheet = mergeSelection(sheet, bounds(1, 6, 2, 7));
  assert.equal(sheet.merges.length, 1);
  assert.equal(sheet.merges[0].start, first.start);
  assert.equal(sheet.merges[0].end, first.end);
});
