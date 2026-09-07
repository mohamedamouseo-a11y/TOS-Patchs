from pathlib import Path
import hashlib, shutil, subprocess, sys, time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
F = ROOT / "frontend"
RAMZY = F / "src/components/RamzyAssistant.jsx"
V1 = F / "src/components/ramzyFlagshipV1.css"
V2 = F / "src/components/ramzyFlagshipV2.css"
V21 = F / "src/components/ramzyFlagshipV2_1VisualCorrection.css"
V22 = F / "src/components/ramzyFlagshipV2_2DarkVisibilityPolish.css"
V23 = F / "src/components/ramzyFlagshipV2_3FinalLightLuxe.css"
VOICE = F / "src/components/ramzyVoicePhase11.css"
ACTION = F / "src/components/ramzyActionControlPhase13.css"
TCS = [F / "src/components/TcsFloatingLauncher.jsx", F / "src/components/TcsDesktopWindow.jsx", F / "src/components/tcsFlagshipV1.css"]
DIST = F / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED = {
    RAMZY: "0c4894c7616c544f44729845b120071b954ae35914cde8feb9677062bc207634",
    V22: "23c3dfdc1c2d6f64545a8e6e8cff20a4a81989c8922b9566d7876ffb58be42ae",
    V21: "7aba54dbe393ad04b91d59031218fd792a80c64e28d3b8cbffc5fb7f6d3c704a",
    V2: "fa986d1a91c58fa8593368d7c4ef014e8a843edd8475bcccb3b9ed57d3904755",
    V1: "1db0fc33bd8549a22a25a304a5272095d56933e5edd4ef8a954685a1d42909ad",
}
VOICE_BLOB = "b289a15d25dc7bec7a10f0ecb72ba2e730553b2e"
ACTION_BLOB = "72761ca23022940e8b98b8c7a8aea3f67c5b50a2"
OLD_IMPORT = 'import "./ramzyFlagshipV2_2DarkVisibilityPolish.css";'
NEW_IMPORT = 'import "./ramzyFlagshipV2_3FinalLightLuxe.css";'
MARKER = "--tos-ramzy-flagship-v2-3"

print("RUNNING=TOS_UXUI_RAMZY_ASSISTANT_FLAGSHIP_V2_3_FINAL_LIGHT_LUXE_POLISH")

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
def count_tree(root, needle):
    total = 0
    if not root.exists(): return 0
    for p in root.rglob("*"):
        if p.is_file():
            try: total += p.read_bytes().count(needle)
            except OSError: pass
    return total

def stop(msg, original=None, remove_v23=False):
    if original is not None:
        try: RAMZY.write_text(original, encoding="utf-8")
        except Exception: pass
    if remove_v23 and V23.exists():
        try: V23.unlink()
        except Exception: pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + msg)
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=SKIPPED_OR_ROLLED_BACK")
    print("RAMZY_FLAGSHIP_V2_3_RUNTIME=NO")
    raise SystemExit(1)

for p in [F, RAMZY, V1, V2, V21, V22, VOICE, ACTION, LIVE_PARENT, *TCS]:
    if not p.exists(): stop(f"required path missing: {p}")
for p, expected in EXPECTED.items():
    if sha(p) != expected: stop(f"baseline mismatch: {p.name}={sha(p)}")
if blob(VOICE) != VOICE_BLOB: stop("voice CSS baseline mismatch")
if blob(ACTION) != ACTION_BLOB: stop("action CSS baseline mismatch")
if V23.exists(): stop("V2.3 CSS already exists")

original = RAMZY.read_text(encoding="utf-8")
if original.count(OLD_IMPORT) != 1: stop("V2.2 import anchor mismatch")
if NEW_IMPORT in original: stop("V2.3 import already present")
for token in ['ramzy-panel opens-', 'ramzy-panel-header', 'ramzy-messages', 'ramzy-composer', 'ramzy-voice-mode-menu', 'ramzy-luxe-meta-strip', 'ramzy-launcher']:
    if token not in original: stop("missing Ramzy UI anchor: " + token)

tcs_before = {p: sha(p) for p in TCS}

