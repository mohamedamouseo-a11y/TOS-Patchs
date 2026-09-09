#!/usr/bin/env python3
import hashlib
import urllib.request

ORIGINAL_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSHEETS-PHASE-7-4-GOOGLE-WORKSPACE-FIDELITY/run_tsheets_phase7_4.py"
ORIGINAL_BLOB = "dc0a0241842c47dbba5e5a31b9a35378d6322b14"

CURRENT_ROOT = '<div className="tws-reference-ui tws-reference-sheets tws-sheets-phase7-premium tws-sheets-phase7-1-restructure tws-sheets-phase7-2-google-parity tws-sheets-phase7-2b-polish tws-sheets-phase7-2c-final tws-sheets-phase7-2d-dark-fidelity tws-sheets-phase7-2e-micro-final tws-sheets-phase7-3-google-menu relative flex h-full flex-col">'
PHASE74_ROOT = '<div className="tws-reference-ui tws-reference-sheets tws-sheets-phase7-premium tws-sheets-phase7-1-restructure tws-sheets-phase7-2-google-parity tws-sheets-phase7-2b-polish tws-sheets-phase7-2c-final tws-sheets-phase7-2d-dark-fidelity tws-sheets-phase7-2e-micro-final tws-sheets-phase7-3-google-menu tws-sheets-phase7-4-workspace-fidelity relative flex h-full flex-col">'
ORIGINAL_OLD_ROOT = '<div className="tws-reference-ui tws-reference-sheets flex h-full flex-col">'
ORIGINAL_NEW_ROOT = '<div className="tws-reference-ui tws-reference-sheets tws-sheets-phase7-4-workspace-fidelity flex h-full flex-col">'


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


request = urllib.request.Request(ORIGINAL_URL, headers={"User-Agent": "TOS-tsheets-phase7-4-r1"})
with urllib.request.urlopen(request, timeout=30) as response:
    data = response.read()

actual = git_blob_sha(data)
if actual != ORIGINAL_BLOB:
    raise SystemExit(f"ORIGINAL_RUNNER_INTEGRITY_FAIL:{actual}")

source = data.decode("utf-8")

if source.count(ORIGINAL_OLD_ROOT) != 1:
    raise SystemExit(f"ORIGINAL_OLD_ROOT_COUNT:{source.count(ORIGINAL_OLD_ROOT)}")
if source.count(ORIGINAL_NEW_ROOT) != 1:
    raise SystemExit(f"ORIGINAL_NEW_ROOT_COUNT:{source.count(ORIGINAL_NEW_ROOT)}")

source = source.replace(ORIGINAL_OLD_ROOT, CURRENT_ROOT, 1)
source = source.replace(ORIGINAL_NEW_ROOT, PHASE74_ROOT, 1)
source = source.replace(
    'PATCH = "TOS-TWS-TSHEETS-PHASE-7-4-GOOGLE-WORKSPACE-FIDELITY"',
    'PATCH = "TOS-TWS-TSHEETS-PHASE-7-4-R1-ROOT-ANCHOR-FIX"',
    1,
)
source = source.replace(
    'SCRIPT = "run_tsheets_phase7_4.py"',
    'SCRIPT = "run_tsheets_phase7_4_r1.py"',
    1,
)

compile(source, "run_tsheets_phase7_4_r1_transformed.py", "exec")
exec(compile(source, "run_tsheets_phase7_4_r1_transformed.py", "exec"), {"__name__": "__main__"})
