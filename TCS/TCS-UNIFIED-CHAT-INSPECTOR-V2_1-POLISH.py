#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-UNIFIED-CHAT-INSPECTOR-V2_1-POLISH"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsUnifiedInspectorV2_1Polish.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

css_import = 'import "./tcsUnifiedInspectorV2_1Polish.css";'
if css_import not in src:
    anchors = [
        'import "./tcsUnifiedInspectorV2Fix1.css";',
        'import "./tcsReferenceLockV1.css";',
    ]
    for anchor in anchors:
        if anchor in src:
            src = src.replace(anchor, anchor + "\n" + css_import, 1)
            break
    else:
        raise SystemExit(f"{PATCH}: no valid CSS import anchor found")

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-unified-chat-inspector-v2-1-polish: 1; }

/* TCS Unified Chat Inspector V2.1
   Visual polish only.
   Keeps current DOM and all existing behavior intact. */

@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 58px 220px minmax(340px, 1fr) 310px !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel:not(.hidden) {
    background: #f8f7f4 !important;
    border-inline-start: 1px solid #e9e5dc !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel:not(.hidden) > div {
    padding: 0 !important;
    gap: 0 !important;
    background: #f8f7f4 !important;
  }

  /* The inspector header reads like a real side panel, not another card. */
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:first-child {
    position: static !important;
    top: auto !important;
    z-index: auto !important;
    margin: 0 !important;
    padding: 15px 14px 12px !important;
    border: 0 !important;
    border-bottom: 1px solid #e9e5dc !important;
    border-radius: 0 !important;
    background: #fff !important;
    box-shadow: none !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:not(:first-child) {
    margin: 10px 10px 0 !important;
    border: 1px solid #ebe7de !important;
    border-radius: 13px !important;
    background: #fff !important;
    box-shadow: 0 1px 2px rgba(35,30,22,.03) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:last-child {
    margin-bottom: 10px !important;
  }

  /* Tabs: restrained segmented control. */
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:first-child .mt-2\.5.grid.grid-cols-3 {
    gap: 3px !important;
    padding: 3px !important;
    border: 1px solid #ece8df !important;
    border-radius: 10px !important;
    background: #f7f6f3 !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:first-child .mt-2\.5.grid.grid-cols-3 button {
    min-height: 29px !important;
    border-radius: 8px !important;
    font-size: 9px !important;
    box-shadow: none !important;
  }

  /* Health / files / unread become quiet information chips. */
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:first-child .grid.grid-cols-3.text-center {
    gap: 5px !important;
    margin-top: 9px !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:first-child .grid.grid-cols-3.text-center > span {
    padding: 7px 5px !important;
    border: 1px solid #eeeae2 !important;
    border-radius: 9px !important;
    background: #faf9f7 !important;
    color: #6d675f !important;
    line-height: 1.35 !important;
  }
}

/* Chat tools = compact command menu, not a mini dashboard. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu {
  width: 258px !important;
  padding: 9px !important;
  border: 1px solid #e7e2d8 !important;
  border-radius: 14px !important;
  background: rgba(255,255,255,.995) !important;
  box-shadow: 0 14px 34px rgba(31,26,18,.13) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu .mb-3 {
  margin: 0 0 7px !important;
  padding: 0 1px 7px !important;
  border-bottom: 1px solid #efebe4 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu .text-sm {
  font-size: 11px !important;
  font-weight: 900 !important;
  letter-spacing: -.01em !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions {
  grid-template-columns: repeat(2, minmax(0,1fr)) !important;
  gap: 5px !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
  border-top: 0 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions button {
  min-height: 34px !important;
  padding: 7px 7px !important;
  border: 1px solid #ebe7df !important;
  border-radius: 9px !important;
  background: #faf9f7 !important;
  color: #4f4941 !important;
  font-size: 9px !important;
  font-weight: 800 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions button:hover {
  border-color: #d8bc73 !important;
  background: #fffaf0 !important;
  color: #8c620e !important;
}

/* Status = one compact segmented row with a single gold active state. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-status-segment {
  gap: 3px !important;
  margin: 7px 0 !important;
  padding: 3px !important;
  border: 1px solid #ece8df !important;
  border-radius: 10px !important;
  background: #f7f6f3 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-status-segment button {
  min-height: 29px !important;
  padding: 5px 3px !important;
  border: 0 !important;
  border-radius: 8px !important;
  background: transparent !important;
  color: #777168 !important;
  font-size: 8px !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-status-segment button[class*="bg-amber-400"] {
  background: #c89224 !important;
  color: #fff !important;
}

/* Secondary commands stay quiet; Call gets one full-width row. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu > .grid.grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0,1fr)) !important;
  gap: 5px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu > .grid.grid-cols-2 > button {
  min-height: 33px !important;
  padding: 7px !important;
  border: 1px solid #ebe7df !important;
  border-radius: 9px !important;
  background: #fff !important;
  color: #544e46 !important;
  font-size: 8.7px !important;
  font-weight: 800 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu > .grid.grid-cols-2 > button:last-child {
  grid-column: 1 / -1 !important;
}

/* Remove the heavy black-button feeling inherited from previous visual layers. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu button[class*="bg-zinc-950"] {
  background: #fff !important;
  color: #514b43 !important;
  border-color: #ebe7df !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu button[class*="bg-zinc-950"]:hover {
  background: #fffaf0 !important;
  color: #8c620e !important;
  border-color: #d8bc73 !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=CSS_ONLY_POLISH")
print("TOOLS=PRO_COMMAND_MENU")
print("INSPECTOR=FLAT_SIDE_PANEL")
print("STICKY_OVERLAP=REMOVED")
print("HEAVY_BLACK_BUTTONS=REMOVED")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
