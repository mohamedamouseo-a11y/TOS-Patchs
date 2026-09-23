#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-EXECUTIVE-PREMIUM-POLISH-V5"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsExecutivePremiumPolishV5.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

backup = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup / "ChatPanel.jsx")
if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)

chat = CHAT.read_text(encoding="utf-8")

import_anchor = 'import "./tcsExecutiveLuxuryFinalReferenceLockV4_5.css";'
import_line = 'import "./tcsExecutivePremiumPolishV5.css";'
if import_line not in chat:
    if import_anchor not in chat:
        raise SystemExit(f"{PATCH}: V4_5 import anchor missing")
    chat = chat.replace(import_anchor, import_anchor + "\n" + import_line, 1)

root_old = '<div ref={chatShellRef} data-tcs-unread-read-flow="v1" data-tcs-presentation={presentation}'
root_new = '<div ref={chatShellRef} data-tcs-premium-polish="v5" data-tcs-unread-read-flow="v1" data-tcs-presentation={presentation}'
if 'data-tcs-premium-polish="v5"' not in chat:
    if root_old not in chat:
        raise SystemExit(f"{PATCH}: root marker anchor missing")
    chat = chat.replace(root_old, root_new, 1)

class_old = 'tos-chat-modern-shell tcs-executive-luxury-v4'
class_new = 'tos-chat-modern-shell tcs-premium-polish-v5 tcs-executive-luxury-v4'
if class_new not in chat:
    if class_old not in chat:
        raise SystemExit(f"{PATCH}: root class anchor missing")
    chat = chat.replace(class_old, class_new, 1)

