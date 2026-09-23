#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-EXECUTIVE-LUXURY-FINAL-REFERENCE-LOCK-V4_5"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsExecutiveLuxuryFinalReferenceLockV4_5.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

css_import = 'import "./tcsExecutiveLuxuryFinalReferenceLockV4_5.css";'
if css_import not in src:
    anchors = [
        'import "./tcsExecutiveLuxuryReferenceLockV4_4.css";',
        'import "./tcsExecutiveLuxuryReferenceLockV4_3.css";',
        'import "./tcsExecutiveLuxuryReferenceLockV4_2.css";',
        'import "./tcsExecutiveLuxuryReferenceLockV4_1.css";',
        'import "./tcsExecutiveLuxuryMockupV4.css";',
    ]
    for anchor in anchors:
        if anchor in src:
            src = src.replace(anchor, anchor + "\n" + css_import, 1)
            break
    else:
        raise SystemExit(f"{PATCH}: V4 stylesheet anchor not found")

# Close details/tools/status when direct-chat has no selected conversation.
effect_anchor = '  const isDirectMode = mode === "direct";'
effect_code = '''  const isDirectMode = mode === "direct";
  useEffect(() => {
    if (!isDirectMode || activeConversationId) return;
    if (detailsPanelOpen) setDetailsPanelOpen(false);
    if (toolbarOpen) setToolbarOpen(false);
    if (statusMenuOpen) setStatusMenuOpen(false);
  }, [isDirectMode, activeConversationId, detailsPanelOpen, toolbarOpen, statusMenuOpen]);'''
if "TCS_V4_5_EMPTY_DIRECT_GUARD" not in src:
    if effect_anchor not in src:
        raise SystemExit(f"{PATCH}: isDirectMode anchor not found")
    effect_code = effect_code.replace(
        '  useEffect(() => {',
        '  // TCS_V4_5_EMPTY_DIRECT_GUARD\n  useEffect(() => {',
        1
    )
    src = src.replace(effect_anchor, effect_code, 1)

# Hide members count + status when no direct conversation exists.
old_members = '''              <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-zinc-500 dark:bg-white/10 dark:text-zinc-300">{currentChatMembers.length} {lang === "en" ? "members" : "عضو"}</span>
              <div className="tcs-v31-status-control" data-status={chatStatus}>'''
new_members = '''              {(!isDirectMode || activeConversationId) && <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-zinc-500 dark:bg-white/10 dark:text-zinc-300">{currentChatMembers.length} {lang === "en" ? "members" : "عضو"}</span>}
              {(!isDirectMode || activeConversationId) && <div className="tcs-v31-status-control" data-status={chatStatus}>'''
if old_members in src:
    src = src.replace(old_members, new_members, 1)
    close_anchor = '''              </div>
              {unreadMessagesCount > 0 && <button'''
    if close_anchor not in src:
        raise SystemExit(f"{PATCH}: status close anchor not found")
    src = src.replace(
        close_anchor,
        '''              </div>}
              {unreadMessagesCount > 0 && <button''',
        1
    )
elif '(!isDirectMode || activeConversationId) && <div className="tcs-v31-status-control"' not in src:
    raise SystemExit(f"{PATCH}: members/status anchor not found")

# Keep Search always visible, but only show call/info/more when there is a real direct conversation.
call_anchor = '''            <button
              type="button"
              onClick={() => { setStatusMenuOpen(false); openHuddle(); setToolbarOpen(false); }}'''
if "{(!isDirectMode || activeConversationId) && <>" not in src:
    if call_anchor not in src:
        raise SystemExit(f"{PATCH}: header action anchor not found")
    src = src.replace(call_anchor, '''            {(!isDirectMode || activeConversationId) && <>
            <button
              type="button"
              onClick={() => { setStatusMenuOpen(false); openHuddle(); setToolbarOpen(false); }}''', 1)

    menu_end = '''            )}
          </div>

          <div className="flex items-center gap-2 rounded-2xl bg-zinc-50 p-1 dark:bg-white/5 lg:hidden">'''
    if menu_end not in src:
        raise SystemExit(f"{PATCH}: desktop action close anchor not found")
    src = src.replace(menu_end, '''            )}
            </>}
          </div>

          <div className="flex items-center gap-2 rounded-2xl bg-zinc-50 p-1 dark:bg-white/5 lg:hidden">''', 1)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-executive-luxury-final-reference-lock-v4-5: 1; }

