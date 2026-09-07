from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
RAMZY = FRONTEND / "src/components/RamzyAssistant.jsx"
V1 = FRONTEND / "src/components/ramzyFlagshipV1.css"
V2 = FRONTEND / "src/components/ramzyFlagshipV2.css"
V21 = FRONTEND / "src/components/ramzyFlagshipV2_1VisualCorrection.css"
V22 = FRONTEND / "src/components/ramzyFlagshipV2_2DarkVisibilityPolish.css"
VOICE = FRONTEND / "src/components/ramzyVoicePhase11.css"
ACTION = FRONTEND / "src/components/ramzyActionControlPhase13.css"
TCS_LAUNCHER = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
TCS_WINDOW = FRONTEND / "src/components/TcsDesktopWindow.jsx"
TCS_STYLE = FRONTEND / "src/components/tcsFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_RAMZY_V21_SHA256 = "c7d31989787d1f1cd6a0227221241f5899302ff7c0af277ecaeae1145d7ad3aa"
EXPECTED_V21_CSS_SHA256 = "7aba54dbe393ad04b91d59031218fd792a80c64e28d3b8cbffc5fb7f6d3c704a"
EXPECTED_V2_CSS_SHA256 = "fa986d1a91c58fa8593368d7c4ef014e8a843edd8475bcccb3b9ed57d3904755"
EXPECTED_V1_CSS_SHA256 = "1db0fc33bd8549a22a25a304a5272095d56933e5edd4ef8a954685a1d42909ad"
EXPECTED_VOICE_BLOB_SHA = "b289a15d25dc7bec7a10f0ecb72ba2e730553b2e"
EXPECTED_ACTION_BLOB_SHA = "72761ca23022940e8b98b8c7a8aea3f67c5b50a2"
V21_IMPORT = 'import "./ramzyFlagshipV2_1VisualCorrection.css";'
V22_IMPORT = 'import "./ramzyFlagshipV2_2DarkVisibilityPolish.css";'
MARKER = "--tos-ramzy-flagship-v2-2"

print("RUNNING=TOS_UXUI_RAMZY_ASSISTANT_FLAGSHIP_V2_2_DARK_VISIBILITY_POLISH")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.read_bytes().count(needle)
        except OSError:
            pass
    return total


