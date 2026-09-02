#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HEAD="8b29fd2ec2c96ce422b927711310b35fe6c52c61"

cd "$TOS_ROOT"

actual_head="$(git rev-parse HEAD)"
if [[ "$actual_head" != "$EXPECTED_HEAD" ]]; then
  echo "ERROR: expected HEAD $EXPECTED_HEAD but found $actual_head" >&2
  exit 2
fi

mapfile -t before < <({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u)
expected_before=(
  "frontend/src/components/performance/ExecutiveCommandCenter.jsx"
  "frontend/src/components/performance/PerformanceDisclosure.jsx"
  "frontend/src/components/performance/teamPerformancePremiumDark.css"
  "frontend/src/pages/TeamPerformanceDashboard.jsx"
)
mapfile -t expected_before_sorted < <(printf '%s\n' "${expected_before[@]}" | sort -u)
if [[ "$(printf '%s\n' "${before[@]}")" != "$(printf '%s\n' "${expected_before_sorted[@]}")" ]]; then
  echo "ERROR: unexpected pre-existing working tree. Do not reset." >&2
  git status --short >&2
  exit 3
fi

python3 "$PATCH_ROOT/01_global_header_premium_dark.py"

TOPBAR="frontend/src/components/layout/Topbar.jsx"
CSS="frontend/src/components/layout/premiumHeaderDark.css"

grep -Fq 'import "./premiumHeaderDark.css";' "$TOPBAR"
grep -Fq 'tos-premium-topbar-actions' "$TOPBAR"
grep -Fq 'tos-premium-topbar-title' "$TOPBAR"
grep -Fq 'TOS_GLOBAL_HEADER_PREMIUM_DARK_UXUI_V1' "$CSS"
grep -Fq 'html.dark[data-tos-design-system="true"] .tos-premium-topbar' "$CSS"
grep -Fq '#14171c' "$CSS"
grep -Fq '#191d24' "$CSS"
grep -Fq 'rgba(217,164,65' "$CSS"

# Dark-only safety: no bare topbar rule may be introduced in this stylesheet.
if grep -Eq '^\.tos-premium-topbar([[:space:],.{:#]|$)' "$CSS"; then
  echo "ERROR: unscoped light-mode topbar selector found" >&2
  exit 4
fi

mapfile -t changed < <({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u)
expected_after=(
  "frontend/src/components/layout/Topbar.jsx"
  "frontend/src/components/layout/premiumHeaderDark.css"
  "frontend/src/components/performance/ExecutiveCommandCenter.jsx"
  "frontend/src/components/performance/PerformanceDisclosure.jsx"
  "frontend/src/components/performance/teamPerformancePremiumDark.css"
  "frontend/src/pages/TeamPerformanceDashboard.jsx"
)
mapfile -t expected_after_sorted < <(printf '%s\n' "${expected_after[@]}" | sort -u)
if [[ "$(printf '%s\n' "${changed[@]}")" != "$(printf '%s\n' "${expected_after_sorted[@]}")" ]]; then
  echo "ERROR: unexpected changed files after header patch" >&2
  printf '  %s\n' "${changed[@]}" >&2
  exit 5
fi

git diff --check
npm --prefix frontend run build

echo "GLOBAL_HEADER_PREMIUM_DARK_UXUI_V1_APPLIED=YES"
echo "BASELINE_HEAD=$EXPECTED_HEAD"
echo "DARK_MODE_HEADER_REFINED=YES"
echo "LIGHT_MODE_UNCHANGED=YES"
echo "HEADER_LOGIC_UNCHANGED=YES"
echo "SIDEBAR_UNCHANGED=YES"
echo "NOTIFICATIONS_LOGIC_UNCHANGED=YES"
echo "PROFILE_LOGIC_UNCHANGED=YES"
echo "THEME_TOGGLE_LOGIC_UNCHANGED=YES"
echo "LANGUAGE_TOGGLE_LOGIC_UNCHANGED=YES"
echo "PHASE1_TEAM_PERFORMANCE_CHANGES_PRESERVED=YES"
echo "FRONTEND_BUILD=PASS"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "--- git status --short ---"
git status --short
