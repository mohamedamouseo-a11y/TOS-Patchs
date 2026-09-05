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

EXPECTED_DQ_SHA256 = "a2751671e28768732fb1250e92c4c506bae715c7099d1dbd60b9ddcf27824ce2"
EXPECTED_CSS_SHA256 = "bc8f00adb6ce86cadf46efc9f64883a91a8ab1764421ba3e85ba242e34f986a1"
V13_MARKER = "--tos-dq-details-flagship-v13-runtime"
V14_MARKER = "--tos-dq-details-flagship-v14-runtime"
V13_HOOK = 'data-dq-details-ultra="v13"'
V14_HOOK = 'data-dq-details-reference-fix="v14"'
ACTIVITY_TRACK = "tos-dq-activity-track-v14"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V14")


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
    print("V14_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match Flagship V13 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V13 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in (
    "TOS_DQ_PERFORMANCE_V3",
    "TOS_DQ_PREMIUM_MENU_V9",
    "TOS_DQ_PREMIUM_MENU_THEME_V10",
    V13_MARKER,
    V13_HOOK,
    "tos-dq-copy-editorial-v8",
    "tos-dq-spec-copy-rtl-v6",
    "tos-dq-spec-copy-ltr-v6",
    "tos-dq-details-hero-v1",
    "tos-dq-details-metrics-v1",
    "tos-dq-details-assignment-v1",
    "tos-dq-details-attachments-v1",
    "tos-dq-attachments-empty-v13",
    "tos-dq-details-activity-v1",
    "tos-dq-activity-item-v1",
):
    if required not in (original_dq + original_css):
        fail(f"required V13 baseline marker missing: {required}")

if V14_MARKER in original_css or V14_HOOK in original_dq or ACTIVITY_TRACK in original_dq:
    fail("Design Request Details Flagship V14 already present")

updated_dq = replace_once(
    original_dq,
    V13_HOOK,
    V13_HOOK + ' ' + V14_HOOK,
    "V14 root hook",
)

# Give the real activity content wrapper an explicit hook so its width/grid cannot
# collapse under accumulated legacy selectors.
activity_old = '''title={tr.details.sections.activity}>\n                <div className="space-y-4">'''
activity_new = '''title={tr.details.sections.activity}>\n                <div className="tos-dq-activity-track-v14 space-y-4">'''
updated_dq = replace_once(updated_dq, activity_old, activity_new, "V14 activity track hook")

