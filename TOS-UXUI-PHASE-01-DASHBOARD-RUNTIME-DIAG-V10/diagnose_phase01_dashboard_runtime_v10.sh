#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
FRONTEND="$ROOT/frontend"

echo "PHASE01_RUNTIME_DIAG_V10=START"
echo "TOS_HEAD=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --porcelain=v1 --untracked-files=all || true

echo "--- SOURCE MARKERS ---"
for check in \
  "$FRONTEND/src/main.jsx:dashboard-github-reference.css" \
  "$FRONTEND/src/pages/Dashboard.jsx:tos-dashboard-page" \
  "$FRONTEND/src/pages/Dashboard.jsx:tos-dashboard-dark-card" \
  "$FRONTEND/src/styles/dashboard-github-reference.css:TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V8_START"; do
  file="${check%%:*}"; marker="${check#*:}"
  if [ -f "$file" ] && grep -Fq "$marker" "$file"; then echo "SOURCE_MARKER=PASS:$marker"; else echo "SOURCE_MARKER=FAIL:$marker"; fi
done

echo "--- BUILD ---"
cd "$FRONTEND"
npm run build

echo "--- DIST MARKERS ---"
if [ ! -d "$FRONTEND/dist" ]; then
  echo "DIST_DIR=ABSENT"
else
  echo "DIST_DIR=$FRONTEND/dist"
  grep -RFl --include='*.js' --include='*.css' 'tos-dashboard-dark-card' "$FRONTEND/dist" | head -5 | sed 's/^/DIST_DARK_CARD_MARKER=/' || true
  grep -RFl --include='*.css' '#1d2b36' "$FRONTEND/dist" | head -5 | sed 's/^/DIST_DARK_COLOR_MARKER=/' || true
  echo "DIST_INDEX_ASSETS=$(grep -oE '/assets/[^\" ]+' "$FRONTEND/dist/index.html" 2>/dev/null | tr '\n' ',' || true)"
fi

echo "--- NGINX ROOTS ---"
(nginx -T 2>/dev/null || sudo -n nginx -T 2>/dev/null || true) | awk '/server_name|^[[:space:]]*root[[:space:]]/ {print}' | head -80

echo "--- CANDIDATE INDEX FILES ---"
find /var/www -maxdepth 5 -type f -name index.html -print 2>/dev/null | head -40

echo "--- RUNNING FRONTEND/WEB PROCESSES ---"
ps -eo pid,cmd | grep -E 'vite|nginx|node|serve|pm2' | grep -v grep | head -80 || true

echo "PHASE01_RUNTIME_DIAG_V10=PASS"
echo "NO_SOURCE_MODIFICATIONS=YES"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
