#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
OUTPUT="${2:-/var/tmp/TOS_SLA_CENTER_PHASE3.patch}"
GENERATOR_COMMIT="54e2f17e6961149da70b83146e23c2200831ead5"
GENERATOR_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/${GENERATOR_COMMIT}/TOS-SLA-CENTER-PHASE3-GIT-GENERATED/generate_sla_center_phase3.py"
TMP_GENERATOR="$(mktemp /var/tmp/tos-sla-center-phase3-generator.XXXXXX.py)"
trap 'rm -f "$TMP_GENERATOR"' EXIT

curl -fsSL "$GENERATOR_URL" -o "$TMP_GENERATOR"
python3 "$TMP_GENERATOR" "$REPO" "$OUTPUT"
