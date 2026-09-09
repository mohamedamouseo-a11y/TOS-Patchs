const SAFE_COLOR_PATTERN = /^(#[0-9a-f]{3,8}|rgba?\([^()<>]{1,60}\)|[a-z]{3,20})$/i;

function stripTags(value = "") {
  return String(value || "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function clampNumber(value, min, max, fallback) {
  const num = Number(value);
  if (!Number.isFinite(num)) return fallback;
  return Math.min(Math.max(num, min), max);
}

function safeColor(value, fallback) {
  return typeof value === "string" && SAFE_COLOR_PATTERN.test(value) ? value : fallback;
}

function safeImageSrc(value = "") {
  const src = String(value || "").trim();
  if (!src || src.length > 2000 || /javascript:|<|>/i.test(src)) return false;
  if (/^\/api\/files\/[a-z0-9_-]+\/(?:preview|download)(?:[?#].*)?$/i.test(src)) return true;
  try {
    const parsed = new URL(src, "https://tamiyouz.local");
    return ["http:", "https:"].includes(parsed.protocol);
  } catch {
    return false;
  }
}

export function normalizeSlideRotation(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return ((num % 360) + 360) % 360;
}

export function sanitizeSlideElementPhase2(element, slideIndex = 0, elementIndex = 0) {
  const type = ["text", "image", "shape", "line"].includes(element?.type) ? element.type : "text";
  const base = {
    id: String(element?.id || `el_${slideIndex}_${elementIndex}`).slice(0, 60),
    type,
    x: clampNumber(element?.x, -2000, 4000, 40),
    y: clampNumber(element?.y, -2000, 4000, 40),
    w: clampNumber(element?.w, 10, 4000, 200),
    h: clampNumber(element?.h, 10, 4000, 60),
    rotation: normalizeSlideRotation(element?.rotation),
    opacity: clampNumber(element?.opacity, 0.05, 1, 1),
  };
  if (element?.groupId) base.groupId = String(element.groupId).slice(0, 80);

  if (type === "text") {
    return {
      ...base,
      text: stripTags(element?.text || "").slice(0, 2000),
      fontSize: clampNumber(element?.fontSize, 6, 200, 18),
      color: safeColor(element?.color, "#111111"),
      align: ["left", "center", "right"].includes(element?.align) ? element.align : "left",
      bold: Boolean(element?.bold),
    };
  }

  if (type === "image") {
    return {
      ...base,
      src: safeImageSrc(element?.src) ? String(element.src).trim() : "",
    };
  }

  if (type === "shape") {
    return {
      ...base,
      shapeKind: ["rect", "ellipse", "roundRect"].includes(element?.shapeKind) ? element.shapeKind : "rect",
      fill: safeColor(element?.fill, "#f1f3f4"),
      stroke: safeColor(element?.stroke, "#5f6368"),
      strokeWidth: clampNumber(element?.strokeWidth, 0, 20, 2),
    };
  }

  return {
    ...base,
    lineKind: element?.lineKind === "arrow" ? "arrow" : "line",
    stroke: safeColor(element?.stroke, "#3c4043"),
    strokeWidth: clampNumber(element?.strokeWidth, 1, 20, 3),
  };
}
