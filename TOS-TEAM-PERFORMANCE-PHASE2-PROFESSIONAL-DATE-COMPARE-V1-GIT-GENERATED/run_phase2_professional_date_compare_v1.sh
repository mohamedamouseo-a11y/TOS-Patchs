#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HEAD="8b29fd2ec2c96ce422b927711310b35fe6c52c61"
DASHBOARD="frontend/src/pages/TeamPerformanceDashboard.jsx"
CONTROL="frontend/src/components/performance/PerformancePeriodControl.jsx"

cd "$TOS_ROOT"

actual_head="$(git rev-parse HEAD)"
if [[ "$actual_head" != "$EXPECTED_HEAD" ]]; then
  echo "ERROR: expected TOS HEAD $EXPECTED_HEAD but found $actual_head" >&2
  exit 2
fi

# Phase 2 is intentionally applied on top of the approved, still-uncommitted
# Premium Dark + Phase 1 + Global Header working tree.
mapfile -t before < <({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u)
expected_before=(
  "frontend/src/components/layout/Topbar.jsx"
  "frontend/src/components/layout/premiumHeaderDark.css"
  "frontend/src/components/performance/ExecutiveCommandCenter.jsx"
  "frontend/src/components/performance/PerformanceDisclosure.jsx"
  "frontend/src/components/performance/teamPerformancePremiumDark.css"
  "frontend/src/pages/TeamPerformanceDashboard.jsx"
)
mapfile -t expected_before_sorted < <(printf '%s\n' "${expected_before[@]}" | sort -u)
if [[ "$(printf '%s\n' "${before[@]}")" != "$(printf '%s\n' "${expected_before_sorted[@]}")" ]]; then
  echo "ERROR: unexpected pre-existing TOS working-tree scope." >&2
  echo "Actual:" >&2
  printf '  %s\n' "${before[@]}" >&2
  exit 3
fi

# Required prior-phase markers.
grep -Fq 'phase1-goals-disclosure' "$DASHBOARD"
grep -Fq 'phase1-intelligence-disclosure' "$DASHBOARD"
grep -Fq 'phase1-deep-dive-disclosure' "$DASHBOARD"
grep -Fq 'phase1-show-all-employees' "$DASHBOARD"
grep -Fq 'teamPerformancePremiumDark.css' "$DASHBOARD"
grep -Fq 'View executive details' frontend/src/components/performance/ExecutiveCommandCenter.jsx
grep -Fq 'premiumHeaderDark.css' frontend/src/components/layout/Topbar.jsx

python3 "$PATCH_ROOT/01_phase2_professional_date_compare.py"

# Phase 2 contract checks.
grep -Fq 'PerformancePeriodControl' "$DASHBOARD"
grep -Fq '{ key: "quarter", label: "Quarter" }' "$DASHBOARD"
grep -Fq 'quarterStartMonth' "$DASHBOARD"
grep -Fq 'const [compareMode, setCompareMode] = useState("previous_period")' "$DASHBOARD"
grep -Fq 'async function loadComparison()' "$DASHBOARD"
grep -Fq 'const comparisonByEmployee = useMemo(' "$DASHBOARD"
grep -Fq 'same employee vs comparison' "$DASHBOARD"
grep -Fq 'preset === "quarter" ? "QUARTERLY"' "$DASHBOARD"
grep -Fq 'id="phase2-professional-period-control"' "$CONTROL"
grep -Fq 'Previous period' "$CONTROL"
grep -Fq 'Previous month' "$CONTROL"
grep -Fq 'Previous year' "$CONTROL"
grep -Fq 'Custom comparison' "$CONTROL"
grep -Fq 'No comparison' "$CONTROL"
grep -Fq 'export function ComparisonDelta' "$CONTROL"

# Existing API is reused for both periods; Phase 2 must not touch backend/API contracts.
team_api_count="$(grep -F 'api.tasks.teamPerformance({' "$DASHBOARD" | wc -l | tr -d ' ')"
if [[ "$team_api_count" -lt 2 ]]; then
  echo "ERROR: expected current + comparison teamPerformance API calls." >&2
  exit 4
fi

# Scope guard.
mapfile -t changed < <({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u)
expected_after=(
  "frontend/src/components/layout/Topbar.jsx"
  "frontend/src/components/layout/premiumHeaderDark.css"
  "frontend/src/components/performance/ExecutiveCommandCenter.jsx"
  "frontend/src/components/performance/PerformanceDisclosure.jsx"
  "frontend/src/components/performance/PerformancePeriodControl.jsx"
  "frontend/src/components/performance/teamPerformancePremiumDark.css"
  "frontend/src/pages/TeamPerformanceDashboard.jsx"
)
mapfile -t expected_after_sorted < <(printf '%s\n' "${expected_after[@]}" | sort -u)
if [[ "$(printf '%s\n' "${changed[@]}")" != "$(printf '%s\n' "${expected_after_sorted[@]}")" ]]; then
  echo "ERROR: unexpected changed file scope after Phase 2:" >&2
  printf '  %s\n' "${changed[@]}" >&2
  exit 5
fi

if printf '%s\n' "${changed[@]}" | grep -Eq '^(backend/|frontend/src/lib/api\.js$|package(-lock)?\.json$|frontend/package(-lock)?\.json$)'; then
  echo "ERROR: Phase 2 changed forbidden backend/API/package files." >&2
  exit 6
fi

git diff --check
npm --prefix frontend run build

test -f frontend/dist/index.html

echo "TEAM_PERFORMANCE_PHASE2_PROFESSIONAL_DATE_COMPARE_V1_APPLIED=YES"
echo "BASELINE_HEAD=$EXPECTED_HEAD"
echo "PROFESSIONAL_DATE_RANGE=YES"
echo "QUARTER_PRESET=YES"
echo "COMPARE_PREVIOUS_PERIOD=YES"
echo "COMPARE_PREVIOUS_MONTH=YES"
echo "COMPARE_PREVIOUS_YEAR=YES"
echo "COMPARE_CUSTOM=YES"
echo "COMPARE_OFF=YES"
echo "CORE_KPI_COMPARISON=YES"
echo "EMPLOYEE_SCORE_COMPARISON=YES"
echo "PHASE1_PRESERVED=YES"
echo "GLOBAL_HEADER_PRESERVED=YES"
echo "BACKEND_CHANGED=NO"
echo "API_CONTRACT_CHANGED=NO"
echo "FRONTEND_BUILD=PASS"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "--- git status --short ---"
git status --short
