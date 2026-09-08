#!/usr/bin/env python3
import base64
import hashlib
import sys
import urllib.request
import zlib

URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-4-FORMULA-ENGINE-EXPANSION/run_phase4_payload.b64"

try:
    raw = urllib.request.urlopen(URL, timeout=30).read().decode("utf-8")
    payload = "".join(raw.split())
    if not payload:
        raise RuntimeError("Phase 4 payload is empty")

    remainder = len(payload) % 4
    padding = (4 - remainder) % 4
    padded = payload + ("=" * padding)

    print("PHASE_4_R1_BASE64_REPAIR=APPLIED")
    print(f"PHASE_4_PAYLOAD_LENGTH={len(payload)}")
    print(f"PHASE_4_PAYLOAD_MOD4={remainder}")
    print(f"PHASE_4_PADDING_ADDED={padding}")
    print(f"PHASE_4_PAYLOAD_SHA256={hashlib.sha256(payload.encode('ascii')).hexdigest()}")

    compressed = base64.b64decode(padded, validate=True)
    source = zlib.decompress(compressed).decode("utf-8")
    if "TOS-TWS-GOOGLE-SHEETS-PHASE-4-FORMULA-ENGINE-EXPANSION" not in source:
        raise RuntimeError("decoded payload does not identify the expected Phase 4 patch")

    print("PHASE_4_PAYLOAD_DECODE=PASS")
    exec(compile(source, "run_phase4_r1_effective.py", "exec"), {"__name__": "__main__"})
except SystemExit:
    raise
except Exception as exc:
    print("PHASE_4_R1_RUN=FAIL")
    print(f"ERROR={exc}")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)
