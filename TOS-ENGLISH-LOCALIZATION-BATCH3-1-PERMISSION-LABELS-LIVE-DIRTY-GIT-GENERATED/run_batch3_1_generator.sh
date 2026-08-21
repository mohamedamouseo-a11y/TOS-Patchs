#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH3_1_PERMISSION_LABELS.patch}"
GEN="/var/tmp/generate_batch3_1_from_live_dirty.py"
URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/af497b9ffde097178c797d275cd1168d2dda24df/TOS-ENGLISH-LOCALIZATION-BATCH3-1-PERMISSION-LABELS-LIVE-DIRTY-GIT-GENERATED/generate_batch3_1_from_live_dirty.py"

rm -f "$GEN" "$PATCH"
curl -fL "$URL" -o "$GEN"
python3 -m py_compile "$GEN"
echo "GENERATOR_COMPILE=PASS"
python3 "$GEN" "$ROOT" "$PATCH"
echo "FINAL_PATCH_SHA256=$(sha256sum "$PATCH" | awk '{print $1}')"
