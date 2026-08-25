#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "fa39c1724226be3e04b1a73052684e6950fa8cd5"
TARGET_FILE = "frontend/src/pages/TeamPage.jsx"
EXPECTED_BLOB = "921a8e8a05c1fa1b401f70499c5b8c07bba11bb7"

MAIN_START = '    <div dir={panelDir} className={cn("mb-5 rounded-[30px] border border-zinc-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-900/70", alignClass)}>'
MAIN_END = '\n\n      {selectedOption && selectedDetails && <div ref={departmentDetailsRef}'

REPLACEMENTS = [
    ('mb-5 rounded-[30px] border border-zinc-100 bg-white p-5 shadow-sm', 'mb-5 rounded-[24px] border border-zinc-100 bg-white p-4 shadow-sm', 1),
    ('mb-5 flex flex-wrap items-center justify-between gap-3', 'mb-3.5 flex flex-wrap items-center justify-between gap-2.5', 1),
    ('text-xl font-black text-zinc-950 dark:text-white', 'text-lg font-black text-zinc-950 dark:text-white', 1),
    ('mt-1 text-xs font-bold text-zinc-500', 'mt-0.5 text-[11px] font-bold text-zinc-500', 1),
    ('rounded-2xl bg-zinc-50 px-4 py-3 text-xs font-black text-zinc-500', 'rounded-xl bg-zinc-50 px-3 py-2.5 text-[11px] font-black text-zinc-500', 1),
    ('overflow-hidden rounded-[26px] border border-zinc-100', 'overflow-hidden rounded-[20px] border border-zinc-100', 1),
    ('hidden bg-zinc-50 px-4 py-3 text-[11px] font-black text-zinc-400', 'hidden bg-zinc-50 px-3.5 py-2.5 text-[10px] font-black text-zinc-400', 1),
    ('md:items-center md:gap-4', 'md:items-center md:gap-3', 1),
    ('grid gap-4 px-4 py-4 transition', 'grid gap-3 px-3.5 py-3 transition', 1),
    ('flex min-w-0 items-center gap-3', 'flex min-w-0 items-center gap-2.5', 1),
    ('grid h-11 w-11 shrink-0 place-items-center rounded-2xl border text-sm font-black', 'grid h-10 w-10 shrink-0 place-items-center rounded-xl border text-xs font-black', 1),
    ('mt-1 text-[11px] font-bold text-zinc-400', 'mt-0.5 text-[10px] font-bold text-zinc-400', 1),
    ('min-w-0 space-y-1', 'min-w-0 space-y-0.5', 1),
    ('inline-flex rounded-full border px-3 py-1 text-xs font-black', 'inline-flex rounded-full border px-2.5 py-1 text-[11px] font-black', 1),
    ('rounded-2xl border border-zinc-200 bg-white px-4 py-2 text-xs font-black', 'rounded-xl border border-zinc-200 bg-white px-3.5 py-1.5 text-[11px] font-black', 1),
]

BEHAVIOR_MARKERS = [
    'rows.map(({ option, details }) => {',
    'openDepartment(option)',
    'departmentLabel(option, lang)',
    'memberCountLabel(details.activeCount, lang)',
    'selectedOption && selectedDetails',
    'setSelectedDepartmentKey(option.key)',
    'setActiveTab("info")',
]

EXCLUDED_MARKERS = [
    'function MiniStat(',
    'selectedDetailUser && (() => {',
    'showInviteDrawer && canManageTeamUsers',
    'function FormerEmployeesModal(',
    'assignProject.user && (',
    'separationRequest.user && (',
    'activeTab === "info"',
    'activeTab === "projects"',
    'activeTab === "settings"',
    'activeTab === "activity"',
    'saveLeadership',
    'saveDesignSettings',
]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def replace_exact(text, old, new, expected, label):
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}_COUNT={count}; expected {expected}")
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

    if before.count(MAIN_START) != 1:
        raise RuntimeError(f"MAIN_START_COUNT={before.count(MAIN_START)}; expected 1")
    start = before.index(MAIN_START)
    post_start = before[start:]
    if post_start.count(MAIN_END) != 1:
        raise RuntimeError(f"POST_START_MAIN_END_COUNT={post_start.count(MAIN_END)}; expected 1")
    end = before.index(MAIN_END, start)

    prefix = before[:start]
    department_main = before[start:end]
    suffix = before[end:]

    prefix_hash = digest(prefix)
    suffix_hash = digest(suffix)
    main_before_hash = digest(department_main)

    updated = department_main
    for i, (old, new, expected) in enumerate(REPLACEMENTS, 1):
        updated = replace_exact(updated, old, new, expected, f"MAIN_ANCHOR_{i:02d}")

    after = prefix + updated + suffix
    if after == before:
        raise RuntimeError("NO_CHANGE")
    if digest(after[:start]) != prefix_hash:
        raise RuntimeError("PREFIX_CHANGED")
    if digest(after[start + len(updated):]) != suffix_hash:
        raise RuntimeError("SUFFIX_CHANGED")

    for marker in BEHAVIOR_MARKERS + EXCLUDED_MARKERS:
        if before.count(marker) != after.count(marker):
            raise RuntimeError(f"MARKER_COUNT_CHANGED={marker}")

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
    print("DEPARTMENT_SCOPE=DEPARTMENT_MANAGEMENT_MAIN_ONLY")
    print("DEPARTMENT_DETAILS_CHANGED=NO")
    print("DESIGN_DEPARTMENT_TABS_CHANGED=NO")
    print("LEADERSHIP_PANEL_CHANGED=NO")
    print("UI16_TEAM_MAIN_CHANGED=NO")
    print("UI17_MEMBER_DETAILS_CHANGED=NO")
    print("INVITE_DRAWER_CHANGED=NO")
    print("FORMER_MEMBERS_CHANGED=NO")
    print("PROJECT_ASSIGNMENT_DIALOG_CHANGED=NO")
    print("SEPARATION_DIALOG_CHANGED=NO")
    print("PERMISSIONS_UI_CHANGED=NO")
    print("DEPARTMENT_BEHAVIOR_CHANGED=NO")
    print("TEAM_BEHAVIOR_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"PREFIX_SHA256={prefix_hash}")
    print(f"SUFFIX_SHA256={suffix_hash}")
    print(f"DEPARTMENT_MAIN_BEFORE_SHA256={main_before_hash}")
    print(f"DEPARTMENT_MAIN_AFTER_SHA256={digest(updated)}")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_PATH={patch_path}")


if __name__ == "__main__":
    main()
