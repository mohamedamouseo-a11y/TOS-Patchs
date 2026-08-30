#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
OUT="${2:-/var/tmp/TOS_DASHBOARD_PREMIUM_UXUI_V1.patch}"
GEN="/var/tmp/generate_dashboard_premium_uxui_v1.py"

GEN_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/de6a41850b70dcaa120dff046291f9290ee93b6a/TOS-DASHBOARD-PREMIUM-UXUI-V1-GIT-GENERATED/generate_dashboard_premium_uxui_v1.py"

rm -f "$GEN" "$OUT"
curl -fL "$GEN_URL" -o "$GEN"
chmod 700 "$GEN"
python3 -m py_compile "$GEN"
echo "GENERATOR_COMPILE=PASS"
python3 "$GEN" "$ROOT" "$OUT"
echo "FINAL_PATCH_SHA256=$(sha256sum "$OUT" | awk '{print $1}')"
echo "PATCH_READY=$OUT"
echo "APPLY_COMMAND=git -C $ROOT apply $OUT"
