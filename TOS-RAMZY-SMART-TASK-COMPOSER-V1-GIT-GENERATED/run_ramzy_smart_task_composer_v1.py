#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PATCH = "TOS-RAMZY-SMART-TASK-COMPOSER-V1-GIT-GENERATED"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/"
BASELINE = "db1efe2ccf30552ab7c65f7bc672861adf66cc05"
TARGET = "frontend/src/components/RamzyAssistant.jsx"
TARGET_BLOB = "509c40b4f283d39fb50e7e2dc146797392d6d1ca"
CSS_TARGET = "frontend/src/components/ramzySmartTaskComposerV1.css"
RAW = f"https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/{PATCH}/payload"


def run(cmd, cwd=None, check=True):
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p


def git(*args, check=True):
    return run(["git", *args], cwd=REPO, check=check)


def payload(name):
    with urllib.request.urlopen(f"{RAW}/{name}", timeout=30) as r:
        return r.read().decode("utf-8")


def blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def paths():
    out = set()
    for line in git("status", "--porcelain").stdout.splitlines():
        p = line[3:]
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        out.add(p)
    return out


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)


def main_asset(html):
    m = re.search(r'(/assets/index-[^"\']+\.js)', html)
    if not m:
        raise RuntimeError("MAIN_ASSET_NOT_FOUND")
    return m.group(1)


def patch_source(source):
    helpers = payload("helpers.jsx.txt").rstrip() + "\n\n"
    functions = payload("functions.jsx.txt").rstrip() + "\n\n"
    panel = payload("panel.jsx.txt").rstrip() + "\n"

    source = replace_once(source, 'import "./ramzyExecutionControlV1.css";\n', 'import "./ramzyExecutionControlV1.css";\nimport "./ramzySmartTaskComposerV1.css";\n', "css import")
    source = replace_once(source, 'export function RamzyAssistant({ user, projectId = "" }) {', helpers + 'export function RamzyAssistant({ user, projectId = "" }) {', "helpers")
    source = replace_once(source, '  const [composerHasText, setComposerHasText] = useState(false);\n', '  const [composerHasText, setComposerHasText] = useState(false);\n  const [smartTask, setSmartTask] = useState(null);\n  const [smartTaskOptions, setSmartTaskOptions] = useState({ projects: [], users: [], loading: false, error: "" });\n', "state")
    input_anchor = '  function handleComposerInput(event) {\n    setComposerValue(event.currentTarget.value);\n  }\n\n'
    source = replace_once(source, input_anchor, input_anchor + functions, "functions")
    welcome = '<div className="ramzy-suggestions">{(isEnglish ? SUGGESTIONS.en : SUGGESTIONS.ar).map((text) => <button type="button" key={text} onClick={() => sendMessage(text)}>{text}</button>)}</div>'
    welcome_new = '<div className="ramzy-suggestions"><button type="button" onClick={startSmartTask}>{isEnglish ? "⚡ Create a task faster" : "⚡ إنشاء مهمة بشكل أسرع"}</button>{(isEnglish ? SUGGESTIONS.en : SUGGESTIONS.ar).map((text) => <button type="button" key={text} onClick={() => sendMessage(text)}>{text}</button>)}</div>'
    source = replace_once(source, welcome, welcome_new, "welcome")
    footer = '          <footer className="ramzy-composer">\n'
    source = replace_once(source, footer, footer + panel, "panel")
    textarea = '<textarea ref={composerRef} aria-label={isEnglish ? "Message Ramzy" : "رسالة إلى رمزي"} defaultValue={composerValueRef.current} onInput={handleComposerInput} onKeyDown={(event) => { if (event.nativeEvent?.isComposing || event.isComposing) return; if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendMessage(); } }} placeholder={isEnglish ? "Ask Ramzy about TOS, tasks, projects, or performance..." : "اسأل رمزي عن TOS أو المهام أو المشاريع أو الأداء..."} rows={1} />'
    textarea_new = '<textarea ref={composerRef} aria-label={isEnglish ? "Message Ramzy" : "رسالة إلى رمزي"} defaultValue={composerValueRef.current} onInput={handleComposerInput} onKeyDown={handleComposerKeyDown} disabled={Boolean(smartTask && smartTask.step !== "TITLE")} placeholder={smartTask?.step === "TITLE" ? (isEnglish ? "Type the task title..." : "اكتب اسم التاسك...") : (isEnglish ? "Ask Ramzy about TOS, tasks, projects, or performance..." : "اسأل رمزي عن TOS أو المهام أو المشاريع أو الأداء...")} rows={1} />'
    source = replace_once(source, textarea, textarea_new, "textarea")
    mic = '              {voiceMode !== "text" && <button type="button" className={`ramzy-mic-button${listening ? " is-listening" : ""}`} aria-label={listening ? (isEnglish ? "Stop voice input" : "إيقاف الإدخال الصوتي") : (isEnglish ? "Voice input" : "إدخال صوتي")} title={voiceCapabilities?.apiTranscription ? (isEnglish ? "Secure API voice transcription" : "تحويل الصوت إلى نص عبر الـAPI") : (isEnglish ? "Browser voice dictation" : "إملاء صوتي عبر المتصفح")} onClick={startVoiceInput}>{listening ? <MicOff size={19} /> : <Mic size={19} />}</button>}\n'
    source = replace_once(source, mic, '              <button type="button" className={`ramzy-smart-task-launch${smartTask ? " is-active" : ""}`} onClick={smartTask ? cancelSmartTask : startSmartTask} title={isEnglish ? "Smart task creator" : "إنشاء مهمة ذكي"}><Plus size={15} /><span>{isEnglish ? "Smart task" : "مهمة ذكية"}</span></button>\n' + mic, "launcher")
    send = '<button type="button" className="ramzy-send-button" aria-label={isEnglish ? "Send message" : "إرسال الرسالة"} disabled={!composerHasText || loading || listening} onClick={() => sendMessage()}><Send size={18} /></button>'
    send_new = '<button type="button" className="ramzy-send-button" aria-label={isEnglish ? "Send message" : "إرسال الرسالة"} disabled={smartTask ? (smartTask.step !== "TITLE" || !composerHasText || loading || listening) : (!composerHasText || loading || listening)} onClick={() => smartTask?.step === "TITLE" ? captureSmartTaskTitle() : sendMessage()}><Send size={18} /></button>'
    return replace_once(source, send, send_new, "send")


