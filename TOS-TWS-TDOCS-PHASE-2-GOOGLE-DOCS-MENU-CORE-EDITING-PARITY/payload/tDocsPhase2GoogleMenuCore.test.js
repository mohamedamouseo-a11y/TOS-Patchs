import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const menu = fs.readFileSync(new URL("./TDocsGoogleMenuBar.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tDocsPhase2GoogleMenuCore.css", import.meta.url), "utf8");

test("Google Docs top menu order is complete", () => {
  const expected = ["File", "Edit", "View", "Insert", "Format", "Tools", "Extensions", "Help"];
  let cursor = -1;
  for (const label of expected) {
    const next = menu.indexOf(`\"${label}\"`, cursor + 1);
    assert.ok(next > cursor, `${label} must appear after previous top menu`);
    cursor = next;
  }
});

test("menu includes real core editing groups", () => {
  for (const token of [
    "Find and replace",
    "Line & paragraph spacing",
    "Bullets & numbering",
    "Header",
    "Footer",
    "Page break",
    "Image options",
    "Insert row below",
    "Insert column right",
    "Delete row",
    "Delete column",
  ]) assert.ok(menu.includes(token), `missing ${token}`);
});

test("context-sensitive table and image commands are guarded", () => {
  assert.ok(menu.includes("enabled: canEdit && onImage"));
  assert.ok(menu.includes("enabled: canEdit && inTable"));
});

test("menu interaction parity is present", () => {
  assert.ok(menu.includes('event.key === "Escape"'));
  assert.ok(menu.includes("event.altKey"));
  assert.ok(menu.includes("cycleMenu(1)"));
  assert.ok(menu.includes("cycleMenu(-1)"));
  assert.ok(menu.includes("onPointerEnter"));
  assert.ok(menu.includes("is-submenu"));
});

test("light dark and core editing visual hooks exist", () => {
  for (const token of [
    ".tws-docs-google-menu-bar",
    ".dark .tws-docs-google-menu-panel",
    ".tws-docs-find-replace",
    ".tws-doc-page-break",
    ".tws-doc-header",
    ".tws-doc-footer",
    ".tws-doc-image-selected",
  ]) assert.ok(css.includes(token), `missing CSS token ${token}`);
});
