import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSheetsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSheetsPhase7_2CFinal.css", import.meta.url), "utf8");

function includesAll(source, values) {
  for (const value of values) assert.ok(source.includes(value), `missing: ${value}`);
}

test("Phase 7.2C stylesheet and root hook are wired", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7_2CFinal.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-2c-final"));
  assert.ok(css.includes(".tws-sheets-phase7-2c-final"));
});

test("active cell selection is stronger and keeps a spreadsheet fill handle", () => {
  includesAll(css, [
    ".tws-sheets-grid td.tws-sheets-cell-focused",
    "inset 0 0 0 2px var(--ts72c-active-strong)",
    ".tws-sheets-grid td.tws-sheets-cell-focused::after",
    "background: var(--ts72c-active-strong)",
  ]);
});

test("selected ranges keep a subtle tint without rounded card cells", () => {
  includesAll(css, [
    ".tws-sheets-cell-selected:not(.tws-sheets-cell-focused)",
    "background-image: linear-gradient(var(--ts72c-active-softer), var(--ts72c-active-softer))",
    "border-radius: 0 !important",
  ]);
});

test("active row and column headers have stronger axis states", () => {
  includesAll(css, [
    "thead th.tws-sheets-axis-active",
    "tbody > tr > td:first-child.tws-sheets-axis-active",
    "inset 0 -3px 0 var(--ts72c-active-strong)",
    "inset -3px 0 0 var(--ts72c-active-strong)",
  ]);
  assert.ok(editor.includes("tws-sheets-axis-active"));
});

test("dark gridlines are softer and controls remain flat", () => {
  includesAll(css, [
    "--ts72c-grid: rgba(255, 255, 255, 0.072)",
    "--ts72c-grid-header: rgba(255, 255, 255, 0.11)",
    ".dark .tws-sheets-phase7-2c-final .tws-sheets-grid input",
    "background: transparent !important",
  ]);
});

test("toolbar dark and light controls use one coherent visual language", () => {
  includesAll(css, [
    ".tws-sheets-toolbar-compact button",
    ".tws-sheets-toolbar-compact select",
    "button[aria-pressed=\"true\"]",
    "button:disabled",
    "--ts72c-control-hover",
  ]);
});

test("formula bar gets clearer contrast and hierarchy", () => {
  includesAll(css, [
    ".tws-sheets-formula-strip-compact",
    ".tws-sheets-formula-strip-compact > input:first-child",
    ".tws-sheets-fx",
    "border-bottom: 1px solid var(--ts7-line)",
  ]);
});

test("sheet tabs and add button are dark-safe with a stronger active state", () => {
  includesAll(css, [
    ".tws-sheets-tabs > button.tws-sheets-tab-active",
    ".tws-sheets-tab-add",
    "inset 0 -3px 0 var(--ts72c-active-strong)",
    "background: transparent !important",
  ]);
});

test("Phase 7.2B interaction work remains wired", () => {
  includesAll(editor, [
    'import "./tSheetsPhase7_2BPolish.css";',
    "tws-sheets-phase7-2b-polish",
    "pasteSpecialValuesAction",
    "pasteSpecialFormatsAction",
    "findReplacePanel",
    "reorderSheetsByIds",
    "tws-sheets-tab-active",
  ]);
});

test("Phase 7.2C remains responsive and reduced-motion safe", () => {
  includesAll(css, [
    "@media (max-width: 900px)",
    "@media (prefers-reduced-motion: reduce)",
    "scrollbar-width: thin",
  ]);
});
