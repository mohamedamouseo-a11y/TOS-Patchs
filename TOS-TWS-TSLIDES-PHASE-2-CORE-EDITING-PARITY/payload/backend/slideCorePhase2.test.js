import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { normalizeSlideRotation, sanitizeSlideElementPhase2 } from "./slideCorePhase2.js";

const service = fs.readFileSync(new URL("../services/workspace.service.js", import.meta.url), "utf8");
const exporter = fs.readFileSync(new URL("./workspaceExport.js", import.meta.url), "utf8");

test("sanitizer preserves shape fields safely", () => {
  const shape = sanitizeSlideElementPhase2({
    id: "shape_1", type: "shape", shapeKind: "ellipse", x: 10, y: 20, w: 300, h: 160,
    fill: "#abcdef", stroke: "#112233", strokeWidth: 4, rotation: -30, opacity: .6, groupId: "g1",
  });
  assert.equal(shape.type, "shape");
  assert.equal(shape.shapeKind, "ellipse");
  assert.equal(shape.rotation, 330);
  assert.equal(shape.opacity, .6);
  assert.equal(shape.groupId, "g1");
});

test("sanitizer preserves line and arrow fields", () => {
  const line = sanitizeSlideElementPhase2({ type: "line", lineKind: "arrow", stroke: "#123456", strokeWidth: 5 });
  assert.equal(line.type, "line");
  assert.equal(line.lineKind, "arrow");
  assert.equal(line.stroke, "#123456");
  assert.equal(line.strokeWidth, 5);
});

test("unsafe values are normalized", () => {
  const shape = sanitizeSlideElementPhase2({ type: "shape", fill: "url(javascript:x)", strokeWidth: 999, opacity: -2 });
  assert.equal(shape.fill, "#f1f3f4");
  assert.equal(shape.strokeWidth, 20);
  assert.equal(shape.opacity, .05);
  assert.equal(normalizeSlideRotation(725), 5);
});

test("legacy text and image contracts remain supported", () => {
  const text = sanitizeSlideElementPhase2({ type: "text", text: "<b>Hello</b>", fontSize: 22, bold: true });
  const image = sanitizeSlideElementPhase2({ type: "image", src: "https://example.com/image.png" });
  assert.equal(text.text, "Hello");
  assert.equal(text.bold, true);
  assert.equal(image.src, "https://example.com/image.png");
});

test("workspace service wires Phase 2 sanitizer", () => {
  assert.ok(service.includes('import { sanitizeSlideElementPhase2 } from "../utils/slideCorePhase2.js";'));
  assert.ok(service.includes("sanitizeSlideElementPhase2(element, index, elIndex)"));
});

test("native exports understand shape and line elements", () => {
  for (const marker of [
    'element.type === "shape"',
    'element.type === "line"',
    "ShapeType.ellipse",
    "ShapeType.line",
    "endArrowType",
    "element.rotation",
    "element.opacity",
  ]) assert.ok(exporter.includes(marker), `missing export marker: ${marker}`);
});
