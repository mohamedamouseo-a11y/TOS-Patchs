#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
FILES = {
    "shared": ROOT / "frontend/src/features/tasks/taskShared.jsx",
    "parts": ROOT / "frontend/src/features/tasks/taskBoardParts.jsx",
}
MARKER = "TOS_TASK_DESCRIPTION_MIXED_DIRECTION_FIX_V1"

def fail(message, originals=None):
    if originals:
        for key, content in originals.items():
            FILES[key].write_text(content, encoding="utf-8")
    print("PATCH=FAIL")
    print(f"ERROR={message}")
    raise SystemExit(1)

if not (ROOT / ".git").is_dir():
    fail(f"TOS git repository not found: {ROOT}")
for key, path in FILES.items():
    if not path.is_file():
        fail(f"Missing target: {path.relative_to(ROOT)}")

originals = {key: path.read_text(encoding="utf-8") for key, path in FILES.items()}
shared = originals["shared"]
parts = originals["parts"]

if MARKER in shared and MARKER in parts:
    required = [
        "function applyRichTextAutoDirection(root)",
        'valueNode.setAttribute("dir", "auto")',
        'block.setAttribute("dir", "auto")',
        'data-tos-manual-direction',
        'style={{ unicodeBidi: "plaintext", textAlign: "start" }}',
    ]
    joined = shared + "\n" + parts
    if any(item not in joined for item in required):
        fail("Marker exists but implementation is incomplete")
    print("PATCH=PASS")
    print("ACTION=ALREADY_APPLIED")
    print("MIXED_DIRECTION=AUTO_PER_BLOCK")
    print("DESIGN_REQUEST_VALUES=AUTO_DIRECTION")
    print("MANUAL_RTL_LTR=PRESERVED")
    print("FILES_CHANGED=0")
    raise SystemExit(0)

helper_anchor = '''function localizeDesignRequestBlocks(root, ui = getTaskUiText("en")) {'''
helper_code = '''// TOS_TASK_DESCRIPTION_MIXED_DIRECTION_FIX_V1
function applyRichTextAutoDirection(root) {
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
}

function localizeDesignRequestBlocks(root, ui = getTaskUiText("en")) {'''

if shared.count(helper_anchor) != 1:
    fail(f"shared helper anchor expected once, found {shared.count(helper_anchor)}")
shared = shared.replace(helper_anchor, helper_code, 1)

old_block = '''  root.querySelectorAll(".tos-design-request-block").forEach((block) => {
    if (block.getAttribute("dir") !== direction) { block.setAttribute("dir", direction); changed = true; }
    const title = block.querySelector(".tos-design-request-title");
    if (title && title.textContent !== copy.title) { title.textContent = copy.title; changed = true; }'''
new_block = '''  root.querySelectorAll(".tos-design-request-block").forEach((block) => {
    // Mixed-language content must not inherit the UI language direction.
    if (block.getAttribute("dir") !== "auto") { block.setAttribute("dir", "auto"); changed = true; }
    if (block.style.unicodeBidi !== "plaintext") { block.style.unicodeBidi = "plaintext"; changed = true; }
    if (block.style.textAlign !== "start") { block.style.textAlign = "start"; changed = true; }
    const title = block.querySelector(".tos-design-request-title");
    if (title && title.textContent !== copy.title) { title.textContent = copy.title; changed = true; }
    if (title && title.getAttribute("dir") !== direction) { title.setAttribute("dir", direction); changed = true; }'''
if shared.count(old_block) != 1:
    fail(f"design block anchor expected once, found {shared.count(old_block)}")
shared = shared.replace(old_block, new_block, 1)

old_row = '''      const field = row.getAttribute("data-design-field") || inferred || "";
      if (field && row.getAttribute("data-design-field") !== field) { row.setAttribute("data-design-field", field); changed = true; }
      if (field && copy[field] && label.textContent !== copy[field]) { label.textContent = copy[field]; changed = true; }
      if (field === "platform" || field === "designType") {
        const value = row.querySelector(".tos-design-request-value");'''
