#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import re, shutil, sys

PATCH = "TCS-UNIFIED-CHAT-INSPECTOR-V2"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsUnifiedInspectorV2.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# Import isolated V2 styling after the latest available TCS reference stylesheet.
css_import = 'import "./tcsUnifiedInspectorV2.css";'
if css_import not in src:
    anchors = [
        'import "./tcsReferencePolishV1_3.css";',
        'import "./tcsReferencePolishV1_2.css";',
        'import "./tcsReferencePolishV1_1.css";',
        'import "./tcsReferenceLockV1.css";',
    ]
    for anchor in anchors:
        if anchor in src:
            src = src.replace(anchor, anchor + "\n" + css_import, 1)
            break
    else:
        raise SystemExit(f"{PATCH}: no TCS CSS import anchor found")

# Stable V2 root hook.
if "tcs-unified-inspector-v2" not in src:
    src = src.replace(
        'className={`tos-chat-modern-shell ',
        'className={`tos-chat-modern-shell tcs-unified-inspector-v2 ',
        1,
    )

# The inline smart search already exists, so remove the duplicate header Search button.
header_search = '''            <button type="button" onClick={() => { setWorkspaceSearchType("smart"); setWorkspaceSearchOpen(true); }} className="rounded-2xl border border-zinc-100 bg-white px-3 py-2.5 text-xs font-black text-zinc-700 shadow-sm transition hover:-translate-y-0.5 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200">{lang === "en" ? "Search" : "بحث"}</button>
'''
src = src.replace(header_search, "", 1)

# Replace the oversized Conversation tools panel with a compact, anchored action popover.
start = src.find('            {toolbarOpen && (')
mobile_marker = '\n          <div className="flex items-center gap-2 rounded-2xl bg-zinc-50 p-1 dark:bg-white/5 lg:hidden">'
if start == -1:
    raise SystemExit(f"{PATCH}: toolbarOpen block start not found")
end = src.find(mobile_marker, start)
if end == -1:
    raise SystemExit(f"{PATCH}: toolbarOpen block end marker not found")

compact_tools = '''            {toolbarOpen && (
              <div className="tcs-v2-tools-popover absolute top-12 z-30" role="menu" aria-label={lang === "en" ? "Chat tools" : "أدوات الشات"}>
                <div className="tcs-v2-tools-head">
                  <div>
                    <div className="tcs-v2-tools-title">{lang === "en" ? "Chat tools" : "أدوات الشات"}</div>
                    <div className="tcs-v2-tools-subtitle">{lang === "en" ? "Quick actions" : "إجراءات سريعة"}</div>
                  </div>
                  <button type="button" onClick={() => setToolbarOpen(false)} className="tcs-v2-tools-close" aria-label={lang === "en" ? "Close tools" : "إغلاق الأدوات"}><X size={14} /></button>
                </div>

                <div className="tcs-v2-tools-grid">
                  <button type="button" role="menuitem" onClick={() => { setWorkspaceSearchType("smart"); setWorkspaceSearchOpen(true); setToolbarOpen(false); }}><Search size={15} /><span>{lang === "en" ? "Search" : "بحث"}</span></button>
                  <button type="button" role="menuitem" onClick={() => { setDetailsTab("files"); setDetailsPanelOpen(true); setToolbarOpen(false); }}><FileText size={15} /><span>{lang === "en" ? "Files" : "الملفات"}</span></button>
                  <button type="button" role="menuitem" onClick={() => { setDetailsTab("tasks"); setDetailsPanelOpen(true); setToolbarOpen(false); }}><Monitor size={15} /><span>{lang === "en" ? "Tasks" : "المهام"}</span></button>
                  <button type="button" role="menuitem" onClick={() => { setDetailsTab("members"); setDetailsPanelOpen(true); setToolbarOpen(false); }}><Eye size={15} /><span>{lang === "en" ? "Details" : "التفاصيل"}</span></button>
                  <button type="button" role="menuitem" onClick={() => { setShowSmartPanel((value) => !value); setToolbarOpen(false); }}><MessageCircle size={15} /><span>{lang === "en" ? "Summary" : "الملخص"}</span></button>
                  <button type="button" role="menuitem" onClick={() => { exportChatCsv(); setToolbarOpen(false); }}><Download size={15} /><span>{lang === "en" ? "Export" : "تصدير"}</span></button>
                  <button type="button" role="menuitem" onClick={() => { setMessageDensity((value) => value === "compact" ? "comfortable" : "compact"); setToolbarOpen(false); }}><Settings2 size={15} /><span>{messageDensity === "compact" ? "Comfort" : "Compact"}</span></button>
                  <button type="button" role="menuitem" onClick={() => { openHuddle(); setToolbarOpen(false); }} disabled={!canUseHuddle}><Phone size={15} /><span>{lang === "en" ? "Call" : "مكالمة"}</span></button>
                  {!isDirectMode && <button type="button" role="menuitem" onClick={() => { setMeetingModalOpen(true); setToolbarOpen(false); }} disabled={!canProjectInteract || meetingLoading}><MessageCircle size={15} /><span>{lang === "en" ? "Meeting" : "اجتماع"}</span></button>}
                </div>

                <div className="tcs-v2-tools-status" aria-label={lang === "en" ? "Chat status" : "حالة الشات"}>
                  {chatStatusOptions.map((item) => (
                    <button key={item.value} type="button" onClick={() => setChatStatus(item.value)} className={chatStatus === item.value ? "is-active" : ""}>{item.label}</button>
                  ))}
                </div>

                {!isDirectMode && activeChannel?.id && canManageChat && (
                  <div className="tcs-v2-admin-row">
                    <button type="button" onClick={toggleChannelLock}>{activeChannelLocked ? (lang === "en" ? "Unlock" : "فتح") : (lang === "en" ? "Lock" : "قفل")}</button>
                    <button type="button" onClick={() => toggleChannelPermission("memberCanSend")}>{lang === "en" ? "Send" : "إرسال"}</button>
                    <button type="button" onClick={() => toggleChannelPermission("memberCanUpload")}>{lang === "en" ? "Files" : "ملفات"}</button>
                    <button type="button" onClick={() => toggleChannelPermission("memberCanReact")}>{lang === "en" ? "React" : "تفاعل"}</button>
                  </div>
                )}
              </div>
            )}
'''
src = src[:start] + compact_tools + src[end:]

