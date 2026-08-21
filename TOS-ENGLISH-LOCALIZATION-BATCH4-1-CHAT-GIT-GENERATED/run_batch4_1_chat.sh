#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-/var/www/TOS}"
OUT_PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH4_1_CHAT.patch}"
GENERATOR="/var/tmp/generate_batch4_1_chat.py"

curl -fL \
  "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/899c177d3c6b69ee74e5fef7c66f60e95e3442b5/TOS-ENGLISH-LOCALIZATION-BATCH4-1-CHAT-GIT-GENERATED/generate_batch4_1_chat.py" \
  -o "$GENERATOR"

chmod 700 "$GENERATOR"
python3 -m py_compile "$GENERATOR"
echo "GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$REPO_ROOT" "$OUT_PATCH"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUT_PATCH" | awk '{print $1}')"
