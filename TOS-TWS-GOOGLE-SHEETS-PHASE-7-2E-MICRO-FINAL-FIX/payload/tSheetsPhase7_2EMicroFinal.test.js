import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSheetsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSheetsPhase7_2EMicroFinal.css", import.meta.url), "utf8");

function includesAll(source, values) {
  for (const value of values) assert.ok(source.includes(value), `missing: ${value}`);
}

test("Phase 7.2E stylesheet and root hook are wired", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7_2EMicroFinal.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-2e-micro-final"));
  assert.ok(css.includes(".tws-sheets-phase7-2e-micro-final"));
});

test("dark title has explicit glyph fill including disabled state", () => {
  includesAll(editor, ["tws-sheets-title-input"]);
  includesAll(css, [
    ".tws-sheets-title-input:disabled",
    "color: #e8eaed !important",
    "-webkit-text-fill-color: #e8eaed !important",
    "opacity: 1 !important",
  ]);
});

test("fill handle uses a dedicated blue selection hook", () => {
  includesAll(editor, ["tws-sheets-fill-handle"]);
  includesAll(css, [
    ".tws-sheets-fill-handle",
    "background: var(--ts72e-selection) !important",
    "border-color: #202124 !important",
  ]);
});

test("fill preview no longer depends on amber ring utility", () => {
  includesAll(editor, ["tws-sheets-fill-preview"]);
  assert.ok(!editor.includes('fillPreviewRef === ref && "ring-2 ring-inset ring-amber-500"'));
  assert.ok(css.includes("--tw-ring-color: var(--ts72e-selection) !important"));
});

test("active cell and focus-within share one blue selection language", () => {
  includesAll(css, [
    "td.tws-sheets-cell-focused",
    "td:focus-within",
    "box-shadow: inset 0 0 0 2px var(--ts72e-selection) !important",
    "td.tws-sheets-cell-focused::after",
  ]);
});

test("legacy amber focus background cannot tint the selected cell", () => {
  includesAll(css, [
    ".tws-sheets-grid input:focus",
    ".tws-sheets-grid textarea:focus",
    ".tws-sheets-grid select:focus",
    "background: transparent !important",
  ]);
});

test("Phase 7.2A through 7.2D remain wired", () => {
  includesAll(editor, [
    'import "./tSheetsPhase7_2GoogleParity.css";',
    'import "./tSheetsPhase7_2BPolish.css";',
    'import "./tSheetsPhase7_2CFinal.css";',
    'import "./tSheetsPhase7_2DDarkFidelity.css";',
    "tws-sheets-phase7-2-google-parity",
    "tws-sheets-phase7-2b-polish",
    "tws-sheets-phase7-2c-final",
    "tws-sheets-phase7-2d-dark-fidelity",
    "pasteSpecialValuesAction",
    "findReplacePanel",
    "reorderSheetsByIds",
  ]);
});

test("Phase 7.2E is visual-only and reduced-motion safe", () => {
  assert.ok(css.includes("@media (prefers-reduced-motion: reduce)"));
  for (const forbidden of ["fetch(", "axios", "api.", "localStorage", "sessionStorage"]) {
    assert.ok(!css.includes(forbidden), `visual CSS must not contain ${forbidden}`);
  }
});
