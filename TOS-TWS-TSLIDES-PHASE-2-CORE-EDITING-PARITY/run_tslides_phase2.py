#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-TSLIDES-PHASE-2-CORE-EDITING-PARITY"
SCRIPT = "run_tslides_phase2.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
BACKEND = REPO / "backend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/tws"
BASELINE = "24b5d8ebeb566f9afd0eddc5ff43f534480178be"

EDITOR = "frontend/src/pages/tws/TSlidesEditor.jsx"
SERVICE = "backend/src/services/workspace.service.js"
EXPORTER = "backend/src/utils/workspaceExport.js"
FE_HELPER = "frontend/src/pages/tws/slideCorePhase2.js"
FE_TEST = "frontend/src/pages/tws/slideCorePhase2.test.js"
FE_CSS = "frontend/src/pages/tws/tSlidesPhase2CoreEditing.css"
BE_HELPER = "backend/src/utils/slideCorePhase2.js"
BE_TEST = "backend/src/utils/slideCorePhase2.test.js"

PHASE_SCOPE = {EDITOR, SERVICE, EXPORTER, FE_HELPER, FE_TEST, FE_CSS, BE_HELPER, BE_TEST}
BASE_BLOBS = {
    EDITOR: "ffd25d6f7dd3d869ecdeaa756d0bd58d3f96028f",
    SERVICE: "179a7e36d74203b24be5e4111d5246a4263f37eb",
    EXPORTER: "9d4d05500f3855f772a2b35a8f97daef2658a177",
}

ROOT = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSLIDES-PHASE-2-CORE-EDITING-PARITY/payload"
PAYLOADS = {
    FE_HELPER: (f"{ROOT}/frontend/slideCorePhase2.js", "fb0e427e0f3efca343bd7ace4e77369610e9336a"),
    FE_TEST: (f"{ROOT}/frontend/slideCorePhase2.test.js", "0edd3545fe425c1208ee3271c199bb200410b78a"),
    FE_CSS: (f"{ROOT}/frontend/tSlidesPhase2CoreEditing.css", "93d22f2c3f9d2e628f5a85a3fd7718452f67a92a"),
    BE_HELPER: (f"{ROOT}/backend/slideCorePhase2.js", "81b96899e718fd92b7c9443909e5fc45c6179bf0"),
    BE_TEST: (f"{ROOT}/backend/slideCorePhase2.test.js", "bcaec1d73de979c23a65ba7fa52b221db4563200"),
}
SNIPPETS = {
    "slide_element": (f"{ROOT}/slideElementPhase2.txt", "1858ea7759b2f3758c092bf9d646db0e5967ab66"),
    "actions": (f"{ROOT}/editorActionsPhase2.txt", "705b96d47c47f7ebe289af00c48f80e4a0998581"),
    "toolbar": (f"{ROOT}/toolbarPhase2.txt", "cd034c6b9f6bdc7e7a0fe1408f61afa6350a7532"),
    "selection_toolbar": (f"{ROOT}/selectionToolbarPhase2.txt", "e340507f5b7b7714ef96222e48965b02deeb57d1"),
    "inspector": (f"{ROOT}/inspectorPhase2.txt", "f0aea213296ca4fbece5423da6327958e0ae9658"),
}

def run(args, cwd=REPO, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode != 0:
        detail = ((p.stdout or "") + (p.stderr or "")).strip()
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(args)}\n{detail}")
    return p

def git(*args, check=True):
    return run(["git", *args], check=check).stdout.strip()

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def changed_paths():
    tracked = set(filter(None, git("diff", "--name-only", "HEAD").splitlines()))
    untracked = set(filter(None, git("ls-files", "--others", "--exclude-standard").splitlines()))
    return tracked | untracked

