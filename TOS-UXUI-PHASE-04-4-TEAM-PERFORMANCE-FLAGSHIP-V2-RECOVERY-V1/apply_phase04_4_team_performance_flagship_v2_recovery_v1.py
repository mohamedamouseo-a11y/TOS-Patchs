from pathlib import Path
import hashlib
import shutil
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PAGE = ROOT / "frontend/src/pages/TeamPerformanceDashboard.jsx"
PERIOD = ROOT / "frontend/src/components/performance/PerformancePeriodControl.jsx"
V1_STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV1.css"
V2_STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV2.css"
LIVE = Path("/opt/apps/tamiyouz-front/build")

EXPECTED_PAGE_SHA256 = "df1d68e31cf82fbc57be411b8ce3cb55f5e326138fb128db70d13d6a94774c66"
EXPECTED_V1_STYLE_SHA256 = "f685c05500b21cb0e60c238c555f213d889c11673ff84868c1f30b74126f2468"
V1_RUNTIME = "--tos-team-performance-flagship-v1-runtime"
V2_RUNTIME = "--tos-team-performance-flagship-v2-runtime"
V2_ROOT = 'data-tp-flagship-v2="v2"'
V2_MENU_TOKEN = "tos-tp-premium-menu-v2"
V2_COMPARE_TOKEN = "tos-tp-compare-trigger-v2"

print("RUNNING=PHASE04_4_TEAM_PERFORMANCE_FLAGSHIP_V2_RECOVERY_V1")


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
    print("V2_RUNTIME=NO")
    print("RECOVERY=PHASE04_4_TEAM_PERFORMANCE_FLAGSHIP_V2_RECOVERY_V1")
    sys.exit(1)


for path in (PAGE, PERIOD, V1_STYLE):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail("TeamPerformanceDashboard.jsx does not match Flagship V1 live source")
if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256:
    fail("teamPerformanceFlagshipV1.css does not match Flagship V1 live source")
if V1_RUNTIME not in V1_STYLE.read_text():
    fail("V1 runtime marker missing")

original_page = PAGE.read_text()
original_period = PERIOD.read_text()
original_v2_style = V2_STYLE.read_text() if V2_STYLE.exists() else None
v2_style_existed = V2_STYLE.exists()

# The failed V2 run rolled back to V1. Guard against applying over a partially-applied V2.
if V2_ROOT in original_page or V2_STYLE.exists() or V2_COMPARE_TOKEN in original_period:
    fail("V2 appears partially/already applied; refusing recovery over non-V1 source")

# Confirm the real current PeriodControl baseline reported by OpenHands.
LUCIDE_IMPORT = 'import { CalendarDays, Minus, TrendingDown, TrendingUp } from "lucide-react";'
SYNTHETIC_REACT_IMPORT = 'import { useState } from "react";'
if LUCIDE_IMPORT not in original_period:
    fail("PerformancePeriodControl.jsx baseline changed: expected lucide import not found")
if SYNTHETIC_REACT_IMPORT in original_period:
    fail("PerformancePeriodControl.jsx unexpectedly already contains the synthetic React import")
if 'from "react";' in original_period:
    fail("PerformancePeriodControl.jsx has an unexpected React import shape; refusing unsafe recovery")

# Locate the original V2 patch script in the same TOS-Patchs checkout.
recovery_dir = Path(__file__).resolve().parent
repo_root = recovery_dir.parent
v2_script = repo_root / "TOS-UXUI-PHASE-04-4-TEAM-PERFORMANCE-FLAGSHIP-V2" / "apply_phase04_4_team_performance_flagship_v2.py"
if not v2_script.exists():
    fail(f"original V2 patch script not found: {v2_script}")

