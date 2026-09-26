#!/usr/bin/env python3
from pathlib import Path

PATCH = "TOS-TWS-TSHEETS-FRAME-HEIGHT-FIT-V1"
MARKER = "TOS_TSHEETS_FRAME_HEIGHT_FIT_V1"
ROOT = Path.cwd()
CSS = ROOT / "vendor" / "tsheets-casual-upstream" / "apps" / "web" / "src" / "styles.css"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


if not CSS.exists():
    fail(f"missing target file: {CSS}")

text = CSS.read_text(encoding="utf-8")

old = '''html,
body,
#root {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  width: 100vw;
  overflow: hidden;
}
'''

new = '''html,
body,
#root {
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

/* TOS_TSHEETS_FRAME_HEIGHT_FIT_V1
 * Casual runs inside the TWS iframe. Size the app to the iframe's
 * containing block instead of creating a second viewport-sized document.
 * The existing flex/min-h-0 grid chain keeps scrolling inside the sheet.
 */
.app {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}
'''

if MARKER not in text:
    count = text.count(old)
    if count != 1:
        fail(f"expected exactly one current runtime root/.app layout block, found {count}; refusing to guess")
    text = text.replace(old, new, 1)
    CSS.write_text(text, encoding="utf-8")

check = CSS.read_text(encoding="utf-8")
app_start = check.find(".app {")
if app_start < 0:
    fail(".app block missing after apply")
app_block = check[app_start:app_start + 350]

requirements = {
    "marker": MARKER in check,
    "root_min_height_zero": "min-height: 0;" in check[:app_start],
    "root_min_width_zero": "min-width: 0;" in check[:app_start],
    "app_height_percent": "height: 100%;" in app_block,
    "app_width_percent": "width: 100%;" in app_block,
    "app_min_height_zero": "min-height: 0;" in app_block,
    "app_min_width_zero": "min-width: 0;" in app_block,
    "old_100dvh_removed": "height: 100dvh;" not in check,
    "old_100vw_removed": "width: 100vw;" not in check,
}
failed = [name for name, ok in requirements.items() if not ok]
if failed:
    fail("validation failed: " + ", ".join(failed))

print(f"PATCH={PATCH}")
print("APPLY=PASS")
print(f"FILE={CSS.relative_to(ROOT)}")
print("RUNTIME_ROOT_HEIGHT=100%")
print("APP_HEIGHT=100%")
print("APP_WIDTH=100%")
print("APP_MIN_HEIGHT=0")
print("APP_MIN_WIDTH=0")
print("VIEWPORT_UNITS_REMOVED=YES")
print("GRID_SCROLL_MODEL=UNCHANGED_INTERNAL")
print("ZOOM_TOUCHED=NO")
print("SCALE_TOUCHED=NO")
print("BACK_HOME_TOUCHED=NO")
print("AUTOSAVE_TOUCHED=NO")
print("BACKEND_TOUCHED=NO")
