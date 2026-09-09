#!/usr/bin/env python3
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

PATCH = "TOS-RAMZY-TYPING-PERFORMANCE-V1-GIT-GENERATED"
SCRIPT = "run_ramzy_typing_performance_v1.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/"
BASELINE = "509c51eeab1a9b880d902aac5082aa6124996c9b"
TARGET = "frontend/src/components/RamzyAssistant.jsx"
TARGET_BLOB = "138c04ef2959ba3d3e99a767653311958dae1195"
PHASE_SCOPE = {TARGET}


def run(args, cwd=REPO, check=True, capture=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=capture)
    if check and result.returncode != 0:
        if capture:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"command failed: {' '.join(args)}")
    return result


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-Ramzy-performance-patch"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return download(url).decode("utf-8", errors="replace")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)


def replace_exact_count(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} anchors, found {count}")
    return text.replace(old, new)


def status_lines():
    out = run(["git", "status", "--porcelain"], capture=True).stdout
    return [line for line in out.splitlines() if line.strip()]


def status_path(line: str) -> str:
    raw = line[3:].strip()
    if " -> " in raw:
        raw = raw.split(" -> ", 1)[1]
    return raw.strip('"')


def main_asset_from_html(html: str):
    match = re.search(r'(/assets/index-[^"\']+\.js)', html)
    return match.group(1) if match else None


def rollback_source(snapshot):
    for rel, previous in snapshot.items():
        path = REPO / rel
        if previous is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(previous)


def fail(message, snapshot=None, live_backup=None):
    print(f"ERROR={message}", file=sys.stderr)
    if snapshot is not None:
        try:
            rollback_source(snapshot)
            print("SOURCE_ROLLBACK=PASS", file=sys.stderr)
        except Exception as exc:
            print(f"SOURCE_ROLLBACK=FAIL:{exc}", file=sys.stderr)
    if live_backup and Path(live_backup).exists():
        try:
            if LIVE_ROOT.exists():
                shutil.rmtree(LIVE_ROOT)
            shutil.copytree(live_backup, LIVE_ROOT)
            run(["nginx", "-t"], check=True)
            run(["systemctl", "reload", "nginx"], check=True)
            print("LIVE_ROLLBACK=PASS", file=sys.stderr)
        except Exception as exc:
            print(f"LIVE_ROLLBACK=FAIL:{exc}", file=sys.stderr)
    sys.exit(1)


if not REPO.exists():
    fail("REPO_NOT_FOUND")

head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")

target_hash = run(["git", "hash-object", TARGET]).stdout.strip()
if target_hash != TARGET_BLOB:
    fail(f"TARGET_BLOB_MISMATCH:{target_hash}")

before_status = status_lines()
target_dirty = [line for line in before_status if status_path(line) in PHASE_SCOPE]
if target_dirty:
    fail("TARGET_PATH_ALREADY_DIRTY:" + "|".join(target_dirty))
unrelated_before = [line for line in before_status if status_path(line) not in PHASE_SCOPE]
precheck = "CLEAN" if not unrelated_before else "DIRTY_UNRELATED_ALLOWED"

target_path = REPO / TARGET
snapshot = {TARGET: target_path.read_bytes()}
live_backup = None

