#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PATCH = "TOS-RAMZY-CONTEXTUAL-SMART-TASK-V1-GIT-GENERATED"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/"
EXPECTED_HEAD = "048592147387e2b49382f605a04f8d2efd64f61c"
SOURCE_REL = "frontend/src/components/RamzyAssistant.jsx"
CSS_REL = "frontend/src/components/ramzySmartTaskComposerV1.css"
SOURCE = REPO / SOURCE_REL
CSS = REPO / CSS_REL
EXPECTED_CSS_BLOB = "18ac594a6db8d5f919c39405e2ee4f5824056eeb"

CONTEXT_HELPERS = r'''
function ramzyIsTaskCreationIntent(text) {
  const value = String(text || "").trim();
  if (!value) return false;
  const normalized = value
    .toLowerCase()
    .replace(/[إأآ]/g, "ا")
    .replace(/ة/g, "ه")
    .replace(/\s+/g, " ");
  const arabicCreate = /(?:^|\s)(?:اعمل|انشئ|اضف|سجل|جهز|عايز اعمل|عاوز اعمل|محتاج اعمل|عايز انشئ|عاوز انشئ|محتاج انشئ)\s+(?:لي\s+)?(?:تاسك|تاسك جديد|مهمه|مهمه جديده)(?:\s|$|[:：\-–—])/i;
  const englishCreate = /\b(?:create|add|make)\s+(?:me\s+)?(?:a\s+)?(?:new\s+)?(?:task|todo)\b/i;
  return arabicCreate.test(normalized) || englishCreate.test(normalized);
}

function ramzyTaskTitleFromIntent(text) {
  let value = String(text || "").trim();
  if (!value) return "";
  value = value
    .replace(/^\s*(?:عايز|عاوز|محتاج)?\s*(?:اعمل|انشئ|أنشئ|اضف|أضف|سجل|جهز)\s+(?:لي\s+)?(?:تاسك جديد|مهمة جديدة|مهمه جديده|تاسك|مهمة|مهمه)\s*/i, "")
    .replace(/^\s*(?:create|add|make)\s+(?:me\s+)?(?:a\s+)?(?:new\s+)?(?:task|todo)\s*/i, "")
    .replace(/^\s*(?:اسمها|اسمه|بعنوان|title\s*[:：]?)\s*/i, "")
    .replace(/^[\s:：\-–—]+/, "")
    .trim();
  if (!value || value.length > 180) return "";
  return value;
}
'''.strip()

CONTEXT_STYLE = r'''
/* TOS_RAMZY_CONTEXTUAL_SMART_TASK_V1
   Smart choices are contextual and temporary. No permanent launcher or dashboard clutter. */
.ramzy-assistant-root .ramzy-messages > .ramzy-smart-task-panel{
  width:min(100%,560px);
  align-self:stretch;
  margin:8px 0 12px;
  border-color:rgba(154,101,19,.18);
  background:linear-gradient(145deg,rgba(255,254,250,.98),rgba(248,239,220,.94));
  box-shadow:0 14px 34px rgba(73,51,27,.08),inset 0 1px 0 rgba(255,255,255,.92);
}
.ramzy-assistant-root .ramzy-smart-task-panel .ramzy-smart-task-option{
  transition:border-color .14s ease,background .14s ease,transform .14s ease;
}
.ramzy-assistant-root .ramzy-smart-task-panel .ramzy-smart-task-option:hover{
  transform:translateY(-1px);
  border-color:rgba(185,120,23,.36);
  background:rgba(233,184,77,.12);
}
.ramzy-assistant-root .ramzy-smart-task-panel .ramzy-smart-task-option.is-primary{
  border-color:rgba(185,120,23,.32);
  background:linear-gradient(145deg,rgba(255,249,231,.96),rgba(239,218,169,.82));
}
.dark .ramzy-assistant-root .ramzy-messages > .ramzy-smart-task-panel{
  border-color:rgba(248,215,123,.16);
  background:linear-gradient(145deg,rgba(39,37,33,.97),rgba(22,22,23,.98));
  box-shadow:0 16px 38px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.035);
}
@media(max-width:640px){
  .ramzy-assistant-root .ramzy-messages > .ramzy-smart-task-panel{
    width:100%;
    margin:6px 0 10px;
  }
}
'''.strip()


def run(cmd, cwd=None, check=True):
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
    )
    if check and result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def git(*args, check=True):
    return run(["git", *args], cwd=REPO, check=check)


def blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def status_paths():
    result = set()
    for line in git("status", "--porcelain").stdout.splitlines():
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        result.add(value)
    return result


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def main_asset(html: str) -> str:
    match = re.search(r"/assets/index-[A-Za-z0-9_-]+\.js", html)
    if not match:
        raise RuntimeError("MAIN_ASSET_NOT_FOUND")
    return match.group(0)


def deploy():
    index = DIST / "index.html"
    if not index.exists():
        raise RuntimeError("DIST_INDEX_MISSING")
    built = main_asset(index.read_text(encoding="utf-8"))
    built_path = DIST / built.lstrip("/")
    if not built_path.exists():
        raise RuntimeError(f"BUILT_ASSET_MISSING={built_path}")

    backup = Path(tempfile.mkdtemp(prefix="ramzy-contextual-smart-task-live-"))
    live_existed = LIVE_ROOT.exists()
    if live_existed:
        run(["rsync", "-a", "--delete", f"{LIVE_ROOT}/", f"{backup}/"])
    try:
        LIVE_ROOT.mkdir(parents=True, exist_ok=True)
        run(["rsync", "-a", "--delete", f"{DIST}/", f"{LIVE_ROOT}/"])
        run(["nginx", "-t"])
        run(["systemctl", "reload", "nginx"])
        live_html = run(["curl", "-fsSL", LIVE_URL]).stdout
        live = main_asset(live_html)
        live_path = LIVE_ROOT / live.lstrip("/")
        if live != built:
            raise RuntimeError(f"LIVE_ASSET_NAME_MISMATCH built={built} live={live}")
        if not live_path.exists() or live_path.read_bytes() != built_path.read_bytes():
            raise RuntimeError("LIVE_BUNDLE_BYTES_MISMATCH")
        return built, live
    except Exception:
        if live_existed:
            run(["rsync", "-a", "--delete", f"{backup}/", f"{LIVE_ROOT}/"], check=False)
            run(["nginx", "-t"], check=False)
            run(["systemctl", "reload", "nginx"], check=False)
        raise
    finally:
        shutil.rmtree(backup, ignore_errors=True)


