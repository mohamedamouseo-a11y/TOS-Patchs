#!/usr/bin/env python3
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = '2e3009a1fb3794cee3c7339ba8f8edc36b4b6b2c'
EXPECTED_SHA256 = {
    'frontend/src/components/layout/Topbar.jsx': 'f40cdcfb52a4639215e0d4686ecae8aa43324e1c10545145867c2b857e478b39',
    'frontend/src/components/RamzyAssistant.jsx': '75487157f35126f99f643b213686327fa8fce1a15cb5a0b57c6a79a1273f8d2d',
}
ALLOWED = set(EXPECTED_SHA256)
HUNK_RE = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?( @@.*)$')


def die(message, code=1):
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end='')
    if proc.stderr:
        print(proc.stderr, end='', file=sys.stderr)
    if check and proc.returncode:
        die(f'command failed rc={proc.returncode}: {" ".join(args)}', 90)
    return proc


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_patch(path: Path):
    lines = path.read_text(encoding='utf-8').splitlines()
    current = None
    per_file = {rel: [] for rel in ALLOWED}
    seen = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('diff --git a/'):
            parts = line.split()
            if len(parts) != 4:
                die(f'bad diff header line {i+1}', 10)
            a = parts[2][2:]
            b = parts[3][2:]
            if a != b or a not in ALLOWED:
                die(f'unexpected path line {i+1}: {a} -> {b}', 11)
            current = a
            seen.add(a)
            i += 1
            continue
        m = HUNK_RE.match(line)
        if not m:
            i += 1
            continue
        if not current:
            die(f'hunk before file header at line {i+1}', 12)
        body = []
        j = i + 1
        while j < len(lines) and not lines[j].startswith('@@ ') and not lines[j].startswith('diff --git '):
            body.append(lines[j])
            j += 1
        old_seq = []
        new_seq = []
        for body_line in body:
            if body_line.startswith(' '):
                old_seq.append(body_line[1:])
                new_seq.append(body_line[1:])
            elif body_line.startswith('-') and not body_line.startswith('--- '):
                old_seq.append(body_line[1:])
            elif body_line.startswith('+') and not body_line.startswith('+++ '):
                new_seq.append(body_line[1:])
            elif body_line == r'\ No newline at end of file':
                pass
            else:
                die(f'invalid hunk body line {j+1}: {body_line!r}', 13)
        if not old_seq:
            die(f'empty old sequence for {current} hunk line {i+1}', 14)
        per_file[current].append((i + 1, old_seq, new_seq))
        i = j
    if seen != ALLOWED:
        die(f'patch targets mismatch: {sorted(seen)}', 15)
    return per_file


def replace_unique(lines, old_seq, new_seq, label):
    n = len(old_seq)
    hits = [idx for idx in range(0, len(lines)-n+1) if lines[idx:idx+n] == old_seq]
    if len(hits) != 1:
        die(f'{label}: expected one exact match, found {len(hits)}', 20)
    idx = hits[0]
    return lines[:idx] + new_seq + lines[idx+n:], idx + 1


def main():
    if len(sys.argv) != 4:
        die('usage: generate_batch1_from_live.py REPO_ROOT STRUCTURED_PATCH OUTPUT_PATCH', 2)

    root = Path(sys.argv[1]).resolve()
    structured = Path(sys.argv[2]).resolve()
    output_patch = Path(sys.argv[3]).resolve()

    if not (root / '.git').is_dir():
        die(f'not a git repo: {root}', 3)
    if not structured.is_file():
        die(f'structured patch missing: {structured}', 4)

    head = run(['git', 'rev-parse', 'HEAD'], root).stdout.strip()
    print(f'HEAD={head}')
    if head != EXPECTED_HEAD:
        die(f'HEAD mismatch expected={EXPECTED_HEAD} actual={head}', 5)

    for rel, expected in EXPECTED_SHA256.items():
        path = root / rel
        if not path.is_file():
            die(f'target missing: {rel}', 6)
        actual = sha256(path)
        print(f'SOURCE_SHA256 {rel} {actual}')
        if actual != expected:
            die(f'{rel}: SHA mismatch expected={expected} actual={actual}', 7)
        diff = run(['git', 'diff', '--', rel], root).stdout
        if diff.strip():
            die(f'{rel}: target has tracked modifications', 8)

    transforms = parse_patch(structured)
    total_hunks = sum(len(v) for v in transforms.values())
    print(f'INPUT_HUNKS={total_hunks}')

    tmp = Path(tempfile.mkdtemp(prefix='tos-batch1-git-generated-'))
    try:
        run(['git', 'init', '-q'], tmp)
        run(['git', 'config', 'user.email', 'batch1@tos.local'], tmp)
        run(['git', 'config', 'user.name', 'TOS Batch1 Generator'], tmp)

        for rel in sorted(ALLOWED):
            src = root / rel
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

        run(['git', 'add', '--'] + sorted(ALLOWED), tmp)
        run(['git', 'commit', '-qm', 'exact live baseline'], tmp)

        for rel in sorted(ALLOWED):
            target = tmp / rel
            raw = target.read_bytes()
            if b'\r\n' in raw:
                die(f'{rel}: CRLF not supported by generator; stop for explicit handling', 30)
            had_terminal_newline = raw.endswith(b'\n')
            lines = raw.decode('utf-8').splitlines()
            for hunk_line, old_seq, new_seq in transforms[rel]:
                lines, matched_line = replace_unique(lines, old_seq, new_seq, f'{rel} source-hunk-{hunk_line}')
                print(f'EXACT_REPLACE {rel} patch_hunk_line={hunk_line} live_line={matched_line} old={len(old_seq)} new={len(new_seq)}')
            text = '\n'.join(lines) + ('\n' if had_terminal_newline else '')
            target.write_text(text, encoding='utf-8', newline='\n')

        diff_proc = subprocess.run(
            ['git', 'diff', '--binary', '--full-index', '--'] + sorted(ALLOWED),
            cwd=tmp,
            text=True,
            capture_output=True,
        )
        if diff_proc.returncode:
            if diff_proc.stderr:
                print(diff_proc.stderr, end='', file=sys.stderr)
            die(f'git diff failed rc={diff_proc.returncode}', 31)
        patch_text = diff_proc.stdout
        if not patch_text.strip():
            die('generated patch is empty', 32)
        output_patch.write_text(patch_text, encoding='utf-8', newline='\n')
        print(f'GENERATED_PATCH_SHA256={sha256(output_patch)}')

        names = run(['git', 'apply', '--numstat', str(output_patch)], root).stdout.strip().splitlines()
        parsed_paths = {row.split('\t')[-1] for row in names if row.strip()}
        if parsed_paths != ALLOWED:
            die(f'generated patch parsed paths mismatch: {sorted(parsed_paths)}', 33)
        print('PARSER=PASS')

        run(['git', 'apply', '--check', str(output_patch)], root)
        print('APPLY_CHECK=PASS')

        print(f'TARGET_PATHS={";".join(sorted(ALLOWED))}')
        print(f'HUNKS_FROM_SPEC={total_hunks}')
        print('GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_SOURCE')
        print('GIT_GENERATED_PATCH=PASS')
        print(f'OUTPUT={output_patch}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
