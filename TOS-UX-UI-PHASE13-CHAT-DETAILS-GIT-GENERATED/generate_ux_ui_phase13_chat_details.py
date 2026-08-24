#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "3d050ab94ceeb093fce81ee347179ceacf728678"
TARGET_FILE = "frontend/src/components/ChatPanel.jsx"
EXPECTED_BLOB = "7363152d2efefc4a935fa12899daddb7d838744b"

DETAILS_START = '      <aside className={`${focusMode || !detailsPanelOpen ?'
DETAILS_END = '      </aside>\n    </div>\n  );\n}'

REPLACEMENTS = [
    (
        '      <aside className={`${focusMode || !detailsPanelOpen ? "hidden" : "fixed inset-0 z-40 block overflow-y-auto bg-zinc-950/45 p-3 backdrop-blur-sm xl:static xl:z-auto xl:block xl:overflow-visible xl:bg-transparent xl:p-2.5 xl:backdrop-blur-0"} tos-chat-details-panel min-h-0 min-w-0 border-r border-zinc-200 dark:border-white/10 2xl:p-3`}>',
        '      <aside className={`${focusMode || !detailsPanelOpen ? "hidden" : "fixed inset-0 z-40 block overflow-y-auto bg-zinc-950/40 p-2.5 backdrop-blur-sm xl:static xl:z-auto xl:block xl:overflow-visible xl:bg-transparent xl:p-2 xl:backdrop-blur-0"} tos-chat-details-panel min-h-0 min-w-0 border-r border-zinc-200 dark:border-white/10 2xl:p-2.5`}>',
        1,
    ),
    (
        '        <div className="mr-auto flex h-full min-h-0 max-w-md flex-col gap-2.5 overflow-y-auto rounded-[28px] bg-zinc-50 p-2.5 shadow-2xl dark:bg-zinc-950 xl:max-w-none xl:rounded-none xl:bg-transparent xl:p-0 xl:shadow-none 2xl:gap-3">',
        '        <div className="mr-auto flex h-full min-h-0 max-w-md flex-col gap-2 overflow-y-auto rounded-[22px] bg-zinc-50 p-2 shadow-xl dark:bg-zinc-950 xl:max-w-none xl:rounded-none xl:bg-transparent xl:p-0 xl:shadow-none 2xl:gap-2.5">',
        1,
    ),
    (
        'tos-chat-detail-card rounded-[22px] border border-zinc-100 bg-white p-3 shadow-sm dark:border-white/10 dark:bg-zinc-900 2xl:rounded-[24px] 2xl:p-4',
        'tos-chat-detail-card rounded-[18px] border border-zinc-100 bg-white p-2.5 shadow-sm dark:border-white/10 dark:bg-zinc-900 2xl:rounded-[20px] 2xl:p-3',
        9,
    ),
    (
        '            <div className="flex items-center justify-between gap-3">',
        '            <div className="flex items-center justify-between gap-2.5">',
        1,
    ),
    (
        '                <div className="mt-1 text-xs text-zinc-400">{ui.detailsSubtitle}</div>',
        '                <div className="mt-0.5 text-[11px] text-zinc-400">{ui.detailsSubtitle}</div>',
        1,
    ),
    (
        '            <div className="mt-3 grid grid-cols-3 gap-1 rounded-2xl bg-zinc-50 p-1 dark:bg-white/5">',
        '            <div className="mt-2.5 grid grid-cols-3 gap-1 rounded-xl bg-zinc-50 p-1 dark:bg-white/5">',
        1,
    ),
    (
        'className={`rounded-xl px-2 py-2 text-[11px] font-black transition ${detailsTab === tab.value ?',
        'className={`rounded-lg px-2 py-1.5 text-[10px] font-black transition ${detailsTab === tab.value ?',
        1,
    ),
    (
        '            <div className="mt-3 grid grid-cols-3 gap-2 text-center text-[11px] font-black">',
        '            <div className="mt-2.5 grid grid-cols-3 gap-1.5 text-center text-[10px] font-black">',
        1,
    ),
    (
        '              <span className="rounded-2xl bg-amber-50 px-2 py-2 text-amber-700 dark:bg-amber-500/10 dark:text-amber-100">Health<br />{chatHealthScore}%</span>',
        '              <span className="rounded-xl bg-amber-50 px-2 py-1.5 text-amber-700 dark:bg-amber-500/10 dark:text-amber-100">Health<br />{chatHealthScore}%</span>',
        1,
    ),
    (
        '              <span className="rounded-2xl bg-zinc-50 px-2 py-2 text-zinc-600 dark:bg-white/5 dark:text-zinc-300">Files<br />{workspaceFiles.length}</span>',
        '              <span className="rounded-xl bg-zinc-50 px-2 py-1.5 text-zinc-600 dark:bg-white/5 dark:text-zinc-300">Files<br />{workspaceFiles.length}</span>',
        1,
    ),
    (
        '              <span className="rounded-2xl bg-red-50 px-2 py-2 text-red-600 dark:bg-red-500/10 dark:text-red-100">Unread<br />{unreadMessagesCount}</span>',
        '              <span className="rounded-xl bg-red-50 px-2 py-1.5 text-red-600 dark:bg-red-500/10 dark:text-red-100">Unread<br />{unreadMessagesCount}</span>',
        1,
    ),
    (
        'className="flex w-full items-center gap-3 rounded-2xl bg-zinc-50 px-3 py-2 text-right transition hover:bg-amber-50 dark:bg-white/5 dark:hover:bg-amber-500/10"',
        'className="flex w-full items-center gap-2.5 rounded-xl bg-zinc-50 px-2.5 py-1.5 text-right transition hover:bg-amber-50 dark:bg-white/5 dark:hover:bg-amber-500/10"',
        1,
    ),
    (
        '              <div className="mt-4 border-t border-zinc-100 pt-3 dark:border-white/10">',
        '              <div className="mt-3 border-t border-zinc-100 pt-2.5 dark:border-white/10">',
        1,
    ),
    (
        '                <div className="max-h-56 space-y-2 overflow-y-auto pr-1">',
        '                <div className="max-h-52 space-y-1.5 overflow-y-auto pr-1">',
        1,
    ),
    (
        'className="flex w-full items-center gap-3 rounded-2xl border border-zinc-100 bg-white px-3 py-2 text-right transition hover:border-amber-200 hover:bg-amber-50 dark:border-white/10 dark:bg-zinc-950 dark:hover:bg-amber-500/10"',
        'className="flex w-full items-center gap-2.5 rounded-xl border border-zinc-100 bg-white px-2.5 py-1.5 text-right transition hover:border-amber-200 hover:bg-amber-50 dark:border-white/10 dark:bg-zinc-950 dark:hover:bg-amber-500/10"',
        1,
    ),
    (
        '                      <div key={file.id || file.name} className="rounded-2xl border border-zinc-100 bg-zinc-50 p-2 text-xs dark:border-white/10 dark:bg-white/5">',
        '                      <div key={file.id || file.name} className="rounded-xl border border-zinc-100 bg-zinc-50 p-2 text-xs dark:border-white/10 dark:bg-white/5">',
        1,
    ),
    (
        'className="block w-full rounded-2xl bg-emerald-50 px-3 py-2 text-right text-xs text-emerald-900 dark:bg-emerald-500/10 dark:text-emerald-100"',
        'className="block w-full rounded-xl bg-emerald-50 px-2.5 py-1.5 text-right text-xs text-emerald-900 dark:bg-emerald-500/10 dark:text-emerald-100"',
        1,
    ),
    (
        'className="block w-full rounded-2xl bg-amber-50 px-3 py-2 text-right text-xs text-amber-900 dark:bg-amber-500/10 dark:text-amber-100"',
        'className="block w-full rounded-xl bg-amber-50 px-2.5 py-1.5 text-right text-xs text-amber-900 dark:bg-amber-500/10 dark:text-amber-100"',
        1,
    ),
    (
        '              <select value={chatStatus} onChange={(event) => setChatStatus(event.target.value)} className="mb-3 w-full rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-2 text-xs font-black text-zinc-700 outline-none dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200">',
        '              <select value={chatStatus} onChange={(event) => setChatStatus(event.target.value)} className="mb-2.5 w-full rounded-xl border border-zinc-100 bg-zinc-50 px-2.5 py-1.5 text-xs font-black text-zinc-700 outline-none dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200">',
        1,
    ),
    (
        '              <textarea value={internalNote} onChange={(event) => setInternalNote(event.target.value)} rows={7} placeholder="ملاحظات داخلية محفوظة محليًا لهذا الشات فقط..." className="w-full resize-none rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-2 text-xs leading-6 text-zinc-700 outline-none focus:border-amber-300 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200" />',
        '              <textarea value={internalNote} onChange={(event) => setInternalNote(event.target.value)} rows={6} placeholder="ملاحظات داخلية محفوظة محليًا لهذا الشات فقط..." className="w-full resize-none rounded-xl border border-zinc-100 bg-zinc-50 px-2.5 py-2 text-xs leading-6 text-zinc-700 outline-none focus:border-amber-300 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200" />',
        1,
    ),
    (
        '              <div className="mt-2 rounded-2xl bg-zinc-50 px-3 py-2 text-[11px] leading-5 text-zinc-400 dark:bg-white/5">لا يتم إرسال هذه الملاحظات ولا حفظها في قاعدة البيانات.</div>',
        '              <div className="mt-2 rounded-xl bg-zinc-50 px-2.5 py-1.5 text-[10px] leading-5 text-zinc-400 dark:bg-white/5">لا يتم إرسال هذه الملاحظات ولا حفظها في قاعدة البيانات.</div>',
        1,
    ),
    (
        '          {detailsTab === "activity" && (\n            <div className="space-y-2.5">',
        '          {detailsTab === "activity" && (\n            <div className="space-y-2">',
        1,
    ),
    (
        '                    <div key={item.id} className="rounded-2xl bg-zinc-50 px-3 py-2 text-xs text-zinc-600 dark:bg-white/5 dark:text-zinc-300">',
        '                    <div key={item.id} className="rounded-xl bg-zinc-50 px-2.5 py-1.5 text-xs text-zinc-600 dark:bg-white/5 dark:text-zinc-300">',
        1,
    ),
    (
        'className={`block w-full rounded-2xl px-3 py-2 text-right text-xs ${notification.readAt ?',
        'className={`block w-full rounded-xl px-2.5 py-1.5 text-right text-xs ${notification.readAt ?',
        1,
    ),
]

