#!/usr/bin/env python3
from pathlib import Path

PATCH = "TOS-TWS-TSHEETS-RUNTIME-BASE-V1"
ROOT = Path.cwd()
TARGET = ROOT / "vendor" / "tsheets-casual-upstream" / "apps" / "web" / "vite.config.ts"
MARKER = "TOS_TSHEETS_RUNTIME_BASE_V1"

def fail(msg):
    raise SystemExit("ERROR: " + msg)

if not TARGET.exists():
    fail(f"missing target: {TARGET}")

src = TARGET.read_text(encoding="utf-8")

if MARKER in src:
    print(f"PATCH={PATCH}")
    print("APPLY=ALREADY_PRESENT")
    print("FILE=vendor/tsheets-casual-upstream/apps/web/vite.config.ts")
    raise SystemExit(0)

old_comment = """// `PAGES_BASE` lets the GitHub Pages workflow build for /sheets/ without
// committing that path into the repo (local dev stays at /).
const base = process.env.PAGES_BASE ?? '/';
"""

new_comment = """// TOS_TSHEETS_RUNTIME_BASE_V1
// `PAGES_BASE` still overrides the base for GitHub Pages or other targets.
// Local dev stays at `/`, while production builds default to the TOS mount
// path so generated index.html references /tws-casual-runtime/assets/... .
const base = process.env.PAGES_BASE ?? (process.env.NODE_ENV === 'production' ? '/tws-casual-runtime/' : '/');
"""

count = src.count(old_comment)
if count != 1:
    fail(f"expected base block exactly once, found {count}; refusing to guess")

src = src.replace(old_comment, new_comment, 1)
TARGET.write_text(src, encoding="utf-8")

verify = TARGET.read_text(encoding="utf-8")
checks = {
    "marker": MARKER in verify,
    "pages_base_override": "process.env.PAGES_BASE ??" in verify,
    "prod_tos_base": "'/tws-casual-runtime/'" in verify,
    "dev_root_base": ": '/'" in verify,
    "define_config_base": "export default defineConfig({\n  base," in verify,
}
bad = [k for k, v in checks.items() if not v]
if bad:
    fail("verification failed: " + ", ".join(bad))

print(f"PATCH={PATCH}")
print("APPLY=PASS")
print("FILE=vendor/tsheets-casual-upstream/apps/web/vite.config.ts")
print("PRODUCTION_BASE=/tws-casual-runtime/")
print("DEV_BASE=/")
print("PAGES_BASE_OVERRIDE=PRESERVED")
print("AUTOSAVE_TOUCHED=NO")
print("RECENTS_TOUCHED=NO")
print("DRIVE_SYNC_TOUCHED=NO")
print("BACK_HOME_TOUCHED=NO")
print("FRAME_FIT_TOUCHED=NO")
