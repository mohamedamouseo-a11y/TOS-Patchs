#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
CSS = ROOT / "frontend/src/pages/googleDriveSettingsFlagshipLuxuryV1.css"
DARK = ROOT / "frontend/src/pages/googleDriveSettingsFlagshipLuxuryV1_1DarkShellContrastFix.css"

for p in (CSS, DARK):
    if not p.exists():
        raise SystemExit(f"PATCH=FAIL\nREASON=Missing {p}")

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH=FAIL\nREASON={label} expected once, found {count}")
    return text.replace(old, new, 1)

changed = []

css = CSS.read_text(encoding="utf-8")
old = '''.tos-gdrive-settings-flagship-v1 > .flex:first-child > div:last-child {
  width: 66px !important;
  height: 66px !important;
  border: 1px solid rgba(48,135,201,.23);
  border-radius: 22px !important;
  background: linear-gradient(145deg,#f1f9ff 0%,#dbeefc 55%,#c9e5f6 100%) !important;
  color: #2d78ac !important;
  box-shadow: 0 13px 29px rgba(38,113,168,.14), inset 0 1px rgba(255,255,255,.92);
}
'''
new = '''.tos-gdrive-settings-flagship-v1 > .flex:first-child > div:last-child {
  width: auto !important;
  height: auto !important;
  min-width: max-content;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  color: inherit !important;
  box-shadow: none !important;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}
.tos-gdrive-settings-flagship-v1 > .flex:first-child > div:last-child .tos-premium-button {
  flex: 0 0 auto;
  white-space: nowrap;
}
'''
if old in css:
    css = replace_once(css, old, new, "light header actions")
elif "min-width: max-content;" not in css:
    raise SystemExit("PATCH=FAIL\nREASON=light header block changed unexpectedly")

# Add responsive alignment if not already present.
marker = '''@media (max-width: 767px) {
  .tos-gdrive-settings-flagship-v1 { padding:20px !important; border-radius:23px !important; }
'''
if "justify-content:flex-start" not in css:
    replacement = '''@media (max-width: 1023px) {
  .tos-gdrive-settings-flagship-v1 > .flex:first-child > div:last-child {
    min-width: 0;
    width: 100% !important;
    justify-content: flex-start;
  }
}

@media (max-width: 767px) {
  .tos-gdrive-settings-flagship-v1 { padding:20px !important; border-radius:23px !important; }
'''
    css = replace_once(css, marker, replacement, "responsive header actions")

if CSS.read_text(encoding="utf-8") != css:
    CSS.write_text(css, encoding="utf-8")
    changed.append(str(CSS.relative_to(ROOT)))

dark = DARK.read_text(encoding="utf-8")
old_dark = '''.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child > div:last-child {
  border-color: rgba(74,177,239,.36) !important;
  background: linear-gradient(145deg,#0e2940 0%,#0b2031 60%,#081823 100%) !important;
  color: #72c8ff !important;
  box-shadow: 0 12px 30px rgba(0,0,0,.31),0 0 24px rgba(55,165,235,.14),inset 0 1px rgba(255,255,255,.04) !important;
}
'''
new_dark = '''.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child > div:last-child {
  border-color: transparent !important;
  background: transparent !important;
  color: inherit !important;
  box-shadow: none !important;
}
'''
if old_dark in dark:
    dark = replace_once(dark, old_dark, new_dark, "dark header actions")
elif "border-color: transparent !important;" not in dark:
    raise SystemExit("PATCH=FAIL\nREASON=dark header block changed unexpectedly")

if DARK.read_text(encoding="utf-8") != dark:
    DARK.write_text(dark, encoding="utf-8")
    changed.append(str(DARK.relative_to(ROOT)))

print("PATCH=PASS")
print(f"FILES_CHANGED={len(changed)}")
for p in changed:
    print(p)
