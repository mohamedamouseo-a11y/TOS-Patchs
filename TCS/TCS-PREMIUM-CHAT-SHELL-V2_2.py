#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-PREMIUM-CHAT-SHELL-V2_2"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsPremiumChatShellV2_2.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

css_import = 'import "./tcsPremiumChatShellV2_2.css";'
if css_import not in src:
    anchors = [
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
:root { --tcs-premium-chat-shell-v2-2: 1; }

/* =========================================================
   TCS Premium Chat Shell V2.2
   Goal: modern professional chat UI, not a dashboard.
   CSS-only visual layer. Existing behavior/functions untouched.
   ========================================================= */

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 {
  --tcs22-ink: #171717;
  --tcs22-muted: #78736b;
  --tcs22-line: #eae6de;
  --tcs22-soft: #f8f7f4;
  --tcs22-gold: #c99122;
  --tcs22-gold-soft: #fbf4e4;
  --tcs22-green: #18b77a;
  background: #fff !important;
}

/* ---------- Overall desktop geometry ---------- */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1:not(.tos-chat-focus-mode) {
    grid-template-columns: 56px 270px minmax(0, 1fr) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 56px 258px minmax(360px, 1fr) 326px !important;
  }
}

/* ---------- Primary mini rail ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-ref-primary-nav {
  padding: 12px 5px !important;
  background: #fbfbfa !important;
  border-inline-end: 1px solid var(--tcs22-line) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-ref-primary-nav-item {
  width: 46px !important;
  min-height: 48px !important;
  margin: 0 auto 6px !important;
  border-radius: 12px !important;
  color: #858078 !important;
  font-size: 8px !important;
  font-weight: 750 !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-ref-primary-nav-item.is-active {
  background: var(--tcs22-gold-soft) !important;
  color: #9b690a !important;
  box-shadow: inset 2px 0 0 var(--tcs22-gold) !important;
}

/* ---------- Conversation rail ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail {
  background: #fff !important;
  border-inline-end: 1px solid var(--tcs22-line) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail > div:first-child {
  padding: 15px 14px 12px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail input {
  min-height: 40px !important;
  border-radius: 10px !important;
  border-color: #e8e4dc !important;
  background: #fff !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail input:focus {
  border-color: #d6b66d !important;
  box-shadow: 0 0 0 3px rgba(201,145,34,.10) !important;
}

/* Project / Direct segmented control */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .grid.grid-cols-2 {
  gap: 3px !important;
  padding: 3px !important;
  border: 1px solid #ebe7df !important;
  border-radius: 11px !important;
  background: #f7f6f3 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .grid.grid-cols-2 > button {
  min-height: 34px !important;
  border: 0 !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}

/* Filter chips */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail [class*="rounded-xl"][class*="text-"] button,
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail [class*="rounded-lg"][class*="text-"] button {
  box-shadow: none !important;
}

/* New conversation: compact primary CTA */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-new-conversation-trigger {
  min-height: 38px !important;
  border: 1px solid #dfc789 !important;
  border-radius: 10px !important;
  background: #fffaf0 !important;
  color: #8c620e !important;
  box-shadow: none !important;
}

