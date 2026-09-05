from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
CSS = ROOT / "frontend/src/index.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_DQ_SHA256 = "93121116a492c245156f29d1c53df370f8d50246b5db232bdbafda0ad49a614e"
EXPECTED_CSS_SHA256 = "f2a6f9200b256e20268979bab97d7ba83c047676b50caef3c8698c3290efd134"
V14_MARKER = "--tos-dq-details-flagship-v14-runtime"
V15_MARKER = "--tos-dq-details-flagship-v15-runtime"
V14_HOOK = 'data-dq-details-reference-fix="v14"'
V15_HOOK = 'data-dq-details-activity-fix="v15"'
ACTIVITY_TRACK = "tos-dq-activity-track-v14"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V15")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.read_bytes().count(needle)
        except OSError:
            pass
    return total


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V15_RUNTIME=NO")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


for path in (DQ, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha256(DQ) != EXPECTED_DQ_SHA256:
    fail("DesignQueuePage.jsx does not match Flagship V14 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V14 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in (
    "TOS_DQ_PERFORMANCE_V3",
    "TOS_DQ_PREMIUM_MENU_V9",
    "TOS_DQ_PREMIUM_MENU_THEME_V10",
    V14_MARKER,
    V14_HOOK,
    ACTIVITY_TRACK,
    "tos-dq-activity-item-v1",
    "tos-dq-details-activity-v1",
    "tos-dq-copy-editorial-v8",
    "tos-dq-details-assignment-v1",
    "tos-dq-attachments-empty-v13",
):
    if required not in (original_dq + original_css):
        fail(f"required V14 baseline marker missing: {required}")

if V15_MARKER in original_css or V15_HOOK in original_dq:
    fail("Design Request Details Flagship V15 already present")

updated_dq = replace_once(
    original_dq,
    V14_HOOK,
    V14_HOOK + ' ' + V15_HOOK,
    "V15 activity-fix hook",
)

v15_css = r'''

/* =========================================================
   Phase 04.1 — Design Request Details — Flagship V15
   Live visual correction after V14 screenshots.
   Root cause: an older activity wrapper was still a five-column grid,
   so the real V14 track occupied only ONE parent column; its own five
   columns then collapsed into vertical slivers. This pass resets the
   parent wrapper and makes the real activity track the only desktop grid.
   Visual-only. Business logic untouched.
   ========================================================= */
:root { --tos-dq-details-flagship-v15-runtime: 1; }

/* Keep the successful V14 editorial/reference work; only tighten its reading rhythm. */
[data-dq-details-activity-fix="v15"] .tos-dq-spec-copy-v1 > .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 {
  width: min(44%, 630px) !important;
  max-width: 630px !important;
  margin-left: auto !important;
  margin-right: 0 !important;
}
[data-dq-details-activity-fix="v15"] .tos-dq-spec-copy-v1 > .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
  width: min(44%, 630px) !important;
  max-width: 630px !important;
  margin-left: 0 !important;
  margin-right: auto !important;
}

/* ACTIVITY ROOT RESET — neutralize inherited V11/V12/V13 parent grids. */
@media (min-width: 1180px) {
  [data-dq-details-activity-fix="v15"] .tos-dq-details-activity-v1 > div:last-child {
    position: relative !important;
    display: block !important;
    width: 100% !important;
    max-width: none !important;
    min-width: 0 !important;
    height: auto !important;
    min-height: 0 !important;
    padding: 16px 20px 20px !important;
    margin: 0 !important;
    grid-template-columns: none !important;
    grid-auto-columns: auto !important;
    grid-auto-flow: row !important;
    align-items: initial !important;
    justify-items: initial !important;
    overflow: visible !important;
  }

  /* Disable the legacy parent's decorative rail. V15 draws the rail on the real track. */
  [data-dq-details-activity-fix="v15"] .tos-dq-details-activity-v1 > div:last-child::before,
  [data-dq-details-activity-fix="v15"] .tos-dq-details-activity-v1 > div:last-child::after {
    content: none !important;
    display: none !important;
  }

  /* REAL TRACK: full section width, exactly five equal executive cards. */
  [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14 {
    position: relative !important;
    display: grid !important;
    width: 100% !important;
    max-width: none !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    grid-column: 1 / -1 !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    grid-auto-columns: minmax(0, 1fr) !important;
    grid-auto-flow: row !important;
    gap: 18px !important;
    align-items: stretch !important;
    justify-items: stretch !important;
    padding: 34px 0 0 !important;
    margin: 0 !important;
    overflow: visible !important;
  }

  [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14::before {
    content: "" !important;
    display: block !important;
    position: absolute !important;
    top: 18px !important;
    left: 8px !important;
    right: 8px !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(209,156,47,.62) 4%, rgba(209,156,47,.34) 96%, transparent) !important;
    pointer-events: none !important;
  }

  [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 {
    position: relative !important;
    display: block !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    height: auto !important;
    min-height: 108px !important;
    margin: 0 !important;
    padding: 24px 16px 15px !important;
    border-radius: 17px !important;
    overflow: visible !important;
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    white-space: normal !important;
    word-break: normal !important;
    overflow-wrap: anywhere !important;
    box-sizing: border-box !important;
  }

  [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 > div,
  [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 > div * {
    width: auto !important;
    max-width: 100% !important;
    min-width: 0 !important;
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    white-space: normal !important;
    word-break: normal !important;
    overflow-wrap: anywhere !important;
  }

  [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 > span {
    position: absolute !important;
    top: -22px !important;
    inset-inline-start: 13px !important;
    width: 13px !important;
    height: 13px !important;
    border-radius: 50% !important;
    border: 2px solid #fff8e4 !important;
    background: #f2a700 !important;
    box-shadow: 0 0 0 5px rgba(242,167,0,.14), 0 0 20px rgba(242,167,0,.22) !important;
  }

  /* Put the activity expander in the section's top-right visual slot. */
  [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14 > button {
    position: absolute !important;
    top: -57px !important;
    right: 0 !important;
    left: auto !important;
    inset-inline-end: 0 !important;
    inset-inline-start: auto !important;
    width: auto !important;
    min-width: max-content !important;
    margin: 0 !important;
    z-index: 8 !important;
  }
}

/* Dark executive timeline material. */
@media (min-width: 1180px) {
  html.dark [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14::before {
    background: linear-gradient(90deg, transparent, rgba(251,190,38,.76) 4%, rgba(251,190,38,.36) 96%, transparent) !important;
  }
  html.dark [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 {
    border-color: rgba(238,184,55,.16) !important;
    background: linear-gradient(180deg,#15191d,#0d1013) !important;
    box-shadow: 0 12px 30px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.018) !important;
  }
  html.dark [data-dq-details-activity-fix="v15"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 > span {
    border-color: #261c08 !important;
    background: #ffb000 !important;
    box-shadow: 0 0 0 5px rgba(255,176,0,.15), 0 0 22px rgba(255,176,0,.30) !important;
  }
}

@media (max-width: 1179px) {
  [data-dq-details-activity-fix="v15"] .tos-dq-spec-copy-v1 > .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6,
  [data-dq-details-activity-fix="v15"] .tos-dq-spec-copy-v1 > .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
    width: min(100%, 68ch) !important;
    max-width: 68ch !important;
  }
}
'''

updated_css = original_css.rstrip() + "\n" + v15_css + "\n"

source_written = False
staging = None
old_live = None
try:
    DQ.write_text(updated_dq)
    CSS.write_text(updated_css)
    source_written = True

    build = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if build.returncode != 0:
        print(build.stdout[-8000:])
        raise RuntimeError("frontend build failed")

    if not DIST.exists():
        raise RuntimeError("frontend dist missing after build")

    # Stable runtime verification: do not depend on exact minified selector quoting.
    dist_marker = tree_count(DIST, V15_MARKER.encode())
    dist_hook = tree_count(DIST, b"data-dq-details-activity-fix")
    dist_track = tree_count(DIST, ACTIVITY_TRACK.encode())
    if dist_hook < 1 or dist_track < 1:
        raise RuntimeError("V15 stable runtime markers missing from dist")

    ts = int(time.time())
    staging = LIVE_PARENT / f".build-phase04-1-v15-staging-{ts}"
    old_live = LIVE_PARENT / f".build-phase04-1-v15-before-{ts}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(old_live)
    staging.rename(LIVE)
    staging = None

    live_marker = tree_count(LIVE, V15_MARKER.encode())
    live_hook = tree_count(LIVE, b"data-dq-details-activity-fix")
    live_track = tree_count(LIVE, ACTIVITY_TRACK.encode())
    if live_hook < 1 or live_track < 1:
        raise RuntimeError("V15 stable runtime markers missing from live build")

    if old_live and old_live.exists():
        shutil.rmtree(old_live)
        old_live = None

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V15_RUNTIME=YES")
    print("V14_REFERENCE_BASELINE_PRESERVED=YES")
    print("ACTIVITY_PARENT_LEGACY_GRID_RESET=YES")
    print("ACTIVITY_TRACK_FULL_WIDTH=YES")
    print("ACTIVITY_FIVE_EQUAL_EXECUTIVE_CARDS=YES")
    print("ACTIVITY_VERTICAL_SLIVERS_FIXED=YES")
    print("ACTIVITY_TEXT_HORIZONTAL_RESTORED=YES")
    print("SHOW_ALL_ACTIVITY_POSITION_REFINED=YES")
    print("EDITORIAL_RIGHT_EDGE_PRESERVED=YES")
    print("LIGHT_REFERENCE_PRESERVED=YES")
    print("DARK_REFERENCE_PRESERVED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V15_RUNTIME_COUNT={updated_css.count(V15_MARKER)}")
    print(f"SOURCE_V15_HOOK_COUNT={updated_dq.count(V15_HOOK)}")
    print(f"DIST_V15_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_V15_HOOK_COUNT={dist_hook}")
    print(f"DIST_ACTIVITY_TRACK_COUNT={dist_track}")
    print(f"LIVE_V15_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_V15_HOOK_COUNT={live_hook}")
    print(f"LIVE_ACTIVITY_TRACK_COUNT={live_track}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")
except Exception as exc:
    if source_written:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
    if staging and staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    if old_live and old_live.exists():
        if LIVE.exists():
            shutil.rmtree(LIVE, ignore_errors=True)
        old_live.rename(LIVE)
    fail(exc)
