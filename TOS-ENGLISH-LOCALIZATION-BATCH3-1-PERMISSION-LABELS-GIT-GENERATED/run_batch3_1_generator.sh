#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH="${2:-/var/tmp/TOS_ENGLISH_LOCALIZATION_BATCH3_1_PERMISSION_LABELS.patch}"
GEN="/var/tmp/generate_batch3_1_from_live.py"

curl -fL \
  "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/f756ad4ed9049e6e305fa4dc966cd3735e7bac04/TOS-ENGLISH-LOCALIZATION-BATCH3-1-PERMISSION-LABELS-GIT-GENERATED/generate_batch3_1_from_live.py" \
  -o "$GEN"

python3 - <<'PY'
from pathlib import Path
src = Path('/var/tmp/generate_batch3_1_from_live.py').read_text(encoding='utf-8')
compile(src, 'generate_batch3_1_from_live.py', 'exec')
print('GENERATOR_COMPILE=PASS')
PY

python3 "$GEN" "$ROOT" "$PATCH"

echo "FINAL_PATCH_SHA256=$(sha256sum "$PATCH" | awk '{print $1}')"
