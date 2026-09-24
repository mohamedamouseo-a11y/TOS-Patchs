#!/usr/bin/env python3
# TOS-TASK-DESCRIPTION-BIDI-MARKDOWN-FIX-V3
from pathlib import Path
import shutil, sys, time

ROOT = Path.cwd()
SHARED = ROOT / "frontend/src/features/tasks/taskShared.jsx"
PARTS = ROOT / "frontend/src/features/tasks/taskBoardParts.jsx"
MARKER = "TOS_TASK_DESCRIPTION_BIDI_MARKDOWN_FIX_V3"

def die(message):
    print(f"PATCH=FAIL\nERROR={message}")
    sys.exit(1)

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        die(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)

for path in (SHARED, PARTS):
    if not path.exists():
        die(f"missing file: {path}")

shared = SHARED.read_text(encoding="utf-8")
parts = PARTS.read_text(encoding="utf-8")

if MARKER in shared and MARKER in parts:
    print("PATCH=SKIP_ALREADY_APPLIED")
    sys.exit(0)

if "TOS_TASK_DESCRIPTION_SMART_DIRECTION_FIX_V2" not in shared:
    die("required smart direction V2 marker missing")
if "TOS_TASK_DESCRIPTION_MIXED_DIRECTION_FIX_V1" not in parts:
    die("required mixed direction V1 marker missing")

stamp = int(time.time())
shutil.copy2(SHARED, SHARED.with_name(SHARED.name + f".bak-bidi-markdown-v3-{stamp}"))
shutil.copy2(PARTS, PARTS.with_name(PARTS.name + f".bak-bidi-markdown-v3-{stamp}"))

plain_anchor = '''function plainTextToRichTextHtml(text = "", ui = getTaskUiText("en")) {
  const source = String(text || "");
  let output = "";
  let lastIndex = 0;

  for (const match of source.matchAll(richTextUrlPattern)) {
    const token = match[0];
    const offset = match.index ?? 0;
    output += escapeHtml(source.slice(lastIndex, offset)).replace(/\\n/g, "<br>");
    const { url, trailing } = sanitizeUrlToken(token);
    output += url ? richTextLinkHtml(url, token.replace(/[),.;!?]+$/, ""), ui) : escapeHtml(token);
    if (trailing) output += escapeHtml(trailing);
    lastIndex = offset + token.length;
  }

  output += escapeHtml(source.slice(lastIndex)).replace(/\\n/g, "<br>");
  return output;
}
'''