def fail(message: str, original_ramzy=None, created_css=False):
    if original_ramzy is not None:
        try:
            RAMZY.write_text(original_ramzy, encoding="utf-8")
        except Exception:
            pass
    if created_css:
        try:
            V22.unlink(missing_ok=True)
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("RAMZY_FLAGSHIP_V2_2_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (FRONTEND, RAMZY, V1, V2, V21, VOICE, ACTION, TCS_LAUNCHER, TCS_WINDOW, TCS_STYLE, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(RAMZY) != EXPECTED_RAMZY_V21_SHA256:
    fail(f"Ramzy V2.1 live-source baseline mismatch: {sha256(RAMZY)}")
if sha256(V21) != EXPECTED_V21_CSS_SHA256:
    fail(f"Ramzy V2.1 CSS baseline mismatch: {sha256(V21)}")
if sha256(V2) != EXPECTED_V2_CSS_SHA256:
    fail(f"Ramzy V2 CSS baseline mismatch: {sha256(V2)}")
if sha256(V1) != EXPECTED_V1_CSS_SHA256:
    fail(f"Ramzy V1 CSS baseline mismatch: {sha256(V1)}")
if git_blob_sha(VOICE) != EXPECTED_VOICE_BLOB_SHA:
    fail(f"Ramzy voice CSS baseline mismatch: {git_blob_sha(VOICE)}")
if git_blob_sha(ACTION) != EXPECTED_ACTION_BLOB_SHA:
    fail(f"Ramzy action CSS baseline mismatch: {git_blob_sha(ACTION)}")
if V22.exists():
    fail("Ramzy V2.2 CSS already exists; refusing non-idempotent reapply")

original_ramzy = RAMZY.read_text(encoding="utf-8")
if original_ramzy.count(V21_IMPORT) != 1:
    fail(f"V2.1 import anchor mismatch: {original_ramzy.count(V21_IMPORT)}")
if V22_IMPORT in original_ramzy:
    fail("V2.2 import already present")
for token in (
    'className={`ramzy-panel opens-',
    'className="ramzy-panel-header"',
    'className="ramzy-messages"',
    'className="ramzy-composer"',
    'className="ramzy-voice-mode-menu"',
    'className="ramzy-luxe-meta-strip"',
    'className="ramzy-launcher"',
):
    if token not in original_ramzy:
        fail(f"required V2.1 UI anchor missing: {token}")

# Preserve TCS byte-for-byte.
tcs_before = {
    TCS_LAUNCHER: sha256(TCS_LAUNCHER),
    TCS_WINDOW: sha256(TCS_WINDOW),
    TCS_STYLE: sha256(TCS_STYLE),
}

css = r'''/* TOS_RAMZY_ASSISTANT_FLAGSHIP_V2_2_DARK_VISIBILITY_POLISH
   Visual-only hotfix after V2.1 live QA.
   Protects dark-mode content layers from Chromium compositing/mask issues and
   strengthens light-mode contrast without touching Ramzy behavior. */
.ramzy-assistant-root {
  --tos-ramzy-flagship-v2-2: 1;
}

/* Structural layer safety: keep the real UI above all decorative pseudo layers. */
.ramzy-panel {
  display: flex !important;
  flex-direction: column !important;
  min-width: 0 !important;
  contain: none !important;
}
.ramzy-panel::before,
.ramzy-panel::after {
  pointer-events: none !important;
  z-index: 0 !important;
}
.ramzy-panel > .ramzy-panel-header,
.ramzy-panel > .ramzy-history-select,
.ramzy-panel > .ramzy-messages,
.ramzy-panel > .ramzy-composer,
.ramzy-panel > .ramzy-luxe-meta-strip {
  position: relative !important;
  z-index: 3 !important;
  opacity: 1 !important;
  visibility: visible !important;
  mix-blend-mode: normal !important;
}
.ramzy-panel > .ramzy-panel-header,
.ramzy-panel > .ramzy-messages,
.ramzy-panel > .ramzy-composer,
.ramzy-panel > .ramzy-luxe-meta-strip {
  flex-shrink: 0;
}
.ramzy-panel > .ramzy-messages {
  flex: 1 1 auto !important;
  min-height: 0 !important;
  overflow-y: auto !important;
}

/* =========================================================
   DARK MODE: deterministic compositing and visibility
   ========================================================= */
html.dark .ramzy-assistant-root .ramzy-panel {
  isolation: isolate !important;
  -webkit-backdrop-filter: none !important;
  backdrop-filter: none !important;
  background:
    radial-gradient(circle at 88% -8%, rgba(244,201,103,.10), transparent 30%),
    radial-gradient(circle at 7% 105%, rgba(126,82,19,.10), transparent 28%),
    linear-gradient(148deg,#171615 0%,#0f1011 48%,#08090a 100%) !important;
  color: #f3efe8 !important;
}
html.dark .ramzy-assistant-root .ramzy-panel::after {
  width: 255px !important;
  height: 150px !important;
  inset-inline-end: 0 !important;
  top: 0 !important;
  opacity: .42 !important;
  -webkit-mask-image: none !important;
  mask-image: none !important;
  background:
    radial-gradient(circle at 1px 1px, rgba(244,201,103,.20) 1px, transparent 1.35px) 0 0/10px 10px,
    linear-gradient(135deg, transparent 4%, rgba(244,201,103,.055), transparent 72%) !important;
  clip-path: polygon(28% 0,100% 0,100% 100%,62% 76%);
}
html.dark .ramzy-assistant-root .ramzy-panel::before {
  z-index: 1 !important;
}

html.dark .ramzy-assistant-root .ramzy-panel > .ramzy-panel-header,
html.dark .ramzy-assistant-root .ramzy-panel > .ramzy-messages,
html.dark .ramzy-assistant-root .ramzy-panel > .ramzy-composer,
html.dark .ramzy-assistant-root .ramzy-panel > .ramzy-luxe-meta-strip,
html.dark .ramzy-assistant-root .ramzy-panel > .ramzy-history-select {
  z-index: 5 !important;
  opacity: 1 !important;
  visibility: visible !important;
  filter: none !important;
  transform: none !important;
  -webkit-mask-image: none !important;
  mask-image: none !important;
}
html.dark .ramzy-assistant-root .ramzy-panel > .ramzy-panel-header {
  display: flex !important;
  flex: 0 0 auto !important;
  min-height: 88px !important;
  border-bottom: 1px solid rgba(244,201,103,.11) !important;
  background:
    linear-gradient(118deg,rgba(35,33,31,.985),rgba(19,19,20,.985) 62%,rgba(59,44,20,.50)) !important;
  box-shadow: 0 14px 34px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.035) !important;
}
html.dark .ramzy-assistant-root .ramzy-panel-header::after {
  z-index: 0 !important;
  opacity: .55 !important;
}
html.dark .ramzy-assistant-root .ramzy-panel-header > * {
  position: relative !important;
  z-index: 2 !important;
  opacity: 1 !important;
  visibility: visible !important;
}
html.dark .ramzy-assistant-root .ramzy-panel-identity strong {
  color: #f4cf70 !important;
  -webkit-text-fill-color: currentColor !important;
  background: none !important;
}
html.dark .ramzy-assistant-root .ramzy-panel-identity span {
  color: #aaa39a !important;
}
html.dark .ramzy-assistant-root .ramzy-panel-controls,
html.dark .ramzy-assistant-root .ramzy-panel-controls button {
  opacity: 1 !important;
  visibility: visible !important;
}

html.dark .ramzy-assistant-root .ramzy-panel > .ramzy-messages {
  display: block !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(244,201,103,.045), transparent 22%),
    linear-gradient(180deg,#111214 0%,#0c0d0f 52%,#090a0b 100%) !important;
  color: #ece8e0 !important;
}
html.dark .ramzy-assistant-root .ramzy-message,
html.dark .ramzy-assistant-root .ramzy-message-content,
html.dark .ramzy-assistant-root .ramzy-markdown,
html.dark .ramzy-assistant-root .ramzy-welcome,
html.dark .ramzy-assistant-root .ramzy-typing,
html.dark .ramzy-assistant-root .ramzy-error,
html.dark .ramzy-assistant-root .ramzy-approval-card {
  opacity: 1 !important;
  visibility: visible !important;
  filter: none !important;
}
html.dark .ramzy-assistant-root .ramzy-message.assistant .ramzy-message-content {
  border-color: rgba(244,201,103,.16) !important;
  background: linear-gradient(145deg,#252526,#171719) !important;
  color: #eeeae2 !important;
  box-shadow: 0 18px 40px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.035) !important;
}
html.dark .ramzy-assistant-root .ramzy-message.user .ramzy-message-content {
  border-color: rgba(244,201,103,.18) !important;
  background: linear-gradient(135deg,#34322f,#202022 68%,#68430c) !important;
  color: #fff !important;
}
html.dark .ramzy-assistant-root .ramzy-markdown,
html.dark .ramzy-assistant-root .ramzy-markdown p,
html.dark .ramzy-assistant-root .ramzy-markdown li,
html.dark .ramzy-assistant-root .ramzy-markdown td {
  color: #e9e4dc !important;
}
html.dark .ramzy-assistant-root .ramzy-welcome strong { color: #f2cf73 !important; }
html.dark .ramzy-assistant-root .ramzy-welcome p { color: #aaa39a !important; }

html.dark .ramzy-assistant-root .ramzy-panel > .ramzy-composer {
  display: grid !important;
  flex: 0 0 auto !important;
  border-top: 1px solid rgba(244,201,103,.10) !important;
  background: linear-gradient(180deg,#131315,#0b0c0d) !important;
  opacity: 1 !important;
  visibility: visible !important;
}
html.dark .ramzy-assistant-root .ramzy-composer > textarea,
html.dark .ramzy-assistant-root .ramzy-composer-actions,
html.dark .ramzy-assistant-root .ramzy-voice-mode-menu,
html.dark .ramzy-assistant-root .ramzy-send-button,
html.dark .ramzy-assistant-root .ramzy-mic-button {
  opacity: 1 !important;
  visibility: visible !important;
  filter: none !important;
}
html.dark .ramzy-assistant-root .ramzy-composer > textarea {
  border-color: rgba(244,201,103,.13) !important;
  background: #202023 !important;
  color: #f3efe8 !important;
}
html.dark .ramzy-assistant-root .ramzy-composer > textarea::placeholder {
  color: #77736d !important;
  opacity: 1 !important;
}
html.dark .ramzy-assistant-root .ramzy-panel > .ramzy-luxe-meta-strip {
  display: flex !important;
  flex: 0 0 auto !important;
  border-top-color: rgba(244,201,103,.08) !important;
  background: #090a0b !important;
  color: #77716a !important;
}

/* Dark table result readability remains explicit above global compatibility CSS. */
html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap,
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap,
html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap table,
html.dark .ramzy-assistant-root .ramzy-operational-table,
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap table {
  opacity: 1 !important;
  visibility: visible !important;
  background-color: #151517 !important;
  color: #e9e4dc !important;
}
html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap th,
html.dark .ramzy-assistant-root .ramzy-operational-table th {
  background: #242326 !important;
  color: #f2cb69 !important;
}
html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap td,
html.dark .ramzy-assistant-root .ramzy-operational-table td {
  background: transparent !important;
  color: #e5dfd6 !important;
}

/* =========================================================
   LIGHT MODE: less washed-out, stronger flagship separation
   ========================================================= */
html:not(.dark) .ramzy-assistant-root .ramzy-panel {
  border-color: rgba(174,112,20,.42) !important;
  background:
    radial-gradient(circle at 88% -8%,rgba(232,176,67,.16),transparent 30%),
    linear-gradient(145deg,#fffdf8 0%,#f8f3e8 58%,#fffaf0 100%) !important;
  box-shadow:
    0 0 0 1px rgba(255,255,255,.92),
    0 42px 105px rgba(71,50,22,.18),
    0 15px 36px rgba(15,23,42,.09),
    0 0 50px rgba(180,119,27,.07) !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-panel > .ramzy-panel-header {
  background: linear-gradient(118deg,#fffefa,#f7f1e4 62%,#f5e7c5) !important;
  border-bottom-color: rgba(174,112,20,.18) !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-panel-identity strong {
  color: #2a2116 !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-panel-identity span {
  color: #6f6558 !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-panel > .ramzy-messages {
  background:
    radial-gradient(circle at 100% 0%,rgba(232,176,67,.065),transparent 23%),
    linear-gradient(180deg,#fbf8f1 0%,#fffdfa 48%,#f8f5ee 100%) !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-message.assistant .ramzy-message-content {
  border-color: rgba(174,112,20,.20) !important;
  background: #fffdfa !important;
  color: #2d271f !important;
  box-shadow: 0 17px 38px rgba(64,45,22,.09), inset 0 1px 0 #fff !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-markdown,
html:not(.dark) .ramzy-assistant-root .ramzy-markdown p,
html:not(.dark) .ramzy-assistant-root .ramzy-markdown li {
  color: #312a22 !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-panel > .ramzy-composer {
  background: linear-gradient(180deg,#fffdf8,#f6efe1) !important;
  border-top-color: rgba(174,112,20,.17) !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-composer > textarea {
  border-color: rgba(174,112,20,.20) !important;
  background: #fff !important;
  color: #29231c !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-trigger {
  border-color: rgba(174,112,20,.19) !important;
  background: linear-gradient(145deg,#fffdf8,#f5eddd) !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-luxe-meta-strip {
  background: #f7f0e3 !important;
  border-top-color: rgba(174,112,20,.15) !important;
  color: #746858 !important;
}

/* Preserve the corrected V2.1 interaction menu geometry. */
.ramzy-voice-mode-menu {
  flex: 0 0 184px !important;
  width: 184px !important;
  min-width: 184px !important;
  max-width: 184px !important;
}
.ramzy-voice-mode-popover {
  z-index: 1200 !important;
}

@media (max-width: 640px) {
  .ramzy-panel { border-radius: 24px !important; }
  .ramzy-panel > .ramzy-panel-header { min-height: 70px !important; }
  .ramzy-voice-mode-menu {
    flex-basis: 158px !important;
    width: 158px !important;
    min-width: 158px !important;
    max-width: 158px !important;
  }
  html.dark .ramzy-assistant-root .ramzy-panel::after {
    width: 180px !important;
    height: 105px !important;
    opacity: .30 !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ramzy-panel *, .ramzy-panel::before, .ramzy-panel::after {
    transition: none !important;
    animation: none !important;
  }
}
'''

created_css = False
try:
    next_ramzy = original_ramzy.replace(V21_IMPORT, V21_IMPORT + "\n" + V22_IMPORT, 1)
    if next_ramzy.count(V22_IMPORT) != 1:
        raise RuntimeError("V2.2 import insertion failed")
    RAMZY.write_text(next_ramzy, encoding="utf-8")
    V22.write_text(css, encoding="utf-8")
    created_css = True
except Exception as exc:
    fail(f"source write failed: {exc}", original_ramzy, created_css)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", original_ramzy, created_css)

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", original_ramzy, created_css)
if tree_count(DIST, MARKER.encode()) < 1:
    fail("Ramzy V2.2 marker missing from dist", original_ramzy, created_css)
for marker in (
    b"--tos-ramzy-flagship-v2-1",
    b"ramzy-voice-mode-menu",
    b"ramzy-luxe-meta-strip",
    b"tos.ramzy.position",
    b"ramzy:approval",
    b"data-tcs-ramzy-collision-sync",
):
    if tree_count(DIST, marker) < 1:
        fail(f"preserved runtime marker missing: {marker.decode(errors='ignore')}", original_ramzy, created_css)

for path, before in tcs_before.items():
    if sha256(path) != before:
        fail(f"TCS out-of-scope file changed: {path}", original_ramzy, created_css)

# Safe live deploy via candidate + atomic rename. No service restart.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.ramzy-flagship-v2-2-candidate-{ts}"
backup = LIVE_PARENT / f"build.ramzy-flagship-v2-2-backup-{ts}"
if candidate.exists():
    shutil.rmtree(candidate)
shutil.copytree(DIST, candidate)
if not (candidate / "index.html").exists():
    fail("candidate index missing", original_ramzy, created_css)
try:
    if LIVE.exists():
        LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists():
            shutil.rmtree(LIVE)
    except Exception:
        pass
    try:
        if backup.exists() and not LIVE.exists():
            backup.rename(LIVE)
    except Exception:
        pass
    fail(f"live deploy failed: {exc}", original_ramzy, created_css)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("RAMZY_FLAGSHIP_V2_2_RUNTIME=YES")
print("RAMZY_V2_1_PRESERVED=YES")
print("RAMZY_DARK_COMPOSITING_GUARD=YES")
print("RAMZY_DARK_DECORATIVE_MASK=REMOVED")
print("RAMZY_DARK_CONTENT_LAYER_RULES=FORCED_VISIBLE")
print("RAMZY_DARK_HEADER_VISIBILITY_RULE=YES")
print("RAMZY_DARK_MESSAGES_VISIBILITY_RULE=YES")
print("RAMZY_DARK_COMPOSER_VISIBILITY_RULE=YES")
print("RAMZY_DARK_META_STRIP_VISIBILITY_RULE=YES")
print("RAMZY_DARK_TABLE_CONTRAST=PRESERVED")
print("RAMZY_LIGHT_CONTRAST=UPGRADED")
print("RAMZY_VOICE_MENU_V2_1_GEOMETRY=PRESERVED")
print("RAMZY_AGENT_LOGIC_CHANGED=NO")
print("RAMZY_API_CHANGED=NO")
print("RAMZY_VOICE_BEHAVIOR_CHANGED=NO")
print("RAMZY_APPROVAL_LOGIC_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("AUTH_CHANGED=NO")
print("TCS_CHANGED=NO")
print(f"V22_CSS_SHA256={sha256(V22)}")
print(f"RAMZY_JS_SHA256={sha256(RAMZY)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")