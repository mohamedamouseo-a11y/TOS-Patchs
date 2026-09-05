from pathlib import Path
import subprocess
import sys
import tempfile

PATCH_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PATCH_ROOT / "TOS-UXUI-PHASE-04-3-TEAM-MEMBERS-FLAGSHIP-V4" / "apply_phase04_3_team_members_flagship_v4.py"
TARGET = sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS"


def fail(message: str):
    print("RUNNING=PHASE04_3_TEAM_MEMBERS_FLAGSHIP_V4_RECOVERY_V1")
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V4_RUNTIME=NO")
    print("V4_RECOVERY_V1=NO")
    sys.exit(1)


if not SOURCE.exists():
    fail(f"original V4 installer missing: {SOURCE}")

script = SOURCE.read_text()

required = [
    'print("RUNNING=PHASE04_3_TEAM_MEMBERS_FLAGSHIP_V4")',
    'PREMIUM_COMPONENT = "TeamPremiumSelectV4"',
    'component_dist = tree_count(DIST, PREMIUM_COMPONENT.encode())',
    'component_live = tree_count(LIVE, PREMIUM_COMPONENT.encode())',
    'raise RuntimeError("premium filter component missing from dist")',
    'raise RuntimeError("Phase 04.3 V4 runtime verification failed")',
]
for needle in required:
    if script.count(needle) != 1:
        fail(f"unexpected V4 installer signature: {needle}")

# Root cause: Vite/esbuild may minify the React function identifier, so the
# literal component name is not a valid dist/live runtime marker. Verify the
# stable DOM class string emitted by the component instead.
script = script.replace(
    'print("RUNNING=PHASE04_3_TEAM_MEMBERS_FLAGSHIP_V4")',
    'print("RUNNING=PHASE04_3_TEAM_MEMBERS_FLAGSHIP_V4_RECOVERY_V1")',
    1,
)
script = script.replace(
    'PREMIUM_COMPONENT = "TeamPremiumSelectV4"',
    'PREMIUM_COMPONENT = "TeamPremiumSelectV4"\nBUNDLE_COMPONENT_MARKER = "tos-team-premium-filter-menu-v4"',
    1,
)
script = script.replace(
    'component_dist = tree_count(DIST, PREMIUM_COMPONENT.encode())',
    'component_dist = tree_count(DIST, BUNDLE_COMPONENT_MARKER.encode())',
    1,
)
script = script.replace(
    'component_live = tree_count(LIVE, PREMIUM_COMPONENT.encode())',
    'component_live = tree_count(LIVE, BUNDLE_COMPONENT_MARKER.encode())',
    1,
)
script = script.replace(
    'raise RuntimeError("premium filter component missing from dist")',
    'raise RuntimeError("premium filter runtime class missing from dist")',
    1,
)
script = script.replace(
    'raise RuntimeError("Phase 04.3 V4 runtime verification failed")',
    'raise RuntimeError("Phase 04.3 V4 runtime class verification failed")',
    1,
)

success_anchor = '    print("V4_RUNTIME=YES")\n'
if script.count(success_anchor) != 1:
    fail("V4 success report anchor missing")
script = script.replace(
    success_anchor,
    success_anchor + '    print("V4_RECOVERY_V1=YES")\n',
    1,
)

# Add explicit stable runtime-marker counts to the success report.
report_anchor = '    print(f"DIST_V4_RUNTIME_COUNT={dist_v4}")\n    print(f"LIVE_V4_RUNTIME_COUNT={live_v4}")\n'
if script.count(report_anchor) != 1:
    fail("V4 runtime report anchor missing")
script = script.replace(
    report_anchor,
    '    print(f"DIST_V4_RUNTIME_COUNT={dist_v4}")\n'
    '    print(f"DIST_PREMIUM_MENU_MARKER_COUNT={component_dist}")\n'
    '    print(f"LIVE_V4_RUNTIME_COUNT={live_v4}")\n'
    '    print(f"LIVE_PREMIUM_MENU_MARKER_COUNT={component_live}")\n',
    1,
)

# Both the early fail() and rollback exception report V4_RUNTIME=NO.
script = script.replace(
    '    print("V4_RUNTIME=NO")\n',
    '    print("V4_RUNTIME=NO")\n    print("V4_RECOVERY_V1=NO")\n',
)

with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
    handle.write(script)
    temp_path = Path(handle.name)

try:
    completed = subprocess.run([sys.executable, str(temp_path), TARGET])
    sys.exit(completed.returncode)
finally:
    try:
        temp_path.unlink()
    except OSError:
        pass
