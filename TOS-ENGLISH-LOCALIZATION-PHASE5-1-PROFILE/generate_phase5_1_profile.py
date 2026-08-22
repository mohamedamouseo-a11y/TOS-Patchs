#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "1b5523316004b2113e8ae3e46b621bd3268b69bf"
TARGET = "frontend/src/pages/ProfilePage.jsx"
EXPECTED_BLOB = "de4ba7ffd9375ef5c0747391dba90c176bdade8d"

REPLACEMENTS = [
    (
        'import { getErrorMessage } from "../lib/errors";\n',
        'import { getErrorMessage } from "../lib/errors";\nimport { usePreferences } from "../contexts/PreferencesContext";\n',
        1,
    ),
    (
        '''const ROLE_LABELS = {\n  SUPER_ADMIN: "مدير النظام",\n  ADMIN: "مدير",\n  MANAGER: "قائد فريق",\n  PROJECT_MANAGER: "مدير مشروع",\n  TEAM_MEMBER: "عضو فريق",\n};''',
        '''const ROLE_LABELS_AR = {\n  SUPER_ADMIN: "مدير النظام",\n  ADMIN: "مدير",\n  MANAGER: "قائد فريق",\n  PROJECT_MANAGER: "مدير مشروع",\n  TEAM_MEMBER: "عضو فريق",\n};\n\nconst ROLE_LABELS_EN = {\n  SUPER_ADMIN: "System Admin",\n  ADMIN: "Admin",\n  MANAGER: "Team Lead",\n  PROJECT_MANAGER: "Project Manager",\n  TEAM_MEMBER: "Team Member",\n};\n\nfunction profileRoleLabel(role, isAr) {\n  const labels = isAr ? ROLE_LABELS_AR : ROLE_LABELS_EN;\n  return labels[role] || role || "—";\n}''',
        1,
    ),
    (
        'export function ProfilePage({ user }) {\n  const canViewAllProfiles = ["SUPER_ADMIN", "ADMIN"].includes(user.role);',
        'export function ProfilePage({ user }) {\n  const { isAr } = usePreferences();\n  const canViewAllProfiles = ["SUPER_ADMIN", "ADMIN"].includes(user.role);',
        1,
    ),
    (
        '        eyebrow="مركز الحساب"\n        title="الملف الشخصي"\n        description="واجهة موحدة لإدارة بيانات العضو، وسائل التواصل، ملاحظات العمل، نشاط الشهر، والمشاريع المرتبطة."',
        '        eyebrow={isAr ? "مركز الحساب" : "Account Center"}\n        title={isAr ? "الملف الشخصي" : "Profile"}\n        description={isAr ? "واجهة موحدة لإدارة بيانات العضو، وسائل التواصل، ملاحظات العمل، نشاط الشهر، والمشاريع المرتبطة." : "A unified workspace for member details, contact methods, work notes, monthly activity, and linked projects."}',
        1,
    ),
    (
        '{profileList.map((item) => <option key={item.id} value={item.id}>{item.name} — {ROLE_LABELS[item.role] || item.role}</option>)}',
        '{profileList.map((item) => <option key={item.id} value={item.id}>{item.name} — {profileRoleLabel(item.role, isAr)}</option>)}',
        1,
    ),
    (
        '<SystemCard className="text-sm font-bold text-zinc-500">جاري تحميل الملف الشخصي...</SystemCard>',
        '<SystemCard className="text-sm font-bold text-zinc-500">{isAr ? "جاري تحميل الملف الشخصي..." : "Loading profile..."}</SystemCard>',
        1,
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
        die("usage: generate_phase5_1_profile.py REPO_ROOT OUTPUT_PATCH", 2)

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

    if run(["git", "diff", "--cached", "--", TARGET], root).stdout.strip():
        die("target has staged changes", 7)
    if run(["git", "diff", "--", TARGET], root).stdout.strip():
        die("target has tracked local changes", 8)
    print("TARGET_CLEAN=YES")

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF source detected", 9)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    for index, (old, new, expected_count) in enumerate(REPLACEMENTS, start=1):
        count = text.count(old)
        print(f"REPLACEMENT_{index}_MATCHES={count}")
        if count != expected_count:
            die(f"replacement {index} expected {expected_count} exact matches, found {count}", 20 + index)
        text = text.replace(old, new)

    if "ROLE_LABELS[" in text:
        print("NOTE=Other ROLE_LABELS references remain outside the audited Profile selector scope; they are intentionally untouched.")

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-1-profile-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-1@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.1 Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)

        encoded = text.encode("utf-8")
        if terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        proc = subprocess.run(["git", "diff", "--binary", "--full-index", "--", TARGET], cwd=tmp, text=True, capture_output=True)
        if proc.returncode:
            die(f"git diff failed rc={proc.returncode}", 50)
        if not proc.stdout.strip():
            die("generated patch is empty", 51)
        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if parsed_paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 52)
        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_SOURCE")
        print("PHASE5_1_PROFILE_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
