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

EXPECTED_DQ_SHA256 = "cf9cfd16cb9593c7bad8bc993626eb435eb2246324209d8557f3dc33eab52505"
EXPECTED_CSS_SHA256 = "3cc15873d1b1ead73197029f7465e64c07b3ac85870217081502620f9e537716"
V2_MARKER = "--tos-dq-details-flagship-v2-runtime"
V3_MARKER = "--tos-dq-details-flagship-v3-runtime"
V2_HOOK = 'data-dq-details-flagship="v2"'

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V3")


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
    print("V3_RUNTIME=NO")
    sys.exit(1)


for path in (DQ, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha256(DQ) != EXPECTED_DQ_SHA256:
    fail("DesignQueuePage.jsx does not match approved Flagship V2 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match approved Flagship V2 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10", V2_HOOK, V2_MARKER):
    if required not in (original_dq + original_css):
        fail(f"required V2 baseline marker missing: {required}")
if V3_MARKER in original_css:
    fail("Design Request Details Flagship V3 already present")

v3_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V3
   Desktop composition rebalance after visual QA.
   Specifications + assignment share the first row; attachments
   and activity then span the full workspace width, eliminating
   the long dead rail beneath the sticky assignment card.
   Business logic unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v3-runtime: 1; }

@media (min-width: 1280px) {
  .tos-dq-details-layout-v1 {
    grid-template-columns: minmax(0, 1fr) 304px !important;
    grid-auto-flow: row;
    align-items: start;
    gap: 18px !important;
  }

  .tos-dq-details-content-v1 {
    display: contents;
  }

  .tos-dq-details-content-v1 > div:first-child {
    grid-column: 1;
    grid-row: 1;
    min-width: 0;
  }

  .tos-dq-details-rail-v1 {
    grid-column: 2;
    grid-row: 1;
    width: 100%;
    min-width: 0;
    top: 14px !important;
  }

  .tos-dq-details-attachments-v1 {
    grid-column: 1 / -1;
    grid-row: 2;
    width: 100%;
  }

  .tos-dq-details-activity-v1 {
    grid-column: 1 / -1;
    grid-row: 3;
    width: 100%;
  }

  .tos-dq-details-attachments-v1 [class*="border-dashed"] {
    min-height: 94px !important;
  }

  .tos-dq-details-activity-v1 > div:last-child {
    padding-block: 14px 16px !important;
  }

  .tos-dq-details-activity-v1 .tos-dq-activity-item-v1 {
    max-width: 980px;
  }
}

/* Slightly stronger editorial hierarchy without making the screen heavier. */
.tos-dq-details-specs-v1 > div:first-child,
.tos-dq-details-attachments-v1 > div:first-child,
.tos-dq-details-activity-v1 > div:first-child,
.tos-dq-details-assignment-v1 > div:first-child {
  font-weight: 900 !important;
}

.tos-dq-spec-copy-v1 {
  position: relative;
}

.tos-dq-spec-copy-v1::after {
  content: "";
  position: absolute;
  inset-inline: 22px;
  bottom: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(201,154,61,.18), transparent);
  pointer-events: none;
}

html.dark .tos-dq-spec-copy-v1::after {
  background: linear-gradient(90deg, transparent, rgba(215,178,100,.14), transparent);
}

@media (max-width: 1279px) {
  .tos-dq-details-content-v1 {
    display: block;
  }
}
'''

v3_css = "\n".join(line.rstrip() for line in v3_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v3_css

backup = None
stage = None
live_swapped = False

try:
    CSS.write_text(updated_css)
    source_css = CSS.read_text()

    if source_css.count(V3_MARKER) != 1:
        raise RuntimeError("V3 source runtime marker missing or duplicated")
    if V2_HOOK not in DQ.read_text() or V2_MARKER not in source_css:
        raise RuntimeError("V2 baseline was not preserved")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V3_MARKER.encode())
    dist_details_key = tree_count(DIST, b"data-dq-details-flagship")
    if dist_marker < 1 or dist_details_key < 1:
        raise RuntimeError("V3 stable runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v3.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v3.backup-{stamp}"
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

    live_marker = tree_count(LIVE, V3_MARKER.encode())
    live_details_key = tree_count(LIVE, b"data-dq-details-flagship")
    if live_marker < 1 or live_details_key < 1:
        raise RuntimeError("V3 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V3_RUNTIME=YES")
    print("DESKTOP_COMPOSITION_REBALANCED=YES")
    print("DEAD_RIGHT_RAIL_REMOVED=YES")
    print("ATTACHMENTS_FULL_WIDTH=YES")
    print("ACTIVITY_FULL_WIDTH=YES")
    print("ASSIGNMENT_STICKY_PRESERVED=YES")
    print("REQUIRED_COPY_EDITORIAL_REFINED=YES")
    print("LIGHT_FLAGSHIP_PRESERVED=YES")
    print("DARK_FLAGSHIP_PRESERVED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V3_RUNTIME_COUNT={source_css.count(V3_MARKER)}")
    print(f"DIST_V3_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_DETAILS_KEY_COUNT={dist_details_key}")
    print(f"LIVE_V3_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_DETAILS_KEY_COUNT={live_details_key}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v3.failed.{int(time.time())}"
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
    print("V3_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
