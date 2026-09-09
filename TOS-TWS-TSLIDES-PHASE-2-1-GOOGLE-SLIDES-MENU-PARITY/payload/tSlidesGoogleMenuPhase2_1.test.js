import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const menu = fs.readFileSync(new URL("./TSlidesGoogleMenuBar.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSlidesGoogleMenuPhase2_1.css", import.meta.url), "utf8");
const editor = fs.readFileSync(new URL("./TSlidesEditor.jsx", import.meta.url), "utf8");

const expectedMenus = ["File", "Edit", "View", "Insert", "Slide", "Format", "Arrange", "Tools", "Extensions", "Help"];

for (const label of expectedMenus) {
  test(`top menu ${label} exists`, () => {
    assert.match(menu, new RegExp(`\\[\\\"[^\\\"]+\\\", \\\"${label}\\\"\\]`));
  });
}

test("single-open menu state and hover switching exist", () => {
  assert.match(menu, /const \[openMenu, setOpenMenu\] = useState\(""\)/);
  assert.match(menu, /setOpenMenu\(\(current\) => current === menuId \? "" : menuId\)/);
  assert.match(menu, /onPointerEnter=.*openMenu/);
});

test("outside click escape and alt shortcuts exist", () => {
  assert.match(menu, /window\.addEventListener\("pointerdown"/);
  assert.match(menu, /event\.key === "Escape"/);
  assert.match(menu, /ALT_MENU_KEYS/);
  assert.match(menu, /event\.altKey/);
});

test("submenu behavior exists", () => {
  assert.match(menu, /openSubmenu/);
  assert.match(menu, /className="tws-slides-google-menu-panel is-submenu"/);
  assert.match(menu, /hasSubmenu/);
});

test("core existing actions are wired into menus", () => {
  for (const marker of [
    "actions.undo", "actions.redo", "actions.copy", "actions.paste", "actions.duplicate",
    "actions.addText", "actions.addImage", "actions.addRectangle", "actions.addEllipse", "actions.addLine", "actions.addArrow",
    "actions.duplicateSlide", "actions.deleteSlide", "actions.alignLeft", "actions.alignCenter", "actions.group", "actions.ungroup",
    "actions.downloadPptx", "actions.downloadPdf", "actions.present", "actions.versionHistory",
  ]) assert.ok(menu.includes(marker), marker);
});

test("disabled states depend on edit and selection context", () => {
  assert.match(menu, /enabled: canEdit && hasSelection/);
  assert.match(menu, /enabled: canEdit && hasMultiSelection/);
  assert.match(menu, /enabled: canEdit && hasThreeSelection/);
  assert.match(menu, /enabled: canEdit && slideCount > 1/);
});

test("editor imports and renders Google menu bar", () => {
  assert.match(editor, /TSlidesGoogleMenuBar/);
  assert.match(editor, /tSlidesGoogleMenuPhase2_1\.css/);
  assert.match(editor, /<TSlidesGoogleMenuBar/);
  assert.match(editor, /data-tws-slides-title/);
  assert.match(editor, /data-tws-slides-notes/);
});

test("menu actions use real existing editor functionality", () => {
  for (const marker of [
    "downloadSlides", "cutSelectedElements", "selectAllElements", "focusSlidesTitle", "focusSpeakerNotes",
    "addShapeElement", "addLineElement", "applyLayoutToCurrentSlide", "applySlideTheme", "alignSelectedElements",
    "distributeSelectedElements", "groupSelectedElements", "ungroupSelectedElements", "rotateSelectedElements",
  ]) assert.ok(editor.includes(marker), marker);
});

test("menu visual fidelity includes Google-like chrome and dark mode", () => {
  assert.match(css, /#202124/);
  assert.match(css, /#f1f3f4/);
  assert.match(css, /#e8f0fe/);
  assert.match(css, /#dadce0/);
  assert.match(css, /\.dark \.tws-slides-google-menu-bar/);
  assert.match(css, /min-width: 270px/);
});
