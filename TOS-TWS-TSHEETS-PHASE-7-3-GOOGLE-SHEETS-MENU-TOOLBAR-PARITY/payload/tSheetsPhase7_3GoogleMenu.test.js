import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const menu = fs.readFileSync(new URL("./TSheetsGoogleMenuBar.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSheetsPhase7_3GoogleMenu.css", import.meta.url), "utf8");
const editor = fs.readFileSync(new URL("./TSheetsEditor.jsx", import.meta.url), "utf8");

for (const label of ["File", "Edit", "View", "Insert", "Format", "Data", "Tools", "Extensions", "Help"]) {
  test(`top menu ${label} exists`, () => assert.ok(menu.includes(`\"${label}\"`), label));
}

test("single-open hover-switch menu behavior exists", () => {
  assert.match(menu, /const \[openMenu, setOpenMenu\] = useState\(""\)/);
  assert.match(menu, /setOpenMenu\(\(current\) => current === menuId \? "" : menuId\)/);
  assert.match(menu, /onPointerEnter=.*openMenu/);
});

test("outside click escape alt and submenus exist", () => {
  assert.match(menu, /window\.addEventListener\("pointerdown"/);
  assert.match(menu, /event\.key === "Escape"/);
  assert.match(menu, /ALT_MENU_KEYS/);
  assert.match(menu, /event\.altKey/);
  assert.match(menu, /openSubmenu/);
  assert.match(menu, /is-submenu/);
});

test("real sheet actions are wired", () => {
  for (const marker of [
    "actions.undo", "actions.redo", "actions.cut", "actions.copy", "actions.paste", "actions.pasteValues", "actions.pasteFormats",
    "actions.findReplace", "actions.addSheet", "actions.addRow", "actions.addCol", "actions.addChart", "actions.addPivot",
    "actions.addDropdown", "actions.addNamedRange", "actions.bold", "actions.italic", "actions.underline", "actions.wrap",
    "actions.merge", "actions.unmerge", "actions.sortAsc", "actions.sortDesc", "actions.createFilter", "actions.filterValues",
    "actions.conditionalFormatting", "actions.protect", "actions.unprotect", "actions.downloadXlsx", "actions.downloadCsv", "actions.downloadPdf",
  ]) assert.ok(menu.includes(marker), marker);
});

test("context disabled states exist", () => {
  assert.match(menu, /enabled: canEdit && hasSelection/);
  assert.match(menu, /enabled: canEdit && hasFilter/);
  assert.match(menu, /sheetCount < 20/);
});

test("editor imports and renders Google Sheets menu", () => {
  assert.match(editor, /TSheetsGoogleMenuBar/);
  assert.match(editor, /tSheetsPhase7_3GoogleMenu\.css/);
  assert.match(editor, /<TSheetsGoogleMenuBar/);
  assert.match(editor, /tws-sheets-phase7-3-google-menu/);
  assert.match(editor, /data-tws-sheets-title/);
});

test("editor exposes menu helpers and existing sheet actions", () => {
  for (const marker of [
    "cutSelectionForMenu", "selectAllSheetForMenu", "downloadSheetForMenu", "focusSheetsTitle", "toggleSheetsFullscreen",
    "showSheetsKeyboardShortcuts", "copySelectionToInternalClipboard", "pasteInternalClipboard", "pasteSpecialValuesAction",
    "pasteSpecialFormatsAction", "clearCurrentSelection", "clearFormattingAction", "findReplaceAction", "addChartAction", "addPivotAction",
    "addDropdownValidationAction", "addConditionalFormattingAction", "protectSelection", "unprotectSelection",
  ]) assert.ok(editor.includes(marker), marker);
});

test("Google-like green chrome and toolbar fidelity exist in light and dark", () => {
  for (const marker of ["#202124", "#f1f3f4", "#e6f4ea", "#137333", "#dadce0", ".dark .tws-sheets-google-menu-bar", "min-width: 280px", ".tws-sheets-toolbar-compact"]) {
    assert.ok(css.includes(marker), marker);
  }
});
