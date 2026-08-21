#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-/var/www/TOS}"
OUTPUT_PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH2_SETTINGS_GITHUB.patch}"
WORK_DIR="${TMPDIR:-/var/tmp}/tos-batch2-generator"
B64="$WORK_DIR/generate_batch2_from_live.py.gz.b64"
GZ="$WORK_DIR/generate_batch2_from_live.py.gz"
PY="$WORK_DIR/generate_batch2_from_live.py"

mkdir -p "$WORK_DIR"
rm -f "$B64" "$GZ" "$PY" "$OUTPUT_PATCH"

curl -fL "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/04ea6214761aa0a450eec2fd523c6b62d1acb047/TOS-ENGLISH-LOCALIZATION-BATCH2-SETTINGS-GITHUB-GIT-GENERATED/generate_batch2_from_live.py.gz.b64" -o "$B64"

printf 'GENERATOR_B64_SHA256='
sha256sum "$B64" | awk '{print $1}'

base64 -d "$B64" > "$GZ"
gzip -dc "$GZ" > "$PY"
chmod 700 "$PY"
python3 -m py_compile "$PY"

python3 "$PY" "$REPO_ROOT" "$OUTPUT_PATCH"

printf 'FINAL_PATCH_SHA256='
sha256sum "$OUTPUT_PATCH" | awk '{print $1}'
printf 'FINAL_PATCH=%s\n' "$OUTPUT_PATCH"
