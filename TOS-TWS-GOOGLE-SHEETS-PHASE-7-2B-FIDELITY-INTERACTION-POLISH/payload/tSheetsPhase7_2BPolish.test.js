import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSheetsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSheetsPhase7_2BPolish.css", import.meta.url), "utf8");

function includesAll(source, values) {
  for (const value of values) assert.ok(source.includes(value), `missing: ${value}`);
}

test("Phase 7.2B stylesheet and root hook are wired", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7_2BPolish.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-2b-polish"));
  assert.ok(css.includes(".tws-sheets-phase7-2b-polish"));
});

test("flat spreadsheet cells and strong active selection are styled", () => {
  includesAll(css, [
    ".tws-sheets-grid td.tws-sheets-cell-focused",
    ".tws-sheets-grid td.tws-sheets-cell-selected",
    "border-radius: 0 !important",
    "box-shadow: inset 0 0 0 2px var(--ts72b-active)",
  ]);
  assert.ok(editor.includes('isFocused && "tws-sheets-cell-focused"'));
  assert.ok(editor.includes('isSelected && "tws-sheets-cell-selected"'));
});

test("focused row and column headers receive active-axis classes", () => {
  assert.ok(editor.includes('focusedParsed?.col === col && "tws-sheets-axis-active"'));
  assert.ok(editor.includes('focusedParsed?.row === row && "tws-sheets-axis-active"'));
  assert.ok(css.includes(".tws-sheets-axis-active"));
});

test("dark and light toolbar/formula controls are visually unified", () => {
  includesAll(css, [
    ".tws-sheets-toolbar-compact button",
    ".tws-sheets-formula-strip-compact",
    ".dark .tws-sheets-phase7-2b-polish",
    "--ts72b-control-hover",
  ]);
});

test("Find & Replace uses a non-blocking in-app panel", () => {
  includesAll(editor, [
    "findReplacePanel",
    "function openFindReplacePanel()",
    "function findNextMatch()",
    "function replaceAllMatches()",
    "tws-sheets-find-replace-panel",
    "tws-sheets-find-replace-grid",
  ]);
  assert.ok(!editor.includes('const needleRaw = window.prompt(ui.lang === "en" ? "Find in this sheet:"'));
});

test("Paste Special supports values-only and format-only from copied selection", () => {
  includesAll(editor, [
    "valueMatrix",
    "formatMatrix",
    "function pasteSpecialValuesAction()",
    "function pasteSpecialFormatsAction()",
    "Paste values only",
    "Paste format only",
  ]);
});

test("sheet tabs support drag reorder and polished active/add states", () => {
  includesAll(editor, [
    "dragSheetId",
    "function reorderSheetsByIds(sourceId, targetId)",
    "draggable={canEdit}",
    "onDragStart",
    "onDrop",
    "tws-sheets-tab-active",
    "tws-sheets-tab-add",
  ]);
  includesAll(css, [".tws-sheets-tab-active", ".tws-sheets-tab-add", ".tws-sheets-tab-dragging"]);
});

test("Phase 7.2A menu, zoom, sheet context and shortcut work remains present", () => {
  includesAll(editor, [
    "closeSiblingSpreadsheetMenus",
    "tws-sheets-zoom-control",
    "sheetZoom",
    "sheetTabMenu",
    "duplicateSheet",
    'event.key.toLowerCase() === "h"',
  ]);
});

test("established power features stay wired", () => {
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

test("Phase 7.2B remains responsive and reduced-motion safe", () => {
  includesAll(css, [
    "@media (max-width: 900px)",
    "@media (prefers-reduced-motion: reduce)",
  ]);
});