# Ensure opening tools closes inspector, and opening inspector closes tools.
src = src.replace(
    'onClick={() => setToolbarOpen((value) => !value)}',
    'onClick={() => setToolbarOpen((value) => { const next = !value; if (next) setDetailsPanelOpen(false); return next; })}',
    1,
)
src = src.replace(
    'onClick={() => setDetailsPanelOpen((value) => !value)} disabled={focusMode}',
    'onClick={() => { setToolbarOpen(false); setDetailsPanelOpen((value) => !value); }} disabled={focusMode}',
    1,
)

# Add a semantic hook to the existing details aside; keep all existing tabs and functionality.
old_aside = 'tos-chat-details-panel tos-chat-v4-details'
if 'tcs-v2-unified-inspector' not in src:
    if old_aside not in src:
        raise SystemExit(f"{PATCH}: details aside marker not found")
    src = src.replace(old_aside, 'tos-chat-details-panel tcs-v2-unified-inspector tos-chat-v4-details', 1)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-unified-chat-inspector-v2: 1; }

/* =========================================================
   TCS Unified Chat Inspector V2
   Desktop UX rule:
   [primary nav] [conversation list] [conversation] [inspector]
   No floating full panels over the conversation.
   Chat tools remains a small anchored popover.
   ========================================================= */

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 {
  --tcs-v2-line: #ece9e3;
  --tcs-v2-soft: #fbfaf7;
  --tcs-v2-gold: #c58c20;
  --tcs-v2-ink: #1c1b1d;
}

/* CLOSED inspector: keep chat as the hero. */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2:not(.tos-chat-focus-mode) {
    grid-template-columns: 58px 232px minmax(0, 1fr) !important;
  }

  /* OPEN inspector: genuine four-column chat workspace. */
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 58px 220px minmax(260px, 1fr) 286px !important;
  }
}

/* Primary navigation is deliberately slim. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-ref-primary-nav {
  width: auto !important;
  min-width: 0 !important;
  padding: 14px 6px 12px !important;
  border-inline-end: 1px solid var(--tcs-v2-line) !important;
  background: #fff !important;
  box-shadow: none !important;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-ref-primary-nav-item {
  width: 46px !important;
  min-height: 50px !important;
  border-radius: 13px !important;
  font-size: 8.5px !important;
}

/* Conversation rail = calm list, not a dashboard. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tos-chat-v8-rail {
  border-inline-end: 1px solid var(--tcs-v2-line) !important;
  background: #fff !important;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tos-chat-v8-rail > div:first-child {
  padding: 16px 14px 12px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tos-chat-v8-rail > .min-h-0.flex-1 {
  padding: 8px 10px !important;
}

/* Main conversation remains visually dominant. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tos-chat-v8-workspace {
  min-width: 0 !important;
  background: #fff !important;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tos-chat-command-center {
  padding: 14px 18px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tos-chat-command-center > .flex > .relative.hidden {
  gap: 7px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tos-chat-command-center > .flex > .relative.hidden > button {
  min-height: 36px !important;
  padding: 8px 12px !important;
  border-radius: 11px !important;
}

/* Unified inspector: static right column on desktop, never a modal/backdrop. */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-unified-inspector:not(.hidden) {
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
    border-inline-start: 1px solid var(--tcs-v2-line) !important;
    background: var(--tcs-v2-soft) !important;
    backdrop-filter: none !important;
    box-shadow: none !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-unified-inspector:not(.hidden) > div {
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
    background: var(--tcs-v2-soft) !important;
    box-shadow: none !important;
  }

  /* Flatten nested cards so the inspector reads as one coherent panel. */
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-unified-inspector .tos-chat-detail-card {
    border: 1px solid #ece8df !important;
    border-radius: 14px !important;
    background: #fff !important;
    box-shadow: none !important;
  }
}