BEHAVIOR_MARKERS = [
    'setDetailsPanelOpen(false)',
    'setDetailsTab(tab.value)',
    'setSelectedProfile(member)',
    'setSelectedDirectUserId(member.id)',
    'api.files.downloadUrl(file.id)',
    'navigator.clipboard?.writeText(url)',
    'scrollToMessage(message.id)',
    'setChatStatus(event.target.value)',
    'setInternalNote(event.target.value)',
    'markNotificationsRead([notification.id])',
    'loadModerationDashboard',
]


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def replace_exact(text, old, new, expected, index):
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f'ANCHOR_{index:02d}_COUNT={count}; expected {expected}')
    return text.replace(old, new)


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: generator.py <repo> <patch-output>')
    repo = Path(sys.argv[1]).resolve()
    patch_path = Path(sys.argv[2]).resolve()

    branch = git(repo, 'branch', '--show-current')
    head = git(repo, 'rev-parse', 'HEAD')
    if branch != 'main':
        raise RuntimeError(f'BRANCH={branch}; expected main')
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f'HEAD={head}; expected {TARGET_BASE_HEAD}')
    if git(repo, 'diff', '--name-only'):
        raise RuntimeError('TRACKED_WORKTREE_NOT_CLEAN')

    target = repo / TARGET_FILE
    before = target.read_text()
    blob = git(repo, 'hash-object', TARGET_FILE)
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f'BLOB={blob}; expected {EXPECTED_BLOB}')

    if before.count(DETAILS_START) != 1:
        raise RuntimeError(f'DETAILS_START_COUNT={before.count(DETAILS_START)}; expected 1')
    if before.count(DETAILS_END) != 1:
        raise RuntimeError(f'DETAILS_END_COUNT={before.count(DETAILS_END)}; expected 1')

    start = before.index(DETAILS_START)
    end = before.index(DETAILS_END, start) + len('      </aside>')
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
        raise RuntimeError('NO_CHANGE')
    if digest(after[:start]) != prefix_hash or digest(after[end + (len(updated) - len(details)):]) != suffix_hash:
        raise RuntimeError('OUTSIDE_DETAILS_SCOPE_CHANGED')

    for marker in BEHAVIOR_MARKERS:
        if before.count(marker) != after.count(marker):
            raise RuntimeError(f'BEHAVIOR_MARKER_CHANGED={marker}')

    for marker in ['api.', 'useChat(', 'useHuddleWebRTC(', 'getSocket(', 'sendMessage(', 'uploadChatFile(', 'deleteChatFile(']:
        if before.count(marker) != after.count(marker):
            raise RuntimeError(f'CALL_COUNT_CHANGED={marker}')

    if any(line.rstrip() != line for line in after.splitlines()):
        raise RuntimeError('TRAILING_WHITESPACE_DETECTED')

    diff = ''.join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True),
        fromfile=f'a/{TARGET_FILE}', tofile=f'b/{TARGET_FILE}'
    ))
    patch = f'diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n' + diff
    patch_path.write_text(patch)

    new_blob = subprocess.check_output(['git', 'hash-object', '--stdin'], input=after, text=True).strip()
    print(f'TARGET_BASE_HEAD={TARGET_BASE_HEAD}')
    print(f'TARGET_FILE={TARGET_FILE}')
    print(f'EXPECTED_BLOB={EXPECTED_BLOB}')
    print(f'NEW_BLOB={new_blob}')
    print(f'PATCH_SHA256={hashlib.sha256(patch.encode()).hexdigest()}')
    print('SOURCE_SCOPE=ONE_FILE')
    print('CHAT_DETAILS_SCOPE=DETAILS_DRAWER_ONLY')
    print('UI12_CHAT_MAIN_CHANGED=NO')
    print('CHAT_BEHAVIOR_CHANGED=NO')
    print('API_CALLS_CHANGED=NO')
    print('CHAT_API_CALLS_CHANGED=NO')
    print('FILE_API_CALLS_CHANGED=NO')
    print('SOCKET_LOGIC_CHANGED=NO')
    print('HUDDLE_LOGIC_CHANGED=NO')
    print('ROUTES_CHANGED=NO')
    print('PERMISSIONS_CHANGED=NO')
    print('BACKEND_INCLUDED=NO')
    print(f'UI12_PREFIX_SHA256={prefix_hash}')
    print(f'UI12_SUFFIX_SHA256={suffix_hash}')
    print(f'DETAILS_BLOCK_BEFORE_SHA256={details_before_hash}')
    print(f'DETAILS_BLOCK_AFTER_SHA256={digest(updated)}')
    print(f'REPLACEMENTS={len(REPLACEMENTS)}')
    print(f'PATCH_PATH={patch_path}')


if __name__ == '__main__':
    main()
