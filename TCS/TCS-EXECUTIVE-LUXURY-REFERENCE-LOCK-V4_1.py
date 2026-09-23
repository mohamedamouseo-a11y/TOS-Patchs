#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-EXECUTIVE-LUXURY-REFERENCE-LOCK-V4_1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsExecutiveLuxuryReferenceLockV4_1.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# Layer V4.1 after the approved V4 mockup stylesheet.
css_import = 'import "./tcsExecutiveLuxuryReferenceLockV4_1.css";'
if css_import not in src:
    anchor = 'import "./tcsExecutiveLuxuryMockupV4.css";'
    if anchor not in src:
        raise SystemExit(f"{PATCH}: V4 stylesheet import not found")
    src = src.replace(anchor, anchor + "\n" + css_import, 1)

# Give the existing empty-state icon a stable hook for the reference illustration.
old_icon = '''<div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-3xl bg-gradient-to-br from-amber-50 to-zinc-50 text-amber-600 ring-1 ring-amber-100 dark:from-amber-500/10 dark:to-white/5 dark:text-amber-200 dark:ring-amber-500/20"><MessageCircle size={22} /></div>'''
new_icon = '''<div className="tcs-v41-empty-icon mx-auto mb-3 grid h-12 w-12 place-items-center rounded-3xl bg-gradient-to-br from-amber-50 to-zinc-50 text-amber-600 ring-1 ring-amber-100 dark:from-amber-500/10 dark:to-white/5 dark:text-amber-200 dark:ring-amber-500/20"><MessageCircle size={22} /></div>'''
if "tcs-v41-empty-icon" not in src:
    if old_icon not in src:
        raise SystemExit(f"{PATCH}: empty-state icon anchor not found")
    src = src.replace(old_icon, new_icon, 1)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-executive-luxury-reference-lock-v4-1: 1; }

/* =========================================================
   TCS Executive Luxury Reference Lock V4.1
   Locks live UI closer to the approved visual mockup.
   Typography/scale/spacing/empty-state refinement only.
   ========================================================= */

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 {
  --v41-gold: #c58e22;
  --v41-gold-deep: #9a6812;
  --v41-line: #e9e2d6;
  --v41-soft: #fbf9f4;
  --v41-ink: #1c1a18;
}