css = r'''/* TOS_RAMZY_ASSISTANT_FLAGSHIP_V2_3_FINAL_LIGHT_LUXE */
.ramzy-assistant-root{--tos-ramzy-flagship-v2-3:1}
html:not(.dark) .ramzy-assistant-root{--v23-gold:#b97817;--v23-bright:#e8b84e;--v23-deep:#75480b;--v23-ink:#2b241c}
html:not(.dark) .ramzy-assistant-root .ramzy-panel{
 border-color:rgba(181,120,27,.42)!important;
 background:radial-gradient(circle at 91% -6%,rgba(232,184,77,.19),transparent 29%),radial-gradient(circle at 3% 108%,rgba(134,82,13,.055),transparent 26%),linear-gradient(148deg,#fffefa,#faf5eb 49%,#fffaf0)!important;
 color:#2b241c!important;
 box-shadow:0 0 0 1px rgba(255,255,255,.95),0 38px 100px rgba(86,60,27,.17),0 13px 32px rgba(54,42,26,.09),0 0 48px rgba(185,120,23,.07),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel::before{height:2px!important;background:linear-gradient(90deg,transparent,rgba(185,120,23,.42) 12%,#e9b84d 48%,rgba(185,120,23,.46) 85%,transparent)!important;box-shadow:0 0 18px rgba(233,184,77,.18)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel::after{opacity:.28!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel>.ramzy-panel-header{
 min-height:90px!important;border-bottom:1px solid rgba(154,101,19,.16)!important;
 background:linear-gradient(118deg,rgba(255,255,255,.995),rgba(250,245,234,.96) 58%,rgba(244,226,185,.56))!important;
 box-shadow:0 14px 34px rgba(73,53,26,.065),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel-identity img{border-color:rgba(185,120,23,.50)!important;background:linear-gradient(145deg,#fff,#f2dfb1)!important;box-shadow:0 0 0 4px rgba(233,184,77,.10),0 14px 30px rgba(112,75,18,.18),0 0 22px rgba(185,120,23,.10),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel-identity strong{color:#3a2a13!important;-webkit-text-fill-color:currentColor!important;background:none!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel-identity span{color:#6f665b!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel-controls button{border-color:rgba(154,101,19,.17)!important;background:linear-gradient(145deg,#fff,#f4ead8)!important;color:#5d5141!important;box-shadow:0 8px 19px rgba(68,49,26,.08),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel-controls button:hover{border-color:rgba(185,120,23,.40)!important;background:linear-gradient(145deg,#fffdf6,#f1ddb0)!important;color:#87520b!important;box-shadow:0 12px 25px rgba(118,75,14,.13),0 0 0 3px rgba(233,184,77,.075)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel>.ramzy-messages{background:radial-gradient(circle at 98% 0%,rgba(233,184,77,.075),transparent 24%),linear-gradient(180deg,#f8f3e9,#fbf8f2 46%,#f5efe5)!important;color:#2f2921!important}
html:not(.dark) .ramzy-assistant-root .ramzy-message.assistant .ramzy-message-content{border:1px solid rgba(154,101,19,.22)!important;background:radial-gradient(circle at 100% 0%,rgba(233,184,77,.11),transparent 27%),linear-gradient(145deg,#fffefa,#fffaf1)!important;color:#30291f!important;box-shadow:0 18px 40px rgba(81,57,26,.105),0 4px 12px rgba(40,33,23,.045),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-message.user .ramzy-message-content{border-color:rgba(120,78,15,.30)!important;background:linear-gradient(135deg,#332d25,#1d1c1a 67%,#80500d)!important;color:#fff!important;box-shadow:0 15px 34px rgba(31,27,22,.20),inset 0 1px 0 rgba(255,255,255,.10)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-markdown,html:not(.dark) .ramzy-assistant-root .ramzy-markdown p,html:not(.dark) .ramzy-assistant-root .ramzy-markdown li{color:#342d24!important}
html:not(.dark) .ramzy-assistant-root .ramzy-message-actions button{border-color:rgba(154,101,19,.13)!important;background:linear-gradient(145deg,#fff,#f4ecdf)!important;color:#82776b!important;box-shadow:0 6px 14px rgba(64,47,27,.06),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-message-actions button:hover{border-color:rgba(185,120,23,.28)!important;background:#fff5db!important;color:#a16410!important}
html:not(.dark) .ramzy-assistant-root .ramzy-evidence-disclosure{border-color:rgba(154,101,19,.20)!important;background:linear-gradient(145deg,#fffdf8,#f8efdd)!important;box-shadow:0 9px 22px rgba(72,51,27,.075),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-evidence-disclosure summary{color:#744813!important}
html:not(.dark) .ramzy-assistant-root .ramzy-markdown-table-wrap,html:not(.dark) .ramzy-assistant-root .ramzy-operational-table-wrap{border-color:rgba(154,101,19,.18)!important;background:#fffdf8!important;box-shadow:0 12px 28px rgba(67,48,27,.075),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-markdown-table-wrap th,html:not(.dark) .ramzy-assistant-root .ramzy-operational-table th{background:linear-gradient(180deg,#f6ead2,#efe0c2)!important;color:#66400f!important;border-color:rgba(154,101,19,.14)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-markdown-table-wrap td,html:not(.dark) .ramzy-assistant-root .ramzy-operational-table td{border-color:rgba(99,76,45,.09)!important;color:#3e352a!important}
html:not(.dark) .ramzy-assistant-root .ramzy-result-card{border-color:rgba(154,101,19,.16)!important;background:linear-gradient(145deg,#fffefa,#faf4e8)!important;color:#342d24!important;box-shadow:0 10px 24px rgba(66,47,26,.07)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel>.ramzy-composer{border-top:1px solid rgba(154,101,19,.18)!important;background:linear-gradient(180deg,#fbf5e9,#f5ead8)!important;box-shadow:0 -15px 34px rgba(70,50,27,.075),inset 0 1px 0 rgba(255,255,255,.92)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-composer>textarea{min-height:56px!important;border:1px solid rgba(154,101,19,.22)!important;background:#fffefa!important;color:#2f2921!important;box-shadow:inset 0 2px 6px rgba(73,51,27,.035),0 8px 20px rgba(73,51,27,.05)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-composer>textarea::placeholder{color:#9a9084!important;opacity:1!important}
html:not(.dark) .ramzy-assistant-root .ramzy-composer>textarea:focus{border-color:rgba(185,120,23,.48)!important;background:#fff!important;box-shadow:0 0 0 4px rgba(233,184,77,.11),0 12px 25px rgba(111,72,14,.085)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-trigger{border-color:rgba(154,101,19,.22)!important;background:linear-gradient(145deg,#fffdf8,#f1e3c7)!important;color:#453a2e!important;box-shadow:0 9px 21px rgba(79,56,27,.085),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-trigger:hover,html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-trigger.is-open{border-color:rgba(185,120,23,.43)!important;background:linear-gradient(145deg,#fffaf0,#ecd6a6)!important;box-shadow:0 12px 26px rgba(118,76,15,.13),0 0 0 3px rgba(233,184,77,.08)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-trigger-icon,html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-option-icon{border-color:rgba(154,101,19,.17)!important;background:rgba(255,255,255,.82)!important;color:#a16510!important}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-trigger-copy b{color:#4a3c2c!important}html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-trigger-copy small{color:#8c8072!important}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-popover{border-color:rgba(154,101,19,.24)!important;background:radial-gradient(circle at 100% 0%,rgba(233,184,77,.13),transparent 29%),linear-gradient(155deg,#fffefa,#f8efe0)!important;box-shadow:0 24px 62px rgba(72,50,24,.18),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-popover-kicker{color:#946018!important}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-popover>button{color:#493d30!important}
html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-popover>button:hover,html:not(.dark) .ramzy-assistant-root .ramzy-voice-mode-popover>button.is-selected{border-color:rgba(185,120,23,.19)!important;background:linear-gradient(135deg,#fff7e4,#f2e0bb)!important;color:#70450d!important}
html:not(.dark) .ramzy-assistant-root .ramzy-mic-button{border-color:rgba(154,101,19,.18)!important;background:linear-gradient(145deg,#fff,#efe4d1)!important;color:#665b4e!important;box-shadow:0 8px 19px rgba(72,51,27,.07),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-send-button{border-color:rgba(118,73,8,.34)!important;background:radial-gradient(circle at 34% 26%,#fff1bd,#edc35f 31%,#cd8f25 70%,#8d570e)!important;color:#241708!important;box-shadow:0 14px 30px rgba(142,88,14,.30),0 0 0 4px rgba(233,184,77,.11),0 0 22px rgba(201,138,36,.10),inset 0 1px 0 rgba(255,255,255,.72)!important}
html:not(.dark) .ramzy-assistant-root .ramzy-panel>.ramzy-luxe-meta-strip{border-top:1px solid rgba(154,101,19,.12)!important;background:linear-gradient(180deg,#f4e8d4,#efe0c5)!important;color:#786c5d!important}
html:not(.dark) .ramzy-assistant-root .ramzy-luxe-meta-brand{color:#655745!important}html:not(.dark) .ramzy-assistant-root .ramzy-luxe-meta-always{color:#956018!important}
html:not(.dark) .ramzy-assistant-root .ramzy-avatar-ring{border-color:rgba(185,120,23,.48)!important;background:linear-gradient(145deg,#fff,#ead6a7)!important;box-shadow:0 20px 46px rgba(91,62,24,.20),0 0 0 5px rgba(233,184,77,.12),0 0 30px rgba(185,120,23,.11),inset 0 1px 0 #fff!important}
html:not(.dark) .ramzy-assistant-root .ramzy-launcher-label,html:not(.dark) .ramzy-assistant-root .ramzy-greeting,html:not(.dark) .ramzy-assistant-root .ramzy-minimized{border-color:rgba(185,120,23,.25)!important;background:linear-gradient(145deg,#fffefa,#f3e5c9)!important;color:#3e3327!important;box-shadow:0 15px 34px rgba(73,51,27,.14),inset 0 1px 0 #fff!important}
'''