css = r''':root {
  --tcs-executive-premium-polish-v5: 1;
  --tcs-v5-ink: #211a12;
  --tcs-v5-muted: #827767;
  --tcs-v5-line: rgba(148, 107, 33, .14);
  --tcs-v5-line-strong: rgba(159, 113, 27, .24);
  --tcs-v5-ivory: #fffdf8;
  --tcs-v5-warm: #f8f2e8;
  --tcs-v5-gold: #c79a3b;
  --tcs-v5-gold-deep: #946712;
  --tcs-v5-shadow: 0 22px 54px rgba(57, 39, 11, .10);
}

/* TCS Executive Premium Polish V5 */
html:not(.dark) .tcs-desktop-window {
  border: 1px solid rgba(157, 113, 29, .20) !important;
  background: linear-gradient(180deg, #fffefa 0%, #f6efe4 100%) !important;
  box-shadow: 0 30px 80px rgba(47, 34, 14, .16), 0 8px 24px rgba(47, 34, 14, .08), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

html:not(.dark) .tcs-desktop-window-titlebar {
  min-height: 51px !important;
  padding-inline: 15px !important;
  border-bottom: 1px solid rgba(159, 113, 27, .15) !important;
  background: radial-gradient(circle at 12% -80%, rgba(217,172,76,.18), transparent 40%), linear-gradient(180deg, #fffefb 0%, #f7efe2 100%) !important;
}

html:not(.dark) .tcs-desktop-window-identity strong {
  color: #251b0f !important;
  font-weight: 900 !important;
  letter-spacing: -.02em !important;
}

html:not(.dark) .tcs-desktop-window-identity span { color: #8d7b5f !important; }

html:not(.dark) .tcs-desktop-window-icon {
  color: #6d4a0a !important;
  border: 1px solid rgba(174,124,26,.22) !important;
  background: linear-gradient(145deg, #fffdf7, #f1dfb8) !important;
  box-shadow: 0 7px 16px rgba(73,50,11,.08), inset 0 1px 0 #fff !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] {
  color: var(--tcs-v5-ink);
  border-color: var(--tcs-v5-line) !important;
  background: radial-gradient(circle at 78% 8%, rgba(202,154,54,.05), transparent 24%), linear-gradient(180deg, #fffefa 0%, #f8f3eb 100%) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-ref-primary-nav {
  border-inline-end: 1px solid rgba(152,109,29,.14) !important;
  background: radial-gradient(circle at 50% 0%, rgba(213,164,66,.14), transparent 27%), linear-gradient(180deg, #f8f0e2 0%, #eee2ce 100%) !important;
  box-shadow: inset -1px 0 0 rgba(255,255,255,.70) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-ref-primary-nav-item {
  color: #7b6c58 !important;
  border: 1px solid transparent !important;
  border-radius: 15px !important;
  transition: transform .16s ease, border-color .16s ease, background .16s ease, color .16s ease !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-ref-primary-nav-item:hover {
  color: #684509 !important;
  border-color: rgba(174,124,27,.18) !important;
  background: rgba(255,255,255,.56) !important;
  transform: translateY(-1px);
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-ref-primary-nav-item.is-active {
  color: #fff7e3 !important;
  border-color: rgba(220,176,81,.40) !important;
  background: linear-gradient(145deg, #2f2519 0%, #5f451c 58%, #9a6813 100%) !important;
  box-shadow: 0 12px 26px rgba(56,38,8,.18), inset 0 1px 0 rgba(255,255,255,.12) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-v8-rail {
  color: #2a2116 !important;
  border-color: rgba(155,111,28,.16) !important;
  background: radial-gradient(circle at 28% -8%, rgba(218,171,75,.17), transparent 28%), linear-gradient(180deg, #fbf6ed 0%, #f2e8d8 100%) !important;
  box-shadow: 11px 0 32px rgba(63,44,12,.045), inset -1px 0 0 rgba(255,255,255,.78) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-v8-rail > div:first-child {
  border-color: rgba(160,115,27,.15) !important;
  background: linear-gradient(180deg, rgba(255,254,250,.90), rgba(247,238,221,.68)) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v4-conversation-list {
  padding: 6px 6px 10px !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v4-conversation-row {
  min-height: 67px !important;
  margin-block: 5px !important;
  padding: 9px 10px !important;
  border: 1px solid rgba(159,114,28,.12) !important;
  border-radius: 16px !important;
  color: #2e2418 !important;
  background: linear-gradient(90deg, rgba(204,153,48,.035), transparent 25%), linear-gradient(180deg, rgba(255,255,255,.92), rgba(249,243,232,.86)) !important;
  box-shadow: 0 7px 18px rgba(58,41,13,.045), inset 0 1px 0 rgba(255,255,255,.92) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v4-conversation-row:hover {
  border-color: rgba(173,123,25,.27) !important;
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(67,46,11,.075), inset 0 1px 0 rgba(255,255,255,.95) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v4-conversation-row.is-active {
  color: #fff8e8 !important;
  border-color: rgba(222,181,91,.44) !important;
  background: radial-gradient(circle at 90% -30%, rgba(235,198,118,.17), transparent 45%), linear-gradient(135deg, #30261b 0%, #55401f 58%, #775419 100%) !important;
  box-shadow: 0 16px 30px rgba(54,37,9,.16), inset 0 1px 0 rgba(255,255,255,.10) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v4-conversation-avatar {
  border: 1px solid rgba(178,128,28,.20) !important;
  background: linear-gradient(145deg, #fffdf8, #ead5a8) !important;
  color: #684708 !important;
  box-shadow: 0 5px 12px rgba(68,47,10,.07) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v4-conversation-row.is-active .tcs-v4-conversation-avatar {
  border-color: rgba(234,198,118,.42) !important;
  background: linear-gradient(145deg, #f5dfaa, #c99c40) !important;
  color: #3f2a06 !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] [data-tcs-group-chat-flow="v1"] {
  border: 1px solid rgba(171,122,25,.18) !important;
  border-radius: 18px !important;
  background: linear-gradient(180deg, rgba(255,255,255,.82), rgba(246,235,216,.72)) !important;
  box-shadow: 0 10px 22px rgba(64,44,11,.055), inset 0 1px 0 rgba(255,255,255,.90) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] [data-tcs-group-chat-flow="v1"] input {
  color: #2b2115 !important;
  border-color: rgba(160,113,25,.18) !important;
  background: rgba(255,255,255,.90) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-command-center {
  padding-top: 13px !important;
  padding-bottom: 12px !important;
  border-color: rgba(160,114,27,.15) !important;
  background: radial-gradient(circle at 90% -60%, rgba(217,171,74,.14), transparent 38%), linear-gradient(180deg, rgba(255,255,255,.97), rgba(249,243,232,.94)) !important;
  box-shadow: 0 12px 32px rgba(58,40,11,.045), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-command-center h2 {
  color: #1d1710 !important;
  font-size: 18px !important;
  font-weight: 900 !important;
  letter-spacing: -.028em !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-command-center p { color: #8a7f70 !important; }

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-command-center button {
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-command-center button:hover { transform: translateY(-1px); }

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v16-inline-search-shell {
  min-height: 43px !important;
  padding-inline: 12px !important;
  border-color: rgba(158,112,26,.16) !important;
  border-radius: 15px !important;
  background: linear-gradient(180deg, #fffefa, #faf5ec) !important;
  box-shadow: 0 7px 18px rgba(57,40,12,.045), inset 0 1px 0 rgba(255,255,255,.94) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v16-inline-search-shell:focus-within {
  border-color: rgba(184,133,29,.34) !important;
  box-shadow: 0 9px 22px rgba(91,62,9,.07), 0 0 0 3px rgba(203,155,56,.055) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v16-inline-search-shell > button:last-child {
  color: #684708 !important;
  border: 1px solid rgba(177,127,27,.22) !important;
  background: linear-gradient(180deg, #f5e4b7, #dfbd66) !important;
  box-shadow: 0 7px 15px rgba(104,72,12,.10), inset 0 1px 0 rgba(255,255,255,.46) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-v8-workspace {
  background: radial-gradient(circle at 50% 24%, rgba(203,153,49,.045), transparent 24%), linear-gradient(180deg, #fffefa 0%, #fbf8f2 100%) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-v8-message-canvas {
  scrollbar-color: rgba(160,114,26,.20) transparent;
  background: radial-gradient(circle at 11% 13%, rgba(198,147,31,.043) 0 1px, transparent 1.3px) 0 0/22px 22px, radial-gradient(circle at 89% 90%, rgba(207,160,56,.055), transparent 27%), linear-gradient(180deg, #fffefa 0%, #fdfaf4 100%) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-empty-clean-card {
  border: 1px solid rgba(164,116,25,.16) !important;
  background: radial-gradient(circle at 13% 6%, rgba(216,169,68,.22), transparent 24%), radial-gradient(circle at 88% 92%, rgba(223,190,112,.15), transparent 27%), linear-gradient(145deg, #fffefb 0%, #fff8e9 100%) !important;
  box-shadow: 0 30px 70px rgba(60,43,16,.09), 0 8px 22px rgba(60,43,16,.045), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-v8-composer {
  border-color: rgba(158,112,26,.14) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.94), rgba(248,241,229,.97)) !important;
  box-shadow: 0 -12px 30px rgba(57,40,12,.045), inset 0 1px 0 rgba(255,255,255,.95) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-v8-composer textarea {
  border-color: rgba(160,114,26,.16) !important;
  background: #fffefa !important;
  color: #271f15 !important;
  box-shadow: inset 0 1px 2px rgba(64,44,10,.03) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-v8-composer textarea:focus {
  border-color: rgba(185,132,27,.34) !important;
  box-shadow: 0 0 0 3px rgba(202,154,55,.055), inset 0 1px 2px rgba(64,44,10,.025) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-details-panel > div {
  background: linear-gradient(180deg, #fbf8f1, #f4ecdf) !important;
  border: 1px solid rgba(158,112,26,.13) !important;
  box-shadow: 0 26px 60px rgba(48,34,12,.13) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-detail-card {
  border-color: rgba(157,111,25,.13) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(250,245,236,.91)) !important;
  box-shadow: 0 8px 20px rgba(58,40,11,.045), inset 0 1px 0 rgba(255,255,255,.95) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] [data-tcs-action-center-flow="v1"] {
  border-color: rgba(159,113,27,.16) !important;
  background: radial-gradient(circle at 92% -30%, rgba(215,168,67,.13), transparent 38%), linear-gradient(180deg, #fffefa, #faf4e9) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] [data-tcs-action-center-flow="v1"] button {
  border: 1px solid rgba(64,122,84,.10) !important;
  background: linear-gradient(180deg, #f8fff9, #edf8ef) !important;
  box-shadow: 0 5px 12px rgba(43,86,58,.045) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] [data-tcs-action-center-flow="v1"] button:hover {
  border-color: rgba(58,121,78,.20) !important;
  transform: translateY(-1px);
}

html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-details-panel form[class*="bg-amber-50"] {
  border-color: rgba(170,121,24,.17) !important;
  background: linear-gradient(180deg, #fffaf0, #f6e9cf) !important;
  box-shadow: 0 8px 18px rgba(62,43,11,.055) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] [data-tcs-huddle-flow="v1"] > div {
  border: 1px solid rgba(163,116,27,.20) !important;
  border-radius: 24px !important;
  background: #fffdf9 !important;
  box-shadow: 0 26px 58px rgba(42,31,14,.20), inset 0 1px 0 #fff !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] [data-tcs-huddle-flow="v1"] > div > div:first-child {
  border-color: rgba(221,183,101,.18) !important;
  background: radial-gradient(circle at 84% -40%, rgba(233,195,112,.18), transparent 42%), linear-gradient(135deg, #2a2117 0%, #4c381d 58%, #6e4c15 100%) !important;
}

html:not(.dark) [data-tcs-premium-polish="v5"] [data-tcs-huddle-flow="v1"] video { border-radius: 14px; }

html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v5-contained-surface > form,
html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v5-contained-surface > div:not(.absolute) {
  border-color: rgba(162,115,26,.18) !important;
  background: radial-gradient(circle at 92% -25%, rgba(216,170,73,.13), transparent 35%), linear-gradient(180deg, #fffefa, #f8f2e8) !important;
  box-shadow: 0 30px 70px rgba(47,33,11,.16), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

.dark [data-tcs-premium-polish="v5"] [data-tcs-action-center-flow="v1"],
.dark [data-tcs-premium-polish="v5"] [data-tcs-group-chat-flow="v1"] {
  box-shadow: 0 10px 24px rgba(0,0,0,.18);
}

@media (max-width: 1024px) {
  html:not(.dark) [data-tcs-premium-polish="v5"] .tcs-v4-conversation-row { min-height: 62px !important; }
  html:not(.dark) [data-tcs-premium-polish="v5"] .tos-chat-command-center { padding-inline: 12px !important; }
}

@media (prefers-reduced-motion: reduce) {
  [data-tcs-premium-polish="v5"] *,
  [data-tcs-premium-polish="v5"] *::before,
  [data-tcs-premium-polish="v5"] *::after {
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
  }
}
'''

CSS.write_text(css, encoding="utf-8")
CHAT.write_text(chat, encoding="utf-8")

print(f"PATCH={PATCH}")
print("FILES_CHANGED=2")
print("PREMIUM_SHELL=YES")
print("WINDOW_CHROME=YES")
print("RAIL=YES")
print("HEADER_SEARCH=YES")
print("WORKSPACE_COMPOSER=YES")
print("INSPECTOR=YES")
print("GROUP_FLOW_STYLED=YES")
print("HUDDLE_STYLED=YES")
print("ACTION_CENTER_STYLED=YES")
print("FUNCTIONAL_LOGIC_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("NEXT=BUILD_DEPLOY")