/* Premium window chrome */
html:not(.dark) .tcs-desktop-window {
  border: 1px solid #e5ded2 !important;
  border-radius: 20px !important;
  background: #fff !important;
  box-shadow: 0 22px 60px rgba(47, 38, 24, .13) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-desktop-window-titlebar {
  min-height: 58px !important;
  padding: 0 16px !important;
  border-bottom: 1px solid #eee8de !important;
  background:
    linear-gradient(180deg, rgba(255,255,255,.99), rgba(253,251,247,.98)) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-desktop-window-identity {
  gap: 10px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-desktop-window-icon {
  width: 34px !important;
  height: 34px !important;
  border: 1px solid #e7d6ad !important;
  border-radius: 11px !important;
  background: linear-gradient(145deg,#fffdf8,#fff4d9) !important;
  color: #9b6911 !important;
  box-shadow: 0 5px 14px rgba(130,94,24,.07) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-desktop-window-identity strong {
  font-size: 13px !important;
  letter-spacing: -.02em !important;
}

html:not(.dark) .tcs-desktop-window .tcs-desktop-window-identity span {
  font-size: 9px !important;
  color: #8f887d !important;
}

html:not(.dark) .tcs-desktop-window .tcs-desktop-window-actions {
  gap: 5px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-desktop-window-actions button {
  width: 34px !important;
  height: 34px !important;
  border: 1px solid #e9e4db !important;
  border-radius: 10px !important;
  background: #fff !important;
  color: #6b655d !important;
  box-shadow: 0 3px 10px rgba(41,34,24,.04) !important;
}

/* Reference proportions */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4:not(.tos-chat-focus-mode) {
    grid-template-columns: 60px 350px minmax(0,1fr) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 60px 315px minmax(360px,1fr) 320px !important;
  }
}

/* App rail */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-ref-primary-nav {
  padding: 15px 7px 13px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-ref-primary-nav-item {
  width: 47px !important;
  min-height: 54px !important;
  border-radius: 13px !important;
}

/* Conversation rail scale and hierarchy */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail > div:first-child {
  padding: 19px 17px 14px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail h2,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail h3 {
  font-size: 15px !important;
  letter-spacing: -.025em !important;
  color: var(--v41-ink) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail input {
  min-height: 44px !important;
  font-size: 11px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail .grid.grid-cols-2 > button {
  min-height: 38px !important;
  font-size: 10px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v8-new-conversation-trigger {
  min-height: 42px !important;
  font-size: 10.5px !important;
  font-weight: 850 !important;
}

/* Rich conversation list — sized like the approved mockup */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-list {
  gap: 4px !important;
  padding-inline: 2px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row {
  grid-template-columns: 42px minmax(0,1fr) auto !important;
  min-height: 66px !important;
  gap: 11px !important;
  padding: 9px 10px !important;
  border-radius: 13px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-avatar {
  width: 40px !important;
  height: 40px !important;
  font-size: 11px !important;
  box-shadow: 0 5px 14px rgba(119,88,27,.06) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-title {
  font-size: 12.5px !important;
  font-weight: 850 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-preview {
  font-size: 10.5px !important;
  line-height: 1.35 !important;
  color: #817a71 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-time {
  font-size: 9px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-unread {
  min-width: 20px !important;
  height: 20px !important;
  font-size: 8.5px !important;
}

/* Filters should remain subtle, not tiny */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail button[class*="text-\[10px\]"],
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail button[class*="text-xs"] {
  font-size: 9.5px !important;
}

/* Main header */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center {
  padding: 19px 22px 16px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center > .flex:first-child > div:first-child > div:first-child {
  font-size: 16px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v3-icon-action {
  width: 40px !important;
  height: 40px !important;
  min-width: 40px !important;
  min-height: 40px !important;
  border-radius: 12px !important;
}

/* Search command bar */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell {
  min-height: 52px !important;
  padding: 6px 8px !important;
  border-radius: 13px !important;
  background: #fffdf9 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v15-inline-smart-search {
  font-size: 12px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell > button:last-child {
  min-height: 36px !important;
  padding-inline: 14px !important;
  border: 1px solid #d8bd7b !important;
  border-radius: 10px !important;
  background: linear-gradient(180deg,#f3dda7,#e8c66d) !important;
  color: #66440a !important;
  box-shadow: 0 6px 14px rgba(146,105,23,.10) !important;
}

/* Direct conversation prompt bar */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center + div,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell + div {
  border-color: #eee9e1 !important;
}

/* Message canvas gets the faint luxury texture from the mockup */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-message-canvas {
  background:
    radial-gradient(circle at 12% 12%, rgba(203,153,41,.045) 0 1px, transparent 1.5px) 0 0/18px 18px,
    radial-gradient(circle at 85% 88%, rgba(203,153,41,.035), transparent 22%),
    linear-gradient(180deg,#fff 0%,#fdfcf9 100%) !important;
}

/* Reference empty state: layered chat illustration, larger typography, softer card */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card {
  max-width: 500px !important;
  padding: 58px 40px 40px !important;
  border-color: #e8d9b6 !important;
  border-radius: 26px !important;
  background:
    radial-gradient(circle at 14% 10%, rgba(219,174,64,.22), transparent 22%),
    radial-gradient(circle at 88% 89%, rgba(221,193,125,.15), transparent 25%),
    linear-gradient(145deg,#fffefa,#fff9ed) !important;
  box-shadow: 0 24px 58px rgba(64,49,20,.085) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon {
  position: relative !important;
  width: 62px !important;
  height: 62px !important;
  margin-bottom: 25px !important;
  overflow: visible !important;
  border-radius: 50% !important;
  background: linear-gradient(145deg,#f8dc91,#d8a52f) !important;
  color: #fff !important;
  ring: 0 !important;
  box-shadow: 0 12px 28px rgba(170,117,18,.20) !important;
  isolation: isolate !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon svg {
  position: relative !important;
  z-index: 3 !important;
  width: 25px !important;
  height: 25px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::before,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::after {
  content: "" !important;
  position: absolute !important;
  z-index: -1 !important;
  border: 1px solid #eadfca !important;
  border-radius: 13px !important;
  background: rgba(255,255,255,.96) !important;
  box-shadow: 0 10px 26px rgba(60,47,24,.07) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::before {
  width: 78px !important;
  height: 49px !important;
  left: -58px !important;
  top: 11px !important;
  transform: rotate(-3deg) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::after {
  width: 84px !important;
  height: 53px !important;
  right: -67px !important;
  top: 25px !important;
  transform: rotate(2deg) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card .text-base {
  font-size: 17px !important;
  line-height: 1.3 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card .text-xs {
  font-size: 11px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card .mt-4 {
  margin-top: 20px !important;
  gap: 7px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card .mt-4 button {
  min-height: 30px !important;
  padding-inline: 13px !important;
  border-color: #e6dac0 !important;
  background: rgba(255,255,255,.91) !important;
  font-size: 9.5px !important;
}

/* More/status utility menus stay compact and premium */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v3-more-menu,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v31-status-menu {
  border-radius: 12px !important;
  border-color: #e6dfd4 !important;
  box-shadow: 0 16px 38px rgba(42,34,23,.13) !important;
}

/* Drive footer */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail > div:last-child {
  padding: 11px 13px !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("REFERENCE_LOCK=V4_1")
print("WINDOW_CHROME=PREMIUM")
print("CONVERSATION_SCALE=INCREASED")
print("CONVERSATION_ROWS=REFERENCE_MATCH")
print("HEADER_SCALE=INCREASED")
print("SEARCH=REFERENCE_MATCH")
print("EMPTY_ILLUSTRATION=LAYERED_CHAT")
print("EMPTY_STATE=REFERENCE_MATCH")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
