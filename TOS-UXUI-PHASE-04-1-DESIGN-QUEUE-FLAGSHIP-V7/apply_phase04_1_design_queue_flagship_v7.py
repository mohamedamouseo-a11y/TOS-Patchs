from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
PATCH_REPO = PATCH_DIR.parent
V6_SOURCE = PATCH_REPO / "TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-FLAGSHIP-V6" / "design-queue-flagship-v6.css"
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
PREF = ROOT / "frontend/src/contexts/PreferencesContext.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

DQ_PERF_V3_SHA = "f71c66b26a5cd7bb06ca849ce82afef897ed58d288c9fcfa198168a1d2d0eb59"
PREF_PERF_V1_SHA = "1d949f3bc668400ffbfa69082166a41654a1c5ed9518b720675a7f13d873b731"
CSS_V6_SHA = "2fa061485f20af185aeae3df1fe99033cbf12d2babe31f87c0f2e776e31fcb13"
V7_MARKER = "--tos-dq-v7-runtime"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V7")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fail(message: str):
    print("PASS/FAIL=FAIL")
    print(f"ERROR={message}")
    sys.exit(1)

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)

if not all(path.exists() for path in [DQ, PREF, CSS, V6_SOURCE]):
    fail("required source file missing")
if sha(DQ) != DQ_PERF_V3_SHA:
    fail("Design Queue differs from verified Performance V3 state")
if sha(PREF) != PREF_PERF_V1_SHA:
    fail("PreferencesContext differs from verified Performance V1 state")
if sha(CSS) != CSS_V6_SHA:
    fail("index.css differs from verified V6 visual state")

original_css = CSS.read_text()
v6 = V6_SOURCE.read_text().strip()
if original_css.count(v6) != 1:
    fail("verified V6 CSS block not found exactly once")
if V7_MARKER in original_css:
    fail("V7 already present")

