#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: run_batch4_2_5_chatpanel_arabic_huddle.sh REPO_ROOT OUTPUT_PATCH" >&2
  exit 2
fi

REPO_ROOT="$1"
OUTPUT_PATCH="$2"
GENERATOR=/var/tmp/generate_batch4_2_5_chatpanel_arabic_huddle.py
GENERATOR_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/150ddb8901a92db552e75bb19bb8a4eead4c8f0e/TOS-ENGLISH-LOCALIZATION-BATCH4-2-5-ARABIC-HUDDLE-GIT-GENERATED/generate_batch4_2_5_chatpanel_arabic_huddle.py"

rm -f "$GENERATOR"
curl -fL "$GENERATOR_URL" -o "$GENERATOR"
python3 -m py_compile "$GENERATOR"
echo "GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$REPO_ROOT" "$OUTPUT_PATCH"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUTPUT_PATCH" | awk '{print $1}')"
