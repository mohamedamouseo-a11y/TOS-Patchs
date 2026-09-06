from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
RAMZY = FRONTEND / "src/components/RamzyAssistant.jsx"
FLAGSHIP = FRONTEND / "src/components/ramzyFlagshipV1.css"
VOICE = FRONTEND / "src/components/ramzyVoicePhase11.css"
ACTION = FRONTEND / "src/components/ramzyActionControlPhase13.css"
TCS_LAUNCHER = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
TCS_WINDOW = FRONTEND / "src/components/TcsDesktopWindow.jsx"
TCS_STYLE = FRONTEND / "src/components/tcsFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_VOICE_BLOB_SHA = "b289a15d25dc7bec7a10f0ecb72ba2e730553b2e"
EXPECTED_ACTION_BLOB_SHA = "72761ca23022940e8b98b8c7a8aea3f67c5b50a2"
IMPORT_ANCHOR = 'import "./ramzyActionControlPhase13.css";'
FLAGSHIP_IMPORT = 'import "./ramzyFlagshipV1.css";'
MARKER = "--tos-ramzy-flagship-v1"

print("RUNNING=TOS_UXUI_RAMZY_ASSISTANT_FLAGSHIP_V1")


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
            FLAGSHIP.unlink(missing_ok=True)
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("RAMZY_FLAGSHIP_V1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (FRONTEND, RAMZY, VOICE, ACTION, TCS_LAUNCHER, TCS_WINDOW, TCS_STYLE, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if git_blob_sha(VOICE) != EXPECTED_VOICE_BLOB_SHA:
    fail(f"Ramzy voice CSS baseline mismatch: {git_blob_sha(VOICE)}")
if git_blob_sha(ACTION) != EXPECTED_ACTION_BLOB_SHA:
    fail(f"Ramzy action CSS baseline mismatch: {git_blob_sha(ACTION)}")
if FLAGSHIP.exists():
    fail("Ramzy Flagship V1 CSS already exists; refusing non-idempotent reapply")

original_ramzy = RAMZY.read_text(encoding="utf-8")
if original_ramzy.count(IMPORT_ANCHOR) != 1:
    fail(f"Ramzy import anchor mismatch: {original_ramzy.count(IMPORT_ANCHOR)}")
if FLAGSHIP_IMPORT in original_ramzy:
    fail("Ramzy Flagship V1 import already present")
for token in (
    'className={`ramzy-panel opens-',
    'className="ramzy-panel-header"',
    'className="ramzy-messages"',
    'className="ramzy-composer"',
    'className="ramzy-approval-card"',
    'className="ramzy-launcher"',
    'className="ramzy-evidence-disclosure"',
):
    if token not in original_ramzy:
        fail(f"required Ramzy UI anchor missing: {token}")

# Preserve TCS byte-for-byte. It is explicitly out of scope.
tcs_before = {
    TCS_LAUNCHER: sha256(TCS_LAUNCHER),
    TCS_WINDOW: sha256(TCS_WINDOW),
    TCS_STYLE: sha256(TCS_STYLE),
}

css = r'''/* TOS_RAMZY_ASSISTANT_FLAGSHIP_V1
   UI-only premium layer. No agent/API/voice/approval behavior changes. */
.ramzy-assistant-root {
  --tos-ramzy-flagship-v1: 1;
  --ramzy-gold: #b7791f;
  --ramzy-gold-strong: #92400e;
  --ramzy-gold-soft: rgba(217, 119, 6, .10);
  --ramzy-border: rgba(24, 24, 27, .10);
  --ramzy-border-strong: rgba(217, 119, 6, .24);
  --ramzy-text: #18181b;
  --ramzy-muted: #71717a;
  --ramzy-surface: rgba(255, 255, 255, .96);
  --ramzy-surface-soft: rgba(250, 250, 249, .92);
  --ramzy-canvas: #faf9f6;
  --ramzy-shadow: 0 34px 90px rgba(15, 23, 42, .16), 0 12px 32px rgba(15, 23, 42, .07);
  --ramzy-shadow-soft: 0 14px 34px rgba(15, 23, 42, .07);
  font-family: var(--tos-font-ar, "Tajawal", "Cairo", system-ui, sans-serif);
}

.ramzy-panel {
  isolation: isolate;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,.86) !important;
  border-radius: 30px !important;
  background:
    radial-gradient(circle at 88% -8%, rgba(245,158,11,.15), transparent 34%),
    radial-gradient(circle at 5% 106%, rgba(120,53,15,.06), transparent 28%),
    linear-gradient(145deg, rgba(255,255,255,.985), rgba(250,249,246,.975) 58%, rgba(255,252,245,.97)) !important;
  color: var(--ramzy-text) !important;
  box-shadow: var(--ramzy-shadow) !important;
  backdrop-filter: blur(24px) saturate(1.12);
  -webkit-backdrop-filter: blur(24px) saturate(1.12);
}

.ramzy-panel::before {
  content: "";
  position: absolute;
  z-index: 0;
  inset: 0 0 auto;
  height: 4px;
  background: linear-gradient(90deg, transparent, rgba(217,119,6,.86) 25%, rgba(251,191,36,.92) 52%, rgba(146,64,14,.62) 78%, transparent) !important;
  pointer-events: none;
}
.ramzy-panel::after {
  content: "";
  position: absolute;
  z-index: 0;
  width: 260px;
  height: 260px;
  inset-inline-end: -120px;
  top: -150px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(245,158,11,.11), transparent 68%);
  pointer-events: none;
}
.ramzy-panel > * { position: relative; z-index: 1; }

.ramzy-panel-header {
  min-height: 88px !important;
  padding: 16px 18px !important;
  border-bottom: 1px solid var(--ramzy-border) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.94), rgba(255,255,255,.76)) !important;
  color: var(--ramzy-text) !important;
  box-shadow: 0 12px 30px rgba(15,23,42,.045) !important;
  backdrop-filter: blur(22px);
}
.ramzy-panel-identity { gap: 12px !important; min-width: 0; }
.ramzy-panel-identity img {
  width: 50px !important;
  height: 50px !important;
  padding: 3px;
  border: 1px solid rgba(217,119,6,.22);
  border-radius: 17px !important;
  background: linear-gradient(145deg,#fff,#fffbeb);
  box-shadow: 0 10px 24px rgba(120,53,15,.12), inset 0 1px 0 rgba(255,255,255,.9);
}
.ramzy-panel-identity strong {
  color: #18181b !important;
  font-size: 20px !important;
  font-weight: 950 !important;
  letter-spacing: -.035em;
}
.ramzy-panel-identity span {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 4px;
  color: #78716c !important;
  font-size: 11.5px !important;
  font-weight: 800 !important;
}
.ramzy-online-dot {
  width: 8px !important;
  height: 8px !important;
  background: #10b981 !important;
  box-shadow: 0 0 0 4px rgba(16,185,129,.11), 0 0 14px rgba(16,185,129,.28) !important;
}

.ramzy-panel-controls { gap: 7px !important; }
.ramzy-panel-controls button {
  width: 37px !important;
  height: 37px !important;
  border: 1px solid rgba(24,24,27,.08) !important;
  border-radius: 13px !important;
  background: rgba(255,255,255,.84) !important;
  color: #57534e !important;
  box-shadow: 0 8px 20px rgba(15,23,42,.055), inset 0 1px 0 rgba(255,255,255,.92) !important;
  transition: transform .16s ease, border-color .16s ease, background .16s ease, color .16s ease, box-shadow .16s ease !important;
}
.ramzy-panel-controls button:hover {
  transform: translateY(-1px) !important;
  border-color: rgba(217,119,6,.28) !important;
  background: rgba(255,251,235,.96) !important;
  color: #92400e !important;
  box-shadow: 0 11px 24px rgba(120,53,15,.09) !important;
}

.ramzy-history-select {
  margin: 12px 16px 0 !important;
  min-height: 42px;
  padding: 0 13px !important;
  border: 1px solid var(--ramzy-border) !important;
  border-radius: 14px !important;
  background: rgba(255,255,255,.92) !important;
  color: var(--ramzy-text) !important;
  box-shadow: 0 8px 20px rgba(15,23,42,.045) !important;
}
.ramzy-history-select:focus {
  border-color: rgba(217,119,6,.44) !important;
  outline: none;
  box-shadow: 0 0 0 4px rgba(245,158,11,.10) !important;
}

.ramzy-messages {
  padding: 22px !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(245,158,11,.065), transparent 24%),
    linear-gradient(180deg, #faf9f6 0%, #ffffff 38%, #fafafa 100%) !important;
  scrollbar-color: rgba(180,83,9,.24) transparent !important;
  scrollbar-gutter: stable;
}
.ramzy-messages::-webkit-scrollbar { width: 9px !important; }
.ramzy-messages::-webkit-scrollbar-track { background: transparent !important; }
.ramzy-messages::-webkit-scrollbar-thumb {
  border: 3px solid transparent !important;
  border-radius: 999px !important;
  background: rgba(180,83,9,.28) !important;
  background-clip: padding-box !important;
}

.ramzy-message { margin-bottom: 16px !important; }
.ramzy-message-content {
  max-width: 87% !important;
  padding: 14px 17px !important;
  border-radius: 20px !important;
  font-size: 14px !important;
  line-height: 1.9 !important;
  transition: transform .16s ease, box-shadow .16s ease !important;
}
.ramzy-message.user .ramzy-message-content {
  border: 1px solid rgba(24,24,27,.16) !important;
  border-radius: 20px 20px 6px 20px !important;
  background: linear-gradient(135deg, #18181b, #27272a 70%, #78350f) !important;
  color: #fff !important;
  box-shadow: 0 14px 30px rgba(24,24,27,.16), inset 0 1px 0 rgba(255,255,255,.13) !important;
}
.ramzy-message.assistant .ramzy-message-content {
  border: 1px solid rgba(24,24,27,.085) !important;
  border-radius: 20px 20px 20px 6px !important;
  background: rgba(255,255,255,.96) !important;
  color: #27272a !important;
  box-shadow: 0 13px 30px rgba(15,23,42,.065), inset 0 1px 0 rgba(255,255,255,.9) !important;
  backdrop-filter: blur(10px);
}
.ramzy-message.user .ramzy-message-content:hover,
.ramzy-message.assistant .ramzy-message-content:hover { transform: translateY(-1px); }

.ramzy-message-actions { gap: 4px !important; margin-top: 6px !important; color: #a8a29e !important; }
.ramzy-message-actions button {
  width: 28px !important;
  height: 28px !important;
  border: 1px solid transparent !important;
  border-radius: 9px !important;
  background: rgba(255,255,255,.72) !important;
  color: inherit !important;
}
.ramzy-message-actions button:hover {
  border-color: rgba(217,119,6,.16) !important;
  background: #fff7ed !important;
  color: #b45309 !important;
}

.ramzy-welcome {
  padding: 32px 12px !important;
  color: var(--ramzy-text) !important;
}
.ramzy-welcome > svg {
  width: 40px !important;
  height: 40px !important;
  padding: 9px !important;
  border: 1px solid rgba(217,119,6,.18);
  border-radius: 15px !important;
  background: linear-gradient(145deg,#fff,#fffbeb) !important;
  color: #b45309 !important;
  box-shadow: 0 12px 26px rgba(120,53,15,.10), inset 0 1px 0 #fff !important;
}
.ramzy-welcome strong { margin-top: 14px !important; font-size: 19px !important; font-weight: 950 !important; letter-spacing: -.025em; }
.ramzy-welcome p { max-width: 470px !important; color: #78716c !important; font-size: 13px !important; line-height: 1.8; }
.ramzy-suggestions {
  grid-template-columns: repeat(2,minmax(0,1fr)) !important;
  max-width: 590px !important;
  gap: 9px !important;
  margin-top: 18px !important;
}
.ramzy-suggestions button {
  min-height: 48px !important;
  padding: 11px 14px !important;
  border: 1px solid rgba(24,24,27,.08) !important;
  border-radius: 15px !important;
  background: rgba(255,255,255,.90) !important;
  color: #44403c !important;
  box-shadow: 0 8px 19px rgba(15,23,42,.045) !important;
  font-weight: 850 !important;
}
.ramzy-suggestions button:hover {
  transform: translateY(-1px) !important;
  border-color: rgba(217,119,6,.24) !important;
  background: #fffbeb !important;
  color: #92400e !important;
  box-shadow: 0 11px 24px rgba(120,53,15,.075) !important;
}

.ramzy-typing {
  border: 1px solid rgba(217,119,6,.14) !important;
  border-radius: 14px !important;
  background: #fffbeb !important;
  color: #92400e !important;
  box-shadow: 0 8px 18px rgba(120,53,15,.05) !important;
}
.ramzy-typing button { background: #fff !important; color: #92400e !important; }
.ramzy-error {
  border: 1px solid rgba(220,38,38,.14) !important;
  border-radius: 14px !important;
  background: #fff7f7 !important;
  color: #991b1b !important;
}

.ramzy-composer {
  gap: 10px !important;
  padding: 15px 16px 16px !important;
  border-top: 1px solid var(--ramzy-border) !important;
  background: rgba(255,255,255,.94) !important;
  box-shadow: 0 -15px 34px rgba(15,23,42,.045) !important;
  backdrop-filter: blur(22px);
}
.ramzy-composer textarea {
  min-height: 58px !important;
  padding: 14px 15px !important;
  border: 1px solid rgba(24,24,27,.11) !important;
  border-radius: 18px !important;
  background: #fafaf9 !important;
  color: #18181b !important;
  font-size: 14px !important;
  box-shadow: inset 0 1px 2px rgba(15,23,42,.025) !important;
}
.ramzy-composer textarea::placeholder { color: #a8a29e !important; }
.ramzy-composer textarea:focus {
  border-color: rgba(217,119,6,.48) !important;
  background: #fff !important;
  outline: none;
  box-shadow: 0 0 0 4px rgba(245,158,11,.10) !important;
}
.ramzy-composer-actions { gap: 8px !important; align-items: center; }
.ramzy-composer-actions button {
  width: 48px !important;
  height: 48px !important;
  border-radius: 16px !important;
}
.ramzy-voice-mode-select {
  min-width: 138px !important;
  height: 40px !important;
  border: 1px solid rgba(24,24,27,.09) !important;
  border-radius: 13px !important;
  background: #fafaf9 !important;
  color: #57534e !important;
  font-size: 11px !important;
  font-weight: 850 !important;
}
.ramzy-mic-button {
  border: 1px solid rgba(24,24,27,.09) !important;
  background: rgba(255,255,255,.95) !important;
  color: #57534e !important;
  box-shadow: 0 9px 20px rgba(15,23,42,.06) !important;
}
.ramzy-mic-button:hover:not(:disabled) { border-color: rgba(217,119,6,.24) !important; color: #b45309 !important; }
.ramzy-mic-button.is-listening {
  border-color: rgba(220,38,38,.20) !important;
  background: #fff1f2 !important;
  color: #dc2626 !important;
  box-shadow: 0 0 0 5px rgba(239,68,68,.07) !important;
}
.ramzy-send-button {
  border: 1px solid rgba(24,24,27,.18) !important;
  background: linear-gradient(135deg,#18181b,#27272a 72%,#78350f) !important;
  color: #fff !important;
  box-shadow: 0 12px 25px rgba(24,24,27,.16), inset 0 1px 0 rgba(255,255,255,.12) !important;
}
.ramzy-send-button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 16px 30px rgba(24,24,27,.20) !important; }
.ramzy-send-button:disabled { opacity: .46 !important; }
.ramzy-voice-status { color: #78716c !important; }
.ramzy-voice-status.is-listening { color: #b45309 !important; }

.ramzy-approval-card {
  border: 1px solid rgba(217,119,6,.18) !important;
  border-radius: 18px !important;
  background: linear-gradient(145deg,#fffdf7,#fffbeb) !important;
  color: #573716 !important;
  box-shadow: 0 11px 25px rgba(120,53,15,.055), inset 0 1px 0 rgba(255,255,255,.9) !important;
}
.ramzy-approval-title { color: #78350f !important; font-weight: 950 !important; }
.ramzy-approval-detail, .ramzy-approval-card > p { color: #78716c !important; }
.ramzy-confirmation-risk,
.ramzy-confirmation-mode,
.ramzy-confirmation-revision-count {
  border-color: rgba(180,83,9,.24) !important;
  background: rgba(255,255,255,.66);
  color: #92400e !important;
}
.ramzy-approval-actions button,
.ramzy-revision-actions button {
  min-height: 36px;
  border-radius: 11px !important;
  font-weight: 900 !important;
}
.ramzy-approval-actions button:not(.secondary):not(.danger),
.ramzy-revision-actions button:not(.secondary) {
  border: 1px solid #18181b !important;
  background: #18181b !important;
  color: #fff !important;
}
.ramzy-approval-actions .secondary,
.ramzy-revision-actions .secondary {
  border-color: rgba(24,24,27,.12) !important;
  background: rgba(255,255,255,.8) !important;
  color: #44403c !important;
}
.ramzy-approval-actions .danger { border-color: rgba(220,38,38,.18) !important; background: #fff1f2 !important; color: #b91c1c !important; }
.ramzy-revision-editor input,
.ramzy-revision-editor textarea,
.ramzy-revision-editor select {
  border-color: rgba(24,24,27,.12) !important;
  background: rgba(255,255,255,.86) !important;
  color: #27272a !important;
}

.ramzy-evidence-disclosure {
  margin-top: 7px;
  border: 1px solid rgba(24,24,27,.07);
  border-radius: 12px;
  background: rgba(250,250,249,.74);
  color: #57534e;
}
.ramzy-evidence-disclosure summary { padding: 7px 10px; color: #78716c; font-size: 11px; font-weight: 850; cursor: pointer; }
.ramzy-evidence-body { padding: 0 10px 9px; color: #78716c; }

.ramzy-markdown { color: inherit !important; }
.ramzy-markdown a { color: #b45309 !important; }
.ramzy-markdown code.ramzy-markdown-code { background: rgba(217,119,6,.09) !important; color: #78350f; }
.ramzy-markdown-pre {
  border-color: rgba(24,24,27,.10) !important;
  background: #18181b !important;
  color: #f4f4f5 !important;
}
.ramzy-markdown-table-wrap,
.ramzy-operational-table-wrap {
  border-color: rgba(24,24,27,.09) !important;
  border-radius: 14px !important;
  background: rgba(255,255,255,.92) !important;
  box-shadow: 0 9px 20px rgba(15,23,42,.045) !important;
}
.ramzy-markdown-table-wrap th,
.ramzy-operational-table th { background: #fafaf9 !important; color: #57534e !important; }
.ramzy-result-card {
  border-color: rgba(24,24,27,.08) !important;
  background: rgba(255,255,255,.92) !important;
  color: #27272a !important;
  box-shadow: 0 8px 18px rgba(15,23,42,.04) !important;
}
.ramzy-result-field > span { color: #78716c !important; }
.ramzy-result-field > b.ramzy-status-badge { background: #fffbeb !important; color: #92400e !important; }

.ramzy-minimized,
.ramzy-launcher-label,
.ramzy-greeting {
  border: 1px solid rgba(24,24,27,.09) !important;
  background: rgba(255,255,255,.95) !important;
  color: #292524 !important;
  box-shadow: 0 14px 32px rgba(15,23,42,.12), inset 0 1px 0 rgba(255,255,255,.9) !important;
  backdrop-filter: blur(18px);
}
.ramzy-launcher-label small { color: #78716c !important; }
.ramzy-avatar-ring {
  border: 1px solid rgba(217,119,6,.20) !important;
  background: linear-gradient(145deg,#fff,#fffbeb) !important;
  box-shadow: 0 16px 36px rgba(120,53,15,.14), 0 0 0 6px rgba(245,158,11,.10), inset 0 1px 0 #fff !important;
}
.ramzy-launcher:hover .ramzy-avatar-ring {
  box-shadow: 0 20px 42px rgba(120,53,15,.17), 0 0 0 8px rgba(245,158,11,.13), inset 0 1px 0 #fff !important;
}
.ramzy-launcher-close {
  border-color: rgba(24,24,27,.08) !important;
  background: #fff !important;
  color: #78716c !important;
  box-shadow: 0 8px 18px rgba(15,23,42,.12) !important;
}
.ramzy-launcher-close:hover { background: #fff7ed !important; color: #b45309 !important; }

/* True Obsidian/Titanium dark mode. This intentionally overrides the legacy
   "force Ramzy light" block in index.css without changing any JSX behavior. */
html.dark .ramzy-assistant-root {
  --ramzy-gold: #fbbf24;
  --ramzy-gold-strong: #fde68a;
  --ramzy-gold-soft: rgba(251,191,36,.11);
  --ramzy-border: rgba(255,255,255,.10);
  --ramzy-border-strong: rgba(251,191,36,.24);
  --ramzy-text: #f4f4f5;
  --ramzy-muted: #a1a1aa;
  --ramzy-surface: rgba(24,24,27,.94);
  --ramzy-surface-soft: rgba(39,39,42,.82);
  --ramzy-canvas: #0d0d0f;
  --ramzy-shadow: 0 36px 100px rgba(0,0,0,.52), 0 14px 34px rgba(0,0,0,.34);
  --ramzy-shadow-soft: 0 14px 34px rgba(0,0,0,.26);
}
html.dark .ramzy-panel {
  border-color: rgba(255,255,255,.10) !important;
  background:
    radial-gradient(circle at 88% -8%, rgba(251,191,36,.10), transparent 34%),
    radial-gradient(circle at 4% 108%, rgba(120,53,15,.10), transparent 30%),
    linear-gradient(145deg, rgba(24,24,27,.985), rgba(15,15,17,.985) 58%, rgba(9,9,11,.99)) !important;
  color: #f4f4f5 !important;
  box-shadow: var(--ramzy-shadow) !important;
}
html.dark .ramzy-panel-header {
  border-bottom-color: rgba(255,255,255,.09) !important;
  background: linear-gradient(180deg, rgba(39,39,42,.90), rgba(24,24,27,.78)) !important;
  color: #f4f4f5 !important;
  box-shadow: 0 14px 32px rgba(0,0,0,.18) !important;
}
html.dark .ramzy-panel-identity img {
  border-color: rgba(251,191,36,.22) !important;
  background: linear-gradient(145deg,rgba(63,63,70,.94),rgba(24,24,27,.96)) !important;
  box-shadow: 0 12px 28px rgba(0,0,0,.28), 0 0 0 4px rgba(251,191,36,.05) !important;
}
html.dark .ramzy-panel-identity strong { color: #fafafa !important; }
html.dark .ramzy-panel-identity span { color: #a1a1aa !important; }
html.dark .ramzy-panel-controls button {
  border-color: rgba(255,255,255,.09) !important;
  background: rgba(39,39,42,.82) !important;
  color: #d4d4d8 !important;
  box-shadow: 0 9px 20px rgba(0,0,0,.22) !important;
}
html.dark .ramzy-panel-controls button:hover {
  border-color: rgba(251,191,36,.22) !important;
  background: rgba(251,191,36,.09) !important;
  color: #fbbf24 !important;
}
html.dark .ramzy-history-select {
  border-color: rgba(255,255,255,.10) !important;
  background: rgba(39,39,42,.90) !important;
  color: #f4f4f5 !important;
}
html.dark .ramzy-messages {
  background:
    radial-gradient(circle at 100% 0%, rgba(251,191,36,.055), transparent 25%),
    linear-gradient(180deg,#111113 0%,#0d0d0f 46%,#09090b 100%) !important;
  scrollbar-color: rgba(251,191,36,.24) transparent !important;
}
html.dark .ramzy-messages::-webkit-scrollbar-thumb { background: rgba(251,191,36,.26) !important; background-clip: padding-box !important; }
html.dark .ramzy-message.user .ramzy-message-content {
  border-color: rgba(251,191,36,.16) !important;
  background: linear-gradient(135deg,#3f3f46,#27272a 68%,#78350f) !important;
  color: #fff !important;
  box-shadow: 0 15px 32px rgba(0,0,0,.30) !important;
}
html.dark .ramzy-message.assistant .ramzy-message-content {
  border-color: rgba(255,255,255,.09) !important;
  background: linear-gradient(145deg,rgba(39,39,42,.94),rgba(24,24,27,.94)) !important;
  color: #e4e4e7 !important;
  box-shadow: 0 14px 32px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.035) !important;
}
html.dark .ramzy-message-actions { color: #71717a !important; }
html.dark .ramzy-message-actions button { background: rgba(39,39,42,.72) !important; }
html.dark .ramzy-message-actions button:hover { border-color: rgba(251,191,36,.17) !important; background: rgba(251,191,36,.08) !important; color: #fbbf24 !important; }
html.dark .ramzy-welcome { color: #f4f4f5 !important; }
html.dark .ramzy-welcome > svg {
  border-color: rgba(251,191,36,.18) !important;
  background: linear-gradient(145deg,#3f3f46,#18181b) !important;
  color: #fbbf24 !important;
  box-shadow: 0 14px 28px rgba(0,0,0,.28) !important;
}
html.dark .ramzy-welcome p { color: #a1a1aa !important; }
html.dark .ramzy-suggestions button {
  border-color: rgba(255,255,255,.08) !important;
  background: rgba(39,39,42,.70) !important;
  color: #d4d4d8 !important;
  box-shadow: 0 9px 20px rgba(0,0,0,.18) !important;
}
html.dark .ramzy-suggestions button:hover { border-color: rgba(251,191,36,.20) !important; background: rgba(251,191,36,.08) !important; color: #fcd34d !important; }
html.dark .ramzy-typing { border-color: rgba(251,191,36,.15) !important; background: rgba(120,53,15,.20) !important; color: #fcd34d !important; }
html.dark .ramzy-typing button { background: rgba(39,39,42,.92) !important; color: #fde68a !important; }
html.dark .ramzy-error { border-color: rgba(248,113,113,.18) !important; background: rgba(127,29,29,.18) !important; color: #fecaca !important; }
html.dark .ramzy-composer {
  border-top-color: rgba(255,255,255,.09) !important;
  background: rgba(18,18,20,.94) !important;
  box-shadow: 0 -16px 34px rgba(0,0,0,.20) !important;
}
html.dark .ramzy-composer textarea {
  border-color: rgba(255,255,255,.10) !important;
  background: rgba(39,39,42,.72) !important;
  color: #f4f4f5 !important;
  box-shadow: inset 0 1px 2px rgba(0,0,0,.18) !important;
}
html.dark .ramzy-composer textarea::placeholder { color: #71717a !important; }
html.dark .ramzy-composer textarea:focus { border-color: rgba(251,191,36,.36) !important; background: #27272a !important; box-shadow: 0 0 0 4px rgba(251,191,36,.08) !important; }
html.dark .ramzy-voice-mode-select {
  border-color: rgba(255,255,255,.09) !important;
  background: rgba(39,39,42,.88) !important;
  color: #d4d4d8 !important;
}
html.dark .ramzy-mic-button { border-color: rgba(255,255,255,.09) !important; background: rgba(39,39,42,.90) !important; color: #d4d4d8 !important; box-shadow: 0 9px 20px rgba(0,0,0,.22) !important; }
html.dark .ramzy-mic-button:hover:not(:disabled) { color: #fbbf24 !important; }
html.dark .ramzy-send-button { border-color: rgba(251,191,36,.18) !important; background: linear-gradient(135deg,#52525b,#27272a 68%,#92400e) !important; box-shadow: 0 13px 28px rgba(0,0,0,.28) !important; }
html.dark .ramzy-voice-status { color: #a1a1aa !important; }
html.dark .ramzy-voice-status.is-listening { color: #fbbf24 !important; }
html.dark .ramzy-approval-card {
  border-color: rgba(251,191,36,.15) !important;
  background: linear-gradient(145deg,rgba(120,53,15,.18),rgba(39,39,42,.86)) !important;
  color: #fde68a !important;
  box-shadow: 0 12px 28px rgba(0,0,0,.22) !important;
}
html.dark .ramzy-approval-title { color: #fcd34d !important; }
html.dark .ramzy-approval-detail,
html.dark .ramzy-approval-card > p { color: #d6d3d1 !important; }
html.dark .ramzy-confirmation-risk,
html.dark .ramzy-confirmation-mode,
html.dark .ramzy-confirmation-revision-count { border-color: rgba(251,191,36,.18) !important; background: rgba(24,24,27,.52) !important; color: #fde68a !important; }
html.dark .ramzy-approval-actions button:not(.secondary):not(.danger),
html.dark .ramzy-revision-actions button:not(.secondary) { border-color: rgba(251,191,36,.16) !important; background: #fbbf24 !important; color: #18181b !important; }
html.dark .ramzy-approval-actions .secondary,
html.dark .ramzy-revision-actions .secondary { border-color: rgba(255,255,255,.10) !important; background: rgba(39,39,42,.82) !important; color: #e4e4e7 !important; }
html.dark .ramzy-approval-actions .danger { border-color: rgba(248,113,113,.18) !important; background: rgba(127,29,29,.20) !important; color: #fecaca !important; }
html.dark .ramzy-revision-editor input,
html.dark .ramzy-revision-editor textarea,
html.dark .ramzy-revision-editor select { border-color: rgba(255,255,255,.10) !important; background: rgba(24,24,27,.72) !important; color: #f4f4f5 !important; }
html.dark .ramzy-evidence-disclosure { border-color: rgba(255,255,255,.08) !important; background: rgba(39,39,42,.55) !important; color: #a1a1aa !important; }
html.dark .ramzy-evidence-disclosure summary,
html.dark .ramzy-evidence-body { color: #a1a1aa !important; }
html.dark .ramzy-markdown { color: #e4e4e7 !important; }
html.dark .ramzy-markdown a { color: #fbbf24 !important; }
html.dark .ramzy-markdown code.ramzy-markdown-code { background: rgba(251,191,36,.08) !important; color: #fde68a !important; }
html.dark .ramzy-markdown-pre { border-color: rgba(255,255,255,.09) !important; background: #09090b !important; color: #e4e4e7 !important; }
html.dark .ramzy-markdown-table-wrap,
html.dark .ramzy-operational-table-wrap { border-color: rgba(255,255,255,.08) !important; background: rgba(24,24,27,.88) !important; box-shadow: 0 9px 20px rgba(0,0,0,.18) !important; }
html.dark .ramzy-markdown-table-wrap th,
html.dark .ramzy-operational-table th { background: #27272a !important; color: #d4d4d8 !important; }
html.dark .ramzy-markdown-table-wrap td,
html.dark .ramzy-operational-table td { border-color: rgba(255,255,255,.07) !important; color: #e4e4e7 !important; }
html.dark .ramzy-result-card { border-color: rgba(255,255,255,.08) !important; background: rgba(39,39,42,.72) !important; color: #e4e4e7 !important; box-shadow: 0 8px 18px rgba(0,0,0,.18) !important; }
html.dark .ramzy-result-field > span { color: #a1a1aa !important; }
html.dark .ramzy-result-field > b.ramzy-status-badge { background: rgba(251,191,36,.10) !important; color: #fde68a !important; }
html.dark .ramzy-minimized,
html.dark .ramzy-launcher-label,
html.dark .ramzy-greeting { border-color: rgba(255,255,255,.09) !important; background: rgba(24,24,27,.94) !important; color: #f4f4f5 !important; box-shadow: 0 16px 36px rgba(0,0,0,.32) !important; }
html.dark .ramzy-launcher-label small { color: #a1a1aa !important; }
html.dark .ramzy-avatar-ring { border-color: rgba(251,191,36,.22) !important; background: linear-gradient(145deg,#3f3f46,#18181b) !important; box-shadow: 0 18px 40px rgba(0,0,0,.34), 0 0 0 6px rgba(251,191,36,.08) !important; }
html.dark .ramzy-launcher:hover .ramzy-avatar-ring { box-shadow: 0 22px 46px rgba(0,0,0,.40), 0 0 0 8px rgba(251,191,36,.11) !important; }
html.dark .ramzy-launcher-close { border-color: rgba(255,255,255,.09) !important; background: #27272a !important; color: #a1a1aa !important; box-shadow: 0 8px 20px rgba(0,0,0,.30) !important; }
html.dark .ramzy-launcher-close:hover { background: rgba(251,191,36,.10) !important; color: #fbbf24 !important; }

@media (max-width: 640px) {
  .ramzy-panel { border-radius: 24px !important; }
  .ramzy-panel-header { min-height: 72px !important; padding: 12px 13px !important; }
  .ramzy-panel-identity img { width: 42px !important; height: 42px !important; border-radius: 14px !important; }
  .ramzy-panel-identity strong { font-size: 17px !important; }
  .ramzy-panel-controls { gap: 4px !important; }
  .ramzy-panel-controls button { width: 31px !important; height: 31px !important; border-radius: 10px !important; }
  .ramzy-messages { padding: 14px !important; }
  .ramzy-message-content { max-width: 94% !important; padding: 12px 14px !important; font-size: 13px !important; }
  .ramzy-suggestions { grid-template-columns: 1fr !important; gap: 8px !important; }
  .ramzy-composer { padding: 11px !important; gap: 7px !important; }
  .ramzy-composer textarea { min-height: 50px !important; padding: 11px 12px !important; font-size: 13px !important; }
  .ramzy-voice-mode-select { min-width: 112px !important; max-width: 138px !important; height: 38px !important; }
  .ramzy-composer-actions button { width: 44px !important; height: 44px !important; border-radius: 14px !important; }
}

@media (prefers-reduced-motion: reduce) {
  .ramzy-panel *, .ramzy-launcher *, .ramzy-minimized { transition: none !important; animation: none !important; }
}
'''

created_css = False
try:
    next_ramzy = original_ramzy.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + FLAGSHIP_IMPORT, 1)
    if next_ramzy.count(FLAGSHIP_IMPORT) != 1:
        raise RuntimeError("Flagship import insertion failed")
    RAMZY.write_text(next_ramzy, encoding="utf-8")
    FLAGSHIP.write_text(css, encoding="utf-8")
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
    fail("Ramzy Flagship V1 marker missing from dist", original_ramzy, created_css)
