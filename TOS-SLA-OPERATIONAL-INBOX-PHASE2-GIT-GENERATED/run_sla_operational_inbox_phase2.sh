#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
OUT="${2:-/var/tmp/TOS_SLA_OPERATIONAL_INBOX_PHASE2.patch}"
GEN="/var/tmp/generate_sla_operational_inbox_phase2.py"

GEN_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/7c504d11b191ea2d2b524dbdc2e85d4c3d8aa518/TOS-SLA-OPERATIONAL-INBOX-PHASE2-GIT-GENERATED/generate_sla_operational_inbox_phase2.py"

rm -f "$GEN" "$OUT"
curl -fL "$GEN_URL" -o "$GEN"
chmod 700 "$GEN"
python3 -m py_compile "$GEN"
echo "GENERATOR_COMPILE=PASS"
python3 "$GEN" "$ROOT" "$OUT"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUT" | awk '{print $1}')"
echo "PATCH_PATH=$OUT"
