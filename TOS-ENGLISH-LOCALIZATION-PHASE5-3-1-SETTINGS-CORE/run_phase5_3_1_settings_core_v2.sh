#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_PHASE5_3_1_SETTINGS_CORE_V2.patch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_GENERATOR="$SCRIPT_DIR/generate_phase5_3_1_settings_core.py"
GENERATOR="$SCRIPT_DIR/generate_phase5_3_1_settings_core_v2.py"

python3 -m py_compile "$BASE_GENERATOR" "$GENERATOR"
echo "PHASE5_3_1_V2_GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$ROOT" "$PATCH"
