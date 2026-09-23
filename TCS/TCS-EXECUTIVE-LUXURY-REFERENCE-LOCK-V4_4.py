#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-EXECUTIVE-LUXURY-REFERENCE-LOCK-V4_4"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsExecutiveLuxuryReferenceLockV4_4.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

css_import = 'import "./tcsExecutiveLuxuryReferenceLockV4_4.css";'
if css_import not in src:
    anchors = [
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

# Add a stable hook to the direct-chat empty notice so desktop can hide the redundant banner.
old_notice = '{isDirectMode && canDirectChat && !activeConversationId && <Notice type="info" className="m-4">اختر محادثة خاصة أو ابدأ محادثة مع أحد أعضاء الفريق.</Notice>}'
new_notice = '{isDirectMode && canDirectChat && !activeConversationId && <Notice type="info" className="tcs-v44-direct-empty-notice m-4">اختر محادثة خاصة أو ابدأ محادثة مع أحد أعضاء الفريق.</Notice>}'
if "tcs-v44-direct-empty-notice" not in src:
    if old_notice not in src:
        raise SystemExit(f"{PATCH}: direct empty notice anchor not found")
    src = src.replace(old_notice, new_notice, 1)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-executive-luxury-reference-lock-v4-4: 1; }

/* V4.4 — composition lock from live screenshot.
   Goal: exact premium composition, hero centered, no redundant banner,
   inspector cleaner and more legible. */

@media (min-width: 1024px) {
  /* Remove the redundant desktop notice above the empty canvas.
     The rail + empty hero already communicate the action. */
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v44-direct-empty-notice {
    display: none !important;
  }

  /* Empty chat must always be centered and fully visible — never clipped at the bottom. */
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-message-canvas:has(.tos-chat-empty-clean-card) {
    display: grid !important;
    place-items: center !important;
    align-content: center !important;
    justify-content: stretch !important;
    min-height: 0 !important;
    padding: 28px 30px !important;
    overflow-y: auto !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-message-canvas:has(.tos-chat-empty-clean-card) .tos-chat-empty-clean-card {
    align-self: center !important;
    justify-self: center !important;
    margin: 0 auto !important;
  }

  /* When the inspector is open, preserve a strong center canvas. */
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 60px 312px minmax(460px, 1fr) 274px !important;
  }
}

/* Refine the hero card so it feels integrated into the canvas, not pasted on top. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card {
  width: min(100%, 520px) !important;
  padding: 52px 42px 38px !important;
  border-color: #e5d4aa !important;
  background:
    radial-gradient(circle at 12% 10%, rgba(213,163,49,.24), transparent 23%),
    radial-gradient(circle at 88% 90%, rgba(231,204,142,.16), transparent 28%),
    linear-gradient(145deg,#fffefa 0%,#fff8ea 100%) !important;
  box-shadow:
    0 26px 66px rgba(61,47,18,.09),
    inset 0 1px 0 rgba(255,255,255,.94) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card .text-base {
  font-size: 18px !important;
  font-weight: 900 !important;
  letter-spacing: -.02em !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card .text-xs {
  max-width: 390px !important;
  margin-inline: auto !important;
  font-size: 11.5px !important;
  line-height: 1.65 !important;
  color: #81786e !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card .mt-4 button {
  min-height: 31px !important;
  padding: 6px 13px !important;
  border: 1px solid #e4d7ba !important;
  background: rgba(255,255,255,.94) !important;
  color: #514a40 !important;
  font-size: 9.5px !important;
  box-shadow: 0 5px 12px rgba(58,47,24,.04) !important;
}

/* Better visual separation between search header and canvas. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center {
  box-shadow: 0 1px 0 rgba(65,55,39,.03) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell {
  box-shadow:
    0 8px 22px rgba(48,39,24,.045),
    inset 0 1px 0 rgba(255,255,255,.9) !important;
}

/* Inspector: clearer typography, flatter cards, lower visual competition. */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel:not(.hidden) {
    background: linear-gradient(180deg,#faf8f4,#f7f4ef) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:first-child {
    padding: 15px 12px 12px !important;
    border-bottom: 1px solid #e8e0d5 !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:first-child > div:first-child > div:first-child {
    font-size: 13px !important;
    font-weight: 900 !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:not(:first-child) {
    margin: 8px 7px 0 !important;
    border: 1px solid #e9e1d6 !important;
    border-radius: 12px !important;
    box-shadow: 0 5px 14px rgba(46,39,27,.03) !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:not(:first-child) .text-sm {
    font-size: 11.5px !important;
  }

  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:not(:first-child) .text-xs {
    font-size: 9.5px !important;
    line-height: 1.5 !important;
  }
}

/* Conversation rows: enough contrast to read at a glance without looking heavy. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row {
  transition:
    background .15s ease,
    border-color .15s ease,
    box-shadow .15s ease,
    transform .15s ease !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 7px 16px rgba(53,43,25,.04) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row.is-active {
  transform: none !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=CSS_FIRST")
print("DIRECT_NOTICE=HIDDEN_DESKTOP")
print("EMPTY_HERO=CENTERED")
print("EMPTY_CLIP=FIXED")
print("CENTER_CHAT=MORE_SPACE")
print("INSPECTOR=CLEANER")
print("CONVERSATION_ROWS=REFINED")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
