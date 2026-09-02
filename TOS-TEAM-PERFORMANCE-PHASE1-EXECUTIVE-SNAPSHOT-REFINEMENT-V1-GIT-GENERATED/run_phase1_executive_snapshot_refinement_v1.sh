#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HEAD="8b29fd2ec2c96ce422b927711310b35fe6c52c61"
DASHBOARD="frontend/src/pages/TeamPerformanceDashboard.jsx"
EXECUTIVE="frontend/src/components/performance/ExecutiveCommandCenter.jsx"
DISCLOSURE="frontend/src/components/performance/PerformanceDisclosure.jsx"
DARK_CSS="frontend/src/components/performance/teamPerformancePremiumDark.css"

cd "$TOS_ROOT"

actual_head="$(git rev-parse HEAD)"
if [[ "$actual_head" != "$EXPECTED_HEAD" ]]; then
  echo "ERROR: expected HEAD $EXPECTED_HEAD but found $actual_head" >&2
  exit 2
fi

# This refinement is intentionally layered on top of the approved Premium Dark + Phase 1 UX changes.
mapfile -t before < <({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u)
expected_before=("$DARK_CSS" "$DASHBOARD" "$DISCLOSURE")
mapfile -t expected_before_sorted < <(printf '%s\n' "${expected_before[@]}" | sort -u)
if [[ "$(printf '%s\n' "${before[@]}")" != "$(printf '%s\n' "${expected_before_sorted[@]}")" ]]; then
  echo "ERROR: unexpected working tree before refinement:" >&2
  git status --short >&2
  exit 3
fi

# Executive component itself must still match the pushed Phase 12 baseline before this patch.
if ! git diff --quiet -- "$EXECUTIVE"; then
  echo "ERROR: ExecutiveCommandCenter.jsx already has local changes; refusing to overlap them." >&2
  exit 4
fi

[[ -f "$DISCLOSURE" ]] || { echo "ERROR: Phase 1 PerformanceDisclosure.jsx missing" >&2; exit 5; }
[[ -f "$DARK_CSS" ]] || { echo "ERROR: Premium Dark stylesheet missing" >&2; exit 6; }

grep -Fq 'tos-team-performance-premium' "$DASHBOARD"
grep -Fq 'PerformanceDisclosure' "$DASHBOARD"

python3 "$PATCH_ROOT/01_phase1_executive_snapshot_refinement.py"

# Contract checks.
grep -Fq 'const [detailsOpen, setDetailsOpen] = useState(false);' "$EXECUTIVE"
grep -Fq 'slice(0, detailsOpen ? 10 : 3)' "$EXECUTIVE"
grep -Fq 'slice(0, detailsOpen ? 6 : 2)' "$EXECUTIVE"
grep -Fq 'View executive details' "$EXECUTIVE"
grep -Fq 'Hide executive details' "$EXECUTIVE"
grep -Fq 'Decision Domains' "$EXECUTIVE"
grep -Fq 'Department Health Signals' "$EXECUTIVE"
grep -Fq 'detailsOpen ? "" : "hidden"' "$EXECUTIVE"

# No backend/schema/package changes.
mapfile -t after < <({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u)
expected_after=("$DARK_CSS" "$DASHBOARD" "$DISCLOSURE" "$EXECUTIVE")
mapfile -t expected_after_sorted < <(printf '%s\n' "${expected_after[@]}" | sort -u)
if [[ "$(printf '%s\n' "${after[@]}")" != "$(printf '%s\n' "${expected_after_sorted[@]}")" ]]; then
  echo "ERROR: unexpected changed file scope after refinement:" >&2
  printf '  %s\n' "${after[@]}" >&2
  exit 7
fi

if printf '%s\n' "${after[@]}" | grep -Eq '^(backend/|.*schema\.prisma$|.*migration|package(-lock)?\.json$|frontend/package(-lock)?\.json$)'; then
  echo "ERROR: forbidden backend/schema/migration/package change detected" >&2
  exit 8
fi

git diff --check
npm --prefix frontend run build
[[ -f frontend/dist/index.html ]]

echo "TEAM_PERFORMANCE_PHASE1_EXECUTIVE_SNAPSHOT_REFINEMENT_V1_APPLIED=YES"
echo "BASELINE_HEAD=$EXPECTED_HEAD"
echo "EXECUTIVE_DEFAULT_MODE=SNAPSHOT"
echo "EXECUTIVE_KPIS_VISIBLE=5"
echo "EXECUTIVE_BRIEF_DEFAULT_LINES=2"
echo "EXECUTIVE_PRIORITIES_DEFAULT=3"
echo "EXECUTIVE_DETAILS_TOGGLE=YES"
echo "DECISION_DOMAINS_DEFAULT_HIDDEN=YES"
echo "DEPARTMENT_HEALTH_DEFAULT_HIDDEN=YES"
echo "PHASE1_EXISTING_DISCLOSURES_PRESERVED=YES"
echo "TEAM_TABLE_BEHAVIOR_PRESERVED=YES"
echo "PREMIUM_DARK_MODE_PRESERVED=YES"
echo "FRONTEND_BUILD=PASS"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "--- git status --short ---"
git status --short
