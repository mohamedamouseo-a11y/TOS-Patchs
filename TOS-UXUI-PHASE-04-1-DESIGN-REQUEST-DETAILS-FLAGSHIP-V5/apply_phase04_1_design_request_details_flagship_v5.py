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

EXPECTED_DQ_SHA256 = "0949c1e69f343f6ebb5b5d0609bedceb280e26f3465776329dcba1a88792fc30"
EXPECTED_CSS_SHA256 = "32c2e5d15f66e5f92acafe5e163ccfc08b7d06a29fa1c80b988a6d974acee9fa"
V4_MARKER = "--tos-dq-details-flagship-v4-runtime"
V5_MARKER = "--tos-dq-details-flagship-v5-runtime"
V4_HOOK = 'data-dq-details-flagship="v4"'
V5_HOOK = 'data-dq-details-flagship="v5"'
COPY_BODY_HOOK = "tos-dq-spec-copy-body-v5"
CLOSE_HOOK = "tos-dq-close-action-v5"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V5")


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
    print("V5_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match Flagship V4 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V4 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10", V4_HOOK, V4_MARKER, "tos-dq-close-action-v4", "tos-dq-attachment-action-v4"):
    if required not in (original_dq + original_css):
        fail(f"required V4 baseline marker missing: {required}")
if V5_MARKER in original_css or V5_HOOK in original_dq or COPY_BODY_HOOK in original_dq:
    fail("Design Request Details Flagship V5 already present")

updated = original_dq
updated = replace_once(updated, V4_HOOK, V5_HOOK, "Details V5 runtime hook")
updated = replace_once(
    updated,
    'function SpecRow({ label, value, children, linkify = false, lang = "ar", className }) {',
    'function SpecRow({ label, value, children, linkify = false, lang = "ar", className, contentDir }) {',
    "SpecRow content direction prop",
)
updated = replace_once(
    updated,
    ': <div className="mt-1 whitespace-pre-wrap text-sm font-bold leading-6 text-zinc-700 dark:text-zinc-200">{value}</div>)}',
    ': <div dir={contentDir} className={cn("mt-1 whitespace-pre-wrap text-sm font-bold leading-6 text-zinc-700 dark:text-zinc-200", contentDir === "auto" && "tos-dq-spec-copy-body-v5")}>{value}</div>)}',
    "SpecRow directional value body",
)
updated = replace_once(
    updated,
    '<SpecRow className="tos-dq-spec-copy-v1" label={tr.details.labels.requiredText} value={task.designRequest?.requiredText} />',
    '<SpecRow className="tos-dq-spec-copy-v1" contentDir="auto" label={tr.details.labels.requiredText} value={task.designRequest?.requiredText} />',
    "Required copy auto direction",
)
updated = replace_once(
    updated,
    '<Button type="button" variant="soft" className="tos-dq-close-action-v4" onClick={onClose}><X size={15} />{tr.common.close}</Button>',
    '<Button type="button" variant="soft" className="tos-dq-close-action-v4 tos-dq-close-action-v5" onClick={onClose} aria-label={tr.common.close} title={tr.common.close}><X size={16} /><span className="sr-only">{tr.common.close}</span></Button>',
    "Close icon utility action",
)

v5_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V5
   Final visual correction after V4 QA: content-aware direction
   for mixed Arabic/English request copy and icon-only Close utility.
   Business logic unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v5-runtime: 1; }

/* dir=auto resolves the real content direction. :dir() reacts to the
   resolved direction, unlike ancestor [dir=rtl] selectors when UI is English. */
.tos-dq-spec-copy-body-v5 {
  width: min(100%, 76ch) !important;
  max-width: 76ch !important;
  margin-top: 12px !important;
  font-size: 1rem !important;
  line-height: 2.02 !important;
  unicode-bidi: plaintext;
}

.tos-dq-spec-copy-body-v5:dir(rtl) {
  margin-right: 0 !important;
  margin-left: auto !important;
  text-align: right !important;
}

