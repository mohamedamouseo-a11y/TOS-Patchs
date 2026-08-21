#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-}"
PATCH="${2:-}"

if [[ -z "$ROOT" || -z "$PATCH" ]]; then
  echo "usage: run_batch4_2_1_task_residuals.sh REPO_ROOT OUTPUT_PATCH" >&2
  exit 2
fi

GENERATOR_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/164e4d97fa285dcac559ae712e0b533b4dac9bb5/TOS-ENGLISH-LOCALIZATION-BATCH4-2-1-TASK-RESIDUALS-GIT-GENERATED/generate_batch4_2_1_task_residuals.py"
GENERATOR="/var/tmp/generate_batch4_2_1_task_residuals.py"

rm -f "$GENERATOR"
curl -fL "$GENERATOR_URL" -o "$GENERATOR"
python3 -m py_compile "$GENERATOR"
echo "GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$ROOT" "$PATCH"
echo "FINAL_PATCH_SHA256=$(sha256sum "$PATCH" | awk '{print $1}')"
