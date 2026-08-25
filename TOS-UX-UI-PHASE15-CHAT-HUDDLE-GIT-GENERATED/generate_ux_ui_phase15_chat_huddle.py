#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "7f6d401b1bce57c05b86559a322dcac2a2dad876"
TARGET_FILE = "frontend/src/components/ChatPanel.jsx"
EXPECTED_BLOB = "8923e607903570001859a17a0ed127de7b50e55c"

HUDDLE_START = "function HuddleRemoteVideo("
HUDDLE_END = "\n\nfunction MessageFiles("

REPLACEMENTS = [('rounded-3xl bg-zinc-950', 'rounded-2xl bg-zinc-950', 2),
 ('h-28 w-full object-cover', 'h-24 w-full object-cover', 2),
 ('fixed inset-x-3 bottom-3 z-40 sm:inset-x-auto sm:left-6 sm:w-[360px]',
  'fixed inset-x-2.5 bottom-2.5 z-40 sm:inset-x-auto sm:left-5 sm:w-[340px]',
  1),
 ('overflow-hidden rounded-[28px] border border-zinc-100 bg-white shadow-2xl shadow-zinc-900/20',
  'overflow-hidden rounded-[22px] border border-zinc-100 bg-white shadow-xl shadow-zinc-900/15',
  1),
 ('border-b border-zinc-100 bg-zinc-950 px-4 py-3 text-white', 'border-b border-zinc-100 bg-zinc-950 px-3.5 py-2.5 text-white', 1),
 ('flex items-start justify-between gap-3', 'flex items-start justify-between gap-2.5', 1),
 ('inline-flex items-center gap-2 rounded-full bg-emerald-400/10 px-2.5 py-1 text-[11px]',
  'inline-flex items-center gap-1.5 rounded-full bg-emerald-400/10 px-2 py-0.5 text-[10px]',
  1),
 ('mt-2 truncate text-sm font-black', 'mt-1.5 truncate text-sm font-black', 1),
 ('mt-1 text-[11px] text-zinc-400">{statusLabel}', 'mt-0.5 text-[10px] text-zinc-400">{statusLabel}', 1),
 ('grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-white/10', 'grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-white/10', 1),
 ('<X size={16} />', '<X size={15} />', 1),
 ('<div className="p-4">', '<div className="p-3">', 1),
 ('rounded-3xl border border-zinc-100 bg-zinc-50 p-3', 'rounded-2xl border border-zinc-100 bg-zinc-50 p-2.5', 1),
 ('mb-3 flex items-center justify-between gap-2 text-xs', 'mb-2.5 flex items-center justify-between gap-2 text-[11px]', 1),
 ('<div className="space-y-2">', '<div className="space-y-1.5">', 1),
 ('flex items-center gap-3 rounded-2xl bg-white px-3 py-2', 'flex items-center gap-2.5 rounded-xl bg-white px-2.5 py-1.5', 2),
 ('mt-3 grid gap-2 sm:grid-cols-2', 'mt-2.5 grid gap-1.5 sm:grid-cols-2', 1),
 ('grid h-28 place-items-center text-xs font-black', 'grid h-24 place-items-center text-[11px] font-black', 1),
 ('mt-3 rounded-2xl border border-red-100 bg-red-50 px-3 py-2', 'mt-2.5 rounded-xl border border-red-100 bg-red-50 px-2.5 py-1.5', 1),
 ('mt-4 grid grid-cols-3 gap-2', 'mt-3 grid grid-cols-3 gap-1.5', 1),
 ('grid h-12 place-items-center rounded-2xl border', 'grid h-10 place-items-center rounded-xl border', 3),
 ('size={18}', 'size={16}', 5),
 ('mt-4 flex gap-2', 'mt-3 flex gap-2', 1),
 ('rounded-2xl bg-red-500 px-4 py-3', 'rounded-xl bg-red-500 px-3.5 py-2.5', 1),
 ('rounded-2xl bg-zinc-950 px-4 py-3', 'rounded-xl bg-zinc-950 px-3.5 py-2.5', 1),
 ('size={17}', 'size={16}', 2)]

BEHAVIOR_MARKERS = [
    "if (videoRef.current) videoRef.current.srcObject = stream || null;",
    "if (!open) return null;",
    "const huddleLang = currentChatLang();",
    "const remoteEntries = Object.entries(remoteStreams || {});",
    "const participantStatus = (participant = {}) => {",
    "participants.map((participant) => (",
    "remoteEntries.map(([socketId, stream]) => {",
    "onClick={onClose}",
    "onClick={onToggleMic}",
    "onClick={onToggleCamera}",
    "onClick={onToggleScreen}",
    "onClick={onLeave}",
    "onClick={onJoin}",
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

    if before.count(HUDDLE_START) != 1:
        raise RuntimeError(f"HUDDLE_START_COUNT={before.count(HUDDLE_START)}; expected 1")
    start = before.index(HUDDLE_START)
    tail = before[start:]
    if tail.count(HUDDLE_END) != 1:
        raise RuntimeError(f"POST_START_HUDDLE_END_COUNT={tail.count(HUDDLE_END)}; expected 1")
    end = start + tail.index(HUDDLE_END)
    prefix = before[:start]
    huddle = before[start:end]
    suffix = before[end:]

    prefix_hash = digest(prefix)
    suffix_hash = digest(suffix)
    huddle_before_hash = digest(huddle)

    updated = huddle
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
    print("HUDDLE_SCOPE=HUDDLE_PANEL_ONLY")
    print("HUDDLE_REMOTE_VIDEO_INCLUDED=YES")
    print("UI12_CHAT_MAIN_CHANGED=NO")
    print("UI13_CHAT_DETAILS_CHANGED=NO")
    print("UI14_CHAT_THREAD_CHANGED=NO")
    print("HUDDLE_BEHAVIOR_CHANGED=NO")
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
    print(f"HUDDLE_BLOCK_BEFORE_SHA256={huddle_before_hash}")
    print(f"HUDDLE_BLOCK_AFTER_SHA256={digest(updated)}")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_PATH={patch_path}")

if __name__ == "__main__":
    main()
