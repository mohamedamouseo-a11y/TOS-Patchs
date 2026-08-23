#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
OUT="${2:-/var/tmp/TOS_SLA_FOUNDATION_PHASE1.patch}"
GEN="/var/tmp/generate_sla_foundation_phase1.py"

GEN_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/d4e860df1a41b97ed97b536abadd420c6e6ab8f1/TOS-SLA-FOUNDATION-PHASE1-GIT-GENERATED/generate_sla_foundation_phase1.py"

rm -f "$GEN" "$OUT"
curl -fL "$GEN_URL" -o "$GEN"
chmod 700 "$GEN"
python3 -m py_compile "$GEN"
echo "GENERATOR_COMPILE=PASS"
python3 "$GEN" "$ROOT" "$OUT"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUT" | awk '{print $1}')"
echo "PATCH_PATH=$OUT"
