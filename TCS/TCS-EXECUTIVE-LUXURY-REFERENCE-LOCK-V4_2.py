#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-EXECUTIVE-LUXURY-REFERENCE-LOCK-V4_2"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsExecutiveLuxuryReferenceLockV4_2.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

css_import = 'import "./tcsExecutiveLuxuryReferenceLockV4_2.css";'
if css_import not in src:
    anchors = [
        'import "./tcsExecutiveLuxuryReferenceLockV4_1.css";',
        'import "./tcsExecutiveLuxuryMockupV4.css";',
    ]
    for anchor in anchors:
        if anchor in src:
            src = src.replace(anchor, anchor + "\n" + css_import, 1)
            break
    else:
        raise SystemExit(f"{PATCH}: V4/V4.1 stylesheet import not found")

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-executive-luxury-reference-lock-v4-2: 1; }

/* V4.2 — screenshot QA pass.
   Goal: stronger premium scale, better legibility, cleaner empty illustration.
   CSS-only; no chat behavior changes. */

/* Increase readable scale without changing window geometry. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 {
  font-size: 14px !important;
}

/* Conversation rail: stronger presence */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4:not(.tos-chat-focus-mode) {
    grid-template-columns: 62px 365px minmax(0,1fr) !important;
  }
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 62px 330px minmax(360px,1fr) 325px !important;
  }
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail > div:first-child {
  padding: 20px 18px 15px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row {
  min-height: 70px !important;
  grid-template-columns: 44px minmax(0,1fr) auto !important;
  gap: 12px !important;
  padding: 10px 11px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-avatar {
  width: 42px !important;
  height: 42px !important;
  font-size: 11.5px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-title {
  font-size: 13px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-preview {
  font-size: 10.5px !important;
  line-height: 1.4 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-time {
  font-size: 9px !important;
}

/* Header hierarchy */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center {
  padding: 20px 22px 17px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center > .flex:first-child > div:first-child > div:first-child {
  font-size: 18px !important;
  font-weight: 900 !important;
  letter-spacing: -.025em !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v4-header-meta {
  margin-top: 7px !important;
}

/* Search bar: stronger but still refined */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell {
  min-height: 54px !important;
  padding: 6px 8px !important;
  border-radius: 13px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v15-inline-smart-search {
  font-size: 12.5px !important;
}

/* Empty state: less boxy and more like the approved mockup */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card {
  max-width: 540px !important;
  padding: 62px 42px 42px !important;
  border-radius: 28px !important;
  box-shadow: 0 26px 64px rgba(64,49,20,.085) !important;
}

/* Replace the overlapping tiny CSS speech bubbles with a cleaner layered illustration. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon {
  width: 68px !important;
  height: 68px !important;
  margin-bottom: 30px !important;
  border: 0 !important;
  border-radius: 50% !important;
  background: linear-gradient(145deg,#e8c66a,#c8921e) !important;
  box-shadow: 0 16px 34px rgba(170,117,18,.20) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::before,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::after {
  top: 50% !important;
  width: 92px !important;
  height: 58px !important;
  border: 1px solid #e7ddc9 !important;
  border-radius: 16px !important;
  background:
    linear-gradient(#d9c89d,#d9c89d) 22px 18px/45px 3px no-repeat,
    linear-gradient(#eee5d3,#eee5d3) 22px 29px/34px 3px no-repeat,
    rgba(255,255,255,.98) !important;
  box-shadow: 0 12px 28px rgba(60,47,24,.08) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::before {
  left: -78px !important;
  transform: translateY(-58%) rotate(-3deg) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::after {
  right: -82px !important;
  transform: translateY(-30%) rotate(3deg) !important;
}

/* Keep center icon clearly above the side cards */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon svg {
  z-index: 5 !important;
  width: 27px !important;
  height: 27px !important;
}

/* Empty copy */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card .text-base {
  font-size: 18px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card .text-xs {
  font-size: 11.5px !important;
}

/* Utility controls */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v3-icon-action {
  width: 40px !important;
  height: 40px !important;
  min-width: 40px !important;
  min-height: 40px !important;
}

/* Tone down excessive micro-size in filters/buttons */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 button[class*="text-\[8px\]"],
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 button[class*="text-\[9px\]"] {
  font-size: 9.5px !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=CSS_ONLY")
print("REFERENCE_LOCK=V4_2")
print("SCALE=INCREASED")
print("CONVERSATION_RAIL=WIDER")
print("HEADER=STRONGER")
print("SEARCH=STRONGER")
print("EMPTY_ILLUSTRATION=CLEAN_LAYERED")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
