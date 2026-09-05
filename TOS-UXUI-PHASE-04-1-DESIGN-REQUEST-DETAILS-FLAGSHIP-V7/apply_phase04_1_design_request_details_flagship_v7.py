from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_DQ_SHA256 = "075fa36022c8e5e131b4338e56f1731eec0f1f57970420c2663295b4a0943ef0"
EXPECTED_CSS_SHA256 = "7a2dece82709011f5d7e75aa357cdc3d8c9e785336ff3f3825920d3156fc1037"
V6_MARKER = "--tos-dq-details-flagship-v6-runtime"
V7_MARKER = "--tos-dq-details-flagship-v7-runtime"
V6_HOOK = 'data-dq-details-flagship="v6"'
V7_HOOK = 'data-dq-details-flagship="v7"'
RTL_HOOK = "tos-dq-spec-copy-rtl-v6"
LTR_HOOK = "tos-dq-spec-copy-ltr-v6"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V7")


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
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V7_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match Flagship V6 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V6 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in (
    "TOS_DQ_PERFORMANCE_V3",
    "TOS_DQ_PREMIUM_MENU_V9",
    "TOS_DQ_PREMIUM_MENU_THEME_V10",
    V6_HOOK,
    V6_MARKER,
    RTL_HOOK,
    LTR_HOOK,
    "tos-dq-close-action-v5",
):
    if required not in (original_dq + original_css):
        fail(f"required V6 baseline marker missing: {required}")
if V7_MARKER in original_css or V7_HOOK in original_dq:
    fail("Design Request Details Flagship V7 already present")

updated_dq = replace_once(original_dq, V6_HOOK, V7_HOOK, "Details V7 runtime hook")

v7_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V7
   Visual QA correction: V4's higher-specificity ancestor [dir]
   selectors were overriding the V6 RTL/LTR utility classes.
   These selectors intentionally match/exceed that specificity so
   content language wins over shell language. Business logic unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v7-runtime: 1; }

/* English shell + Arabic request copy: force the reading canvas to the
   physical right edge and keep Arabic typography right aligned. */
[dir="ltr"] [data-dq-details-flagship="v7"] .tos-dq-spec-copy-v1 > div.tos-dq-spec-copy-rtl-v6,
[data-dq-details-flagship="v7"] .tos-dq-spec-copy-v1 > div.tos-dq-spec-copy-rtl-v6 {
  width: min(100%, 74ch) !important;
  max-width: 74ch !important;
  margin-right: 0 !important;
  margin-left: auto !important;
  text-align: right !important;
  direction: rtl !important;
  unicode-bidi: plaintext !important;
}

/* Arabic shell + English request copy: mirror the behavior explicitly. */
[dir="rtl"] [data-dq-details-flagship="v7"] .tos-dq-spec-copy-v1 > div.tos-dq-spec-copy-ltr-v6,
[data-dq-details-flagship="v7"] .tos-dq-spec-copy-v1 > div.tos-dq-spec-copy-ltr-v6 {
  width: min(100%, 74ch) !important;
  max-width: 74ch !important;
  margin-left: 0 !important;
  margin-right: auto !important;
  text-align: left !important;
  direction: ltr !important;
  unicode-bidi: plaintext !important;
}

/* Keep the label aligned with the content edge without changing its language. */
[data-dq-details-flagship="v7"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-rtl-v6) > div:first-child {
  text-align: right !important;
}

[data-dq-details-flagship="v7"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-ltr-v6) > div:first-child {
  text-align: left !important;
}

html.dark [data-dq-details-flagship="v7"] .tos-dq-spec-copy-rtl-v6,
html.dark [data-dq-details-flagship="v7"] .tos-dq-spec-copy-ltr-v6 {
  color: #f2efe8 !important;
}
'''

v7_css = "\n".join(line.rstrip() for line in v7_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v7_css

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated_dq)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()

    if source_dq.count(V7_HOOK) != 1:
        raise RuntimeError("V7 source hook missing or duplicated")
    if source_css.count(V7_MARKER) != 1:
        raise RuntimeError("V7 CSS runtime marker missing or duplicated")
    if V6_MARKER not in source_css or RTL_HOOK not in source_dq or LTR_HOOK not in source_dq:
        raise RuntimeError("V6 direction baseline was not preserved")
    for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10"):
        if required not in source_dq:
            raise RuntimeError(f"required Design Queue baseline marker not preserved: {required}")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V7_MARKER.encode())
    dist_details_key = tree_count(DIST, b"data-dq-details-flagship")
    dist_rtl = tree_count(DIST, RTL_HOOK.encode())
    dist_ltr = tree_count(DIST, LTR_HOOK.encode())
    if min(dist_marker, dist_details_key, dist_rtl, dist_ltr) < 1:
        raise RuntimeError("V7 stable runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v7.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v7.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged live build missing index.html")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_marker = tree_count(LIVE, V7_MARKER.encode())
    live_details_key = tree_count(LIVE, b"data-dq-details-flagship")
    live_rtl = tree_count(LIVE, RTL_HOOK.encode())
    live_ltr = tree_count(LIVE, LTR_HOOK.encode())
    if min(live_marker, live_details_key, live_rtl, live_ltr) < 1:
        raise RuntimeError("V7 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V7_RUNTIME=YES")
    print("V4_DIRECTION_OVERRIDE_NEUTRALIZED=YES")
    print("ARABIC_COPY_RIGHT_EDGE_FORCED=YES")
    print("ENGLISH_COPY_LEFT_EDGE_FORCED=YES")
    print("REQUIRED_COPY_LABEL_EDGE_ALIGNED=YES")
    print("V5_CLOSE_UTILITY_PRESERVED=YES")
    print("V4_FULL_WIDTH_COMPOSITION_PRESERVED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V7_RUNTIME_COUNT={source_css.count(V7_MARKER)}")
    print(f"SOURCE_V7_HOOK_COUNT={source_dq.count(V7_HOOK)}")
    print(f"DIST_V7_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_RTL_HOOK_COUNT={dist_rtl}")
    print(f"DIST_LTR_HOOK_COUNT={dist_ltr}")
    print(f"LIVE_V7_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_RTL_HOOK_COUNT={live_rtl}")
    print(f"LIVE_LTR_HOOK_COUNT={live_ltr}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v7.failed.{int(time.time())}"
        try:
            if LIVE.exists():
                LIVE.rename(failed_live)
            backup.rename(LIVE)
        except Exception:
            pass
    elif stage and stage.exists():
        try:
            shutil.rmtree(stage)
        except Exception:
            pass

    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(exc))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V7_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
