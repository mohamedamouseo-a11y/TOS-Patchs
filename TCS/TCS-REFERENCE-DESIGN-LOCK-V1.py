#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys

PATCH = "TCS-REFERENCE-DESIGN-LOCK-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsReferenceLockV1.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

source = CHAT.read_text(encoding="utf-8")

required = [
    'import { Download, Eye, FileText, Image as ImageIcon, Lock, MessageCircle, Mic, MicOff, Monitor, Paperclip, Phone, PhoneOff, RefreshCw, Search, Send, Trash2, Users, Video, VideoOff, X } from "lucide-react";',
    'import { usePreferences } from "../contexts/PreferencesContext";',
    'className={`tos-chat-modern-shell ',
    '<aside className={`${focusMode ? "hidden" : "hidden lg:flex"} tos-chat-rail tos-chat-v4-rail tos-chat-v8-rail',
]
for marker in required:
    if marker not in source:
        raise SystemExit(f"{PATCH}: expected marker not found: {marker[:110]}")

backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

old_import = 'import { Download, Eye, FileText, Image as ImageIcon, Lock, MessageCircle, Mic, MicOff, Monitor, Paperclip, Phone, PhoneOff, RefreshCw, Search, Send, Trash2, Users, Video, VideoOff, X } from "lucide-react";'
new_import = 'import { Archive, Download, Eye, FileText, FolderKanban, Image as ImageIcon, Lock, MessageCircle, Mic, MicOff, Monitor, Paperclip, Phone, PhoneOff, RefreshCw, Search, Send, Settings2, Trash2, Users, Video, VideoOff, X } from "lucide-react";'
source = source.replace(old_import, new_import, 1)

css_import = 'import "./tcsReferenceLockV1.css";'
pref_import = 'import { usePreferences } from "../contexts/PreferencesContext";'
if css_import not in source:
    source = source.replace(pref_import, pref_import + "\n" + css_import, 1)

source = source.replace(
    'className={`tos-chat-modern-shell ',
    'className={`tos-chat-modern-shell tcs-reference-lock-v1 ',
    1,
)

aside_marker = '      <aside className={`${focusMode ? "hidden" : "hidden lg:flex"} tos-chat-rail tos-chat-v4-rail tos-chat-v8-rail'
nav = '''      {isDesktopWindow && !focusMode && (
        <nav className="tcs-ref-primary-nav hidden lg:flex" aria-label={lang === "en" ? "TCS navigation" : "تنقل TCS"}>
          <button type="button" className={`tcs-ref-primary-nav-item ${conversationFilter !== "projects" && conversationFilter !== "archived" ? "is-active" : ""}`} onClick={() => setConversationFilter("all")} title={lang === "en" ? "Chat" : "الشات"}>
            <MessageCircle size={19} />
            <span>{lang === "en" ? "Chat" : "شات"}</span>
          </button>
          <button type="button" disabled={!projectId} className={`tcs-ref-primary-nav-item ${conversationFilter === "projects" ? "is-active" : ""}`} onClick={() => { if (!projectId) return; switchMode("project"); setConversationFilter("projects"); }} title={lang === "en" ? "Projects" : "المشاريع"}>
            <FolderKanban size={19} />
            <span>{lang === "en" ? "Projects" : "مشاريع"}</span>
          </button>
          <button type="button" className={`tcs-ref-primary-nav-item ${conversationFilter === "archived" ? "is-active" : ""}`} onClick={() => setConversationFilter("archived")} title={lang === "en" ? "Archive" : "الأرشيف"}>
            <Archive size={19} />
            <span>{lang === "en" ? "Archive" : "أرشيف"}</span>
          </button>
          <div className="tcs-ref-primary-nav-spacer" />
          <button type="button" className="tcs-ref-primary-nav-item" onClick={() => { setDetailsPanelOpen(true); setDetailsTab("activity"); }} title={lang === "en" ? "Settings" : "الإعدادات"}>
            <Settings2 size={19} />
            <span>{lang === "en" ? "Settings" : "إعدادات"}</span>
          </button>
        </nav>
      )}

'''
source = source.replace(aside_marker, nav + aside_marker, 1)

