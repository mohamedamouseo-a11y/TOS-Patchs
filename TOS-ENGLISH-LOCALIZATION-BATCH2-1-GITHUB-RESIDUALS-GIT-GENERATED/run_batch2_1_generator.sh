#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-/var/www/TOS}"
OUTPUT_PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH2_1_GITHUB_RESIDUALS.patch}"
GENERATOR="/var/tmp/generate_batch2_1_from_live.py"
COMMIT="766b616f3047bd16633ab8f77afd795e6b2a4e81"
URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/${COMMIT}/TOS-ENGLISH-LOCALIZATION-BATCH2-1-GITHUB-RESIDUALS-GIT-GENERATED/generate_batch2_1_from_live.py"

rm -f "$GENERATOR" "$OUTPUT_PATCH"
curl -fL "$URL" -o "$GENERATOR"
chmod 700 "$GENERATOR"
python3 -m py_compile "$GENERATOR"
echo "GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$REPO_ROOT" "$OUTPUT_PATCH"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUTPUT_PATCH" | awk '{print $1}')"
