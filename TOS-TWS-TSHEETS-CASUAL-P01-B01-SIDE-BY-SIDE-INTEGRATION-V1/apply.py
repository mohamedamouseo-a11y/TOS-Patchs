#!/usr/bin/env python3
# TOS-TWS-TSHEETS-CASUAL-P01-B01-SIDE-BY-SIDE-INTEGRATION-V1
from pathlib import Path
import json, sys

ROOT = Path("/var/www/TOS")
TWS = ROOT / "frontend/src/pages/tws/TwsPage.jsx"
PKG = ROOT / "frontend/package.json"
MARKER = "TOS_TWS_TSHEETS_CASUAL_P01_B01_SIDE_BY_SIDE_INTEGRATION_V1"

def die(msg):
    print("PATCH=FAIL")
    print(f"ERROR={msg}")
    sys.exit(1)

for p in (TWS, PKG):
    if not p.exists():
        die(f"MISSING:{p}")

tws = TWS.read_text(encoding="utf-8")

if MARKER not in tws:
    import_anchor = 'import { TSheetsEditor } from "./TSheetsEditor";\n'
    if tws.count(import_anchor) != 1:
        die(f"TWS_IMPORT_ANCHOR_COUNT={tws.count(import_anchor)}")
    tws = tws.replace(
        import_anchor,
        import_anchor + 'import { TSheetsCasualLab } from "./TSheetsCasualLab"; // ' + MARKER + '\n',
        1,
    )

    parse_anchor = '''function parseTwsPath(pathname) {
  const match = pathname.match(/^\\/tws\\/(docs|sheets|slides)\\/([^/]+)\\/?$/);'''
    if tws.count(parse_anchor) != 1:
        die(f"TWS_PARSE_ANCHOR_COUNT={tws.count(parse_anchor)}")
    tws = tws.replace(
        parse_anchor,
        '''function parseTwsPath(pathname) {
  if (/^\\/tws\\/sheets-lab\\/?$/.test(pathname)) return { mode: "sheetsLab" }; // ''' + MARKER + '''
  const match = pathname.match(/^\\/tws\\/(docs|sheets|slides)\\/([^/]+)\\/?$/);''',
        1,
    )

    render_anchor = '''  if (view.mode === "settings") {
    return <TwsShareSettingsPage user={user} onBack={navigateToDashboard} />;
  }

  if (view.mode === "editor") {'''
    if tws.count(render_anchor) != 1:
        die(f"TWS_RENDER_ANCHOR_COUNT={tws.count(render_anchor)}")
    tws = tws.replace(
        render_anchor,
        '''  if (view.mode === "settings") {
    return <TwsShareSettingsPage user={user} onBack={navigateToDashboard} />;
  }

  if (view.mode === "sheetsLab") {
    return <TSheetsCasualLab />;
  }

  if (view.mode === "editor") {''',
        1,
    )
    TWS.write_text(tws, encoding="utf-8")

pkg = json.loads(PKG.read_text(encoding="utf-8"))
scripts = pkg.setdefault("scripts", {})
build = scripts.get("build", "")
target = "vite build && node scripts/syncTsheetsCasualRuntime.mjs"
if build == "vite build":
    scripts["build"] = target
elif build != target:
    die(f"UNEXPECTED_FRONTEND_BUILD_SCRIPT:{build}")
PKG.write_text(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-TWS-TSHEETS-CASUAL-P01-B01-SIDE-BY-SIDE-INTEGRATION-V1")
print("ROUTE=/tws/sheets-lab")
print("RUNTIME_PATH=/tws-casual-runtime/")
print("OLD_TSHEETS_ROUTE_PRESERVED=/tws/sheets/:id")
print("SIDEBAR_CHANGED=NO")
print("BRANDING_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DB_CHANGED=NO")
