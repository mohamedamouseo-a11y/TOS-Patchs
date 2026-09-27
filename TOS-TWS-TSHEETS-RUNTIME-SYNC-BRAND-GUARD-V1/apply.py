#!/usr/bin/env python3
from pathlib import Path

PATCH = "TOS-TWS-TSHEETS-RUNTIME-SYNC-BRAND-GUARD-V1"
ROOT = Path.cwd()
TARGET = ROOT / "frontend" / "scripts" / "syncTsheetsCasualRuntime.mjs"
MARKER = "TOS_TSHEETS_RUNTIME_SYNC_BRAND_GUARD_V1"

def fail(msg):
    raise SystemExit("ERROR: " + msg)

if not TARGET.exists():
    fail(f"missing target: {TARGET}")

src = TARGET.read_text(encoding="utf-8")

if MARKER in src:
    print(f"PATCH={PATCH}")
    print("APPLY=ALREADY_PRESENT")
    print("FILE=frontend/scripts/syncTsheetsCasualRuntime.mjs")
    raise SystemExit(0)

old = '''  // If brand-name span already exists (P03-B02+ build), skip injection
  if (src.includes("titlebar__brand-name")) {
    console.log("[tsheets-casual] Brand already present in " + file + ", skipping injection");
    patched = true;
    break;
  }
'''

new = '''  // TOS_TSHEETS_RUNTIME_SYNC_BRAND_GUARD_V1
  // Current TitleBar source owns the brand directly. A fresh Vite bundle may
  // contain the source-native brand icon without the legacy injected
  // titlebar__brand-name span. Treat either marker as an already-branded
  // runtime and never fail/build-mutate just because minification changed the
  // old JSX fallback pattern.
  if (src.includes("titlebar__brand-name") || src.includes("titlebar__brand-icon")) {
    console.log("[tsheets-casual] Source-native brand present in " + file + ", skipping legacy injection");
    patched = true;
    break;
  }
'''

count = src.count(old)
if count != 1:
    fail(f"expected exact brand guard block once, found {count}; refusing to guess")

src = src.replace(old, new, 1)
TARGET.write_text(src, encoding="utf-8")

verify = TARGET.read_text(encoding="utf-8")
checks = {
    "marker": MARKER in verify,
    "brand_name_guard": 'src.includes("titlebar__brand-name")' in verify,
    "brand_icon_guard": 'src.includes("titlebar__brand-icon")' in verify,
    "legacy_fallback_preserved": 'const pattern = /(children:)' in verify,
    "failure_guard_preserved": 'ERROR: No brand pattern found and no pre-existing brand span' in verify,
}
bad = [k for k, v in checks.items() if not v]
if bad:
    fail("verification failed: " + ", ".join(bad))

print(f"PATCH={PATCH}")
print("APPLY=PASS")
print("FILE=frontend/scripts/syncTsheetsCasualRuntime.mjs")
print("SOURCE_NATIVE_BRAND_ICON_ACCEPTED=YES")
print("BRAND_NAME_ACCEPTED=YES")
print("LEGACY_INJECTION_FALLBACK=UNCHANGED")
print("RUNTIME_SOURCE_TOUCHED=NO")
print("BACK_HOME_TOUCHED=NO")
print("FRAME_FIT_TOUCHED=NO")
print("AUTOSAVE_TOUCHED=NO")
print("BACKEND_TOUCHED=NO")
