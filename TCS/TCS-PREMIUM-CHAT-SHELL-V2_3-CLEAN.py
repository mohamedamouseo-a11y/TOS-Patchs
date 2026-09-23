#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-PREMIUM-CHAT-SHELL-V2_3-CLEAN"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsPremiumChatShellV2_3Clean.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

css_import = 'import "./tcsPremiumChatShellV2_3Clean.css";'
if css_import not in src:
    anchors = [
        'import "./tcsPremiumChatShellV2_2.css";',
        'import "./tcsUnifiedInspectorV2_1Polish.css";',
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
:root { --tcs-premium-chat-shell-v2-3-clean: 1; }

/* V2.3 CLEAN
   Fixes the V2.2 conversation-list regression and removes dashboard-like clutter.
   CSS-only; no behavior/API/backend changes.
*/

@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1:not(.tos-chat-focus-mode) {
    grid-template-columns: 56px 286px minmax(0, 1fr) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 56px 270px minmax(360px, 1fr) 320px !important;
  }
}

/* ---------- Conversation rail: clean, readable, no fake avatars ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .space-y-1 > button {
  min-height: 44px !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 8px 10px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  gap: 8px !important;
  overflow: hidden !important;
  border: 1px solid transparent !important;
  border-radius: 10px !important;
  background: transparent !important;
  color: #37332f !important;
  text-align: start !important;
  box-shadow: none !important;
}

/* Remove the synthetic avatar introduced by V2.2; it clips real names. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .space-y-1 > button::before {
  content: none !important;
  display: none !important;
}

/* Override LTR/RTL padding from V2.2. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1[dir="ltr"] .tos-chat-v8-rail .space-y-1 > button,
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1[dir="rtl"] .tos-chat-v8-rail .space-y-1 > button {
  padding-inline: 10px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .space-y-1 > button:hover {
  border-color: #ece8e0 !important;
  background: #faf9f7 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .space-y-1 > button[class*="bg-white"] {
  border-color: #ead6a5 !important;
  background: #fffaf0 !important;
  box-shadow: inset 3px 0 0 #c99122 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1[dir="rtl"] .tos-chat-v8-rail .space-y-1 > button[class*="bg-white"] {
  box-shadow: inset -3px 0 0 #c99122 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-ref-conversation-title {
  display: block !important;
  flex: 1 1 auto !important;
  min-width: 0 !important;
  max-width: none !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  line-height: 1.35 !important;
  color: inherit !important;
}

/* Search/filter block tighter and less card-like. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail > .min-h-0.flex-1 {
  padding: 8px 10px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .rounded-2xl.border {
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-new-conversation-trigger {
  min-height: 36px !important;
  margin-block: 8px !important;
  border-radius: 9px !important;
  background: #fff !important;
  border-color: #e5d3a7 !important;
}

/* ---------- Main header: remove duplicate Search action ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-command-center .relative.hidden.items-center > button:first-child {
  display: none !important;
}

/* Focus + Tools should be small utilities, not big CTAs. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-command-center .relative.hidden.items-center > button {
  min-height: 34px !important;
  padding: 7px 11px !important;
  border-radius: 9px !important;
  font-size: 10px !important;
}

/* ---------- Smart search: primary search surface ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-inline-search-shell {
  min-height: 44px !important;
  border-radius: 10px !important;
  border: 1px solid #e8e4dc !important;
  background: #fff !important;
}

/* ---------- Empty state: smaller, cleaner, less decorative ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-empty-clean-card {
  max-width: 380px !important;
  padding: 26px 24px !important;
  border-radius: 18px !important;
  border-color: #eadab3 !important;
  background:
    radial-gradient(circle at 0 0, rgba(222,181,80,.13), transparent 30%),
    linear-gradient(150deg, #fffefa, #fffaf0) !important;
  box-shadow: 0 12px 30px rgba(55,43,18,.07) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-empty-clean-card h3 {
  font-size: 14px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-empty-clean-card p {
  font-size: 10.5px !important;
  line-height: 1.55 !important;
}

/* Quick templates in empty state should be light chips, not heavy pills. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-empty-clean-card button {
  border-color: #e8dcc1 !important;
  background: rgba(255,255,255,.78) !important;
  color: #5e574d !important;
  box-shadow: none !important;
}

/* ---------- Tools popover: single compact utility surface ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu {
  width: 228px !important;
  max-height: 430px !important;
  padding: 8px !important;
  border-radius: 12px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions {
  grid-template-columns: repeat(2, minmax(0,1fr)) !important;
  gap: 4px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions button {
  min-height: 30px !important;
  font-size: 8px !important;
}

/* ---------- Inspector: keep it visually quieter than the chat ---------- */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel:not(.hidden) {
    background: #faf9f7 !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:not(:first-child) {
    margin: 8px 8px 0 !important;
    border-radius: 11px !important;
    border-color: #ece8e0 !important;
  }
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=CSS_ONLY")
print("CONVERSATION_NAMES=VISIBLE")
print("FAKE_AVATARS=REMOVED")
print("DUPLICATE_HEADER_SEARCH=HIDDEN")
print("TOOLS=SMALLER")
print("EMPTY_STATE=SMALLER")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
