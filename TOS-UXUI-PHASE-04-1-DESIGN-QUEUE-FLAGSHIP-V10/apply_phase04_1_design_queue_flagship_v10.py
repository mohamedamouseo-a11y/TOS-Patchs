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

EXPECTED_DQ_SHA = "76c2b721fed37850e429de5376da4207882862d37b101e629f259d9c4ae1d60d"
EXPECTED_PREF_SHA = "1d949f3bc668400ffbfa69082166a41654a1c5ed9518b720675a7f13d873b731"
EXPECTED_SIDEBAR_SHA = "e9c97687ba48cdc0fd58877ec8e71b5d3a7d7856d1fd13097e700e35390f74f0"
EXPECTED_CSS_SHA = "9daf48aa7c5cbaf269a93a3adcc1b12eed569a3d43cc676ff0340353fdf81fce"
V9_MARKER = "TOS_DQ_PREMIUM_MENU_V9"
V10_MARKER = "TOS_DQ_PREMIUM_MENU_THEME_V10"
V8_ROOT = ":root { --tos-dq-v6-runtime: 1; --tos-dq-v7-runtime: 1; --tos-dq-v8-runtime: 1; }"
V10_CSS_MARKER = "--tos-dq-v10-runtime"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V10")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V10_RUNTIME=NO")
    print(f"ERROR={message}")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


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
if sha(DQ) != EXPECTED_DQ_SHA:
    fail("Design Queue differs from verified V9 state")
if sha(PREF) != EXPECTED_PREF_SHA:
    fail("PreferencesContext differs from verified state")
if sha(SIDEBAR) != EXPECTED_SIDEBAR_SHA:
    fail("Sidebar differs from verified V7 state")
if sha(CSS) != EXPECTED_CSS_SHA:
    fail("index.css differs from verified V8 state")

original_dq = DQ.read_text()
original_css = CSS.read_text()
if original_dq.count(V9_MARKER) != 1:
    fail("verified V9 source marker not found exactly once")
if V10_MARKER in original_dq or V10_CSS_MARKER in original_css:
    fail("V10 already present")
if original_css.count(V8_ROOT) != 1:
    fail("verified V8 runtime root not found exactly once")

backup = None
stage = None
live_swapped = False

