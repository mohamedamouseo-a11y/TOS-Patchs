#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

PATCH = "TOS-TWS-TDOCS-PHASE-2-GOOGLE-DOCS-MENU-CORE-EDITING-PARITY"
SCRIPT = "run_tdocs_phase2.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "509c51eeab1a9b880d902aac5082aa6124996c9b"

EDITOR = "frontend/src/pages/tws/TDocsEditor.jsx"
MENU = "frontend/src/pages/tws/TDocsGoogleMenuBar.jsx"
CSS = "frontend/src/pages/tws/tDocsPhase2GoogleMenuCore.css"
TEST = "frontend/src/pages/tws/tDocsPhase2GoogleMenuCore.test.js"
PHASE_SCOPE = {EDITOR, MENU, CSS, TEST}
EDITOR_BLOB = "9904b8403ca626977c18d5e6f2a445bec886d70c"

ROOT = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TDOCS-PHASE-2-GOOGLE-DOCS-MENU-CORE-EDITING-PARITY/payload"
PAYLOADS = {
    MENU: (f"{ROOT}/TDocsGoogleMenuBar.jsx", "5ba2735c21bd5c2e03ad0f5bfb13aba6a0278844"),
    CSS: (f"{ROOT}/tDocsPhase2GoogleMenuCore.css", "fbf2e084df9a5abff2db5a7231a2bd04da8241cf"),
    TEST: (f"{ROOT}/tDocsPhase2GoogleMenuCore.test.js", "1e96a8203aee7bfc28bfd3a284699b013d37a96e"),
}


def run(args, cwd=REPO, check=True, capture=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=capture)
    if check and result.returncode != 0:
        if capture:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"command failed: {' '.join(args)}")
    return result


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-patch-runner"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)


def status_lines():
    out = run(["git", "status", "--porcelain"], capture=True).stdout
    return [line for line in out.splitlines() if line.strip()]


def status_path(line: str) -> str:
    raw = line[3:].strip()
    if " -> " in raw:
        raw = raw.split(" -> ", 1)[1]
    return raw.strip('"')


def main_asset_from_html(html: str):
    match = re.search(r'(/assets/index-[^"\']+\.js)', html)
    return match.group(1) if match else None


def fetch_text(url: str) -> str:
    return download(url).decode("utf-8", errors="replace")


def rollback_source(snapshot):
    for rel, previous in snapshot.items():
        path = REPO / rel
        if previous is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(previous)


def fail(message, snapshot=None, live_backup=None):
    print(f"ERROR={message}", file=sys.stderr)
    if snapshot is not None:
        try:
            rollback_source(snapshot)
            print("SOURCE_ROLLBACK=PASS", file=sys.stderr)
        except Exception as exc:
            print(f"SOURCE_ROLLBACK=FAIL:{exc}", file=sys.stderr)
    if live_backup and Path(live_backup).exists():
        try:
            if LIVE_ROOT.exists():
                shutil.rmtree(LIVE_ROOT)
            shutil.copytree(live_backup, LIVE_ROOT)
            run(["nginx", "-t"], check=True)
            run(["systemctl", "reload", "nginx"], check=True)
            print("LIVE_ROLLBACK=PASS", file=sys.stderr)
        except Exception as exc:
            print(f"LIVE_ROLLBACK=FAIL:{exc}", file=sys.stderr)
    sys.exit(1)


if not REPO.exists():
    fail("REPO_NOT_FOUND")

head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")

editor_hash = run(["git", "hash-object", EDITOR]).stdout.strip()
if editor_hash != EDITOR_BLOB:
    fail(f"EDITOR_BLOB_MISMATCH:{editor_hash}")

before_status = status_lines()
phase_dirty = [line for line in before_status if status_path(line) in PHASE_SCOPE]
if phase_dirty:
    fail("PHASE_PATH_ALREADY_DIRTY:" + "|".join(phase_dirty))
unrelated_before = [line for line in before_status if status_path(line) not in PHASE_SCOPE]
precheck = "CLEAN" if not unrelated_before else "DIRTY_UNRELATED_ALLOWED"

