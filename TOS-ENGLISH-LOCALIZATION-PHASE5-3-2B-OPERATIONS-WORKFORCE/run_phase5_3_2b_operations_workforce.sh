#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-/var/www/TOS}"
PATCH_OUT="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_PHASE5_3_2B_OPERATIONS_WORKFORCE.patch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="$SCRIPT_DIR/generate_phase5_3_2b_operations_workforce.py"

python3 -m py_compile "$GENERATOR"
echo "PHASE5_3_2B_GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$REPO_ROOT" "$PATCH_OUT"
