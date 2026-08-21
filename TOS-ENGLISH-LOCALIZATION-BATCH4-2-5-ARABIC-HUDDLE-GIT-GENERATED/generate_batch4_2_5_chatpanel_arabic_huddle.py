#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "ba9cffdc9e02d85bd53a4e945e711fade6521aeb"
TARGET = "frontend/src/components/ChatPanel.jsx"
EXPECTED_BLOB = "c9a999b04e7ecff208b639c8284e88fa77cf9eae"

REPLACEMENTS = [
    (
        '  const statusLabel = connectionStatus || (joined ? "متصل الآن" : "جاهز للانضمام");',
        '''  const huddleLang = currentChatLang();
  const statusLabel = ["Ready to join", "جاهز للانضمام"].includes(connectionStatus)
    ? (huddleLang === "en" ? "Ready to join" : "جاهز للانضمام")
    : (connectionStatus || (joined
      ? (huddleLang === "en" ? "Connected now" : "متصل الآن")
      : (huddleLang === "en" ? "Ready to join" : "جاهز للانضمام")));''',
        1,
    ),
    (
        '''                  <div className="text-[11px] text-zinc-400">{joined ? `${micOn ? "الميكروفون يعمل" : "الميكروفون مكتوم"}${screenOn ? " · مشاركة شاشة" : cameraOn ? " · كاميرا" : ""}` : "لم ينضم بعد"}</div>''',
        '''                  <div className="text-[11px] text-zinc-400">{joined ? `${micOn ? "الميكروفون يعمل" : "الميكروفون مكتوم"}${screenOn ? " · مشاركة شاشة" : cameraOn ? " · كاميرا" : ""}` : (huddleLang === "en" ? "Not joined yet" : "لم ينضم بعد")}</div>''',
        1,
    ),
    (
        '''                <Phone size={17} /> Join Huddle''',
        '''                <Phone size={17} /> {huddleLang === "en" ? "Join Huddle" : "انضم إلى Huddle"}''',
        1,
    ),
]


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if check and proc.returncode:
        die(f"command failed rc={proc.returncode}: {' '.join(args)}", 90)
    return proc


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 3:
        die("usage: generate_batch4_2_5_chatpanel_arabic_huddle.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET

    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)
    if not target.is_file():
        die(f"target missing: {TARGET}", 4)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 5)

    blob = run(["git", "hash-object", TARGET], root).stdout.strip()
    print(f"SOURCE_BLOB={blob}")
    if blob != EXPECTED_BLOB:
        die(f"blob mismatch expected={EXPECTED_BLOB} actual={blob}", 6)

    if run(["git", "diff", "--cached", "--", TARGET], root).stdout.strip():
        die("target has staged changes", 7)
    if run(["git", "diff", "--", TARGET], root).stdout.strip():
        die("target has tracked local changes", 8)
    print("TARGET_CLEAN=YES")

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF source detected", 9)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    for index, (old, new, expected_count) in enumerate(REPLACEMENTS, start=1):
        count = text.count(old)
        print(f"REPLACEMENT_{index}_MATCHES={count}")
        if count != expected_count:
            die(f"replacement {index} expected {expected_count} exact matches, found {count}", 20 + index)
        text = text.replace(old, new)

    tmp = Path(tempfile.mkdtemp(prefix="tos-batch4-2-5-huddle-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "batch4-2-5@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Batch 4.2.5 Generator"], tmp)

        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)

        encoded = text.encode("utf-8")
        if terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        proc = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", TARGET],
            cwd=tmp,
            text=True,
            capture_output=True,
        )
        if proc.returncode:
            if proc.stderr:
                print(proc.stderr, end="", file=sys.stderr)
            die(f"git diff failed rc={proc.returncode}", 50)
        if not proc.stdout.strip():
            die("generated patch is empty", 51)

        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if parsed_paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 52)
        print("PARSER=PASS")

        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_SOURCE")
        print("BATCH4_2_5_ARABIC_HUDDLE_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
