#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 REPO_ROOT OUTPUT_PATCH" >&2
  exit 2
fi

REPO_ROOT="$1"
OUTPUT_PATCH="$2"
GENERATOR="/var/tmp/generate_batch2_2_from_live.py"

rm -f "$GENERATOR"

curl -fL \
"https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/0a66dde91a2426f11e3befc09da0f2fc0fa38bb2/TOS-ENGLISH-LOCALIZATION-BATCH2-2-GITHUB-VERIFY-GIT-GENERATED/generate_batch2_2_from_live.py" \
-o "$GENERATOR"

chmod 700 "$GENERATOR"
python3 -m py_compile "$GENERATOR"
echo "GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$REPO_ROOT" "$OUTPUT_PATCH"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUTPUT_PATCH" | awk '{print $1}')"