helpers = r'''
// TOS_TASK_DESCRIPTION_BIDI_MARKDOWN_FIX_V3
function basicMarkdownTextToRichTextHtml(text = "") {
  let html = escapeHtml(String(text || ""));
  html = html
    .replace(/`([^`\n]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_\n]+)__/g, "<strong>$1</strong>")
    .replace(/~~([^~\n]+)~~/g, "<s>$1</s>")
    .replace(/(^|[\s(\\[{])\*([^*\n]+)\*(?=$|[\s).,!?:;\]}\u060C\u061B\u061F])/g, "$1<em>$2</em>")
    .replace(/(^|[\s(\\[{])_([^_\n]+)_(?=$|[\s).,!?:;\]}\u060C\u061B\u061F])/g, "$1<em>$2</em>");
  return html.replace(/\n/g, "<br>");
}

function hasBasicMarkdownSyntax(text = "") {
  return /(\*\*[^*\n]+\*\*|__[^_\n]+__|~~[^~\n]+~~|`[^`\n]+`|(^|[\s(\\[{])\*[^*\n]+\*(?=$|[\s).,!?:;\]}\u060C\u061B\u061F])|(^|[\s(\\[{])_[^_\n]+_(?=$|[\s).,!?:;\]}\u060C\u061B\u061F]))/m.test(String(text || ""));
}

function upgradeBasicMarkdownInRichText(root) {
  if (!root || typeof document === "undefined") return false;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node?.parentElement;
      if (!parent) return NodeFilter.FILTER_REJECT;
      if (parent.closest("a,code,pre,script,style,textarea,input,select,option,bdi,.tos-smart-link-chip,[contenteditable='false']")) return NodeFilter.FILTER_REJECT;
      return hasBasicMarkdownSyntax(node.nodeValue || "") ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  let changed = false;
  nodes.forEach((node) => {
    const text = String(node.nodeValue || "");
    if (!hasBasicMarkdownSyntax(text)) return;
    const template = document.createElement("template");
    template.innerHTML = basicMarkdownTextToRichTextHtml(text);
    node.replaceWith(template.content);
    changed = true;
  });
  return changed;
}

function isolateRichTextMixedDirectionRuns(root) {
  if (!root || typeof document === "undefined") return false;
  const blockSelector = "p,li,blockquote,h1,h2,h3,h4,h5,h6,figcaption,.tos-design-request-value";
  const blocks = [root, ...root.querySelectorAll(blockSelector)];
  let changed = false;

  const wrapRuns = (textNode, direction) => {
    const text = String(textNode.nodeValue || "");
    const pattern = direction === "rtl"
      ? /(?:https?:\/\/[^\s<>]+|www\.[^\s<>]+|[A-Za-z0-9][A-Za-z0-9@._+:/?#&=%-]*(?:[ \t]+[A-Za-z0-9][A-Za-z0-9@._+:/?#&=%-]*)*)/g
      : /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF][\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9\u0660-\u0669]*(?:[ \t]+[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF][\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9\u0660-\u0669]*)*/g;
    const matches = [...text.matchAll(pattern)];
    if (!matches.length) return false;
    const fragment = document.createDocumentFragment();
    let offset = 0;
    matches.forEach((match) => {
      const index = match.index ?? 0;
      if (index > offset) fragment.appendChild(document.createTextNode(text.slice(offset, index)));
      const bdi = document.createElement("bdi");
      bdi.setAttribute("dir", direction === "rtl" ? "ltr" : "rtl");
      bdi.setAttribute("data-tos-bidi-isolate", "v3");
      bdi.style.unicodeBidi = "isolate";
      bdi.textContent = match[0];
      fragment.appendChild(bdi);
      offset = index + match[0].length;
    });
    if (offset < text.length) fragment.appendChild(document.createTextNode(text.slice(offset)));
    textNode.replaceWith(fragment);
    return true;
  };

  blocks.forEach((block) => {
    if (!(block instanceof HTMLElement)) return;
    if (block.closest?.(".tos-smart-link-chip,[contenteditable='false']")) return;
    const baseDirection = ["rtl", "ltr"].includes(block.getAttribute("dir"))
      ? block.getAttribute("dir")
      : getRichTextDominantDirection(block);
    if (!baseDirection) return;

    const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node?.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (parent.closest("a,code,pre,script,style,bdi,.tos-smart-link-chip,[contenteditable='false']")) return NodeFilter.FILTER_REJECT;
        const ownerBlock = parent.closest(blockSelector);
        if (block === root) {
          if (ownerBlock) return NodeFilter.FILTER_REJECT;
        } else if (ownerBlock !== block) {
          return NodeFilter.FILTER_REJECT;
        }
        return String(node.nodeValue || "").trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      },
    });

    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);
    textNodes.forEach((node) => {
      if (wrapRuns(node, baseDirection)) changed = true;
    });
  });

  return changed;
}
'''

shared = replace_once(shared, plain_anchor, plain_anchor + helpers, "markdown/bidi helpers")

shared = replace_once(
    shared,
    '''  applyRichTextAutoDirection,
  localizeDesignRequestBlocks,''',
    '''  applyRichTextAutoDirection,
  basicMarkdownTextToRichTextHtml,
  hasBasicMarkdownSyntax,
  upgradeBasicMarkdownInRichText,
  isolateRichTextMixedDirectionRuns,
  localizeDesignRequestBlocks,''',
    "shared exports",
)

