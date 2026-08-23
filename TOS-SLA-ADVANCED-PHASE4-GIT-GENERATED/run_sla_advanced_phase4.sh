#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
OUTPUT="${2:-/var/tmp/TOS_SLA_ADVANCED_PHASE4.patch}"
GENERATOR_COMMIT="003a0154ee6b3d19bbcbe21a0324d29eb0dbf984"
GENERATOR_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/${GENERATOR_COMMIT}/TOS-SLA-ADVANCED-PHASE4-GIT-GENERATED/generate_sla_advanced_phase4.py"
TMP_GENERATOR="$(mktemp /var/tmp/tos-sla-advanced-phase4-generator.XXXXXX.py)"
trap 'rm -f "$TMP_GENERATOR"' EXIT

curl -fsSL "$GENERATOR_URL" -o "$TMP_GENERATOR"
python3 "$TMP_GENERATOR" "$REPO" "$OUTPUT"
