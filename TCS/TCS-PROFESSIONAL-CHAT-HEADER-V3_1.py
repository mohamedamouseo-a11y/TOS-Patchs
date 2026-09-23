#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-PROFESSIONAL-CHAT-HEADER-V3_1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsProfessionalChatHeaderV3_1.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# Add state for custom status popover.
state_anchor = '  const [toolbarOpen, setToolbarOpen] = useState(false);'
if 'const [statusMenuOpen, setStatusMenuOpen]' not in src:
    if state_anchor not in src:
        raise SystemExit(f"{PATCH}: toolbar state anchor not found")
    src = src.replace(
        state_anchor,
        state_anchor + '\n  const [statusMenuOpen, setStatusMenuOpen] = useState(false);',
        1
    )

# Replace native select status badge with custom professional popover.
old_status = '''              <label className="tcs-v3-status-badge" title={lang === "en" ? "Conversation status" : "حالة المحادثة"}>
                <span className="tcs-v3-status-dot" />
                <select value={chatStatus} onChange={(event) => setChatStatus(event.target.value)} aria-label={lang === "en" ? "Conversation status" : "حالة المحادثة"}>
                  {chatStatusOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </label>'''

new_status = '''              <div className="tcs-v31-status-control" data-status={chatStatus}>
                <button
                  type="button"
                  className={`tcs-v31-status-trigger ${statusMenuOpen ? "is-open" : ""}`}
                  onClick={() => { setToolbarOpen(false); setStatusMenuOpen((value) => !value); }}
                  aria-haspopup="menu"
                  aria-expanded={statusMenuOpen}
                  title={lang === "en" ? "Conversation status" : "حالة المحادثة"}
                >
                  <span className="tcs-v31-status-dot" />
                  <span>{chatStatusOptions.find((item) => item.value === chatStatus)?.label || chatStatus}</span>
                  <span className="tcs-v31-status-chevron" aria-hidden="true">⌄</span>
                </button>
                {statusMenuOpen && (
                  <div className="tcs-v31-status-menu" role="menu" aria-label={lang === "en" ? "Conversation status" : "حالة المحادثة"}>
                    {chatStatusOptions.map((item) => (
                      <button
                        key={item.value}
                        type="button"
                        role="menuitemradio"
                        aria-checked={chatStatus === item.value}
                        className={chatStatus === item.value ? "is-active" : ""}
                        onClick={() => { setChatStatus(item.value); setStatusMenuOpen(false); }}
                      >
                        <span className="tcs-v31-status-option-dot" data-value={item.value} />
                        <span>{item.label}</span>
                        {chatStatus === item.value && <span className="tcs-v31-status-check">✓</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>'''

if old_status in src:
    src = src.replace(old_status, new_status, 1)
elif 'tcs-v31-status-control' not in src:
    raise SystemExit(f"{PATCH}: native status block not found")

# Opening More/Info/Search/Call closes the status popover for clean UX.
src = src.replace(
    'onClick={() => { setWorkspaceSearchType("smart"); setWorkspaceSearchOpen(true); setToolbarOpen(false); }}',
    'onClick={() => { setStatusMenuOpen(false); setWorkspaceSearchType("smart"); setWorkspaceSearchOpen(true); setToolbarOpen(false); }}',
    1
)
src = src.replace(
    'onClick={() => { openHuddle(); setToolbarOpen(false); }}',
    'onClick={() => { setStatusMenuOpen(false); openHuddle(); setToolbarOpen(false); }}',
    1
)
src = src.replace(
    'onClick={() => { setToolbarOpen(false); setDetailsTab("members"); setDetailsPanelOpen((value) => !value); }}',
    'onClick={() => { setStatusMenuOpen(false); setToolbarOpen(false); setDetailsTab("members"); setDetailsPanelOpen((value) => !value); }}',
    1
)
src = src.replace(
    'onClick={() => setToolbarOpen((value) => { const next = !value; if (next) setDetailsPanelOpen(false); return next; })}',
    'onClick={() => { setStatusMenuOpen(false); setToolbarOpen((value) => { const next = !value; if (next) setDetailsPanelOpen(false); return next; }); }}',
    1
)

css_import = 'import "./tcsProfessionalChatHeaderV3_1.css";'
if css_import not in src:
    anchor = 'import "./tcsProfessionalChatHeaderV3.css";'
    if anchor not in src:
        raise SystemExit(f"{PATCH}: V3 CSS import anchor not found")
    src = src.replace(anchor, anchor + '\n' + css_import, 1)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-professional-chat-header-v3-1: 1; }

/* V3.1 — custom status control; removes ugly native browser select. */

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-status-badge {
  display: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-control {
  position: relative;
  display: inline-flex;
  align-items: center;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-trigger {
  display: inline-flex;
  height: 24px;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
  border: 1px solid #e7e3db;
  border-radius: 999px;
  background: #fff;
  color: #625d56;
  font-size: 9px;
  font-weight: 800;
  box-shadow: none;
  cursor: pointer;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-trigger:hover,
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-trigger.is-open {
  border-color: #d9c18a;
  background: #fffaf0;
  color: #8c620e;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-dot,
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-option-dot {
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #c99122;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-control[data-status="open"] .tcs-v31-status-dot,
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-option-dot[data-value="open"] {
  background: #1fb879;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-control[data-status="waiting"] .tcs-v31-status-dot,
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-option-dot[data-value="waiting"] {
  background: #d49a22;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-control[data-status="in_progress"] .tcs-v31-status-dot,
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-option-dot[data-value="in_progress"] {
  background: #4f7edb;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-control[data-status="closed"] .tcs-v31-status-dot,
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-option-dot[data-value="closed"] {
  background: #9b9b9b;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-chevron {
  margin-inline-start: 1px;
  color: #aaa39a;
  font-size: 10px;
  line-height: 1;
  transform: translateY(-1px);
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-menu {
  position: absolute;
  top: 30px;
  inset-inline-start: 0;
  z-index: 60;
  width: 154px;
  padding: 5px;
  border: 1px solid #e5e1d9;
  border-radius: 11px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(31,26,18,.13);
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-menu > button {
  display: flex;
  width: 100%;
  min-height: 31px;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #554f48;
  font-size: 9px;
  font-weight: 750;
  text-align: start;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-menu > button:hover {
  background: #f7f5f1;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-menu > button.is-active {
  background: #fffaf0;
  color: #8d620e;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-check {
  margin-inline-start: auto;
  color: #a87413;
  font-size: 10px;
  font-weight: 900;
}

/* Slight refinement of the More menu after V3 screenshot QA. */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu {
  width: 214px !important;
  padding: 5px !important;
  border-radius: 11px !important;
  box-shadow: 0 12px 30px rgba(31,26,18,.13) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu > button {
  min-height: 32px !important;
  padding: 6px 8px !important;
  border-radius: 7px !important;
  font-size: 9.5px !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("STATUS=NATIVE_SELECT_REMOVED")
print("STATUS_POPOVER=CUSTOM_COMPACT")
print("STATUS_COLORS=YES")
print("MORE_MENU=REFINED")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
