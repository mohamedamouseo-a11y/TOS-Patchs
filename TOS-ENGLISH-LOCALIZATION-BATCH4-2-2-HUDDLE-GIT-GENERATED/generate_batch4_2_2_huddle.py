#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "47036c9934aef7b3ef901d182947db70b656a4e2"
TARGET = "frontend/src/hooks/useHuddleWebRTC.js"
EXPECTED_BLOB = "f9cba09631d0bc504f8cde309d9d1260c13922a7"

REPLACEMENTS = [
    (
'''function mediaErrorMessage(error, deviceLabel = "الجهاز") {
  if (isDeviceNotFound(error)) return `لم يتم العثور على ${deviceLabel}. وصّل الجهاز أو فعّله من إعدادات المتصفح ثم جرّب مرة أخرى.`;
  if (error?.name === "NotAllowedError" || error?.name === "PermissionDeniedError") return `تم رفض صلاحية ${deviceLabel}. اسمح للمتصفح باستخدامه ثم حاول مرة أخرى.`;
  if (error?.name === "NotReadableError" || error?.name === "TrackStartError") return `${deviceLabel} مستخدم من برنامج آخر أو غير متاح الآن.`;
  if (error?.name === "SecurityError") return "تشغيل Huddle يحتاج HTTPS وصلاحيات متصفح صحيحة.";
  return error?.message || `تعذر تشغيل ${deviceLabel}.`;
}''',
'''function currentHuddleLang() {
  if (typeof document !== "undefined" && document.documentElement?.lang === "en") return "en";
  try { return window.localStorage.getItem("tamiyouz-language") === "en" ? "en" : "ar"; } catch { return "ar"; }
}

function huddleText(ar, en) {
  return currentHuddleLang() === "en" ? en : ar;
}

function localizedHuddleDeviceLabel(deviceLabel = "الجهاز") {
  if (currentHuddleLang() !== "en") return deviceLabel;
  if (deviceLabel === "الميكروفون") return "microphone";
  if (deviceLabel === "الكاميرا") return "camera";
  if (deviceLabel === "الجهاز") return "device";
  return deviceLabel;
}

function mediaErrorMessage(error, deviceLabel = "الجهاز") {
  const localizedDevice = localizedHuddleDeviceLabel(deviceLabel);
  if (isDeviceNotFound(error)) return huddleText(
    `لم يتم العثور على ${deviceLabel}. وصّل الجهاز أو فعّله من إعدادات المتصفح ثم جرّب مرة أخرى.`,
    `${localizedDevice} was not found. Connect or enable it in browser settings, then try again.`,
  );
  if (error?.name === "NotAllowedError" || error?.name === "PermissionDeniedError") return huddleText(
    `تم رفض صلاحية ${deviceLabel}. اسمح للمتصفح باستخدامه ثم حاول مرة أخرى.`,
    `${localizedDevice} permission was denied. Allow browser access, then try again.`,
  );
  if (error?.name === "NotReadableError" || error?.name === "TrackStartError") return huddleText(
    `${deviceLabel} مستخدم من برنامج آخر أو غير متاح الآن.`,
    `${localizedDevice} is in use by another application or is unavailable right now.`,
  );
  if (error?.name === "SecurityError") return huddleText(
    "تشغيل Huddle يحتاج HTTPS وصلاحيات متصفح صحيحة.",
    "Huddle requires HTTPS and valid browser permissions.",
  );
  return error?.message || huddleText(`تعذر تشغيل ${deviceLabel}.`, `Could not start ${localizedDevice}.`);
}''',
1),
    ('"جاهز للانضمام"', 'huddleText("جاهز للانضمام", "Ready to join")', 2),
    ('setStatus("تعذر الاتصال")', 'setStatus(huddleText("تعذر الاتصال", "Connection failed"))', 1),
    ('throw new Error("المتصفح لا يدعم تشغيل الميكروفون والكاميرا.")', 'throw new Error(huddleText("المتصفح لا يدعم تشغيل الميكروفون والكاميرا.", "This browser does not support microphone and camera access."))', 1),
    ('throw new Error("المتصفح لا يدعم تشغيل Huddle.")', 'throw new Error(huddleText("المتصفح لا يدعم تشغيل Huddle.", "This browser does not support Huddle."))', 1),
    ('throw new Error("المتصفح لا يدعم تشغيل الميكروفون.")', 'throw new Error(huddleText("المتصفح لا يدعم تشغيل الميكروفون.", "This browser does not support microphone access."))', 1),
    ('throw new Error("المتصفح لا يدعم تشغيل الكاميرا.")', 'throw new Error(huddleText("المتصفح لا يدعم تشغيل الكاميرا.", "This browser does not support camera access."))', 1),
    ('reportError("تعذر إنشاء اتصال Huddle مع أحد المشاركين.")', 'reportError(huddleText("تعذر إنشاء اتصال Huddle مع أحد المشاركين.", "Could not establish a Huddle connection with a participant."))', 1),
    ('reportError("اختر محادثة صحيحة قبل فتح Huddle.")', 'reportError(huddleText("اختر محادثة صحيحة قبل فتح Huddle.", "Choose a valid conversation before opening Huddle."))', 1),
    ('setStatus("طلب صلاحية الميكروفون...")', 'setStatus(huddleText("طلب صلاحية الميكروفون...", "Requesting microphone permission..."))', 1),
    ('reportError(`${mediaErrorMessage(error, "الميكروفون")} تم الانضمام بدون ميكروفون.`, { blocking: false })', 'reportError(`${mediaErrorMessage(error, "الميكروفون")} ${huddleText("تم الانضمام بدون ميكروفون.", "Joined without a microphone.")}`, { blocking: false })', 1),
    ('setStatus(joinMicOn ? "جاري الاتصال..." : "جاري الاتصال بدون ميكروفون...")', 'setStatus(joinMicOn ? huddleText("جاري الاتصال...", "Connecting...") : huddleText("جاري الاتصال بدون ميكروفون...", "Connecting without a microphone..."))', 1),
    ('reportError("المتصفح لا يدعم مشاركة الشاشة.")', 'reportError(huddleText("المتصفح لا يدعم مشاركة الشاشة.", "This browser does not support screen sharing."))', 1),
    ('setStatus("جاري بدء مشاركة الشاشة...")', 'setStatus(huddleText("جاري بدء مشاركة الشاشة...", "Starting screen share..."))', 1),
    ('throw new Error("تعذر الحصول على شاشة للمشاركة.")', 'throw new Error(huddleText("تعذر الحصول على شاشة للمشاركة.", "Could not obtain a screen to share."))', 1),
    ('setStatus("متصل الآن")', 'setStatus(huddleText("متصل الآن", "Connected now"))', 2),
    ('? "تم رفض صلاحية مشاركة الشاشة. اسمح للمتصفح بالمشاركة ثم حاول مرة أخرى."\n        : (error?.message || "تعذر بدء مشاركة الشاشة.")', '? huddleText("تم رفض صلاحية مشاركة الشاشة. اسمح للمتصفح بالمشاركة ثم حاول مرة أخرى.", "Screen-sharing permission was denied. Allow browser sharing, then try again.")\n        : (error?.message || huddleText("تعذر بدء مشاركة الشاشة.", "Could not start screen sharing."))', 1),
    ('reportError(message || "تعذر الاتصال بالـ Huddle.")', 'reportError(message || huddleText("تعذر الاتصال بالـ Huddle.", "Could not connect to Huddle."))', 1),
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
        die("usage: generate_batch4_2_2_huddle.py REPO_ROOT OUTPUT_PATCH", 2)

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

    tmp = Path(tempfile.mkdtemp(prefix="tos-batch4-2-2-huddle-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "batch4-2-2@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Batch 4.2.2 Generator"], tmp)

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
        print("BATCH4_2_2_HUDDLE_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
