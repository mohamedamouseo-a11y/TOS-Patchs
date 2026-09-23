#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-PROFESSIONAL-CHAT-HEADER-V3"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsProfessionalChatHeaderV3.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# 1) Add MoreHorizontal icon safely.
old_import = 'import { Archive, Download, Eye, FileText, FolderKanban, Image as ImageIcon, Lock, MessageCircle, Mic, MicOff, Monitor, Paperclip, Phone, PhoneOff, RefreshCw, Search, Send, Settings2, Trash2, Users, Video, VideoOff, X } from "lucide-react";'
new_import = 'import { Archive, Download, Eye, FileText, FolderKanban, Image as ImageIcon, Lock, MessageCircle, Mic, MicOff, Monitor, MoreHorizontal, Paperclip, Phone, PhoneOff, RefreshCw, Search, Send, Settings2, Trash2, Users, Video, VideoOff, X } from "lucide-react";'
if old_import in src:
    src = src.replace(old_import, new_import, 1)
elif "MoreHorizontal" not in src:
    raise SystemExit(f"{PATCH}: lucide import anchor not found")

# 2) Add V3 CSS after latest known TCS layer.
css_import = 'import "./tcsProfessionalChatHeaderV3.css";'
if css_import not in src:
    anchors = [
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
        raise SystemExit(f"{PATCH}: CSS import anchor not found")

# 3) Add stable root hook.
if "tcs-professional-chat-header-v3" not in src:
    root_anchor = 'className={`tos-chat-modern-shell '
    if root_anchor not in src:
        raise SystemExit(f"{PATCH}: root class anchor not found")
    src = src.replace(root_anchor, 'className={`tos-chat-modern-shell tcs-professional-chat-header-v3 ', 1)

# 4) Add compact status selector beside conversation metadata.
meta_anchor = '''              <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-zinc-500 dark:bg-white/10 dark:text-zinc-300">{currentChatMembers.length} {lang === "en" ? "members" : "عضو"}</span>'''
status_select = meta_anchor + '''
              <label className="tcs-v3-status-badge" title={lang === "en" ? "Conversation status" : "حالة المحادثة"}>
                <span className="tcs-v3-status-dot" />
                <select value={chatStatus} onChange={(event) => setChatStatus(event.target.value)} aria-label={lang === "en" ? "Conversation status" : "حالة المحادثة"}>
                  {chatStatusOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </label>'''
if "tcs-v3-status-badge" not in src:
    if meta_anchor not in src:
        raise SystemExit(f"{PATCH}: header meta anchor not found")
    src = src.replace(meta_anchor, status_select, 1)

# 5) Replace the desktop action area only.
#    Boundary markers are preserved; no file-tail replacement.
start_marker = '          <div className="relative hidden items-center gap-2 lg:flex">'
end_marker = '          <div className="flex items-center gap-2 rounded-2xl bg-zinc-50 p-1 dark:bg-white/5 lg:hidden">'
start = src.find(start_marker)
end = src.find(end_marker, start)
if start == -1 or end == -1:
    raise SystemExit(f"{PATCH}: desktop toolbar boundary not found")

new_toolbar = '''          <div className="tcs-v3-header-actions relative hidden items-center gap-1.5 lg:flex">
            <button
              type="button"
              onClick={() => { setWorkspaceSearchType("smart"); setWorkspaceSearchOpen(true); setToolbarOpen(false); }}
              className="tcs-v3-icon-action"
              title={lang === "en" ? "Search" : "بحث"}
              aria-label={lang === "en" ? "Search" : "بحث"}
            >
              <Search size={16} />
            </button>

            <button
              type="button"
              onClick={() => { openHuddle(); setToolbarOpen(false); }}
              disabled={!canUseHuddle}
              className="tcs-v3-icon-action"
              title={lang === "en" ? "Start call" : "بدء مكالمة"}
              aria-label={lang === "en" ? "Start call" : "بدء مكالمة"}
            >
              <Phone size={16} />
            </button>

            <button
              type="button"
              onClick={() => { setToolbarOpen(false); setDetailsTab("members"); setDetailsPanelOpen((value) => !value); }}
              disabled={focusMode}
              className={`tcs-v3-icon-action ${detailsPanelOpen ? "is-active" : ""}`}
              title={lang === "en" ? "Conversation info" : "معلومات المحادثة"}
              aria-label={lang === "en" ? "Conversation info" : "معلومات المحادثة"}
            >
              <Eye size={16} />
            </button>

            <button
              type="button"
              onClick={() => setToolbarOpen((value) => { const next = !value; if (next) setDetailsPanelOpen(false); return next; })}
              className={`tcs-v3-icon-action ${toolbarOpen ? "is-active" : ""}`}
              title={lang === "en" ? "More" : "المزيد"}
              aria-label={lang === "en" ? "More" : "المزيد"}
              aria-expanded={toolbarOpen}
            >
              <MoreHorizontal size={18} />
            </button>

            {toolbarOpen && (
              <div className="tcs-v3-more-menu" role="menu" aria-label={lang === "en" ? "More conversation actions" : "إجراءات إضافية للمحادثة"}>
                <button type="button" role="menuitem" onClick={() => { setFocusMode((value) => !value); setToolbarOpen(false); }}>
                  <Eye size={14} />
                  <span>{focusMode ? (lang === "en" ? "Exit focus mode" : "إنهاء وضع التركيز") : (lang === "en" ? "Focus mode" : "وضع التركيز")}</span>
                </button>

                <button type="button" role="menuitem" onClick={() => { setShowSmartPanel((value) => !value); setToolbarOpen(false); }}>
                  <MessageCircle size={14} />
                  <span>{showSmartPanel ? (lang === "en" ? "Hide chat summary" : "إخفاء ملخص الشات") : (lang === "en" ? "Chat summary" : "ملخص الشات")}</span>
                </button>

                <button type="button" role="menuitem" onClick={() => { copyChatBrief(); setToolbarOpen(false); }}>
                  <MessageCircle size={14} />
                  <span>{lang === "en" ? "Copy summary" : "نسخ الملخص"}</span>
                </button>

                <button type="button" role="menuitem" onClick={() => { exportChatCsv(); setToolbarOpen(false); }}>
                  <Download size={14} />
                  <span>{lang === "en" ? "Export conversation" : "تصدير المحادثة"}</span>
                </button>

                <button type="button" role="menuitem" onClick={() => { setMessageDensity((value) => value === "compact" ? "comfortable" : "compact"); setToolbarOpen(false); }}>
                  <Settings2 size={14} />
                  <span>{messageDensity === "compact" ? (lang === "en" ? "Comfortable spacing" : "مسافات مريحة") : (lang === "en" ? "Compact spacing" : "مسافات مضغوطة")}</span>
                </button>

                {!isDirectMode && (
                  <button type="button" role="menuitem" onClick={() => { setMeetingModalOpen(true); setToolbarOpen(false); }} disabled={!canProjectInteract || meetingLoading}>
                    <MessageCircle size={14} />
                    <span>{lang === "en" ? "Meeting link" : "رابط اجتماع"}</span>
                  </button>
                )}

                {!isDirectMode && activeChannel?.id && canManageChat && (
                  <>
                    <div className="tcs-v3-menu-divider" />
                    <div className="tcs-v3-menu-label">{lang === "en" ? "Channel controls" : "إدارة القناة"}</div>
                    <button type="button" role="menuitem" onClick={() => { toggleChannelLock(); setToolbarOpen(false); }}>
                      <Lock size={14} />
                      <span>{activeChannelLocked ? (lang === "en" ? "Unlock channel" : "فتح القناة") : (lang === "en" ? "Lock channel" : "قفل القناة")}</span>
                    </button>
                    <button type="button" role="menuitem" onClick={() => toggleChannelPermission("memberCanSend")}>
                      <Send size={14} />
                      <span>{lang === "en" ? "Toggle member sending" : "صلاحية إرسال الأعضاء"}</span>
                    </button>
                    <button type="button" role="menuitem" onClick={() => toggleChannelPermission("memberCanUpload")}>
                      <FileText size={14} />
                      <span>{lang === "en" ? "Toggle member files" : "صلاحية ملفات الأعضاء"}</span>
                    </button>
                    <button type="button" role="menuitem" onClick={() => toggleChannelPermission("memberCanReact")}>
                      <MessageCircle size={14} />
                      <span>{lang === "en" ? "Toggle reactions" : "صلاحية التفاعلات"}</span>
                    </button>
                  </>
                )}
              </div>
            )}
          </div>

'''
src = src[:start] + new_toolbar + src[end:]

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-professional-chat-header-v3: 1; }

