#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_PHASE5_3_1_SETTINGS_CORE_V3.patch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$SCRIPT_DIR/generate_phase5_3_1_settings_core.py"
V2="$SCRIPT_DIR/generate_phase5_3_1_settings_core_v2.py"
V3="$SCRIPT_DIR/generate_phase5_3_1_settings_core_v3.py"

python3 -m py_compile "$BASE" "$V2" "$V3"
echo "PHASE5_3_1_V3_GENERATOR_COMPILE=PASS"
python3 "$V3" "$ROOT" "$PATCH"
