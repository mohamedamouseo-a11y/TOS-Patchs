import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import {
  alignElements, createLineElement, createShapeElement, distributeElements, duplicateElements,
  groupElements, normalizeRotation, resizeElement, selectionIdsForElement, ungroupElements,
} from "./slideCorePhase2.js";

const editor = fs.readFileSync(new URL("./TSlidesEditor.jsx", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("./tSlidesPhase2CoreEditing.css", import.meta.url), "utf8");

test("shape and line factories create persisted slide elements", () => {
  const shape = createShapeElement("ellipse", { id: "s1" });
  const line = createLineElement("arrow", { id: "l1" });
  assert.equal(shape.type, "shape");
  assert.equal(shape.shapeKind, "ellipse");
  assert.equal(line.type, "line");
  assert.equal(line.lineKind, "arrow");
  assert.equal(shape.rotation, 0);
});

test("group selection expands to all grouped members", () => {
  const elements = [{ id: "a", groupId: "g1" }, { id: "b", groupId: "g1" }, { id: "c" }];
  assert.deepEqual(selectionIdsForElement(elements, "a"), ["a", "b"]);
  assert.deepEqual(selectionIdsForElement(elements, "c"), ["c"]);
});

test("duplicate preserves style and offsets clones", () => {
  const result = duplicateElements([{ id: "a", x: 10, y: 20, w: 100, h: 50, fill: "#fff" }], ["a"], { now: 7, offset: 18 });
  assert.equal(result.cloneIds.length, 1);
  assert.equal(result.elements[1].x, 28);
  assert.equal(result.elements[1].fill, "#fff");
});

test("align and distribute support slide design workflows", () => {
  const base = [{ id: "a", x: 10, y: 10, w: 50, h: 20 }, { id: "b", x: 100, y: 60, w: 50, h: 20 }, { id: "c", x: 300, y: 150, w: 50, h: 20 }];
  assert.equal(alignElements(base, ["a"], "center")[0].x, 455);
  const distributed = distributeElements(base, ["a", "b", "c"], "horizontal");
  assert.equal(distributed[1].x, 155);
});

test("group and ungroup are reversible", () => {
  const base = [{ id: "a" }, { id: "b" }, { id: "c" }];
  const grouped = groupElements(base, ["a", "b"], "g");
  assert.equal(grouped[0].groupId, "g");
  assert.equal(grouped[1].groupId, "g");
  const ungrouped = ungroupElements(grouped, ["a"]);
  assert.equal(ungrouped[0].groupId, undefined);
  assert.equal(ungrouped[1].groupId, undefined);
});

test("four-corner resize changes position and size safely", () => {
  const next = resizeElement({ x: 100, y: 100, w: 200, h: 100 }, "nw", 20, 10);
  assert.equal(next.x, 120);
  assert.equal(next.y, 110);
  assert.equal(next.w, 180);
  assert.equal(next.h, 90);
  assert.equal(normalizeRotation(-30), 330);
});

test("editor wires Phase 2 shapes lines rotation clipboard grouping and distribution", () => {
  for (const marker of [
    'import "./tSlidesPhase2CoreEditing.css";',
    "createShapeElement",
    "createLineElement",
    "duplicateSelectedElements",
    "copySelectedElements",
    "pasteSelectedElements",
    "groupSelectedElements",
    "ungroupSelectedElements",
    "distributeSelectedElements",
    "rotateSelectedElements",
    "updateSelectedElementStyle",
    "tws-slides-phase2-core",
  ]) assert.ok(editor.includes(marker), `missing editor marker: ${marker}`);
});

test("canvas renders shape line and rotation affordances", () => {
  for (const marker of [
    'element.type === "shape"',
    'element.type === "line"',
    "tws-slides-resize-handle",
    "tws-slides-rotate-handle",
    "markerEnd",
    "rotation",
  ]) assert.ok(editor.includes(marker), `missing canvas marker: ${marker}`);
});

test("keyboard parity includes copy paste duplicate group and ungroup", () => {
  for (const marker of [
    'key === "c"',
    'key === "v"',
    'key === "d"',
    'key === "g"',
    "event.shiftKey",
  ]) assert.ok(editor.includes(marker), `missing shortcut marker: ${marker}`);
});

test("Phase 1 and established presentation workflows remain wired", () => {
  for (const marker of [
    'import "./tSlidesPhase1GoogleSlidesFidelity.css";',
    "addSlide",
    "duplicateSlide",
    "reorderSlides",
    "addTextElement",
    "addImageElement",
    "applyLayoutToCurrentSlide",
    "updateSpeakerNotes",
    "PresentMode",
    "CommentsPanel",
    'format="pptx"',
    'format="pdf"',
  ]) assert.ok(editor.includes(marker), `missing regression marker: ${marker}`);
});

test("Phase 2 CSS provides interaction fidelity in light and dark modes", () => {
  for (const marker of [
    ".tws-slides-phase2-core",
    ".tws-slides-resize-handle",
    ".tws-slides-rotate-handle",
    ".tws-slides-shape",
    ".tws-slides-line",
    ".dark .tws-slides-phase2-core",
    "@media (max-width: 1180px)",
    "@media (prefers-reduced-motion: reduce)",
  ]) assert.ok(css.includes(marker), `missing css marker: ${marker}`);
});