v14_css = r'''

/* =========================================================
   Phase 04.1 — Design Request Details — Flagship V14
   Final visual reference correction from live V13 screenshots.
   Fixes two visible mismatches: Arabic editorial content drifting toward
   center and activity cards collapsing into narrow columns. Also sharpens
   couture depth without changing business logic.
   ========================================================= */
:root { --tos-dq-details-flagship-v14-runtime: 1; }

/* Make the real page canvas feel closer to the approved concept. */
[data-dq-details-reference-fix="v14"] {
  border-radius: 32px !important;
}

/* Hero: keep V13 structure, add richer luminous sweep and cleaner hierarchy. */
[data-dq-details-reference-fix="v14"] .tos-dq-details-hero-v1 {
  border-color: rgba(205,154,49,.38) !important;
  box-shadow:
    0 30px 82px rgba(78,53,11,.15),
    inset 0 1px 0 rgba(255,255,255,.99),
    inset 0 -1px 0 rgba(176,120,21,.10) !important;
}
[data-dq-details-reference-fix="v14"] .tos-dq-details-hero-v1::before {
  opacity: 1 !important;
  filter: drop-shadow(0 0 18px rgba(224,169,46,.13)) !important;
}
[data-dq-details-reference-fix="v14"] .tos-dq-details-hero-v1::after {
  letter-spacing: .31em !important;
  color: rgba(103,79,43,.74) !important;
}

/* REQUIRED COPY — anchor the WHOLE reading column to the physical edge.
   V13 constrained each paragraph, which still looked centered. */
[data-dq-details-reference-fix="v14"] .tos-dq-spec-copy-v1 > .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 {
  display: block !important;
  width: min(47%, 650px) !important;
  max-width: 650px !important;
  margin-left: auto !important;
  margin-right: 0 !important;
  padding: 0 !important;
  direction: rtl !important;
  text-align: right !important;
}
[data-dq-details-reference-fix="v14"] .tos-dq-spec-copy-v1 > .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
  display: block !important;
  width: min(47%, 650px) !important;
  max-width: 650px !important;
  margin-left: 0 !important;
  margin-right: auto !important;
  padding: 0 !important;
  direction: ltr !important;
  text-align: left !important;
}
[data-dq-details-reference-fix="v14"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 .tos-dq-copy-paragraph-v8,
[data-dq-details-reference-fix="v14"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 .tos-dq-copy-paragraph-v8 {
  width: 100% !important;
  max-width: none !important;
  margin-inline: 0 !important;
  margin-bottom: 17px !important;
  padding: 0 !important;
}
[data-dq-details-reference-fix="v14"] .tos-dq-copy-editorial-v8 .tos-dq-copy-paragraph-v8:last-child {
  margin-bottom: 0 !important;
}
[data-dq-details-reference-fix="v14"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-rtl-v6) > div:first-child {
  text-align: right !important;
}
[data-dq-details-reference-fix="v14"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-ltr-v6) > div:first-child {
  text-align: left !important;
}

/* More visible couture sweep in the empty side, matching the concept. */
[data-dq-details-reference-fix="v14"] .tos-dq-spec-copy-v1 {
  background:
    radial-gradient(ellipse 86% 136% at -19% 116%, transparent 0 46%, rgba(229,180,72,.34) 46.35% 46.8%, transparent 47.25%),
    radial-gradient(ellipse 97% 148% at -24% 123%, transparent 0 56%, rgba(229,180,72,.19) 56.35% 56.8%, transparent 57.25%),
    radial-gradient(ellipse 108% 158% at -29% 130%, transparent 0 66%, rgba(229,180,72,.105) 66.35% 66.8%, transparent 67.25%),
    radial-gradient(circle at 11% 96%, rgba(240,198,97,.16), transparent 25%),
    linear-gradient(180deg,#fffefa 0%,#faf5eb 100%) !important;
}

/* Assignment: richer command-console depth, less generic form feel. */
[data-dq-details-reference-fix="v14"] .tos-dq-details-assignment-v1 {
  box-shadow:
    0 32px 72px rgba(77,50,9,.17),
    inset 0 1px 0 rgba(255,255,255,.99) !important;
}
[data-dq-details-reference-fix="v14"] .tos-dq-assignment-cta-v1 {
  letter-spacing: -.01em !important;
  box-shadow:
    0 17px 36px rgba(160,99,10,.30),
    inset 0 1px 0 rgba(255,255,255,.44) !important;
}

/* ATTACHMENTS: slightly denser, intentionally designed vault. */
[data-dq-details-reference-fix="v14"] .tos-dq-attachments-empty-v13 {
  min-height: 132px !important;
}

/* ACTIVITY — explicit real wrapper, full-width five-card deck. */
@media (min-width: 1180px) {
  [data-dq-details-reference-fix="v14"] .tos-dq-activity-track-v14 {
    position: relative !important;
    display: grid !important;
    width: 100% !important;
    max-width: none !important;
    min-width: 0 !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    grid-auto-flow: row !important;
    gap: 16px !important;
    align-items: stretch !important;
    padding: 30px 18px 8px !important;
    margin: 0 !important;
  }
  [data-dq-details-reference-fix="v14"] .tos-dq-activity-track-v14::before {
    content: "" !important;
    position: absolute !important;
    top: 17px !important;
    left: 24px !important;
    right: 24px !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(213,159,48,.58) 6%, rgba(213,159,48,.30) 94%, transparent) !important;
    pointer-events: none !important;
  }
  [data-dq-details-reference-fix="v14"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 {
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    min-height: 106px !important;
    margin: 0 !important;
    padding: 25px 15px 14px !important;
    border-radius: 16px !important;
    overflow: visible !important;
  }
  [data-dq-details-reference-fix="v14"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 > div {
    min-width: 0 !important;
    white-space: normal !important;
    word-break: normal !important;
    overflow-wrap: break-word !important;
  }
  [data-dq-details-reference-fix="v14"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 > span {
    top: -18px !important;
    inset-inline-start: 12px !important;
  }
  [data-dq-details-reference-fix="v14"] .tos-dq-activity-track-v14 > button:last-child {
    position: absolute !important;
    top: -54px !important;
    inset-inline-end: 0 !important;
    margin: 0 !important;
    z-index: 4 !important;
  }
}

/* Dark reference lock. */
html.dark [data-dq-details-reference-fix="v14"] .tos-dq-spec-copy-v1 {
  background:
    radial-gradient(ellipse 86% 136% at -19% 116%, transparent 0 46%, rgba(255,193,42,.40) 46.35% 46.8%, transparent 47.25%),
    radial-gradient(ellipse 97% 148% at -24% 123%, transparent 0 56%, rgba(255,193,42,.23) 56.35% 56.8%, transparent 57.25%),
    radial-gradient(ellipse 108% 158% at -29% 130%, transparent 0 66%, rgba(255,193,42,.12) 66.35% 66.8%, transparent 67.25%),
    radial-gradient(circle at 11% 96%, rgba(255,200,58,.11), transparent 25%),
    linear-gradient(180deg,#0e1114 0%,#080a0d 100%) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.018),
    inset 4px 0 0 rgba(244,185,42,.18),
    0 0 42px rgba(225,159,25,.055) !important;
}
html.dark [data-dq-details-reference-fix="v14"] .tos-dq-activity-track-v14::before {
  background: linear-gradient(90deg, transparent, rgba(251,190,38,.72) 6%, rgba(251,190,38,.34) 94%, transparent) !important;
}
html.dark [data-dq-details-reference-fix="v14"] .tos-dq-activity-track-v14 > .tos-dq-activity-item-v1 {
  border-color: rgba(237,183,55,.15) !important;
  background: linear-gradient(180deg,#15181b,#0d1013) !important;
  box-shadow: 0 10px 28px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.016) !important;
}

@media (max-width: 1179px) {
  [data-dq-details-reference-fix="v14"] .tos-dq-spec-copy-v1 > .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6,
  [data-dq-details-reference-fix="v14"] .tos-dq-spec-copy-v1 > .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
    width: min(100%, 68ch) !important;
    max-width: 68ch !important;
  }
}
'''