try:
    # Compatibility shim only: the V2 patch expected this import to exist so it could
    # replace it with useEffect/useRef/useState + createPortal. The current component
    # legitimately has no React import because it previously used no local React hooks.
    PERIOD.write_text(SYNTHETIC_REACT_IMPORT + "\n" + original_period)

    run = subprocess.run(
        [sys.executable, str(v2_script), str(ROOT)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if run.returncode != 0:
        # The original V2 script rolls its own edits back, but its rollback snapshot
        # contains the compatibility shim. Restore the exact real pre-recovery source.
        PAGE.write_text(original_page)
        PERIOD.write_text(original_period)
        if v2_style_existed:
            V2_STYLE.write_text(original_v2_style)
        elif V2_STYLE.exists():
            V2_STYLE.unlink()
        print(run.stdout[-12000:])
        fail("original V2 patch failed during recovery")

    # Stable postconditions. Do not verify component/function names in minified bundles.
    if V2_ROOT not in PAGE.read_text():
        raise RuntimeError("V2 root hook missing after original patch")
    if V2_COMPARE_TOKEN not in PERIOD.read_text():
        raise RuntimeError("premium compare trigger missing after original patch")
    if not V2_STYLE.exists() or V2_RUNTIME not in V2_STYLE.read_text():
        raise RuntimeError("V2 stylesheet/runtime marker missing after original patch")

    dist = ROOT / "frontend/dist"
    dist_runtime = tree_count(dist, V2_RUNTIME.encode())
    dist_menu = tree_count(dist, V2_MENU_TOKEN.encode())
    dist_compare = tree_count(dist, V2_COMPARE_TOKEN.encode())
    live_runtime = tree_count(LIVE, V2_RUNTIME.encode())
    live_menu = tree_count(LIVE, V2_MENU_TOKEN.encode())
    live_compare = tree_count(LIVE, V2_COMPARE_TOKEN.encode())
    if min(dist_runtime, dist_menu, dist_compare, live_runtime, live_menu, live_compare) < 1:
        raise RuntimeError("V2 stable runtime tokens missing from dist/live after recovery")

    # Keep the original V2 report for auditability, then append the recovery-specific result.
    print(run.stdout.rstrip())
    print("RECOVERY_RUN=PHASE04_4_TEAM_PERFORMANCE_FLAGSHIP_V2_RECOVERY_V1")
    print("RECOVERY_PASS_FAIL=PASS")
    print("V2_RECOVERY_V1=YES")
    print("PERIOD_REACT_IMPORT_BASELINE_FIXED=YES")
    print("COMPATIBILITY_SHIM_REMOVED_BY_V2=YES")
    print("VERIFICATION=STABLE_MINIFIED_RUNTIME_TOKENS")
    print(f"RECOVERY_DIST_V2_RUNTIME_COUNT={dist_runtime}")
    print(f"RECOVERY_DIST_MENU_TOKEN_COUNT={dist_menu}")
    print(f"RECOVERY_DIST_COMPARE_TOKEN_COUNT={dist_compare}")
    print(f"RECOVERY_LIVE_V2_RUNTIME_COUNT={live_runtime}")
    print(f"RECOVERY_LIVE_MENU_TOKEN_COUNT={live_menu}")
    print(f"RECOVERY_LIVE_COMPARE_TOKEN_COUNT={live_compare}")
    print(f"TEAM_PERFORMANCE_SHA256={sha256(PAGE)}")
    print(f"PERIOD_CONTROL_SHA256={sha256(PERIOD)}")
    print(f"FLAGSHIP_V2_CSS_SHA256={sha256(V2_STYLE)}")
except Exception as exc:
    # Source safety first. If the original patch somehow succeeded but our extra
    # verification failed, leave the live build untouched only if V2 is actually live;
    # otherwise restore the exact V1 sources. The main V2 script already handled live rollback.
    if tree_count(LIVE, V2_RUNTIME.encode()) < 1:
        PAGE.write_text(original_page)
        PERIOD.write_text(original_period)
        if v2_style_existed:
            V2_STYLE.write_text(original_v2_style)
        elif V2_STYLE.exists():
            V2_STYLE.unlink()
    fail(exc)