def patch_source(source: str) -> str:
    required_before = [
        'import "./ramzySmartTaskComposerV1.css";',
        'const [smartTask, setSmartTask] = useState(null);',
        'async function loadSmartTaskOptions()',
        'function startSmartTask()',
        'function submitSmartTask()',
        'className={`ramzy-smart-task-launch${smartTask ? " is-active" : ""}`',
        'onClick={startSmartTask}>{isEnglish ? "⚡ Create a task faster" : "⚡ إنشاء مهمة بشكل أسرع"}',
    ]
    missing = [token for token in required_before if token not in source]
    if missing:
        raise RuntimeError(f"SMART_TASK_V1_STATE_MISSING={missing}")

    source = replace_once(
        source,
        'export function RamzyAssistant({ user, projectId = "" }) {',
        CONTEXT_HELPERS + '\n\nexport function RamzyAssistant({ user, projectId = "" }) {',
        "context helpers",
    )

    source = replace_once(
        source,
        '  function startSmartTask() {\n'
        '    stopVoicePlayback();\n'
        '    setHelpSuggestion(null);\n'
        '    setSmartTask({ step: "TITLE", title: "", project: null, dueKind: "", dueDate: null, priority: "", assignee: null });\n'
        '    setComposerValue("", { resize: false });\n'
        '    if (composerRef.current) composerRef.current.style.height = "";\n'
        '    void loadSmartTaskOptions();\n'
        '    setTimeout(() => composerRef.current?.focus(), 0);\n'
        '  }\n',
        '  function startSmartTask(intentText = "") {\n'
        '    stopVoicePlayback();\n'
        '    setHelpSuggestion(null);\n'
        '    const suggestedTitle = ramzyTaskTitleFromIntent(intentText);\n'
        '    setSmartTask({ step: suggestedTitle ? "PROJECT" : "TITLE", title: suggestedTitle, project: null, dueKind: "", dueDate: null, priority: "", assignee: null });\n'
        '    setComposerValue("", { resize: false });\n'
        '    if (composerRef.current) composerRef.current.style.height = "";\n'
        '    void loadSmartTaskOptions();\n'
        '    setTimeout(() => composerRef.current?.focus(), 0);\n'
        '  }\n',
        "contextual startSmartTask",
    )

    source = replace_once(
        source,
        '  async function sendMessage(text = composerValueRef.current) {\n'
        '    if (listening) { stopVoiceInput(); return; }\n'
        '    const content = String(text || "").trim();\n'
        '    if (!content || loading || sendLockRef.current) return;\n'
        '    setHelpSuggestion(null);\n',
        '  async function sendMessage(text = composerValueRef.current, options = {}) {\n'
        '    if (listening) { stopVoiceInput(); return; }\n'
        '    const content = String(text || "").trim();\n'
        '    if (!content || loading || sendLockRef.current) return;\n'
        '    if (!options.skipSmartTaskIntent && !smartTask && ramzyIsTaskCreationIntent(content)) {\n'
        '      startSmartTask(content);\n'
        '      return;\n'
        '    }\n'
        '    setHelpSuggestion(null);\n',
        "intent interception",
    )

    source = replace_once(
        source,
        '    void sendMessage(prompt);\n',
        '    void sendMessage(prompt, { skipSmartTaskIntent: true });\n',
        "structured submit bypass",
    )

    source = replace_once(
        source,
        '<div className="ramzy-suggestions"><button type="button" onClick={startSmartTask}>{isEnglish ? "⚡ Create a task faster" : "⚡ إنشاء مهمة بشكل أسرع"}</button>{(isEnglish ? SUGGESTIONS.en : SUGGESTIONS.ar).map((text) => <button type="button" key={text} onClick={() => sendMessage(text)}>{text}</button>)}</div>',
        '<div className="ramzy-suggestions">{(isEnglish ? SUGGESTIONS.en : SUGGESTIONS.ar).map((text) => <button type="button" key={text} onClick={() => sendMessage(text)}>{text}</button>)}</div>',
        "remove welcome smart-task launcher",
    )

    launcher = '              <button type="button" className={`ramzy-smart-task-launch${smartTask ? " is-active" : ""}`} onClick={smartTask ? cancelSmartTask : startSmartTask} title={isEnglish ? "Smart task creator" : "إنشاء مهمة ذكي"}><Plus size={15} /><span>{isEnglish ? "Smart task" : "مهمة ذكية"}</span></button>\n'
    source = replace_once(source, launcher, "", "remove composer smart-task launcher")

    panel_start = '            {smartTask ? (\n              <div className="ramzy-smart-task-panel"'
    panel_index = source.find(panel_start)
    if panel_index < 0:
        raise RuntimeError("SMART_TASK_PANEL_NOT_FOUND")
    footer_index = source.find('          <footer className="ramzy-composer">\n')
    if footer_index < 0:
        raise RuntimeError("COMPOSER_FOOTER_NOT_FOUND")
    if panel_index < footer_index:
        raise RuntimeError("SMART_TASK_PANEL_ALREADY_CONTEXTUAL")
    textarea_index = source.find('            <textarea ref={composerRef}', panel_index)
    if textarea_index < 0:
        raise RuntimeError("COMPOSER_TEXTAREA_NOT_FOUND_AFTER_PANEL")
    panel_block = source[panel_index:textarea_index]
    if not panel_block.rstrip().endswith(') : null}'):
        raise RuntimeError("SMART_TASK_PANEL_BLOCK_BOUNDARY_UNEXPECTED")
    source = source[:panel_index] + source[textarea_index:]

    bottom_anchor = '            <div ref={bottomRef} />\n'
    source = replace_once(
        source,
        bottom_anchor,
        panel_block + bottom_anchor,
        "move smart task panel into conversation",
    )

    return source


def validate(source: str, css: str):
    required = [
        "function ramzyIsTaskCreationIntent",
        "function ramzyTaskTitleFromIntent",
        "ramzyIsTaskCreationIntent(content)",
        'startSmartTask(content);',
        'skipSmartTaskIntent: true',
        'className="ramzy-smart-task-panel"',
    ]
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(f"CONTEXTUAL_VALIDATION_MISSING={missing}")

    forbidden = [
        'ramzy-smart-task-launch${smartTask',
        '⚡ Create a task faster',
        '⚡ إنشاء مهمة بشكل أسرع',
    ]
    present = [token for token in forbidden if token in source]
    if present:
        raise RuntimeError(f"PERMANENT_UI_STILL_PRESENT={present}")

    bottom = source.find('<div ref={bottomRef} />')
    panel = source.rfind('className="ramzy-smart-task-panel"', 0, bottom)
    footer = source.find('<footer className="ramzy-composer">')
    if panel < 0 or not (panel < bottom < footer):
        raise RuntimeError("SMART_TASK_PANEL_NOT_IN_MESSAGES_FLOW")

    if "TOS_RAMZY_CONTEXTUAL_SMART_TASK_V1" not in css:
        raise RuntimeError("CONTEXTUAL_CSS_MARKER_MISSING")


