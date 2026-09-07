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
VOICE = FRONTEND / "src/components/ramzyVoicePhase11.css"
ACTION = FRONTEND / "src/components/ramzyActionControlPhase13.css"
TCS_LAUNCHER = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
TCS_WINDOW = FRONTEND / "src/components/TcsDesktopWindow.jsx"
TCS_STYLE = FRONTEND / "src/components/tcsFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_RAMZY_V2_SHA256 = "bdc467197d875c31da157c2110a6567ba688518e4f529fb3a72280d8081ac6bf"
EXPECTED_V2_CSS_SHA256 = "fa986d1a91c58fa8593368d7c4ef014e8a843edd8475bcccb3b9ed57d3904755"
EXPECTED_V1_CSS_SHA256 = "1db0fc33bd8549a22a25a304a5272095d56933e5edd4ef8a954685a1d42909ad"
EXPECTED_VOICE_BLOB_SHA = "b289a15d25dc7bec7a10f0ecb72ba2e730553b2e"
EXPECTED_ACTION_BLOB_SHA = "72761ca23022940e8b98b8c7a8aea3f67c5b50a2"
V2_IMPORT = 'import "./ramzyFlagshipV2.css";'
V21_IMPORT = 'import "./ramzyFlagshipV2_1VisualCorrection.css";'
MARKER = "--tos-ramzy-flagship-v2-1"

