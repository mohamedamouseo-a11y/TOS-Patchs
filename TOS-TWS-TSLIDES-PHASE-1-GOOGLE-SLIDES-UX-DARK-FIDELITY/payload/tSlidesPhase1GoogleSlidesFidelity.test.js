import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const editor = fs.readFileSync(new URL("./TSlidesEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSlidesPhase1GoogleSlidesFidelity.css", import.meta.url), "utf8");

function includesAll(source, values) {
  for (const value of values) assert.ok(source.includes(value), `missing: ${value}`);
}

test("Phase 1 stylesheet and root hook are wired", () => {
  assert.ok(editor.includes('import "./tSlidesPhase1GoogleSlidesFidelity.css";'));
  assert.ok(editor.includes("tws-slides-phase1-google-fidelity"));
  assert.ok(css.includes(".tws-slides-phase1-google-fidelity"));
});

test("document chrome and header actions have dedicated fidelity hooks", () => {
  includesAll(editor, ["tws-slides-chrome", "tws-slides-header-actions"]);
  includesAll(css, [".tws-slides-chrome", ".tws-slides-header-actions"]);
});

test("compact presentation toolbar is coherent in both themes", () => {
  includesAll(editor, ["tws-slides-toolbar"]);
  includesAll(css, [
    ".tws-slides-toolbar",
    "flex-wrap: nowrap !important",
    "overflow-x: auto",
    ".dark .tws-slides-phase1-google-fidelity .tws-slides-toolbar",
    "background: #202124 !important",
  ]);
});

test("slide rail and active thumbnail use a blue presentation selection language", () => {
  includesAll(editor, ["tws-slides-rail", "tws-slides-thumb", "tws-slides-thumb-active"]);
  includesAll(css, [
    ".tws-slides-thumb-active",
    "border-color: var(--tsl1-blue) !important",
    "border-color: var(--tsl1-blue-dark) !important",
  ]);
});

test("editing stage and canvas are flattened and dark-shell safe", () => {
  includesAll(editor, ["tws-slides-stage", "tws-slides-canvas"]);
  includesAll(css, [
    ".tws-slides-stage",
    ".tws-slides-canvas",
    "border-radius: 3px !important",
    ".dark .tws-slides-phase1-google-fidelity .tws-slides-stage",
  ]);
});

test("amber element selection accents are visually normalized to blue", () => {
  includesAll(css, [
    ".tws-slides-canvas .ring-amber-400",
    ".tws-slides-canvas .bg-amber-400",
    ".tws-slides-canvas .bg-amber-500",
    "--tw-ring-color: var(--tsl1-blue-dark) !important",
  ]);
});

test("speaker notes and right inspector avoid washed-out dark panels", () => {
  includesAll(editor, [
    "tws-slides-notes",
    "tws-slides-inspector",
    "tws-slides-properties-card",
    "tws-slides-layout-card",
  ]);
  includesAll(css, [
    ".dark .tws-slides-phase1-google-fidelity .tws-slides-notes",
    ".dark .tws-slides-phase1-google-fidelity .tws-slides-inspector",
    "background: #28292c !important",
    "opacity: 1 !important",
    "filter: none !important",
  ]);
});

test("existing presentation editing features remain wired", () => {
  includesAll(editor, [
    "addSlide",
    "duplicateSlide",
    "reorderSlides",
    "addTextElement",
    "addImageElement",
    "applyLayoutToCurrentSlide",
    "alignSelectedElements",
    "reorderSelectedLayer",
    "updateSpeakerNotes",
    "PresentMode",
    "CommentsPanel",
    "PermissionsModal",
    "ShareLinkModal",
    "VersionHistoryModal",
    'format="pptx"',
    'format="pdf"',
  ]);
});

test("history, autosave and keyboard interactions remain wired", () => {
  includesAll(editor, [
    "performSave",
    "scheduleSave",
    "pushHistory",
    "undo",
    "redo",
    "handleStageKeyDown",
    "computeSnap",
  ]);
});

test("Phase 1 is visual-only, responsive, and reduced-motion safe", () => {
  includesAll(css, [
    "@media (max-width: 1180px)",
    "@media (max-width: 820px)",
    "@media (prefers-reduced-motion: reduce)",
  ]);
  for (const forbidden of ["fetch(", "axios", "api.", "localStorage", "sessionStorage"]) {
    assert.ok(!css.includes(forbidden), `visual CSS must not contain ${forbidden}`);
  }
});
