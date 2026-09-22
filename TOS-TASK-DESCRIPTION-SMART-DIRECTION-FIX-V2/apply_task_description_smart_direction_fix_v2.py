#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
REL = Path("frontend/src/features/tasks/taskShared.jsx")
TARGET = ROOT / REL
V1 = "TOS_TASK_DESCRIPTION_MIXED_DIRECTION_FIX_V1"
V2 = "TOS_TASK_DESCRIPTION_SMART_DIRECTION_FIX_V2"

def fail(message, original=None):
    if original is not None:
        TARGET.write_text(original, encoding="utf-8")
    print("PATCH=FAIL")
    print(f"ERROR={message}")
    raise SystemExit(1)

if not (ROOT / ".git").is_dir():
    fail(f"TOS git repository not found: {ROOT}")
if not TARGET.is_file():
    fail(f"Missing target: {REL}")

original = TARGET.read_text(encoding="utf-8")

if V2 in original:
    required = [
        "function getRichTextDominantDirection(node)",
        'return arabicCount > latinCount ? "rtl" : "ltr"',
        'node.style.unicodeBidi = "isolate"',
        'root.style.unicodeBidi = "isolate"',
        'data-tos-auto-direction',
    ]
    if any(item not in original for item in required):
        fail("V2 marker exists but implementation is incomplete")
    print("PATCH=PASS")
    print("ACTION=ALREADY_APPLIED")
    print("DIRECTION_ENGINE=DOMINANT_SCRIPT_PER_BLOCK")
    print("ARABIC_MAJORITY=RTL")
    print("LATIN_MAJORITY=LTR")
    print("FIRST_ENGLISH_WORD_NO_LONGER_FORCES_LTR=YES")
    print("FILES_CHANGED=0")
    raise SystemExit(0)

if V1 not in original:
    fail("V1 mixed-direction fix is not present; apply V1 first")

old = '''function applyRichTextAutoDirection(root) {
  if (!root || typeof document === "undefined") return false;
  let changed = false;
  const blockSelector = "p,li,blockquote,h1,h2,h3,h4,h5,h6,pre,figcaption,.tos-design-request-value";

  const hasManualAlignment = (node) => {
    const style = String(node?.getAttribute?.("style") || "").toLowerCase();
    const className = typeof node?.className === "string" ? node.className : "";
    return /(?:^|;)\\s*text-align\\s*:/.test(style)
      || /(?:^|\\s)text-(?:left|right|center|justify)(?:\\s|$)/.test(className);
  };

  const isProtected = (node) => Boolean(
    node?.closest?.(".tos-smart-link-chip,[data-link-preview='true'],[contenteditable='false']")
  );

  const applyNode = (node) => {
    if (!(node instanceof HTMLElement) || isProtected(node)) return;
    const explicit = String(node.getAttribute("dir") || "").toLowerCase();
    const manual = node.dataset.tosManualDirection === "true" || explicit === "rtl" || explicit === "ltr";
    if (manual) return;
    if (explicit !== "auto") {
      node.setAttribute("dir", "auto");
      changed = true;
    }
    if (node.style.unicodeBidi !== "plaintext") {
      node.style.unicodeBidi = "plaintext";
      changed = true;
    }
    if (!hasManualAlignment(node) && node.style.textAlign !== "start") {
      node.style.textAlign = "start";
      changed = true;
    }
  };

  const rootDir = String(root.getAttribute?.("dir") || "").toLowerCase();
  const rootManual = root.dataset?.tosManualDirection === "true" || rootDir === "rtl" || rootDir === "ltr";
  if (!rootManual && rootDir !== "auto") {
    root.setAttribute("dir", "auto");
    changed = true;
  }
  if (root.style && root.style.unicodeBidi !== "plaintext") {
    root.style.unicodeBidi = "plaintext";
    changed = true;
  }
  if (root.style && !hasManualAlignment(root) && root.style.textAlign !== "start") {
    root.style.textAlign = "start";
    changed = true;
  }

  root.querySelectorAll?.(blockSelector).forEach(applyNode);
  return changed;
}'''