new_row = '''      const field = row.getAttribute("data-design-field") || inferred || "";
      if (field && row.getAttribute("data-design-field") !== field) { row.setAttribute("data-design-field", field); changed = true; }
      if (field && copy[field] && label.textContent !== copy[field]) { label.textContent = copy[field]; changed = true; }
      if (label.getAttribute("dir") !== direction) { label.setAttribute("dir", direction); changed = true; }
      const valueNode = row.querySelector(".tos-design-request-value");
      if (valueNode && valueNode.dataset.tosManualDirection !== "true") {
        if (valueNode.getAttribute("dir") !== "auto") { valueNode.setAttribute("dir", "auto"); changed = true; }
        if (valueNode.style.unicodeBidi !== "plaintext") { valueNode.style.unicodeBidi = "plaintext"; changed = true; }
        if (!/(?:^|;)\\s*text-align\\s*:/i.test(String(valueNode.getAttribute("style") || "").replace(/text-align\\s*:\\s*start\\s*;?/i, "")) && valueNode.style.textAlign !== "start") {
          valueNode.style.textAlign = "start";
          changed = true;
        }
      }
      if (field === "platform" || field === "designType") {
        const value = valueNode;'''
if shared.count(old_row) != 1:
    fail(f"design row anchor expected once, found {shared.count(old_row)}")
shared = shared.replace(old_row, new_row, 1)

old_section = '''      const key = section.getAttribute("data-design-section") || inferred || "";
      if (key && section.getAttribute("data-design-section") !== key) { section.setAttribute("data-design-section", key); changed = true; }
      if (key && copy[key] && heading.textContent !== copy[key]) { heading.textContent = copy[key]; changed = true; }
      if (key === "attachments") {'''
new_section = '''      const key = section.getAttribute("data-design-section") || inferred || "";
      if (key && section.getAttribute("data-design-section") !== key) { section.setAttribute("data-design-section", key); changed = true; }
      if (key && copy[key] && heading.textContent !== copy[key]) { heading.textContent = copy[key]; changed = true; }
      if (heading.getAttribute("dir") !== direction) { heading.setAttribute("dir", direction); changed = true; }
      section.querySelectorAll("p,li,blockquote").forEach((node) => {
        if (node.dataset.tosManualDirection === "true") return;
        if (node.getAttribute("dir") !== "auto") { node.setAttribute("dir", "auto"); changed = true; }
        if (node.style.unicodeBidi !== "plaintext") { node.style.unicodeBidi = "plaintext"; changed = true; }
        if (node.style.textAlign !== "start") { node.style.textAlign = "start"; changed = true; }
      });
      if (key === "attachments") {'''
if shared.count(old_section) != 1:
    fail(f"design section anchor expected once, found {shared.count(old_section)}")
shared = shared.replace(old_section, new_section, 1)

old_localize_tail = '''    });
  });
  return changed;
}

function compactDesignRequestLinks(root) {'''
new_localize_tail = '''    });
  });
  if (applyRichTextAutoDirection(root)) changed = true;
  return changed;
}

function compactDesignRequestLinks(root) {'''
if shared.count(old_localize_tail) != 1:
    fail(f"localize tail anchor expected once, found {shared.count(old_localize_tail)}")
shared = shared.replace(old_localize_tail, new_localize_tail, 1)

old_display = '''    decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    enhanceSmartLinkTitles(root, undefined, ui);'''
new_display = '''    decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    applyRichTextAutoDirection(root);
    enhanceSmartLinkTitles(root, undefined, ui);'''
if shared.count(old_display) != 1:
    fail(f"RichTextContent anchor expected once, found {shared.count(old_display)}")
shared = shared.replace(old_display, new_display, 1)

old_export = '''  normalizeRichTextLinks,
  localizeDesignRequestBlocks,
  compactDesignRequestLinks,''';
new_export = '''  normalizeRichTextLinks,
  applyRichTextAutoDirection,
  localizeDesignRequestBlocks,
  compactDesignRequestLinks,''';
