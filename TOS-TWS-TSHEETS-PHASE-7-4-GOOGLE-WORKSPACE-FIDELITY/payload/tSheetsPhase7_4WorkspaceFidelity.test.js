import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSheetsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSheetsPhase7_4WorkspaceFidelity.css", import.meta.url), "utf8");

test("phase 7.4 workspace fidelity is wired into T-Sheets", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7_4WorkspaceFidelity.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-4-workspace-fidelity"));
});

test("phase 7.4 keeps the existing Sheets workspace architecture", () => {
  for (const token of [
    "tws-sheets-chrome",
    "tws-sheets-toolbar-compact",
    "tws-sheets-formula-strip-compact",
    "tws-sheets-grid",
    "tws-sheets-cell-selected",
    "tws-sheets-cell-focused",
    "tws-sheets-tabs",
    "tws-sheets-inspector",
  ]) assert.ok(css.includes(token), `missing ${token}`);
});

test("phase 7.4 provides light/dark spreadsheet selection fidelity", () => {
  assert.ok(css.includes("--ts74-green: #0f9d58"));
  assert.ok(css.includes(".dark .tws-sheets-phase7-4-workspace-fidelity"));
  assert.ok(css.includes("box-shadow: inset 0 0 0 2px var(--ts74-green)"));
  assert.ok(css.includes("color-scheme: dark"));
});

test("phase 7.4 preserves single-row responsive toolbar and formula bar", () => {
  assert.ok(css.includes("flex-wrap: nowrap !important"));
  assert.ok(css.includes("overflow-x: auto !important"));
  assert.ok(css.includes("grid-template-columns: 86px 32px minmax(260px, 1fr)"));
  assert.ok(css.includes("@media (max-width: 760px)"));
});
