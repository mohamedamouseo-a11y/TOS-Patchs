#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
OUTPUT="${2:-/var/tmp/TOS_SLA_CENTER_PHASE3.patch}"
GENERATOR_COMMIT="54e2f17e6961149da70b83146e23c2200831ead5"
GENERATOR_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/${GENERATOR_COMMIT}/TOS-SLA-CENTER-PHASE3-GIT-GENERATED/generate_sla_center_phase3.py"
TMP_GENERATOR="$(mktemp /var/tmp/tos-sla-center-phase3-generator.XXXXXX.py)"
trap 'rm -f "$TMP_GENERATOR"' EXIT

curl -fsSL "$GENERATOR_URL" -o "$TMP_GENERATOR"

# Phase 2 renamed the existing section comment while keeping the alerts router.
# Repair the pinned generator anchors deterministically before execution.
python3 - "$TMP_GENERATOR" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
old = "  // ---- Alerts ----\n  alerts: router({"
new = "  // ---- Operational Inbox / Alerts ----\n  alerts: router({"
count = source.count(old)
if count != 2:
    raise SystemExit(f"ERROR: expected exactly 2 Phase 3 alert anchors in pinned generator, found {count}")
path.write_text(source.replace(old, new))
PY

python3 "$TMP_GENERATOR" "$REPO" "$OUTPUT"
