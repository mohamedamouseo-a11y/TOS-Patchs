#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "cc0090ceaed31f3d887808a058ac76d1e5324c3b"
TARGET_FILE = "frontend/src/components/ChatPanel.jsx"
EXPECTED_BLOB = "f6aaec8dcc908b18f3dcf10995eb621b1ba84bcd"

CHAT_PANEL_START = "export function ChatPanel("
CHAT_RETURN_START = '  return (\n    <div ref={chatShellRef}'
DETAILS_START = '      <aside className={`${focusMode || !detailsPanelOpen ?'
DETAILS_FINAL = '      </aside>\n    </div>\n  );\n}'

REPLACEMENTS = [
    (
        '    <div ref={chatShellRef} dir={chatDirection} className={`tos-chat-modern-shell tos-chat-lang-${lang} tos-chat-light-layout-v1124 tos-chat-premium-v113 tos-chat-premium-ux-v114 tos-chat-minimal-v116 tos-chat-declutter-v117 tos-chat-executive-polish-v118 tos-chat-executive-polish-v119 ${focusMode ? "tos-chat-focus-mode" : ""} tos-chat-density-${messageDensity} grid h-full min-h-[640px] overflow-hidden rounded-[28px] border border-zinc-100 bg-zinc-100/80 shadow-sm dark:border-white/10 dark:bg-zinc-950 ${focusMode ? "lg:grid-cols-1 xl:grid-cols-1 2xl:grid-cols-1" : "lg:grid-cols-[230px_minmax(0,1fr)] 2xl:grid-cols-[250px_minmax(0,1fr)]"}`}>',
        '    <div ref={chatShellRef} dir={chatDirection} className={`tos-chat-modern-shell tos-chat-lang-${lang} tos-chat-light-layout-v1124 tos-chat-premium-v113 tos-chat-premium-ux-v114 tos-chat-minimal-v116 tos-chat-declutter-v117 tos-chat-executive-polish-v118 tos-chat-executive-polish-v119 ${focusMode ? "tos-chat-focus-mode" : ""} tos-chat-density-${messageDensity} grid h-full min-h-[600px] overflow-hidden rounded-[24px] border border-zinc-100 bg-zinc-50/90 shadow-[0_12px_36px_rgba(24,24,27,0.06)] dark:border-white/10 dark:bg-zinc-950 ${focusMode ? "lg:grid-cols-1 xl:grid-cols-1 2xl:grid-cols-1" : "lg:grid-cols-[220px_minmax(0,1fr)] 2xl:grid-cols-[236px_minmax(0,1fr)]"}`}>',
        1,
    ),
    (
        '      <aside className={`${focusMode ? "hidden" : "hidden lg:flex"} tos-chat-rail min-h-0 min-w-0 flex-col border-l border-zinc-200 bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-900 text-zinc-100 shadow-inner shadow-black/20`}>',
        '      <aside className={`${focusMode ? "hidden" : "hidden lg:flex"} tos-chat-rail min-h-0 min-w-0 flex-col border-l border-zinc-200 bg-zinc-950 text-zinc-100 shadow-inner shadow-black/10`}>',
        1,
    ),
    (
        '        <div className="border-b border-white/10 p-3 2xl:p-4">',
        '        <div className="border-b border-white/10 p-2.5 2xl:p-3">',
        1,
    ),
    (
        '        <div className="min-h-0 flex-1 overflow-y-auto p-2.5 2xl:p-3">',
        '        <div className="min-h-0 flex-1 overflow-y-auto p-2 2xl:p-2.5">',
        1,
    ),
    (
        '      <section className="tos-chat-main-workspace flex min-h-0 min-w-0 flex-col overflow-hidden bg-white shadow-xl shadow-zinc-200/50 dark:bg-zinc-950 dark:shadow-none">',
        '      <section className="tos-chat-main-workspace flex min-h-0 min-w-0 flex-col overflow-hidden bg-white shadow-sm shadow-zinc-200/40 dark:bg-zinc-950 dark:shadow-none">',
        1,
    ),
    (
        '        <div className="tos-chat-command-center sticky top-0 z-10 border-b border-zinc-100 bg-white/95 px-4 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/95 sm:px-5 sm:py-4">',
        '        <div className="tos-chat-command-center sticky top-0 z-10 border-b border-zinc-100 bg-white/95 px-3 py-2.5 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/95 sm:px-4 sm:py-3">',
        1,
    ),
    (
        '        <div className="tos-chat-command-metrics mt-2 grid gap-2 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات الشات المختصرة">',
        '        <div className="tos-chat-command-metrics mt-1.5 grid gap-1.5 sm:grid-cols-2 xl:grid-cols-4" aria-label="مؤشرات الشات المختصرة">',
        1,
    ),
    (
        '        <div className="tos-chat-v114-dashboard mt-3 grid gap-2 lg:grid-cols-4" aria-label="Premium chat dashboard">',
        '        <div className="tos-chat-v114-dashboard mt-2 grid gap-1.5 lg:grid-cols-4" aria-label="Premium chat dashboard">',
        1,
    ),
    (
        '            <div key={card.label} className={`tos-chat-v114-dashboard-card tos-chat-v114-dashboard-card-${card.tone} rounded-2xl border border-zinc-100 bg-white/75 px-3 py-2.5 shadow-sm dark:border-white/10 dark:bg-white/5`}>',
        '            <div key={card.label} className={`tos-chat-v114-dashboard-card tos-chat-v114-dashboard-card-${card.tone} rounded-xl border border-zinc-100 bg-white/75 px-2.5 py-2 shadow-sm dark:border-white/10 dark:bg-white/5`}>',
        1,
    ),
    (
        '        <div className="tos-chat-v117-brief mt-2 flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-zinc-100 bg-white/70 px-3 py-2 text-[11px] font-black text-zinc-500 shadow-sm dark:border-white/10 dark:bg-white/5 dark:text-zinc-300">',
        '        <div className="tos-chat-v117-brief mt-1.5 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-100 bg-white/70 px-2.5 py-1.5 text-[11px] font-black text-zinc-500 shadow-sm dark:border-white/10 dark:bg-white/5 dark:text-zinc-300">',
        1,
    ),
    (
        '        <div className="tos-chat-v117-filterbar mt-3 rounded-[24px] border border-zinc-100 bg-white/80 p-2.5 shadow-sm dark:border-white/10 dark:bg-zinc-900/60">',
        '        <div className="tos-chat-v117-filterbar mt-2 rounded-[20px] border border-zinc-100 bg-white/80 p-2 shadow-sm dark:border-white/10 dark:bg-zinc-900/60">',
        1,
    ),
    (
        '        <div className="mt-3 flex items-center gap-2 rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-2 shadow-sm transition focus-within:border-amber-300 focus-within:bg-white dark:border-white/10 dark:bg-white/5 dark:focus-within:bg-zinc-900">\n          <Search size={16} className="text-zinc-400" />',
        '        <div className="mt-2 flex items-center gap-2 rounded-xl border border-zinc-100 bg-zinc-50 px-3 py-1.5 shadow-sm transition focus-within:border-amber-300 focus-within:bg-white dark:border-white/10 dark:bg-white/5 dark:focus-within:bg-zinc-900">\n          <Search size={15} className="text-zinc-400" />',
        1,
    ),
    (
        '      <div ref={messagesScrollRef} onScroll={handleMessagesScroll} className={`tos-chat-messages-canvas flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_left,rgba(245,158,11,0.08),transparent_32%),linear-gradient(180deg,#fbfbfa_0%,#f7f7f5_100%)] ${messageDensity === "compact" ? "p-3 sm:p-4" : "p-4 sm:p-6"} dark:bg-zinc-950 ${!loading && filteredMessages.length === 0 ? "grid place-items-start justify-items-center pt-6 sm:pt-8" : messageDensity === "compact" ? "space-y-3" : "space-y-5"}`}>',
        '      <div ref={messagesScrollRef} onScroll={handleMessagesScroll} className={`tos-chat-messages-canvas flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_left,rgba(245,158,11,0.06),transparent_30%),linear-gradient(180deg,#fbfbfa_0%,#f7f7f5_100%)] ${messageDensity === "compact" ? "p-2.5 sm:p-3" : "p-3 sm:p-4"} dark:bg-zinc-950 ${!loading && filteredMessages.length === 0 ? "grid place-items-start justify-items-center pt-4 sm:pt-5" : messageDensity === "compact" ? "space-y-2.5" : "space-y-4"}`}>',
        1,
    ),
    (
        '          <div className="tos-chat-empty-clean-card mx-auto w-full max-w-md rounded-[28px] border border-zinc-100 bg-white p-5 text-center shadow-lg shadow-zinc-200/50 dark:border-white/10 dark:bg-zinc-900 dark:shadow-none sm:p-6">',
        '          <div className="tos-chat-empty-clean-card mx-auto w-full max-w-md rounded-[22px] border border-zinc-100 bg-white p-4 text-center shadow-sm shadow-zinc-200/50 dark:border-white/10 dark:bg-zinc-900 dark:shadow-none sm:p-5">',
        1,
    ),
    (
        '                  <div data-chat-user-content="true" className={`tos-chat-bubble max-h-72 max-w-full overflow-y-auto whitespace-pre-wrap break-words rounded-[24px] border shadow-sm ring-1 ring-black/[0.02] ${messageDensity === "compact" ? "px-3 py-2 text-[13px] leading-6" : "px-4 py-3 text-sm leading-7"} ${message.deletedAt ? "border-zinc-100 bg-zinc-50 text-zinc-400 dark:border-white/10 dark:bg-white/5 dark:text-zinc-500" : isOwner ? "rounded-bl-md border-amber-200 bg-gradient-to-br from-amber-50 to-white text-zinc-800 dark:border-amber-500/20 dark:from-amber-500/15 dark:to-zinc-900 dark:text-zinc-100" : "rounded-br-md border-zinc-100 bg-white text-zinc-700 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200"}`}>',
        '                  <div data-chat-user-content="true" className={`tos-chat-bubble max-h-72 max-w-full overflow-y-auto whitespace-pre-wrap break-words rounded-[20px] border shadow-sm ring-1 ring-black/[0.02] ${messageDensity === "compact" ? "px-3 py-1.5 text-[13px] leading-6" : "px-3.5 py-2.5 text-sm leading-6"} ${message.deletedAt ? "border-zinc-100 bg-zinc-50 text-zinc-400 dark:border-white/10 dark:bg-white/5 dark:text-zinc-500" : isOwner ? "rounded-bl-md border-amber-200 bg-gradient-to-br from-amber-50 to-white text-zinc-800 dark:border-amber-500/20 dark:from-amber-500/15 dark:to-zinc-900 dark:text-zinc-100" : "rounded-br-md border-zinc-100 bg-white text-zinc-700 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200"}`}>',
        1,
    ),
    (
        '        <div className="tos-chat-composer sticky bottom-0 z-20 border-t border-zinc-100 bg-white/95 p-3 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/95 sm:p-4">',
        '        <div className="tos-chat-composer sticky bottom-0 z-20 border-t border-zinc-100 bg-white/95 p-2.5 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/95 sm:p-3">',
        1,
    ),
    (
        '            className={`relative flex items-end gap-2 rounded-[24px] border bg-zinc-50 p-2 shadow-sm ring-1 ring-black/[0.02] transition focus-within:border-amber-300 focus-within:bg-white focus-within:shadow-lg focus-within:shadow-amber-500/10 dark:bg-white/5 dark:focus-within:bg-zinc-900 sm:gap-3 sm:rounded-[26px] ${isDraggingFiles ? "border-amber-300 ring-4 ring-amber-200/60 dark:ring-amber-500/20" : "border-zinc-100 dark:border-white/10"}`}',
        '            className={`relative flex items-end gap-2 rounded-[20px] border bg-zinc-50 p-1.5 shadow-sm ring-1 ring-black/[0.02] transition focus-within:border-amber-300 focus-within:bg-white focus-within:shadow-md focus-within:shadow-amber-500/10 dark:bg-white/5 dark:focus-within:bg-zinc-900 sm:gap-2.5 sm:rounded-[22px] ${isDraggingFiles ? "border-amber-300 ring-4 ring-amber-200/60 dark:ring-amber-500/20" : "border-zinc-100 dark:border-white/10"}`}',
        1,
    ),
]


