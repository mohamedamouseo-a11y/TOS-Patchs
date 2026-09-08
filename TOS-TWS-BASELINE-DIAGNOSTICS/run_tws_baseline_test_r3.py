#!/usr/bin/env python3
import sys
import urllib.request

R2_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-BASELINE-DIAGNOSTICS/run_tws_baseline_test_r2.py"


def main():
    with urllib.request.urlopen(R2_URL, timeout=30) as response:
        source = response.read().decode("utf-8")

    replacements = {
        "TWS_BASELINE_TEST_R2": "TWS_BASELINE_TEST_R3",
        "tws-baseline-r2-": "tws-baseline-r3-",
        "assert.equal(v.C5, true);": "assert.equal(v.C5, 'TRUE');",
        "assert.equal(v.C6, true);": "assert.equal(v.C6, 'TRUE');",
        "assert.equal(v.H1, true);": "assert.equal(v.H1, 'TRUE');",
    }
    for old, new in replacements.items():
        if old not in source:
            raise RuntimeError(f"R3 source guard failed: missing expected R2 marker: {old}")
        source = source.replace(old, new)

    print("BOOLEAN_DISPLAY_CONTRACT=TRUE_FALSE_STRINGS")
    code = compile(source, R2_URL, "exec")
    exec(code, {"__name__": "__main__", "__file__": R2_URL})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("TWS_BASELINE_TEST_R3=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_UPDATE=NO")
        sys.exit(1)