/* =========================================================
   TCS Professional Chat Header V3
   Familiar professional chat pattern:
   Search | Call | Info | More
   Status lives beside conversation identity.
   More is a small utility menu, never a dashboard panel.
   ========================================================= */

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-header-actions {
  flex: 0 0 auto;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-icon-action {
  display: inline-grid;
  width: 36px;
  height: 36px;
  min-width: 36px !important;
  min-height: 36px !important;
  padding: 0 !important;
  place-items: center;
  border: 1px solid #e8e4dc !important;
  border-radius: 10px !important;
  background: #fff !important;
  color: #69635c !important;
  box-shadow: none !important;
  transition: background .15s ease, border-color .15s ease, color .15s ease;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-icon-action:hover {
  border-color: #dcc78f !important;
  background: #fffaf0 !important;
  color: #8f620b !important;
  transform: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-icon-action.is-active {
  border-color: #d6b76e !important;
  background: #fbf3df !important;
  color: #96680f !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-icon-action:disabled {
  opacity: .4;
  cursor: not-allowed;
}

/* Conversation status becomes a compact inline badge/select. */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 24px;
  padding: 0 7px;
  border: 1px solid #e8e4dc;
  border-radius: 999px;
  background: #fff;
  color: #666159;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-status-dot {
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #c99122;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-status-badge select {
  max-width: 112px;
  appearance: none;
  border: 0;
  outline: 0;
  background: transparent;
  color: inherit;
  font-size: 9px;
  font-weight: 800;
  cursor: pointer;
}

/* More menu: narrow vertical utility menu attached to the ellipsis. */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu {
  position: absolute;
  top: 43px;
  inset-inline-end: 0;
  z-index: 50;
  width: 228px;
  padding: 6px;
  border: 1px solid #e5e1d9;
  border-radius: 12px;
  background: rgba(255,255,255,.995);
  box-shadow: 0 14px 36px rgba(31,26,18,.14);
  text-align: start;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu::before {
  content: "";
  position: absolute;
  top: -5px;
  inset-inline-end: 13px;
  width: 9px;
  height: 9px;
  transform: rotate(45deg);
  border-left: 1px solid #e5e1d9;
  border-top: 1px solid #e5e1d9;
  background: #fff;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu > button {
  display: flex;
  width: 100%;
  min-height: 34px;
  align-items: center;
  gap: 9px;
  padding: 7px 9px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #4d4841;
  font-size: 10px;
  font-weight: 750;
  text-align: start;
  box-shadow: none;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu > button:hover {
  background: #f7f5f1;
  color: #8d620d;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu > button:disabled {
  opacity: .4;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-menu-divider {
  height: 1px;
  margin: 5px 3px;
  background: #eeeae3;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-menu-label {
  padding: 3px 9px 4px;
  color: #a29b92;
  font-size: 8px;
  font-weight: 850;
  text-transform: uppercase;
  letter-spacing: .06em;
}

/* Kill old toolbar dashboard visual if an old selector survives elsewhere. */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v16-tools-menu {
  display: none !important;
}

/* Header spacing more like a chat app. */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tos-chat-command-center {
  padding-block: 13px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tos-chat-v4-header-meta {
  margin-top: 7px !important;
  gap: 6px !important;
}

/* The inline smart search remains the primary visible search field. */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v16-inline-search-shell {
  margin-top: 10px !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("HEADER=SEARCH_CALL_INFO_MORE")
print("OLD_CHAT_TOOLS_PANEL=REMOVED")
print("MORE_MENU=COMPACT_VERTICAL")
print("STATUS=INLINE_BADGE_SELECT")
print("INSPECTOR=INFO_BUTTON")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
