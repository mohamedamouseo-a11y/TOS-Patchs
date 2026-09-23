#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-EXECUTIVE-LUXURY-MOCKUP-V4"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsExecutiveLuxuryMockupV4.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# Load V4 visual layer after the newest known TCS stylesheet.
css_import = 'import "./tcsExecutiveLuxuryMockupV4.css";'
if css_import not in src:
    anchors = [
        'import "./tcsProfessionalChatHeaderV3_2FinalPolish.css";',
        'import "./tcsProfessionalChatHeaderV3_1.css";',
        'import "./tcsProfessionalChatHeaderV3.css";',
        'import "./tcsPremiumChatShellV2_3Clean.css";',
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
        raise SystemExit(f"{PATCH}: no TCS CSS import anchor found")

# Stable design hook.
if "tcs-executive-luxury-v4" not in src:
    root_anchor = 'className={`tos-chat-modern-shell '
    if root_anchor not in src:
        raise SystemExit(f"{PATCH}: root class anchor not found")
    src = src.replace(root_anchor, 'className={`tos-chat-modern-shell tcs-executive-luxury-v4 ', 1)

# Upgrade the desktop direct-conversation list to match the approved mockup:
# avatar/initials + title + preview + time + unread.
old_list = '''              <div className="space-y-1">
                {visibleConversations.map((conversation) => (
                  <button key={conversation.id} type="button" onClick={() => { closeHuddle(); setActiveConversationId(conversation.id); resetMessageContext(); }} className={`flex w-full items-center justify-between rounded-2xl px-3 py-2.5 text-right text-sm font-black transition ${activeConversationId === conversation.id ? "bg-white text-zinc-950 shadow-sm" : "text-zinc-300 hover:bg-white/10"}`}>
                    <span className="tcs-ref-conversation-title" title={conversationTitle(conversation, user?.id)}>{conversationTitle(conversation, user?.id)}</span>
                    {(conversation.unreadCount || 0) > 0 && <span className="rounded-full bg-red-500 px-2 py-0.5 text-[10px] text-white">{conversation.unreadCount}</span>}
                  </button>
                ))}
                {sideLoading && <div className="px-3 py-2 text-xs text-zinc-500">{ui.loading}</div>}
              </div>'''

new_list = '''              <div className="tcs-v4-conversation-list space-y-1">
                {visibleConversations.map((conversation) => {
                  const title = conversationTitle(conversation, user?.id);
                  const preview = conversationLastPreview(conversation);
                  const time = conversationLastTime(conversation);
                  const initials = String(title || "T").split(/\\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
                  return (
                    <button key={conversation.id} type="button" onClick={() => { closeHuddle(); setActiveConversationId(conversation.id); resetMessageContext(); }} className={`tcs-v4-conversation-row ${activeConversationId === conversation.id ? "is-active" : ""}`}>
                      <span className="tcs-v4-conversation-avatar">{initials || "T"}</span>
                      <span className="tcs-v4-conversation-copy">
                        <span className="tcs-v4-conversation-title" title={title}>{title}</span>
                        <span className="tcs-v4-conversation-preview">{preview}</span>
                      </span>
                      <span className="tcs-v4-conversation-side">
                        {time && <span className="tcs-v4-conversation-time">{time}</span>}
                        {(conversation.unreadCount || 0) > 0 && <span className="tcs-v4-unread">{conversation.unreadCount}</span>}
                      </span>
                    </button>
                  );
                })}
                {sideLoading && <div className="px-3 py-2 text-xs text-zinc-500">{ui.loading}</div>}
              </div>'''

if "tcs-v4-conversation-list" not in src:
    if old_list not in src:
        raise SystemExit(f"{PATCH}: desktop conversation list anchor not found")
    src = src.replace(old_list, new_list, 1)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-executive-luxury-mockup-v4: 1; }

/* =========================================================
   TCS Executive Luxury Mockup V4
   Reference: approved premium cream/ivory/gold desktop mockup.
   Visual hierarchy first, gold as accent only.
   ========================================================= */

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 {
  --v4-bg: #fbfaf7;
  --v4-surface: #ffffff;
  --v4-surface-soft: #f8f6f1;
  --v4-line: #e9e3d7;
  --v4-line-strong: #dec98e;
  --v4-gold: #c99122;
  --v4-gold-dark: #9c6810;
  --v4-gold-soft: #fff7e5;
  --v4-ink: #1c1b19;
  --v4-muted: #817a70;
  --v4-green: #1cb77b;
  background: #fff !important;
  border-color: #e6e1d8 !important;
  border-radius: 22px !important;
  box-shadow: 0 18px 50px rgba(52, 43, 27, .10) !important;
}

