#!/usr/bin/env python3
import urllib.request

URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-2B-FIDELITY-INTERACTION-POLISH/run_phase7_2b.py"
source = urllib.request.urlopen(URL, timeout=45).read().decode("utf-8")

patches = [
    (
        'SCRIPT = "run_phase7_2b.py"',
        'SCRIPT = "run_phase7_2b_r2.py"',
        "script label",
    ),
    (
        'result, count = re.subn(pattern, replacement, source, count=1, flags=re.S)',
        'result, count = re.subn(pattern, lambda _match: replacement, source, count=1, flags=re.S)',
        "regex replacement safety",
    ),
    (
        '''    current_dirty = changed_paths()\n    if current_dirty != PHASE72A_DIRTY:\n        raise RuntimeError("Phase 7.2A worktree state mismatch: " + ", ".join(sorted(current_dirty)))\n''',
        '''    current_dirty = changed_paths()\n    if not PHASE72A_DIRTY.issubset(current_dirty):\n        missing = PHASE72A_DIRTY - current_dirty\n        raise RuntimeError("Phase 7.2A worktree state is missing required paths: " + ", ".join(sorted(missing)))\n\n    unrelated_dirty = current_dirty - PHASE72A_DIRTY\n\n    def _r2_fingerprint(rel):\n        target = REPO / rel\n        if not target.exists():\n            return "MISSING"\n        if target.is_file():\n            return "FILE:" + sha256(target)\n        parts = []\n        for child in sorted(p for p in target.rglob("*") if p.is_file()):\n            parts.append(f"{child.relative_to(target)}:{sha256(child)}")\n        return "DIR:" + hashlib.sha256("\\n".join(parts).encode()).hexdigest()\n\n    unrelated_fingerprints = {path: _r2_fingerprint(path) for path in unrelated_dirty}\n''',
        "allow unrelated dirty state",
    ),
    (
        '''    if changed_paths() != FINAL_SCOPE:\n        raise RuntimeError("unexpected final changed paths: " + ", ".join(sorted(changed_paths())))\n''',
        '''    for path, fp in unrelated_fingerprints.items():\n        if _r2_fingerprint(path) != fp:\n            raise RuntimeError(f"pre-existing unrelated dirty path changed: {path}")\n\n    final_paths = changed_paths()\n    expected_final = FINAL_SCOPE | unrelated_dirty\n    if final_paths != expected_final:\n        raise RuntimeError("unexpected final changed paths: " + ", ".join(sorted(final_paths)))\n''',
        "preserve unrelated dirty state",
    ),
]

for old, new, label in patches:
    if source.count(old) != 1:
        raise SystemExit(f"R2 integrity guard failed: {label} anchor count={source.count(old)}")
    source = source.replace(old, new, 1)

compile(source, "run_phase7_2b_r2_inner.py", "exec")
exec(compile(source, "run_phase7_2b_r2_inner.py", "exec"), {"__name__": "__main__"})