try:
    v7 = v6
    v7 = replace_once(v7, "/* Phase 04.1 — Design Queue Flagship V6", "/* Phase 04.1 — Design Queue Flagship V7", "header")
    v7 = replace_once(v7, "Screenshot-driven final composition refinement over verified V5.", "Screenshot-driven executive density refinement over verified V6.", "subtitle")
    v7 = replace_once(v7, ":root { --tos-dq-v6-runtime: 1; }", ":root { --tos-dq-v6-runtime: 1; --tos-dq-v7-runtime: 1; }", "runtime")

    # Slightly stronger KPI hierarchy without increasing page weight.
    v7 = replace_once(v7, "min-height: 76px !important;", "min-height: 80px !important;", "kpi height")
    v7 = replace_once(v7, "font-size: .76rem !important;\n  letter-spacing: -.01em !important;", "font-size: .81rem !important;\n  letter-spacing: -.012em !important;", "kpi label")
    v7 = replace_once(v7, "font-size: .58rem !important;\n  opacity: .82;", "font-size: .62rem !important;\n  opacity: .88;", "kpi note")

    # Command strip: improve legibility.
    v7 = replace_once(v7, "min-height: 38px !important;\n  height: 38px !important;\n  border-radius: 10px !important;\n  font-size: .72rem !important;", "min-height: 40px !important;\n  height: 40px !important;\n  border-radius: 11px !important;\n  font-size: .78rem !important;", "command controls")

    # Board: slightly denser shell, more readable cards.
    v7 = replace_once(v7, "min-height: 665px !important;", "min-height: 640px !important;", "board height")
    v7 = replace_once(v7, "min-height: 58px !important;\n  padding: .72rem .72rem !important;", "min-height: 54px !important;\n  padding: .64rem .7rem !important;", "column header")
    v7 = replace_once(v7, "font-size: .84rem !important;\n  line-height: 1.38 !important;", "font-size: .89rem !important;\n  line-height: 1.38 !important;", "card title")
    v7 = replace_once(v7, "font-size: .64rem !important;", "font-size: .69rem !important;", "card metadata")

    # New V7 rules live inside the single replacement block rather than accumulating another full layer.
    v7 += r'''

/* =========================================================
   V7 — expanded capacity as an executive inspector, not a page takeover
   ========================================================= */
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t {
  padding: .72rem .82rem .68rem !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .grid.gap-3 {
  gap: .48rem !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .grid.gap-3 > div {
  min-height: 58px !important;
  padding: .52rem .66rem !important;
  border-radius: 12px !important;
  background: linear-gradient(145deg, rgba(255,255,255,.92), rgba(248,246,241,.78)) !important;
  border-color: rgba(113,103,83,.11) !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .grid.gap-3 .text-2xl {
  font-size: 1.28rem !important;
  line-height: 1 !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .grid.gap-3 .text-\[10px\] {
  font-size: .61rem !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-3.grid {
  margin-top: .55rem !important;
  gap: .42rem !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-3.grid :is(input,select) {
  height: 36px !important;
  min-height: 36px !important;
  border-radius: 10px !important;
  font-size: .72rem !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden {
  margin-top: .58rem !important;
  border-radius: 13px !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden > .hidden {
  padding: .4rem .7rem !important;
  min-height: 32px !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden > .divide-y > div {
  min-height: 48px !important;
  padding: .42rem .7rem !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t .grid.h-10.w-10 {
  width: 32px !important;
  height: 32px !important;
  font-size: .66rem !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t .h-9 {
  height: 32px !important;
  min-height: 32px !important;
}
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-3.flex.flex-wrap {
  margin-top: .5rem !important;
  min-height: 30px !important;
}

/* Light — sharper porcelain separation and calmer data table. */
html:not(.dark) .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden {
  background: rgba(255,255,255,.7) !important;
  border-color: rgba(99,88,67,.12) !important;
}
html:not(.dark) .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden > .divide-y > div:hover {
  background: rgba(214,179,90,.055) !important;
}

/* Dark — black titanium data inspector with visible row rhythm. */
html.dark .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t {
  background: linear-gradient(180deg, rgba(255,255,255,.012), transparent) !important;
}
html.dark .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .grid.gap-3 > div {
  background: linear-gradient(145deg, #17191e, #111318) !important;
  border-color: rgba(255,255,255,.07) !important;
}
html.dark .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden {
  background: #0d0f12 !important;
  border-color: rgba(255,255,255,.075) !important;
}
html.dark .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden > .divide-y > div {
  border-color: rgba(255,255,255,.055) !important;
}
html.dark .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden > .divide-y > div:hover {
  background: rgba(216,179,90,.035) !important;
}
html.dark .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t :is(input,select) {
  background: #15171b !important;
  border-color: rgba(255,255,255,.09) !important;
  color: #f1f0ed !important;
}

@media (max-width: 1279px) {
  .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden > .divide-y > div {
    min-height: 52px !important;
  }
}
'''

    updated_css = original_css.replace(v6, v7, 1)
    CSS.write_text(updated_css)

    if updated_css.count(V7_MARKER) != 1:
        raise RuntimeError("V7 runtime marker missing or duplicated")
    if updated_css.count("/* Phase 04.1 — Design Queue Flagship V6") != 0:
        raise RuntimeError("old V6 block still present")
    if sha(DQ) != DQ_PERF_V3_SHA or sha(PREF) != PREF_PERF_V1_SHA:
        raise RuntimeError("performance source changed unexpectedly")

    subprocess.run(["git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/index.css"], check=True)
    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-design-queue-v7.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-design-queue-v7.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged index missing")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")
    LIVE.rename(backup)
    try:
        stage.rename(LIVE)
        subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)
    except Exception:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if backup.exists():
            backup.rename(LIVE)
        raise

except Exception as exc:
    CSS.write_text(original_css)
    fail(str(exc))

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("SCREEN=Design_Queue_ONLY")
print("V6_BLOCK_REPLACED=YES")
print("V7_RUNTIME=YES")
print("PERFORMANCE_V3_PRESERVED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("DESIGN_QUEUE_SHA256=" + sha(DQ))
print("PREFERENCES_CONTEXT_SHA256=" + sha(PREF))
print("INDEX_CSS_SHA256=" + sha(CSS))
