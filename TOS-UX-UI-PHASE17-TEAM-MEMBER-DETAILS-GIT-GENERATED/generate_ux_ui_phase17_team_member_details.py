#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "0121274839273eb96bb7877d15506e834ee478e5"
TARGET_FILE = "frontend/src/pages/TeamPage.jsx"
EXPECTED_BLOB = "cd69a16ef5b17c95a33bd30b7e60f25a4bd9a355"

DETAILS_START = '      {selectedDetailUser && (() => {'
DETAILS_END = '\n    </div>\n  );\n}\n'

REPLACEMENTS = [
    (
        'fixed inset-0 z-50 overflow-y-auto bg-[#f5f1e8]/95 p-2 backdrop-blur-md dark:bg-zinc-950/90 sm:p-4',
        'fixed inset-0 z-50 overflow-y-auto bg-[#f5f1e8]/94 p-1.5 backdrop-blur-[3px] dark:bg-zinc-950/90 sm:p-3',
        1,
    ),
    (
        'mx-auto min-h-[calc(100vh-1rem)] w-full max-w-[1500px] overflow-hidden rounded-[30px] border border-white/90 bg-[#fbfaf7] text-right shadow-[0_30px_100px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-zinc-900 sm:min-h-[calc(100vh-2rem)]',
        'mx-auto min-h-[calc(100vh-.75rem)] w-full max-w-[1400px] overflow-hidden rounded-[24px] border border-white/90 bg-[#fbfaf7] text-right shadow-[0_24px_80px_rgba(15,23,42,0.18)] dark:border-white/10 dark:bg-zinc-900 sm:min-h-[calc(100vh-1.5rem)]',
        1,
    ),
    (
        'sticky top-0 z-20 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 bg-white/95 px-4 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/95 sm:px-6',
        'sticky top-0 z-20 flex flex-wrap items-center justify-between gap-2.5 border-b border-zinc-100 bg-white/95 px-3.5 py-2.5 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/95 sm:px-5',
        1,
    ),
    (
        'flex flex-wrap items-center justify-start gap-2 text-[11px] font-black text-zinc-400',
        'flex flex-wrap items-center justify-start gap-1.5 text-[10px] font-black text-zinc-400',
        1,
    ),
    (
        'mt-1 flex items-center justify-start gap-2',
        'mt-0.5 flex items-center justify-start gap-1.5',
        1,
    ),
    ('<UserCog size={21} className="text-amber-600" />', '<UserCog size={18} className="text-amber-600" />', 1),
    (
        'text-xl font-black text-zinc-950 dark:text-white">{teamText("تفاصيل العضو", "Member details", lang)}',
        'text-lg font-black text-zinc-950 dark:text-white">{teamText("تفاصيل العضو", "Member details", lang)}',
        1,
    ),
    (
        'mt-1 text-xs font-bold text-zinc-500">{teamText("استعراض وإدارة بيانات العضو وصلاحياته وإجراءاته دون حذف أي وظيفة قائمة.", "Review and manage member data, permissions, and actions without removing existing functionality.", lang)}',
        'mt-0.5 text-[11px] font-bold text-zinc-500">{teamText("استعراض وإدارة بيانات العضو وصلاحياته وإجراءاته دون حذف أي وظيفة قائمة.", "Review and manage member data, permissions, and actions without removing existing functionality.", lang)}',
        1,
    ),
    (
        'grid h-10 w-10 shrink-0 place-items-center rounded-full border border-zinc-200 bg-white text-zinc-500 shadow-sm transition',
        'grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-zinc-200 bg-white text-zinc-500 shadow-sm transition',
        1,
    ),
    ('<X size={18} />', '<X size={16} />', 1),
    (
        'form onSubmit={saveEdit} className="space-y-4 p-4 sm:p-5 lg:p-6"',
        'form onSubmit={saveEdit} className="space-y-3 p-3 sm:p-4 lg:p-4"',
        1,
    ),
    (
        'rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/35 sm:p-5',
        'rounded-[22px] border border-zinc-100 bg-white p-3.5 shadow-sm dark:border-white/10 dark:bg-zinc-950/35 sm:p-4',
        1,
    ),
    ('flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between', 'flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between', 1),
    ('flex min-w-0 items-center gap-4', 'flex min-w-0 items-center gap-3', 1),
    (
        'size="h-20 w-20 sm:h-24 sm:w-24" radius="rounded-full" textSize="text-2xl"',
        'size="h-16 w-16 sm:h-20 sm:w-20" radius="rounded-full" textSize="text-xl"',
        1,
    ),
    ('break-words text-2xl font-black text-zinc-950 dark:text-white', 'break-words text-xl font-black text-zinc-950 dark:text-white', 1),
    (
        'grid min-w-0 flex-1 gap-3 sm:grid-cols-2 xl:max-w-[820px] xl:grid-cols-5',
        'grid min-w-0 flex-1 gap-2 sm:grid-cols-2 xl:max-w-[760px] xl:grid-cols-5',
        1,
    ),
    (
        'rounded-[24px] border border-zinc-100 bg-white p-3 shadow-sm dark:border-white/10 dark:bg-zinc-950/35',
        'rounded-[20px] border border-zinc-100 bg-white p-2.5 shadow-sm dark:border-white/10 dark:bg-zinc-950/35',
        1,
    ),
    ('grid gap-4 xl:grid-cols-12', 'grid gap-3 xl:grid-cols-12', 1),
    (
        'rounded-[26px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/35 xl:col-span-4',
        'rounded-[22px] border border-zinc-100 bg-white p-3.5 shadow-sm dark:border-white/10 dark:bg-zinc-950/35 xl:col-span-4',
        5,
    ),
    (
        'rounded-[26px] border border-amber-200 bg-white p-4 shadow-sm ring-2 ring-amber-50 dark:border-amber-500/30 dark:bg-zinc-950/35 dark:ring-amber-500/5 xl:col-span-4',
        'rounded-[22px] border border-amber-200 bg-white p-3.5 shadow-sm ring-1 ring-amber-50 dark:border-amber-500/30 dark:bg-zinc-950/35 dark:ring-amber-500/5 xl:col-span-4',
        1,
    ),
    ('mt-4 grid grid-cols-3 gap-2 text-center', 'mt-3 grid grid-cols-3 gap-1.5 text-center', 1),
    ('mt-3 max-h-56 space-y-2 overflow-y-auto pe-1', 'mt-2.5 max-h-48 space-y-1.5 overflow-y-auto pe-1', 1),
    ('mt-4 grid gap-3 sm:grid-cols-2', 'mt-3 grid gap-2.5 sm:grid-cols-2', 2),
    ('mt-4 grid gap-2 sm:grid-cols-2', 'mt-3 grid gap-1.5 sm:grid-cols-2', 1),
    (
        'mt-3 space-y-2 rounded-2xl bg-zinc-50 p-3 dark:bg-white/[0.04]',
        'mt-2.5 space-y-1.5 rounded-xl bg-zinc-50 p-2.5 dark:bg-white/[0.04]',
        1,
    ),
    (
        'mt-4 min-h-36 rounded-2xl border border-zinc-100 bg-zinc-50 p-4 text-xs font-bold leading-6',
        'mt-3 min-h-28 rounded-xl border border-zinc-100 bg-zinc-50 p-3 text-xs font-bold leading-6',
        1,
    ),
    (
        'w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 pe-12 text-sm font-bold',
        'w-full rounded-xl border border-zinc-200 bg-zinc-50 px-3.5 py-2.5 pe-11 text-sm font-bold',
        2,
    ),
    ('mt-4 space-y-3', 'mt-3 space-y-2.5', 2),
    (
        'flex items-start justify-end gap-3 rounded-2xl bg-zinc-50 p-3 dark:bg-white/[0.04]',
        'flex items-start justify-end gap-2.5 rounded-xl bg-zinc-50 p-2.5 dark:bg-white/[0.04]',
        1,
    ),
]

