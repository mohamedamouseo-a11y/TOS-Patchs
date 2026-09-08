import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSheetsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSheetsPhase7_2DDarkFidelity.css", import.meta.url), "utf8");

function includesAll(source, values) {
  for (const value of values) assert.ok(source.includes(value), `missing: ${value}`);
}

test("Phase 7.2D stylesheet and root hook are wired", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7_2DDarkFidelity.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-2d-dark-fidelity"));
  assert.ok(css.includes(".tws-sheets-phase7-2d-dark-fidelity"));
});

test("dark editor resets to a coherent charcoal surface family", () => {
  includesAll(css, [
    "--ts7-bg: #202124",
    "--ts7-surface: #202124",
    "--ts7-surface-soft: #28292c",
    "--ts7-surface-muted: #303134",
    "--ts7-line: #3c4043",
    "--ts7-text: #e8eaed",
  ]);
});

test("dark toolbar explicitly neutralizes legacy white utility classes", () => {
  includesAll(css, [
    '.tws-sheets-toolbar-compact [class*="bg-white"]',
    '.tws-sheets-toolbar-compact [class*="dark:bg-white"]',
    '.tws-sheets-toolbar-compact [class*="bg-zinc-950"]',
    "background: transparent !important",
    "color: #e8eaed !important",
  ]);
});

test("dark formula bar removes the mid-grey slab", () => {
  includesAll(css, [
    ".tws-sheets-formula-strip-compact input",
    ".tws-sheets-formula-strip-compact textarea",
    '.tws-sheets-formula-strip-compact [contenteditable="true"]',
    "background: #202124 !important",
  ]);
});

test("dark document title no longer looks disabled", () => {
  includesAll(css, [
    ".tws-sheets-chrome > input",
    "border: 1px solid transparent !important",
    "opacity: 1 !important",
  ]);
});

test("spreadsheet selection uses one familiar blue selection language", () => {
  includesAll(css, [
    "--ts72d-selection: #8ab4f8",
    ".tws-sheets-cell-focused",
    ".tws-sheets-cell-focused::after",
    ".tws-sheets-axis-active",
    "var(--ts72d-selection)",
  ]);
});

test("dark active row and column headers stay charcoal instead of cream", () => {
  includesAll(css, [
    "background: var(--ts72d-selection-axis) !important",
    "color: #aecbfa !important",
    "inset 0 -2px 0 var(--ts72d-selection)",
    "inset -2px 0 0 var(--ts72d-selection)",
  ]);
});

test("dark sheet tabs and add button cannot render as white cards", () => {
  includesAll(css, [
    ".tws-sheets-tab-add",
    '.tws-sheets-tabs > button[class*="dark:bg-white"]',
    '.tws-sheets-tabs > button[class*="bg-white"]',
    "background: #28292c !important",
  ]);
});

test("Phase 7.2A through 7.2C work remains wired", () => {
  includesAll(editor, [
    'import "./tSheetsPhase7_2GoogleParity.css";',
    'import "./tSheetsPhase7_2BPolish.css";',
    'import "./tSheetsPhase7_2CFinal.css";',
    "tws-sheets-phase7-2-google-parity",
    "tws-sheets-phase7-2b-polish",
    "tws-sheets-phase7-2c-final",
    "pasteSpecialValuesAction",
    "findReplacePanel",
    "reorderSheetsByIds",
  ]);
});

test("Phase 7.2D is visual-only and reduced-motion safe", () => {
  includesAll(css, ["@media (prefers-reduced-motion: reduce)"]);
  for (const forbidden of ["fetch(", "axios", "api.", "localStorage", "sessionStorage"]) {
    assert.ok(!css.includes(forbidden), `visual CSS must not contain ${forbidden}`);
  }
});
