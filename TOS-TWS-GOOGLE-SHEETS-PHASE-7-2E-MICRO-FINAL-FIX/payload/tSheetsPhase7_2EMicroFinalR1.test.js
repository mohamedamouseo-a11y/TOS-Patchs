import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSheetsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSheetsPhase7_2EMicroFinalR1.css", import.meta.url), "utf8");

function includesAll(source, values) {
  for (const value of values) assert.ok(source.includes(value), `missing: ${value}`);
}

test("Phase 7.2E R1 stylesheet and root hook are wired", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7_2EMicroFinalR1.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-2e-micro-final"));
  assert.ok(css.includes(".tws-sheets-phase7-2e-micro-final"));
});

test("dark title stays readable even when disabled in Chromium", () => {
  includesAll(css, [
    ".tws-sheets-chrome > input:disabled",
    "-webkit-text-fill-color: #e8eaed !important",
    "color: #e8eaed !important",
    "opacity: 1 !important",
  ]);
});

test("active cell and fill handle use one blue selection language", () => {
  includesAll(css, [
    "--ts72e-selection: #8ab4f8",
    ".tws-sheets-cell-focused",
    ".tws-sheets-cell-focused::after",
    'button[class*="cursor-crosshair"][class*="bg-amber-500"]',
    "background: var(--ts72e-selection) !important",
  ]);
});

test("legacy amber focus and fill preview are neutralized visually", () => {
  includesAll(css, [
    ".tws-sheets-grid input:focus",
    ".tws-sheets-grid textarea:focus",
    ".tws-sheets-grid select:focus",
    'td[class*="ring-amber-500"]',
    "--tw-ring-color: var(--ts72e-selection) !important",
  ]);
});

test("active row and column axes remain in the blue family", () => {
  includesAll(css, [
    "thead th.tws-sheets-axis-active",
    "tbody > tr > td:first-child.tws-sheets-axis-active",
    "color: #aecbfa !important",
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
  ]);
});

test("interaction features from Phase 7.2 remain intact", () => {
  includesAll(editor, [
    "pasteSpecialValuesAction",
    "pasteSpecialFormatsAction",
    "findReplacePanel",
    "reorderSheetsByIds",
    "tws-sheets-tab-active",
  ]);
});

test("Phase 7.2E R1 is visual-only and reduced-motion safe", () => {
  assert.ok(css.includes("@media (prefers-reduced-motion: reduce)"));
  for (const forbidden of ["fetch(", "axios", "api.", "localStorage", "sessionStorage"]) {
    assert.ok(!css.includes(forbidden), `visual CSS must not contain ${forbidden}`);
  }
});
