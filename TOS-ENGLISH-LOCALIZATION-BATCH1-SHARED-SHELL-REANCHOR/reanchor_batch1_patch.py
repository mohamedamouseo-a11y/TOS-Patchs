#!/usr/bin/env python3
import hashlib, re, subprocess, sys
from pathlib import Path

ALLOWED = {
    'frontend/src/components/layout/Topbar.jsx': 'f40cdcfb52a4639215e0d4686ecae8aa43324e1c10545145867c2b857e478b39',
    'frontend/src/components/RamzyAssistant.jsx': '75487157f35126f99f643b213686327fa8fce1a15cb5a0b57c6a79a1273f8d2d',
}
HUNK = re.compile(r'^@@ -(\d+),(\d+) \+(\d+),(\d+)( @@.*)$')

def die(msg, code=1):
    print('ERROR:', msg, file=sys.stderr); raise SystemExit(code)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def find_unique(haystack, needle, label):
    if not needle: die(f'{label}: empty old hunk sequence', 10)
    hits=[]; n=len(needle)
    for i in range(0, len(haystack)-n+1):
        if haystack[i:i+n] == needle: hits.append(i)
    if len(hits) != 1: die(f'{label}: expected unique exact live match, found {len(hits)}', 11)
    return hits[0]

def main():
    if len(sys.argv) != 4: die('usage: reanchor_batch1_patch.py REPO_ROOT INPUT.patch OUTPUT.patch', 2)
    root=Path(sys.argv[1]).resolve(); src=Path(sys.argv[2]).resolve(); dst=Path(sys.argv[3]).resolve()
    if not (root/'.git').exists(): die(f'not a git repo: {root}', 3)
    if not src.is_file(): die(f'patch missing: {src}', 4)

    live={}
    for rel, expected in ALLOWED.items():
        p=root/rel
        if not p.is_file(): die(f'target missing: {rel}', 5)
        actual=sha(p); print(f'SOURCE_SHA {rel} {actual}')
        if actual != expected: die(f'{rel}: SHA mismatch expected={expected} actual={actual}', 6)
        live[rel]=p.read_text(encoding='utf-8').splitlines()

    lines=src.read_text(encoding='utf-8').splitlines()
    out=[]; current=None; delta=0; seen=set(); i=0; hunks=0
    while i < len(lines):
        line=lines[i]
        if line.startswith('diff --git a/'):
            parts=line.split()
            if len(parts)!=4: die(f'bad diff header line {i+1}', 7)
            a=parts[2][2:]; b=parts[3][2:]
            if a!=b or a not in ALLOWED: die(f'unexpected path at line {i+1}: {a} -> {b}', 8)
            current=a; delta=0; seen.add(a); out.append(line); i+=1; continue
        m=HUNK.match(line)
        if not m:
            out.append(line); i+=1; continue
        if not current: die(f'hunk before file header at line {i+1}', 9)
        hunks+=1
        old_count=int(m.group(2)); new_count=int(m.group(4)); suffix=m.group(5)
        body=[]; j=i+1
        while j < len(lines) and not lines[j].startswith('@@ ') and not lines[j].startswith('diff --git '):
            body.append(lines[j]); j+=1
        old_seq=[x[1:] for x in body if x.startswith(' ') or (x.startswith('-') and not x.startswith('--- '))]
        pos=find_unique(live[current], old_seq, f'{current} hunk@{i+1}')
        old_start=pos+1; new_start=old_start+delta
        actual_old=sum(1 for x in body if x.startswith(' ') or (x.startswith('-') and not x.startswith('--- ')))
        actual_new=sum(1 for x in body if x.startswith(' ') or (x.startswith('+') and not x.startswith('+++ ')))
        if (actual_old,actual_new)!=(old_count,new_count): die(f'count mismatch at line {i+1}', 12)
        before=line; after=f'@@ -{old_start},{old_count} +{new_start},{new_count}{suffix}'
        print(f'REANCHOR {current}: {before} -> {after}')
        out.append(after); out.extend(body)
        delta += new_count-old_count
        i=j

    if seen != set(ALLOWED): die(f'patch targets mismatch: {sorted(seen)}', 13)
    if hunks == 0: die('no hunks found', 14)
    dst.write_text('\n'.join(out)+'\n', encoding='utf-8', newline='\n')
    print(f'HUNKS={hunks}'); print(f'OUTPUT_SHA256={sha(dst)}'); print('TERMINAL_NEWLINE=PASS')

    for args, label in [(['git','apply','--numstat',str(dst)],'PARSER'), (['git','apply','--check',str(dst)],'APPLY_CHECK')]:
        r=subprocess.run(args,cwd=root,text=True,capture_output=True)
        if r.stdout: print(r.stdout,end='')
        if r.stderr: print(r.stderr,end='',file=sys.stderr)
        if r.returncode: die(f'{label}=FAIL rc={r.returncode}', 20)
        print(f'{label}=PASS')
    print('REANCHOR=PASS')

if __name__ == '__main__': main()