/* Main desktop proportions from the reference. */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4:not(.tos-chat-focus-mode) {
    grid-template-columns: 58px 330px minmax(0, 1fr) !important;
  }
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 58px 300px minmax(360px, 1fr) 310px !important;
  }
}

/* Mini app rail */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-ref-primary-nav {
  padding: 13px 6px !important;
  border-inline-end: 1px solid var(--v4-line) !important;
  background: #fbfaf8 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-ref-primary-nav-item {
  width: 46px !important;
  min-height: 52px !important;
  margin-bottom: 7px !important;
  border-radius: 13px !important;
  color: #8a847b !important;
  font-size: 8px !important;
  box-shadow: none !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-ref-primary-nav-item.is-active {
  background: var(--v4-gold-soft) !important;
  color: var(--v4-gold-dark) !important;
  box-shadow: inset 3px 0 0 var(--v4-gold) !important;
}

/* Conversation rail */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail {
  background: #fff !important;
  border-inline-end: 1px solid var(--v4-line) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail > div:first-child {
  padding: 17px 16px 13px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail input {
  min-height: 42px !important;
  border: 1px solid var(--v4-line) !important;
  border-radius: 11px !important;
  background: #fff !important;
  box-shadow: none !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail input:focus {
  border-color: #d8bc75 !important;
  box-shadow: 0 0 0 3px rgba(201,145,34,.08) !important;
}

/* Project / Direct toggle */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail .grid.grid-cols-2 {
  gap: 3px !important;
  padding: 3px !important;
  border: 1px solid var(--v4-line) !important;
  border-radius: 11px !important;
  background: #f9f7f3 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail .grid.grid-cols-2 > button {
  min-height: 36px !important;
  border: 0 !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}

/* Filter chips */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail button {
  box-shadow: none !important;
}

/* New conversation CTA */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v8-new-conversation-trigger {
  min-height: 40px !important;
  margin: 10px 0 !important;
  border: 1px solid #dcc484 !important;
  border-radius: 10px !important;
  background: linear-gradient(180deg, #fffdfa, #fff8e8) !important;
  color: #8b610d !important;
  box-shadow: 0 4px 12px rgba(120,91,31,.05) !important;
}

/* Rich conversation rows */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-list {
  display: flex !important;
  flex-direction: column !important;
  gap: 3px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row {
  display: grid !important;
  grid-template-columns: 38px minmax(0,1fr) auto !important;
  align-items: center !important;
  gap: 10px !important;
  width: 100% !important;
  min-height: 60px !important;
  padding: 8px 9px !important;
  border: 1px solid transparent !important;
  border-radius: 12px !important;
  background: transparent !important;
  color: #3a3732 !important;
  text-align: start !important;
  transition: background .15s ease, border-color .15s ease !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row:hover {
  background: #faf8f4 !important;
  border-color: #eee8dd !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row.is-active {
  background: #fff9ec !important;
  border-color: #ead5a2 !important;
  box-shadow: inset 3px 0 0 var(--v4-gold) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4[dir="rtl"] .tcs-v4-conversation-row.is-active {
  box-shadow: inset -3px 0 0 var(--v4-gold) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-avatar {
  display: grid !important;
  width: 36px !important;
  height: 36px !important;
  place-items: center !important;
  border: 1px solid #e6d5af !important;
  border-radius: 50% !important;
  background: linear-gradient(145deg, #fff9eb, #f3e7c8) !important;
  color: #9a6a14 !important;
  font-size: 10px !important;
  font-weight: 900 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-copy {
  min-width: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 3px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-title {
  min-width: 0 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  color: #2b2926 !important;
  font-size: 11px !important;
  font-weight: 850 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-preview {
  min-width: 0 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  color: #8d867c !important;
  font-size: 9.5px !important;
  font-weight: 600 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-side {
  display: flex !important;
  min-width: 48px !important;
  align-items: flex-end !important;
  flex-direction: column !important;
  gap: 5px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-time {
  color: #a59d92 !important;
  font-size: 8.5px !important;
  font-weight: 650 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-unread {
  display: grid !important;
  min-width: 18px !important;
  height: 18px !important;
  padding: 0 5px !important;
  place-items: center !important;
  border-radius: 999px !important;
  background: var(--v4-gold) !important;
  color: #fff !important;
  font-size: 8px !important;
  font-weight: 900 !important;
}

/* Main chat */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-workspace {
  min-width: 0 !important;
  background: #fff !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center {
  padding: 18px 20px 15px !important;
  border-bottom: 1px solid #eee9e0 !important;
  background: #fff !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center h1,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center h2 {
  color: var(--v4-ink) !important;
  letter-spacing: -.025em !important;
}

/* Premium utility icons */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v3-icon-action {
  width: 38px !important;
  height: 38px !important;
  min-width: 38px !important;
  min-height: 38px !important;
  border: 1px solid #e8e3da !important;
  border-radius: 11px !important;
  background: #fff !important;
  color: #5f5a54 !important;
  box-shadow: 0 4px 12px rgba(45,38,25,.04) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v3-icon-action:hover {
  border-color: #d9c18c !important;
  background: #fffaf0 !important;
  color: #8d620d !important;
}

/* Status */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v31-status-trigger {
  height: 25px !important;
  padding: 0 9px !important;
  border-color: #e7e2d8 !important;
  background: #fff !important;
  font-size: 9px !important;
}

/* Smart search */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell {
  min-height: 48px !important;
  margin-top: 11px !important;
  padding: 5px 7px !important;
  border: 1px solid #e8e2d8 !important;
  border-radius: 12px !important;
  background: #fbfaf7 !important;
  box-shadow: none !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell:focus-within {
  border-color: #d8bd79 !important;
  box-shadow: 0 0 0 3px rgba(201,145,34,.08) !important;
}

/* Empty state inspired by the approved mockup */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card {
  position: relative !important;
  max-width: 520px !important;
  padding: 46px 34px 38px !important;
  overflow: hidden !important;
  border: 1px solid #ead8ac !important;
  border-radius: 24px !important;
  background:
    radial-gradient(circle at 17% 14%, rgba(216,169,58,.25), transparent 24%),
    radial-gradient(circle at 86% 88%, rgba(227,199,131,.17), transparent 28%),
    linear-gradient(145deg, #fffefa, #fff8e9) !important;
  box-shadow: 0 22px 54px rgba(62,48,20,.08) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card::before {
  content: "";
  position: absolute;
  top: -74px;
  left: -70px;
  width: 160px;
  height: 160px;
  border: 1px solid rgba(201,145,34,.16);
  border-radius: 50%;
  box-shadow: 34px 34px 0 -1px rgba(201,145,34,.055);
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card h3 {
  position: relative;
  z-index: 1;
  font-size: 17px !important;
  letter-spacing: -.025em !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card p {
  position: relative;
  z-index: 1;
  max-width: 390px !important;
  margin-inline: auto !important;
  color: #81786d !important;
  line-height: 1.65 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card button {
  position: relative;
  z-index: 1;
  border-color: #e5d8ba !important;
  background: rgba(255,255,255,.86) !important;
  color: #5f584e !important;
  box-shadow: 0 4px 12px rgba(61,49,25,.04) !important;
}

/* More/status popovers */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v3-more-menu,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v31-status-menu {
  border-color: #e5dfd5 !important;
  background: rgba(255,255,255,.995) !important;
  box-shadow: 0 16px 38px rgba(34,28,19,.13) !important;
}

/* Inspector */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel:not(.hidden) {
    background: #f9f7f3 !important;
    border-inline-start: 1px solid var(--v4-line) !important;
  }
}

/* Google Drive footer */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail > div:last-child {
  border-top-color: #eee8de !important;
  background: linear-gradient(180deg, #fff, #fbfaf7) !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("REFERENCE=APPROVED_MOCKUP")
print("CONVERSATION_ROWS=RICH_AVATAR_PREVIEW_TIME")
print("HEADER=EXECUTIVE_PREMIUM")
print("SEARCH=PREMIUM_COMMAND_BAR")
print("EMPTY_STATE=LUXURY_REFERENCE")
print("GOLD_ACCENT=RESTRAINED")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
