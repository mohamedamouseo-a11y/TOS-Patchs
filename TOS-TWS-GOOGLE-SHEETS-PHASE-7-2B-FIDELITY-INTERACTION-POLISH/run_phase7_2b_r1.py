#!/usr/bin/env python3
import urllib.request

URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2B-FIDELITY-INTERACTION-POLISH/run_phase7_2b.py"
source = urllib.request.urlopen(URL, timeout=45).read().decode("utf-8")
old = "result, count = re.subn(pattern, replacement, source, count=1, flags=re.S)"
new = "result, count = re.subn(pattern, lambda _match: replacement, source, count=1, flags=re.S)"
if source.count(old) != 1:
    raise SystemExit("R1 integrity guard failed: regex_once anchor mismatch")
source = source.replace(old, new, 1)
compile(source, "run_phase7_2b_r1_inner.py", "exec")
exec(compile(source, "run_phase7_2b_r1_inner.py", "exec"), {"__name__": "__main__"})
