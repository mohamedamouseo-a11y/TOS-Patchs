#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-PROFESSIONAL-CHAT-HEADER-V3_2-FINAL-POLISH"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsProfessionalChatHeaderV3_2FinalPolish.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

css_import = 'import "./tcsProfessionalChatHeaderV3_2FinalPolish.css";'
if css_import not in src:
    anchors = [
        'import "./tcsProfessionalChatHeaderV3_1.css";',
        'import "./tcsProfessionalChatHeaderV3.css";',
        'import "./tcsPremiumChatShellV2_3Clean.css";',
    ]
    for anchor in anchors:
        if anchor in src:
            src = src.replace(anchor, anchor + "\n" + css_import, 1)
            break
    else:
        raise SystemExit(f"{PATCH}: no valid CSS import anchor found")

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-professional-chat-header-v3-2-final-polish: 1; }

/* TCS Professional Chat Header V3.2 Final Polish
   CSS-only finishing pass.
   No chat logic, API, socket, permissions, Drive or backend changes. */

/* 1) Status pill — cleaner, tighter, more premium */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-trigger {
  height: 22px !important;
  gap: 5px !important;
  padding: 0 7px !important;
  border-color: #e5e0d7 !important;
  background: #fff !important;
  color: #59544e !important;
  font-size: 8.5px !important;
  font-weight: 800 !important;
  letter-spacing: -.005em !important;
  box-shadow: none !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-trigger:hover,
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-trigger.is-open {
  border-color: #d8c28f !important;
  background: #fffaf0 !important;
  color: #8b620f !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-dot {
  width: 5px !important;
  height: 5px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-chevron {
  font-size: 9px !important;
  opacity: .75 !important;
}

/* 2) Header actions — exact same box, spacing and weight */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-header-actions {
  gap: 5px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-icon-action {
  width: 34px !important;
  height: 34px !important;
  min-width: 34px !important;
  min-height: 34px !important;
  border-color: #e7e3dc !important;
  border-radius: 9px !important;
  background: #fff !important;
  color: #6c665f !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-icon-action:hover {
  border-color: #d9c38e !important;
  background: #fffaf1 !important;
  color: #8f650f !important;
}

/* 3) More menu — smaller, tighter, closer to native chat app utility menu */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu {
  width: 198px !important;
  padding: 5px !important;
  border-radius: 10px !important;
  border-color: #e6e1d8 !important;
  box-shadow: 0 10px 26px rgba(31,26,18,.12) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu > button {
  min-height: 30px !important;
  gap: 8px !important;
  padding: 6px 8px !important;
  border-radius: 7px !important;
  font-size: 9px !important;
  font-weight: 760 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-more-menu > button:hover {
  background: #f7f5f1 !important;
  color: #8a6110 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-menu-divider {
  margin: 4px 3px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v3-menu-label {
  padding: 2px 8px 3px !important;
  font-size: 7.5px !important;
}

/* 4) Status popover — compact and consistent with More */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-menu {
  width: 142px !important;
  padding: 4px !important;
  border-radius: 10px !important;
  border-color: #e6e1d8 !important;
  box-shadow: 0 10px 26px rgba(31,26,18,.12) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v31-status-menu > button {
  min-height: 29px !important;
  gap: 7px !important;
  padding: 5px 7px !important;
  border-radius: 7px !important;
  font-size: 8.5px !important;
}

/* 5) Reduce gold-heavy borders in search and empty state */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v16-inline-search-shell {
  border-color: #e7e3db !important;
  background: #fbfaf8 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tcs-v16-inline-search-shell:focus-within {
  border-color: #d8c28f !important;
  box-shadow: 0 0 0 3px rgba(201,145,34,.07) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tos-chat-empty-clean-card {
  border-color: #e8dfca !important;
  background:
    radial-gradient(circle at 0 0, rgba(222,181,80,.10), transparent 30%),
    linear-gradient(150deg, #fffefa, #fffaf2) !important;
  box-shadow: 0 10px 24px rgba(55,43,18,.055) !important;
}

/* 6) Slightly tighter header rhythm */
html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tos-chat-command-center {
  padding-top: 12px !important;
  padding-bottom: 11px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-professional-chat-header-v3 .tos-chat-v4-header-meta {
  margin-top: 6px !important;
  gap: 5px !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=CSS_ONLY")
print("STATUS_PILL=REFINED")
print("HEADER_ICONS=UNIFIED")
print("MORE_MENU=SMALLER")
print("STATUS_MENU=SMALLER")
print("GOLD_BORDERS=SOFTENED")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
