import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TDocsEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tDocsPhase1GoogleDocsFidelity.css", import.meta.url), "utf8");

function includesAll(source, values) {
  for (const value of values) assert.ok(source.includes(value), `missing: ${value}`);
}

test("Phase 1 stylesheet and root hook are wired", () => {
  assert.ok(editor.includes('import "./tDocsPhase1GoogleDocsFidelity.css";'));
  assert.ok(editor.includes("tws-docs-phase1-google-fidelity"));
  assert.ok(css.includes(".tws-docs-phase1-google-fidelity"));
});

test("dark document paper remains readable instead of inheriting light text", () => {
  includesAll(css, [
    ".dark .tws-docs-phase1-google-fidelity .tws-doc-page",
    "background: #fff !important",
    ".dark .tws-docs-phase1-google-fidelity .tws-tdoc-editor",
    "color: #202124 !important",
  ]);
});

test("dark title remains readable even when disabled", () => {
  includesAll(css, [
    ".tws-docs-chrome > input:disabled",
    "-webkit-text-fill-color: #e8eaed !important",
    "opacity: 1 !important",
  ]);
});

test("document canvas is flatter and closer to a professional page editor", () => {
  includesAll(css, [
    ".tws-doc-page",
    "border-radius: 3px !important",
    "box-shadow: 0 2px 8px rgba(60,64,67,.14)",
    ".tws-docs-page-shell",
  ]);
});

test("compact toolbar is coherent in both themes", () => {
  includesAll(css, [
    ".tws-docs-toolbar",
    "flex-wrap: nowrap !important",
    "overflow-x: auto",
    ".dark .tws-docs-phase1-google-fidelity .tws-docs-toolbar",
    "background: #202124 !important",
  ]);
});

test("familiar ruler strip is present without changing page setup behavior", () => {
  assert.ok(editor.includes('className="tws-doc-ruler"'));
  includesAll(css, [
    ".tws-doc-ruler",
    "repeating-linear-gradient",
    "border-top: 7px solid var(--td1-blue)",
  ]);
});

test("outline and document-info inspector have dedicated fidelity hooks", () => {
  includesAll(editor, [
    "tws-docs-inspector",
    "tws-docs-outline-card",
    "tws-docs-info-card",
  ]);
  includesAll(css, [
    ".tws-docs-inspector",
    ".tws-docs-outline-card",
    ".tws-docs-info-card",
  ]);
});

test("existing document editing and collaboration features remain wired", () => {
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

test("page setup and zoom behavior remain intact", () => {
  includesAll(editor, [
    "DOC_PAGE_SIZES",
    "DOC_PAGE_MARGINS",
    "updatePageSetup",
    "setZoom",
    "transform: `scale(${zoom / 100})`",
  ]);
});

test("Phase 1 is visual-only, responsive, and reduced-motion safe", () => {
  includesAll(css, [
    "@media (max-width: 1100px)",
    "@media (max-width: 720px)",
    "@media (prefers-reduced-motion: reduce)",
  ]);
  for (const forbidden of ["fetch(", "axios", "api.", "localStorage", "sessionStorage"]) {
    assert.ok(!css.includes(forbidden), `visual CSS must not contain ${forbidden}`);
  }
});
