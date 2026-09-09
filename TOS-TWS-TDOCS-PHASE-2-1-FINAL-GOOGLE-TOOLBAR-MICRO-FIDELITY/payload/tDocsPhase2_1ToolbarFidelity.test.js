import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const toolbar = fs.readFileSync(new URL("./TDocsGoogleToolbar.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tDocsPhase2_1ToolbarFidelity.css", import.meta.url), "utf8");
const editor = fs.readFileSync(new URL("./TDocsEditor.jsx", import.meta.url), "utf8");

test("phase 2.1 toolbar exposes Google Docs primary control flow", () => {
  for (const token of [
    "Printer", "Undo", "Redo", "ZOOM_LEVELS", "Normal text", "FONT_FAMILIES",
    "Bold", "Italic", "Underline", "Insert link", "Align left", "Bulleted list", "Insert image", "Insert table",
  ]) assert.ok(toolbar.includes(token), `missing ${token}`);
});

test("secondary page setup and outline/version actions stay out of the primary toolbar", () => {
  assert.equal(toolbar.includes("Page size"), false);
  assert.equal(toolbar.includes("Margins"), false);
  assert.equal(toolbar.includes("Save named version"), false);
  assert.equal(toolbar.includes("document outline"), false);
});

test("toolbar is single-row scrollable and has light/dark fidelity", () => {
  for (const token of [
    ".tws-docs-gtoolbar-shell",
    ".tws-docs-gtoolbar-track",
    "overflow-x: auto",
    "border-radius: 20px",
    "background: #edf2fa",
    ".dark .tws-docs-gtoolbar-track",
    ".dark .tws-docs-gtoolbar-icon",
  ]) assert.ok(css.includes(token), `missing CSS token ${token}`);
});

test("editor uses phase 2.1 toolbar and preserves phase 2 menu", () => {
  assert.ok(editor.includes('import { TDocsGoogleToolbar } from "./TDocsGoogleToolbar";'));
  assert.ok(editor.includes('import "./tDocsPhase2_1ToolbarFidelity.css";'));
  assert.ok(editor.includes("tws-docs-phase2-1-toolbar-fidelity"));
  assert.ok(editor.includes("<TDocsGoogleToolbar"));
  assert.ok(editor.includes("<TDocsGoogleMenuBar"));
  assert.ok(editor.includes('paragraphStyle: (value) => exec("formatBlock", value)'));
  assert.ok(editor.includes('fontFamily: (value) => exec("fontName", value)'));
  assert.ok(editor.includes("print: printDocument"));
});