new = '''// TOS_TASK_DESCRIPTION_SMART_DIRECTION_FIX_V2
function getRichTextDominantDirection(node) {
  const rawText = String(node?.innerText || node?.textContent || "");
  const text = rawText
    .replace(/https?:\\/\\/\\S+|www\\.\\S+/gi, " ")
    .replace(/[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}/g, " ");
  const arabicCount = (text.match(/[\\u0600-\\u06FF]/g) || []).length;
  const latinCount = (text.match(/[A-Za-z]/g) || []).length;

  if (!arabicCount && !latinCount) return "";
  if (arabicCount === latinCount) {
    const firstStrong = text.match(/[\\u0600-\\u06FFA-Za-z]/)?.[0] || "";
    return /[\\u0600-\\u06FF]/.test(firstStrong) ? "rtl" : "ltr";
  }
  return arabicCount > latinCount ? "rtl" : "ltr";
}

function applyRichTextAutoDirection(root) {
  if (!root || typeof document === "undefined") return false;
  let changed = false;
  const blockSelector = "p,li,blockquote,h1,h2,h3,h4,h5,h6,pre,figcaption,.tos-design-request-value";

  const hasManualAlignment = (node) => {
    const style = String(node?.getAttribute?.("style") || "").toLowerCase();
    const className = typeof node?.className === "string" ? node.className : "";
    return /(?:^|;)\\s*text-align\\s*:/.test(style.replace(/text-align\\s*:\\s*start\\s*;?/gi, ""))
      || /(?:^|\\s)text-(?:left|right|center|justify)(?:\\s|$)/.test(className);
  };

  const isProtected = (node) => Boolean(
    node?.closest?.(".tos-smart-link-chip,[data-link-preview='true'],[contenteditable='false']")
  );

  const applyNode = (node) => {
    if (!(node instanceof HTMLElement) || isProtected(node)) return;
    if (node.dataset.tosManualDirection === "true") return;

    const direction = getRichTextDominantDirection(node);
    if (!direction) return;

    if (node.getAttribute("dir") !== direction) {
      node.setAttribute("dir", direction);
      changed = true;
    }
    if (node.dataset.tosAutoDirection !== "true") {
      node.dataset.tosAutoDirection = "true";
      changed = true;
    }
    if (node.style.unicodeBidi !== "isolate") {
      node.style.unicodeBidi = "isolate";
      changed = true;
    }
    if (!hasManualAlignment(node) && node.style.textAlign !== "start") {
      node.style.textAlign = "start";
      changed = true;
    }
  };

  if (root.dataset?.tosManualDirection !== "true") {
    const rootDirection = getRichTextDominantDirection(root);
    if (rootDirection && root.getAttribute("dir") !== rootDirection) {
      root.setAttribute("dir", rootDirection);
      changed = true;
    }
    if (rootDirection && root.dataset?.tosAutoDirection !== "true") {
      root.dataset.tosAutoDirection = "true";
      changed = true;
    }
    if (root.style && rootDirection && root.style.unicodeBidi !== "isolate") {
      root.style.unicodeBidi = "isolate";
      changed = true;
    }
    if (root.style && !hasManualAlignment(root) && root.style.textAlign !== "start") {
      root.style.textAlign = "start";
      changed = true;
    }
  }

  root.querySelectorAll?.(blockSelector).forEach(applyNode);

  Array.from(root.children || []).forEach((node) => {
    if (
      node?.tagName === "DIV"
      && !node.matches?.(".tos-design-request-block,.tos-design-request-row,.tos-design-request-section,.tos-design-request-links,.tos-design-request-inline-links,.tos-smart-link-chip,[contenteditable='false']")
    ) {
      applyNode(node);
    }
  });

  return changed;
}'''

count = original.count(old)
if count != 1:
    fail(f"V1 helper anchor expected once, found {count}")

patched = original.replace(old, new, 1)

required_after = [
    V1,
    V2,
    "function getRichTextDominantDirection(node)",
    'return arabicCount > latinCount ? "rtl" : "ltr"',
    'node.style.unicodeBidi = "isolate"',
    'root.style.unicodeBidi = "isolate"',
    'node.dataset.tosManualDirection === "true"',
]
missing = [item for item in required_after if item not in patched]
if missing:
    fail(f"Post-patch validation failed: {missing}")

TARGET.write_text(patched, encoding="utf-8")

try:
    subprocess.run(["git", "-C", str(ROOT), "diff", "--check", "--", str(REL)], check=True)
except Exception:
    fail("git diff --check failed; source restored", original)

print("PATCH=PASS")
print("ACTION=APPLIED")
print("ROOT_CAUSE=DIR_AUTO_USES_FIRST_STRONG_CHARACTER")
print("DIRECTION_ENGINE=DOMINANT_SCRIPT_PER_BLOCK")
print("ARABIC_MAJORITY=RTL")
print("LATIN_MAJORITY=LTR")
print("URL_EMAIL_NOISE=IGNORED")
print("UNICODE_BIDI=ISOLATE")
print("MANUAL_RTL_LTR=PRESERVED")
print("FIRST_ENGLISH_WORD_NO_LONGER_FORCES_LTR=YES")
print("TEXT_CONTENT=UNCHANGED")
print(f"FILES_CHANGED={REL}")
print("BUILD=NOT_RUN")
print("DEPLOY=NOT_RUN")
