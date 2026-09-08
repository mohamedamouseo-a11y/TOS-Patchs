import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSheetsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSheetsPhase7_2GoogleParity.css", import.meta.url), "utf8");

function includesAll(source, values) {
  for (const value of values) assert.ok(source.includes(value), `missing: ${value}`);
}

test("Phase 7.2 stylesheet and root hook are wired", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7_2GoogleParity.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-2-google-parity"));
  assert.ok(css.includes(".tws-sheets-phase7-2-google-parity"));
});

test("spreadsheet menus enforce single-open behavior and close after actions", () => {
  assert.ok(editor.includes("function closeSiblingSpreadsheetMenus"));
  assert.ok((editor.match(/onToggle=\{\(event\) => closeSiblingSpreadsheetMenus\(event\.currentTarget\)\}/g) || []).length >= 7);
  assert.ok(editor.includes('querySelectorAll("details.tws-sheets-menu[open]")'));
});

test("toolbar gains print, zoom, currency, and percent quick controls", () => {
  includesAll(editor, [
    "onClick={printCurrentSheet}",
    "tws-sheets-zoom-control",
    "setSheetZoom(Number(event.target.value))",
    "tws-sheets-number-shortcut",
    'toggleFormat(focusedRef, "numberFormat", "currency")',
    'toggleFormat(focusedRef, "numberFormat", "percent")',
  ]);
  assert.ok(css.includes(".tws-sheets-zoom-control"));
  assert.ok(css.includes(".tws-sheets-number-shortcut"));
});

test("grid fills viewport and supports spreadsheet zoom", () => {
  assert.ok(editor.includes("style={{ zoom: sheetZoom / 100 }}"));
  assert.ok(css.includes("width: max-content !important"));
  assert.ok(css.includes("min-width: 100% !important"));
  assert.ok(css.includes("--ts72-row-height: 28px"));
});

test("formula bar keeps Name Box + fx + long formula input hierarchy", () => {
  includesAll(editor, ["tws-sheets-formula-strip-compact", "tws-sheets-fx", "nameBoxDraft || selectedRangeLabel", "activeSheet?.cells?.[focusedRef]?.v"]);
  assert.ok(css.includes("grid-template-columns: 92px 30px minmax(260px, 1fr)"));
  assert.ok(css.includes(".tws-sheets-formula-meta"));
  assert.ok(css.includes("display: none !important"));
});

test("sheet tabs use a safe context menu with rename duplicate delete", () => {
  includesAll(editor, [
    "sheetTabMenu",
    "setSheetTabMenu({ x: event.clientX, y: event.clientY, sheetId: sheet.id })",
    "function duplicateSheet(sheetId)",
    "tws-sheets-sheet-tab-menu",
    "renameSheet(sheetTabMenu.sheetId)",
    "duplicateSheet(sheetTabMenu.sheetId)",
    "removeSheet(sheetTabMenu.sheetId)",
  ]);
  assert.ok(!editor.includes("onContextMenu={(event) => { event.preventDefault(); if (canEdit) removeSheet(sheet.id); }}"));
});

test("Find & Replace and familiar formatting/print shortcuts are present", () => {
  includesAll(editor, [
    "function findReplaceAction()",
    'event.key.toLowerCase() === "h"',
    '["b", "i", "u"].includes(event.key.toLowerCase())',
    'event.key.toLowerCase() === "p"',
    "findReplaceAction",
  ]);
});

test("established T-Sheets power features remain wired", () => {
  includesAll(editor, [
    "computeSheetValues",
    "buildSheetCollabPatch",
    "addChartAction",
    "addPivotAction",
    "addNamedRange",
    "handleImportXlsx",
    "mergeSelectionAction",
    "addConditionalFormattingAction",
    "protectSelection",
    "useTwsPresence",
  ]);
});

test("Phase 7 and 7.1 layers remain preserved", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7Premium.css";'));
  assert.ok(editor.includes('import "./tSheetsPhase7_1Restructure.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-premium"));
  assert.ok(editor.includes("tws-sheets-phase7-1-restructure"));
});

test("Phase 7.2 supports dark, responsive, and reduced-motion modes", () => {
  includesAll(css, [
    ".dark .tws-sheets-phase7-2-google-parity",
    "@media (max-width: 1180px)",
    "@media (max-width: 760px)",
    "@media (prefers-reduced-motion: reduce)",
  ]);
});