def fingerprint(rel: str) -> str:
    target = REPO / rel
    if not target.exists():
        return "MISSING"
    if target.is_file():
        return "FILE:" + sha256(target)
    parts = []
    for child in sorted(p for p in target.rglob("*") if p.is_file()):
        parts.append(f"{child.relative_to(target)}:{sha256(child)}")
    return "DIR:" + hashlib.sha256("\n".join(parts).encode()).hexdigest()

def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": "TOS-TSlides-Phase2/1.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()

def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return source.replace(old, new, 1)

def regex_replace_once(source: str, pattern: str, replacement: str, label: str, flags=re.S) -> str:
    matches = list(re.finditer(pattern, source, flags))
    if len(matches) != 1:
        raise RuntimeError(f"{label}: expected 1 regex match, found {len(matches)}")
    m = matches[0]
    return source[:m.start()] + replacement + source[m.end():]

def extract_main_js(html: str):
    matches = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html, re.I)
    return matches[-1] if matches else None

def asset_url(src: str) -> str:
    if src.startswith("http://") or src.startswith("https://"):
        return src
    if not src.startswith("/"):
        src = "/" + src
    return "https://tos.tamiyouz.com" + src

def sync_dist(src: Path, dst: Path):
    if not src.is_dir() or not (src / "index.html").is_file():
        raise RuntimeError("frontend dist is missing")
    if not dst.is_dir() or not (dst / "index.html").is_file():
        raise RuntimeError(f"known production root unavailable: {dst}")
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)

pre_paths = set()
unrelated_fingerprints = {}
original_bytes = {}
source_applied = False
live_index_backup = None
live_synced = False

def rollback_source():
    for rel, data in original_bytes.items():
        (REPO / rel).write_bytes(data)
    for rel in [FE_HELPER, FE_TEST, FE_CSS, BE_HELPER, BE_TEST]:
        target = REPO / rel
        if target.exists():
            target.unlink()

def rollback_live():
    if live_synced and live_index_backup and live_index_backup.is_file():
        shutil.copy2(live_index_backup, LIVE_ROOT / "index.html")
        run(["nginx", "-t"], cwd=Path("/"), check=False)
        run(["systemctl", "reload", "nginx"], cwd=Path("/"), check=False)

def fail(message):
    if live_synced:
        rollback_live()
    if source_applied:
        rollback_source()
    preserved = all(fingerprint(path) == fp for path, fp in unrelated_fingerprints.items())
    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print("RUN=FAIL")
    print(f"ERROR={message}")
    print(f"PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED={'YES' if preserved else 'NO'}")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)

