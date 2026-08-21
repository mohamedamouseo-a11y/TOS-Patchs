#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH4_3_1_TEAM.patch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="$SCRIPT_DIR/generate_batch4_3_1_team.py"

python3 -m py_compile "$GENERATOR"
echo "GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$ROOT" "$PATCH"
