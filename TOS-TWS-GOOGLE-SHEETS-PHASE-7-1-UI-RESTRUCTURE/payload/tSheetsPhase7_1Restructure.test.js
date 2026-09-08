import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSheetsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSheetsPhase7_1Restructure.css", import.meta.url), "utf8");

test("Phase 7.1 restructure stylesheet and root hook are wired", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7_1Restructure.css";'));
  assert.ok(editor.includes("tws-sheets-phase7-1-restructure"));
  assert.ok(css.includes(".tws-sheets-phase7-1-restructure"));
});

test("Phase 7.1 introduces familiar spreadsheet menu hierarchy", () => {
  assert.ok(editor.includes("tws-sheets-menu-strip"));
  for (const label of ['"File"', '"Edit"', '"View"', '"Insert"', '"Format"', '"Data"', '"Tools"']) {
    assert.ok(editor.includes(label), `missing menu label ${label}`);
  }
  for (const action of ["addChartAction", "addPivotAction", "addDropdownValidationAction", "addNamedRange", "createFilterAction", "protectSelection"]) {
    assert.ok(editor.includes(action), `missing menu action ${action}`);
  }
});

test("Phase 7.1 header keeps collaboration primary and moves secondary actions into More", () => {
  assert.ok(editor.includes("tws-sheets-actions-compact"));
  assert.ok(editor.includes("tws-sheets-share-primary"));
  assert.ok(editor.includes("tws-sheets-more-menu"));
  assert.ok(editor.includes("setShowComments"));
  assert.ok(editor.includes("setShowPermissions"));
  assert.ok(editor.includes("setShowVersions"));
  assert.ok(editor.includes("setShowShareLink"));
});

test("Phase 7.1 compact toolbar removes advanced button wall", () => {
  const start = editor.indexOf('className="tws-sheets-toolbar tws-sheets-toolbar-compact');
  const end = editor.indexOf('className="tws-sheets-formula-strip tws-sheets-formula-strip-compact', start);
  assert.ok(start >= 0 && end > start);
  const toolbar = editor.slice(start, end);
  assert.ok(toolbar.includes("toggleFormat"));
  assert.ok(toolbar.includes("createFilterAction"));
  assert.ok(toolbar.includes("setShowSheetPanel"));
  assert.ok(!toolbar.includes("addPivotAction"));
  assert.ok(!toolbar.includes("mergeSelectionAction"));
  assert.ok(!toolbar.includes("addDropdownValidationAction"));
});

test("Phase 7.1 formula bar is compact and inspector defaults collapsed", () => {
  assert.ok(editor.includes("tws-sheets-fx"));
  assert.ok(editor.includes("tws-sheets-formula-meta"));
  assert.ok(editor.includes("const [showSheetPanel, setShowSheetPanel] = useState(false);"));
  assert.ok(css.includes("grid-template-columns: 94px 28px minmax(220px, 1fr) auto"));
});

test("Phase 7.1 preserves established spreadsheet functionality", () => {
  for (const feature of [
    "computeSheetValues",
    "buildSheetCollabPatch",
    "addChartAction",
    "addPivotAction",
    "printCurrentSheet",
    "addNamedRange",
    "handleImportXlsx",
    "undo",
    "redo",
    "mergeSelectionAction",
    "addConditionalFormattingAction",
  ]) {
    assert.ok(editor.includes(feature), `existing feature missing: ${feature}`);
  }
});

test("Phase 7.1 provides responsive compact chrome without removing Phase 7", () => {
  assert.ok(editor.includes('import "./tSheetsPhase7Premium.css";'));
  assert.ok(css.includes("@media (max-width: 1280px)"));
  assert.ok(css.includes("@media (max-width: 820px)"));
  assert.ok(css.includes("@media (prefers-reduced-motion: reduce)"));
});
