from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
PREF = ROOT / "frontend/src/contexts/PreferencesContext.jsx"
SIDEBAR = ROOT / "frontend/src/components/layout/Sidebar.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

DQ_PERF_V3_SHA = "f71c66b26a5cd7bb06ca849ce82afef897ed58d288c9fcfa198168a1d2d0eb59"
PREF_PERF_V1_SHA = "1d949f3bc668400ffbfa69082166a41654a1c5ed9518b720675a7f13d873b731"
CSS_V6_SHA = "2fa061485f20af185aeae3df1fe99033cbf12d2babe31f87c0f2e776e31fcb13"
SIDEBAR_PRE_V7_SHA = "8e62b2753e1c44e5bd580a4c301a0b41443508ab732cd8a579ab80368433c5e8"
V7_MARKER = "--tos-dq-v7-runtime"
SIDEBAR_MARKER = 'data-sidebar-premium="v7"'

print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V7_RECOVERY_V3")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V7_RECOVERY_V3=NO")
    print(f"ERROR={message}")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def replace_count(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, found {count}")
    return text.replace(old, new)


def clean_block(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines())


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


for path in (DQ, PREF, SIDEBAR, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha(DQ) != DQ_PERF_V3_SHA:
    fail("Design Queue differs from verified Performance V3 state")
if sha(PREF) != PREF_PERF_V1_SHA:
    fail("PreferencesContext differs from verified Performance V1 state")
if sha(CSS) != CSS_V6_SHA:
    fail("index.css differs from verified V6 state")
if sha(SIDEBAR) != SIDEBAR_PRE_V7_SHA:
    fail("Sidebar differs from verified clean pre-V7 state")

original_css = CSS.read_text()
original_sidebar = SIDEBAR.read_text()
if V7_MARKER in original_css or SIDEBAR_MARKER in original_sidebar:
    fail("V7 marker already present before recovery")

V6_START = "/* Phase 04.1 — Design Queue Flagship V6"
V6_TAIL = """@media (max-width: 767px) {
  .tos-core-design-queue-premium { padding: .65rem !important; }
  .tos-core-design-queue-premium > .flex.flex-wrap.justify-between > div {
    flex: 1 1 calc(50% - .58rem) !important;
    min-height: 72px !important;
  }
  .tos-core-design-queue-premium > .h-\\[calc\\(100vh-350px\\)\\] {
    min-height: 620px !important;
  }
}"""

start = original_css.find(V6_START)
if start < 0:
    fail("V6 block start marker not found")
tail_at = original_css.find(V6_TAIL, start)
if tail_at < 0:
    fail("V6 block tail marker not found")
end = tail_at + len(V6_TAIL)
v6 = original_css[start:end]

backup = None
stage = None
live_swapped = False

try:
    v7 = v6
    v7 = replace_once(v7, "/* Phase 04.1 — Design Queue Flagship V6", "/* Phase 04.1 — Design Queue Flagship V7", "header")
    v7 = replace_once(v7, "Screenshot-driven final composition refinement over verified V5.", "Screenshot-driven executive density refinement over verified V6.", "subtitle")
    v7 = replace_once(v7, ":root { --tos-dq-v6-runtime: 1; }", ":root { --tos-dq-v6-runtime: 1; --tos-dq-v7-runtime: 1; }", "runtime")
    v7 = replace_once(v7, "min-height: 76px !important;", "min-height: 80px !important;", "kpi height")
    v7 = replace_once(v7, "font-size: .76rem !important;\n  letter-spacing: -.01em !important;", "font-size: .81rem !important;\n  letter-spacing: -.012em !important;", "kpi label")
    v7 = replace_once(v7, "font-size: .58rem !important;\n  opacity: .82;", "font-size: .62rem !important;\n  opacity: .88;", "kpi note")
    v7 = replace_once(v7, "min-height: 38px !important;\n  height: 38px !important;\n  border-radius: 10px !important;\n  font-size: .72rem !important;", "min-height: 40px !important;\n  height: 40px !important;\n  border-radius: 11px !important;\n  font-size: .78rem !important;", "command controls")
    v7 = replace_once(v7, "min-height: 665px !important;", "min-height: 640px !important;", "board height")
    v7 = replace_once(v7, "min-height: 58px !important;\n  padding: .72rem .72rem !important;", "min-height: 54px !important;\n  padding: .64rem .7rem !important;", "column header")
    v7 = replace_once(v7, "font-size: .84rem !important;\n  line-height: 1.38 !important;", "font-size: .89rem !important;\n  line-height: 1.38 !important;", "card title")
    v7 = replace_once(v7, "font-size: .64rem !important;", "font-size: .69rem !important;", "card metadata")

    extra_css = r'''

/* V7 — compact capacity inspector */
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
.tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden > .divide-y > div {
  min-height: 48px !important;
  padding: .42rem .7rem !important;
}
html.dark .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .grid.gap-3 > div {
  background: linear-gradient(145deg, #17191e, #111318) !important;
  border-color: rgba(255,255,255,.07) !important;
}
html.dark .tos-core-design-queue-premium > .overflow-hidden.p-0 > .border-t > .mt-4.overflow-hidden {
  background: #0d0f12 !important;
  border-color: rgba(255,255,255,.075) !important;
}

/* V7 — premium system navigation */
.tos-premium-sidebar[data-sidebar-premium="v7"] {
  border-color: rgba(151,126,69,.18) !important;
  background: linear-gradient(165deg, rgba(255,255,255,.985), rgba(248,245,238,.965)) !important;
  box-shadow: 0 24px 60px rgba(43,34,18,.09), inset 0 1px 0 rgba(255,255,255,.94) !important;
}
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav {
  margin-top: .7rem !important;
  padding-inline: .08rem .12rem !important;
}
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav > div {
  gap: .52rem !important;
}
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav > div > a,
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section {
  border-radius: 17px !important;
}
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section {
  overflow: hidden !important;
  border-color: rgba(104,91,63,.12) !important;
  background: linear-gradient(145deg, rgba(255,255,255,.82), rgba(247,244,237,.72)) !important;
  box-shadow: 0 7px 18px rgba(43,34,20,.035), inset 0 1px 0 rgba(255,255,255,.82) !important;
}
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section:has(> button[aria-expanded="true"]) {
  border-color: rgba(193,151,57,.24) !important;
  background: linear-gradient(145deg, #fffefb, #f7f2e7) !important;
  box-shadow: 0 10px 24px rgba(65,48,18,.06), inset 3px 0 0 rgba(205,165,75,.78) !important;
}
[dir="rtl"].tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section:has(> button[aria-expanded="true"]) {
  box-shadow: 0 10px 24px rgba(65,48,18,.06), inset -3px 0 0 rgba(205,165,75,.78) !important;
}
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section > button {
  position: static !important;
  min-height: 48px !important;
  padding: .66rem .78rem !important;
  gap: .62rem !important;
  font-size: .84rem !important;
  line-height: 1.3 !important;
}
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section > div {
  padding: .34rem .38rem .42rem !important;
  background: rgba(255,255,255,.52) !important;
}
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section > div > a {
  min-height: 42px !important;
  margin-block: .12rem !important;
  padding: .58rem .64rem !important;
  gap: .52rem !important;
  border-radius: 12px !important;
  color: #68645d !important;
  font-size: .76rem !important;
  line-height: 1.3 !important;
}
.tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav a[aria-current="page"] {
  color: #171714 !important;
  background: linear-gradient(135deg, rgba(250,244,224,.98), rgba(255,253,247,.98)) !important;
  border-color: rgba(192,147,49,.25) !important;
  box-shadow: 0 5px 14px rgba(74,54,17,.065), inset 0 1px 0 rgba(255,255,255,.94) !important;
}
html.dark .tos-premium-sidebar[data-sidebar-premium="v7"] {
  border-color: rgba(219,184,94,.14) !important;
  background: linear-gradient(165deg, rgba(16,18,22,.99), rgba(8,9,11,.985)) !important;
  box-shadow: 0 26px 66px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.03) !important;
}
html.dark .tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section {
  border-color: rgba(255,255,255,.075) !important;
  background: linear-gradient(145deg, rgba(25,27,32,.92), rgba(14,16,19,.90)) !important;
}
html.dark .tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section > button > span {
  color: #f0eee9 !important;
}
html.dark .tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav section > div > a {
  color: #aeb1b7 !important;
}
html.dark .tos-premium-sidebar[data-sidebar-premium="v7"][data-collapsed="false"] > nav a[aria-current="page"] {
  color: #fbfaf7 !important;
  background: linear-gradient(135deg, rgba(64,51,25,.78), rgba(28,27,24,.92)) !important;
  border-color: rgba(224,190,102,.25) !important;
}
'''
    v7 = clean_block(v7 + extra_css)

    sidebar = original_sidebar
    sidebar = replace_once(sidebar, "const SIDEBAR_DEFAULT_WIDTH = 248;", "const SIDEBAR_DEFAULT_WIDTH = 272;", "sidebar expanded width")
    sidebar = replace_once(
        sidebar,
        '      dir={isRtl ? "rtl" : "ltr"}\n      className={cn(',
        '      dir={isRtl ? "rtl" : "ltr"}\n      data-sidebar-premium="v7"\n      data-collapsed={isCollapsedMode ? "true" : "false"}\n      className={cn(',
        "sidebar data attributes",
    )
    sidebar = replace_count(
        sidebar,
        '<span className="truncate">{item.label}</span>',
        '<span className="min-w-0 flex-1 whitespace-normal break-words leading-[1.3]">{item.label}</span>',
        2,
        "root/group labels",
    )
    sidebar = replace_once(
        sidebar,
        '<span className="truncate">{subItem.label}</span>',
        '<span className="min-w-0 flex-1 whitespace-normal break-words leading-[1.3]">{subItem.label}</span>',
        "submenu label",
    )

    updated_css = original_css[:start] + v7 + original_css[end:]
    CSS.write_text(updated_css)
    SIDEBAR.write_text(sidebar)

    if CSS.read_text().count(V7_MARKER) != 1:
        raise RuntimeError("source V7 marker count is not 1")
    if SIDEBAR.read_text().count(SIDEBAR_MARKER) != 1:
        raise RuntimeError("source Sidebar marker count is not 1")
    if 'className="truncate">{item.label}</span>' in SIDEBAR.read_text():
        raise RuntimeError("root menu label truncation remains")
    if 'className="truncate">{subItem.label}</span>' in SIDEBAR.read_text():
        raise RuntimeError("submenu label truncation remains")
    if sha(DQ) != DQ_PERF_V3_SHA or sha(PREF) != PREF_PERF_V1_SHA:
        raise RuntimeError("performance source changed unexpectedly")

    subprocess.run([
        "git", "-C", str(ROOT), "diff", "--check", "--",
        "frontend/src/index.css", "frontend/src/components/layout/Sidebar.jsx"
    ], check=True)

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    source_v7 = CSS.read_text().count(V7_MARKER)
    source_sidebar = SIDEBAR.read_text().count(SIDEBAR_MARKER)
    dist_v7 = tree_count(DIST, V7_MARKER.encode())
    dist_sidebar = tree_count(DIST, SIDEBAR_MARKER.encode())
    if source_v7 != 1 or source_sidebar != 1:
        raise RuntimeError("source marker verification failed")
    if dist_v7 < 1 or dist_sidebar < 1:
        raise RuntimeError(f"dist marker verification failed: css={dist_v7}, sidebar={dist_sidebar}")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-v7-recovery-v3.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-v7-recovery-v3.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_v7 = tree_count(LIVE, V7_MARKER.encode())
    live_sidebar = tree_count(LIVE, SIDEBAR_MARKER.encode())
    if live_v7 < 1 or live_sidebar < 1:
        raise RuntimeError(f"live marker verification failed: css={live_v7}, sidebar={live_sidebar}")

except Exception as exc:
    CSS.write_text(original_css)
    SIDEBAR.write_text(original_sidebar)
    if live_swapped and backup and backup.exists():
        if LIVE.exists():
            shutil.rmtree(LIVE)
        backup.rename(LIVE)
    if stage and stage.exists():
        shutil.rmtree(stage)
    fail(str(exc))

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("V7_RECOVERY_V3=YES")
print("SOURCE_V7_RUNTIME_COUNT=" + str(CSS.read_text().count(V7_MARKER)))
print("SOURCE_SIDEBAR_MARKER_COUNT=" + str(SIDEBAR.read_text().count(SIDEBAR_MARKER)))
print("DIST_V7_RUNTIME_COUNT=" + str(tree_count(DIST, V7_MARKER.encode())))
print("DIST_SIDEBAR_MARKER_COUNT=" + str(tree_count(DIST, SIDEBAR_MARKER.encode())))
print("LIVE_V7_RUNTIME_COUNT=" + str(tree_count(LIVE, V7_MARKER.encode())))
print("LIVE_SIDEBAR_MARKER_COUNT=" + str(tree_count(LIVE, SIDEBAR_MARKER.encode())))
print("MENU_TEXT_READABLE=YES")
print("COLLAPSED_MODE_PRESERVED=YES")
print("PERFORMANCE_V3_PRESERVED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("DESIGN_QUEUE_SHA256=" + sha(DQ))
print("PREFERENCES_CONTEXT_SHA256=" + sha(PREF))
print("SIDEBAR_SHA256=" + sha(SIDEBAR))
print("INDEX_CSS_SHA256=" + sha(CSS))
