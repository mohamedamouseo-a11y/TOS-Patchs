#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HEAD="8b29fd2ec2c96ce422b927711310b35fe6c52c61"
DASHBOARD="frontend/src/pages/TeamPerformanceDashboard.jsx"
CSS_FILE="frontend/src/components/performance/teamPerformancePremiumDark.css"

cd "$TOS_ROOT"

actual_head="$(git rev-parse HEAD)"
if [[ "$actual_head" != "$EXPECTED_HEAD" ]]; then
  echo "ERROR: expected TOS HEAD $EXPECTED_HEAD but found $actual_head" >&2
  exit 2
fi

if [[ -n "$(git status --short)" ]]; then
  echo "ERROR: TOS working tree must be clean before applying premium dark mode patch." >&2
  git status --short >&2
  exit 3
fi

python3 "$PATCH_ROOT/01_team_performance_premium_dark.py"

# Contract checks.
grep -Fq 'import "../components/performance/teamPerformancePremiumDark.css";' "$DASHBOARD"
grep -Fq 'tos-page tos-team-performance-premium space-y-4' "$DASHBOARD"
grep -Fq 'html.dark .tos-team-performance-premium' "$CSS_FILE"
grep -Fq -- '--tp-surface: #14171c;' "$CSS_FILE"
grep -Fq -- '--tp-gold: #d9a441;' "$CSS_FILE"
grep -Fq 'Tables: remove beige/light sheet appearance' "$CSS_FILE"
grep -Fq 'Active segmented controls: premium gold instead of white inversion' "$CSS_FILE"

# Dark-mode-only guard: CSS must not define a light-mode root selector.
if grep -Eq '(^|[,{[:space:]])\.tos-team-performance-premium[[:space:]]*\{' "$CSS_FILE"; then
  echo "ERROR: found an unscoped Team Performance CSS rule that could affect light mode." >&2
  exit 4
fi

# Scope guard: exactly the dashboard plus the new scoped stylesheet may change.
mapfile -t changed < <({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u)
expected=("$CSS_FILE" "$DASHBOARD")
mapfile -t expected_sorted < <(printf '%s\n' "${expected[@]}" | sort -u)
if [[ "$(printf '%s\n' "${changed[@]}")" != "$(printf '%s\n' "${expected_sorted[@]}")" ]]; then
  echo "ERROR: unexpected changed file scope:" >&2
  printf '  %s\n' "${changed[@]}" >&2
  exit 5
fi

git diff --check

# Compile the actual frontend. Do not deploy here; deployment is an explicit OpenHands step.
npm --prefix frontend run build

echo "TEAM_PERFORMANCE_PREMIUM_DARK_MODE_V1_APPLIED=YES"
echo "BASELINE_HEAD=$EXPECTED_HEAD"
echo "DARK_MODE_ONLY=YES"
echo "LIGHT_MODE_UNCHANGED=YES"
echo "LAYOUT_STRUCTURE_UNCHANGED=YES"
echo "FRONTEND_BUILD=PASS"
echo "EXPECTED_CHANGED_FILES=$DASHBOARD,$CSS_FILE"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "--- git status --short ---"
git status --short
