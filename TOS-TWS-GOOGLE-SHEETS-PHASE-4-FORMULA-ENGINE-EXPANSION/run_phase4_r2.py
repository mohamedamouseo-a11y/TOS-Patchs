#!/usr/bin/env python3
import base64
import hashlib
import sys
import urllib.request
import zlib

BASE = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-4-FORMULA-ENGINE-EXPANSION/r2"
PARTS = [
    ("payload.part01", "1190560dadbb510864ba19ac8d85b0a13ff5a9557bd1bc3159e124d5d04ff212"),
    ("payload.part02", "82e7eabc30bfa7750e131a0a52949e9dd2c43d082d2786403b360fdf02af3920"),
    ("payload.part03", "43e713b63547109d6ef28181afdf09c265fde0ee85a06987197f70ec3a379930"),
    ("payload.part04", "8d5a09e5b911e2a69c0ca4e8c9e122efc3cbd4e2ca45bdced33f1b6cead49180"),
    ("payload.part05", "bfe65e17f5fa80b5e0892450d7bb795356834147d125f1f923af5bd33a54e843"),
]
B64_SHA = "72e4b965dbac9137ac1ec319016f363e581ea356de0ff1cae8c05e8ecdafc2a4"
PACKED_SHA = "f793e2ba1bff8291301353e6b7b39b6b2b76917443ec27ac2e54b314764ab2e1"
SOURCE_SHA = "146105a98e7db5857bfa0898fb9583a9a6a9062add050331db33c51d0166f042"

try:
    chunks = []
    for name, expected in PARTS:
        data = urllib.request.urlopen(f"{BASE}/{name}", timeout=30).read()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise RuntimeError(f"{name} SHA256 mismatch: {actual} != {expected}")
        chunks.append(data)

    payload = b"".join(chunks)
    actual_b64_sha = hashlib.sha256(payload).hexdigest()
    if actual_b64_sha != B64_SHA:
        raise RuntimeError(f"joined payload SHA256 mismatch: {actual_b64_sha} != {B64_SHA}")

    compressed = base64.b64decode(payload, validate=True)
    actual_packed_sha = hashlib.sha256(compressed).hexdigest()
    if actual_packed_sha != PACKED_SHA:
        raise RuntimeError(f"compressed payload SHA256 mismatch: {actual_packed_sha} != {PACKED_SHA}")

    source_bytes = zlib.decompress(compressed)
    actual_source_sha = hashlib.sha256(source_bytes).hexdigest()
    if actual_source_sha != SOURCE_SHA:
        raise RuntimeError(f"source SHA256 mismatch: {actual_source_sha} != {SOURCE_SHA}")

    source = source_bytes.decode("utf-8")
    if "TOS-TWS-GOOGLE-SHEETS-PHASE-4-FORMULA-ENGINE-EXPANSION" not in source:
        raise RuntimeError("unexpected Phase 4 source")

    compiled = compile(source, "run_phase4_r2_effective.py", "exec")
    print("PHASE_4_R2_PARTS_INTEGRITY=PASS")
    print("PHASE_4_R2_ZLIB_INTEGRITY=PASS")
    print(f"PHASE_4_R2_SOURCE_SHA256={SOURCE_SHA}")
    exec(compiled, {"__name__": "__main__"})
except SystemExit:
    raise
except Exception as exc:
    print("PHASE_4_R2_RUN=FAIL")
    print(f"ERROR={exc}")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)
