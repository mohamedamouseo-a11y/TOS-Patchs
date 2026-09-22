#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys

PATCH = "TCS-REFERENCE-DESIGN-LOCK-V1.3"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsReferencePolishV1_3.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")

backup_dir = Path("/tmp") / f"TCS-REFERENCE-DESIGN-LOCK-V1_3-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

import_anchor = 'import "./tcsReferencePolishV1_2.css";'
polish_import = 'import "./tcsReferencePolishV1_3.css";'
if polish_import not in src:
    if import_anchor not in src:
        raise SystemExit(f"{PATCH}: V1.2 CSS import marker not found")
    src = src.replace(import_anchor, import_anchor + "\n" + polish_import, 1)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-reference-design-lock-v1-3: 1; }

/* TCS Reference Design Lock V1.3
   Physical-right details drawer correction only.
   Direction-independent. No chat/backend behavior changes. */

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-details-panel:not(.hidden) {
  position: absolute !important;
  inset: 0 !important;
  display: block !important;
  padding: 0 !important;
  background: rgba(28, 25, 20, .12) !important;
  backdrop-filter: blur(3px) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-details-panel:not(.hidden) > div {
  position: absolute !important;
  top: 10px !important;
  right: 10px !important;
  bottom: 10px !important;
  left: auto !important;
  width: min(380px, calc(100% - 20px)) !important;
  max-width: 380px !important;
  height: auto !important;
  margin: 0 !important;
  overflow-y: auto !important;
  border: 1px solid #e9e5dd !important;
  border-radius: 18px !important;
  background: #fbfaf7 !important;
  box-shadow: 0 20px 54px rgba(28,24,18,.18) !important;
}

/* Explicitly override logical-margin rules from earlier polish in both LTR and RTL. */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1[dir="ltr"] .tos-chat-details-panel:not(.hidden) > div,
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1[dir="rtl"] .tos-chat-details-panel:not(.hidden) > div {
  margin-left: 0 !important;
  margin-right: 0 !important;
  margin-inline-start: 0 !important;
  margin-inline-end: 0 !important;
  right: 10px !important;
  left: auto !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("DETAILS_PHYSICAL_RIGHT=YES")
print("TOOLS_DETAILS_EXCLUSIVE=PRESERVED")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_AND_DEPLOY_FRONTEND")