if shared.count(old_export) != 1:
    fail(f"export anchor expected once, found {shared.count(old_export)}")
shared = shared.replace(old_export, new_export, 1)

old_import = '''  normalizeRichTextLinks,
  localizeDesignRequestBlocks,
  compactDesignRequestLinks,''';
new_import = '''  normalizeRichTextLinks,
  applyRichTextAutoDirection,
  localizeDesignRequestBlocks,
  compactDesignRequestLinks,''';
if parts.count(old_import) != 1:
    fail(f"parts import anchor expected once, found {parts.count(old_import)}")
parts = parts.replace(old_import, new_import, 1)

old_normalize = '''    const localized = localizeDesignRequestBlocks(root, ui);
    const normalized = normalizeRichTextLinks(root, ui);
    const compacted = compactDesignRequestLinks(root);
    const decorated = decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    if (localized || normalized || compacted || (options.emitDecorations && decorated)) emitChange();
    return localized || normalized || compacted || decorated;'''
new_normalize = '''    const localized = localizeDesignRequestBlocks(root, ui);
    const normalized = normalizeRichTextLinks(root, ui);
    const compacted = compactDesignRequestLinks(root);
    const autoDirected = applyRichTextAutoDirection(root);
    const decorated = decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    if (localized || normalized || compacted || autoDirected || (options.emitDecorations && decorated)) emitChange();
    return localized || normalized || compacted || autoDirected || decorated;'''
if parts.count(old_normalize) != 1:
    fail(f"normalizeEditorDom anchor expected once, found {parts.count(old_normalize)}")
parts = parts.replace(old_normalize, new_normalize, 1)

old_input = '''  function handleEditorInput(event) {
    if (disabled) return;
    if (isComposingRef.current || event?.nativeEvent?.isComposing) {
      updateStats(event.currentTarget);
      return;
    }
    emitChange();
  }'''
new_input = '''  function handleEditorInput(event) {
    if (disabled) return;
    if (isComposingRef.current || event?.nativeEvent?.isComposing) {
      updateStats(event.currentTarget);
      return;
    }
    applyRichTextAutoDirection(event.currentTarget);
    emitChange();
  }'''
if parts.count(old_input) != 1:
    fail(f"input anchor expected once, found {parts.count(old_input)}")
parts = parts.replace(old_input, new_input, 1)

old_comp = '''  function handleCompositionEnd() {
    isComposingRef.current = false;
    emitChange();
    saveEditorSelection();
  }'''
new_comp = '''  function handleCompositionEnd() {
    isComposingRef.current = false;
    applyRichTextAutoDirection(editorRef.current);
    emitChange();
    saveEditorSelection();
  }'''
if parts.count(old_comp) != 1:
    fail(f"composition anchor expected once, found {parts.count(old_comp)}")
parts = parts.replace(old_comp, new_comp, 1)

old_load = '''    decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    updateStats(root);
  }, [value, designBriefFiles, ui]);'''
new_load = '''    decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    applyRichTextAutoDirection(root);
    updateStats(root);
  }, [value, designBriefFiles, ui]);'''
if parts.count(old_load) != 1:
    fail(f"load anchor expected once, found {parts.count(old_load)}")
parts = parts.replace(old_load, new_load, 1)

old_manual = '''    if (block && editorRef.current?.contains(block)) {
      block.setAttribute("dir", direction);
      block.style.textAlign = direction === "rtl" ? "right" : "left";
      emitChange();
      saveEditorSelection();
    }'''
new_manual = '''    if (block && editorRef.current?.contains(block)) {
      block.setAttribute("dir", direction);
      block.setAttribute("data-tos-manual-direction", "true");
      block.style.unicodeBidi = "isolate";
      block.style.textAlign = direction === "rtl" ? "right" : "left";
      emitChange();
      saveEditorSelection();
    }'''
if parts.count(old_manual) != 1:
    fail(f"manual direction anchor expected once, found {parts.count(old_manual)}")
parts = parts.replace(old_manual, new_manual, 1)

