#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/var/www/TOS")
EXPECTED_HEAD = "293280da438adb8f8d9a8a821fe29e1deff41dd1"

EXPECTED_BLOBS = {
    "backend/src/routes/files.routes.js": "12684b4f617766736dcc298a4c371143c000fca9",
    "backend/src/routes/users.routes.js": "2d65febb608d33aac2077e86eb70198feaaf50f6",
    "backend/src/services/companyDepartments.service.js": "c6d0979f71564f84293a72b05c5f142775d13ce9",
    "frontend/src/App.jsx": "930f4da68dd9fcf021b967576e3edee2b1cbd630",
    "frontend/src/lib/api.js": "d5fa521cd22495237ab41e1ebb463485d587ef6d",
    "frontend/src/pages/TeamPage.jsx": "e9e098e3a2e7ac7070ed6c6d6d6c674573a9a222",
}

EXPECTED_PRE_MODIFIED = {
    "backend/src/routes/files.routes.js",
    "backend/src/routes/userProfile.routes.js",
    "backend/src/routes/users.routes.js",
    "backend/src/services/companyDepartments.service.js",
    "frontend/src/App.jsx",
    "frontend/src/lib/api.js",
    "frontend/src/pages/TeamPage.jsx",
}

TARGET = "backend/src/utils/sanitize.js"
PROFILE_ROUTE = "backend/src/routes/userProfile.routes.js"


def run(*args):
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


def git_blob(rel):
    return run("git", "hash-object", str(ROOT / rel))


def tracked_modified():
    output = run("git", "diff", "--name-only")
    return {line.strip() for line in output.splitlines() if line.strip()}


def staged_modified():
    output = run("git", "diff", "--cached", "--name-only")
    return {line.strip() for line in output.splitlines() if line.strip()}


def guard_state():
    head = run("git", "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD_MISMATCH expected={EXPECTED_HEAD} actual={head}")

    modified = tracked_modified()
    if modified != EXPECTED_PRE_MODIFIED:
        raise RuntimeError(
            "MODIFIED_SET_MISMATCH expected="
            + ",".join(sorted(EXPECTED_PRE_MODIFIED))
            + " actual="
            + ",".join(sorted(modified))
        )

    staged = staged_modified()
    if staged:
        raise RuntimeError("STAGED_FILES_PRESENT=" + ",".join(sorted(staged)))

    for rel, expected in EXPECTED_BLOBS.items():
        actual = git_blob(rel)
        if actual != expected:
            raise RuntimeError(f"BLOB_MISMATCH {rel}: expected={expected} actual={actual}")

    # sanitize.js must still be pristine relative to the pinned production HEAD.
    target_blob = git_blob(TARGET)
    head_target_blob = run("git", "rev-parse", f"HEAD:{TARGET}")
    if target_blob != head_target_blob:
        raise RuntimeError(f"TARGET_NOT_PRISTINE {TARGET}: head={head_target_blob} actual={target_blob}")

    # Phase 3.1 must be present on the earlier userProfile avatar route.
    profile = (ROOT / PROFILE_ROUTE).read_text(encoding="utf-8")
    required_markers = [
        'const dataMatch = avatarUrl.match(/^data:image\\/(png|jpeg|jpg|webp);base64,(.+)$/is);',
        'return res.send(buffer);',
        'return res.redirect(302, avatarUrl);',
    ]
    for marker in required_markers:
        if marker not in profile:
            raise RuntimeError(f"PHASE3_1_MARKER_MISSING {marker}")
    if 'if (target.avatarUrl) return res.redirect(target.avatarUrl);' in profile:
        raise RuntimeError("PHASE3_1_LEGACY_REDIRECT_STILL_PRESENT")


def build_change():
    guard_state()
    path = ROOT / TARGET
    text = path.read_text(encoding="utf-8")

    old = '''export function sanitizeChatUser(user) {\n  if (!user) return null;\n  return {\n    id: user.id,\n    name: user.name,\n    role: user.role,\n    avatar: user.avatarUrl || user.avatar || null,\n  };\n}'''

    new = '''function compactChatAvatarUrl(user) {\n  const avatarUrl = String(user?.avatarUrl || user?.avatar || "").trim();\n  if (!avatarUrl) return null;\n  if (!/^data:image\\//i.test(avatarUrl)) return avatarUrl;\n  if (!user?.id) return null;\n  return `/api/users/${encodeURIComponent(user.id)}/avatar`;\n}\n\nexport function sanitizeChatUser(user) {\n  if (!user) return null;\n  return {\n    id: user.id,\n    name: user.name,\n    role: user.role,\n    avatar: compactChatAvatarUrl(user),\n  };\n}'''

    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"SANITIZE_CHAT_USER_MATCH_COUNT expected=1 actual={count}")

    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.check == args.apply:
        parser.error("use exactly one of --check or --apply")

    content = build_change()
    print(f"PHASE4_TARGET={TARGET}")

    if args.check:
        print("PHASE4_PATCH_CHECK=PASS")
        return 0

    path = ROOT / TARGET
    tmp = path.with_name(path.name + ".phase4.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
    print(f"UPDATED {TARGET} blob={git_blob(TARGET)}")
    print("PHASE4_PATCH_APPLIED=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PHASE4_PATCH_ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
