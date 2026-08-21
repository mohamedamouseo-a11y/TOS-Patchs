#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "313ef7da0da16a43b6eccc2bfc6b79bac8d369b4"
TARGET = "backend/src/routes/auditLog.routes.js"
EXPECTED_BLOB = "f8e6d87e20ef470ca773d1cd2267954c6aa00a02"

REPLACEMENTS = [
    (
        'import { sanitizeChatUser } from "../utils/sanitize.js";\n',
        ''
    ),
    (
'''function normalizeMetadata(metadata) {
  if (!metadata || typeof metadata !== "object") return metadata || null;
  return metadata;
}
''',
'''function normalizeMetadata(metadata) {
  if (!metadata || typeof metadata !== "object") return metadata || null;
  return metadata;
}

const AUDIT_USER_SELECT = { id: true, name: true, role: true };

function sanitizeAuditUser(user) {
  if (!user) return null;
  return { id: user.id, name: user.name, role: user.role };
}
'''
    ),
    (
        '    actor: sanitizeChatUser(actor),\n    target: sanitizeChatUser(target),',
        '    actor: sanitizeAuditUser(actor),\n    target: sanitizeAuditUser(target),'
    ),
    (
        '      include: { actor: true },',
        '      include: { actor: { select: AUDIT_USER_SELECT } },'
    ),
    (
        '      include: { actor: true, targetUser: true },',
        '      include: { actor: { select: AUDIT_USER_SELECT }, targetUser: { select: AUDIT_USER_SELECT } },'
    ),
    (
        '      include: { user: true },',
        '      include: { user: { select: AUDIT_USER_SELECT } },'
    ),
    (
        '      include: { user: true, task: { select: { projectId: true } } },',
        '      include: { user: { select: AUDIT_USER_SELECT }, task: { select: { projectId: true } } },'
    ),
]

EXPECTED_MATCH_COUNTS = [1, 1, 1, 1, 1, 1, 1]


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
        die("usage: generate_audit_log_payload_fix_v1.py REPO_ROOT OUTPUT_PATCH", 2)

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
        die("target has staged changes", 7)

    diff = run(["git", "diff", "--", TARGET], root).stdout
    if diff.strip():
        die("target has tracked local changes", 8)
    print("TARGET_CLEAN=YES")

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF source detected; explicit handling required", 9)
    had_terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    for index, ((old, new), expected_count) in enumerate(zip(REPLACEMENTS, EXPECTED_MATCH_COUNTS), start=1):
        count = text.count(old)
        print(f"REPLACEMENT_{index}_MATCHES={count}")
        if count != expected_count:
            die(f"replacement {index} expected {expected_count} exact match, found {count}", 20 + index)
        text = text.replace(old, new, expected_count)

    tmp = Path(tempfile.mkdtemp(prefix="tos-audit-payload-fix-v1-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "audit-fix@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Audit Payload Fix Generator"], tmp)

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

        run(["node", "--check", str(tmp_target)], tmp)
        print("NODE_CHECK=PASS")

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
        print("GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_SOURCE")
        print("AUDIT_LOG_PAYLOAD_FIX_V1_GENERATOR=PASS")
        print(f"TARGET_PATH={TARGET}")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
