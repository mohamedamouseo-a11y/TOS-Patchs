#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "b56f3d00af1abcfc2553c079278f3db4b7d14115"
TARGET_FILE = "frontend/src/components/ChatPanel.jsx"
EXPECTED_BLOB = "082f578eaec997cec8a2afccee9954b93ab468b1"

THREAD_START = "function ThreadPanel("
THREAD_END = "\n\n\nfunction MessageActions("

REPLACEMENTS = [
    (
        '    <div className="fixed inset-0 z-40 bg-zinc-950/30 backdrop-blur-sm lg:inset-auto lg:bottom-0 lg:right-0 lg:top-0 lg:w-[420px]" role="dialog" aria-modal="true">',
        '    <div className="fixed inset-0 z-40 bg-zinc-950/25 backdrop-blur-[2px] lg:inset-auto lg:bottom-0 lg:right-0 lg:top-0 lg:w-[390px]" role="dialog" aria-modal="true">',
        1,
    ),
    (
        '      <aside className="relative mr-auto flex h-full w-full max-w-[420px] flex-col border-r border-zinc-100 bg-white shadow-2xl dark:border-white/10 dark:bg-zinc-950 lg:mr-0">',
        '      <aside className="relative mr-auto flex h-full w-full max-w-[390px] flex-col border-r border-zinc-100 bg-white shadow-xl dark:border-white/10 dark:bg-zinc-950 lg:mr-0">',
        1,
    ),
    (
        '        <div className="flex items-start justify-between gap-3 border-b border-zinc-100 p-4 dark:border-white/10">',
        '        <div className="flex items-start justify-between gap-2.5 border-b border-zinc-100 p-3.5 dark:border-white/10">',
        1,
    ),
    (
        '            <div className="mt-1 text-xs text-zinc-400">ردود منفصلة على الرسالة الأصلية</div>',
        '            <div className="mt-0.5 text-[11px] text-zinc-400">ردود منفصلة على الرسالة الأصلية</div>',
        1,
    ),
    (
        '            {latestReply && <div className="mt-2 rounded-2xl bg-zinc-50 px-3 py-2 text-[11px] text-zinc-500 dark:bg-white/5 dark:text-zinc-300">آخر رد: {truncateMessagePreview(latestReply.body, 70)}</div>}',
        '            {latestReply && <div className="mt-1.5 rounded-xl bg-zinc-50 px-2.5 py-1.5 text-[10px] text-zinc-500 dark:bg-white/5 dark:text-zinc-300">آخر رد: {truncateMessagePreview(latestReply.body, 70)}</div>}',
        1,
    ),
    (
        '          <button type="button" onClick={onClose} className="grid h-9 w-9 place-items-center rounded-2xl border border-zinc-100 text-zinc-500 dark:border-white/10"><X size={16} /></button>',
        '          <button type="button" onClick={onClose} className="grid h-8 w-8 place-items-center rounded-xl border border-zinc-100 text-zinc-500 dark:border-white/10"><X size={15} /></button>',
        1,
    ),
    (
        '        <div className="min-h-0 flex-1 overflow-y-auto p-4">',
        '        <div className="min-h-0 flex-1 overflow-y-auto p-3">',
        1,
    ),
    (
        '          <div className="rounded-3xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-100">',
        '          <div className="rounded-2xl border border-amber-100 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-100">',
        1,
    ),
    (
        '          <div className="mt-4 space-y-3">',
        '          <div className="mt-3 space-y-2">',
        1,
    ),
    (
        'className="rounded-2xl bg-zinc-50 p-3 text-xs text-zinc-400 dark:bg-white/5"',
        'className="rounded-xl bg-zinc-50 p-2.5 text-xs text-zinc-400 dark:bg-white/5"',
        2,
    ),
    (
        '              <div key={reply.id} className="rounded-2xl bg-zinc-50 p-3 text-sm dark:bg-white/5">',
        '              <div key={reply.id} className="rounded-xl bg-zinc-50 p-2.5 text-sm dark:bg-white/5">',
        1,
    ),
    (
        '        <div className="border-t border-zinc-100 p-4 dark:border-white/10">',
        '        <div className="border-t border-zinc-100 p-3 dark:border-white/10">',
        1,
    ),
    (
        '          <button type="button" onClick={() => onReply(rootMessage)} className="w-full rounded-2xl bg-zinc-950 px-4 py-3 text-xs font-black text-white dark:bg-white dark:text-zinc-950">رد داخل الـ Thread</button>',
        '          <button type="button" onClick={() => onReply(rootMessage)} className="w-full rounded-xl bg-zinc-950 px-3.5 py-2.5 text-xs font-black text-white dark:bg-white dark:text-zinc-950">رد داخل الـ Thread</button>',
        1,
    ),
]

BEHAVIOR_MARKERS = [
    "if (!open || !rootMessage) return null;",
    "const visibleReplies = replies.length ? replies : localReplies;",
    "const latestReply = visibleReplies[visibleReplies.length - 1];",
    "onClick={onClose}",
    "onClick={() => onReply(rootMessage)}",
    "truncateMessagePreview(latestReply.body, 70)",
    "formatMessageTime(reply.createdAt)",
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

    if before.count(THREAD_START) != 1:
        raise RuntimeError(f"THREAD_START_COUNT={before.count(THREAD_START)}; expected 1")

    start = before.index(THREAD_START)
    tail = before[start:]
    if tail.count(THREAD_END) != 1:
        raise RuntimeError(f"POST_START_THREAD_END_COUNT={tail.count(THREAD_END)}; expected 1")

    end = start + tail.index(THREAD_END)
    prefix = before[:start]
    thread = before[start:end]
    suffix = before[end:]

    prefix_hash = digest(prefix)
    suffix_hash = digest(suffix)
    thread_before_hash = digest(thread)

    updated = thread
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

    for marker in ["api.", "useChat(", "useHuddleWebRTC(", "getSocket(", "sendMessage(", "uploadChatFile(", "deleteChatFile("]:
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
    print("THREAD_SCOPE=THREAD_PANEL_ONLY")
    print("UI12_CHAT_MAIN_CHANGED=NO")
    print("UI13_CHAT_DETAILS_CHANGED=NO")
    print("THREAD_BEHAVIOR_CHANGED=NO")
    print("CHAT_BEHAVIOR_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("CHAT_API_CALLS_CHANGED=NO")
    print("FILE_API_CALLS_CHANGED=NO")
    print("SOCKET_LOGIC_CHANGED=NO")
    print("HUDDLE_LOGIC_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"PREFIX_SHA256={prefix_hash}")
    print(f"SUFFIX_SHA256={suffix_hash}")
    print(f"THREAD_BLOCK_BEFORE_SHA256={thread_before_hash}")
    print(f"THREAD_BLOCK_AFTER_SHA256={digest(updated)}")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_PATH={patch_path}")


if __name__ == "__main__":
    main()