old_insert = '''  function insertHtml(html, options = {}) {
    if (disabled) return;
    focusEditorAndRestoreSelection();
    try { document.execCommand("insertHTML", false, html); } catch { return; }
    if (options.emit !== false) emitChange({ normalizeLinks: options.normalizeLinks !== false });
    saveEditorSelection();
  }'''
new_insert = '''  function insertHtml(html, options = {}) {
    if (disabled) return;
    focusEditorAndRestoreSelection();
    try { document.execCommand("insertHTML", false, html); } catch { return; }
    applyRichTextAutoDirection(editorRef.current);
    if (options.emit !== false) emitChange({ normalizeLinks: options.normalizeLinks !== false });
    saveEditorSelection();
  }'''
if parts.count(old_insert) != 1:
    fail(f"insertHtml anchor expected once, found {parts.count(old_insert)}")
parts = parts.replace(old_insert, new_insert, 1)

old_editor = '''        dir="auto"
        spellCheck
        onInput={handleEditorInput}'''
new_editor = '''        dir="auto"
        style={{ unicodeBidi: "plaintext", textAlign: "start" }}
        spellCheck
        onInput={handleEditorInput}'''
if parts.count(old_editor) < 1:
    fail("contentEditable dir anchor not found")
parts = parts.replace(old_editor, new_editor, 1)

# Add marker in parts near editor function for idempotence.
parts_marker_anchor = '''function PremiumTaskRichTextEditor({ value, onChange, placeholder, minHeight = "min-h-[110px]", label, disabled = false, ui = getTaskUiText("en"), onInlineImageUpload = null, variant = "standard", designBriefFiles = [] }) {'''
parts_marker_new = '''// TOS_TASK_DESCRIPTION_MIXED_DIRECTION_FIX_V1
function PremiumTaskRichTextEditor({ value, onChange, placeholder, minHeight = "min-h-[110px]", label, disabled = false, ui = getTaskUiText("en"), onInlineImageUpload = null, variant = "standard", designBriefFiles = [] }) {'''
if parts.count(parts_marker_anchor) != 1:
    fail(f"parts marker anchor expected once, found {parts.count(parts_marker_anchor)}")
parts = parts.replace(parts_marker_anchor, parts_marker_new, 1)

FILES["shared"].write_text(shared, encoding="utf-8")
FILES["parts"].write_text(parts, encoding="utf-8")

try:
    subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--check", "--",
         "frontend/src/features/tasks/taskShared.jsx",
         "frontend/src/features/tasks/taskBoardParts.jsx"],
        check=True,
    )
except Exception:
    fail("git diff --check failed; originals restored", originals)

required_after = [
    MARKER,
    "function applyRichTextAutoDirection(root)",
    'block.setAttribute("dir", "auto")',
    'valueNode.setAttribute("dir", "auto")',
    'block.setAttribute("data-tos-manual-direction", "true")',
    'style={{ unicodeBidi: "plaintext", textAlign: "start" }}',
]
joined = FILES["shared"].read_text(encoding="utf-8") + "\n" + FILES["parts"].read_text(encoding="utf-8")
missing = [item for item in required_after if item not in joined]
if missing:
    fail(f"Post-patch validation failed: {missing}", originals)

print("PATCH=PASS")
print("ACTION=APPLIED")
print("ROOT_CAUSE=UI_LANGUAGE_DIRECTION_WAS_FORCED_ON_MIXED_DESIGN_REQUEST_CONTENT")
print("EDITOR_DIRECTION=AUTO_PER_BLOCK")
print("DISPLAY_DIRECTION=AUTO_PER_BLOCK")
print("DESIGN_REQUEST_VALUES=AUTO_DIRECTION")
print("MANUAL_RTL_LTR=PRESERVED")
print("TEXT_CONTENT=UNCHANGED")
print("DB_CHANGES=NONE")
print("FILES_CHANGED=frontend/src/features/tasks/taskShared.jsx,frontend/src/features/tasks/taskBoardParts.jsx")
print("BUILD=NOT_RUN")
print("DEPLOY=NOT_RUN")