BEHAVIOR_MARKERS = [
    'const closeDetails = () => {',
    'setExpandedUserId("");',
    'setEditing(null);',
    'onSubmit={saveEdit}',
    'onClick={closeDetails}',
    'onClick={() => resendInvite(item.id)}',
    'onClick={() => cancelInvite(item.id)}',
    'onClick={() => changeStatus(item, "DISABLED")}',
    'onClick={() => changeStatus(item, "ACTIVE")}',
    'onClick={() => openSeparationRequest(item)}',
    'onClick={() => removeUserFromProject(item, project)}',
    'onClick={() => openAssignProject(item)}',
    'onClick={() => sendPasswordReset(item.id)}',
    'setShowEditNewPassword((value) => !value)',
    'setShowEditConfirmPassword((value) => !value)',
]

EXCLUDED_MARKERS = [
    'function DepartmentManagementPanel(',
    'function FormerEmployeesModal(',
    'function ProjectsPopupModal(',
    'showInviteDrawer && canManageTeamUsers',
    'assignProject.user && (',
    'separationRequest.user && (',
    'TEAM_SCOPE=TEAM_MEMBERS_MAIN_ONLY',
]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def replace_exact(text, old, new, expected, index):
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"ANCHOR_{index:02d}_COUNT={count}; expected {expected}")
    return text.replace(old, new)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: generator.py <repo> <patch-output>")

    repo = Path(sys.argv[1]).resolve()
    patch_path = Path(sys.argv[2]).resolve()

    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    if branch != "main":
        raise RuntimeError(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"HEAD={head}; expected {TARGET_BASE_HEAD}")
    if git(repo, "diff", "--name-only"):
        raise RuntimeError("TRACKED_WORKTREE_NOT_CLEAN")

    target = repo / TARGET_FILE
    before = target.read_text()
    blob = git(repo, "hash-object", TARGET_FILE)
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f"BLOB={blob}; expected {EXPECTED_BLOB}")

    if before.count(DETAILS_START) != 1:
        raise RuntimeError(f"DETAILS_START_COUNT={before.count(DETAILS_START)}; expected 1")
    start = before.index(DETAILS_START)
    tail = before[start:]
    if tail.count(DETAILS_END) != 1:
        raise RuntimeError(f"POST_START_DETAILS_END_COUNT={tail.count(DETAILS_END)}; expected 1")
    end = start + tail.index(DETAILS_END)

    prefix = before[:start]
    details = before[start:end]
    suffix = before[end:]

    prefix_hash = digest(prefix)
    suffix_hash = digest(suffix)
    details_before_hash = digest(details)

    updated = details
    for i, (old, new, expected) in enumerate(REPLACEMENTS, 1):
        updated = replace_exact(updated, old, new, expected, i)

    after = prefix + updated + suffix
    if after == before:
        raise RuntimeError("NO_CHANGE")
    if after[:len(prefix)] != prefix:
        raise RuntimeError("PREFIX_CHANGED")
    if after[len(prefix) + len(updated):] != suffix:
        raise RuntimeError("SUFFIX_CHANGED")

    for marker in BEHAVIOR_MARKERS:
        if before.count(marker) != after.count(marker):
            raise RuntimeError(f"BEHAVIOR_MARKER_CHANGED={marker}")

    for marker in EXCLUDED_MARKERS:
        if marker == 'TEAM_SCOPE=TEAM_MEMBERS_MAIN_ONLY':
            continue
        if before.count(marker) != after.count(marker):
            raise RuntimeError(f"EXCLUDED_MARKER_CHANGED={marker}")

    for marker in ["api.", "api.users.", "api.projects.", "api.permissions.", "useRealtimeRefresh("]:
        if before.count(marker) != after.count(marker):
            raise RuntimeError(f"CALL_COUNT_CHANGED={marker}")

    if any(line.rstrip() != line for line in after.splitlines()):
        raise RuntimeError("TRAILING_WHITESPACE_DETECTED")

    diff = "".join(difflib.unified_diff(
        before.splitlines(True),
        after.splitlines(True),
        fromfile=f"a/{TARGET_FILE}",
        tofile=f"b/{TARGET_FILE}",
    ))
    patch = f"diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n" + diff
    patch_path.write_text(patch)

    new_blob = subprocess.check_output(["git", "hash-object", "--stdin"], input=after, text=True).strip()

    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
    print(f"NEW_BLOB={new_blob}")
    print(f"PATCH_SHA256={hashlib.sha256(patch.encode()).hexdigest()}")
    print("SOURCE_SCOPE=ONE_FILE")
    print("TEAM_MEMBER_DETAILS_SCOPE=DETAILS_DRAWER_ONLY")
    print("UI16_TEAM_MAIN_CHANGED=NO")
    print("DEPARTMENT_MANAGEMENT_CHANGED=NO")
    print("INVITE_DRAWER_CHANGED=NO")
    print("FORMER_MEMBERS_CHANGED=NO")
    print("PROJECT_ASSIGNMENT_DIALOG_CHANGED=NO")
    print("SEPARATION_DIALOG_CHANGED=NO")
    print("PERMISSIONS_UI_CHANGED=NO")
    print("MEMBER_DETAILS_BEHAVIOR_CHANGED=NO")
    print("TEAM_BEHAVIOR_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"PREFIX_SHA256={prefix_hash}")
    print(f"SUFFIX_SHA256={suffix_hash}")
    print(f"DETAILS_BLOCK_BEFORE_SHA256={details_before_hash}")
    print(f"DETAILS_BLOCK_AFTER_SHA256={digest(updated)}")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_PATH={patch_path}")


if __name__ == "__main__":
    main()
