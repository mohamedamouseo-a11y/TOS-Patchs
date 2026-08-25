#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "03a61b7bc84baa8e801ec40f33d24bbaf0969894"
TARGET_FILE = "frontend/src/pages/SlaInboxPage.jsx"
EXPECTED_BLOB = "98644467a39ea41584b1305d6de343b26b7af582"

REPLACEMENTS = [
    ('<div className="p-4 sm:p-6">', '<div className="p-3.5 sm:p-5">', 1),
    ('<div className="mx-auto max-w-7xl space-y-5">', '<div className="mx-auto max-w-7xl space-y-4">', 1),
    ('<div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">', '<div className="flex flex-col gap-2.5 lg:flex-row lg:items-end lg:justify-between">', 1),
    ('<p className="text-xs font-black uppercase tracking-[0.2em] text-amber-600">SLA Operations</p>', '<p className="text-[10px] font-black uppercase tracking-[0.16em] text-amber-600">SLA Operations</p>', 1),
    ('<h1 className="mt-1 text-2xl font-black text-app">', '<h1 className="mt-0.5 text-xl font-black text-app">', 1),
    ('<p className="mt-1 text-sm text-muted">{ar ? "تنبيهات الاختراق والتصعيد والحل الخاصة بك." : "Your SLA breach, escalation, and resolution notifications."}</p>', '<p className="mt-0.5 text-xs text-muted">{ar ? "تنبيهات الاختراق والتصعيد والحل الخاصة بك." : "Your SLA breach, escalation, and resolution notifications."}</p>', 1),
    ('<div className="flex gap-2">', '<div className="flex gap-1.5">', 1),
    ('className="inline-flex items-center gap-2 rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft"', 'className="inline-flex items-center gap-1.5 rounded-lg border border-app px-2.5 py-1.5 text-xs font-bold hover:bg-app-soft"', 1),
    ('className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-3 py-2 text-sm font-black text-zinc-950 disabled:opacity-50"', 'className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-2.5 py-1.5 text-xs font-black text-zinc-950 disabled:opacity-50"', 1),
    ('<div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">', '<div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-4">', 1),
    ('className="rounded-2xl border border-app bg-app-card p-4 shadow-sm"', 'className="rounded-xl border border-app bg-app-card p-3.5 shadow-sm"', 1),
    ('<p className="mt-1 text-3xl font-black text-app">{value}</p>', '<p className="mt-0.5 text-2xl font-black text-app">{value}</p>', 1),
    ('<div className="rounded-xl bg-amber-500/10 p-2.5 text-amber-600"><Icon className="h-5 w-5" /></div>', '<div className="rounded-lg bg-amber-500/10 p-2 text-amber-600"><Icon className="h-4.5 w-4.5" /></div>', 1),
    ('<div className="flex flex-wrap gap-2">', '<div className="flex flex-wrap gap-1.5">', 1),
    ('className={`rounded-full px-4 py-2 text-sm font-bold ${filter === item ? "bg-app text-app-card" : "border border-app bg-app-card text-app"}`}', 'className={`rounded-xl px-3 py-1.5 text-xs font-bold ${filter === item ? "bg-app text-app-card" : "border border-app bg-app-card text-app"}`}', 1),
    ('{error && <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm font-bold text-red-600">{error}</div>}', '{error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 text-xs font-bold text-red-600">{error}</div>}', 1),
    ('<div className="rounded-2xl border border-app bg-app-card p-10 text-center text-sm font-bold text-muted">{ar ? "جارٍ التحميل..." : "Loading..."}</div>', '<div className="rounded-xl border border-app bg-app-card p-7 text-center text-xs font-bold text-muted">{ar ? "جارٍ التحميل..." : "Loading..."}</div>', 1),
    ('<div className="overflow-hidden rounded-2xl border border-app bg-app-card">', '<div className="overflow-hidden rounded-xl border border-app bg-app-card">', 1),
    ('className={`flex flex-col gap-3 border-b border-app p-4 last:border-0 md:flex-row md:items-center md:justify-between ${item.readAt ? "opacity-70" : "bg-amber-500/[0.035]"}`}', 'className={`flex flex-col gap-2.5 border-b border-app p-3.5 last:border-0 md:flex-row md:items-center md:justify-between ${item.readAt ? "opacity-70" : "bg-amber-500/[0.035]"}`}', 1),
    ('className={`rounded-full px-2.5 py-1 text-[11px] font-black ${item.type === "SLA_BREACH" ? "bg-red-500/10 text-red-600" : item.type === "SLA_ESCALATION" ? "bg-amber-500/10 text-amber-700" : "bg-emerald-500/10 text-emerald-600"}`}', 'className={`rounded-lg px-2 py-0.5 text-[10px] font-black ${item.type === "SLA_BREACH" ? "bg-red-500/10 text-red-600" : item.type === "SLA_ESCALATION" ? "bg-amber-500/10 text-amber-700" : "bg-emerald-500/10 text-emerald-600"}`}', 1),
    ('<p className="mt-2 font-black text-app">{item.title}</p>', '<p className="mt-1.5 text-sm font-black text-app">{item.title}</p>', 1),
    ('{item.body && <p className="mt-1 text-sm text-muted">{item.body}</p>}', '{item.body && <p className="mt-0.5 text-xs text-muted">{item.body}</p>}', 1),
    ('<p className="mt-1 text-xs text-muted">{formatWhen(item.createdAt, ar)}</p>', '<p className="mt-0.5 text-[10px] text-muted">{formatWhen(item.createdAt, ar)}</p>', 1),
    ('className="rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft disabled:opacity-50"', 'className="rounded-lg border border-app px-2.5 py-1.5 text-xs font-bold hover:bg-app-soft disabled:opacity-50"', 1),
    ('{!notifications.length && <div className="p-10 text-center text-sm font-bold text-muted">{ar ? "لا توجد تنبيهات في هذا التصنيف." : "No notifications in this queue."}</div>}', '{!notifications.length && <div className="p-7 text-center text-xs font-bold text-muted">{ar ? "لا توجد تنبيهات في هذا التصنيف." : "No notifications in this queue."}</div>}', 1),
]

