#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH4_3_1_TEAM.patch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIGINAL="$SCRIPT_DIR/generate_batch4_3_1_team.py"
V3="$SCRIPT_DIR/generate_batch4_3_1_team_v3.py"

python3 -m py_compile "$V3"
echo "V3_WRAPPER_COMPILE=PASS"
python3 "$V3" "$ORIGINAL" "$ROOT" "$PATCH"