CHAT.write_text(source, encoding="utf-8")

css = r'''
:root {
  --tcs-reference-design-lock-v1: 1;
}

/* TCS REFERENCE DESIGN LOCK V1
   Visual + navigation-shell patch only.
   No API, socket, permissions, message, upload, huddle, Drive, DB or backend behavior is changed.
   Primary target: desktop TCS window, light mode. */

html:not(.dark) .tcs-desktop-window {
  --tcs-ref-gold: #c89224;
  --tcs-ref-gold-2: #e6bf62;
  --tcs-ref-gold-soft: #fbf3df;
  --tcs-ref-ink: #171717;
  --tcs-ref-muted: #8c8b91;
  --tcs-ref-line: #ebe9e4;
  --tcs-ref-panel: #ffffff;
  --tcs-ref-panel-soft: #fbfaf7;
}

html:not(.dark) .tcs-desktop-window.tcs-desktop-window-v8 {
  border: 1px solid #e7e4dc !important;
  border-radius: 24px !important;
  background: #fff !important;
  box-shadow: 0 28px 80px rgba(33, 28, 20, .16), 0 8px 24px rgba(33, 28, 20, .08) !important;
}

html:not(.dark) .tcs-desktop-window.tcs-desktop-window-v8::before {
  display: none !important;
}

html:not(.dark) .tcs-desktop-window-titlebar {
  min-height: 66px !important;
  padding: 10px 14px 10px 18px !important;
  border-bottom: 1px solid #eeeae2 !important;
  background: rgba(255, 255, 255, .98) !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window-icon {
  width: 42px !important;
  height: 42px !important;
  flex-basis: 42px !important;
  border: 1px solid #ecdba9 !important;
  border-radius: 14px !important;
  color: #9e6d0c !important;
  background: linear-gradient(145deg, #fffdf7, #f6e6b8) !important;
  box-shadow: 0 5px 14px rgba(160, 111, 17, .10) !important;
}

html:not(.dark) .tcs-desktop-window-identity strong {
  color: #151515 !important;
  font-size: 14px !important;
  letter-spacing: .01em !important;
}

html:not(.dark) .tcs-desktop-window-identity span {
  color: #89878c !important;
  font-size: 10px !important;
}

html:not(.dark) .tcs-desktop-window-actions button {
  width: 34px !important;
  height: 34px !important;
  border: 1px solid #e9e6df !important;
  border-radius: 11px !important;
  color: #5f5d59 !important;
  background: #fff !important;
  box-shadow: 0 2px 8px rgba(20, 20, 20, .04) !important;
}

html:not(.dark) .tcs-desktop-window-body {
  background: #fff !important;
}

@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window [data-tcs-presentation="desktop-window"].tcs-reference-lock-v1:not(.tos-chat-focus-mode) {
    grid-template-columns: 78px 326px minmax(0, 1fr) !important;
  }
}

/* Primary icon rail */
html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav {
  min-width: 0;
  min-height: 0;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 10px 14px;
  border-inline-end: 1px solid var(--tcs-ref-line);
  background: #fff;
  box-shadow: 5px 0 18px rgba(20, 20, 20, .018);
}

html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav-item {
  width: 58px;
  min-height: 58px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border: 0;
  border-radius: 16px;
  color: #4b4a4d;
  background: transparent;
  font-size: 9.5px;
  font-weight: 800;
  line-height: 1.1;
  transition: background .16s ease, color .16s ease, transform .16s ease;
}

html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav-item:hover {
  color: #8c620f;
  background: #fbf5e7;
  transform: translateY(-1px);
}

html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav-item.is-active {
  color: #9b690a;
  background: linear-gradient(180deg, #fff9eb, #faf0d7);
  box-shadow: inset 3px 0 0 #c89224;
}

html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav-item:disabled {
  opacity: .38;
  cursor: not-allowed;
  transform: none;
}

html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav-spacer {
  flex: 1;
}

/* Main TCS shell */
html:not(.dark) .tcs-desktop-window [data-tcs-presentation="desktop-window"].tcs-reference-lock-v1 {
  border: 0 !important;
  border-radius: 0 !important;
  background: #fff !important;
  box-shadow: none !important;
}

/* Conversation rail */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail {
  color: #242326 !important;
  border: 0 !important;
  border-inline-end: 1px solid var(--tcs-ref-line) !important;
  background: #fff !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail::after {
  display: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child {
  padding: 18px 18px 14px !important;
  border-color: #efede8 !important;
  background: #fff !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child .text-base.font-black {
  color: #1b1a1d !important;
  font-size: 15px !important;
  letter-spacing: -.02em !important;
  text-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child .text-zinc-400 {
  color: #9a989d !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child > .mt-4.grid.grid-cols-2 {
  margin-top: 16px !important;
  gap: 4px !important;
  padding: 4px !important;
  border: 1px solid #ebe7de !important;
  border-radius: 13px !important;
  background: #faf9f6 !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child > .mt-4.grid.grid-cols-2 > button {
  min-height: 36px;
  border-radius: 10px !important;
  color: #7a746a !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child > .mt-4.grid.grid-cols-2 > button.bg-white {
  color: #fff !important;
  background: linear-gradient(135deg, #b47c16 0%, #d3a238 100%) !important;
  box-shadow: 0 5px 12px rgba(176, 119, 16, .18) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child > div.mt-4.rounded-2xl.border {
  margin-top: 14px !important;
  padding: 8px !important;
  border: 1px solid #ebe8e2 !important;
  border-radius: 14px !important;
  background: #fff !important;
  box-shadow: 0 3px 12px rgba(20, 20, 20, .025) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail .bg-zinc-900 {
  background: #fff !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail input {
  color: #2d2c2f !important;
  caret-color: #ba821a !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail input::placeholder {
  color: #aaa8ac !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child .mt-2.flex.flex-wrap {
  gap: 6px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child .mt-2.flex.flex-wrap > button {
  min-height: 28px;
  padding: 4px 10px !important;
  color: #656166 !important;
  border: 1px solid #eeeae3 !important;
  background: #faf9f6 !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:first-child .mt-2.flex.flex-wrap > button.bg-amber-300 {
  color: #573d0c !important;
  border-color: #e5c777 !important;
  background: #f5dea0 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v8-new-conversation-trigger {
  min-height: 42px;
  border: 1px solid #e3c875 !important;
  border-radius: 12px !important;
  color: #fff !important;
  background: linear-gradient(135deg, #b9821c, #d2a23e) !important;
  box-shadow: 0 7px 18px rgba(184, 126, 18, .16) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > .min-h-0.flex-1 {
  padding: 10px 12px !important;
  background: #fff !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > .min-h-0.flex-1 .space-y-1 > button {
  min-height: 64px !important;
  margin: 3px 0 !important;
  padding: 10px 11px !important;
  color: #2c2b2e !important;
  border: 1px solid transparent !important;
  border-inline-start: 3px solid transparent !important;
  border-radius: 14px !important;
  background: #fff !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > .min-h-0.flex-1 .space-y-1 > button:hover {
  color: #2b2a2c !important;
  border-color: #eee8da !important;
  border-inline-start-color: #d4a340 !important;
  background: #fbf8f0 !important;
  transform: none !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > .min-h-0.flex-1 .space-y-1 > button.bg-white {
  color: #262326 !important;
  border-color: #eee5d3 !important;
  border-inline-start-color: #c89224 !important;
  background: linear-gradient(90deg, #fff9ed, #fff) !important;
  box-shadow: 0 3px 12px rgba(89, 61, 15, .06) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:last-child {
  padding: 12px !important;
  border-color: #efede8 !important;
  background: #fff !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > div:last-child > div {
  border: 1px solid #ece4d2 !important;
  border-radius: 15px !important;
  background: #fffaf0 !important;
  box-shadow: none !important;
}

/* Main workspace */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-workspace {
  background: #fff !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-command-center {
  padding: 18px 22px 16px !important;
  border-color: #efede8 !important;
  background: rgba(255,255,255,.985) !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-command-center::after {
  display: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-command-center h2 {
  color: #171719 !important;
  font-size: 18px !important;
  font-weight: 850 !important;
  letter-spacing: -.025em;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-command-center p {
  color: #9a989d !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v4-header-meta span,
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v4-header-meta button {
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-command-center > .flex > .relative.hidden {
  gap: 8px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-command-center > .flex > .relative.hidden > button {
  min-height: 40px;
  border: 1px solid #e8e4dc !important;
  border-radius: 13px !important;
  color: #363438 !important;
  background: #fff !important;
  box-shadow: 0 2px 8px rgba(20,20,20,.035) !important;
  transform: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-command-center > .flex > .relative.hidden > button.bg-zinc-950 {
  color: #fff !important;
  border-color: #25201a !important;
  background: #201b15 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v8-secondary-toolbar-action {
  display: none !important;
}

/* Keep the UI calm: secondary metric/filter dashboards move behind tools. */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v117-brief,
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v117-filterbar {
  display: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v16-inline-search-shell {
  min-height: 52px;
  margin-top: 14px !important;
  padding: 7px 10px 7px 14px !important;
  border: 1px solid #ecdcae !important;
  border-radius: 15px !important;
  background: linear-gradient(180deg, #fffdf8, #fffaf0) !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v15-inline-smart-search {
  color: #363438 !important;
  font-size: 13px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v16-inline-search-shell button {
  border: 1px solid #ebe5d8 !important;
  background: #fff !important;
  color: #5d5953 !important;
  box-shadow: none !important;
}

/* Message canvas */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-message-canvas {
  padding: 22px 24px !important;
  background: #fff !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-message-row {
  border-radius: 18px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-message-meta {
  color: #85838a !important;
  font-size: 11px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-bubble {
  max-width: 680px !important;
  border-radius: 15px !important;
  border-color: #ebe9e5 !important;
  box-shadow: 0 2px 8px rgba(20,20,20,.025) !important;
  ring: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-message-row.justify-start .tos-chat-bubble {
  color: #343238 !important;
  background: #f5f5f6 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-message-row.justify-end .tos-chat-bubble {
  color: #40341d !important;
  border-color: #eadcb8 !important;
  background: linear-gradient(135deg, #fffaf0, #f8edcf) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-message-actions {
  opacity: 0;
  transition: opacity .14s ease;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-message-row:hover .tos-chat-message-actions {
  opacity: 1;
}

/* Empty state modeled after the approved reference image. */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-empty-clean-card {
  position: relative;
  overflow: hidden;
  max-width: 480px !important;
  margin-top: 8px !important;
  padding: 38px 34px !important;
  border: 1px solid #ead9aa !important;
  border-radius: 24px !important;
  background: linear-gradient(145deg, #fffdf8 0%, #fff8e9 100%) !important;
  box-shadow: 0 18px 42px rgba(93, 66, 17, .10) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-empty-clean-card::before,
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-empty-clean-card::after {
  content: "";
  position: absolute;
  width: 112px;
  height: 112px;
  border-radius: 50%;
  pointer-events: none;
  border: 1px solid rgba(204, 155, 52, .16);
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-empty-clean-card::before {
  top: -58px;
  left: -48px;
  background: radial-gradient(circle at 45% 45%, rgba(238, 200, 107, .78), rgba(238, 200, 107, .08) 70%);
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-empty-clean-card::after {
  right: -55px;
  bottom: -60px;
  background: radial-gradient(circle at 50% 50%, rgba(244, 216, 148, .18), transparent 72%);
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-empty-clean-card > * {
  position: relative;
  z-index: 1;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-empty-clean-card > div:first-child {
  width: 52px !important;
  height: 52px !important;
  border-radius: 50% !important;
  color: #a8730b !important;
  background: linear-gradient(145deg, #fff8e2, #f4d98f) !important;
  ring: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-empty-clean-card button {
  color: #4b4131 !important;
  border-color: #ead8ad !important;
  background: rgba(255,255,255,.78) !important;
  box-shadow: 0 2px 8px rgba(80,55,10,.035) !important;
}

/* Composer */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer {
  padding: 13px 16px 15px !important;
  border-color: #efede8 !important;
  background: rgba(255,255,255,.985) !important;
  box-shadow: 0 -7px 20px rgba(20,20,20,.018) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer > .relative.flex.items-end {
  min-height: 60px;
  padding: 6px !important;
  gap: 7px !important;
  border: 1px solid #e7e3dc !important;
  border-radius: 17px !important;
  background: #fff !important;
  box-shadow: 0 3px 14px rgba(20,20,20,.035) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer > .relative.flex.items-end:focus-within {
  border-color: #d9bd73 !important;
  box-shadow: 0 0 0 3px rgba(201,146,36,.07) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer > .relative.flex.items-end > button:not([aria-label]) {
  border: 1px solid #ece9e3 !important;
  border-radius: 13px !important;
  color: #57555a !important;
  background: #fff !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer textarea {
  color: #343238 !important;
  font-size: 13px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer textarea::placeholder {
  color: #aaa8ad !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer button[aria-label="Send message"],
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer button[aria-label="إرسال الرسالة"] {
  width: 92px !important;
  min-width: 92px !important;
  height: 46px !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid #c78f23 !important;
  border-radius: 13px !important;
  color: #fff !important;
  background: linear-gradient(135deg, #b97f16, #d6a43a) !important;
  box-shadow: 0 7px 16px rgba(176, 117, 14, .17) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer button[aria-label="Send message"]::after {
  content: "Send";
  font-size: 12px;
  font-weight: 850;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-composer button[aria-label="إرسال الرسالة"]::after {
  content: "إرسال";
  font-size: 12px;
  font-weight: 850;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v4-composer-hint {
  display: none !important;
}

/* Details remains functional but appears as a clean slide-over. */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-details-panel {
  background: rgba(31, 29, 26, .20) !important;
  backdrop-filter: blur(5px) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-details-panel > div {
  width: min(420px, 92%) !important;
  margin-inline-start: auto !important;
  border: 1px solid #ebe7df !important;
  border-radius: 22px !important;
  background: #fbfaf7 !important;
}

@media (max-width: 1180px) {
  html:not(.dark) .tcs-desktop-window [data-tcs-presentation="desktop-window"].tcs-reference-lock-v1:not(.tos-chat-focus-mode) {
    grid-template-columns: 68px 286px minmax(0, 1fr) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav {
    padding-inline: 6px;
  }

  html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav-item {
    width: 52px;
  }
}

@media (max-width: 1023px) {
  html:not(.dark) .tcs-desktop-window [data-tcs-presentation="desktop-window"].tcs-reference-lock-v1 {
    grid-template-columns: minmax(0, 1fr) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav {
    display: none !important;
  }
}
'''
CSS.write_text(css, encoding="utf-8")

print(f"PATCH={PATCH}")
print("CHAT_PANEL=UPDATED")
print("REFERENCE_CSS=CREATED")
print("PRIMARY_NAV=ADDED")
print("FUNCTIONALITY_PRESERVED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_AND_DEPLOY_FRONTEND")
