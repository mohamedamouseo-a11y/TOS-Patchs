#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
OUTPUT="${2:-/var/tmp/TOS_SLA_ADVANCED_PHASE4_TESTFIX.patch}"
GENERATOR_COMMIT="eac010014e777bc6e7ee6533a7087817d85b8a84"
GENERATOR_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/${GENERATOR_COMMIT}/TOS-SLA-ADVANCED-PHASE4-GIT-GENERATED/generate_sla_advanced_phase4_testfix.py"
TMP_GENERATOR="$(mktemp /var/tmp/tos-sla-advanced-phase4-testfix.XXXXXX.py)"
trap 'rm -f "$TMP_GENERATOR"' EXIT

curl -fsSL "$GENERATOR_URL" -o "$TMP_GENERATOR"
python3 "$TMP_GENERATOR" "$REPO" "$OUTPUT"