def run(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def git_blob_sha(text: str) -> str:
    data = text.encode("utf-8")
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_details(text: str) -> str:
    start = text.find(DETAILS_START)
    if start < 0:
        raise RuntimeError("DETAILS_START_NOT_FOUND")
    tail = text.find(DETAILS_FINAL, start)
    if tail < 0:
        raise RuntimeError("DETAILS_FINAL_NOT_FOUND")
    end = tail + len('      </aside>')
    return text[start:end]


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <tos-repo> <output-patch>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = repo / TARGET_FILE

    branch = run(repo, "branch", "--show-current")
    head = run(repo, "rev-parse", "HEAD")
    if branch != "main":
        raise RuntimeError(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"HEAD={head}; expected {TARGET_BASE_HEAD}")

    tracked = run(repo, "diff", "--name-only")
    if tracked:
        raise RuntimeError(f"TRACKED_DIFF_NOT_EMPTY={tracked}")

    original = target.read_text(encoding="utf-8")
    blob = git_blob_sha(original)
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f"TARGET_BLOB={blob}; expected {EXPECTED_BLOB}")

    if CHAT_PANEL_START not in original or CHAT_RETURN_START not in original:
        raise RuntimeError("CHAT_PANEL_BOUNDARY_NOT_FOUND")

    helper_prefix_before = original[:original.index(CHAT_PANEL_START)]
    chat_logic_before = original[original.index(CHAT_PANEL_START):original.index(CHAT_RETURN_START)]
    details_before = extract_details(original)

    api_count_before = original.count("api.")
    chat_api_count_before = original.count("api.chat.")
    file_api_count_before = original.count("api.files.")
    socket_count_before = original.count("getSocket()")
    use_chat_count_before = original.count("useChat({")
    huddle_count_before = original.count("useHuddleWebRTC({")

    updated = original
    applied = 0
    for idx, (old, new, expected_count) in enumerate(REPLACEMENTS, 1):
        count = updated.count(old)
        if count != expected_count:
            raise RuntimeError(f"ANCHOR_{idx:02d}_COUNT={count}; expected {expected_count}")
        updated = updated.replace(old, new, expected_count)
        applied += expected_count

    helper_prefix_after = updated[:updated.index(CHAT_PANEL_START)]
    chat_logic_after = updated[updated.index(CHAT_PANEL_START):updated.index(CHAT_RETURN_START)]
    details_after = extract_details(updated)

    if helper_prefix_after != helper_prefix_before:
        raise RuntimeError("CHAT_HELPERS_CHANGED")
    if chat_logic_after != chat_logic_before:
        raise RuntimeError("CHAT_LOGIC_CHANGED")
    if details_after != details_before:
        raise RuntimeError("CHAT_DETAILS_CHANGED")

    behavior_markers = [
        "sendMessage(",
        "addReaction(",
        "pinMessage(",
        "markDecision(",
        "convertToTask(",
        "editMessage(",
        "deleteMessage(",
        "uploadChatFile(",
        "deleteChatFile(",
        "createChannel(",
        "startMeeting(",
        "loadOlderMessages(",
        "markNotificationsRead(",
        "reloadChannels(",
        "toggleVoiceRecording()",
        "openHuddle()",
        "submit()",
    ]
    for marker in behavior_markers:
        if original.count(marker) != updated.count(marker):
            raise RuntimeError(f"BEHAVIOR_MARKER_CHANGED={marker}")

    if updated.count("api.") != api_count_before:
        raise RuntimeError("API_CALL_COUNT_CHANGED")
    if updated.count("api.chat.") != chat_api_count_before:
        raise RuntimeError("CHAT_API_CALL_COUNT_CHANGED")
    if updated.count("api.files.") != file_api_count_before:
        raise RuntimeError("FILE_API_CALL_COUNT_CHANGED")
    if updated.count("getSocket()") != socket_count_before:
        raise RuntimeError("SOCKET_USAGE_CHANGED")
    if updated.count("useChat({") != use_chat_count_before:
        raise RuntimeError("USE_CHAT_CHANGED")
    if updated.count("useHuddleWebRTC({") != huddle_count_before:
        raise RuntimeError("HUDDLE_HOOK_CHANGED")

    trailing = [i for i, line in enumerate(updated.splitlines(), 1) if line.rstrip(" \t") != line]
    if trailing:
        raise RuntimeError(f"TRAILING_WHITESPACE_LINES={trailing[:20]}")

    if updated == original:
        raise RuntimeError("NO_CHANGES_GENERATED")

    diff_lines = list(difflib.unified_diff(
        original.splitlines(),
        updated.splitlines(),
        fromfile=f"a/{TARGET_FILE}",
        tofile=f"b/{TARGET_FILE}",
        lineterm="",
    ))
    patch = f"diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n" + "\n".join(diff_lines) + "\n"
    output.write_text(patch, encoding="utf-8")

    new_blob = git_blob_sha(updated)
    patch_sha = hashlib.sha256(patch.encode("utf-8")).hexdigest()

    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
    print(f"NEW_BLOB={new_blob}")
    print(f"PATCH_SHA256={patch_sha}")
    print("SOURCE_SCOPE=ONE_FILE")
    print("CHAT_SCOPE=CHAT_MAIN_ONLY")
    print("CHAT_DETAILS_CHANGED=NO")
    print("CHAT_HELPERS_CHANGED=NO")
    print("CHAT_LOGIC_CHANGED=NO")
    print("CHAT_BEHAVIOR_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("CHAT_API_CALLS_CHANGED=NO")
    print("FILE_API_CALLS_CHANGED=NO")
    print("SOCKET_LOGIC_CHANGED=NO")
    print("HUDDLE_LOGIC_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"CHAT_HELPERS_BLOCK_SHA256={sha256_text(helper_prefix_before)}")
    print(f"CHAT_LOGIC_BLOCK_SHA256={sha256_text(chat_logic_before)}")
    print(f"CHAT_DETAILS_BLOCK_SHA256={sha256_text(details_before)}")
    print(f"REPLACEMENTS={applied}")
    print(f"PATCH_PATH={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