if "html.dark" in css: stop("V2.3 accidentally contains a dark selector")
if css.count("html:not(.dark)") < 20: stop("V2.3 light-only scoping too weak")

created = False
try:
    RAMZY.write_text(original.replace(OLD_IMPORT, OLD_IMPORT + "\n" + NEW_IMPORT, 1), encoding="utf-8")
    V23.write_text(css, encoding="utf-8")
    created = True
except Exception as exc:
    stop("source write failed: " + str(exc), original, created)

build = subprocess.run(["npm", "run", "build"], cwd=F, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-8000:]); print(build.stderr[-8000:])
    stop("frontend build failed", original, created)
if not (DIST / "index.html").exists(): stop("dist/index.html missing", original, created)
for marker in [MARKER.encode(), b"--tos-ramzy-flagship-v2-2", b"ramzy-voice-mode-menu", b"ramzy-luxe-meta-strip", b"tos.ramzy.position", b"ramzy:approval", b"data-tcs-ramzy-collision-sync"]:
    if count_tree(DIST, marker) < 1: stop("runtime marker missing: " + marker.decode(errors="ignore"), original, created)
for p, before in tcs_before.items():
    if sha(p) != before: stop("TCS changed: " + p.name, original, created)

ts = int(time.time())
candidate = LIVE_PARENT / f"build.ramzy-flagship-v2-3-candidate-{ts}"
backup = LIVE_PARENT / f"build.ramzy-flagship-v2-3-backup-{ts}"
shutil.copytree(DIST, candidate)
if not (candidate / "index.html").exists(): stop("candidate index missing", original, created)
try:
    LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    if backup.exists() and not LIVE.exists():
        try: backup.rename(LIVE)
        except Exception: pass
    stop("live deploy failed: " + str(exc), original, created)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("RAMZY_FLAGSHIP_V2_3_RUNTIME=YES")
