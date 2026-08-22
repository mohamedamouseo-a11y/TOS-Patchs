#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_PHASE5_3_1B_SETTINGS_CORE_RESIDUAL.patch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="$SCRIPT_DIR/generate_phase5_3_1b_settings_core_residual.py"

python3 -m py_compile "$GENERATOR"
echo "PHASE5_3_1B_GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$ROOT" "$PATCH"
