#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-EXECUTIVE-LUXURY-REFERENCE-LOCK-V4_3"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsExecutiveLuxuryReferenceLockV4_3.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

css_import = 'import "./tcsExecutiveLuxuryReferenceLockV4_3.css";'
if css_import not in src:
    anchors = [
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

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-executive-luxury-reference-lock-v4-3: 1; }

/* V4.3 — final premium depth pass based on live screenshot.
   CSS-only. Preserve all chat behavior and backend. */

html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 {
  --v43-ink: #191816;
  --v43-muted: #766f65;
  --v43-line: #e7dfd2;
  --v43-gold: #c48d20;
  --v43-gold-deep: #8e5f0c;
  --v43-ivory: #fdfbf6;
}

/* Give the center conversation more room when inspector is open. */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4.tos-chat-details-open:not(.tos-chat-focus-mode) {
    grid-template-columns: 60px 320px minmax(420px,1fr) 282px !important;
  }
}

/* Stronger rail typography and breathing room. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail h2,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-rail h3 {
  font-size: 15.5px !important;
  font-weight: 900 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row {
  min-height: 68px !important;
  border-radius: 14px !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-title {
  font-size: 12.5px !important;
  font-weight: 900 !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-preview {
  font-size: 10px !important;
  color: #7f786f !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-time {
  font-size: 8.8px !important;
}

/* Premium selected row, closer to approved reference. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v4-conversation-row.is-active {
  background: linear-gradient(180deg,#fffdf8,#fff7e8) !important;
  border-color: #e2c982 !important;
  box-shadow:
    inset 3px 0 0 var(--v43-gold),
    0 8px 18px rgba(92,67,20,.055) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4[dir="rtl"] .tcs-v4-conversation-row.is-active {
  box-shadow:
    inset -3px 0 0 var(--v43-gold),
    0 8px 18px rgba(92,67,20,.055) !important;
}

/* Main header hierarchy. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center {
  padding: 19px 20px 15px !important;
  background:
    linear-gradient(180deg,#fff,#fffdf9) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-command-center > .flex:first-child > div:first-child > div:first-child {
  font-size: 17px !important;
  color: var(--v43-ink) !important;
}

/* Utility actions become slightly more jewel-like but restrained. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v3-icon-action {
  border-color: #e5ddd1 !important;
  background: linear-gradient(180deg,#fff,#fdfbf7) !important;
  box-shadow: 0 6px 16px rgba(46,38,25,.055) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v3-icon-action:hover {
  border-color: #d7bc79 !important;
  background: #fff9eb !important;
  color: var(--v43-gold-deep) !important;
}

/* Command search bar with a cleaner premium gold action. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell {
  min-height: 50px !important;
  border-color: #e5ded3 !important;
  background: linear-gradient(180deg,#fff,#fdfbf7) !important;
  box-shadow: 0 7px 20px rgba(49,40,26,.045) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v16-inline-search-shell > button:last-child {
  border: 1px solid #d0ae5f !important;
  background: linear-gradient(180deg,#eed58f,#ddb754) !important;
  color: #5d3f08 !important;
  font-weight: 900 !important;
  box-shadow: 0 7px 16px rgba(146,105,23,.12) !important;
}

/* Main conversation canvas — soft architectural depth instead of flat white. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-v8-message-canvas {
  background:
    radial-gradient(circle at 12% 10%, rgba(205,157,43,.045) 0 1px, transparent 1.5px) 0 0/20px 20px,
    radial-gradient(circle at 88% 88%, rgba(205,157,43,.055), transparent 24%),
    linear-gradient(180deg,#fff 0%,#fdfcf8 100%) !important;
}

/* Empty state becomes the visual hero, not a small card floating in space. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-empty-clean-card {
  max-width: 520px !important;
  padding: 54px 42px 40px !important;
  border: 1px solid #e8d8b1 !important;
  border-radius: 28px !important;
  background:
    radial-gradient(circle at 13% 12%, rgba(217,168,56,.23), transparent 23%),
    radial-gradient(circle at 88% 88%, rgba(230,202,137,.17), transparent 28%),
    linear-gradient(145deg,#fffefa,#fff8ea) !important;
  box-shadow:
    0 28px 68px rgba(63,49,20,.085),
    inset 0 1px 0 rgba(255,255,255,.9) !important;
}

/* The three-chat illustration reads more clearly and no longer overlaps awkwardly. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon {
  width: 72px !important;
  height: 72px !important;
  margin-bottom: 31px !important;
  background: linear-gradient(145deg,#f0d37d,#c99122) !important;
  box-shadow: 0 16px 36px rgba(163,112,17,.22) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::before,
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::after {
  width: 94px !important;
  height: 58px !important;
  border-radius: 16px !important;
  background:
    linear-gradient(#d8c799,#d8c799) 22px 17px/48px 3px no-repeat,
    linear-gradient(#ebe1ca,#ebe1ca) 22px 29px/34px 3px no-repeat,
    #fff !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::before {
  left: -84px !important;
  top: 15px !important;
  transform: rotate(-4deg) !important;
}
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tcs-v41-empty-icon::after {
  right: -86px !important;
  top: 24px !important;
  transform: rotate(4deg) !important;
}

/* Inspector: slimmer, calmer, premium — never competes with chat. */
@media (min-width: 1024px) {
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel:not(.hidden) {
    background: #faf8f4 !important;
    border-inline-start: 1px solid #e8e1d6 !important;
  }
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:first-child {
    padding: 15px 13px 12px !important;
    background: #fff !important;
  }
  html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel .tos-chat-detail-card:not(:first-child) {
    margin: 8px 8px 0 !important;
    border-color: #ebe4d9 !important;
    border-radius: 13px !important;
    background: #fff !important;
    box-shadow: 0 6px 16px rgba(47,39,27,.035) !important;
  }
}

/* Reduce visual clutter of inspector metrics/tabs. */
html:not(.dark) .tcs-desktop-window .tcs-executive-luxury-v4 .tos-chat-details-panel button {
  box-shadow: none !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=CSS_ONLY")
print("CENTER_CHAT=MORE_SPACE")
print("CONVERSATION_RAIL=PREMIUM_DEPTH")
print("HEADER=PREMIUM_DEPTH")
print("SEARCH=PREMIUM_GOLD_ACTION")
print("EMPTY_STATE=HERO")
print("INSPECTOR=SLIMMER")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
