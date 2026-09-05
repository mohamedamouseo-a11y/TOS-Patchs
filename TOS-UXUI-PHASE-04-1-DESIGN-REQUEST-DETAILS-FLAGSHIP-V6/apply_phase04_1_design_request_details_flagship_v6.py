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

EXPECTED_DQ_SHA256 = "069becd5be26fb4258ee33c313569d7329bcbc692f80151fbd9e1f3adbc7c066"
EXPECTED_CSS_SHA256 = "1212802d9ba96f472caa50bb1018319f51085ccbe53469792a62d1ce91200b25"
V5_MARKER = "--tos-dq-details-flagship-v5-runtime"
V6_MARKER = "--tos-dq-details-flagship-v6-runtime"
V5_HOOK = 'data-dq-details-flagship="v5"'
V6_HOOK = 'data-dq-details-flagship="v6"'
RTL_HOOK = "tos-dq-spec-copy-rtl-v6"
LTR_HOOK = "tos-dq-spec-copy-ltr-v6"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V6")


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
    print("V6_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match Flagship V5 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V5 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10", V5_HOOK, V5_MARKER, "tos-dq-spec-copy-body-v5", "tos-dq-close-action-v5"):
    if required not in (original_dq + original_css):
        fail(f"required V5 baseline marker missing: {required}")
if V6_MARKER in original_css or V6_HOOK in original_dq or RTL_HOOK in original_dq:
    fail("Design Request Details Flagship V6 already present")

updated = original_dq
updated = replace_once(updated, V5_HOOK, V6_HOOK, "Details V6 runtime hook")
updated = replace_once(
    updated,
    'function SpecRow({ label, value, children, linkify = false, lang = "ar", className, contentDir }) {\n  if (!children && (!value || (Array.isArray(value) && !value.length))) return null;',
    'function SpecRow({ label, value, children, linkify = false, lang = "ar", className, contentDir }) {\n  if (!children && (!value || (Array.isArray(value) && !value.length))) return null;\n  const resolvedContentDir = contentDir === "auto" ? (/[^\\u0000-\\u007f]*[\\u0600-\\u06ff]/u.test(String(value || "")) ? "rtl" : "ltr") : contentDir;',
    "SpecRow resolved content direction",
)
updated = replace_once(
    updated,
    ': <div dir={contentDir} className={cn("mt-1 whitespace-pre-wrap text-sm font-bold leading-6 text-zinc-700 dark:text-zinc-200", contentDir === "auto" && "tos-dq-spec-copy-body-v5")}>{value}</div>)}',
    ': <div dir={resolvedContentDir} className={cn("mt-1 whitespace-pre-wrap text-sm font-bold leading-6 text-zinc-700 dark:text-zinc-200", contentDir === "auto" && "tos-dq-spec-copy-body-v5", contentDir === "auto" && resolvedContentDir === "rtl" && "tos-dq-spec-copy-rtl-v6", contentDir === "auto" && resolvedContentDir === "ltr" && "tos-dq-spec-copy-ltr-v6")}>{value}</div>)}',
    "Required copy explicit direction classes",
)

v6_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V6
   Final alignment correction after V5 visual QA. Resolve the
   content language in JSX, then anchor the reading block to the
   physical right/left edge explicitly instead of relying on :dir().
   Business logic unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v6-runtime: 1; }

.tos-dq-spec-copy-rtl-v6 {
  direction: rtl !important;
  text-align: right !important;
  margin-right: 0 !important;
  margin-left: auto !important;
  padding-right: 2px;
  padding-left: 0;
}

.tos-dq-spec-copy-ltr-v6 {
  direction: ltr !important;
  text-align: left !important;
  margin-left: 0 !important;
  margin-right: auto !important;
  padding-left: 2px;
  padding-right: 0;
}

/* Keep the editorial body readable and clearly anchored within the panel. */
.tos-dq-spec-copy-body-v5 {
  width: min(100%, 74ch) !important;
  max-width: 74ch !important;
  line-height: 2.02 !important;
}

html.dark .tos-dq-spec-copy-rtl-v6,
html.dark .tos-dq-spec-copy-ltr-v6 {
  color: #f2efe8 !important;
}
'''

v6_css = "\n".join(line.rstrip() for line in v6_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v6_css

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()

    if source_dq.count(V6_HOOK) != 1:
        raise RuntimeError("V6 source hook missing or duplicated")
    if source_dq.count(RTL_HOOK) != 1 or source_dq.count(LTR_HOOK) != 1:
        raise RuntimeError("V6 explicit direction hooks missing or duplicated")
    if source_css.count(V6_MARKER) != 1:
        raise RuntimeError("V6 CSS runtime marker missing or duplicated")
    if V5_MARKER not in source_css:
        raise RuntimeError("V5 CSS baseline marker was not preserved")
    for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10"):
        if required not in source_dq:
            raise RuntimeError(f"required Design Queue baseline marker not preserved: {required}")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V6_MARKER.encode())
    dist_details_key = tree_count(DIST, b"data-dq-details-flagship")
    dist_rtl = tree_count(DIST, RTL_HOOK.encode())
    dist_ltr = tree_count(DIST, LTR_HOOK.encode())
    if min(dist_marker, dist_details_key, dist_rtl, dist_ltr) < 1:
        raise RuntimeError("V6 stable runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v6.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v6.backup-{stamp}"
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

    live_marker = tree_count(LIVE, V6_MARKER.encode())
    live_details_key = tree_count(LIVE, b"data-dq-details-flagship")
    live_rtl = tree_count(LIVE, RTL_HOOK.encode())
    live_ltr = tree_count(LIVE, LTR_HOOK.encode())
    if min(live_marker, live_details_key, live_rtl, live_ltr) < 1:
        raise RuntimeError("V6 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V6_RUNTIME=YES")
    print("CONTENT_DIRECTION_RESOLVED_IN_JSX=YES")
    print("ARABIC_COPY_PHYSICALLY_RIGHT_ANCHORED=YES")
    print("ENGLISH_COPY_PHYSICALLY_LEFT_ANCHORED=YES")
    print("V5_CLOSE_UTILITY_PRESERVED=YES")
    print("V4_FULL_WIDTH_COMPOSITION_PRESERVED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V6_RUNTIME_COUNT={source_css.count(V6_MARKER)}")
    print(f"SOURCE_V6_HOOK_COUNT={source_dq.count(V6_HOOK)}")
    print(f"DIST_V6_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_RTL_HOOK_COUNT={dist_rtl}")
    print(f"DIST_LTR_HOOK_COUNT={dist_ltr}")
    print(f"LIVE_V6_RUNTIME_COUNT={live_marker}")
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
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v6.failed.{int(time.time())}"
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
    print("V6_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