/* V4.5 final reference lock.
   Finishes the premium empty-chat composition and inspector styling. */

/* Empty direct header should look intentional, not like a zero-state conversation. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v4-header-meta {
  min-height: 24px !important;
}

/* Stronger title/subtitle hierarchy. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center h2 {
  font-size: 18px !important;
  font-weight: 900 !important;
  letter-spacing: -.03em !important;
  color: #171614 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center h2 + span,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center p {
  color: #8a8379 !important;
}

/* Conversation rail: richer spacing and hover. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-list {
  padding: 2px 4px 4px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row {
  min-height: 69px !important;
  border-radius: 14px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row:hover {
  background: linear-gradient(180deg,#fff,#faf7f0) !important;
  border-color: #e9e1d4 !important;
}

/* Search action gets subtle dimensionality rather than a flat gold slab. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell > button:last-child {
  background:
    linear-gradient(180deg,#f1d998 0%,#dfb954 100%) !important;
  border-color: #d0ad5b !important;
  color: #62430a !important;
  box-shadow:
    0 7px 16px rgba(145,103,20,.13),
    inset 0 1px 0 rgba(255,255,255,.5) !important;
}

/* Center hero: closer to approved mockup proportions. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card {
  width: min(100%, 550px) !important;
  max-width: 550px !important;
  padding: 56px 44px 42px !important;
  border-radius: 30px !important;
  background:
    radial-gradient(circle at 10% 8%, rgba(214,161,43,.27), transparent 23%),
    radial-gradient(circle at 91% 91%, rgba(229,200,129,.17), transparent 28%),
    linear-gradient(145deg,#fffefa 0%,#fff8e9 100%) !important;
  box-shadow:
    0 30px 72px rgba(64,49,20,.095),
    inset 0 1px 0 rgba(255,255,255,.95) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon {
  margin-bottom: 32px !important;
}

/* Inspector tabs: remove the harsh black active tab from the legacy layer. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:first-child .mt-2\.5.grid.grid-cols-3 button {
  min-height: 30px !important;
  border: 1px solid transparent !important;
  background: transparent !important;
  color: #746d64 !important;
  font-size: 8.8px !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:first-child .mt-2\.5.grid.grid-cols-3 button[class*="bg-zinc-950"] {
  border-color: #d9bd78 !important;
  background: linear-gradient(180deg,#fff8e6,#f2dfad) !important;
  color: #845b0c !important;
  box-shadow: 0 5px 12px rgba(137,96,17,.07) !important;
}

/* Inspector KPI chips become restrained ivory metrics. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:first-child .grid.grid-cols-3.text-center > span {
  border: 1px solid #ece5d9 !important;
  background: #fbfaf7 !important;
  color: #6f685f !important;
}

/* All-member rows become calmer and more premium. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel button[class*="rounded-xl"][class*="bg-zinc-50"] {
  border: 1px solid #eee7dc !important;
  background: #fff !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel button[class*="rounded-xl"][class*="bg-zinc-50"]:hover {
  border-color: #ddc98e !important;
  background: #fffaf0 !important;
}

/* Canvas subtle texture stays visible while remaining premium. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-message-canvas {
  background:
    radial-gradient(circle at 14% 12%, rgba(199,148,33,.045) 0 1px, transparent 1.4px) 0 0/20px 20px,
    radial-gradient(circle at 88% 88%, rgba(211,171,77,.055), transparent 25%),
    linear-gradient(180deg,#fff 0%,#fdfcf8 100%) !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=CSS_PLUS_SMALL_UI_GUARDS")
print("EMPTY_DIRECT_META=HIDDEN")
print("EMPTY_DIRECT_ACTIONS=SEARCH_ONLY")
print("EMPTY_DIRECT_INSPECTOR=AUTO_CLOSE")
print("INSPECTOR_ACTIVE_TAB=GOLD_PREMIUM")
print("EMPTY_HERO=FINAL_REFERENCE")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
