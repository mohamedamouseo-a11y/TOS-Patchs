#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "2ecd378d422726d45299e4353b4a9fc30e983207"
TARGET_FILE = "frontend/src/pages/ProfilePage.jsx"
EXPECTED_BLOB = "4c204e2ff6a9a49c2f93fc78e8ae00c3cbfe08b7"

REPLACEMENTS = [
    (
        'function ProfileIdentityCard({ profile, form, isOwnProfile, avatarAllowed, nextAvatarDate, handleAvatarFile }) {',
        'function ProfileIdentityCard({ profile, form, isOwnProfile, avatarAllowed, nextAvatarDate, handleAvatarFile, isAr }) {'
    ),
    (
        '<Badge tone="gold">{ROLE_LABELS[profile.role] || profile.role}</Badge>',
        '<Badge tone="gold">{profileRoleLabel(profile.role, isAr)}</Badge>'
    ),
    (
        '<ProfileIdentityCard profile={profile} form={form} isOwnProfile={isOwnProfile} avatarAllowed={avatarAllowed} nextAvatarDate={nextAvatarDate} handleAvatarFile={handleAvatarFile} />',
        '<ProfileIdentityCard profile={profile} form={form} isOwnProfile={isOwnProfile} avatarAllowed={avatarAllowed} nextAvatarDate={nextAvatarDate} handleAvatarFile={handleAvatarFile} isAr={isAr} />'
    ),
    (
        '<p className="text-sm font-black text-zinc-950 dark:text-white">{ROLE_LABELS[profile.role] || profile.role}</p>',
        '<p className="text-sm font-black text-zinc-950 dark:text-white">{profileRoleLabel(profile.role, isAr)}</p>'
    ),
]


def run(cmd, cwd):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def replace_exact(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"ANCHOR_{label}_COUNT={count}; expected 1")
    return text.replace(old, new, 1)


def main():
    if len(sys.argv) != 3:
        print("Usage: generate_profile_role_labels_hotfix.py <repo> <output.patch>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = repo / TARGET_FILE

    branch = run(["git", "branch", "--show-current"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo)
    blob = run(["git", "hash-object", "--", TARGET_FILE], repo)

    if branch != "main":
        raise RuntimeError(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"HEAD={head}; expected {TARGET_BASE_HEAD}")
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f"BLOB={blob}; expected {EXPECTED_BLOB}")

    original = target.read_text(encoding="utf-8")

    # Root-cause guard: the undefined identifier must exist exactly twice before the hotfix.
    undefined_ref = 'ROLE_LABELS[profile.role]'
    if original.count(undefined_ref) != 2:
        raise RuntimeError(f"UNDEFINED_ROLE_LABELS_REF_COUNT={original.count(undefined_ref)}; expected 2")
    if 'const ROLE_LABELS =' in original:
        raise RuntimeError("ROLE_LABELS_ALREADY_DEFINED_UNEXPECTEDLY")

    updated = original
    for idx, (old, new) in enumerate(REPLACEMENTS, start=1):
        updated = replace_exact(updated, old, new, f"{idx:02d}")

    if undefined_ref in updated:
        raise RuntimeError("UNDEFINED_ROLE_LABELS_REFERENCE_REMAINS")
    if updated.count('profileRoleLabel(profile.role, isAr)') < 2:
        raise RuntimeError("LOCALIZED_ROLE_LABEL_FIX_MISSING")

    # No business/API behavior may change.
    for marker in [
        'api.users.myProfile()',
        'api.users.profile(profileId)',
        'api.users.profiles()',
        'loadProfile(selectedProfileId)',
        'handleAvatarFile',
    ]:
        if original.count(marker) != updated.count(marker):
            raise RuntimeError(f"BEHAVIOR_MARKER_CHANGED={marker}")

    if original.count('api.') != updated.count('api.'):
        raise RuntimeError("API_CALL_COUNT_CHANGED")

    # Prevent whitespace-only CI failures.
    for lineno, line in enumerate(updated.splitlines(), start=1):
        if line.rstrip(" \t") != line:
            raise RuntimeError(f"TRAILING_WHITESPACE_LINE={lineno}")

    new_blob = git_blob_sha(updated.encode("utf-8"))
    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f"a/{TARGET_FILE}",
        tofile=f"b/{TARGET_FILE}",
        n=3,
    ))

    patch = (
        f"diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n"
        f"index {EXPECTED_BLOB[:7]}..{new_blob[:7]} 100644\n"
        + "".join(diff)
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(patch, encoding="utf-8")
    sha256 = hashlib.sha256(output.read_bytes()).hexdigest()

    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
    print(f"NEW_BLOB={new_blob}")
    print("ROOT_CAUSE=UNDEFINED_ROLE_LABELS_REFERENCE")
    print("FIX_SCOPE=PROFILE_ROLE_LABEL_RENDERING_ONLY")
    print("SOURCE_SCOPE=ONE_FILE")
    print("API_CALLS_CHANGED=NO")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_SHA256={sha256}")
    print(f"PATCH_PATH={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
