#!/usr/bin/env python3
import hashlib, shutil, subprocess, sys, tempfile
from pathlib import Path

EXPECTED_HEAD = "e022b2071363010a5113e56478c6dbed71e44a2e"
TARGET = "frontend/src/components/ChatPanel.jsx"
EXPECTED_BLOB = "c94ff3840b22f39fa05fc2e3b841c87c0845fffd"

REPLACEMENTS = [
(
'''function UserProfileCard({ user, currentUserId = "", summary = null, avatarUploading = false, onAvatarFile = null, onClose }) {
  if (!user) return null;''',
'''function UserProfileCard({ user, currentUserId = "", summary = null, avatarUploading = false, onAvatarFile = null, onClose }) {
  const { lang } = usePreferences();
  if (!user) return null;'''
),
(
'''{user.lastSeenAt ? new Date(user.lastSeenAt).toLocaleString("ar-EG") : "غير متاح"}''',
'''{user.lastSeenAt ? new Date(user.lastSeenAt).toLocaleString(chatLocale(lang)) : "غير متاح"}'''
),
(
'''{item.createdAt && <span className="block text-[10px] opacity-60">{new Date(item.createdAt).toLocaleString("ar-EG")}</span>}''',
'''{item.createdAt && <span className="block text-[10px] opacity-60">{new Date(item.createdAt).toLocaleString(chatLocale(lang))}</span>}'''
),
(
'''const CHAT_EN_TEXT_MAP = new Map(Object.entries({
  "عرض بيانات المستخدم": "View user profile",''',
'''const CHAT_EN_TEXT_MAP = new Map(Object.entries({
  "التفاصيل": "Details",
  "بحث متقدم": "Advanced search",
  "نسخ Brief": "Copy brief",
  "ملخص التفاصيل": "Details summary",
  "الجاهزية": "Readiness",
  "فتح لوحة التفاصيل كاملة": "Open full details panel",
  "آخر الملفات": "Latest files",
  "آخر رسالة:": "Latest message:",
  "الحالة": "Status",
  "الأعضاء": "Members",
  "عرض بيانات المستخدم": "View user profile",'''
),
]

def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr); raise SystemExit(code)

def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if p.stdout: print(p.stdout, end="")
    if p.stderr: print(p.stderr, end="", file=sys.stderr)
    if check and p.returncode: die(f"command failed rc={p.returncode}: {' '.join(args)}", 90)
    return p

def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    if len(sys.argv) != 3: die("usage: generate_batch4_1_chat.py REPO_ROOT OUTPUT_PATCH", 2)
    root = Path(sys.argv[1]).resolve(); output = Path(sys.argv[2]).resolve(); target = root / TARGET
    if not (root / ".git").is_dir(): die("not a git repo", 3)
    if not target.is_file(): die("target missing", 4)
    head = run(["git","rev-parse","HEAD"], root).stdout.strip(); print(f"HEAD={head}")
    if head != EXPECTED_HEAD: die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 5)
    blob = run(["git","hash-object",TARGET], root).stdout.strip(); print(f"SOURCE_BLOB={blob}")
    if blob != EXPECTED_BLOB: die(f"blob mismatch expected={EXPECTED_BLOB} actual={blob}", 6)
    if run(["git","diff","--cached","--",TARGET], root).stdout.strip(): die("target staged", 7)
    if run(["git","diff","--",TARGET], root).stdout.strip(): die("target dirty", 8)
    print("TARGET_CLEAN=YES")
    raw = target.read_bytes()
    if b"\r\n" in raw: die("CRLF detected", 9)
    text = raw.decode("utf-8"); terminal = raw.endswith(b"\n")
    for i,(old,new) in enumerate(REPLACEMENTS,1):
        c=text.count(old); print(f"REPLACEMENT_{i}_MATCHES={c}")
        if c != 1: die(f"replacement {i} expected 1 match, found {c}", 20+i)
        text=text.replace(old,new,1)
    tmp=Path(tempfile.mkdtemp(prefix="tos-batch4-1-chat-"))
    try:
        run(["git","init","-q"],tmp); run(["git","config","user.email","batch4-1@tos.local"],tmp); run(["git","config","user.name","TOS Batch 4.1"],tmp)
        t=tmp/TARGET; t.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(target,t)
        run(["git","add","--",TARGET],tmp); run(["git","commit","-qm","exact live baseline"],tmp)
        enc=text.encode("utf-8")
        if terminal and not enc.endswith(b"\n"): enc += b"\n"
        if not terminal and enc.endswith(b"\n"): enc = enc[:-1]
        t.write_bytes(enc)
        diff=subprocess.run(["git","diff","--binary","--full-index","--",TARGET],cwd=tmp,text=True,capture_output=True)
        if diff.returncode or not diff.stdout.strip(): die("git diff failed/empty", 40)
        output.write_text(diff.stdout,encoding="utf-8",newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")
        paths={r.split("\t")[-1] for r in run(["git","apply","--numstat",str(output)],root).stdout.splitlines() if r.strip()}
        if paths != {TARGET}: die(f"unexpected paths {sorted(paths)}", 41)
        print("PARSER=PASS"); run(["git","apply","--check",str(output)],root); print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_SOURCE"); print("BATCH4_1_CHAT_GENERATOR=PASS")
    finally: shutil.rmtree(tmp,ignore_errors=True)

if __name__ == "__main__": main()