/* Conversation rows: proper chat-list rhythm instead of floating names. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .space-y-1 {
  display: flex !important;
  flex-direction: column !important;
  gap: 3px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .space-y-1 > button {
  position: relative !important;
  min-height: 48px !important;
  margin: 0 !important;
  padding: 8px 10px 8px 44px !important;
  border: 1px solid transparent !important;
  border-radius: 11px !important;
  background: transparent !important;
  color: #3f3b36 !important;
  text-align: start !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .space-y-1 > button::before {
  content: "";
  position: absolute;
  left: 8px;
  top: 50%;
  width: 28px;
  height: 28px;
  transform: translateY(-50%);
  border: 1px solid #e8ddc3;
  border-radius: 9px;
  background:
    radial-gradient(circle at 50% 38%, #c99a3a 0 14%, transparent 15%),
    radial-gradient(circle at 50% 75%, #e7d6ac 0 28%, transparent 29%),
    #fbf7ed;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1[dir="rtl"] .tos-chat-v8-rail .space-y-1 > button {
  padding-left: 10px !important;
  padding-right: 44px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1[dir="rtl"] .tos-chat-v8-rail .space-y-1 > button::before {
  left: auto;
  right: 8px;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .space-y-1 > button:hover {
  border-color: #ede8df !important;
  background: #faf9f7 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-v8-rail .space-y-1 > button[class*="bg-white"] {
  border-color: #ead8aa !important;
  background: #fffaf0 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-ref-conversation-title {
  max-width: 165px !important;
  font-size: 11px !important;
  font-weight: 820 !important;
  color: #302d29 !important;
}

/* ---------- Main chat header ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-command-center {
  padding: 15px 18px 13px !important;
  border-bottom: 1px solid #efebe4 !important;
  background: rgba(255,255,255,.98) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-command-center h1,
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-command-center h2 {
  color: var(--tcs22-ink) !important;
  letter-spacing: -.025em !important;
}

/* Top actions: smaller and calmer */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-command-center .relative.hidden.items-center > button {
  min-height: 36px !important;
  padding: 8px 12px !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-command-center .relative.hidden.items-center > button:not([class*="bg-zinc-950"]) {
  border-color: #e8e4dc !important;
  background: #fff !important;
}

/* Smart search becomes a true command/search bar */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-inline-search-shell {
  min-height: 46px !important;
  padding: 5px 7px !important;
  border: 1px solid #e8e3d9 !important;
  border-radius: 11px !important;
  background: #faf9f7 !important;
  box-shadow: none !important;
}

/* ---------- Empty state ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-empty-clean-card {
  max-width: 410px !important;
  padding: 30px 28px !important;
  border: 1px solid #ead7a6 !important;
  border-radius: 20px !important;
  background:
    radial-gradient(circle at 0 0, rgba(223,181,78,.18), transparent 31%),
    linear-gradient(145deg, #fffdf9, #fff9eb) !important;
  box-shadow: 0 18px 44px rgba(62,48,20,.08) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-empty-clean-card h3 {
  font-size: 15px !important;
  letter-spacing: -.015em !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-empty-clean-card p {
  max-width: 330px !important;
  margin-inline: auto !important;
  line-height: 1.55 !important;
  color: #81786a !important;
}

/* ---------- Chat tools: refined command palette ---------- */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu {
  width: 242px !important;
  padding: 8px !important;
  border: 1px solid #e4dfd6 !important;
  border-radius: 13px !important;
  background: #fff !important;
  box-shadow: 0 18px 48px rgba(31,26,18,.14) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu::before {
  content: "";
  position: absolute;
  top: -5px;
  right: 22px;
  width: 10px;
  height: 10px;
  transform: rotate(45deg);
  border-left: 1px solid #e4dfd6;
  border-top: 1px solid #e4dfd6;
  background: #fff;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1[dir="rtl"] .tcs-v16-tools-menu::before {
  right: auto;
  left: 22px;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu .mb-3 {
  padding: 2px 2px 7px !important;
  margin: 0 0 6px !important;
  border-bottom: 1px solid #efebe4 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu .text-sm {
  font-size: 10.5px !important;
  font-weight: 900 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions {
  grid-template-columns: repeat(4, minmax(0,1fr)) !important;
  gap: 4px !important;
  margin: 0 !important;
  padding: 0 0 6px !important;
  border: 0 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v8-toolbar-menu-actions button {
  min-height: 31px !important;
  padding: 5px 2px !important;
  border: 1px solid #ece8e0 !important;
  border-radius: 8px !important;
  background: #faf9f7 !important;
  color: #615b53 !important;
  font-size: 7.8px !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-status-segment {
  grid-template-columns: repeat(4, minmax(0,1fr)) !important;
  gap: 3px !important;
  margin: 0 0 6px !important;
  padding: 3px !important;
  border: 1px solid #ece8df !important;
  border-radius: 9px !important;
  background: #f7f6f3 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-status-segment button {
  min-height: 27px !important;
  padding: 4px 2px !important;
  border: 0 !important;
  border-radius: 7px !important;
  background: transparent !important;
  color: #777168 !important;
  font-size: 7.6px !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-status-segment button[class*="bg-amber-400"] {
  background: var(--tcs22-gold) !important;
  color: #fff !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu > .grid.grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0,1fr)) !important;
  gap: 4px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tcs-v16-tools-menu > .grid.grid-cols-2 > button {
  min-height: 30px !important;
  padding: 5px 5px !important;
  border: 1px solid #ece8e0 !important;
  border-radius: 8px !important;
  background: #fff !important;
  color: #5e5850 !important;
  font-size: 8px !important;
  box-shadow: none !important;
}

/* ---------- Unified inspector ---------- */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel:not(.hidden) {
    background: #f9f8f6 !important;
    border-inline-start: 1px solid var(--tcs22-line) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel:not(.hidden) > div {
    padding: 0 !important;
    gap: 0 !important;
    background: #f9f8f6 !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:first-child {
    margin: 0 !important;
    padding: 14px 14px 12px !important;
    border: 0 !important;
    border-bottom: 1px solid #e9e5dc !important;
    border-radius: 0 !important;
    background: #fff !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:not(:first-child) {
    margin: 9px 9px 0 !important;
    padding: 11px !important;
    border: 1px solid #ebe7df !important;
    border-radius: 12px !important;
    background: #fff !important;
    box-shadow: none !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1 .tos-chat-details-panel .tos-chat-detail-card:last-child {
    margin-bottom: 9px !important;
  }
}

/* ---------- Responsive safety ---------- */
@media (max-width: 1180px) {
  @media (min-width: 1024px) {
    html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2-fix1.tos-chat-details-open:not(.tos-chat-focus-mode) {
      grid-template-columns: 54px 230px minmax(300px, 1fr) 292px !important;
    }
  }
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=CSS_ONLY")
print("CONVERSATION_RAIL=PREMIUM_CHAT_LIST")
print("EMPTY_STATE=REFINED")
print("TOOLS=COMPACT_COMMAND_PALETTE")
print("INSPECTOR=REFINED_SIDE_PANEL")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
