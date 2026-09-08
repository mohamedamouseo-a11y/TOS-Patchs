#!/usr/bin/env python3
import sys
import urllib.request

URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-2-GRID-UX-FOUNDATION/run_phase2.py"
OLD = '"frontend/src/pages/tws/sheetFormula.js": "a2848117c24c2b9ff3e3a4d18c93ab774df6d172"'
NEW = '"frontend/src/pages/tws/sheetFormula.js": "537dadaf87a23c01465d1507d6f990a3e998db02"'

try:
    source = urllib.request.urlopen(URL, timeout=30).read().decode("utf-8")
    if source.count(OLD) != 1:
        raise RuntimeError("Phase 2 base runner baseline correction target missing")
    source = source.replace(OLD, NEW, 1)
    print("PHASE_2_R1_BASELINE_CORRECTION=APPLIED")
    exec(compile(source, "run_phase2_r1_effective.py", "exec"), {"__name__": "__main__"})
except SystemExit:
    raise
except Exception as exc:
    print("PHASE_2_R1_RUN=FAIL")
    print(f"ERROR={exc}")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)