for marker in (b"tos.ramzy.position", b"ramzy:approval", b"ramzy-voice-mode", b"data-tcs-ramzy-collision-sync"):
    if tree_count(DIST, marker) < 1:
        fail(f"preserved runtime marker missing: {marker.decode(errors='ignore')}", original_ramzy, created_css)

for path, before in tcs_before.items():
    if sha256(path) != before:
        fail(f"TCS out-of-scope file changed: {path}", original_ramzy, created_css)

# Safe live deploy via candidate + atomic rename. No service restart.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.ramzy-flagship-v1-candidate-{ts}"
backup = LIVE_PARENT / f"build.ramzy-flagship-v1-backup-{ts}"
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
print("RAMZY_FLAGSHIP_V1_RUNTIME=YES")
print("RAMZY_LIGHT_MODE=IVORY_CHAMPAGNE")
print("RAMZY_DARK_MODE=OBSIDIAN_TITANIUM")
print("LEGACY_FORCE_LIGHT_OVERRIDE=NEUTRALIZED_BY_SCOPED_FLAGSHIP_LAYER")
print("RAMZY_HEADER_PREMIUM=YES")
print("RAMZY_MESSAGES_PREMIUM=YES")
print("RAMZY_COMPOSER_PREMIUM=YES")
print("RAMZY_SUGGESTIONS_PREMIUM=YES")
print("RAMZY_APPROVALS_PREMIUM=YES")
print("RAMZY_EVIDENCE_TABLES_PREMIUM=YES")
print("RAMZY_LAUNCHER_PREMIUM=YES")
print("RAMZY_MOBILE_RESPONSIVE=YES")
print("RAMZY_AGENT_LOGIC_CHANGED=NO")
print("RAMZY_API_CHANGED=NO")
print("RAMZY_VOICE_LOGIC_CHANGED=NO")
print("RAMZY_APPROVAL_LOGIC_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("AUTH_CHANGED=NO")
print("TCS_CHANGED=NO")
print(f"FLAGSHIP_CSS_SHA256={sha256(FLAGSHIP)}")
print(f"RAMZY_JS_SHA256={sha256(RAMZY)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
