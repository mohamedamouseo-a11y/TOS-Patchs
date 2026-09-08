#!/usr/bin/env python3
import urllib.request

RUNNER_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-AUDIT-LOG-V2-PHASE-5-AUDIT-CENTER-HARDENING-GIT-GENERATED/run_phase5.py"
OLD_CENTER_BLOB = "2ffcdcef91fefb0bdb700568fbc07a7f92f2a4ca"
NEW_CENTER_BLOB = "9bff6d40c8c5c8a684eb75453575d21a59ac969b"

with urllib.request.urlopen(RUNNER_URL, timeout=30) as response:
    source = response.read().decode("utf-8")

if source.count(OLD_CENTER_BLOB) != 1:
    raise SystemExit("PHASE_5_R1=FAIL: base runner center guard mismatch")

source = source.replace(OLD_CENTER_BLOB, NEW_CENTER_BLOB, 1)
exec(compile(source, "run_phase5_r1_inner.py", "exec"), {"__name__": "__main__"})
