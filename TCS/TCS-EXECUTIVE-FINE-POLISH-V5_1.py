#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-EXECUTIVE-FINE-POLISH-V5_1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsExecutiveFinePolishV5_1.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

backup = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup / "ChatPanel.jsx")
if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)

chat = CHAT.read_text(encoding="utf-8")

import_anchor = 'import "./tcsExecutivePremiumPolishV5.css";'
import_line = 'import "./tcsExecutiveFinePolishV5_1.css";'
if import_line not in chat:
    if import_anchor not in chat:
        raise SystemExit(f"{PATCH}: V5 import anchor missing")
    chat = chat.replace(import_anchor, import_anchor + "\n" + import_line, 1)

root_anchor = '<div ref={chatShellRef} data-tcs-premium-polish="v5"'
if 'data-tcs-fine-polish="v5.1"' not in chat:
    if root_anchor not in chat:
        raise SystemExit(f"{PATCH}: root marker anchor missing")
    chat = chat.replace(root_anchor, '<div ref={chatShellRef} data-tcs-fine-polish="v5.1" data-tcs-premium-polish="v5"', 1)

class_anchor = "tos-chat-modern-shell tcs-premium-polish-v5"
if "tcs-fine-polish-v51" not in chat:
    if class_anchor not in chat:
        raise SystemExit(f"{PATCH}: root class anchor missing")
    chat = chat.replace(class_anchor, "tos-chat-modern-shell tcs-fine-polish-v51 tcs-premium-polish-v5", 1)

# Safety fix discovered during V5.1 source review: canPin is passed by caller but was not destructured.
sig_old = 'function MessageActions({ message, canInteract, canManageChat, isOwner,'
sig_new = 'function MessageActions({ message, canInteract, canManageChat, canPin = false, isOwner,'
if sig_old in chat:
    chat = chat.replace(sig_old, sig_new, 1)
elif "canPin = false" not in chat[chat.find("function MessageActions("):chat.find("function conversationTitle(")]:
    raise SystemExit(f"{PATCH}: MessageActions canPin signature anchor missing")