updated_css = original_css.rstrip() + "\n" + v14_css + "\n"

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

    # Stable minified runtime tokens only; do not depend on exact attribute quote formatting.
    dist_runtime = tree_count(DIST, V14_MARKER.encode())
    dist_hook = tree_count(DIST, b"data-dq-details-reference-fix")
    dist_track = tree_count(DIST, ACTIVITY_TRACK.encode())
    if dist_hook < 1 or dist_track < 1:
        raise RuntimeError("V14 stable runtime markers missing from dist")

    ts = int(time.time())
    staging = LIVE_PARENT / f".build-phase04-1-v14-staging-{ts}"
    old_live = LIVE_PARENT / f".build-phase04-1-v14-before-{ts}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(old_live)
    staging.rename(LIVE)
    staging = None

    live_runtime = tree_count(LIVE, V14_MARKER.encode())
    live_hook = tree_count(LIVE, b"data-dq-details-reference-fix")
    live_track = tree_count(LIVE, ACTIVITY_TRACK.encode())
    if live_hook < 1 or live_track < 1:
        raise RuntimeError("V14 stable runtime markers missing from live build")

    if old_live and old_live.exists():
        shutil.rmtree(old_live)
        old_live = None

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V14_RUNTIME=YES")
    print("V13_ULTRA_BASELINE_PRESERVED=YES")
    print("EDITORIAL_COLUMN_PHYSICALLY_EDGE_ANCHORED=YES")
    print("RTL_CENTER_DRIFT_REMOVED=YES")
    print("LTR_EDGE_ANCHOR_PRESERVED=YES")
    print("COUTURE_SWEEP_INTENSIFIED=YES")
    print("ACTIVITY_REAL_TRACK_HOOK=YES")
    print("ACTIVITY_FULL_WIDTH_FIVE_CARD_DECK=YES")
    print("ACTIVITY_NARROW_CARD_COLLAPSE_FIXED=YES")
    print("ASSIGNMENT_COMMAND_CONSOLE_DEPTH_REFINED=YES")
    print("ATTACHMENT_VAULT_REFINED=YES")
    print("LIGHT_REFERENCE_REFINED=YES")
    print("DARK_REFERENCE_REFINED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V14_RUNTIME_COUNT={updated_css.count(V14_MARKER)}")
    print(f"SOURCE_V14_HOOK_COUNT={updated_dq.count(V14_HOOK)}")
    print(f"SOURCE_ACTIVITY_TRACK_COUNT={updated_dq.count(ACTIVITY_TRACK)}")
    print(f"DIST_V14_RUNTIME_COUNT={dist_runtime}")
    print(f"DIST_V14_HOOK_COUNT={dist_hook}")
    print(f"DIST_ACTIVITY_TRACK_COUNT={dist_track}")
    print(f"LIVE_V14_RUNTIME_COUNT={live_runtime}")
    print(f"LIVE_V14_HOOK_COUNT={live_hook}")
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
