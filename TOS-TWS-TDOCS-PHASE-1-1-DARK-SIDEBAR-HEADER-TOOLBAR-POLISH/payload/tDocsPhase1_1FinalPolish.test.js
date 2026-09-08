import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TDocsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tDocsPhase1_1FinalPolish.css", import.meta.url), "utf8");

function includesAll(source, values) {
  for (const value of values) assert.ok(source.includes(value), `missing: ${value}`);
}

test("Phase 1.1 stylesheet and root hook are wired after Phase 1", () => {
  assert.ok(editor.includes('import "./tDocsPhase1GoogleDocsFidelity.css";'));
  assert.ok(editor.includes('import "./tDocsPhase1_1FinalPolish.css";'));
  assert.ok(editor.includes("tws-docs-phase1-google-fidelity"));
  assert.ok(editor.includes("tws-docs-phase1-1-final-polish"));
});

test("dark outline rows are transparent instead of white pills", () => {
  includesAll(css, [
    ".dark .tws-docs-phase1-1-final-polish .tws-docs-outline-card button",
    "background: transparent !important",
    "border: 0 !important",
    "color: #bdc1c6 !important",
    "background: #303134 !important",
  ]);
});

test("dark header actions use quiet charcoal chrome and subtle delete state", () => {
  includesAll(css, [
    ".dark .tws-docs-phase1-1-final-polish .tws-docs-header-actions button",
    "background: #28292c !important",
    "border-color: #3c4043 !important",
    ".tws-docs-header-actions button:last-child",
    "color: #f28b82 !important",
  ]);
});

test("toolbar controls are compact and coherent", () => {
  includesAll(css, [
    ".tws-docs-toolbar button.grid",
    "width: 30px !important",
    "height: 30px !important",
    ".tws-docs-toolbar select",
    "height: 30px !important",
    "border-radius: 5px !important",
  ]);
});

test("ruler is refined without changing page setup behavior", () => {
  includesAll(css, [
    ".tws-doc-ruler",
    "height: 20px !important",
    "repeating-linear-gradient",
    "#28292c !important",
  ]);
  includesAll(editor, [
    "DOC_PAGE_SIZES",
    "DOC_PAGE_MARGINS",
    "updatePageSetup",
    "transform: `scale(${zoom / 100})`",
  ]);
});

test("Phase 1 paper readability contract remains the underlying layer", () => {
  assert.ok(editor.includes('import "./tDocsPhase1GoogleDocsFidelity.css";'));
  assert.ok(css.includes("Phase 1 paper contract remains deliberately untouched"));
});

test("existing document features remain wired", () => {
  includesAll(editor, [
    "performSave",
    "saveVersionNow",
    "insertLink",
    "insertImage",
    "insertTable",
    "insertMention",
    "CommentsPanel",
    "PermissionsModal",
    "ShareLinkModal",
    "VersionHistoryModal",
    'format="docx"',
    'format="pdf"',
  ]);
});

test("Phase 1.1 is visual-only, responsive, and reduced-motion safe", () => {
  includesAll(css, [
    "@media (max-width: 1180px)",
    "@media (max-width: 760px)",
    "@media (prefers-reduced-motion: reduce)",
  ]);
  for (const forbidden of ["fetch(", "axios", "api.", "localStorage", "sessionStorage"]) {
    assert.ok(!css.includes(forbidden), `visual CSS must not contain ${forbidden}`);
  }
});