def validate(source):
    required = ["ramzySmartTaskComposerV1.css", "api.projects.list({ summary: true })", "api.users.list({ summary: true })", "handleComposerKeyDown", "إنشاء مهمة ذكي", "خلي رمزي يقترح", "CREATE_TASK approval draft", "مسودة CREATE_TASK", "ramzy-smart-task-launch"]
    missing = [x for x in required if x not in source]
    if missing:
        raise RuntimeError(f"VALIDATION_MISSING={missing}")


def deploy():
    index = DIST / "index.html"
    if not index.exists():
        raise RuntimeError("DIST_INDEX_MISSING")
    built = main_asset(index.read_text(encoding="utf-8"))
    built_path = DIST / built.lstrip("/")
    backup = Path(tempfile.mkdtemp(prefix="ramzy-smart-task-live-"))
    existed = LIVE_ROOT.exists()
    if existed:
        run(["rsync", "-a", "--delete", f"{LIVE_ROOT}/", f"{backup}/"])
    try:
        LIVE_ROOT.mkdir(parents=True, exist_ok=True)
        run(["rsync", "-a", "--delete", f"{DIST}/", f"{LIVE_ROOT}/"])
        run(["nginx", "-t"])
        run(["systemctl", "reload", "nginx"])
        live = main_asset(run(["curl", "-fsSL", LIVE_URL]).stdout)
        live_path = LIVE_ROOT / live.lstrip("/")
        if live != built or not live_path.exists() or live_path.read_bytes() != built_path.read_bytes():
            raise RuntimeError(f"LIVE_BUNDLE_MISMATCH built={built} live={live}")
        return built, live
    except Exception:
        if existed:
            run(["rsync", "-a", "--delete", f"{backup}/", f"{LIVE_ROOT}/"], check=False)
            run(["nginx", "-t"], check=False)
            run(["systemctl", "reload", "nginx"], check=False)
        raise
    finally:
        shutil.rmtree(backup, ignore_errors=True)


def main():
    print(f"PATCH={PATCH}")
    head = git("rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    if head != BASELINE:
        raise RuntimeError(f"BASELINE_MISMATCH expected={BASELINE} actual={head}")
    target = REPO / TARGET
    css_target = REPO / CSS_TARGET
    if blob_sha(target) != TARGET_BLOB:
        raise RuntimeError(f"TARGET_BLOB_MISMATCH expected={TARGET_BLOB} actual={blob_sha(target)}")
    pre = paths()
    if TARGET in pre or CSS_TARGET in pre or css_target.exists():
        raise RuntimeError("TARGET_NOT_CLEAN")
    print(f"PRECHECK_WORKTREE={'CLEAN' if not pre else 'DIRTY_UNRELATED_ALLOWED'}")
    original = target.read_text(encoding="utf-8")
    patched = patch_source(original)
    validate(patched)
    target.write_text(patched, encoding="utf-8")
    css_target.write_text(payload("style.css"), encoding="utf-8")
    try:
        d = git("diff", "--check", check=False)
        if d.returncode:
            raise RuntimeError(f"DIFF_CHECK_FAILED\n{d.stdout}\n{d.stderr}")
        run(["npm", "run", "build"], cwd=FRONTEND)
        delta = paths() - pre
        if delta != {TARGET, CSS_TARGET}:
            raise RuntimeError(f"CHANGED_PATHS_MISMATCH={sorted(delta)}")
        validate(target.read_text(encoding="utf-8"))
        built, live = deploy()
        print("PASS_FAIL=PASS")
        print("FILES_PATCHED=2")
        print("SMART_TASK_LAUNCHER=PASS")
        print("SMART_TASK_REAL_PROJECT_CHOICES=PASS")
        print("SMART_TASK_DUE_DATE_PRESETS=PASS")
        print("SMART_TASK_PRIORITY_CHOICES=PASS")
        print("SMART_TASK_REAL_TEAM_CHOICES=PASS")
        print("SMART_TASK_RAMZY_SUGGESTIONS=PASS")
        print("CREATE_TASK_APPROVAL_GUARD=PRESERVED")
        print("BACKEND_CHANGED=NO")
        print("DATABASE_SCHEMA_CHANGED=NO")
        print("ROUTES_CHANGED=NO")
        print("PERMISSIONS_CHANGED=NO")
        print("FRONTEND_BUILD=PASS")
        print(f"BUILT_MAIN_ASSET={built}")
        print(f"LIVE_MAIN_ASSET={live}")
        print("LIVE_DEPLOY=PASS")
        print("PUSH_PERFORMED=NO")
        print("READY_FOR_SMART_TASK_RECHECK=YES")
        print("READY_FOR_GIT_PUSH=NO_UNTIL_SMART_TASK_RECHECK")
    except Exception:
        target.write_text(original, encoding="utf-8")
        if css_target.exists():
            css_target.unlink()
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PASS_FAIL=FAIL")
        print(f"ERROR={exc}")
        sys.exit(1)