print("RAMZY_V2_2_DARK_VISUAL_BASELINE=PRESERVED")
print("RAMZY_V2_3_SCOPE=LIGHT_MODE_ONLY")
print("RAMZY_LIGHT_OUTER_SHELL=CHAMPAGNE_DEPTH_UPGRADED")
print("RAMZY_LIGHT_HEADER=CONTRAST_UPGRADED")
print("RAMZY_LIGHT_ASSISTANT_CARD=CONTRAST_UPGRADED")
print("RAMZY_LIGHT_COMPOSER=UPGRADED")
print("RAMZY_LIGHT_VOICE_MENU=UPGRADED")
print("RAMZY_LIGHT_SEND_BUTTON=UPGRADED")
print("RAMZY_LIGHT_EVIDENCE_TABLES=UPGRADED")
print("RAMZY_LIGHT_META_STRIP=UPGRADED")
print("RAMZY_LIGHT_LAUNCHER=UPGRADED")
print("RAMZY_DARK_SELECTOR_ADDED=NO")
print("RAMZY_AGENT_LOGIC_CHANGED=NO")
print("RAMZY_API_CHANGED=NO")
print("RAMZY_VOICE_BEHAVIOR_CHANGED=NO")
print("RAMZY_APPROVAL_LOGIC_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("AUTH_CHANGED=NO")
print("TCS_CHANGED=NO")
print("V23_CSS_SHA256=" + sha(V23))
print("RAMZY_JS_SHA256=" + sha(RAMZY))
print("LIVE_BACKUP=" + str(backup))
print("STATUS=READY")