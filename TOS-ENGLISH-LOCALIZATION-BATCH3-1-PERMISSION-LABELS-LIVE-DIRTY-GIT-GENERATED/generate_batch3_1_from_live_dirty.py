#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "a70c072e30deb87b23f3c81f81f5bc28d86447e2"
TARGET = "frontend/src/pages/PermissionsPage.jsx"
EXPECTED_BLOB = "c1c8a1471781b120762ceaec4383e59b0361c6aa"

REPLACEMENTS = [
    (
'''const ROLE_LABELS_EN = {
  SUPER_ADMIN: "System Admin",
  ADMIN: "Admin",
  MANAGER: "Team Lead",
  PROJECT_MANAGER: "Project Manager",
  TEAM_MEMBER: "Team Member",
};''',
'''const ROLE_LABELS_EN = {
  SUPER_ADMIN: "System Admin",
  ADMIN: "Admin",
  MANAGER: "Team Lead",
  PROJECT_MANAGER: "Project Manager",
  TEAM_MEMBER: "Team Member",
};

const PERMISSION_LABELS_EN = {
  "إدارة العملاء": "Manage clients",
  "إدارة المستخدمين": "Manage users",
  "استخدام الشات الداخلي": "Use internal chat",
  "رفع الملفات": "Upload files",
  "إدارة المشاريع": "Manage projects",
  "إنشاء المشاريع": "Create projects",
  "مشاهدة المشاريع": "View projects",
  "مشاهدة التقارير": "View reports",
  "إدارة Boards": "Manage Boards",
  "إدارة Workspaces": "Manage Workspaces",
  "إدارة المهام": "Manage tasks",
  "توزيع طلبات التصميم": "Assign design requests",
  "إدارة TWS": "Manage TWS",
};

function permissionUiLabel(permission, isEnglish) {
  const raw = permission?.label || permission?.key || "";
  return isEnglish ? (PERMISSION_LABELS_EN[raw] || raw) : raw;
}'''
    ),
    (
'''  const filteredPermissions = permissions.filter((permission) => {
    const haystack = `${permission.label || ""} ${permission.key || ""}`.toLowerCase();
    return haystack.includes(String(query || "").trim().toLowerCase());
  });''',
'''  const filteredPermissions = permissions.filter((permission) => {
    const localizedLabel = permissionUiLabel(permission, isEnglish);
    const haystack = `${localizedLabel} ${permission.label || ""} ${permission.key || ""}`.toLowerCase();
    return haystack.includes(String(query || "").trim().toLowerCase());
  });'''
    ),
    (
'''                  <div className="font-black text-slate-950 dark:text-white">{permission.label || permission.key}</div>''',
'''                  <div className="font-black text-slate-950 dark:text-white">{permissionUiLabel(permission, isEnglish)}</div>'''
    ),
]


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if check and proc.returncode:
        die(f"command failed rc={proc.returncode}: {' '.join(args)}", 90)
    return proc


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 3:
        die("usage: generate_batch3_1_from_live_dirty.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET

    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)
    if not target.is_file():
        die(f"target missing: {TARGET}", 4)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 5)

    blob = run(["git", "hash-object", TARGET], root).stdout.strip()
    print(f"SOURCE_BLOB={blob}")
    if blob != EXPECTED_BLOB:
        die(f"blob mismatch expected={EXPECTED_BLOB} actual={blob}", 6)

    staged = run(["git", "diff", "--cached", "--", TARGET], root).stdout
    if staged.strip():
        die("target has staged changes; not allowed", 7)
    print("TARGET_STAGED=NO")

    worktree_diff = run(["git", "diff", "--", TARGET], root).stdout
    print(f"TARGET_TRACKED_DIRTY={'YES' if worktree_diff.strip() else 'NO'}")
    print("TARGET_STATE_POLICY=EXACT_BLOB_ALLOWED_EVEN_IF_TRACKED_DIRTY")

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF source detected; explicit handling required", 8)
    had_terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    for index, (old, new) in enumerate(REPLACEMENTS, start=1):
        count = text.count(old)
        print(f"REPLACEMENT_{index}_MATCHES={count}")
        if count != 1:
            die(f"replacement {index} expected one exact match, found {count}", 20 + index)
        text = text.replace(old, new, 1)

    tmp = Path(tempfile.mkdtemp(prefix="tos-batch3-1-live-dirty-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "batch3-1@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Batch 3.1 Generator"], tmp)

        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)

        encoded = text.encode("utf-8")
        if had_terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not had_terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        proc = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", TARGET],
            cwd=tmp,
            text=True,
            capture_output=True,
        )
        if proc.returncode:
            if proc.stderr:
                print(proc.stderr, end="", file=sys.stderr)
            die(f"git diff failed rc={proc.returncode}", 40)
        if not proc.stdout.strip():
            die("generated patch is empty", 41)

        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if parsed_paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 42)
        print("PARSER=PASS")

        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_WORKTREE_SOURCE")
        print("BATCH3_1_GENERATOR=PASS")
        print(f"TARGET_PATH={TARGET}")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
