#!/usr/bin/env python3
import base64
import sys
import urllib.request
import zlib

URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-4-FORMULA-ENGINE-EXPANSION/run_phase4_payload.b64"

try:
    payload = urllib.request.urlopen(URL, timeout=30).read().decode("utf-8").strip()
    source = zlib.decompress(base64.b64decode(payload)).decode("utf-8")
    exec(compile(source, "run_phase4_effective.py", "exec"), {"__name__": "__main__"})
except SystemExit:
    raise
except Exception as exc:
    print("PHASE_4_LAUNCHER=FAIL")
    print(f"ERROR={exc}")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)
