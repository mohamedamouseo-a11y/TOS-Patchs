#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
OUTPUT="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH3.patch}"
PAYLOAD=/var/tmp/generate_batch3_from_live.py.gz.b64
GENERATOR=/var/tmp/generate_batch3_from_live.py

curl -fL "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/203ba928430707cd08c89caf78f31526b67959b2/TOS-ENGLISH-LOCALIZATION-BATCH3-DASHBOARD-FILES-AUDIT-PERMISSIONS-GIT-GENERATED/generate_batch3_from_live.py.gz.b64" -o "$PAYLOAD"

echo "GENERATOR_B64_SHA256=$(sha256sum "$PAYLOAD" | awk '{print $1}')"
base64 -d "$PAYLOAD" | gzip -dc > "$GENERATOR"
chmod 700 "$GENERATOR"
python3 -m py_compile "$GENERATOR"
echo "GENERATOR_COMPILE=PASS"
python3 "$GENERATOR" "$ROOT" "$OUTPUT"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUTPUT" | awk '{print $1}')"