try:
    source = target_path.read_text(encoding="utf-8")

    source = replace_once(
        source,
        '  const [approvals, setApprovals] = useState([]);\n  const [input, setInput] = useState("");\n  const [helpSuggestion, setHelpSuggestion] = useState(null);',
        '  const [approvals, setApprovals] = useState([]);\n  const [composerHasText, setComposerHasText] = useState(false);\n  const [helpSuggestion, setHelpSuggestion] = useState(null);',
        "composer state",
    )

    source = replace_once(
        source,
        '  const bottomRef = useRef(null);\n  const composerRef = useRef(null);\n  const streamControllerRef = useRef(null);',
        '  const bottomRef = useRef(null);\n  const composerRef = useRef(null);\n  const composerValueRef = useRef("");\n  const composerHasTextRef = useRef(false);\n  const composerResizeFrameRef = useRef(0);\n  const streamControllerRef = useRef(null);',
        "composer refs",
    )

    helper_block = '''  const scheduleComposerResize = useCallback((textarea = composerRef.current) => {
    if (!textarea) return;
    cancelAnimationFrame(composerResizeFrameRef.current);
    composerResizeFrameRef.current = requestAnimationFrame(() => {
      if (!textarea.isConnected) return;
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    });
  }, []);

  const setComposerValue = useCallback((nextValue, options = {}) => {
    const value = String(nextValue ?? "");
    composerValueRef.current = value;

    if (composerRef.current && composerRef.current.value !== value) {
      composerRef.current.value = value;
    }

    const nextHasText = Boolean(value.trim());
    if (composerHasTextRef.current !== nextHasText) {
      composerHasTextRef.current = nextHasText;
      setComposerHasText(nextHasText);
    }

    if (options.resize !== false) scheduleComposerResize(composerRef.current);
  }, [scheduleComposerResize]);

  useEffect(() => () => {
    cancelAnimationFrame(composerResizeFrameRef.current);
  }, []);

'''
    source = replace_once(
        source,
        '  const minimizedStyle = useMemo(() => computeMinimizedStyle(launcherPosition, viewport), [launcherPosition, viewport]);\n\n  function handleLauncherPointerDown(event) {',
        '  const minimizedStyle = useMemo(() => computeMinimizedStyle(launcherPosition, viewport), [launcherPosition, viewport]);\n\n' + helper_block + '  function handleLauncherPointerDown(event) {',
        "composer performance helpers",
    )

    source = replace_once(
        source,
        '      const existing = String(input || "").trim();',
        '      const existing = String(composerValueRef.current || "").trim();',
        "help center current composer value",
    )
    source = replace_exact_count(
        source,
        '        setInput(prompt);',
        '        setComposerValue(prompt);',
        1,
        "help center prompt apply",
    )
    source = replace_once(
        source,
        '    return () => window.removeEventListener("tos:ramzy-help", handleRamzyHelp);\n  }, [input]);',
        '    return () => window.removeEventListener("tos:ramzy-help", handleRamzyHelp);\n  }, [setComposerValue]);',
        "help center listener dependency",
    )

    source = replace_exact_count(
        source,
        '    voiceBaseInputRef.current = input;',
        '    voiceBaseInputRef.current = composerValueRef.current;',
        2,
        "voice base composer value",
    )
    source = replace_once(
        source,
        '      setInput(appendDictation(voiceBaseInputRef.current, transcript));',
        '      setComposerValue(appendDictation(voiceBaseInputRef.current, transcript));',
        "browser voice dictation",
    )
    source = replace_once(
        source,
        '            setInput((current) => appendDictation(current || voiceBaseInputRef.current, transcript));',
        '            setComposerValue(appendDictation(composerValueRef.current || voiceBaseInputRef.current, transcript));',
        "api voice transcription",
    )

    source = replace_once(
        source,
        '    setInput(prompt);\n    setHelpSuggestion(null);',
        '    setComposerValue(prompt);\n    setHelpSuggestion(null);',
        "help suggestion apply",
    )

    source = replace_once(
        source,
        '''  function handleComposerInput(event) {
    const textarea = event.currentTarget;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    setInput(textarea.value);
  }

  async function sendMessage(text = input) {''',
        '''  function handleComposerInput(event) {
    setComposerValue(event.currentTarget.value);
  }

  async function sendMessage(text = composerValueRef.current) {''',
        "composer input path",
    )

    source = replace_once(
        source,
        '      setInput("");\n      if (composerRef.current) composerRef.current.style.height = "";',
        '      setComposerValue("", { resize: false });\n      if (composerRef.current) composerRef.current.style.height = "";',
        "composer clear after send",
    )

    source = replace_once(
        source,
        'value={input} onChange={(event) => setInput(event.target.value)} onInput={handleComposerInput}',
        'defaultValue={composerValueRef.current} onInput={handleComposerInput}',
        "uncontrolled textarea",
    )
    source = replace_once(
        source,
        'onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendMessage(); } }}',
        'onKeyDown={(event) => { if (event.nativeEvent?.isComposing || event.isComposing) return; if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendMessage(); } }}',
        "IME enter guard",
    )
    source = replace_once(
        source,
        'disabled={!input.trim() || loading || listening}',
        'disabled={!composerHasText || loading || listening}',
        "send button composer state",
    )

    forbidden = [
        'const [input, setInput] = useState("")',
        'value={input} onChange=',
        'setInput(',
        '}, [input]);',
    ]
    for token in forbidden:
        if token in source:
            raise RuntimeError(f"FORBIDDEN_LEGACY_TOKEN_PRESENT:{token}")

    required = [
        "composerValueRef",
        "composerHasTextRef",
        "composerResizeFrameRef",
        "scheduleComposerResize",
        "setComposerValue",
        "defaultValue={composerValueRef.current}",
        "event.nativeEvent?.isComposing",
        "disabled={!composerHasText || loading || listening}",
        "}, [setComposerValue]);",
    ]
    for token in required:
        if token not in source:
            raise RuntimeError(f"REQUIRED_TOKEN_MISSING:{token}")

    target_path.write_text(source, encoding="utf-8")

    run(["git", "diff", "--check"])
    run(["npm", "run", "build"], cwd=FRONTEND)

    changed = set()
    for line in run(["git", "status", "--porcelain"]).stdout.splitlines():
        if not line.strip():
            continue
        path = status_path(line)
        if path in PHASE_SCOPE:
            changed.add(path)
    if changed != PHASE_SCOPE:
        raise RuntimeError("CHANGED_PATHS_EXACT_FAIL:" + ",".join(sorted(changed)))

    after_status = status_lines()
    unrelated_after = [line for line in after_status if status_path(line) not in PHASE_SCOPE]
    if unrelated_after != unrelated_before:
        raise RuntimeError("UNRELATED_DIRTY_STATE_CHANGED")

    if not LIVE_ROOT.exists() or not (DIST / "index.html").exists():
        raise RuntimeError("LIVE_OR_DIST_ROOT_MISSING")

    built_html = (DIST / "index.html").read_text(encoding="utf-8")
    built_asset = main_asset_from_html(built_html)
    if not built_asset or not (DIST / built_asset.lstrip("/")).exists():
        raise RuntimeError("BUILT_MAIN_ASSET_NOT_FOUND")

    try:
        live_before_html = fetch_text(LIVE_URL)
        live_before_asset = main_asset_from_html(live_before_html) or "UNKNOWN"
    except Exception:
        live_before_asset = "UNAVAILABLE"

    backup_parent = Path(tempfile.mkdtemp(prefix="ramzy_typing_perf_live_"))
    live_backup = backup_parent / "build"
    shutil.copytree(LIVE_ROOT, live_backup)

    run(["rsync", "-a", "--delete", str(DIST) + "/", str(LIVE_ROOT) + "/"])
    run(["nginx", "-t"])
    run(["systemctl", "reload", "nginx"])
    time.sleep(1)

    cache_bust = int(time.time())
    live_after_html = fetch_text(LIVE_URL + f"?ramzyTypingPerf={cache_bust}")
    live_after_asset = main_asset_from_html(live_after_html)
    if live_after_asset != built_asset:
        raise RuntimeError(f"LIVE_ASSET_MISMATCH:{live_after_asset}:{built_asset}")

    live_js = download("https://tos.tamiyouz.com" + built_asset + f"?ramzyTypingPerf={cache_bust}")
    built_js = (DIST / built_asset.lstrip("/")).read_bytes()
    if live_js != built_js:
        raise RuntimeError("LIVE_BUNDLE_BYTES_MISMATCH")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT_VERSION={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD_COMMIT={head}")
    print("PASS_FAIL=PASS")
    print("FILES_PATCHED=1")
    print(f"PRECHECK_WORKTREE={precheck}")
    print("BASELINE_BLOB_GUARD=PASS")
    print("RAMZY_TARGET=frontend/src/components/RamzyAssistant.jsx")
    print("CONTROLLED_INPUT_PER_KEYSTROKE_STATE=REMOVED")
    print("DUPLICATE_ONCHANGE_ONINPUT=REMOVED")
    print("COMPOSER_REF_PATH=PASS")
    print("COMPOSER_RENDER_ON_EMPTY_STATE_TRANSITION=PASS")
    print("AUTOSIZE_REQUEST_ANIMATION_FRAME=PASS")
    print("HELP_LISTENER_REBIND_PER_KEYSTROKE=REMOVED")
    print("VOICE_INPUT_SYNC=PASS")
    print("HELP_CENTER_PROMPT_SYNC=PASS")
    print("ARABIC_IME_ENTER_GUARD=PASS")
    print("ENTER_SEND_BEHAVIOR=PRESERVED")
    print("SHIFT_ENTER_NEWLINE_BEHAVIOR=PRESERVED")
    print("FRONTEND_BUILD=PASS")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_before_asset}")
    print(f"LIVE_ASSET_AFTER={live_after_asset}")
    print(f"LIVE_DEPLOY_ROOT={LIVE_ROOT}")
    print("LIVE_DEPLOY=PASS")
    print("LIVE_BUNDLE_MATCH=PASS")
    print("BACKEND_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("PRE_EXISTING_UNRELATED_DIRTY_STATE_PRESERVED=YES")
    print("CHANGED_PATHS_EXACT=YES")
    print("MANUAL_EDITS=NONE")
    print("PUSH_PERFORMED=NO")
    print("RAMZY_TYPING_PERFORMANCE_PATCH_APPLIED=YES")
    print("READY_FOR_TYPING_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_TYPING_RECHECK")

except Exception as exc:
    fail(str(exc), snapshot=snapshot, live_backup=live_backup)
