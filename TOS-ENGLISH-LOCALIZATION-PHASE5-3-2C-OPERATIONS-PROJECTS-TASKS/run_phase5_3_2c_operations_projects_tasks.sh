#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 REPO_ROOT OUTPUT_PATCH" >&2
  exit 2
fi

REPO_ROOT="$1"
OUTPUT_PATCH="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="$SCRIPT_DIR/generate_phase5_3_2c_operations_projects_tasks.py"

python3 -m py_compile "$GENERATOR"
echo "PHASE5_3_2C_GENERATOR_COMPILE=PASS"

exec python3 "$GENERATOR" "$REPO_ROOT" "$OUTPUT_PATCH"
