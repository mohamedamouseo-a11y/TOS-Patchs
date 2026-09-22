#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys

PATCH = "TCS-CHAT-ROUTE-WINDOW-RECOVERY-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
APP = ROOT / "frontend/src/App.jsx"

if not APP.exists():
    raise SystemExit(f"{PATCH}: missing {APP}")

src = APP.read_text(encoding="utf-8")

anchor = '''  useEffect(() => {
    if (centralChatEmbed || tcsWindowOpen) return;
    syncBrowserPathForPage(active, { replace: window.location.pathname === "/" });
  }, [active, centralChatEmbed, tcsWindowOpen]);
'''

guard = '''  // TCS_CHAT_ROUTE_WINDOW_RECOVERY_V1
  // Direct /chat loads must always restore/open the desktop TCS window.
  // Keep the underlying main page on a real page instead of the non-rendered "chat" route.
  useEffect(() => {
    if (centralChatEmbed || typeof window === "undefined") return;
    if (pageFromCurrentLocation() !== "chat") return;
    setActive((current) => current === "chat" ? "dashboard" : current);
    setTcsWindowOpen(true);
    setTcsWindowRestoreSignal((value) => value + 1);
  }, [centralChatEmbed]);

'''

if "TCS_CHAT_ROUTE_WINDOW_RECOVERY_V1" not in src:
    if anchor not in src:
        raise SystemExit(f"{PATCH}: route sync anchor not found")
    src = src.replace(anchor, guard + anchor, 1)

old_open = '''  function openTcsWindow() {
    setTcsWindowOpen(true);
    setTcsWindowRestoreSignal((value) => value + 1);
'''
new_open = '''  function openTcsWindow() {
    if (active === "chat") setActive("dashboard");
    setTcsWindowOpen(true);
    setTcsWindowRestoreSignal((value) => value + 1);
'''

if old_open not in src:
    if 'if (active === "chat") setActive("dashboard");' not in src:
        raise SystemExit(f"{PATCH}: openTcsWindow anchor not found")
else:
    src = src.replace(old_open, new_open, 1)

backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(APP, backup_dir / "App.jsx")

APP.write_text(src, encoding="utf-8")

print(f"PATCH={PATCH}")
print("APP_ROUTE_GUARD=ADDED")
print("DIRECT_CHAT_ROUTE_RESTORE=YES")
print("ACTIVE_CHAT_BLANK_STATE_GUARD=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_AND_DEPLOY_FRONTEND")
