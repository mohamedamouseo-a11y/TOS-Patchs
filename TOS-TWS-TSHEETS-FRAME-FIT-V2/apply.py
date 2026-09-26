#!/usr/bin/env python3
from pathlib import Path
import re

PATCH = "TOS-TWS-TSHEETS-FRAME-FIT-V2"
ROOT = Path.cwd()
LAB = ROOT / "frontend" / "src" / "pages" / "tws" / "TSheetsCasualLab.jsx"
CSS = ROOT / "vendor" / "tsheets-casual-upstream" / "apps" / "web" / "src" / "styles.css"

def fail(msg):
    raise SystemExit(f"ERROR: {msg}")

for p in (LAB, CSS):
    if not p.exists():
        fail(f"missing target: {p}")

lab = LAB.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")

# Parent TOS container: fit the already-constrained TOS page viewport.
old_section = 'className="relative h-[calc(100dvh-64px)] min-h-[640px] w-full overflow-hidden bg-white"'
new_section = 'className="relative h-full min-h-0 w-full overflow-hidden bg-white"'
if old_section in lab:
    lab = lab.replace(old_section, new_section, 1)
elif new_section not in lab:
    fail("TSheetsCasualLab section height anchor not found; refusing to guess")

old_iframe = 'className="block h-full w-full border-0 bg-white"'
new_iframe = 'className="block h-full min-h-0 w-full border-0 bg-white"'
if old_iframe in lab:
    lab = lab.replace(old_iframe, new_iframe, 1)
elif new_iframe not in lab:
    fail("TSheetsCasualLab iframe class anchor not found; refusing to guess")

if 'data-tsheets-frame-fit="v2"' not in lab:
    anchor = 'data-tsheets-casual-lab="p03-v2-clean"'
    if anchor not in lab:
        fail("TSheetsCasualLab data anchor not found")
    lab = lab.replace(anchor, anchor + '\n      data-tsheets-frame-fit="v2"', 1)

# V1 changed Casual's own viewport sizing to percentages. That was the wrong
# layer: CSS viewport units inside an iframe refer to the iframe viewport, which
# is exactly what Casual should fill. Restore the native iframe-local sizing.
v1_comment = re.compile(
    r"\n?/\* TOS_TSHEETS_FRAME_HEIGHT_FIT_V1[\s\S]*?\*/\n?",
    re.M,
)
css = v1_comment.sub("\n", css)

start = css.find(".app {")
end = css.find("\n.app--no-formula-bar", start)
if start < 0 or end < 0:
    fail("Casual .app block not found")
app = css[start:end]

app, h_count = re.subn(r"(?m)^\s*height:\s*(?:100%|100dvh);\s*$", "  height: 100dvh;", app, count=1)
app, w_count = re.subn(r"(?m)^\s*width:\s*(?:100%|100vw);\s*$", "  width: 100vw;", app, count=1)
if h_count != 1 or w_count != 1:
    fail(f"Casual .app size anchors unexpected: height={h_count}, width={w_count}")

marker = """  /* TOS_TSHEETS_FRAME_FIT_V2
     The outer TOS wrapper owns page height. Inside the iframe, 100dvh/100vw
     correctly means the iframe viewport itself, so Casual fills that frame. */
"""
if "TOS_TSHEETS_FRAME_FIT_V2" not in app:
    insert_at = app.find("  height: 100dvh;")
    if insert_at < 0:
        fail("normalized app height not found")
    app = app[:insert_at] + marker + app[insert_at:]

css = css[:start] + app + css[end:]

LAB.write_text(lab, encoding="utf-8")
CSS.write_text(css, encoding="utf-8")

# Verification
lab2 = LAB.read_text(encoding="utf-8")
css2 = CSS.read_text(encoding="utf-8")
app2 = css2[css2.find(".app {"):css2.find("\n.app--no-formula-bar", css2.find(".app {"))]

checks = {
    "parent_fit_marker": 'data-tsheets-frame-fit="v2"' in lab2,
    "parent_height_full": 'className="relative h-full min-h-0 w-full overflow-hidden bg-white"' in lab2,
    "parent_old_viewport_calc_removed": "h-[calc(100dvh-64px)]" not in lab2,
    "parent_min_640_removed": "min-h-[640px]" not in lab2,
    "iframe_min_h_zero": 'className="block h-full min-h-0 w-full border-0 bg-white"' in lab2,
    "casual_v2_marker": "TOS_TSHEETS_FRAME_FIT_V2" in app2,
    "casual_iframe_height": "height: 100dvh;" in app2,
    "casual_iframe_width": "width: 100vw;" in app2,
    "v1_marker_removed": "TOS_TSHEETS_FRAME_HEIGHT_FIT_V1" not in css2,
}
bad = [k for k,v in checks.items() if not v]
if bad:
    fail("verification failed: " + ", ".join(bad))

print(f"PATCH={PATCH}")
print("APPLY=PASS")
print("ROOT_CAUSE_LAYER=OUTER_TOS_IFRAME_WRAPPER")
print("PARENT_HEIGHT=100%")
print("PARENT_MIN_HEIGHT=0")
print("OUTER_100DVH_CALC=REMOVED")
print("OUTER_MIN_640=REMOVED")
print("IFRAME_HEIGHT=100%")
print("CASUAL_APP_HEIGHT=100dvh_IFRAME_LOCAL")
print("CASUAL_APP_WIDTH=100vw_IFRAME_LOCAL")
print("ZOOM_TOUCHED=NO")
print("BACK_HOME_TOUCHED=NO")
print("AUTOSAVE_TOUCHED=NO")
print("BACKEND_TOUCHED=NO")
print("FILES=frontend/src/pages/tws/TSheetsCasualLab.jsx,vendor/tsheets-casual-upstream/apps/web/src/styles.css")
