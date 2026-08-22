#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_PHASE5_3_2A_OPERATIONS_V2.patch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$SCRIPT_DIR/generate_phase5_3_2a_operations_shell_general_security.py"
V2="$SCRIPT_DIR/generate_phase5_3_2a_operations_shell_general_security_v2.py"

python3 -m py_compile "$BASE" "$V2"
echo "PHASE5_3_2A_V2_GENERATOR_COMPILE=PASS"
python3 "$V2" "$ROOT" "$PATCH"