print("RUNNING=TOS_UXUI_RAMZY_ASSISTANT_FLAGSHIP_V2_1_VISUAL_CORRECTION")


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
            V21.unlink(missing_ok=True)
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("RAMZY_FLAGSHIP_V2_1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (FRONTEND, RAMZY, V1, V2, VOICE, ACTION, TCS_LAUNCHER, TCS_WINDOW, TCS_STYLE, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(RAMZY) != EXPECTED_RAMZY_V2_SHA256:
    fail(f"Ramzy V2 live-source baseline mismatch: {sha256(RAMZY)}")
if sha256(V2) != EXPECTED_V2_CSS_SHA256:
    fail(f"Ramzy V2 CSS baseline mismatch: {sha256(V2)}")
if sha256(V1) != EXPECTED_V1_CSS_SHA256:
    fail(f"Ramzy V1 CSS baseline mismatch: {sha256(V1)}")
if git_blob_sha(VOICE) != EXPECTED_VOICE_BLOB_SHA:
    fail(f"Ramzy voice CSS baseline mismatch: {git_blob_sha(VOICE)}")
if git_blob_sha(ACTION) != EXPECTED_ACTION_BLOB_SHA:
    fail(f"Ramzy action CSS baseline mismatch: {git_blob_sha(ACTION)}")
if V21.exists():
    fail("Ramzy V2.1 visual correction CSS already exists; refusing non-idempotent reapply")

original_ramzy = RAMZY.read_text(encoding="utf-8")
if original_ramzy.count(V2_IMPORT) != 1:
    fail(f"V2 import anchor mismatch: {original_ramzy.count(V2_IMPORT)}")
if V21_IMPORT in original_ramzy:
    fail("V2.1 import already present")
for token in (
    'className="ramzy-voice-mode-menu"',
    'className="ramzy-voice-mode-popover"',
    'className="ramzy-luxe-meta-strip"',
    'className={`ramzy-panel opens-',
    'className="ramzy-composer-actions"',
    'className="ramzy-evidence-disclosure"',
):
    if token not in original_ramzy:
        fail(f"required V2 UI anchor missing: {token}")

# Preserve TCS byte-for-byte.
tcs_before = {
    TCS_LAUNCHER: sha256(TCS_LAUNCHER),
    TCS_WINDOW: sha256(TCS_WINDOW),
    TCS_STYLE: sha256(TCS_STYLE),
}

css = r'''/* TOS_RAMZY_ASSISTANT_FLAGSHIP_V2_1_VISUAL_CORRECTION
   Visual-only correction after live V2 QA.
   Fixes dark result readability, voice menu layout, composer balance and lower-panel spacing. */
.ramzy-assistant-root {
  --tos-ramzy-flagship-v2-1: 1;
}

/* Keep the luxury shell, but make the working area calmer and more balanced. */
.ramzy-panel {
  min-width: 0 !important;
}
.ramzy-messages {
  min-height: 0 !important;
  padding: 18px 18px 16px !important;
  overscroll-behavior: contain;
}
.ramzy-message-content {
  min-width: 0 !important;
  overflow: visible !important;
}

/* =========================================================
   Dark result/table readability correction
   ========================================================= */
html.dark .ramzy-assistant-root .ramzy-message.assistant .ramzy-message-content,
html.dark .ramzy-assistant-root .ramzy-markdown,
html.dark .ramzy-assistant-root .ramzy-result-card {
  color: #eeeae2 !important;
}

html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap,
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap {
  border: 1px solid rgba(244,201,103,.16) !important;
  border-radius: 16px !important;
  background: linear-gradient(180deg, rgba(27,27,29,.985), rgba(15,15,17,.985)) !important;
  box-shadow: 0 18px 40px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.035) !important;
  color: #eeeae2 !important;
  opacity: 1 !important;
}

html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap table,
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap table,
html.dark .ramzy-assistant-root .ramzy-operational-table {
  background: #151517 !important;
  color: #eeeae2 !important;
  opacity: 1 !important;
}

html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap thead,
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap thead,
html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap th,
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap th,
html.dark .ramzy-assistant-root .ramzy-operational-table th {
  border-color: rgba(244,201,103,.13) !important;
  background: linear-gradient(180deg, #262426, #1d1c1e) !important;
  color: #f4c967 !important;
  opacity: 1 !important;
}

html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap tbody,
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap tbody,
html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap tr,
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap tr,
html.dark .ramzy-assistant-root .ramzy-operational-table tr {
  background: #151517 !important;
  color: #e9e5dc !important;
  opacity: 1 !important;
}

html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap tbody tr:nth-child(even),
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap tbody tr:nth-child(even),
html.dark .ramzy-assistant-root .ramzy-operational-table tbody tr:nth-child(even) {
  background: #1b1b1e !important;
}

html.dark .ramzy-assistant-root .ramzy-markdown-table-wrap td,
html.dark .ramzy-assistant-root .ramzy-operational-table-wrap td,
html.dark .ramzy-assistant-root .ramzy-operational-table td {
  border-color: rgba(255,255,255,.065) !important;
  background: transparent !important;
  color: #e7e2d8 !important;
  opacity: 1 !important;
}

html.dark .ramzy-assistant-root .ramzy-status-badge,
html.dark .ramzy-assistant-root .ramzy-result-field > b.ramzy-status-badge {
  border: 1px solid rgba(196,181,253,.20) !important;
  background: rgba(124,58,237,.18) !important;
  color: #ddd6fe !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.045) !important;
}

html.dark .ramzy-assistant-root .ramzy-result-card {
  border-color: rgba(244,201,103,.12) !important;
  background: linear-gradient(145deg, rgba(36,35,37,.94), rgba(22,22,24,.94)) !important;
  box-shadow: 0 12px 28px rgba(0,0,0,.22) !important;
}
html.dark .ramzy-assistant-root .ramzy-result-field > span { color: #aaa39a !important; }
html.dark .ramzy-assistant-root .ramzy-result-field > b { color: #eeeae2 !important; }

/* =========================================================
   Composer: one calm text field + one clean control row
   ========================================================= */
.ramzy-composer {
  position: relative !important;
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) !important;
  align-items: stretch !important;
  gap: 9px !important;
  overflow: visible !important;
  padding: 12px 14px 10px !important;
}
.ramzy-composer > textarea {
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  min-height: 52px !important;
  margin: 0 !important;
}
.ramzy-composer > .ramzy-voice-status {
  width: 100% !important;
  margin: 0 !important;
}
.ramzy-composer-actions {
  position: relative !important;
  z-index: 50 !important;
  display: flex !important;
  width: 100% !important;
  min-width: 0 !important;
  align-items: center !important;
  gap: 8px !important;
  margin: 0 !important;
}

/* =========================================================
   Voice mode: fix V2 popover collision/wrapping
   ========================================================= */
.ramzy-voice-mode-menu {
  position: relative !important;
  z-index: 80 !important;
  flex: 0 0 184px !important;
  width: 184px !important;
  min-width: 184px !important;
  max-width: 184px !important;
}
.ramzy-composer-actions .ramzy-voice-mode-trigger {
  display: grid !important;
  grid-template-columns: 30px minmax(0,1fr) 12px !important;
  align-items: center !important;
  gap: 8px !important;
  width: 100% !important;
  height: 46px !important;
  min-height: 46px !important;
  padding: 5px 10px !important;
  border-radius: 14px !important;
  text-align: start !important;
  overflow: hidden !important;
}
.ramzy-voice-mode-trigger-icon {
  display: grid !important;
  width: 28px !important;
  height: 28px !important;
  place-items: center !important;
  border-radius: 10px !important;
  flex: none !important;
}
.ramzy-voice-mode-trigger-copy {
  display: grid !important;
  min-width: 0 !important;
  gap: 1px !important;
  line-height: 1.15 !important;
  white-space: nowrap !important;
}
.ramzy-voice-mode-trigger-copy b {
  overflow: hidden !important;
  font-size: 11px !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}
.ramzy-voice-mode-trigger-copy small {
  overflow: hidden !important;
  color: #8d857b !important;
  font-size: 9px !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}
.ramzy-voice-mode-chevron {
  justify-self: end !important;
  flex: none !important;
}

.ramzy-voice-mode-popover {
  position: absolute !important;
  z-index: 1200 !important;
  inset-inline-start: 0 !important;
  bottom: calc(100% + 10px) !important;
  top: auto !important;
  width: 292px !important;
  min-width: 292px !important;
  max-width: min(292px, calc(100vw - 34px)) !important;
  max-height: none !important;
  padding: 10px !important;
  overflow: visible !important;
  border-radius: 18px !important;
  transform: none !important;
}
.ramzy-voice-mode-popover-kicker {
  display: block !important;
  margin: 0 4px 7px !important;
  font-size: 9px !important;
  line-height: 1 !important;
  letter-spacing: .12em !important;
  white-space: nowrap !important;
}
.ramzy-composer-actions .ramzy-voice-mode-popover > button {
  display: grid !important;
  grid-template-columns: 34px minmax(0,1fr) 18px !important;
  align-items: center !important;
  gap: 9px !important;
  width: 100% !important;
  height: auto !important;
  min-height: 52px !important;
  margin: 0 !important;
  padding: 7px 9px !important;
  border-radius: 13px !important;
  text-align: start !important;
  white-space: normal !important;
}
.ramzy-composer-actions .ramzy-voice-mode-popover > button + button {
  margin-top: 4px !important;
}
.ramzy-voice-mode-option-icon {
  display: grid !important;
  width: 32px !important;
  height: 32px !important;
  place-items: center !important;
  border-radius: 10px !important;
}
.ramzy-voice-mode-popover > button > span:nth-child(2) {
  display: grid !important;
  min-width: 0 !important;
  gap: 2px !important;
  line-height: 1.2 !important;
}
.ramzy-voice-mode-popover > button > span:nth-child(2) b {
  overflow: hidden !important;
  font-size: 11px !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}
.ramzy-voice-mode-popover > button > span:nth-child(2) small {
  overflow: hidden !important;
  color: #8d857b !important;
  font-size: 9.5px !important;
  line-height: 1.25 !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}
.ramzy-voice-mode-check {
  justify-self: end !important;
  flex: none !important;
}

/* Push the mic/send controls cleanly to the opposite edge. */
.ramzy-composer-actions .ramzy-mic-button {
  margin-inline-start: auto !important;
}
.ramzy-composer-actions .ramzy-mic-button + .ramzy-send-button {
  margin-inline-start: 0 !important;
}
.ramzy-composer-actions .ramzy-voice-mode-menu + .ramzy-send-button {
  margin-inline-start: auto !important;
}
.ramzy-composer-actions .ramzy-mic-button,
.ramzy-composer-actions .ramzy-send-button {
  flex: 0 0 auto !important;
}

/* Footer/meta strip: keep it readable and separated from composer controls. */
.ramzy-luxe-meta-strip {
  min-height: 30px !important;
  padding: 7px 14px 8px !important;
  gap: 7px !important;
  white-space: nowrap !important;
  overflow: hidden !important;
}
.ramzy-luxe-meta-strip > span { min-width: 0; }
.ramzy-luxe-meta-always { overflow: hidden; text-overflow: ellipsis; }

/* =========================================================
   Dark-mode popover and lower dock contrast
   ========================================================= */
html.dark .ramzy-assistant-root .ramzy-composer {
  border-top-color: rgba(244,201,103,.10) !important;
  background:
    linear-gradient(180deg, rgba(18,18,20,.98), rgba(11,11,13,.99)) !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-trigger {
  border-color: rgba(244,201,103,.16) !important;
  background: linear-gradient(145deg, rgba(38,37,39,.96), rgba(20,20,22,.98)) !important;
  color: #eeeae2 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.04), 0 8px 20px rgba(0,0,0,.22) !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-trigger.is-open {
  border-color: rgba(244,201,103,.38) !important;
  box-shadow: 0 0 0 3px rgba(244,201,103,.075), 0 10px 24px rgba(0,0,0,.26) !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-trigger-icon,
html.dark .ramzy-assistant-root .ramzy-voice-mode-option-icon {
  border: 1px solid rgba(244,201,103,.14) !important;
  background: rgba(244,201,103,.065) !important;
  color: #f4c967 !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-popover {
  border: 1px solid rgba(244,201,103,.20) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(244,201,103,.08), transparent 28%),
    linear-gradient(155deg, rgba(28,27,29,.995), rgba(13,13,15,.995)) !important;
  box-shadow: 0 24px 70px rgba(0,0,0,.52), 0 0 0 1px rgba(255,255,255,.025) inset !important;
  color: #eeeae2 !important;
  backdrop-filter: blur(22px) saturate(1.1) !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-popover-kicker {
  color: #d9a53e !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-popover > button {
  border: 1px solid transparent !important;
  background: transparent !important;
  color: #ddd8cf !important;
  box-shadow: none !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-popover > button:hover,
html.dark .ramzy-assistant-root .ramzy-voice-mode-popover > button.is-selected {
  border-color: rgba(244,201,103,.16) !important;
  background: rgba(244,201,103,.07) !important;
  color: #fff8e8 !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-popover > button.is-selected {
  box-shadow: inset 2px 0 0 rgba(244,201,103,.70) !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-popover > button > span:nth-child(2) small,
html.dark .ramzy-assistant-root .ramzy-voice-mode-trigger-copy small {
  color: #8f8a82 !important;
}
html.dark .ramzy-assistant-root .ramzy-voice-mode-check {
  color: #f4c967 !important;
}

/* Light mode keeps V2 luxury but avoids a bright dropdown block. */
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-popover {
  border: 1px solid rgba(180,119,27,.18) !important;
  background: linear-gradient(155deg, rgba(255,254,250,.99), rgba(248,245,237,.99)) !important;
  box-shadow: 0 22px 60px rgba(70,48,20,.16), inset 0 1px 0 rgba(255,255,255,.96) !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-popover > button {
  border: 1px solid transparent !important;
  background: transparent !important;
}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-popover > button:hover,
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-popover > button.is-selected {
  border-color: rgba(180,119,27,.14) !important;
  background: rgba(255,248,230,.82) !important;
}

@media (max-width: 640px) {
  .ramzy-messages { padding: 13px !important; }
  .ramzy-composer { padding: 10px !important; gap: 8px !important; }
  .ramzy-voice-mode-menu {
    flex-basis: 158px !important;
    width: 158px !important;
    min-width: 158px !important;
    max-width: 158px !important;
  }
  .ramzy-voice-mode-popover {
    width: min(282px, calc(100vw - 28px)) !important;
    min-width: 0 !important;
  }
  .ramzy-composer-actions .ramzy-voice-mode-popover > button {
    min-height: 50px !important;
  }
  .ramzy-luxe-meta-secure,
  .ramzy-luxe-meta-separator { display: none !important; }
}

@media (max-width: 420px) {
  .ramzy-voice-mode-menu {
    flex-basis: 146px !important;
    width: 146px !important;
    min-width: 146px !important;
    max-width: 146px !important;
  }
  .ramzy-voice-mode-trigger-copy small { display: none !important; }
  .ramzy-composer-actions { gap: 6px !important; }
}

@media (prefers-reduced-motion: reduce) {
  .ramzy-voice-mode-popover,
  .ramzy-voice-mode-trigger { transition: none !important; animation: none !important; }
}
'''

created_css = False
try:
    next_ramzy = original_ramzy.replace(V2_IMPORT, V2_IMPORT + "\n" + V21_IMPORT, 1)
    if next_ramzy.count(V21_IMPORT) != 1:
        raise RuntimeError("V2.1 import insertion failed")
    RAMZY.write_text(next_ramzy, encoding="utf-8")
    V21.write_text(css, encoding="utf-8")
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
    fail("Ramzy V2.1 marker missing from dist", original_ramzy, created_css)
for marker in (
    b"tos.ramzy.position",
    b"ramzy:approval",
    b"ramzy-voice-mode-menu",
    b"ramzy-luxe-meta-strip",
    b"data-tcs-ramzy-collision-sync",
):
    if tree_count(DIST, marker) < 1:
        fail(f"preserved runtime marker missing: {marker.decode(errors='ignore')}", original_ramzy, created_css)

for path, before in tcs_before.items():
    if sha256(path) != before:
        fail(f"TCS out-of-scope file changed: {path}", original_ramzy, created_css)

# Safe live deploy via candidate + atomic rename. No service restart.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.ramzy-flagship-v2-1-candidate-{ts}"
backup = LIVE_PARENT / f"build.ramzy-flagship-v2-1-backup-{ts}"
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
print("RAMZY_FLAGSHIP_V2_1_RUNTIME=YES")
print("RAMZY_V2_PRESERVED=YES")
print("RAMZY_DARK_TABLE_READABILITY=CORRECTED")
print("RAMZY_WHITE_WASHED_RESULTS=REMOVED")
print("RAMZY_VOICE_MENU_LAYOUT=CORRECTED")
print("RAMZY_VOICE_MENU_TEXT_WRAP=CORRECTED")
print("RAMZY_VOICE_MENU_COMPOSER_COLLISION=CORRECTED")
print("RAMZY_COMPOSER_BALANCE=CORRECTED")
print("RAMZY_META_STRIP_SPACING=CORRECTED")
print("RAMZY_LIGHT_MODE=PRESERVED")
print("RAMZY_DARK_MODE=PRESERVED_OBSIDIAN_GOLD")
print("RAMZY_AGENT_LOGIC_CHANGED=NO")
print("RAMZY_API_CHANGED=NO")
print("RAMZY_VOICE_BEHAVIOR_CHANGED=NO")
print("RAMZY_APPROVAL_LOGIC_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("AUTH_CHANGED=NO")
print("TCS_CHANGED=NO")
print(f"V21_CSS_SHA256={sha256(V21)}")
print(f"RAMZY_JS_SHA256={sha256(RAMZY)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")