parts = replace_once(
    parts,
    '''  normalizeRichTextLinks,
  applyRichTextAutoDirection,
  localizeDesignRequestBlocks,''',
    '''  normalizeRichTextLinks,
  applyRichTextAutoDirection,
  basicMarkdownTextToRichTextHtml,
  hasBasicMarkdownSyntax,
  upgradeBasicMarkdownInRichText,
  isolateRichTextMixedDirectionRuns,
  localizeDesignRequestBlocks,''',
    "task editor imports",
)

parts = replace_once(
    parts,
    '''    const localized = localizeDesignRequestBlocks(root, ui);
    const normalized = normalizeRichTextLinks(root, ui);
    const compacted = compactDesignRequestLinks(root);
    const autoDirected = applyRichTextAutoDirection(root);
    const decorated = decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    if (localized || normalized || compacted || autoDirected || (options.emitDecorations && decorated)) emitChange();
    return localized || normalized || compacted || autoDirected || decorated;''',
    '''    // TOS_TASK_DESCRIPTION_BIDI_MARKDOWN_FIX_V3
    const localized = localizeDesignRequestBlocks(root, ui);
    const markdownUpgraded = upgradeBasicMarkdownInRichText(root);
    const normalized = normalizeRichTextLinks(root, ui);
    const compacted = compactDesignRequestLinks(root);
    const autoDirected = applyRichTextAutoDirection(root);
    const bidiIsolated = isolateRichTextMixedDirectionRuns(root);
    const decorated = decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    if (localized || markdownUpgraded || normalized || compacted || autoDirected || bidiIsolated || (options.emitDecorations && decorated)) emitChange();
    return localized || markdownUpgraded || normalized || compacted || autoDirected || bidiIsolated || decorated;''',
    "editor normalize pipeline",
)

parts = replace_once(
    parts,
    '''    decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    applyRichTextAutoDirection(root);
    updateStats(root);''',
    '''    decorateDesignRequestBriefFiles(root, designBriefFiles, ui);
    upgradeBasicMarkdownInRichText(root);
    normalizeRichTextLinks(root, ui);
    applyRichTextAutoDirection(root);
    isolateRichTextMixedDirectionRuns(root);
    updateStats(root);''',
    "initial editor normalization",
)

parts = replace_once(
    parts,
    '''    if (richHtml) {
      event.preventDefault();
      insertHtml(sanitizeHtml(richHtml));
      return;
    }
    if (/(https?:\\/\\/|www\\.)/i.test(text)) {
      event.preventDefault();
      insertHtml(plainTextToRichTextHtml(text, ui));
    }''',
    '''    if (richHtml) {
      event.preventDefault();
      insertHtml(sanitizeHtml(richHtml));
      return;
    }
    if (hasBasicMarkdownSyntax(text)) {
      event.preventDefault();
      insertHtml(basicMarkdownTextToRichTextHtml(text), { normalizeLinks: true });
      return;
    }
    if (/(https?:\\/\\/|www\\.)/i.test(text)) {
      event.preventDefault();
      insertHtml(plainTextToRichTextHtml(text, ui));
    }''',
    "markdown paste handling",
)

SHARED.write_text(shared, encoding="utf-8")
PARTS.write_text(parts, encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-TASK-DESCRIPTION-BIDI-MARKDOWN-FIX-V3")
print("FILES_CHANGED=frontend/src/features/tasks/taskShared.jsx;frontend/src/features/tasks/taskBoardParts.jsx")
print("RAW_MARKDOWN_BOLD=UPGRADED")
print("RAW_MARKDOWN_ITALIC=UPGRADED")
print("RAW_MARKDOWN_CODE=UPGRADED")
print("RAW_MARKDOWN_STRIKE=UPGRADED")
print("EXISTING_DESCRIPTION_MARKDOWN=NORMALIZED_ON_LOAD")
print("PASTED_MARKDOWN=NORMALIZED_IMMEDIATELY")
print("MIXED_INLINE_BIDI_ISOLATION=ACTIVE")
print("DOMINANT_BLOCK_DIRECTION=PRESERVED")
print("MANUAL_RTL_LTR=PRESERVED")
print("SMART_LINKS=PRESERVED")
print("INLINE_IMAGES=PRESERVED")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
print("DEPENDENCIES_ADDED=NO")
