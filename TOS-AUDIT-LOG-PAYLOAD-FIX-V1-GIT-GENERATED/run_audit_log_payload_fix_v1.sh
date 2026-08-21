#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
OUT="${2:-/var/tmp/TOS_AUDIT_LOG_PAYLOAD_FIX_V1.patch}"
GEN="/var/tmp/generate_audit_log_payload_fix_v1.py"

GEN_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/acb034336f4b78b6bcc2deda9a1e95959acac736/TOS-AUDIT-LOG-PAYLOAD-FIX-V1-GIT-GENERATED/generate_audit_log_payload_fix_v1.py"

rm -f "$GEN" "$OUT"
curl -fL "$GEN_URL" -o "$GEN"
chmod 700 "$GEN"
python3 -m py_compile "$GEN"
echo "GENERATOR_COMPILE=PASS"
python3 "$GEN" "$ROOT" "$OUT"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUT" | awk '{print $1}')"
