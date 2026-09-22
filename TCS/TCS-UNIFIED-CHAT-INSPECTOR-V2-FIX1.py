#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-UNIFIED-CHAT-INSPECTOR-V2-FIX1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsUnifiedInspectorV2Fix1.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# Safe additive CSS import only.
css_import = 'import "./tcsUnifiedInspectorV2Fix1.css";'
if css_import not in src:
    anchor = 'import "./tcsReferenceLockV1.css";'
    if anchor not in src:
        raise SystemExit(f"{PATCH}: base TCS CSS import not found")
    src = src.replace(anchor, anchor + "\n" + css_import, 1)

# Root hook only; no JSX block replacement/truncation.
if "tcs-unified-inspector-v2-fix1" not in src:
    root_anchor = 'className={`tos-chat-modern-shell '
    if root_anchor not in src:
        raise SystemExit(f"{PATCH}: root class anchor not found")
    src = src.replace(root_anchor, 'className={`tos-chat-modern-shell tcs-unified-inspector-v2-fix1 ', 1)

# Preserve mutual exclusivity with tiny event-handler edits only.
old_tools = 'onClick={() => setToolbarOpen((value) => !value)}'
new_tools = 'onClick={() => setToolbarOpen((value) => { const next = !value; if (next) setDetailsPanelOpen(false); return next; })}'
if old_tools in src:
    src = src.replace(old_tools, new_tools, 1)

old_details = 'onClick={() => setDetailsPanelOpen((value) => !value)} disabled={focusMode}'
new_details = 'onClick={() => { setToolbarOpen(false); setDetailsPanelOpen((value) => !value); }} disabled={focusMode}'
if old_details in src:
    src = src.replace(old_details, new_details, 1)

# Files/tasks direct buttons: close popover before opening inspector.
src = src.replace(
    'onClick={() => { setDetailsPanelOpen(true); setDetailsTab("files"); }}',
    'onClick={() => { setToolbarOpen(false); setDetailsPanelOpen(true); setDetailsTab("files"); }}'
)
src = src.replace(
    'onClick={() => { setDetailsPanelOpen(true); setDetailsTab("tasks"); }}',
    'onClick={() => { setToolbarOpen(false); setDetailsPanelOpen(true); setDetailsTab("tasks"); }}'
)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-unified-chat-inspector-v2-fix1: 1; }

/* SAFE V2 FIX1
   CSS-first, no large JSX replacement.
   Desktop: nav | conversations | chat | unified inspector.
   Chat tools: small anchored popover.
*/

@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1:not(.tos-chat-focus-mode) {
    grid-template-columns: 58px 236px minmax(0, 1fr) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 58px 220px minmax(300px, 1fr) 292px !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel:not(.hidden) {
    position: static !important;
    inset: auto !important;
    z-index: 1 !important;
    grid-column: 4 !important;
    display: block !important;
    min-width: 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
    padding: 0 !important;
    border: 0 !important;
    border-inline-start: 1px solid #ece8df !important;
    background: #fbfaf7 !important;
    backdrop-filter: none !important;
    box-shadow: none !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel:not(.hidden) > div {
    position: static !important;
    width: 100% !important;
    max-width: none !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 10px !important;
    gap: 8px !important;
    overflow-y: auto !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: #fbfaf7 !important;
    box-shadow: none !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-detail-card {
    border: 1px solid #ece8df !important;
    border-radius: 14px !important;
    background: #fff !important;
    box-shadow: none !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-detail-card:first-child {
    position: sticky !important;
    top: 0 !important;
    z-index: 3 !important;
  }
}

/* Existing Chat tools DOM becomes a professional compact popover. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu {
  left: auto !important;
  right: 0 !important;
  width: 276px !important;
  max-height: min(520px, calc(100vh - 180px)) !important;
  overflow-y: auto !important;
  padding: 10px !important;
  border: 1px solid #e8e2d6 !important;
  border-radius: 16px !important;
  background: rgba(255,253,248,.99) !important;
  box-shadow: 0 16px 38px rgba(34,27,17,.14) !important;
  text-align: start !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1[dir="rtl"] .tcs-v16-tools-menu {
  right: auto !important;
  left: 0 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu .mb-3 {
  margin-bottom: 8px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu .text-sm {
  font-size: 12px !important;
  line-height: 1.2 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu .mt-1.text-\[11px\] {
  display: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions {
  margin-top: 8px !important;
  padding-top: 8px !important;
  gap: 6px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions button,
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu > .grid button {
  min-height: 34px !important;
  padding: 7px 8px !important;
  border: 1px solid #ece7de !important;
  border-radius: 10px !important;
  background: #fff !important;
  color: #4a443c !important;
  font-size: 9.5px !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions button:hover,
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu > .grid button:hover {
  border-color: #dec98f !important;
  background: #fffaf0 !important;
  color: #8c620e !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-status-segment {
  gap: 4px !important;
  margin-bottom: 6px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-status-segment button {
  min-height: 30px !important;
  padding: 5px 4px !important;
  border-radius: 9px !important;
  font-size: 8.5px !important;
}

/* Main chat remains the visual hero. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-workspace {
  min-width: 0 !important;
  background: #fff !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail {
  background: #fff !important;
  border-inline-end: 1px solid #ece8df !important;
}

/* Narrow window fallback remains a right sheet. */
@media (max-width: 1023px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel:not(.hidden) {
    position: absolute !important;
    inset: 0 !important;
    z-index: 40 !important;
    display: block !important;
    padding: 8px !important;
    background: rgba(24,22,19,.14) !important;
    backdrop-filter: blur(3px) !important;
  }
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel:not(.hidden) > div {
    position: static !important;
    width: min(340px,94%) !important;
    height: 100% !important;
    margin-left: auto !important;
    margin-right: 0 !important;
    border-radius: 16px !important;
    background: #fbfaf7 !important;
  }
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=SAFE_CSS_FIRST")
print("INSPECTOR=RIGHT_STATIC_COLUMN")
print("TOOLS=COMPACT_EXISTING_POPOVER")
print("TOOLS_DETAILS_EXCLUSIVE=YES")
print("LARGE_JSX_REPLACEMENT=NO")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
