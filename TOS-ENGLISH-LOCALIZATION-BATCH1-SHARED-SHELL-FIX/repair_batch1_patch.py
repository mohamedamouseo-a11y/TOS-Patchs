#!/usr/bin/env python3
import hashlib
import re
import sys
from pathlib import Path

HUNK_RE = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?( @@.*)$')
ALLOWED_PATHS = {
    'frontend/src/components/layout/Topbar.jsx',
    'frontend/src/components/RamzyAssistant.jsx',
}


def die(message, code=1):
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(code)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        die('usage: repair_batch1_patch.py INPUT.patch OUTPUT.patch', 2)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    if not src.is_file():
        die(f'input patch not found: {src}', 3)

    raw = src.read_bytes()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        die(f'patch is not utf-8: {exc}', 4)

    print(f'INPUT_SHA256={sha256(raw)}')
    print(f'INPUT_TERMINAL_NEWLINE={"YES" if raw.endswith(bytes([10])) else "NO"}')

    lines = text.splitlines()
    touched = set()
    for line in lines:
        if line.startswith('diff --git a/'):
            parts = line.split()
            if len(parts) != 4:
                die(f'invalid diff header: {line}', 5)
            a_path = parts[2][2:]
            b_path = parts[3][2:]
            if a_path != b_path:
                die(f'path rename not allowed: {a_path} -> {b_path}', 6)
            touched.add(a_path)

    if touched != ALLOWED_PATHS:
        die(f'unexpected target paths: {sorted(touched)}', 7)

    repaired = list(lines)
    hunk_count = 0
    header_repairs = 0
    i = 0
    while i < len(lines):
        match = HUNK_RE.match(lines[i])
        if not match:
            i += 1
            continue

        hunk_count += 1
        old_start = int(match.group(1))
        old_declared = int(match.group(2) or '1')
        new_start = int(match.group(3))
        new_declared = int(match.group(4) or '1')
        suffix = match.group(5)
        old_actual = 0
        new_actual = 0
        j = i + 1

        while j < len(lines):
            line = lines[j]
            if line.startswith('@@ ') or line.startswith('diff --git '):
                break
            if line.startswith(' '):
                old_actual += 1
                new_actual += 1
            elif line.startswith('-') and not line.startswith('--- '):
                old_actual += 1
            elif line.startswith('+') and not line.startswith('+++ '):
                new_actual += 1
            elif line == r'\ No newline at end of file':
                pass
            else:
                die(f'invalid hunk body line {j + 1}: {line!r}', 8)
            j += 1

        before = lines[i]
        after = f'@@ -{old_start},{old_actual} +{new_start},{new_actual}{suffix}'
        if old_declared != old_actual or new_declared != new_actual:
            repaired[i] = after
            header_repairs += 1
            print(f'HUNK_REPAIRED line={i + 1} BEFORE={before}')
            print(f'HUNK_REPAIRED line={i + 1} AFTER={after}')
        else:
            print(f'HUNK_OK line={i + 1} old={old_actual} new={new_actual}')
        i = j

    if hunk_count == 0:
        die('no hunks found', 9)

    output_text = '\n'.join(repaired) + '\n'
    output = output_text.encode('utf-8')
    dst.write_bytes(output)

    # Independent structure validation of the repaired output.
    check = output_text.splitlines()
    validated = 0
    i = 0
    while i < len(check):
        match = HUNK_RE.match(check[i])
        if not match:
            i += 1
            continue
        validated += 1
        old_expected = int(match.group(2) or '1')
        new_expected = int(match.group(4) or '1')
        old_actual = new_actual = 0
        j = i + 1
        while j < len(check):
            line = check[j]
            if line.startswith('@@ ') or line.startswith('diff --git '):
                break
            if line.startswith(' '):
                old_actual += 1
                new_actual += 1
            elif line.startswith('-') and not line.startswith('--- '):
                old_actual += 1
            elif line.startswith('+') and not line.startswith('+++ '):
                new_actual += 1
            elif line == r'\ No newline at end of file':
                pass
            else:
                die(f'output contains invalid hunk body line {j + 1}: {line!r}', 10)
            j += 1
        if old_expected != old_actual or new_expected != new_actual:
            die(f'self-check mismatch hunk line {i + 1}: old {old_expected}!={old_actual}, new {new_expected}!={new_actual}', 11)
        i = j

    if validated != hunk_count:
        die(f'hunk count changed during repair: {hunk_count}->{validated}', 12)
    if not output.endswith(b'\n'):
        die('output terminal newline missing', 13)

    print(f'TARGET_PATHS={";".join(sorted(touched))}')
    print(f'HUNKS={validated}')
    print(f'HEADER_REPAIRS={header_repairs}')
    print('TERMINAL_NEWLINE=PASS')
    print('UNIFIED_DIFF_STRUCTURE=PASS')
    print(f'OUTPUT_SHA256={sha256(output)}')
    print(f'OUTPUT={dst}')


if __name__ == '__main__':
    main()
