#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH4_1_1_CHAT_RESIDUALS.patch}"
GEN="/var/tmp/generate_batch4_1_1_chat_residuals.py"

URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/aa85f06b03869e6766fb8d79749c4c7cbb856e65/TOS-ENGLISH-LOCALIZATION-BATCH4-1-1-CHAT-RESIDUALS-LIVE-GIT-GENERATED/generate_batch4_1_1_chat_residuals.py"

rm -f "$GEN" "$PATCH"
curl -fL "$URL" -o "$GEN"
python3 -m py_compile "$GEN"
echo "GENERATOR_COMPILE=PASS"
chmod 700 "$GEN"
python3 "$GEN" "$ROOT" "$PATCH"
echo "FINAL_PATCH_SHA256=$(sha256sum "$PATCH" | awk '{print $1}')"