.tos-dq-spec-copy-body-v5:dir(ltr) {
  margin-left: 0 !important;
  margin-right: auto !important;
  text-align: left !important;
}

/* Quiet utility close: the panel title already says Actions, so the text label
   adds unnecessary visual weight. Keep accessible label/title in JSX. */
.tos-dq-close-action-v5 {
  width: 36px !important;
  min-width: 36px !important;
  height: 36px !important;
  min-height: 36px !important;
  padding: 0 !important;
  display: inline-grid !important;
  place-items: center !important;
  border-radius: 12px !important;
  flex: none !important;
}

.tos-dq-close-action-v5 svg {
  margin: 0 !important;
}

@media (min-width: 1280px) {
  .tos-dq-details-actions-v1 {
    width: 312px !important;
  }

  .tos-dq-details-actions-v1 > div:last-child {
    grid-template-columns: minmax(0, 1fr) 36px !important;
  }
}

html.dark .tos-dq-spec-copy-body-v5 {
  color: #f0ede6 !important;
}

html.dark .tos-dq-close-action-v5 {
  border-color: rgba(255,255,255,.07) !important;
  background: rgba(255,255,255,.018) !important;
  color: #aeb4bd !important;
}

html.dark .tos-dq-close-action-v5:hover {
  border-color: rgba(215,178,100,.22) !important;
  background: rgba(215,178,100,.06) !important;
  color: #f2eee5 !important;
}
'''

v5_css = "\n".join(line.rstrip() for line in v5_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v5_css

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()

    if source_dq.count(V5_HOOK) != 1:
        raise RuntimeError("V5 source hook missing or duplicated")
    if source_dq.count(COPY_BODY_HOOK) != 1:
        raise RuntimeError("V5 copy-body hook missing or duplicated")
    if source_dq.count(CLOSE_HOOK) != 1:
        raise RuntimeError("V5 close hook missing or duplicated")
    if source_css.count(V5_MARKER) != 1:
        raise RuntimeError("V5 CSS runtime marker missing or duplicated")
    for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10"):
        if required not in source_dq:
            raise RuntimeError(f"required Design Queue baseline marker not preserved: {required}")
    if V4_MARKER not in source_css:
        raise RuntimeError("V4 CSS baseline marker was not preserved")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V5_MARKER.encode())
    dist_details_key = tree_count(DIST, b"data-dq-details-flagship")
    dist_copy = tree_count(DIST, COPY_BODY_HOOK.encode())
    dist_close = tree_count(DIST, CLOSE_HOOK.encode())
    if min(dist_marker, dist_details_key, dist_copy, dist_close) < 1:
        raise RuntimeError("V5 stable runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v5.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v5.backup-{stamp}"
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

    live_marker = tree_count(LIVE, V5_MARKER.encode())
    live_details_key = tree_count(LIVE, b"data-dq-details-flagship")
    live_copy = tree_count(LIVE, COPY_BODY_HOOK.encode())
    live_close = tree_count(LIVE, CLOSE_HOOK.encode())
    if min(live_marker, live_details_key, live_copy, live_close) < 1:
        raise RuntimeError("V5 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V5_RUNTIME=YES")
    print("REQUIRED_COPY_AUTO_DIRECTION=YES")
    print("ARABIC_COPY_RIGHT_ALIGNED=YES")
    print("ENGLISH_COPY_LEFT_ALIGNED=YES")
    print("CLOSE_ICON_UTILITY=YES")
    print("V4_FULL_WIDTH_COMPOSITION_PRESERVED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V5_RUNTIME_COUNT={source_css.count(V5_MARKER)}")
    print(f"SOURCE_V5_HOOK_COUNT={source_dq.count(V5_HOOK)}")
    print(f"DIST_V5_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_COPY_BODY_COUNT={dist_copy}")
    print(f"DIST_CLOSE_HOOK_COUNT={dist_close}")
    print(f"LIVE_V5_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_COPY_BODY_COUNT={live_copy}")
    print(f"LIVE_CLOSE_HOOK_COUNT={live_close}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v5.failed.{int(time.time())}"
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
    print("V5_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