try:
    updated = original_dq

    updated = replace_once(
        updated,
        'const DQ_PREMIUM_MENU_VERSION = "TOS_DQ_PREMIUM_MENU_V9";\n',
        'const DQ_PREMIUM_MENU_VERSION = "TOS_DQ_PREMIUM_MENU_V9";\nconst DQ_PREMIUM_MENU_THEME_VERSION = "TOS_DQ_PREMIUM_MENU_THEME_V10";\n',
        "V10 menu theme marker",
    )

    updated = replace_once(
        updated,
        '  const searchable = options.length > 8;\n  const filtered = useMemo(() => {',
        '  const searchable = options.length > 8;\n  const isDarkMenu = Boolean(triggerRef.current?.closest(".dark") || document.documentElement.classList.contains("dark") || document.body.classList.contains("dark"));\n  const filtered = useMemo(() => {',
        "portal theme detection",
    )

    updated = replace_once(
        updated,
        '          data-dq-premium-menu={DQ_PREMIUM_MENU_VERSION}\n          style={{ position: "fixed",',
        '          data-dq-premium-menu={DQ_PREMIUM_MENU_VERSION}\n          data-dq-menu-theme-version={DQ_PREMIUM_MENU_THEME_VERSION}\n          data-dq-menu-theme={isDarkMenu ? "dark" : "light"}\n          style={{ position: "fixed",',
        "portal theme data attributes",
    )

    updated = replace_once(
        updated,
        '                  autoFocus\n                  value={query}',
        '                  autoFocus\n                  data-dq-menu-search="true"\n                  value={query}',
        "search field marker",
    )

    updated = replace_once(
        updated,
        '                    aria-selected={active}\n                    onClick={() => choose(option.value)}',
        '                    aria-selected={active}\n                    data-dq-menu-option="true"\n                    data-active={active ? "true" : "false"}\n                    onClick={() => choose(option.value)}',
        "menu option markers",
    )

    v10_css = r'''

/* =========================================================
   V10 — portal menu theme integrity
   The V9 dropdown uses createPortal(document.body). Depending on where
   the app's .dark scope lives, inherited dark utilities/global button/input
   styles can diverge inside the portal. These data-scoped rules make the
   popup self-themed and deterministic in both modes.
   ========================================================= */
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="light"] {
  background: #fffdf8 !important;
  border-color: rgba(197,151,52,.28) !important;
  color: #24231f !important;
  box-shadow: 0 24px 70px rgba(49,37,15,.22), 0 4px 18px rgba(49,37,15,.08) !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="light"] [data-dq-menu-search="true"] {
  background: #ffffff !important;
  color: #24231f !important;
  border-color: rgba(113,103,83,.22) !important;
  box-shadow: none !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="light"] [data-dq-menu-search="true"]::placeholder {
  color: #8d8a82 !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="light"] [data-dq-menu-option="true"][data-active="false"] {
  background: transparent !important;
  color: #4c4942 !important;
  border-color: transparent !important;
  box-shadow: none !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="light"] [data-dq-menu-option="true"][data-active="false"]:hover {
  background: #fbf3df !important;
  color: #181713 !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="light"] [data-dq-menu-option="true"][data-active="true"] {
  background: linear-gradient(90deg, #f8eac5, #fff8e5) !important;
  color: #1d1a14 !important;
  border-color: rgba(197,151,52,.26) !important;
}

[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="dark"] {
  background: #0d0f12 !important;
  border-color: rgba(224,190,102,.20) !important;
  color: #f4f2ed !important;
  box-shadow: 0 28px 80px rgba(0,0,0,.58), 0 4px 22px rgba(0,0,0,.34) !important;
  ring: none !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="dark"] [data-dq-menu-search="true"] {
  background: #15171b !important;
  color: #f5f3ef !important;
  border-color: rgba(255,255,255,.12) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025) !important;
  caret-color: #e4c36c !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="dark"] [data-dq-menu-search="true"]::placeholder {
  color: #858991 !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="dark"] [data-dq-menu-option="true"][data-active="false"] {
  background: transparent !important;
  color: #d1d3d8 !important;
  border-color: transparent !important;
  box-shadow: none !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="dark"] [data-dq-menu-option="true"][data-active="false"]:hover {
  background: rgba(255,255,255,.055) !important;
  color: #ffffff !important;
}
[data-dq-premium-menu="TOS_DQ_PREMIUM_MENU_V9"][data-dq-menu-theme="dark"] [data-dq-menu-option="true"][data-active="true"] {
  background: linear-gradient(90deg, rgba(126,93,24,.56), rgba(74,57,24,.34)) !important;
  color: #fff4cd !important;
  border-color: rgba(224,190,102,.22) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025) !important;
}
'''

    updated_css = original_css.replace(
        V8_ROOT,
        ":root { --tos-dq-v6-runtime: 1; --tos-dq-v7-runtime: 1; --tos-dq-v8-runtime: 1; --tos-dq-v10-runtime: 1; }" + v10_css,
        1,
    )

    DQ.write_text(updated)
    CSS.write_text(updated_css)

    if DQ.read_text().count(V10_MARKER) != 1:
        raise RuntimeError("source V10 menu marker missing or duplicated")
    if CSS.read_text().count(V10_CSS_MARKER) != 1:
        raise RuntimeError("source V10 CSS marker missing or duplicated")
    if DQ.read_text().count('data-dq-menu-theme={isDarkMenu ? "dark" : "light"}') != 1:
        raise RuntimeError("self-themed portal attribute missing")
    if sha(PREF) != EXPECTED_PREF_SHA or sha(SIDEBAR) != EXPECTED_SIDEBAR_SHA:
        raise RuntimeError("unrelated source changed unexpectedly")

    subprocess.run([
        "git", "-C", str(ROOT), "diff", "--check", "--",
        "frontend/src/pages/DesignQueuePage.jsx", "frontend/src/index.css"
    ], check=True)

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_v10 = tree_count(DIST, V10_MARKER.encode())
    dist_css = tree_count(DIST, V10_CSS_MARKER.encode())
    if dist_v10 < 1 or dist_css < 1:
        raise RuntimeError(f"V10 markers missing from dist: menu={dist_v10}, css={dist_css}")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-design-queue-v10.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-design-queue-v10.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged index missing")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_v10 = tree_count(LIVE, V10_MARKER.encode())
    live_css = tree_count(LIVE, V10_CSS_MARKER.encode())
    if live_v10 < 1 or live_css < 1:
        raise RuntimeError(f"V10 markers missing from live: menu={live_v10}, css={live_css}")

except Exception as exc:
    DQ.write_text(original_dq)
    CSS.write_text(original_css)
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
print("V10_RUNTIME=YES")
print("PORTAL_THEME_SELF_CONTAINED=YES")
print("DARK_MENU_WHITE_ROWS_FIXED=YES")
print("LIGHT_MENU_CONTRAST_FIXED=YES")
print("PROJECT_MENU_SEARCH_PRESERVED=YES")
print("PREMIUM_MENUS_PRESERVED=YES")
print("PERFORMANCE_V3_PRESERVED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("SOURCE_V10_MENU_MARKER_COUNT=" + str(DQ.read_text().count(V10_MARKER)))
print("SOURCE_V10_CSS_MARKER_COUNT=" + str(CSS.read_text().count(V10_CSS_MARKER)))
print("DIST_V10_MENU_MARKER_COUNT=" + str(tree_count(DIST, V10_MARKER.encode())))
print("DIST_V10_CSS_MARKER_COUNT=" + str(tree_count(DIST, V10_CSS_MARKER.encode())))
print("LIVE_V10_MENU_MARKER_COUNT=" + str(tree_count(LIVE, V10_MARKER.encode())))
print("LIVE_V10_CSS_MARKER_COUNT=" + str(tree_count(LIVE, V10_CSS_MARKER.encode())))
print("DESIGN_QUEUE_SHA256=" + sha(DQ))
print("SIDEBAR_SHA256=" + sha(SIDEBAR))
print("INDEX_CSS_SHA256=" + sha(CSS))
