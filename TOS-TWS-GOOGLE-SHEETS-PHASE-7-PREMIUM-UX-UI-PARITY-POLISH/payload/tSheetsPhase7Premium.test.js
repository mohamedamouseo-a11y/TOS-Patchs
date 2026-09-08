import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editorPath = new URL("./TSheetsEditor.jsx", import.meta.url);
const cssPath = new URL("./tSheetsPhase7Premium.css", import.meta.url);

const editor = fs.readFileSync(editorPath, "utf8");
const css = fs.readFileSync(cssPath, "utf8");

test("Phase 7 premium stylesheet is wired into TSheetsEditor", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7Premium.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-premium"));
});

test("Phase 7 semantic visual hooks cover the main spreadsheet surfaces", () => {
  for (const hook of [
    "tws-sheets-chrome",
    "tws-sheets-actions",
    "tws-sheets-toolbar",
    "tws-sheets-formula-strip",
    "tws-sheets-workspace",
    "tws-sheets-grid-scroll",
    "tws-sheets-grid",
    "tws-sheets-tabs",
    "tws-sheets-inspector",
    "tws-sheets-context-menu",
  ]) {
    assert.ok(editor.includes(hook), `missing editor hook: ${hook}`);
    assert.ok(css.includes(`.${hook}`), `missing stylesheet hook: ${hook}`);
  }
});

test("Phase 7 keeps Tamiyouz accent and provides light/dark premium surfaces", () => {
  assert.ok(css.includes("--ts7-accent:"));
  assert.ok(css.includes(".dark .tws-sheets-phase7-premium"));
  assert.ok(css.includes("--ts7-surface:"));
  assert.ok(css.includes("--ts7-line:"));
});

test("Phase 7 provides focused-cell, tabs, toolbar and context-menu fidelity", () => {
  assert.ok(css.includes(".tws-sheets-grid td:focus-within"));
  assert.ok(css.includes(".tws-sheets-tabs"));
  assert.ok(css.includes(".tws-sheets-toolbar"));
  assert.ok(css.includes(".tws-sheets-context-menu"));
  assert.ok(css.includes("box-shadow"));
});

test("Phase 7 includes responsive and reduced-motion safeguards", () => {
  assert.ok(css.includes("@media (max-width: 1180px)"));
  assert.ok(css.includes("@media (max-width: 720px)"));
  assert.ok(css.includes("@media (prefers-reduced-motion: reduce)"));
});

test("Phase 7 remains visual-only and preserves established functional wiring", () => {
  for (const existingFeature of [
    "computeSheetValues",
    "buildSheetCollabPatch",
    "addChartAction",
    "addPivotAction",
    "printCurrentSheet",
    "addNamedRange",
    "handleImportXlsx",
    "undo",
    "redo",
  ]) assert.ok(editor.includes(existingFeature), `existing feature missing: ${existingFeature}`);
});