BEHAVIOR_MARKERS = [
    'request("/api/sla/inbox?limit=250")',
    'request(`/api/users/notifications/${encodeURIComponent(id)}/read`, { method: "PATCH" })',
    'request("/api/sla/inbox/mark-all-read", { method: "POST", body: "{}" })',
    'window.setInterval(() => load({ quiet: true }), 60_000)',
    'setFilter(item)',
    'onClick={markAllRead}',
    'onClick={() => markRead(item.id)}',
    'FILTERS.map((item) => {',
]


def run_git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def git_blob_sha_bytes(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate_ux_ui_phase21_sla_inbox_main.py <repo> <patch-output>")

    repo = Path(sys.argv[1]).resolve()
    patch_path = Path(sys.argv[2]).resolve()
    target = repo / TARGET_FILE

    branch = run_git(repo, "branch", "--show-current")
    head = run_git(repo, "rev-parse", "HEAD")
    if branch != "main":
        raise SystemExit(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD:
        raise SystemExit(f"HEAD={head}; expected {TARGET_BASE_HEAD}")
    if not target.is_file():
        raise SystemExit(f"MISSING_TARGET={TARGET_FILE}")

    before_bytes = target.read_bytes()
    actual_blob = git_blob_sha_bytes(before_bytes)
    if actual_blob != EXPECTED_BLOB:
        raise SystemExit(f"TARGET_BLOB={actual_blob}; expected {EXPECTED_BLOB}")

    tracked = run_git(repo, "diff", "--name-only")
    if tracked:
        raise SystemExit(f"TRACKED_DIFF_NOT_EMPTY={tracked}")

    before = before_bytes.decode("utf-8")
    after = before
    occurrences = 0
    for index, (old, new, expected_count) in enumerate(REPLACEMENTS, 1):
        count = after.count(old)
        if count != expected_count:
            raise SystemExit(f"ANCHOR_{index}_COUNT={count}; expected {expected_count}")
        after = after.replace(old, new)
        occurrences += expected_count

    if after == before:
        raise SystemExit("NO_CHANGES")

    for marker in BEHAVIOR_MARKERS:
        b = before.count(marker)
        a = after.count(marker)
        if b != a:
            raise SystemExit(f"BEHAVIOR_MARKER_CHANGED={marker!r}:{b}->{a}")

    if before.count("request(") != after.count("request("):
        raise SystemExit("API_CALLS_CHANGED")
    if before.count("useEffect(") != after.count("useEffect("):
        raise SystemExit("EFFECT_LOGIC_CHANGED")
    if before.count("useMemo(") != after.count("useMemo("):
        raise SystemExit("FILTER_LOGIC_CHANGED")

    raw_diff = "".join(difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{TARGET_FILE}",
        tofile=f"b/{TARGET_FILE}",
    ))
    if not raw_diff:
        raise SystemExit("EMPTY_PATCH")

    git_header = f"diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n"
    diff = git_header + raw_diff
    if diff.count("diff --git ") != 1:
        raise SystemExit("PATCH_SCOPE_HEADER_COUNT_INVALID")

    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(diff, encoding="utf-8")

    after_bytes = after.encode("utf-8")
    new_blob = git_blob_sha_bytes(after_bytes)

    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
    print("SOURCE_SCOPE=ONE_FILE")
    print("SLA_SCOPE=SLA_INBOX_MAIN_ONLY")
    print("SLA_INBOX_PRESENTATION_CHANGED=YES")
    print("SLA_SUMMARY_PRESENTATION_CHANGED=YES")
    print("SLA_FILTERS_PRESENTATION_CHANGED=YES")
    print("SLA_NOTIFICATION_LIST_PRESENTATION_CHANGED=YES")
    print("SLA_BEHAVIOR_CHANGED=NO")
    print("SLA_MARK_READ_BEHAVIOR_CHANGED=NO")
    print("SLA_MARK_ALL_READ_BEHAVIOR_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("FILTER_LOGIC_CHANGED=NO")
    print("REFRESH_LOGIC_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"REPLACEMENT_ANCHORS={len(REPLACEMENTS)}")
    print(f"REPLACEMENT_OCCURRENCES={occurrences}")
    print(f"SOURCE_BEFORE_SHA256={sha256_text(before)}")
    print(f"SOURCE_AFTER_SHA256={sha256_text(after)}")
    print(f"NEW_BLOB={new_blob}")
    print(f"PATCH_SHA256={hashlib.sha256(diff.encode('utf-8')).hexdigest()}")
    print("PATCH_SCOPE_HEADER_COUNT=1")
    print(f"PATCH_SCOPE_HEADER={git_header.strip()}")
    print(f"PATCH_PATH={patch_path}")


if __name__ == "__main__":
    main()
