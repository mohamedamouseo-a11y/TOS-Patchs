#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH4_3_1_TEAM.patch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIGINAL="$SCRIPT_DIR/generate_batch4_3_1_team.py"
REPAIR="$SCRIPT_DIR/generate_batch4_3_1_team_v2.py"

python3 -m py_compile "$REPAIR"
echo "V2_WRAPPER_COMPILE=PASS"
python3 "$REPAIR" "$ORIGINAL" "$ROOT" "$PATCH"