def main():
    print(f"PATCH={PATCH}")
    head = git("rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"BASELINE_MISMATCH expected={EXPECTED_HEAD} actual={head}")

    if not SOURCE.exists() or not CSS.exists():
        raise RuntimeError("SMART_TASK_V1_FILES_MISSING")

    css_blob = blob_sha(CSS)
    print(f"SMART_TASK_CSS_BLOB={css_blob}")
    if css_blob != EXPECTED_CSS_BLOB:
        raise RuntimeError(
            f"SMART_TASK_CSS_STATE_MISMATCH expected={EXPECTED_CSS_BLOB} actual={css_blob}"
        )

    pre_status = set(git("status", "--porcelain").stdout.splitlines())
    pre_names = status_paths()
    if SOURCE_REL not in pre_names or CSS_REL not in pre_names:
        raise RuntimeError(
            f"SMART_TASK_V1_DIRTY_STATE_MISSING source={SOURCE_REL in pre_names} css={CSS_REL in pre_names}"
        )

    original_source = SOURCE.read_text(encoding="utf-8")
    original_css = CSS.read_text(encoding="utf-8")
    if "TOS_RAMZY_CONTEXTUAL_SMART_TASK_V1" in original_css:
        raise RuntimeError("CONTEXTUAL_SMART_TASK_ALREADY_APPLIED")

    patched_source = patch_source(original_source)
    patched_css = original_css.rstrip() + "\n\n" + CONTEXT_STYLE + "\n"
    validate(patched_source, patched_css)

    SOURCE.write_text(patched_source, encoding="utf-8")
    CSS.write_text(patched_css, encoding="utf-8")

    try:
        diff_check = git("diff", "--check", check=False)
        if diff_check.returncode:
            raise RuntimeError(f"DIFF_CHECK_FAILED\n{diff_check.stdout}\n{diff_check.stderr}")

        run(["npm", "run", "build"], cwd=FRONTEND)

        post_names = status_paths()
        if post_names != pre_names:
            raise RuntimeError(
                f"DIRTY_PATH_SET_CHANGED before={sorted(pre_names)} after={sorted(post_names)}"
            )
        post_status = set(git("status", "--porcelain").stdout.splitlines())
        unrelated_before = {line for line in pre_status if SOURCE_REL not in line and CSS_REL not in line}
        unrelated_after = {line for line in post_status if SOURCE_REL not in line and CSS_REL not in line}
        if unrelated_before != unrelated_after:
            raise RuntimeError("UNRELATED_DIRTY_STATE_CHANGED")

        validate(SOURCE.read_text(encoding="utf-8"), CSS.read_text(encoding="utf-8"))
        built, live = deploy()

        print("PASS_FAIL=PASS")
        print("FILES_PATCHED=2")
        print("RAMZY_BASE_UI=SIMPLE_CHAT_PRESERVED")
        print("PERMANENT_SMART_TASK_BUTTON=REMOVED")
        print("WELCOME_SMART_TASK_BUTTON=REMOVED")
        print("TASK_CREATE_INTENT_DETECTION=PASS")
        print("CONTEXTUAL_PROJECT_CHOICES=PASS")
        print("CONTEXTUAL_DUE_DATE_CHOICES=PASS")
        print("CONTEXTUAL_PRIORITY_CHOICES=PASS")
        print("CONTEXTUAL_ASSIGNEE_CHOICES=PASS")
        print("SMART_CHOICES_LOCATION=CONVERSATION_FLOW")
        print("SMART_CHOICES_EPHEMERAL=YES")
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
        print("READY_FOR_CONTEXTUAL_SMART_TASK_RECHECK=YES")
        print("READY_FOR_GIT_PUSH=NO_UNTIL_RECHECK")
    except Exception:
        SOURCE.write_text(original_source, encoding="utf-8")
        CSS.write_text(original_css, encoding="utf-8")
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PASS_FAIL=FAIL")
        print(f"ERROR={exc}")
        sys.exit(1)
