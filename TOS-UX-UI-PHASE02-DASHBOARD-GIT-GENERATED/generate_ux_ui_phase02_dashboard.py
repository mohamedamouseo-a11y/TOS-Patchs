#!/usr/bin/env python3
import base64, hashlib, json, shutil, subprocess, sys, tempfile, zlib
from pathlib import Path

TARGET_BASE_HEAD = "bd1df69a3034ba7c4875006ae01e1b857a66d1c8"
TARGET_FILE = "frontend/src/pages/Dashboard.jsx"
EXPECTED_BLOB = "400fbc244fe23a37cea9d2838a57793bcbe23372"
PAYLOAD = "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"

def run(args, cwd, check=True):
    r = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and r.returncode != 0:
        raise RuntimeError(f"Command failed ({r.returncode}): {' '.join(args)}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    return r

def replace_section(source, start_marker, end_marker, replacement, label):
    start = source.find(start_marker)
    if start < 0: raise RuntimeError(f"Missing {label} start marker")
    end = source.find(end_marker, start)
    if end < 0: raise RuntimeError(f"Missing {label} end marker")
    if source.find(start_marker, start + 1) >= 0: raise RuntimeError(f"Duplicate {label} start marker")
    return source[:start] + replacement + source[end:]

def transform(source):
    cfg = json.loads(zlib.decompress(base64.b64decode(PAYLOAD)).decode())
    source = replace_section(source, "function DateFilterBar(", "function roleLabel(", cfg["date_filter"], "DateFilterBar")
    source = replace_section(source, "function QuickAction(", "function ActivityTimeline(", cfg["quick_action"], "QuickAction")
    marker = '  return (\n    <div className="tos-page tos-dashboard-premium">'
    start = source.find(marker, source.find("export function Dashboard("))
    if start < 0: raise RuntimeError("Missing Dashboard return marker")
    if not source.rstrip().endswith("  );\n}"): raise RuntimeError("Unexpected Dashboard file ending")
    source = source[:start] + cfg["dashboard_return"] + "\n"
    preserved = [
        'onNavigate?.("projects:create")', 'onNavigate?.("files:upload")', 'onNavigate?.("team:invite")',
        'getDateRange(datePreset, customStart, customEnd, isEnglish)',
        'projects.filter((project) => inDateRange(project, activeRange))',
        'files.filter((file) => inDateRange(file, activeRange))',
        'clients.filter((client) => inDateRange(client, activeRange))', '<TwsRecentFilesWidget />'
    ]
    missing = [x for x in preserved if x not in source]
    if missing: raise RuntimeError(f"Behavior-preservation check failed; missing markers: {missing}")
    return source

def main():
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "/var/tmp/TOS_UX_UI_PHASE02_DASHBOARD.patch").resolve()
    branch = run(["git", "branch", "--show-current"], repo).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    if branch != "main": raise RuntimeError(f"Expected branch main, found {branch}")
    if head != TARGET_BASE_HEAD: raise RuntimeError(f"Expected HEAD {TARGET_BASE_HEAD}, found {head}")
    target = repo / TARGET_FILE
    if not target.is_file(): raise RuntimeError(f"Missing dashboard source target: {TARGET_FILE}")
    blob = run(["git", "hash-object", "--", TARGET_FILE], repo).stdout.strip()
    if blob != EXPECTED_BLOB: raise RuntimeError(f"Dashboard target drift: expected {EXPECTED_BLOB}, found {blob}")
    root = Path(tempfile.mkdtemp(prefix="tos-ui02-dashboard-")); wt = root / "worktree"
    try:
        run(["git", "worktree", "add", "--detach", str(wt), TARGET_BASE_HEAD], repo)
        p = wt / TARGET_FILE; original = p.read_text(); updated = transform(original)
        if updated == original: raise RuntimeError("Dashboard transform produced no change")
        p.write_text(updated)
        changed = run(["git", "diff", "--name-only"], wt).stdout.strip().splitlines()
        if changed != [TARGET_FILE]: raise RuntimeError(f"Unexpected UI-02 patch scope: {changed}")
        dc = run(["git", "diff", "--check"], wt, check=False)
        if dc.returncode != 0: raise RuntimeError(f"git diff --check failed:\n{dc.stdout}{dc.stderr}")
        patch = run(["git", "diff", "--binary", "--", TARGET_FILE], wt).stdout
        if not patch.strip() or patch.count("diff --git ") != 1: raise RuntimeError("Invalid generated UI-02 patch")
        output.parent.mkdir(parents=True, exist_ok=True); output.write_text(patch)
        ac = run(["git", "apply", "--check", str(output)], repo, check=False)
        if ac.returncode != 0: raise RuntimeError(f"git apply --check failed against production working tree:\n{ac.stderr}")
        print(f"PATCH={output}")
        print(f"SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")
        print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
        print(f"EXPECTED_DASHBOARD_BLOB={EXPECTED_BLOB}")
        print("PHASE=UI-02 DASHBOARD\nFRONTEND_ONLY=YES\nBACKEND_INCLUDED=NO\nFILES=\n" + TARGET_FILE)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        shutil.rmtree(root, ignore_errors=True)

if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr); raise SystemExit(1)
