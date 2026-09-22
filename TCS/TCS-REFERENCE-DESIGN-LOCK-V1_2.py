#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys

PATCH = "TCS-REFERENCE-DESIGN-LOCK-V1.2"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsReferencePolishV1_2.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")

backup_dir = Path("/tmp") / f"TCS-REFERENCE-DESIGN-LOCK-V1_2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# Load V1.2 CSS.
import_anchor = 'import "./tcsReferencePolishV1_1.css";'
polish_import = 'import "./tcsReferencePolishV1_2.css";'
if polish_import not in src:
    if import_anchor not in src:
        raise SystemExit(f"{PATCH}: V1.1 CSS import marker not found")
    src = src.replace(import_anchor, import_anchor + "\n" + polish_import, 1)

# Opening Chat tools must close Details first.
old_tools = '''<button type="button" onClick={() => setToolbarOpen((value) => !value)} className="rounded-2xl border border-zinc-100 bg-white px-4 py-2.5 text-xs font-black text-zinc-700 shadow-sm transition hover:-translate-y-0.5 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200">'''
new_tools = '''<button type="button" onClick={() => setToolbarOpen((value) => { const next = !value; if (next) setDetailsPanelOpen(false); return next; })} className="rounded-2xl border border-zinc-100 bg-white px-4 py-2.5 text-xs font-black text-zinc-700 shadow-sm transition hover:-translate-y-0.5 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200">'''
if old_tools in src:
    src = src.replace(old_tools, new_tools, 1)
elif "if (next) setDetailsPanelOpen(false)" not in src:
    raise SystemExit(f"{PATCH}: Chat tools trigger marker not found")

# Opening direct details controls must close tools first as well.
src = src.replace(
    'onClick={() => { setDetailsPanelOpen(true); setDetailsTab("files"); }}',
    'onClick={() => { setToolbarOpen(false); setDetailsPanelOpen(true); setDetailsTab("files"); }}'
)
src = src.replace(
    'onClick={() => { setDetailsPanelOpen(true); setDetailsTab("tasks"); }}',
    'onClick={() => { setToolbarOpen(false); setDetailsPanelOpen(true); setDetailsTab("tasks"); }}'
)
src = src.replace(
    'onClick={() => setDetailsPanelOpen((value) => !value)} disabled={focusMode}',
    'onClick={() => { setToolbarOpen(false); setDetailsPanelOpen((value) => !value); }} disabled={focusMode}',
    1
)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-reference-design-lock-v1-2: 1; }

/* TCS Reference Design Lock V1.2
   Micro-fix for drawer/menu exclusivity and drawer placement only. */

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-details-panel:not(.hidden) {
  display: flex !important;
  align-items: stretch !important;
  justify-content: flex-end !important;
  padding: 10px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-details-panel:not(.hidden) > div {
  width: min(380px, 92%) !important;
  max-width: 380px !important;
  height: 100% !important;
  margin: 0 !important;
  margin-inline-start: auto !important;
  margin-inline-end: 0 !important;
  border-radius: 18px !important;
  overflow-y: auto !important;
}

/* Tools stays attached to its trigger and must not dominate the workspace. */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v16-tools-menu {
  inset-inline-start: auto !important;
  inset-inline-end: 0 !important;
  width: 292px !important;
  max-width: calc(100vw - 32px) !important;
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("TOOLS_DETAILS_EXCLUSIVE=YES")
print("DETAILS_DRAWER_RIGHT_EDGE=YES")
print("TOOLS_MENU_TRIGGER_ALIGNED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_AND_DEPLOY_FRONTEND")
