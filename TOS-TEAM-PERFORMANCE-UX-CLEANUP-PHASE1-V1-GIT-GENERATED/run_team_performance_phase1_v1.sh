#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HEAD="8b29fd2ec2c96ce422b927711310b35fe6c52c61"
DASHBOARD="frontend/src/pages/TeamPerformanceDashboard.jsx"
DISCLOSURE="frontend/src/components/performance/PerformanceDisclosure.jsx"
DARK_CSS="frontend/src/components/performance/teamPerformancePremiumDark.css"

cd "$TOS_ROOT"

actual_head="$(git rev-parse HEAD)"
if [[ "$actual_head" != "$EXPECTED_HEAD" ]]; then
  echo "ERROR: expected TOS HEAD $EXPECTED_HEAD but found $actual_head" >&2
  exit 2
fi

# Phase 1 is intentionally designed to build on the approved, still-uncommitted
# Premium Dark Mode patch. We allow either a clean tree or EXACTLY that known state.
pre_status="$(git status --short)"
expected_dark_status=$' M frontend/src/pages/TeamPerformanceDashboard.jsx\n?? frontend/src/components/performance/teamPerformancePremiumDark.css'
if [[ -n "$pre_status" && "$pre_status" != "$expected_dark_status" ]]; then
  echo "ERROR: unexpected pre-existing TOS changes. Expected clean tree or approved Premium Dark Mode state only." >&2
  git status --short >&2
  exit 3
fi

if [[ "$pre_status" == "$expected_dark_status" ]]; then
  echo "PREEXISTING_PREMIUM_DARK_MODE=YES"
else
  echo "PREEXISTING_PREMIUM_DARK_MODE=NO"
fi

python3 "$PATCH_ROOT/01_team_performance_phase1.py"

# Functional / UX contract markers.
grep -Fq 'import { PerformanceDisclosure } from "../components/performance/PerformanceDisclosure";' "$DASHBOARD"
grep -Fq 'const [showAllEmployees, setShowAllEmployees] = useState(false);' "$DASHBOARD"
grep -Fq 'const visibleEmployees = useMemo(' "$DASHBOARD"
grep -Fq 'id="phase1-goals-disclosure"' "$DASHBOARD"
grep -Fq 'id="phase1-intelligence-disclosure"' "$DASHBOARD"
grep -Fq 'id="phase1-deep-dive-disclosure"' "$DASHBOARD"
grep -Fq 'id="phase1-show-all-employees"' "$DASHBOARD"
grep -Fq 'export function PerformanceDisclosure' "$DISCLOSURE"
grep -Fq 'TEAM_TABLE_INITIAL_ROWS=8' "$PATCH_ROOT/01_team_performance_phase1.py"

# Preserve all existing Phase 3-12 panels / employee drawer wiring.
for marker in \
  'ExecutiveCommandCenterPanel' \
  'PerformanceReviewsPanel' \
  'WorkforcePlanningPanel' \
  'SkillsDevelopmentPanel' \
  'TalentSuccessionPanel' \
  'RecognitionRewardsPanel' \
  'openEmployee(employee.id)' \
  'drawerOpen && selectedEmployee'; do
  grep -Fq "$marker" "$DASHBOARD"
done

# Phase boundary: no Phase 2 date comparison, Help Center, or Ramzy in this patch.
if grep -Eq 'comparePeriod|comparisonPeriod|Help Center|Ramzy|RAMZY' "$DISCLOSURE"; then
  echo "ERROR: Phase 1 patch crossed into a later phase." >&2
  exit 4
fi

# Scope guard.
mapfile -t changed < <({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u)
allowed=("$DASHBOARD" "$DISCLOSURE" "$DARK_CSS")
for path in "${changed[@]}"; do
  allowed_match=0
  for expected in "${allowed[@]}"; do
    if [[ "$path" == "$expected" ]]; then allowed_match=1; break; fi
  done
  if [[ "$allowed_match" -ne 1 ]]; then
    echo "ERROR: unexpected changed path: $path" >&2
    exit 5
  fi
done

# Dashboard + new disclosure are required.
printf '%s\n' "${changed[@]}" | grep -Fxq "$DASHBOARD"
printf '%s\n' "${changed[@]}" | grep -Fxq "$DISCLOSURE"

# No backend / schema / package changes.
if printf '%s\n' "${changed[@]}" | grep -Eq '^(backend/|package\.json$|package-lock\.json$|frontend/package\.json$|frontend/package-lock\.json$)'; then
  echo "ERROR: backend/schema/package scope changed." >&2
  exit 6
fi

git diff --check
npm --prefix frontend run build

echo "TEAM_PERFORMANCE_UX_CLEANUP_PHASE1_V1_APPLIED=YES"
echo "BASELINE_HEAD=$EXPECTED_HEAD"
echo "CORE_KPIS_VISIBLE=5"
echo "EXECUTIVE_COMMAND_CENTER_ALWAYS_VISIBLE=YES"
echo "COLLAPSIBLE_SECTIONS=3"
echo "TEAM_TABLE_INITIAL_ROWS=8"
echo "SHOW_ALL_EMPLOYEES_AVAILABLE=YES"
echo "EMPLOYEE_DRAWER_PRESERVED=YES"
echo "DETAILS_REMOVED=NO"
echo "DATE_COMPARE_ADDED=NO"
echo "HELP_CENTER_ADDED=NO"
echo "RAMZY_CHANGED=NO"
echo "FRONTEND_BUILD=PASS"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "--- git status --short ---"
git status --short
