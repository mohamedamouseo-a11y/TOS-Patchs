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
VOICE = FRONTEND / "src/components/ramzyVoicePhase11.css"
ACTION = FRONTEND / "src/components/ramzyActionControlPhase13.css"
TCS_LAUNCHER = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
TCS_WINDOW = FRONTEND / "src/components/TcsDesktopWindow.jsx"
TCS_STYLE = FRONTEND / "src/components/tcsFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_RAMZY_V1_SHA256 = "9262b8fe8a03b0555038ffcbbf9934eca4631adbafe98391f48ce6e0f899bab7"
EXPECTED_V1_CSS_SHA256 = "1db0fc33bd8549a22a25a304a5272095d56933e5edd4ef8a954685a1d42909ad"
EXPECTED_VOICE_BLOB_SHA = "b289a15d25dc7bec7a10f0ecb72ba2e730553b2e"
EXPECTED_ACTION_BLOB_SHA = "72761ca23022940e8b98b8c7a8aea3f67c5b50a2"
V1_IMPORT = 'import "./ramzyFlagshipV1.css";'
V2_IMPORT = 'import "./ramzyFlagshipV2.css";'
MARKER = "--tos-ramzy-flagship-v2"
VOICE_STATE_ANCHOR = '  const [voiceMode, setVoiceMode] = useState(() => localStorage.getItem(`${RAMZY_VOICE_MODE_STORAGE_PREFIX}.${user?.id || "anonymous"}`) || "voice-input");'
VOICE_MENU_STATE = '  const [voiceModeMenuOpen, setVoiceModeMenuOpen] = useState(false);'
OLD_VOICE_SELECT = '''              <select className="ramzy-voice-mode-select" aria-label={isEnglish ? "Voice mode" : "وضع الصوت"} value={voiceMode} onChange={(event) => { stopVoiceInput(); stopVoicePlayback(); setVoiceMode(event.target.value); }}>
                <option value="text">{isEnglish ? "Text only" : "نص فقط"}</option>
                <option value="voice-input">{isEnglish ? "Voice input" : "إدخال صوتي"}</option>
                <option value="voice-conversation">{isEnglish ? "Voice conversation" : "محادثة صوتية"}</option>
              </select>'''
NEW_VOICE_MENU = '''              <div className="ramzy-voice-mode-menu" onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setVoiceModeMenuOpen(false); }}>
                <button type="button" className={`ramzy-voice-mode-trigger${voiceModeMenuOpen ? " is-open" : ""}`} aria-haspopup="listbox" aria-expanded={voiceModeMenuOpen} aria-label={isEnglish ? "Voice mode" : "وضع الصوت"} onClick={() => setVoiceModeMenuOpen((value) => !value)}>
                  <span className="ramzy-voice-mode-trigger-icon">{voiceMode === "text" ? <MessageCircle size={16} /> : voiceMode === "voice-input" ? <Mic size={16} /> : <Volume2 size={16} />}</span>
                  <span className="ramzy-voice-mode-trigger-copy"><b>{voiceMode === "text" ? (isEnglish ? "Text only" : "نص فقط") : voiceMode === "voice-input" ? (isEnglish ? "Voice input" : "إدخال صوتي") : (isEnglish ? "Voice conversation" : "محادثة صوتية")}</b><small>{isEnglish ? "Interaction mode" : "وضع التفاعل"}</small></span>
                  <span className="ramzy-voice-mode-chevron" aria-hidden="true" />
                </button>
                {voiceModeMenuOpen && (
                  <div className="ramzy-voice-mode-popover" role="listbox" aria-label={isEnglish ? "Choose interaction mode" : "اختر وضع التفاعل"}>
                    <div className="ramzy-voice-mode-popover-kicker">{isEnglish ? "Interaction mode" : "وضع التفاعل"}</div>
                    <button type="button" role="option" aria-selected={voiceMode === "text"} className={voiceMode === "text" ? "is-selected" : ""} onClick={() => { stopVoiceInput(); stopVoicePlayback(); setVoiceMode("text"); setVoiceModeMenuOpen(false); }}><span className="ramzy-voice-mode-option-icon"><MessageCircle size={16} /></span><span><b>{isEnglish ? "Text only" : "نص فقط"}</b><small>{isEnglish ? "Chat without audio" : "محادثة بدون صوت"}</small></span>{voiceMode === "text" && <Check size={15} className="ramzy-voice-mode-check" />}</button>
                    <button type="button" role="option" aria-selected={voiceMode === "voice-input"} className={voiceMode === "voice-input" ? "is-selected" : ""} onClick={() => { stopVoiceInput(); stopVoicePlayback(); setVoiceMode("voice-input"); setVoiceModeMenuOpen(false); }}><span className="ramzy-voice-mode-option-icon"><Mic size={16} /></span><span><b>{isEnglish ? "Voice input" : "إدخال صوتي"}</b><small>{isEnglish ? "Dictate directly into your prompt" : "حوّل كلامك مباشرة إلى نص"}</small></span>{voiceMode === "voice-input" && <Check size={15} className="ramzy-voice-mode-check" />}</button>
                    <button type="button" role="option" aria-selected={voiceMode === "voice-conversation"} className={voiceMode === "voice-conversation" ? "is-selected" : ""} onClick={() => { stopVoiceInput(); stopVoicePlayback(); setVoiceMode("voice-conversation"); setVoiceModeMenuOpen(false); }}><span className="ramzy-voice-mode-option-icon"><Volume2 size={16} /></span><span><b>{isEnglish ? "Voice conversation" : "محادثة صوتية"}</b><small>{isEnglish ? "Speak and hear Ramzy replies" : "تحدث واستمع إلى ردود رمزي"}</small></span>{voiceMode === "voice-conversation" && <Check size={15} className="ramzy-voice-mode-check" />}</button>
                  </div>
                )}
              </div>'''
