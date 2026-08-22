#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_PHASE5_3_1_SETTINGS_CORE.patch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="$SCRIPT_DIR/generate_phase5_3_1_settings_core.py"

python3 -m py_compile "$GENERATOR"
echo "PHASE5_3_1_GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$ROOT" "$PATCH"