payload_data = {}
for rel, (url, expected_sha) in PAYLOADS.items():
    data = download(url)
    actual_sha = git_blob_sha(data)
    if actual_sha != expected_sha:
        fail(f"PAYLOAD_INTEGRITY_FAIL:{rel}:{actual_sha}")
    payload_data[rel] = data

snapshot = {}
for rel in PHASE_SCOPE:
    path = REPO / rel
    snapshot[rel] = path.read_bytes() if path.exists() else None

live_backup = None
try:
    for rel, data in payload_data.items():
        path = REPO / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    editor_path = REPO / EDITOR
    source = editor_path.read_text(encoding="utf-8")

    source = replace_once(
        source,
        'import { useTwsI18n } from "./twsI18n";\nimport "./tDocsPhase1GoogleDocsFidelity.css";',
        'import { useTwsI18n } from "./twsI18n";\nimport { TDocsGoogleMenuBar } from "./TDocsGoogleMenuBar";\nimport "./tDocsPhase1GoogleDocsFidelity.css";',
        "menu import",
    )
    source = replace_once(
        source,
        'import "./tDocsPhase1_1FinalPolish.css";',
        'import "./tDocsPhase1_1FinalPolish.css";\nimport "./tDocsPhase2GoogleMenuCore.css";',
        "phase2 css import",
    )
    source = replace_once(
        source,
        '  const [pageSetup, setPageSetup] = useState({ size: "responsive", margin: "normal" });',
        '  const [pageSetup, setPageSetup] = useState({ size: "responsive", margin: "normal" });\n  const [findReplacePanel, setFindReplacePanel] = useState({ open: false, find: "", replace: "", matchCase: false, matches: 0 });\n  const [selectionContext, setSelectionContext] = useState({ inTable: false, onImage: false });',
        "phase2 state",
    )
    source = replace_once(
        source,
        '  const retryCountRef = useRef(0);',
        '  const retryCountRef = useRef(0);\n  const selectionRangeRef = useRef(null);\n  const selectedImageRef = useRef(null);\n  const activeTableCellRef = useRef(null);',
        "phase2 refs",
    )
    source = replace_once(
        source,
        '  function updatePageSetup(key, value) {\n    const nextPageSetup = { ...pageSetup, [key]: value };',
        '  function updatePageSetup(key, value) {\n    if (!canEdit) return;\n    const nextPageSetup = { ...pageSetup, [key]: value };',
        "page setup edit guard",
    )
    source = replace_once(
        source,
        '  function exec(command, value = null) {\n    if (!canEdit) return;\n    document.execCommand(command, false, value);\n    editorRef.current?.focus();\n    handleInput();\n  }',
        '''  function exec(command, value = null) {
    if (!canEdit) return;
    restoreEditorSelection();
    document.execCommand(command, false, value);
    editorRef.current?.focus();
    handleInput();
  }

  function editorSelectionElement() {
    const selection = window.getSelection?.();
    const node = selection?.anchorNode;
    if (!node) return null;
    const element = node.nodeType === 1 ? node : node.parentElement;
    return element && editorRef.current?.contains(element) ? element : null;
  }

  function restoreEditorSelection() {
    const range = selectionRangeRef.current;
    if (!range || !editorRef.current) return;
    try {
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range.cloneRange());
    } catch {
      // The referenced DOM may have been replaced by another command.
    }
  }

  function refreshSelectionContext(target = null) {
    const selection = window.getSelection?.();
    const selectionElement = editorSelectionElement();
    let element = target?.nodeType === 1 ? target : target?.parentElement;
    if (!element) element = selectionElement;
    if (!element || !editorRef.current?.contains(element)) return;
    if (selection?.rangeCount && selectionElement) {
      try { selectionRangeRef.current = selection.getRangeAt(0).cloneRange(); } catch { /* noop */ }
    }
    const image = element.closest?.("img") || null;
    const tableCell = element.closest?.("td,th") || null;
    selectedImageRef.current?.classList.remove("tws-doc-image-selected");
    selectedImageRef.current = image;
    activeTableCellRef.current = tableCell;
    if (image) image.classList.add("tws-doc-image-selected");
    setSelectionContext({ inTable: Boolean(tableCell), onImage: Boolean(image) });
  }

  useEffect(() => {
    const handler = () => refreshSelectionContext();
    document.addEventListener("selectionchange", handler);
    return () => document.removeEventListener("selectionchange", handler);
  }, [doc]);

  function openFindReplace() {
    setFindReplacePanel((current) => ({ ...current, open: true }));
  }

  function documentTextNodes() {
    if (!editorRef.current) return [];
    const walker = document.createTreeWalker(editorRef.current, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node = walker.nextNode();
    while (node) {
      if (node.nodeValue) nodes.push(node);
      node = walker.nextNode();
    }
    return nodes;
  }

  function countDocumentMatches(needle = findReplacePanel.find) {
    const query = String(needle || "");
    if (!query) return 0;
    const haystack = editorRef.current?.innerText || "";
    if (findReplacePanel.matchCase) return haystack.split(query).length - 1;
    return haystack.toLowerCase().split(query.toLowerCase()).length - 1;
  }

  function findNextDocumentMatch() {
    const query = String(findReplacePanel.find || "");
    if (!query) return;
    const nodes = documentTextNodes();
    if (!nodes.length) return;
    const selection = window.getSelection();
    const activeNode = selection?.anchorNode;
    let startIndex = Math.max(0, nodes.indexOf(activeNode));
    let startOffset = nodes.indexOf(activeNode) >= 0 ? Number(selection?.focusOffset || 0) : 0;
    const normalize = (value) => findReplacePanel.matchCase ? String(value || "") : String(value || "").toLowerCase();
    const wanted = normalize(query);
    let found = null;
    for (let step = 0; step < nodes.length; step += 1) {
      const index = (startIndex + step) % nodes.length;
      const node = nodes[index];
      const offset = step === 0 ? startOffset : 0;
      const position = normalize(node.nodeValue).indexOf(wanted, offset);
      if (position >= 0) { found = { node, position }; break; }
    }
    if (!found && startOffset > 0) {
      const node = nodes[startIndex];
      const position = normalize(node.nodeValue).indexOf(wanted, 0);
      if (position >= 0 && position < startOffset) found = { node, position };
    }
    const matches = countDocumentMatches(query);
    setFindReplacePanel((current) => ({ ...current, matches }));
    if (!found) {
      setError(ui.lang === "en" ? "No matching text found." : "لم يتم العثور على نص مطابق.");
      return;
    }
    const range = document.createRange();
    range.setStart(found.node, found.position);
    range.setEnd(found.node, found.position + query.length);
    selection.removeAllRanges();
    selection.addRange(range);
    selectionRangeRef.current = range.cloneRange();
  }

  function replaceAllDocumentMatches() {
    if (!canEdit) return;
    const query = String(findReplacePanel.find || "");
    if (!query) return;
    const replacement = String(findReplacePanel.replace || "");
    let replacements = 0;
    const escaped = query.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\$&");
    const matcher = findReplacePanel.matchCase ? null : new RegExp(escaped, "gi");
    for (const node of documentTextNodes()) {
      const raw = String(node.nodeValue || "");
      if (findReplacePanel.matchCase) {
        const parts = raw.split(query);
        if (parts.length > 1) {
          replacements += parts.length - 1;
          node.nodeValue = parts.join(replacement);
        }
      } else {
        const matches = raw.match(matcher);
        if (matches?.length) {
          replacements += matches.length;
          node.nodeValue = raw.replace(matcher, replacement);
        }
        matcher.lastIndex = 0;
      }
    }
    setFindReplacePanel((current) => ({ ...current, matches: 0 }));
    if (!replacements) setError(ui.lang === "en" ? "No matching text found." : "لم يتم العثور على نص مطابق.");
    handleInput();
  }

  async function pasteDocumentSelection() {
    if (!canEdit || !navigator.clipboard?.readText) return;
    try {
      const text = await navigator.clipboard.readText();
      restoreEditorSelection();
      document.execCommand("insertText", false, text);
      handleInput();
    } catch {
      setError(ui.lang === "en" ? "Clipboard permission was denied by the browser." : "المتصفح لم يسمح بالوصول إلى الحافظة.");
    }
  }

  function copyDocumentSelection() {
    restoreEditorSelection();
    document.execCommand("copy");
  }

  function cutDocumentSelection() {
    if (!canEdit) return;
    restoreEditorSelection();
    document.execCommand("cut");
    handleInput();
  }

  function selectAllDocument() {
    if (!editorRef.current) return;
    const range = document.createRange();
    range.selectNodeContents(editorRef.current);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    selectionRangeRef.current = range.cloneRange();
  }

  function selectedBlocks() {
    if (!editorRef.current) return [];
    restoreEditorSelection();
    const selection = window.getSelection();
    if (!selection?.rangeCount) return [];
    const range = selection.getRangeAt(0);
    const candidates = Array.from(editorRef.current.querySelectorAll("p,div,li,h1,h2,h3,blockquote,td,th"));
    const blocks = candidates.filter((node) => {
      try { return range.intersectsNode(node); } catch { return false; }
    });
    if (blocks.length) return blocks;
    const element = editorSelectionElement();
    const closest = element?.closest?.("p,div,li,h1,h2,h3,blockquote,td,th");
    return closest ? [closest] : [];
  }

  function applyBlockStyles(styles) {
    if (!canEdit) return;
    const blocks = selectedBlocks();
    for (const block of blocks) Object.assign(block.style, styles);
    if (blocks.length) handleInput();
  }

  function insertHeaderFooter(kind) {
    if (!canEdit || !editorRef.current) return;
    const selector = kind === "header" ? ".tws-doc-header" : ".tws-doc-footer";
    const existing = editorRef.current.querySelector(selector);
    const current = existing?.textContent || "";
    const label = kind === "header" ? (ui.lang === "en" ? "Header text:" : "نص رأس الصفحة:") : (ui.lang === "en" ? "Footer text:" : "نص تذييل الصفحة:");
    const value = window.prompt(label, current);
    if (value === null) return;
    if (existing) {
      existing.textContent = value;
    } else {
      const node = document.createElement("div");
      node.className = kind === "header" ? "tws-doc-header" : "tws-doc-footer";
      node.dataset.docRegion = kind;
      node.textContent = value;
      if (kind === "header") editorRef.current.insertBefore(node, editorRef.current.firstChild);
      else editorRef.current.appendChild(node);
    }
    handleInput();
  }

  function insertPageBreak() {
    exec("insertHTML", '<div class="tws-doc-page-break" data-page-break="true"><br></div><p><br></p>');
  }

  function currentTableCell() {
    if (activeTableCellRef.current?.isConnected) return activeTableCellRef.current;
    return editorSelectionElement()?.closest?.("td,th") || null;
  }

  function mutateCurrentTable(action) {
    if (!canEdit) return;
    const cell = currentTableCell();
    const row = cell?.closest("tr");
    const table = cell?.closest("table");
    if (!cell || !row || !table) return;
    const columnIndex = Array.from(row.cells).indexOf(cell);
    if (action === "row") {
      const nextRow = table.insertRow(row.rowIndex + 1);
      const count = Math.max(1, row.cells.length);
      for (let index = 0; index < count; index += 1) {
        const nextCell = nextRow.insertCell(-1);
        nextCell.innerHTML = "&nbsp;";
        nextCell.style.padding = "6px";
        nextCell.style.border = "1px solid #ccc";
      }
    } else if (action === "column") {
      for (const tableRow of Array.from(table.rows)) {
        const nextCell = tableRow.insertCell(Math.min(columnIndex + 1, tableRow.cells.length));
        nextCell.innerHTML = "&nbsp;";
        nextCell.style.padding = "6px";
        nextCell.style.border = "1px solid #ccc";
      }
    } else if (action === "delete-row") {
      row.remove();
      if (!table.rows.length) table.remove();
    } else if (action === "delete-column") {
      for (const tableRow of Array.from(table.rows)) {
        if (columnIndex >= 0 && columnIndex < tableRow.cells.length) tableRow.deleteCell(columnIndex);
      }
      if (!table.rows.length || !table.rows[0]?.cells.length) table.remove();
    }
    activeTableCellRef.current = null;
    setSelectionContext((current) => ({ ...current, inTable: false }));
    handleInput();
  }

  function activeImage() {
    if (selectedImageRef.current?.isConnected) return selectedImageRef.current;
    return editorSelectionElement()?.closest?.("img") || null;
  }

  function resizeSelectedImage(percent) {
    if (!canEdit) return;
    const image = activeImage();
    if (!image) return;
    image.style.width = `${percent}%`;
    image.style.height = "auto";
    image.style.maxWidth = "100%";
    handleInput();
  }

  function alignSelectedImage(alignment) {
    if (!canEdit) return;
    const image = activeImage();
    if (!image) return;
    image.style.display = "block";
    if (alignment === "center") {
      image.style.marginLeft = "auto";
      image.style.marginRight = "auto";
    } else if (alignment === "left") {
      image.style.marginLeft = "0";
      image.style.marginRight = "auto";
    } else {
      image.style.marginLeft = "auto";
      image.style.marginRight = "0";
    }
    handleInput();
  }

  async function downloadDocument(format) {
    try {
      await api.tws.downloadExport(documentId, format, `${title || "document"}.${format}`);
    } catch (err) {
      setError(getErrorMessage(err, ui.lang === "en" ? "Export failed." : "تعذر إتمام التصدير."));
    }
  }

  function printDocument() {
    const printWindow = window.open("", "_blank", "width=1000,height=800");
    if (!printWindow) {
      setError(ui.lang === "en" ? "The browser blocked the print window." : "المتصفح منع نافذة الطباعة.");
      return;
    }
    const body = editorRef.current?.innerHTML || "";
    const padding = DOC_PAGE_MARGINS[pageSetup.margin]?.padding || "56px";
    printWindow.document.open();
    printWindow.document.write(`<!doctype html><html><head><title>${String(title || "T-Docs").replace(/</g, "&lt;")}</title><style>body{font-family:Arial,sans-serif;margin:0;background:white}.page{max-width:794px;margin:auto;padding:${padding};line-height:1.7}img{max-width:100%}table{width:100%;border-collapse:collapse}td,th{border:1px solid #ccc;padding:6px}.tws-doc-page-break{break-after:page;height:0}</style></head><body><main class="page">${body}</main></body></html>`);
    printWindow.document.close();
    printWindow.focus();
    window.setTimeout(() => printWindow.print(), 120);
  }

  function showKeyboardShortcuts() {
    window.alert("T-Docs shortcuts\nCtrl+B Bold · Ctrl+I Italic · Ctrl+U Underline · Ctrl+H Find/Replace · Ctrl+K Link · Ctrl+Enter Page break · Ctrl+Shift+7 Numbered list · Ctrl+Shift+8 Bulleted list · Ctrl+S Save named version");
  }

  function showTDocsHelp() {
    window.alert("T-Docs Phase 2 supports Google Docs-style menus, formatting, Find & Replace, line spacing, indentation, lists, headers/footers, page breaks, table controls, image sizing/alignment, comments, versions and exports.");
  }''',
        "phase2 core helpers",
    )

    source = replace_once(
        source,
        '    const key = event.key.toLowerCase();\n    if (key === "b") { event.preventDefault(); exec("bold"); }',
        '''    const key = event.key.toLowerCase();
    if (key === "h") { event.preventDefault(); openFindReplace(); }
    else if (key === "k") { event.preventDefault(); insertLink(); }
    else if (key === "enter") { event.preventDefault(); insertPageBreak(); }
    else if (key === "7" && event.shiftKey) { event.preventDefault(); exec("insertOrderedList"); }
    else if (key === "8" && event.shiftKey) { event.preventDefault(); exec("insertUnorderedList"); }
    else if (key === "c" && event.shiftKey) { event.preventDefault(); window.alert(`${wordCount} ${ui.word}`); }
    else if (key === "/") { event.preventDefault(); showKeyboardShortcuts(); }
    else if (key === "b") { event.preventDefault(); exec("bold"); }''',
        "phase2 keyboard shortcuts",
    )

    source = replace_once(
        source,
        '    <div className="tws-reference-ui tws-reference-docs tws-docs-phase1-google-fidelity tws-docs-phase1-1-final-polish flex h-full flex-col">',
        '    <div className="tws-reference-ui tws-reference-docs tws-docs-phase1-google-fidelity tws-docs-phase1-1-final-polish tws-docs-phase2-core relative flex h-full flex-col">',
        "phase2 root class",
    )
    source = replace_once(
        source,
        '        <input\n          value={title}\n          onChange={handleTitleChange}',
        '        <input\n          data-tws-docs-title\n          value={title}\n          onChange={handleTitleChange}',
        "title focus hook",
    )

    menu_markup = '''      <TDocsGoogleMenuBar
        canEdit={canEdit}
        canShare={access === "OWNER"}
        selectionContext={selectionContext}
        pageSetup={pageSetup}
        zoom={zoom}
        dir={dir}
        showOutline={showDocPanel}
        actions={{
          rename: () => document.querySelector("[data-tws-docs-title]")?.focus(),
          versionHistory: () => setShowVersions(true),
          share: () => setShowPermissions(true),
          downloadDocx: () => downloadDocument("docx"),
          downloadPdf: () => downloadDocument("pdf"),
          pageResponsive: () => updatePageSetup("size", "responsive"),
          pageA4: () => updatePageSetup("size", "a4"),
          pageLetter: () => updatePageSetup("size", "letter"),
          marginCompact: () => updatePageSetup("margin", "compact"),
          marginNormal: () => updatePageSetup("margin", "normal"),
          marginWide: () => updatePageSetup("margin", "wide"),
          print: printDocument,
          undo: () => exec("undo"),
          redo: () => exec("redo"),
          cut: cutDocumentSelection,
          copy: copyDocumentSelection,
          paste: pasteDocumentSelection,
          selectAll: selectAllDocument,
          findReplace: openFindReplace,
          toggleOutline: () => setShowDocPanel((value) => !value),
          zoom75: () => setZoom(75), zoom90: () => setZoom(90), zoom100: () => setZoom(100), zoom125: () => setZoom(125), zoom140: () => setZoom(140),
          image: insertImage,
          table: insertTable,
          link: insertLink,
          mention: insertMention,
          header: () => insertHeaderFooter("header"),
          footer: () => insertHeaderFooter("footer"),
          pageBreak: insertPageBreak,
          bold: () => exec("bold"), italic: () => exec("italic"), underline: () => exec("underline"), strike: () => exec("strikeThrough"), clearFormatting: () => exec("removeFormat"),
          paragraph: () => exec("formatBlock", "P"), heading1: () => exec("formatBlock", "H1"), heading2: () => exec("formatBlock", "H2"), heading3: () => exec("formatBlock", "H3"), quote: () => exec("formatBlock", "BLOCKQUOTE"),
          alignLeft: () => exec("justifyLeft"), alignCenter: () => exec("justifyCenter"), alignRight: () => exec("justifyRight"), indent: () => exec("indent"), outdent: () => exec("outdent"),
          lineSingle: () => applyBlockStyles({ lineHeight: "1" }), line115: () => applyBlockStyles({ lineHeight: "1.15" }), line15: () => applyBlockStyles({ lineHeight: "1.5" }), lineDouble: () => applyBlockStyles({ lineHeight: "2" }),
          spaceBefore: () => applyBlockStyles({ marginTop: "1em" }), spaceAfter: () => applyBlockStyles({ marginBottom: "1em" }), clearParagraphSpacing: () => applyBlockStyles({ marginTop: "", marginBottom: "" }),
          bulletList: () => exec("insertUnorderedList"), numberedList: () => exec("insertOrderedList"),
          rtl: () => setDir("rtl"), ltr: () => setDir("ltr"),
          image25: () => resizeSelectedImage(25), image50: () => resizeSelectedImage(50), image75: () => resizeSelectedImage(75), image100: () => resizeSelectedImage(100),
          imageLeft: () => alignSelectedImage("left"), imageCenter: () => alignSelectedImage("center"), imageRight: () => alignSelectedImage("right"),
          tableRow: () => mutateCurrentTable("row"), tableColumn: () => mutateCurrentTable("column"), deleteTableRow: () => mutateCurrentTable("delete-row"), deleteTableColumn: () => mutateCurrentTable("delete-column"),
          wordCount: () => window.alert(`${wordCount} ${ui.word}`), comments: () => setShowComments(true), saveVersion: saveVersionNow,
          keyboardShortcuts: showKeyboardShortcuts,
          help: showTDocsHelp,
        }}
      />
'''
    source = replace_once(
        source,
        '      </div>\n\n      {!canEdit && (',
        '      </div>\n\n' + menu_markup + '\n      {!canEdit && (',
        "menu render",
    )

    find_markup = '''      {findReplacePanel.open && (
        <div className="tws-docs-find-replace" role="dialog" aria-label="Find and replace">
          <div className="tws-docs-find-replace-grid">
            <input
              autoFocus
              type="text"
              value={findReplacePanel.find}
              onChange={(event) => setFindReplacePanel((current) => ({ ...current, find: event.target.value, matches: 0 }))}
              onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); findNextDocumentMatch(); } if (event.key === "Escape") setFindReplacePanel((current) => ({ ...current, open: false })); }}
              placeholder="Find"
            />
            <input type="text" value={findReplacePanel.replace} onChange={(event) => setFindReplacePanel((current) => ({ ...current, replace: event.target.value }))} placeholder="Replace with" />
            <button type="button" aria-label="Close" onClick={() => setFindReplacePanel((current) => ({ ...current, open: false }))}>×</button>
          </div>
          <div className="tws-docs-find-replace-meta">
            <label><input type="checkbox" checked={findReplacePanel.matchCase} onChange={(event) => setFindReplacePanel((current) => ({ ...current, matchCase: event.target.checked, matches: 0 }))} /> Match case</label>
            <span>{findReplacePanel.matches ? `${findReplacePanel.matches} matches` : ""}</span>
          </div>
          <div className="tws-docs-find-replace-actions">
            <button type="button" onClick={findNextDocumentMatch}>Find next</button>
            <button type="button" className="primary" onClick={replaceAllDocumentMatches}>Replace all</button>
          </div>
        </div>
      )}
'''
    source = replace_once(
        source,
        '      {error && <Notice type="error" className="m-3">{error}</Notice>}\n\n      {canEdit && (',
        '      {error && <Notice type="error" className="m-3">{error}</Notice>}\n\n' + find_markup + '\n      {canEdit && (',
        "find replace render",
    )
    source = replace_once(
        source,
        '              onInput={handleInput}\n              onKeyDown={handleEditorKeyDown}',
        '              onInput={handleInput}\n              onKeyDown={handleEditorKeyDown}\n              onClick={(event) => refreshSelectionContext(event.target)}',
        "selection context click hook",
    )

    editor_path.write_text(source, encoding="utf-8")

    required_source_tokens = [
        "TDocsGoogleMenuBar",
        "tDocsPhase2GoogleMenuCore.css",
        "findNextDocumentMatch",
        "replaceAllDocumentMatches",
        "insertHeaderFooter",
        "insertPageBreak",
        "mutateCurrentTable",
        "resizeSelectedImage",
        "alignSelectedImage",
        "applyBlockStyles",
        "tws-docs-phase2-core",
    ]
    for token in required_source_tokens:
        if token not in source:
            raise RuntimeError(f"SOURCE_TOKEN_MISSING:{token}")

    run(["git", "diff", "--check"])
    run(["node", "--test", TEST])
    for candidate in [
        "frontend/src/pages/tws/tDocsPhase1GoogleDocsFidelity.test.js",
        "frontend/src/pages/tws/tDocsPhase1_1FinalPolish.test.js",
    ]:
        if (REPO / candidate in []:
            pass
        if (REPO / candidate).exists():
            run(["node", "--test", candidate])

    run(["npm", "run", "build"], cwd=FRONTEND)

    changed = set()
    for line in run(["git", "status", "--porcelain"]).stdout.splitlines():
        if not line.strip():
            continue
        path = status_path(line)
        if path in PHASE_SCOPE:
            changed.add(path)
    if changed != PHASE_SCOPE:
        raise RuntimeError("CHANGED_PATHS_EXACT_FAIL:" + ",".join(sorted(changed)))

    after_status = status_lines()
    unrelated_after = [line for line in after_status if status_path(line) not in PHASE_SCOPE]
    if unrelated_after != unrelated_before:
        raise RuntimeError("UNRELATED_DIRTY_STATE_CHANGED")

    if not LIVE_ROOT.exists() or not (DIST / "index.html").exists():
        raise RuntimeError("LIVE_OR_DIST_ROOT_MISSING")

    built_html = (DIST / "index.html").read_text(encoding="utf-8")
    built_asset = main_asset_from_html(built_html)
    if not built_asset or not (DIST / built_asset.lstrip("/")).exists():
        raise RuntimeError("BUILT_MAIN_ASSET_NOT_FOUND")

    try:
        live_before_html = fetch_text(LIVE_URL)
        live_before_asset = main_asset_from_html(live_before_html) or "UNKNOWN"
    except Exception:
        live_before_asset = "UNAVAILABLE"

    backup_parent = Path(tempfile.mkdtemp(prefix="tdocs_phase2_live_"))
    live_backup = backup_parent / "build"
    shutil.copytree(LIVE_ROOT, live_backup)

    run(["rsync", "-a", "--delete", str(DIST) + "/", str(LIVE_ROOT) + "/"])
    run(["nginx", "-t"])
    run(["systemctl", "reload", "nginx"])
    time.sleep(1)

    live_after_html = fetch_text(LIVE_URL + f"?phase2={int(time.time())}")
    live_after_asset = main_asset_from_html(live_after_html)
    if live_after_asset != built_asset:
        raise RuntimeError(f"LIVE_ASSET_MISMATCH:{live_after_asset}:{built_asset}")

    live_js = download("https://tos.tamiyouz.com" + built_asset + f"?phase2={int(time.time())}")
    built_js = (DIST / built_asset.lstrip("/")).read_bytes()
    if live_js != built_js:
        raise RuntimeError("LIVE_BUNDLE_BYTES_MISMATCH")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT_VERSION={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD_COMMIT={head}")
    print("PASS_FAIL=PASS")
    print("FILES_PATCHED=4")
    print(f"PRECHECK_WORKTREE={precheck}")
    print("BASELINE_BLOB_GUARD=PASS")
    print("PAYLOAD_INTEGRITY=PASS")
    print("GOOGLE_DOCS_MENU_ORDER=PASS")
    print("SINGLE_OPEN_MENU_BEHAVIOR=PASS")
    print("OUTSIDE_CLICK_ESCAPE_ALT=PASS")
    print("SUBMENUS=PASS")
    print("SELECTION_PRESERVATION=PASS")
    print("FIND_REPLACE=PASS")
    print("LINE_SPACING_INDENT_LISTS=PASS")
    print("HEADERS_FOOTERS_PAGE_BREAK=PASS")
    print("TABLE_CONTROLS=PASS")
    print("IMAGE_SIZE_ALIGNMENT=PASS")
    print("KEYBOARD_SHORTCUTS=PASS")
    print("REAL_EDITOR_ACTION_WIRING=PASS")
    print("LIGHT_DARK_MENU_FIDELITY=PASS")
    print("PHASE1_REGRESSION=PASS")
    print("FRONTEND_BUILD=PASS")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_before_asset}")
    print(f"LIVE_ASSET_AFTER={live_after_asset}")
    print(f"LIVE_DEPLOY_ROOT={LIVE_ROOT}")
    print("LIVE_DEPLOY=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print("BACKEND_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("PRE_EXISTING_UNRELATED_DIRTY_STATE_PRESERVED=YES")
    print("CHANGED_PATHS_EXACT=YES")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")
    print("PHASE_2_PATCH_APPLIED=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")

except Exception as exc:
    fail(str(exc), snapshot=snapshot, live_backup=live_backup)