/* Details header/tabs should feel like a professional inspector. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-unified-inspector .tos-chat-detail-card:first-child {
  position: sticky !important;
  top: 0 !important;
  z-index: 3 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-unified-inspector .tos-chat-detail-card:first-child .grid.grid-cols-3 {
  grid-template-columns: repeat(3, minmax(0,1fr)) !important;
  gap: 4px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-unified-inspector .tos-chat-detail-card:first-child .grid.grid-cols-3 button {
  min-height: 30px !important;
  border-radius: 9px !important;
}

/* Compact anchored tools popover. */
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-popover {
  inset-inline-end: 0 !important;
  inset-inline-start: auto !important;
  width: 268px !important;
  padding: 10px !important;
  border: 1px solid #e8e2d5 !important;
  border-radius: 16px !important;
  background: rgba(255,253,248,.99) !important;
  box-shadow: 0 16px 38px rgba(33,27,17,.14) !important;
  text-align: start !important;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 2px 2px 8px;
  border-bottom: 1px solid #eee9df;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-title {
  color: var(--tcs-v2-ink);
  font-size: 12px;
  font-weight: 900;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-subtitle {
  margin-top: 2px;
  color: #9a9690;
  font-size: 9.5px;
  font-weight: 650;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-close {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border: 1px solid #ece7de;
  border-radius: 9px;
  color: #74706b;
  background: #fff;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 6px;
  padding-top: 8px;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-grid > button {
  min-height: 36px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 9px;
  border: 1px solid #ece7de;
  border-radius: 10px;
  color: #3d3934;
  background: #fff;
  font-size: 10px;
  font-weight: 800;
  text-align: start;
  box-shadow: none;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-grid > button:hover {
  border-color: #dec88e;
  color: #8d610c;
  background: #fffaf0;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-grid > button:disabled {
  opacity: .42;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-status {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #eee9df;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-status > button {
  flex: 1;
  min-width: 0;
  padding: 6px 3px;
  border: 1px solid #ece7de;
  border-radius: 8px;
  color: #817b72;
  background: #fff;
  font-size: 8.5px;
  font-weight: 800;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-tools-status > button.is-active {
  color: #fff;
  border-color: #2c2418;
  background: #2c2418;
}

html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-admin-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 4px;
  margin-top: 7px;
}
html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-admin-row > button {
  padding: 5px 2px;
  border: 1px solid #eee9df;
  border-radius: 8px;
  color: #746f68;
  background: #faf9f6;
  font-size: 8px;
  font-weight: 800;
}

/* On narrower TCS windows, inspector becomes a clean right sheet instead of destroying chat width. */
@media (max-width: 1023px) {
  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-unified-inspector:not(.hidden) {
    position: absolute !important;
    inset: 0 !important;
    z-index: 40 !important;
    display: block !important;
    padding: 8px !important;
    background: rgba(25,23,20,.14) !important;
    backdrop-filter: blur(3px) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-unified-inspector-v2 .tcs-v2-unified-inspector:not(.hidden) > div {
    width: min(340px, 94%) !important;
    height: 100% !important;
    margin-left: auto !important;
    margin-right: 0 !important;
    border: 1px solid #e9e5dc !important;
    border-radius: 16px !important;
    background: var(--tcs-v2-soft) !important;
    box-shadow: 0 18px 44px rgba(29,25,18,.18) !important;
  }
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("LAYOUT=3_COLUMN_CHAT_PLUS_INSPECTOR")
print("INSPECTOR=UNIFIED_RIGHT_COLUMN")
print("TOOLS=COMPACT_POPOVER")
print("FLOATING_FULL_PANELS=REMOVED_ON_DESKTOP")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_AND_DEPLOY_FRONTEND")
