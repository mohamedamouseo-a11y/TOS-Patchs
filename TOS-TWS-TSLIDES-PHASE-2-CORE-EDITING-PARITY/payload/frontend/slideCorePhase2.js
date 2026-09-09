export const SLIDE_CANVAS_W = 960;
export const SLIDE_CANVAS_H = 540;

export function clamp(value, min, max) {
  return Math.min(Math.max(Number(value) || 0, min), max);
}

export function normalizeRotation(value) {
  const n = Number(value) || 0;
  return ((n % 360) + 360) % 360;
}

export function createShapeElement(kind = "rect", overrides = {}) {
  const now = Date.now();
  return {
    id: overrides.id || `el_shape_${now}`,
    type: "shape",
    shapeKind: ["rect", "ellipse", "roundRect"].includes(kind) ? kind : "rect",
    x: 300,
    y: 180,
    w: 260,
    h: 150,
    fill: "#f1f3f4",
    stroke: "#5f6368",
    strokeWidth: 2,
    opacity: 1,
    rotation: 0,
    ...overrides,
  };
}

export function createLineElement(kind = "line", overrides = {}) {
  const now = Date.now();
  return {
    id: overrides.id || `el_line_${now}`,
    type: "line",
    lineKind: kind === "arrow" ? "arrow" : "line",
    x: 300,
    y: 240,
    w: 300,
    h: 30,
    stroke: "#3c4043",
    strokeWidth: 3,
    opacity: 1,
    rotation: 0,
    ...overrides,
  };
}

export function selectionIdsForElement(elements, elementId) {
  const element = (elements || []).find((item) => item.id === elementId);
  if (!element) return [];
  if (!element.groupId) return [element.id];
  return (elements || []).filter((item) => item.groupId === element.groupId).map((item) => item.id);
}

export function duplicateElements(elements, selectedIds, options = {}) {
  const selected = new Set(selectedIds || []);
  const offset = Number(options.offset ?? 18);
  const now = Number(options.now ?? Date.now());
  const clones = (elements || [])
    .filter((item) => selected.has(item.id))
    .map((item, index) => ({
      ...item,
      id: `el_copy_${now}_${index}`,
      x: clamp((Number(item.x) || 0) + offset, 0, SLIDE_CANVAS_W - 20),
      y: clamp((Number(item.y) || 0) + offset, 0, SLIDE_CANVAS_H - 20),
      groupId: item.groupId ? `group_copy_${now}` : undefined,
    }));
  return { elements: [...(elements || []), ...clones], cloneIds: clones.map((item) => item.id) };
}

export function alignElements(elements, selectedIds, mode, canvasW = SLIDE_CANVAS_W, canvasH = SLIDE_CANVAS_H) {
  const ids = new Set(selectedIds || []);
  return (elements || []).map((item) => {
    if (!ids.has(item.id)) return item;
    if (mode === "left") return { ...item, x: 0 };
    if (mode === "center") return { ...item, x: Math.round((canvasW - item.w) / 2) };
    if (mode === "right") return { ...item, x: Math.max(0, canvasW - item.w) };
    if (mode === "top") return { ...item, y: 0 };
    if (mode === "middle") return { ...item, y: Math.round((canvasH - item.h) / 2) };
    if (mode === "bottom") return { ...item, y: Math.max(0, canvasH - item.h) };
    return item;
  });
}

export function distributeElements(elements, selectedIds, axis = "horizontal") {
  const ids = new Set(selectedIds || []);
  const selected = (elements || []).filter((item) => ids.has(item.id));
  if (selected.length < 3) return elements || [];
  const ordered = [...selected].sort((a, b) => axis === "vertical" ? a.y - b.y : a.x - b.x);
  const first = ordered[0];
  const last = ordered[ordered.length - 1];
  const start = axis === "vertical" ? first.y : first.x;
  const end = axis === "vertical" ? last.y : last.x;
  const step = (end - start) / (ordered.length - 1);
  const positions = new Map(ordered.map((item, index) => [item.id, start + step * index]));
  return (elements || []).map((item) => {
    if (!positions.has(item.id)) return item;
    return axis === "vertical" ? { ...item, y: Math.round(positions.get(item.id)) } : { ...item, x: Math.round(positions.get(item.id)) };
  });
}

export function groupElements(elements, selectedIds, groupId = `group_${Date.now()}`) {
  const ids = new Set(selectedIds || []);
  if (ids.size < 2) return elements || [];
  return (elements || []).map((item) => ids.has(item.id) ? { ...item, groupId } : item);
}

export function ungroupElements(elements, selectedIds) {
  const ids = new Set(selectedIds || []);
  const groupIds = new Set((elements || []).filter((item) => ids.has(item.id) && item.groupId).map((item) => item.groupId));
  if (!groupIds.size) return elements || [];
  return (elements || []).map((item) => groupIds.has(item.groupId) ? { ...item, groupId: undefined } : item);
}

export function resizeElement(element, handle, dx, dy, minW = 24, minH = 18) {
  const next = { ...element };
  const startX = Number(element.x) || 0;
  const startY = Number(element.y) || 0;
  const startW = Number(element.w) || minW;
  const startH = Number(element.h) || minH;
  let x = startX;
  let y = startY;
  let w = startW;
  let h = startH;

  if (handle.includes("e")) w = Math.max(minW, startW + dx);
  if (handle.includes("s")) h = Math.max(minH, startH + dy);
  if (handle.includes("w")) {
    w = Math.max(minW, startW - dx);
    x = startX + (startW - w);
  }
  if (handle.includes("n")) {
    h = Math.max(minH, startH - dy);
    y = startY + (startH - h);
  }

  next.x = clamp(x, 0, SLIDE_CANVAS_W - minW);
  next.y = clamp(y, 0, SLIDE_CANVAS_H - minH);
  next.w = Math.min(w, SLIDE_CANVAS_W - next.x);
  next.h = Math.min(h, SLIDE_CANVAS_H - next.y);
  return next;
}
