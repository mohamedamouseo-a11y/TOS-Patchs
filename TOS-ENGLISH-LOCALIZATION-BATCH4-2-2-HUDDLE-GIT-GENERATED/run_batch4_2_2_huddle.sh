#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: run_batch4_2_2_huddle.sh REPO_ROOT OUTPUT_PATCH" >&2
  exit 2
fi

REPO_ROOT="$1"
OUTPUT_PATCH="$2"
GENERATOR=/var/tmp/generate_batch4_2_2_huddle.py
GENERATOR_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/c5c2babb46f93d0cba8760145221e662fff0f5d8/TOS-ENGLISH-LOCALIZATION-BATCH4-2-2-HUDDLE-GIT-GENERATED/generate_batch4_2_2_huddle.py"

rm -f "$GENERATOR"
curl -fL "$GENERATOR_URL" -o "$GENERATOR"
python3 -m py_compile "$GENERATOR"
echo "GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$REPO_ROOT" "$OUTPUT_PATCH"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUTPUT_PATCH" | awk '{print $1}')"