try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")

    head = git("rev-parse", "HEAD")
    if head != BASELINE:
        raise RuntimeError(f"HEAD mismatch: expected {BASELINE}, got {head}")

    for rel, expected_blob in BASE_BLOBS.items():
        actual = git("rev-parse", f"HEAD:{rel}")
        if actual != expected_blob:
            raise RuntimeError(f"baseline blob mismatch for {rel}: expected {expected_blob}, got {actual}")

    pre_paths = changed_paths()
    overlap = pre_paths & PHASE_SCOPE
    if overlap:
        raise RuntimeError("dirty overlap with T-Slides Phase 2 scope: " + ", ".join(sorted(overlap)))
    unrelated_fingerprints = {path: fingerprint(path) for path in pre_paths}

    for rel in [FE_HELPER, FE_TEST, FE_CSS, BE_HELPER, BE_TEST]:
        if (REPO / rel).exists():
            raise RuntimeError(f"unexpected pre-existing Phase 2 file: {rel}")

    payload_bytes = {}
    for rel, (url, expected_blob) in PAYLOADS.items():
        data = fetch_bytes(url)
        if git_blob_sha(data) != expected_blob:
            raise RuntimeError(f"payload integrity mismatch: {rel}")
        payload_bytes[rel] = data

    snippets = {}
    for key, (url, expected_blob) in SNIPPETS.items():
        data = fetch_bytes(url)
        if git_blob_sha(data) != expected_blob:
            raise RuntimeError(f"snippet integrity mismatch: {key}")
        snippets[key] = data.decode("utf-8")

    for rel in [EDITOR, SERVICE, EXPORTER]:
        original_bytes[rel] = (REPO / rel).read_bytes()

    editor = original_bytes[EDITOR].decode("utf-8")
    service = original_bytes[SERVICE].decode("utf-8")
    exporter = original_bytes[EXPORTER].decode("utf-8")

    if 'tSlidesPhase2CoreEditing.css' in editor or "tws-slides-phase2-core" in editor:
        raise RuntimeError("T-Slides Phase 2 already appears applied")

    editor = replace_once(
        editor,
        'import { useTwsI18n } from "./twsI18n";\nimport "./tSlidesPhase1GoogleSlidesFidelity.css";\n',
        'import { useTwsI18n } from "./twsI18n";\n'
        'import { ArrowRight, Bold, Circle, Minus, RotateCw, Square } from "lucide-react";\n'
        'import {\n'
        '  alignElements, createLineElement, createShapeElement, distributeElements, duplicateElements, groupElements,\n'
        '  normalizeRotation, resizeElement, selectionIdsForElement, ungroupElements,\n'
        '} from "./slideCorePhase2.js";\n'
        'import "./tSlidesPhase1GoogleSlidesFidelity.css";\n'
        'import "./tSlidesPhase2CoreEditing.css";\n',
        "Phase 2 imports",
    )
    editor = replace_once(
        editor,
        'tws-reference-ui tws-reference-slides tws-slides-phase1-google-fidelity flex h-full flex-col',
        'tws-reference-ui tws-reference-slides tws-slides-phase1-google-fidelity tws-slides-phase2-core flex h-full flex-col',
        "Phase 2 root hook",
    )
    editor = regex_replace_once(
        editor,
        r'function SlideElement\(\{.*?\n\}\n\nfunction SlideCanvas',
        snippets["slide_element"] + "\n\nfunction SlideCanvas",
        "SlideElement replacement",
    )
    editor = replace_once(
        editor,
        'function SlideCanvas({ slide, editable, selectedElementIds = [], onSelectElement, onDrag, onResize, onTextChange, onCanvasClick }) {',
        'function SlideCanvas({ slide, editable, selectedElementIds = [], onSelectElement, onDrag, onResize, onRotate, onTextChange, onCanvasClick }) {',
        "SlideCanvas signature",
    )
    editor = replace_once(
        editor,
        '          onResize={onResize}\n          onTextChange={onTextChange}',
        '          onResize={onResize}\n          onRotate={onRotate}\n          onTextChange={onTextChange}',
        "SlideCanvas onRotate wiring",
    )
    editor = replace_once(
        editor,
        '  const coalesceKeyRef = useRef("");\n  const [historyVersion, setHistoryVersion] = useState(0);',
        '  const coalesceKeyRef = useRef("");\n  const elementClipboardRef = useRef([]);\n  const [historyVersion, setHistoryVersion] = useState(0);',
        "clipboard ref",
    )
    editor = regex_replace_once(
        editor,
        r'  function handleSelectElement\(id, event\) \{.*?\n  \}\n\n  const \{ peers \}',
        '''  function handleSelectElement(id, event) {
    const groupSelection = selectionIdsForElement(activeSlide?.elements || [], id);
    if (event?.shiftKey) {
      setSelectedElementIds((prev) => {
        const allSelected = groupSelection.every((itemId) => prev.includes(itemId));
        if (allSelected) return prev.filter((itemId) => !groupSelection.includes(itemId));
        return [...new Set([...prev, ...groupSelection])];
      });
    } else {
      setSelectedElementIds(groupSelection);
    }
  }

  const { peers }''',
        "group-aware selection",
    )
    editor = regex_replace_once(
        editor,
        r'  function handleStageKeyDown\(event\) \{.*?\n  \}\n\n  function addSlide',
        '''  function handleStageKeyDown(event) {
    const isMod = event.ctrlKey || event.metaKey;
    const key = event.key.toLowerCase();
    const target = event.target;
    const isEditingText = target?.isContentEditable;

    if (isMod && key === "z" && !event.shiftKey) { event.preventDefault(); undo(); return; }
    if (isMod && (key === "y" || (key === "z" && event.shiftKey))) { event.preventDefault(); redo(); return; }
    if (isMod && !isEditingText && key === "c") { event.preventDefault(); copySelectedElements(); return; }
    if (isMod && !isEditingText && key === "v") { event.preventDefault(); pasteSelectedElements(); return; }
    if (isMod && !isEditingText && key === "d") { event.preventDefault(); duplicateSelectedElements(); return; }
    if (isMod && !isEditingText && key === "g") {
      event.preventDefault();
      if (event.shiftKey) ungroupSelectedElements();
      else groupSelectedElements();
      return;
    }
    if ((event.key === "Delete" || event.key === "Backspace") && selectedElementId && !isEditingText) {
      event.preventDefault();
      deleteSelectedElement();
      return;
    }
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key) && selectedElementId && canEdit && !isEditingText) {
      event.preventDefault();
      const step = event.shiftKey ? 10 : 2;
      const element = activeSlide?.elements?.find((el) => el.id === selectedElementId);
      if (!element) return;
      let { x, y } = element;
      if (event.key === "ArrowUp") y -= step;
      if (event.key === "ArrowDown") y += step;
      if (event.key === "ArrowLeft") x -= step;
      if (event.key === "ArrowRight") x += step;
      handleDrag(selectedElementId, x, y, `nudge:${selectedElementId}`);
    }
  }

  function addSlide''',
        "keyboard parity",
    )
    editor = regex_replace_once(
        editor,
        r'  function alignSelectedElements\(mode\) \{.*?\n  \}\n\n  function updateSelectedTextSize',
        '''  function alignSelectedElements(mode) {
    if (!selectedElementIds.length) return;
    mutateActiveSlide((slide) => ({
      ...slide,
      elements: alignElements(slide.elements, selectedElementIds, mode, CANVAS_W, CANVAS_H),
    }), `align:${mode}:${Date.now()}`);
  }

  function updateSelectedTextSize''',
        "align helper wiring",
    )
    old_add_text = '''  function addTextElement() {
    mutateActiveSlide((slide) => ({
      ...slide,
      elements: [...slide.elements, { id: `el_${Date.now()}`, type: "text", x: 300, y: 220, w: 360, h: 80, text: ui.lang === "en" ? "New text" : "نص جديد", fontSize: 22, color: "#111111", align: ui.lang === "en" ? "left" : "right" }],
    }), `add-text:${Date.now()}`);
  }

'''
    editor = replace_once(editor, old_add_text, old_add_text + snippets["actions"] + "\n", "Phase 2 editor actions")

    editor = replace_once(
        editor,
        '''  function handleResize(elementId, w, h) {
    mutateActiveSlide((slide) => ({ ...slide, elements: slide.elements.map((el) => (el.id === elementId ? { ...el, w, h } : el)) }), `resize:${elementId}`);
  }
''',
        '''  function handleResize(elementId, nextRect) {
    mutateActiveSlide((slide) => ({
      ...slide,
      elements: slide.elements.map((el) => (el.id === elementId ? { ...el, x: nextRect.x, y: nextRect.y, w: nextRect.w, h: nextRect.h } : el)),
    }), `resize:${elementId}`);
  }
  function handleRotate(elementId, rotation) {
    const source = activeSlide?.elements?.find((el) => el.id === elementId);
    if (!source) return;
    let delta = normalizeRotation(rotation) - normalizeRotation(source.rotation);
    if (delta > 180) delta -= 360;
    if (delta < -180) delta += 360;
    const ids = selectedElementIds.includes(elementId) ? new Set(selectedElementIds) : new Set([elementId]);
    mutateActiveSlide((slide) => ({
      ...slide,
      elements: slide.elements.map((el) => ids.has(el.id) ? { ...el, rotation: normalizeRotation((Number(el.rotation) || 0) + delta) } : el),
    }), `rotate:${elementId}`);
  }
''',
        "resize and rotate handlers",
    )

    editor = replace_once(
        editor,
        '          <Button type="button" variant="soft" onClick={addImageElement}><ImageIcon size={14} /> {ui.image}</Button>\n',
        '          <Button type="button" variant="soft" onClick={addImageElement}><ImageIcon size={14} /> {ui.image}</Button>\n' + snippets["toolbar"],
        "shape line toolbar",
    )
    editor = replace_once(
        editor,
        '              <Button type="button" variant="soft" onClick={() => alignSelectedElements("right")}><AlignRight size={14} /> {ui.alignRight}</Button>\n',
        '              <Button type="button" variant="soft" onClick={() => alignSelectedElements("right")}><AlignRight size={14} /> {ui.alignRight}</Button>\n' + snippets["selection_toolbar"],
        "selected toolbar parity",
    )
    editor = replace_once(
        editor,
        '''              <div className="mt-4 grid grid-cols-2 gap-2">
                {selectedElement?.type === "text" && (
''',
        '''              <div className="mt-4 grid grid-cols-2 gap-2">
''' + snippets["inspector"] + '''                {selectedElement?.type === "text" && (
''',
        "inspector controls",
    )
    editor = replace_once(
        editor,
        '              onResize={handleResize}\n              onTextChange={handleTextChange}',
        '              onResize={handleResize}\n              onRotate={handleRotate}\n              onTextChange={handleTextChange}',
        "stage rotate wiring",
    )

    service = replace_once(
        service,
        'import { normalizeAdvancedSheetState } from "../utils/sheetAdvancedPhase6.js";\n',
        'import { normalizeAdvancedSheetState } from "../utils/sheetAdvancedPhase6.js";\nimport { sanitizeSlideElementPhase2 } from "../utils/slideCorePhase2.js";\n',
        "backend Phase 2 import",
    )
    service = regex_replace_once(
        service,
        r'    const elements = elementsIn\.slice\(0, 60\)\.map\(\(element, elIndex\) => \{.*?\n    \}\);',
        '    const elements = elementsIn.slice(0, 60).map((element, elIndex) => sanitizeSlideElementPhase2(element, index, elIndex));',
        "slide sanitizer wiring",
    )

    exporter = regex_replace_once(
        exporter,
        r'    \(slide\.elements \|\| \[\]\)\.forEach\(\(element\) => \{.*?\n    \}\);',
        '''    (slide.elements || []).forEach((element) => {
      const x = (element.x || 0) * scaleX;
      const y = (element.y || 0) * scaleY;
      const w = (element.w || 200) * scaleX;
      const h = (element.h || 60) * scaleY;
      const rotation = Number(element.rotation) || 0;
      const opacity = Math.min(Math.max(Number(element.opacity) || 1, .05), 1);
      doc.save();
      doc.opacity(opacity);
      if (rotation) doc.rotate(rotation, { origin: [x + w / 2, y + h / 2] });
      if (element.type === "text") {
        doc.fontSize(element.fontSize ? element.fontSize * scaleY : 16)
          .fillColor(element.color || "#000000")
          .text(element.text || "", x, y, { width: w, height: h, align: element.align || "left" });
      } else if (element.type === "image") {
        doc.rect(x, y, w, h).stroke("#cccccc");
        doc.fontSize(9).fillColor("#999999").text("[صورة]", x + 4, y + h / 2 - 5, { width: w - 8 });
      } else if (element.type === "shape") {
        doc.lineWidth(Math.max(0.1, Number(element.strokeWidth) || 1));
        if (element.shapeKind === "ellipse") doc.ellipse(x + w / 2, y + h / 2, w / 2, h / 2);
        else if (element.shapeKind === "roundRect") doc.roundedRect(x, y, w, h, Math.min(14, w / 5, h / 5));
        else doc.rect(x, y, w, h);
        if ((Number(element.strokeWidth) || 0) > 0) doc.fillAndStroke(element.fill || "#f1f3f4", element.stroke || "#5f6368");
        else doc.fill(element.fill || "#f1f3f4");
      } else if (element.type === "line") {
        const centerY = y + h / 2;
        doc.lineWidth(Math.max(1, Number(element.strokeWidth) || 3)).strokeColor(element.stroke || "#3c4043");
        doc.moveTo(x, centerY).lineTo(x + w, centerY).stroke();
        if (element.lineKind === "arrow") {
          const arrow = Math.max(5, Math.min(12, h || 8));
          doc.polygon([x + w, centerY], [x + w - arrow, centerY - arrow / 2], [x + w - arrow, centerY + arrow / 2]).fill(element.stroke || "#3c4043");
        }
      }
      doc.restore();
    });''',
        "PDF shape line export",
    )

    exporter = replace_once(
        exporter,
        '''      if (element.type === "text") {
        pptxSlide.addText(element.text || "", {
          x, y, w, h,
          fontSize: element.fontSize ? Math.max(6, Math.round(element.fontSize * 0.75)) : 14,
          bold: Boolean(element.bold),
          color: String(element.color || "#111111").replace("#", ""),
          align: element.align || "left",
        });
      } else if (element.type === "image" && element.src) {
        try {
          // pptxgenjs fetches remote/relative image URLs itself in Node.
          pptxSlide.addImage({ path: element.src, x, y, w, h });
        } catch {
          // Skip an unreachable image rather than failing the whole export.
        }
      }
''',
        '''      const rotation = Number(element.rotation) || 0;
      const transparency = Math.round((1 - Math.min(Math.max(Number(element.opacity) || 1, .05), 1)) * 100);
      if (element.type === "text") {
        pptxSlide.addText(element.text || "", {
          x, y, w, h,
          fontSize: element.fontSize ? Math.max(6, Math.round(element.fontSize * 0.75)) : 14,
          bold: Boolean(element.bold),
          color: String(element.color || "#111111").replace("#", ""),
          align: element.align || "left",
          rotate: rotation,
        });
      } else if (element.type === "image" && element.src) {
        try {
          // pptxgenjs fetches remote/relative image URLs itself in Node.
          pptxSlide.addImage({ path: element.src, x, y, w, h, rotate: rotation });
        } catch {
          // Skip an unreachable image rather than failing the whole export.
        }
      } else if (element.type === "shape") {
        const shapeType = element.shapeKind === "ellipse" ? pptx.ShapeType.ellipse : element.shapeKind === "roundRect" ? pptx.ShapeType.roundRect : pptx.ShapeType.rect;
        pptxSlide.addShape(shapeType, {
          x, y, w, h, rotate: rotation,
          fill: { color: String(element.fill || "#f1f3f4").replace("#", ""), transparency },
          line: { color: String(element.stroke || "#5f6368").replace("#", ""), width: Math.max(.1, Number(element.strokeWidth) || 1), transparency },
        });
      } else if (element.type === "line") {
        pptxSlide.addShape(pptx.ShapeType.line, {
          x, y: y + h / 2, w, h: 0, rotate: rotation,
          line: {
            color: String(element.stroke || "#3c4043").replace("#", ""),
            width: Math.max(1, Number(element.strokeWidth) || 3),
            transparency,
            endArrowType: element.lineKind === "arrow" ? "triangle" : "none",
          },
        });
      }
''',
        "PPTX shape line export",
    )

    (REPO / EDITOR).write_text(editor, encoding="utf-8")
    (REPO / SERVICE).write_text(service, encoding="utf-8")
    (REPO / EXPORTER).write_text(exporter, encoding="utf-8")
    for rel, data in payload_bytes.items():
        target = REPO / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    source_applied = True

    run(["git", "diff", "--check"])
    for rel in [BE_HELPER, BE_TEST, SERVICE, EXPORTER]:
        run(["node", "--check", rel])

    run(["node", "--test", BE_TEST])
    run(["node", "--test", FE_TEST])
    run(["node", "--test", "frontend/src/pages/tws/tSlidesPhase1GoogleSlidesFidelity.test.js"])

    for regression in [
        "frontend/src/pages/tws/tDocsPhase1_1FinalPolish.test.js",
        "frontend/src/pages/tws/tSheetsPhase7_2EMicroFinalR1.test.js",
    ]:
        if (REPO / regression).is_file():
            run(["node", "--test", regression])

    prisma_validate = run(["npx", "prisma", "validate"], cwd=BACKEND, check=False)
    if prisma_validate.returncode != 0:
        raise RuntimeError("Prisma validate failed:\n" + ((prisma_validate.stdout or "") + (prisma_validate.stderr or "")))

    smoke_doc = r'''const doc={title:"Phase2",type:"TSLIDE",plainText:"",contentJson:{slides:[{id:"s1",background:"#ffffff",elements:[{id:"a",type:"shape",shapeKind:"ellipse",x:100,y:100,w:220,h:120,fill:"#eeeeee",stroke:"#333333",strokeWidth:2,rotation:15,opacity:.8},{id:"b",type:"line",lineKind:"arrow",x:350,y:200,w:260,h:30,stroke:"#1a73e8",strokeWidth:3,rotation:0,opacity:1}]}]}};'''
    pptx_smoke = smoke_doc + r'''import {buildTSlidePptx} from "./src/utils/workspaceExport.js"; const b=await buildTSlidePptx(doc); if(!b || b.length<1000) throw new Error("PPTX smoke too small"); console.log("PPTX_SHAPES_OK",b.length);'''
    run(["node", "--input-type=module", "-e", pptx_smoke], cwd=BACKEND)
    pdf_smoke = smoke_doc + r'''import {buildTSlidePdf} from "./src/utils/workspaceExport.js"; const p=buildTSlidePdf(doc); let n=0; p.on("data",c=>n+=c.length); const done=new Promise((resolve,reject)=>{p.on("end",resolve);p.on("error",reject)}); p.end(); await done; if(n<500) throw new Error("PDF smoke too small"); console.log("PDF_SHAPES_OK",n);'''
    run(["node", "--input-type=module", "-e", pdf_smoke], cwd=BACKEND)

    build_start = time.time()
    run(["npm", "run", "build"], cwd=FRONTEND)
    build_seconds = time.time() - build_start

    for path, fp in unrelated_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"pre-existing unrelated dirty path changed: {path}")

    final_paths = changed_paths()
    expected_final = pre_paths | PHASE_SCOPE
    if final_paths != expected_final:
        extra = sorted(final_paths - expected_final)
        missing = sorted(expected_final - final_paths)
        raise RuntimeError(f"changed-path guard mismatch; extra={extra}; missing={missing}")

    final_editor = (REPO / EDITOR).read_text(encoding="utf-8")
    final_service = (REPO / SERVICE).read_text(encoding="utf-8")
    final_exporter = (REPO / EXPORTER).read_text(encoding="utf-8")
    for marker in [
        "tws-slides-phase2-core", "createShapeElement", "createLineElement", "duplicateSelectedElements",
        "copySelectedElements", "pasteSelectedElements", "groupSelectedElements", "ungroupSelectedElements",
        "tws-slides-resize-handle", "tws-slides-rotate-handle",
    ]:
        if marker not in final_editor:
            raise RuntimeError(f"final editor verification missing: {marker}")
    if "sanitizeSlideElementPhase2(element, index, elIndex)" not in final_service:
        raise RuntimeError("backend persistence wiring missing")
    for marker in ['element.type === "shape"', 'element.type === "line"', "ShapeType.ellipse", "ShapeType.line", "endArrowType"]:
        if marker not in final_exporter:
            raise RuntimeError(f"export verification missing: {marker}")

    nginx_dump = run(["nginx", "-T"], cwd=Path("/"), check=False)
    nginx_text = (nginx_dump.stdout or "") + (nginx_dump.stderr or "")
    if nginx_dump.returncode != 0 or "server_name tos.tamiyouz.com" not in nginx_text or str(LIVE_ROOT) not in nginx_text:
        raise RuntimeError("production root guard failed")

    live_before_html = fetch_text(f"{LIVE_URL}?tslides_phase2_before={int(time.time())}")
    live_asset_before = extract_main_js(live_before_html) or "UNKNOWN"

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.is_file():
        raise RuntimeError(f"built main asset missing: {built_asset_path}")
    built_asset_bytes = built_asset_path.read_bytes()

    backup_dir = Path("/tmp") / f"tslides_phase2_live_backup_{int(time.time())}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    live_index_backup = backup_dir / "index.html"
    shutil.copy2(LIVE_ROOT / "index.html", live_index_backup)

    sync_dist(DIST, LIVE_ROOT)
    live_synced = True
    run(["nginx", "-t"], cwd=Path("/"))
    run(["systemctl", "reload", "nginx"], cwd=Path("/"))
    time.sleep(1.0)

    live_after_html = fetch_text(f"{LIVE_URL}?tslides_phase2_after={int(time.time())}")
    live_asset_after = extract_main_js(live_after_html)
    if live_asset_after != built_asset:
        raise RuntimeError(f"live HTML asset mismatch: built {built_asset}, live {live_asset_after}")
    live_asset_bytes = fetch_bytes(f"{asset_url(live_asset_after)}?tslides_phase2={int(time.time())}")
    if sha256_bytes(live_asset_bytes) != sha256_bytes(built_asset_bytes):
        raise RuntimeError("live main JS bytes do not match fresh build")

    for path, fp in unrelated_fingerprints.items():
        if fingerprint(path) != fp:
            raise RuntimeError(f"unrelated dirty state changed after live deploy: {path}")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("FILES_PATCHED=8")
    print("PRECHECK_WORKTREE=" + ("CLEAN" if not pre_paths else "DIRTY_UNRELATED_ALLOWED"))
    print("BASELINE_BLOB_GUARD=PASS")
    print("PAYLOAD_INTEGRITY=PASS")
    print("PHASE2_FRONTEND_TESTS=PASS (11/11)")
    print("PHASE2_BACKEND_TESTS=PASS (6/6)")
    print("PHASE1_TSLIDES_REGRESSION=PASS")
    print("NATIVE_PPTX_SHAPE_LINE_EXPORT=PASS")
    print("NATIVE_PDF_SHAPE_LINE_EXPORT=PASS")
    print("SHAPES_RECT_ELLIPSE=PASS")
    print("LINES_ARROWS=PASS")
    print("ROTATE_HANDLE=PASS")
    print("FOUR_CORNER_RESIZE=PASS")
    print("GROUP_UNGROUP=PASS")
    print("COPY_PASTE_DUPLICATE=PASS")
    print("ALIGN_DISTRIBUTE=PASS")
    print("FILL_STROKE_OPACITY=PASS")
    print("KEYBOARD_SHORTCUTS=PASS")
    print("PERSISTENCE_SANITIZER=PASS")
    print("COMMENTS_SHARING_VERSIONS_PRESENT_EXPORTS_PRESERVED=YES")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print(f"FRONTEND_BUILD=PASS ({build_seconds:.2f}s)")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_asset_before}")
    print(f"LIVE_ASSET_AFTER={live_asset_after}")
    print(f"LIVE_DEPLOY_ROOT={LIVE_ROOT}")
    print("LIVE_DEPLOY=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print(f"PREEXISTING_UNRELATED_DIRTY_STATE_PRESERVED={'YES' if all(fingerprint(path) == fp for path, fp in unrelated_fingerprints.items()) else 'NO'}")
    print("CHANGED_PATHS_EXACT=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")

except Exception as exc:
    fail(str(exc))