FOOTER_ANCHOR = '''          </footer>
        </section>'''
FOOTER_REPLACEMENT = '''          </footer>
          <div className="ramzy-luxe-meta-strip">
            <span className="ramzy-luxe-meta-brand"><i />{isEnglish ? "Powered by TOS AI" : "مدعوم بواسطة TOS AI"}</span>
            <span className="ramzy-luxe-meta-separator" aria-hidden="true" />
            <span className="ramzy-luxe-meta-secure">{isEnglish ? "Secure workspace" : "مساحة عمل آمنة"}</span>
            <span className="ramzy-luxe-meta-spacer" />
            <span className="ramzy-luxe-meta-always">{isEnglish ? "Always here to help" : "دائمًا هنا للمساعدة"}</span>
          </div>
        </section>'''

print("RUNNING=TOS_UXUI_RAMZY_ASSISTANT_FLAGSHIP_V2")


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
            V2.unlink(missing_ok=True)
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("RAMZY_FLAGSHIP_V2_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (FRONTEND, RAMZY, V1, VOICE, ACTION, TCS_LAUNCHER, TCS_WINDOW, TCS_STYLE, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(RAMZY) != EXPECTED_RAMZY_V1_SHA256:
    fail(f"Ramzy V1 live-source baseline mismatch: {sha256(RAMZY)}")
if sha256(V1) != EXPECTED_V1_CSS_SHA256:
    fail(f"Ramzy V1 CSS baseline mismatch: {sha256(V1)}")
if git_blob_sha(VOICE) != EXPECTED_VOICE_BLOB_SHA:
    fail(f"Ramzy voice CSS baseline mismatch: {git_blob_sha(VOICE)}")
if git_blob_sha(ACTION) != EXPECTED_ACTION_BLOB_SHA:
    fail(f"Ramzy action CSS baseline mismatch: {git_blob_sha(ACTION)}")
if V2.exists():
    fail("Ramzy Flagship V2 CSS already exists; refusing non-idempotent reapply")

original_ramzy = RAMZY.read_text(encoding="utf-8")
if original_ramzy.count(V1_IMPORT) != 1:
    fail(f"V1 import anchor mismatch: {original_ramzy.count(V1_IMPORT)}")
if V2_IMPORT in original_ramzy:
    fail("V2 import already present")
if original_ramzy.count(VOICE_STATE_ANCHOR) != 1:
    fail(f"voice mode state anchor mismatch: {original_ramzy.count(VOICE_STATE_ANCHOR)}")
if VOICE_MENU_STATE in original_ramzy:
    fail("voice menu state already present")
if original_ramzy.count(OLD_VOICE_SELECT) != 1:
    fail(f"native voice select anchor mismatch: {original_ramzy.count(OLD_VOICE_SELECT)}")
if original_ramzy.count(FOOTER_ANCHOR) != 1:
    fail(f"footer anchor mismatch: {original_ramzy.count(FOOTER_ANCHOR)}")
for token in (
    'className={`ramzy-panel opens-',
    'className="ramzy-panel-header"',
    'className="ramzy-messages"',
    'className="ramzy-composer-actions"',
    'className="ramzy-approval-card"',
    'className="ramzy-launcher"',
    'className="ramzy-evidence-disclosure"',
):
    if token not in original_ramzy:
        fail(f"required Ramzy UI anchor missing: {token}")

# Explicitly preserve TCS byte-for-byte.
tcs_before = {
    TCS_LAUNCHER: sha256(TCS_LAUNCHER),
    TCS_WINDOW: sha256(TCS_WINDOW),
    TCS_STYLE: sha256(TCS_STYLE),
}

css = r'''/* TOS_RAMZY_ASSISTANT_FLAGSHIP_V2
   Luxe UI layer over V1. Logic/API/voice/approval behavior intentionally untouched. */
.ramzy-assistant-root {
  --tos-ramzy-flagship-v2: 1;
  --ramzy-v2-gold: #c98a24;
  --ramzy-v2-gold-bright: #f4c967;
  --ramzy-v2-gold-deep: #85520d;
  --ramzy-v2-ink: #171717;
  --ramzy-v2-muted: #78716c;
  --ramzy-v2-line: rgba(134, 88, 20, .18);
  --ramzy-v2-surface: rgba(255,255,255,.965);
  --ramzy-v2-soft: rgba(250,248,243,.92);
  --ramzy-v2-shadow: 0 42px 120px rgba(32, 24, 16, .18), 0 14px 38px rgba(15,23,42,.08);
}

/* ===== Outer flagship frame ===== */
.ramzy-panel {
  border: 1px solid rgba(180, 119, 27, .34) !important;
  border-radius: 32px !important;
  background:
    radial-gradient(circle at 86% -12%, rgba(244,201,103,.20), transparent 31%),
    radial-gradient(circle at 4% 110%, rgba(133,82,13,.08), transparent 29%),
    linear-gradient(145deg, #fffefa 0%, #faf7f0 58%, #fffdf8 100%) !important;
  box-shadow:
    0 0 0 1px rgba(255,255,255,.82),
    0 42px 120px rgba(32,24,16,.18),
    0 15px 38px rgba(15,23,42,.08),
    0 0 62px rgba(180,83,9,.07),
    inset 0 1px 0 rgba(255,255,255,.98) !important;
}
.ramzy-panel::before {
  height: 2px !important;
  inset: 0 22px auto !important;
  border-radius: 999px !important;
  background: linear-gradient(90deg, transparent, rgba(201,138,36,.46) 12%, #f4c967 48%, rgba(201,138,36,.52) 84%, transparent) !important;
  box-shadow: 0 0 18px rgba(244,201,103,.24);
}
.ramzy-panel::after {
  width: 330px !important;
  height: 230px !important;
  inset-inline-end: -64px !important;
  top: -86px !important;
  border-radius: 0 !important;
  opacity: .75;
  background:
    radial-gradient(circle at 1px 1px, rgba(180,119,27,.24) 1px, transparent 1.4px) 0 0/10px 10px,
    linear-gradient(135deg, transparent 18%, rgba(244,201,103,.08), transparent 66%) !important;
  -webkit-mask-image: linear-gradient(135deg, transparent 4%, #000 38%, transparent 88%);
  mask-image: linear-gradient(135deg, transparent 4%, #000 38%, transparent 88%);
}

/* ===== Header identity ===== */
.ramzy-panel-header {
  position: relative;
  min-height: 92px !important;
  padding: 17px 20px !important;
  border-bottom-color: rgba(134,88,20,.13) !important;
  background:
    linear-gradient(118deg, rgba(255,255,255,.98), rgba(252,249,242,.88) 58%, rgba(248,236,208,.56)) !important;
  box-shadow: 0 15px 35px rgba(70,51,24,.055) !important;
}
.ramzy-panel-header::after {
  content: "";
  position: absolute;
  inset-inline-end: 74px;
  top: 12px;
  width: 190px;
  height: 56px;
  pointer-events: none;
  background: linear-gradient(115deg, transparent, rgba(244,201,103,.12), transparent);
  transform: skewX(-24deg);
}
.ramzy-panel-identity {
  position: relative;
  isolation: isolate;
  gap: 14px !important;
}
.ramzy-panel-identity::before {
  content: "";
  position: absolute;
  z-index: -1;
  width: 64px;
  height: 64px;
  inset-inline-start: -7px;
  top: 50%;
  transform: translateY(-50%);
  border-radius: 22px;
  background: radial-gradient(circle, rgba(244,201,103,.28), transparent 67%);
  filter: blur(3px);
}
.ramzy-panel-identity img {
  width: 52px !important;
  height: 52px !important;
  padding: 3px !important;
  border: 1px solid rgba(201,138,36,.52) !important;
  border-radius: 18px !important;
  background: linear-gradient(145deg,#fff,#f9e9bd) !important;
  box-shadow:
    0 0 0 4px rgba(244,201,103,.10),
    0 13px 30px rgba(112,75,18,.18),
    inset 0 1px 0 rgba(255,255,255,.95) !important;
}
.ramzy-panel-identity strong {
  display: inline-block;
  color: #211b12 !important;
  font-size: 21px !important;
  font-weight: 950 !important;
  letter-spacing: -.045em !important;
}
.ramzy-panel-identity span { color: #756c60 !important; letter-spacing: .005em; }
.ramzy-online-dot {
  background: #16c784 !important;
  box-shadow: 0 0 0 4px rgba(22,199,132,.12), 0 0 16px rgba(22,199,132,.38) !important;
}

.ramzy-panel-controls button {
  width: 39px !important;
  height: 39px !important;
  border-color: rgba(134,88,20,.15) !important;
  border-radius: 13px !important;
  background: linear-gradient(145deg, rgba(255,255,255,.96), rgba(246,240,228,.90)) !important;
  color: #5d5142 !important;
  box-shadow: 0 9px 22px rgba(59,44,25,.08), inset 0 1px 0 rgba(255,255,255,.98) !important;
}
.ramzy-panel-controls button:hover {
  transform: translateY(-2px) !important;
  border-color: rgba(201,138,36,.42) !important;
  background: linear-gradient(145deg,#fffdf5,#f8e8be) !important;
  color: #8a570c !important;
  box-shadow: 0 13px 28px rgba(133,82,13,.14), 0 0 0 3px rgba(244,201,103,.08) !important;
}

/* ===== Conversation canvas + richer assistant cards ===== */
.ramzy-messages {
  padding: 22px 24px !important;
  background:
    radial-gradient(circle at 95% 4%, rgba(244,201,103,.09), transparent 25%),
    radial-gradient(circle at 3% 94%, rgba(133,82,13,.045), transparent 24%),
    linear-gradient(180deg,#fbfaf7 0%,#fff 44%,#faf9f6 100%) !important;
}
.ramzy-message-content {
  position: relative;
  overflow: hidden;
  max-width: 90% !important;
}
.ramzy-message.assistant .ramzy-message-content {
  border: 1px solid rgba(134,88,20,.16) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(244,201,103,.13), transparent 26%),
    linear-gradient(145deg,rgba(255,255,255,.985),rgba(252,249,243,.965)) !important;
  color: #2b261f !important;
  box-shadow:
    0 18px 42px rgba(61,45,24,.09),
    0 3px 10px rgba(15,23,42,.035),
    inset 0 1px 0 #fff !important;
}
.ramzy-message.assistant .ramzy-message-content::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background: linear-gradient(120deg, rgba(255,255,255,.65), transparent 25%, transparent 76%, rgba(244,201,103,.08));
}
.ramzy-message.user .ramzy-message-content {
  border-color: rgba(109,72,18,.25) !important;
  background: linear-gradient(135deg,#25211c,#171717 68%,#6f450b) !important;
  box-shadow: 0 16px 36px rgba(24,24,24,.18), inset 0 1px 0 rgba(255,255,255,.10) !important;
}
.ramzy-markdown p { line-height: 1.95; }
.ramzy-markdown h1,.ramzy-markdown h2,.ramzy-markdown h3 { letter-spacing: -.02em; }

.ramzy-message-actions {
  gap: 6px !important;
  margin-top: 8px !important;
}
.ramzy-message-actions button {
  width: 30px !important;
  height: 30px !important;
  border: 1px solid rgba(134,88,20,.10) !important;
  border-radius: 10px !important;
  background: linear-gradient(145deg,rgba(255,255,255,.94),rgba(247,243,235,.90)) !important;
  color: #8a8176 !important;
  box-shadow: 0 6px 14px rgba(45,34,22,.055), inset 0 1px 0 rgba(255,255,255,.96) !important;
}
.ramzy-message-actions button:hover {
  transform: translateY(-1px);
  border-color: rgba(201,138,36,.28) !important;
  background: #fff9e9 !important;
  color: #a66a13 !important;
  box-shadow: 0 9px 18px rgba(133,82,13,.10) !important;
}

/* ===== Evidence becomes a deliberate premium control ===== */
.ramzy-evidence-disclosure {
  width: max-content;
  max-width: 100%;
  margin-top: 9px !important;
  margin-inline-start: auto;
  border: 1px solid rgba(134,88,20,.14) !important;
  border-radius: 14px !important;
  background: linear-gradient(145deg,rgba(255,255,255,.94),rgba(250,246,236,.90)) !important;
  box-shadow: 0 8px 20px rgba(62,46,26,.06) !important;
}
.ramzy-evidence-disclosure summary {
  min-height: 34px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 7px 11px !important;
  color: #74511c !important;
  font-size: 10.5px !important;
  font-weight: 900 !important;
  list-style: none;
}
.ramzy-evidence-disclosure summary::-webkit-details-marker { display:none; }
.ramzy-evidence-disclosure summary::before { content: "◇"; color: #c98a24; font-size: 13px; }
.ramzy-evidence-disclosure summary::after { content: "›"; margin-inline-start: 5px; font-size: 15px; transition: transform .16s ease; }
.ramzy-evidence-disclosure[open] { width: min(100%, 460px); }
.ramzy-evidence-disclosure[open] summary::after { transform: rotate(90deg); }
.ramzy-evidence-body { padding: 0 12px 11px !important; }

/* ===== Composer dock ===== */
.ramzy-composer {
  position: relative;
  gap: 10px !important;
  padding: 13px 14px 10px !important;
  border-top: 1px solid rgba(134,88,20,.13) !important;
  background:
    linear-gradient(180deg,rgba(255,255,255,.91),rgba(249,246,239,.98)) !important;
  box-shadow: 0 -18px 42px rgba(59,44,25,.055) !important;
}
.ramzy-composer textarea {
  min-height: 58px !important;
  border: 1px solid rgba(134,88,20,.16) !important;
  border-radius: 19px !important;
  background: rgba(255,255,255,.93) !important;
  color: #29251f !important;
  box-shadow: inset 0 2px 7px rgba(59,44,25,.035), 0 10px 24px rgba(59,44,25,.045) !important;
}
.ramzy-composer textarea:focus {
  border-color: rgba(201,138,36,.52) !important;
  box-shadow: 0 0 0 4px rgba(244,201,103,.12), 0 13px 28px rgba(133,82,13,.075) !important;
}
.ramzy-composer-actions { align-items: flex-end !important; gap: 8px !important; }
.ramzy-send-button {
  width: 52px !important;
  height: 52px !important;
  border: 1px solid rgba(117,72,8,.30) !important;
  border-radius: 18px !important;
  background:
    radial-gradient(circle at 35% 28%, #ffe8a6 0%, #f4c967 34%, #d99a2b 70%, #9b6211 100%) !important;
  color: #24180a !important;
  box-shadow:
    0 13px 29px rgba(155,98,17,.28),
    0 0 0 4px rgba(244,201,103,.10),
    inset 0 1px 0 rgba(255,255,255,.70),
    inset 0 -2px 6px rgba(117,72,8,.18) !important;
}
.ramzy-send-button:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  filter: saturate(1.05) brightness(1.03);
  box-shadow: 0 17px 34px rgba(155,98,17,.34), 0 0 0 5px rgba(244,201,103,.13) !important;
}
.ramzy-mic-button {
  border-color: rgba(134,88,20,.13) !important;
  background: linear-gradient(145deg,#fff,#f4efe5) !important;
  color: #665c50 !important;
}

/* ===== Custom luxury interaction-mode menu ===== */
.ramzy-voice-mode-select { display:none !important; }
.ramzy-voice-mode-menu { position: relative; min-width: 174px; }
.ramzy-voice-mode-trigger {
  width: 178px;
  min-height: 48px;
  display: grid;
  grid-template-columns: 30px minmax(0,1fr) 12px;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid rgba(134,88,20,.16);
  border-radius: 15px;
  background: linear-gradient(145deg,rgba(255,255,255,.96),rgba(246,241,231,.94));
  color: #3a3228;
  box-shadow: 0 9px 22px rgba(59,44,25,.07), inset 0 1px 0 rgba(255,255,255,.95);
  text-align: start;
}
.ramzy-voice-mode-trigger:hover,
.ramzy-voice-mode-trigger.is-open {
  border-color: rgba(201,138,36,.40);
  background: linear-gradient(145deg,#fffdf7,#f8edcf);
  box-shadow: 0 12px 27px rgba(133,82,13,.11), 0 0 0 3px rgba(244,201,103,.07);
}
.ramzy-voice-mode-trigger-icon,
.ramzy-voice-mode-option-icon {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 1px solid rgba(134,88,20,.13);
  border-radius: 10px;
  background: rgba(255,255,255,.72);
  color: #a66a13;
}
.ramzy-voice-mode-trigger-copy,
.ramzy-voice-mode-popover button > span:nth-child(2) { min-width:0; display:flex; flex-direction:column; gap:2px; }
.ramzy-voice-mode-trigger-copy b,
.ramzy-voice-mode-popover button b { font-size: 11px; font-weight: 900; line-height: 1.25; }
.ramzy-voice-mode-trigger-copy small,
.ramzy-voice-mode-popover button small { color: #8a8176; font-size: 8.5px; font-weight: 750; line-height: 1.25; }
.ramzy-voice-mode-chevron {
  width: 7px;
  height: 7px;
  border-inline-end: 1.5px solid currentColor;
  border-bottom: 1.5px solid currentColor;
  transform: rotate(45deg) translateY(-2px);
  opacity: .62;
  transition: transform .16s ease;
}
.ramzy-voice-mode-trigger.is-open .ramzy-voice-mode-chevron { transform: rotate(225deg) translate(-1px,-1px); }
.ramzy-voice-mode-popover {
  position: absolute;
  z-index: 80;
  inset-inline-start: 0;
  bottom: calc(100% + 9px);
  width: 252px;
  padding: 8px;
  border: 1px solid rgba(134,88,20,.22);
  border-radius: 18px;
  background:
    radial-gradient(circle at 92% 0%, rgba(244,201,103,.14), transparent 34%),
    rgba(255,254,250,.985);
  box-shadow: 0 24px 60px rgba(48,35,20,.18), 0 0 0 1px rgba(255,255,255,.78) inset;
  backdrop-filter: blur(22px) saturate(1.12);
}
.ramzy-voice-mode-popover-kicker {
  padding: 5px 8px 7px;
  color: #9a6a22;
  font-size: 8.5px;
  font-weight: 950;
  letter-spacing: .10em;
  text-transform: uppercase;
}
.ramzy-voice-mode-popover button {
  width: 100%;
  min-height: 52px;
  display: grid;
  grid-template-columns: 34px minmax(0,1fr) 18px;
  align-items: center;
  gap: 9px;
  padding: 7px 8px;
  border: 1px solid transparent;
  border-radius: 13px;
  background: transparent;
  color: #3a3228;
  text-align: start;
}
.ramzy-voice-mode-popover button:hover { background: rgba(201,138,36,.07); border-color: rgba(201,138,36,.13); }
.ramzy-voice-mode-popover button.is-selected {
  border-color: rgba(201,138,36,.22);
  background: linear-gradient(135deg,rgba(255,248,229,.98),rgba(250,241,215,.84));
  color: #77480b;
}
.ramzy-voice-mode-check { color:#b97816; justify-self:end; }

/* ===== Approval / result surfaces ===== */
.ramzy-approval-card {
  border-color: rgba(201,138,36,.20) !important;
  background: radial-gradient(circle at 100% 0%,rgba(244,201,103,.14),transparent 28%),linear-gradient(145deg,#fffdf7,#fff8e8) !important;
  box-shadow: 0 15px 34px rgba(94,61,15,.08), inset 0 1px 0 #fff !important;
}
.ramzy-result-card,
.ramzy-operational-table-wrap,
.ramzy-markdown-table-wrap { box-shadow: 0 12px 28px rgba(59,44,25,.055), inset 0 1px 0 rgba(255,255,255,.88) !important; }

/* ===== Meta strip gives the panel a finished product edge ===== */
.ramzy-luxe-meta-strip {
  flex: 0 0 auto;
  min-height: 34px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 15px 9px;
  border-top: 1px solid rgba(134,88,20,.10);
  background: linear-gradient(180deg,rgba(249,246,239,.97),rgba(247,243,234,.99));
  color: #90877c;
  font-size: 8.5px;
  font-weight: 800;
}
.ramzy-luxe-meta-brand { display:flex; align-items:center; gap:6px; color:#766a5c; }
.ramzy-luxe-meta-brand i { width:6px; height:6px; border-radius:999px; background:#c98a24; box-shadow:0 0 10px rgba(201,138,36,.30); }
.ramzy-luxe-meta-separator { width:1px; height:10px; background:rgba(134,88,20,.18); }
.ramzy-luxe-meta-spacer { flex:1; }
.ramzy-luxe-meta-always { color:#9a6a22; }

/* ===== Launcher: jewelry-like floating identity ===== */
.ramzy-avatar-ring {
  position: relative;
  border: 1px solid rgba(201,138,36,.50) !important;
  background: linear-gradient(145deg,#fffdf7,#edd79d) !important;
  box-shadow:
    0 20px 46px rgba(97,63,14,.19),
    0 0 0 5px rgba(244,201,103,.13),
    0 0 28px rgba(201,138,36,.14),
    inset 0 1px 0 #fff !important;
}
.ramzy-launcher:hover .ramzy-avatar-ring {
  transform: translateY(-2px) scale(1.025);
  box-shadow: 0 24px 54px rgba(97,63,14,.23), 0 0 0 7px rgba(244,201,103,.16), 0 0 36px rgba(201,138,36,.18) !important;
}
.ramzy-launcher-label,.ramzy-greeting,.ramzy-minimized {
  border-color: rgba(201,138,36,.24) !important;
  background: linear-gradient(145deg,rgba(255,255,255,.97),rgba(249,244,231,.96)) !important;
  box-shadow: 0 17px 38px rgba(67,49,27,.14), inset 0 1px 0 #fff !important;
}

/* ========================================================================
   TRUE FLAGSHIP DARK: obsidian, black titanium, restrained cinematic gold
   ======================================================================== */
html.dark .ramzy-assistant-root {
  --ramzy-v2-gold: #d6a33a;
  --ramzy-v2-gold-bright: #f8d77b;
  --ramzy-v2-gold-deep: #8a5a10;
}
html.dark .ramzy-panel {
  border-color: rgba(236,190,91,.28) !important;
  background:
    radial-gradient(circle at 86% -11%, rgba(248,215,123,.15), transparent 32%),
    radial-gradient(circle at 5% 110%, rgba(138,90,16,.13), transparent 31%),
    linear-gradient(148deg,#181716 0%,#101011 47%,#08090a 100%) !important;
  color:#f5f2eb !important;
  box-shadow:
    0 0 0 1px rgba(255,255,255,.035),
    0 46px 130px rgba(0,0,0,.70),
    0 18px 44px rgba(0,0,0,.42),
    0 0 80px rgba(180,110,18,.11),
    inset 0 1px 0 rgba(255,235,188,.055) !important;
}
html.dark .ramzy-panel::before {
  background: linear-gradient(90deg,transparent,rgba(214,163,58,.25) 10%,#f8d77b 49%,rgba(214,163,58,.31) 86%,transparent) !important;
  box-shadow: 0 0 24px rgba(248,215,123,.22);
}
html.dark .ramzy-panel::after {
  opacity:.62;
  background: radial-gradient(circle at 1px 1px,rgba(248,215,123,.24) 1px,transparent 1.4px) 0 0/10px 10px,linear-gradient(135deg,transparent 18%,rgba(248,215,123,.09),transparent 66%) !important;
}
html.dark .ramzy-panel-header {
  border-bottom-color: rgba(248,215,123,.10) !important;
  background:
    linear-gradient(118deg,rgba(31,30,29,.96),rgba(19,19,20,.93) 58%,rgba(55,42,19,.42)) !important;
  box-shadow: 0 17px 38px rgba(0,0,0,.24) !important;
}
html.dark .ramzy-panel-header::after { background:linear-gradient(115deg,transparent,rgba(248,215,123,.08),transparent); }
html.dark .ramzy-panel-identity::before { background:radial-gradient(circle,rgba(248,215,123,.20),transparent 67%); }
html.dark .ramzy-panel-identity img {
  border-color: rgba(248,215,123,.55) !important;
  background: linear-gradient(145deg,#39342b,#151515) !important;
  box-shadow: 0 0 0 4px rgba(248,215,123,.08),0 15px 34px rgba(0,0,0,.46),0 0 22px rgba(214,163,58,.12) !important;
}
html.dark .ramzy-panel-identity strong {
  color: #f5d77c !important;
  background: linear-gradient(90deg,#f7dda0,#d7a843 62%,#f6d579);
  -webkit-background-clip:text;
  background-clip:text;
  -webkit-text-fill-color:transparent;
}
html.dark .ramzy-panel-identity span { color:#a9a39b !important; }
html.dark .ramzy-panel-controls button {
  border-color: rgba(248,215,123,.12) !important;
  background: linear-gradient(145deg,rgba(48,47,45,.88),rgba(25,25,26,.96)) !important;
  color:#c8c2b8 !important;
  box-shadow:0 10px 24px rgba(0,0,0,.32),inset 0 1px 0 rgba(255,255,255,.045) !important;
}
html.dark .ramzy-panel-controls button:hover {
  border-color: rgba(248,215,123,.34) !important;
  background: linear-gradient(145deg,rgba(67,55,31,.92),rgba(29,28,27,.98)) !important;
  color:#f8d77b !important;
  box-shadow:0 13px 29px rgba(0,0,0,.38),0 0 0 3px rgba(248,215,123,.055) !important;
}
html.dark .ramzy-messages {
  background:
    radial-gradient(circle at 98% 0%,rgba(248,215,123,.055),transparent 25%),
    radial-gradient(circle at 3% 98%,rgba(138,90,16,.055),transparent 23%),
    linear-gradient(180deg,#121212 0%,#0c0d0e 49%,#090a0b 100%) !important;
}
html.dark .ramzy-message.assistant .ramzy-message-content {
  border-color: rgba(248,215,123,.15) !important;
  background:
    radial-gradient(circle at 100% 0%,rgba(248,215,123,.075),transparent 28%),
    linear-gradient(145deg,rgba(35,35,35,.96),rgba(22,22,23,.97)) !important;
  color:#e9e6df !important;
  box-shadow:0 20px 46px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.035) !important;
}
html.dark .ramzy-message.assistant .ramzy-message-content::after { background:linear-gradient(120deg,rgba(255,255,255,.025),transparent 26%,transparent 76%,rgba(248,215,123,.045)); }
html.dark .ramzy-message.user .ramzy-message-content {
  border-color: rgba(248,215,123,.18) !important;
  background: linear-gradient(135deg,#343330,#1f1f20 66%,#6d450b) !important;
  box-shadow:0 17px 38px rgba(0,0,0,.40),inset 0 1px 0 rgba(255,255,255,.045) !important;
}
html.dark .ramzy-message-actions button {
  border-color:rgba(248,215,123,.07) !important;
  background:linear-gradient(145deg,rgba(43,43,42,.86),rgba(24,24,25,.94)) !important;
  color:#77736d !important;
  box-shadow:0 7px 16px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.025) !important;
}
html.dark .ramzy-message-actions button:hover { border-color:rgba(248,215,123,.18) !important; background:rgba(248,215,123,.075) !important; color:#f0c968 !important; }
html.dark .ramzy-evidence-disclosure {
  border-color:rgba(248,215,123,.13) !important;
  background:linear-gradient(145deg,rgba(41,38,31,.88),rgba(22,22,23,.94)) !important;
  box-shadow:0 10px 22px rgba(0,0,0,.25) !important;
}
html.dark .ramzy-evidence-disclosure summary { color:#d7b967 !important; }
html.dark .ramzy-evidence-body { color:#a8a29a !important; }
html.dark .ramzy-composer {
  border-top-color:rgba(248,215,123,.09) !important;
  background:linear-gradient(180deg,rgba(17,17,18,.96),rgba(10,11,12,.99)) !important;
  box-shadow:0 -18px 44px rgba(0,0,0,.27) !important;
}
html.dark .ramzy-composer textarea {
  border-color:rgba(248,215,123,.12) !important;
  background:linear-gradient(145deg,rgba(34,34,34,.92),rgba(22,22,23,.94)) !important;
  color:#f0ede7 !important;
  box-shadow:inset 0 2px 7px rgba(0,0,0,.25),0 10px 25px rgba(0,0,0,.18) !important;
}
html.dark .ramzy-composer textarea::placeholder { color:#77736d !important; }
html.dark .ramzy-composer textarea:focus { border-color:rgba(248,215,123,.34) !important; box-shadow:0 0 0 4px rgba(248,215,123,.065),0 13px 28px rgba(0,0,0,.24) !important; }
html.dark .ramzy-mic-button { border-color:rgba(248,215,123,.10) !important; background:linear-gradient(145deg,#302f2d,#1b1b1c) !important; color:#b8b2aa !important; }
html.dark .ramzy-send-button {
  border-color:rgba(248,215,123,.32) !important;
  background:radial-gradient(circle at 35% 28%,#ffe9a8 0%,#f8d77b 31%,#d6a33a 68%,#8a5a10 100%) !important;
  color:#201507 !important;
  box-shadow:0 15px 34px rgba(138,90,16,.34),0 0 0 4px rgba(248,215,123,.08),0 0 25px rgba(214,163,58,.12),inset 0 1px 0 rgba(255,255,255,.58) !important;
}
html.dark .ramzy-voice-mode-trigger {
  border-color:rgba(248,215,123,.12);
  background:linear-gradient(145deg,rgba(42,41,39,.94),rgba(23,23,24,.98));
  color:#e0dbd1;
  box-shadow:0 10px 24px rgba(0,0,0,.30),inset 0 1px 0 rgba(255,255,255,.03);
}
html.dark .ramzy-voice-mode-trigger:hover,
html.dark .ramzy-voice-mode-trigger.is-open { border-color:rgba(248,215,123,.27); background:linear-gradient(145deg,rgba(58,49,31,.94),rgba(25,25,26,.98)); box-shadow:0 13px 29px rgba(0,0,0,.35),0 0 0 3px rgba(248,215,123,.045); }
html.dark .ramzy-voice-mode-trigger-icon,
html.dark .ramzy-voice-mode-option-icon { border-color:rgba(248,215,123,.11); background:rgba(255,255,255,.025); color:#e2b94f; }
html.dark .ramzy-voice-mode-trigger-copy small,
html.dark .ramzy-voice-mode-popover button small { color:#858079; }
html.dark .ramzy-voice-mode-popover {
  border-color:rgba(248,215,123,.16);
  background:radial-gradient(circle at 92% 0%,rgba(248,215,123,.08),transparent 35%),rgba(18,18,19,.985);
  box-shadow:0 28px 70px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.025) inset;
}
html.dark .ramzy-voice-mode-popover-kicker { color:#c39a3a; }
html.dark .ramzy-voice-mode-popover button { color:#d8d3cb; }
html.dark .ramzy-voice-mode-popover button:hover { background:rgba(248,215,123,.055); border-color:rgba(248,215,123,.09); }
html.dark .ramzy-voice-mode-popover button.is-selected { border-color:rgba(248,215,123,.16); background:linear-gradient(135deg,rgba(78,59,25,.46),rgba(34,31,25,.58)); color:#f3d47a; }
html.dark .ramzy-voice-mode-check { color:#f0c968; }
html.dark .ramzy-approval-card { border-color:rgba(248,215,123,.14) !important; background:radial-gradient(circle at 100% 0%,rgba(248,215,123,.07),transparent 28%),linear-gradient(145deg,rgba(52,43,26,.55),rgba(26,26,27,.91)) !important; box-shadow:0 16px 36px rgba(0,0,0,.30) !important; }
html.dark .ramzy-luxe-meta-strip {
  border-top-color:rgba(248,215,123,.08);
  background:linear-gradient(180deg,rgba(14,14,15,.98),rgba(10,10,11,1));
  color:#6f6b65;
}
html.dark .ramzy-luxe-meta-brand { color:#938b7e; }
html.dark .ramzy-luxe-meta-brand i { background:#d6a33a; box-shadow:0 0 12px rgba(214,163,58,.28); }
html.dark .ramzy-luxe-meta-separator { background:rgba(248,215,123,.11); }
html.dark .ramzy-luxe-meta-always { color:#b9943d; }
html.dark .ramzy-avatar-ring {
  border-color:rgba(248,215,123,.50) !important;
  background:linear-gradient(145deg,#37332a,#151515) !important;
  box-shadow:0 22px 52px rgba(0,0,0,.48),0 0 0 5px rgba(248,215,123,.10),0 0 34px rgba(214,163,58,.15),inset 0 1px 0 rgba(255,255,255,.045) !important;
}
html.dark .ramzy-launcher:hover .ramzy-avatar-ring { box-shadow:0 27px 60px rgba(0,0,0,.55),0 0 0 7px rgba(248,215,123,.13),0 0 42px rgba(214,163,58,.18) !important; }
html.dark .ramzy-launcher-label,
html.dark .ramzy-greeting,
html.dark .ramzy-minimized { border-color:rgba(248,215,123,.18) !important; background:linear-gradient(145deg,rgba(35,34,32,.96),rgba(17,17,18,.98)) !important; color:#eeeae2 !important; box-shadow:0 18px 42px rgba(0,0,0,.42),inset 0 1px 0 rgba(255,255,255,.035) !important; }

@media (max-width: 640px) {
  .ramzy-panel { border-radius: 25px !important; }
  .ramzy-panel::before { inset-inline: 16px !important; }
  .ramzy-panel-header { min-height: 74px !important; padding: 12px 13px !important; }
  .ramzy-panel-header::after { display:none; }
  .ramzy-panel-identity img { width:43px !important; height:43px !important; border-radius:14px !important; }
  .ramzy-panel-identity::before { width:52px; height:52px; }
  .ramzy-panel-identity strong { font-size:17px !important; }
  .ramzy-panel-controls button { width:31px !important; height:31px !important; border-radius:10px !important; }
  .ramzy-messages { padding:14px !important; }
  .ramzy-message-content { max-width:96% !important; }
  .ramzy-composer { padding:10px !important; }
  .ramzy-voice-mode-menu { min-width:142px; }
  .ramzy-voice-mode-trigger { width:148px; min-height:44px; grid-template-columns:26px minmax(0,1fr) 10px; padding:5px 7px; }
  .ramzy-voice-mode-trigger-icon { width:26px; height:26px; border-radius:8px; }
  .ramzy-voice-mode-trigger-copy small { display:none; }
  .ramzy-voice-mode-popover { width:min(244px,calc(100vw - 34px)); }
  .ramzy-send-button { width:46px !important; height:46px !important; border-radius:15px !important; }
  .ramzy-luxe-meta-strip { padding-inline:11px; font-size:8px; }
  .ramzy-luxe-meta-secure,.ramzy-luxe-meta-separator { display:none; }
}

@media (prefers-reduced-motion: reduce) {
  .ramzy-panel *, .ramzy-launcher *, .ramzy-minimized { transition:none !important; animation:none !important; }
}
'''

created_css = False
try:
    next_ramzy = original_ramzy.replace(V1_IMPORT, V1_IMPORT + "\n" + V2_IMPORT, 1)
    next_ramzy = next_ramzy.replace(VOICE_STATE_ANCHOR, VOICE_STATE_ANCHOR + "\n" + VOICE_MENU_STATE, 1)
    next_ramzy = next_ramzy.replace(OLD_VOICE_SELECT, NEW_VOICE_MENU, 1)
    next_ramzy = next_ramzy.replace(FOOTER_ANCHOR, FOOTER_REPLACEMENT, 1)
    if next_ramzy.count(V2_IMPORT) != 1:
        raise RuntimeError("V2 import insertion failed")
    if next_ramzy.count(VOICE_MENU_STATE) != 1:
        raise RuntimeError("voice menu state insertion failed")
    if 'className="ramzy-voice-mode-popover"' not in next_ramzy:
        raise RuntimeError("custom voice mode menu insertion failed")
    if 'className="ramzy-luxe-meta-strip"' not in next_ramzy:
        raise RuntimeError("luxe meta strip insertion failed")
    if 'className="ramzy-voice-mode-select"' in next_ramzy:
        raise RuntimeError("native voice select remained after V2 replacement")
    RAMZY.write_text(next_ramzy, encoding="utf-8")
    V2.write_text(css, encoding="utf-8")
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
    fail("Ramzy Flagship V2 marker missing from dist", original_ramzy, created_css)
for marker in (
    b"ramzy-voice-mode-popover",
    b"ramzy-luxe-meta-strip",
    b"tos.ramzy.position",
    b"ramzy:approval",
    b"ramzy-voice-mode",
    b"data-tcs-ramzy-collision-sync",
):
    if tree_count(DIST, marker) < 1:
        fail(f"required/preserved runtime marker missing: {marker.decode(errors='ignore')}", original_ramzy, created_css)

for path, before in tcs_before.items():
    if sha256(path) != before:
        fail(f"TCS out-of-scope file changed: {path}", original_ramzy, created_css)

# Safe live deploy via candidate + atomic rename. No service restart.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.ramzy-flagship-v2-candidate-{ts}"
backup = LIVE_PARENT / f"build.ramzy-flagship-v2-backup-{ts}"
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
print("RAMZY_FLAGSHIP_V2_RUNTIME=YES")
print("RAMZY_OUTER_SHELL_LUXE=YES")
print("RAMZY_HEADER_LUXE=YES")
print("RAMZY_ASSISTANT_CARDS_LUXE=YES")
print("RAMZY_COMPOSER_LUXE=YES")
print("RAMZY_NATIVE_VOICE_SELECT=REMOVED")
print("RAMZY_CUSTOM_VOICE_MENU_LUXE=YES")
print("RAMZY_ACTIONS_LUXE=YES")
print("RAMZY_EVIDENCE_PILL_LUXE=YES")
print("RAMZY_META_STRIP_LUXE=YES")
print("RAMZY_LAUNCHER_LUXE=YES")
print("RAMZY_DARK_MODE=OBSIDIAN_BLACK_TITANIUM_GOLD")
print("RAMZY_LIGHT_MODE=IVORY_CHAMPAGNE_PRESERVED")
print("RAMZY_MOBILE_RESPONSIVE=YES")
print("RAMZY_AGENT_LOGIC_CHANGED=NO")
print("RAMZY_API_CHANGED=NO")
print("RAMZY_VOICE_BEHAVIOR_CHANGED=NO")
print("RAMZY_APPROVAL_LOGIC_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("AUTH_CHANGED=NO")
print("TCS_CHANGED=NO")
print(f"V2_CSS_SHA256={sha256(V2)}")
print(f"RAMZY_JS_SHA256={sha256(RAMZY)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")