css = r''':root {
  --tcs-executive-fine-polish-v5-1: 1;
}

/* V5.1 Fine Polish — messages, actions, composer, inspector, responsive spacing. */

/* Message stream rhythm */
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-message-canvas {
  padding-inline: 18px !important;
  padding-block: 16px 20px !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-row {
  border-radius: 22px !important;
  transition: background .16s ease, box-shadow .16s ease, transform .16s ease !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-row:hover {
  background: rgba(255,255,255,.34);
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-meta {
  margin-bottom: 6px !important;
  color: #8b8173 !important;
  font-size: 11px !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-meta > span:first-child {
  color: #3a2c1b !important;
  font-size: 12px !important;
  letter-spacing: -.01em;
}

/* Message bubbles */
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-bubble {
  max-width: min(100%, 680px) !important;
  border-radius: 18px !important;
  border-color: rgba(145,105,35,.13) !important;
  box-shadow:
    0 7px 18px rgba(55,39,13,.045),
    inset 0 1px 0 rgba(255,255,255,.90) !important;
  line-height: 1.72 !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-row.justify-start .tos-chat-bubble {
  color: #3c3328 !important;
  background:
    linear-gradient(180deg, #ffffff 0%, #fcfaf6 100%) !important;
  border-end-start-radius: 7px !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-row.justify-end .tos-chat-bubble {
  color: #302617 !important;
  border-color: rgba(181,133,35,.19) !important;
  background:
    radial-gradient(circle at 88% -45%, rgba(220,174,75,.12), transparent 45%),
    linear-gradient(145deg, #fffaf0 0%, #f7ead0 100%) !important;
  border-end-end-radius: 7px !important;
  box-shadow:
    0 8px 20px rgba(92,63,11,.065),
    inset 0 1px 0 rgba(255,255,255,.78) !important;
}

/* Reply/thread context cards */
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-row button[class*="border-r-4"] {
  border-color: rgba(187,137,35,.30) !important;
  background: linear-gradient(180deg, #fffefa, #f8f1e4) !important;
  color: #786c5d !important;
  box-shadow: 0 5px 13px rgba(57,40,12,.035) !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-row button[class*="border-blue-100"] {
  border-color: rgba(93,120,155,.12) !important;
  background: linear-gradient(180deg, #f9fbfd, #f1f5f8) !important;
  color: #53697d !important;
}

/* Reactions */
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-reactions {
  gap: 6px !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-reactions > button,
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-reactions > span {
  min-height: 27px;
  padding: 4px 9px !important;
  border-color: rgba(148,106,30,.12) !important;
  background: rgba(255,255,255,.82) !important;
  box-shadow: 0 4px 10px rgba(55,39,12,.035) !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-reactions > button:hover {
  border-color: rgba(180,129,28,.27) !important;
  background: #fff9eb !important;
}

/* Message action toolbar: compact executive controls instead of visual clutter */
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-actions {
  width: fit-content;
  max-width: min(100%, 720px);
  gap: 5px !important;
  margin-top: 7px !important;
  padding: 5px !important;
  border: 1px solid rgba(148,106,29,.11);
  border-radius: 14px;
  background: rgba(255,255,255,.82);
  box-shadow: 0 8px 20px rgba(57,40,12,.05);
  backdrop-filter: blur(12px);
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-actions > button {
  min-height: 27px;
  padding: 4px 9px !important;
  border-color: transparent !important;
  background: transparent !important;
  color: #756956 !important;
  font-size: 10.5px !important;
  box-shadow: none !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-actions > button:hover {
  color: #674608 !important;
  border-color: rgba(177,126,25,.13) !important;
  background: #fff7e6 !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-actions > button[class*="text-red"] {
  color: #aa5147 !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-actions > div[aria-label] {
  gap: 1px !important;
  padding: 2px 4px !important;
  border-color: rgba(148,106,29,.10) !important;
  background: #faf6ef !important;
  box-shadow: none !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-message-actions > div[aria-label] button {
  width: 25px !important;
  height: 25px !important;
  font-size: 12px !important;
}

/* Date / unread separators */
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-message-canvas > .flex.justify-center > span {
  border-color: rgba(150,108,31,.12) !important;
  color: #9a8c78 !important;
  background: rgba(255,253,248,.90) !important;
  box-shadow: 0 5px 14px rgba(54,38,12,.035) !important;
}

/* Composer becomes a single deliberate command surface */
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer {
  padding: 12px 14px 10px !important;
  background:
    linear-gradient(180deg, rgba(255,255,255,.96), rgba(247,239,226,.98)) !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer > div.relative.flex.items-end {
  padding: 6px !important;
  gap: 7px !important;
  border: 1px solid rgba(161,115,27,.17) !important;
  border-radius: 18px !important;
  background:
    radial-gradient(circle at 88% -50%, rgba(215,168,68,.09), transparent 38%),
    linear-gradient(180deg, #fffefa, #fbf6ed) !important;
  box-shadow:
    0 11px 27px rgba(57,40,12,.06),
    inset 0 1px 0 rgba(255,255,255,.96) !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer > div.relative.flex.items-end:focus-within {
  border-color: rgba(185,133,29,.34) !important;
  box-shadow:
    0 13px 30px rgba(84,57,10,.075),
    0 0 0 3px rgba(204,157,58,.055),
    inset 0 1px 0 rgba(255,255,255,.96) !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer textarea {
  min-height: 44px !important;
  padding: 10px 9px !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  line-height: 1.55 !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer > div.relative.flex.items-end > button {
  border: 1px solid rgba(153,110,30,.12);
  border-radius: 14px !important;
  background: rgba(255,255,255,.78);
  box-shadow: 0 5px 13px rgba(56,39,12,.045);
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer > div.relative.flex.items-end > button:hover:not(:disabled) {
  border-color: rgba(177,127,27,.25) !important;
  background: #fff9eb !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer button[aria-label="إرسال الرسالة"],
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer button[aria-label="Send message"] {
  border-color: rgba(169,118,20,.30) !important;
  color: #2d210b !important;
  background: linear-gradient(145deg, #f1d78f 0%, #d5aa44 100%) !important;
  box-shadow: 0 9px 20px rgba(120,82,11,.15), inset 0 1px 0 rgba(255,255,255,.42) !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v4-composer-hint {
  margin-top: 7px !important;
  color: #9a8f80 !important;
  font-size: 10px !important;
}

/* Reply/edit strip in composer */
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer > div[class*="bg-amber-50"] {
  border-color: rgba(183,132,30,.18) !important;
  background: linear-gradient(180deg, #fffaf0, #f7ebd3) !important;
  color: #71500e !important;
  box-shadow: 0 6px 14px rgba(76,52,10,.04) !important;
}

/* Inspector refinement */
html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-details-panel > div {
  padding: 8px !important;
  gap: 8px !important;
  border-radius: 22px !important;
  background:
    radial-gradient(circle at 86% 0%, rgba(210,161,58,.08), transparent 28%),
    linear-gradient(180deg, #fbf8f1 0%, #f2e9da 100%) !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-detail-card {
  border-radius: 16px !important;
  border-color: rgba(151,108,29,.12) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.97), rgba(250,245,236,.93)) !important;
  box-shadow: 0 7px 18px rgba(56,39,11,.04), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-details-panel .tos-chat-detail-card:first-child {
  padding: 12px !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-details-panel .tos-chat-detail-card:first-child .mt-2\.5.grid.grid-cols-3 {
  gap: 4px !important;
  padding: 4px !important;
  border: 1px solid rgba(157,112,27,.10) !important;
  border-radius: 12px !important;
  background: #f5edde !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-details-panel .tos-chat-detail-card:first-child .mt-2\.5.grid.grid-cols-3 button {
  min-height: 29px !important;
  border-radius: 9px !important;
  font-size: 9px !important;
}

html:not(.dark) [data-tcs-fine-polish="v5.1"] .tos-chat-details-panel .grid.grid-cols-3.text-center > span {
  border: 1px solid rgba(151,108,29,.10) !important;
  border-radius: 10px !important;
  background: rgba(255,255,255,.66) !important;
  color: #756a59 !important;
}

/* Scrollbars stay subtle */
[data-tcs-fine-polish="v5.1"] .tos-chat-v8-message-canvas,
[data-tcs-fine-polish="v5.1"] .tos-chat-details-panel > div {
  scrollbar-width: thin;
  scrollbar-color: rgba(143,104,33,.20) transparent;
}

/* Dark mode refinement without gold wash */
.dark [data-tcs-fine-polish="v5.1"] .tos-chat-message-actions {
  border-color: rgba(255,255,255,.08);
  background: rgba(24,24,27,.82);
  box-shadow: 0 8px 20px rgba(0,0,0,.20);
}

.dark [data-tcs-fine-polish="v5.1"] .tos-chat-v8-composer > div.relative.flex.items-end {
  border-color: rgba(255,255,255,.09) !important;
  background: rgba(24,24,27,.82) !important;
  box-shadow: 0 10px 26px rgba(0,0,0,.18) !important;
}

/* Window-aware responsive spacing */
[data-tcs-fine-polish="v5.1"].tos-chat-window-size-medium .tos-chat-v8-message-canvas {
  padding-inline: 13px !important;
}

[data-tcs-fine-polish="v5.1"].tos-chat-window-size-medium .tos-chat-bubble {
  max-width: min(100%, 610px) !important;
}

[data-tcs-fine-polish="v5.1"].tos-chat-window-size-narrow .tos-chat-v8-message-canvas {
  padding: 10px !important;
}

[data-tcs-fine-polish="v5.1"].tos-chat-window-size-narrow .tos-chat-message-row {
  gap: 7px !important;
  padding-inline: 1px !important;
}

[data-tcs-fine-polish="v5.1"].tos-chat-window-size-narrow .tos-chat-bubble {
  max-width: 100% !important;
  border-radius: 15px !important;
}

[data-tcs-fine-polish="v5.1"].tos-chat-window-size-narrow .tos-chat-message-actions {
  max-width: 100%;
  gap: 3px !important;
  padding: 4px !important;
}

[data-tcs-fine-polish="v5.1"].tos-chat-window-size-narrow .tos-chat-message-actions > button {
  padding: 4px 7px !important;
  font-size: 10px !important;
}

[data-tcs-fine-polish="v5.1"].tos-chat-window-size-narrow .tos-chat-v8-composer {
  padding: 8px !important;
}

[data-tcs-fine-polish="v5.1"].tos-chat-window-size-narrow .tos-chat-v8-composer > div.relative.flex.items-end {
  gap: 4px !important;
  padding: 4px !important;
  border-radius: 15px !important;
}

[data-tcs-fine-polish="v5.1"].tos-chat-window-size-narrow .tos-chat-v8-composer > div.relative.flex.items-end > button {
  width: 38px !important;
  height: 38px !important;
  border-radius: 12px !important;
}

@media (max-width: 640px) {
  [data-tcs-fine-polish="v5.1"] .tos-chat-v8-message-canvas { padding: 9px !important; }
  [data-tcs-fine-polish="v5.1"] .tos-chat-message-row { gap: 7px !important; padding-inline: 0 !important; }
  [data-tcs-fine-polish="v5.1"] .tos-chat-message-actions { opacity: 1 !important; }
  [data-tcs-fine-polish="v5.1"] .tos-chat-v4-composer-hint > span:last-child { display: none; }
}
'''

CSS.write_text(css, encoding="utf-8")
CHAT.write_text(chat, encoding="utf-8")

print(f"PATCH={PATCH}")
print("FILES_CHANGED=2")
print("MESSAGE_BUBBLES=POLISHED")
print("MESSAGE_ACTIONS=COMPACT")
print("REACTIONS=POLISHED")
print("COMPOSER=FINE_POLISH")
print("INSPECTOR=FINE_POLISH")
print("RESPONSIVE_SPACING=WINDOW_AWARE")
print("CANPIN_PROP_GUARD=FIXED")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("NEXT=BUILD_DEPLOY")
