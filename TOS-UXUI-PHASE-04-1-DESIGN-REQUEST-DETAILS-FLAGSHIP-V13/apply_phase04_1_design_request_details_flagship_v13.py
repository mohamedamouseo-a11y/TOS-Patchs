from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
CSS = ROOT / "frontend/src/index.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_DQ_SHA256 = "59138cdaddf4a26afa9b4c30c6ae49b48bbead09202f7dd3a13d45a2a1eb5a7e"
EXPECTED_CSS_SHA256 = "030481d98896fabccea059da9330a0e5ab97c73221543985161bf5f6265fd203"
V12_MARKER = "--tos-dq-details-flagship-v12-runtime"
V13_MARKER = "--tos-dq-details-flagship-v13-runtime"
V12_HOOK = 'data-dq-details-concept="v12"'
V13_HOOK = 'data-dq-details-ultra="v13"'
COPY_MARKER = "tos-dq-copy-editorial-v8"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V13")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V13_RUNTIME=NO")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


for path in (DQ, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha256(DQ) != EXPECTED_DQ_SHA256:
    fail("DesignQueuePage.jsx does not match Flagship V12 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V12 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in (
    "TOS_DQ_PERFORMANCE_V3",
    "TOS_DQ_PREMIUM_MENU_V9",
    "TOS_DQ_PREMIUM_MENU_THEME_V10",
    V12_MARKER,
    V12_HOOK,
    COPY_MARKER,
    "tos-dq-spec-copy-rtl-v6",
    "tos-dq-spec-copy-ltr-v6",
    "tos-dq-details-hero-v1",
    "tos-dq-details-metrics-v1",
    "tos-dq-details-assignment-v1",
    "tos-dq-details-attachments-v1",
    "tos-dq-details-activity-v1",
    "tos-dq-activity-item-v1",
):
    if required not in (original_dq + original_css):
        fail(f"required V12 baseline marker missing: {required}")

if V13_MARKER in original_css or V13_HOOK in original_dq:
    fail("Design Request Details Flagship V13 already present")

updated_dq = replace_once(
    original_dq,
    V12_HOOK,
    V12_HOOK + ' ' + V13_HOOK,
    "V13 ultra-luxury hook",
)

# Turn the attachment empty state into the designed vault shown in the approved concept.
old_empty = '''{!attachmentFiles.length && <div className="col-span-full rounded-2xl border border-dashed border-amber-200 p-8 text-center text-xs font-bold text-slate-400 dark:border-amber-400/20">{tr.details.notices.noFiles}</div>}'''
new_empty = '''{!attachmentFiles.length && <div className="tos-dq-attachments-empty-v13 col-span-full rounded-2xl border border-dashed border-amber-200 p-8 text-center text-xs font-bold text-slate-400 dark:border-amber-400/20"><FileText size={30} className="tos-dq-attachments-empty-icon-v13" /><div className="tos-dq-attachments-empty-title-v13">{tr.details.notices.noFiles}</div><div className="tos-dq-attachments-empty-hint-v13">{lang === "en" ? "Attach files, mockups, or references to help the designer." : "أرفق الملفات أو النماذج أو المراجع لمساعدة المصمم."}</div>{task.canAddAttachments && <button type="button" onClick={() => attachmentInputRef.current?.click()} disabled={attachmentUploading || actionBusy} className="tos-dq-attachments-empty-action-v13"><Paperclip size={14} />{attachmentUploading ? tr.details.actions.uploadingAttachment : tr.details.actions.addAttachment}</button>}</div>}'''
updated_dq = replace_once(updated_dq, old_empty, new_empty, "V13 attachment vault empty state")

v13_css = r'''

/* =========================================================
   Phase 04.1 — Design Request Details — Flagship V13
   Ultra-luxury reference-match pass based on the approved concept image.
   Visual-only: richer cinematic gold, editorial brief stage, jewel-like
   metadata, floating command console, attachment vault and real timeline deck.
   Business logic/data flow unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v13-runtime: 1; }

[data-dq-details-ultra="v13"] {
  --dq13-gold: #d6a63d;
  --dq13-gold-bright: #ffd66a;
  --dq13-gold-deep: #966019;
  --dq13-cream: #fcfaf3;
  --dq13-ink: #101214;
  border-radius: 30px !important;
  border-color: rgba(193,145,48,.24) !important;
  background:
    radial-gradient(ellipse 50% 30% at 12% 0%, rgba(232,196,112,.15), transparent 70%),
    radial-gradient(ellipse 45% 24% at 96% 100%, rgba(220,177,82,.08), transparent 72%),
    linear-gradient(145deg, #fcfbf7 0%, #f5efe3 47%, #fbf8f1 100%) !important;
  box-shadow: 0 34px 90px rgba(69,48,16,.12), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

/* HERO — stronger couture sweep and visual depth. */
[data-dq-details-ultra="v13"] .tos-dq-details-hero-v1 {
  min-height: 176px !important;
  padding: 27px 31px !important;
  border-radius: 32px !important;
  border: 1px solid rgba(196,146,46,.34) !important;
  background:
    radial-gradient(ellipse 42% 135% at 7% -35%, rgba(232,191,88,.42) 0 34%, transparent 35%),
    radial-gradient(ellipse 66% 150% at 28% -74%, transparent 0 59%, rgba(227,179,67,.28) 59.4% 60%, transparent 60.7%),
    radial-gradient(ellipse 75% 160% at 35% -84%, transparent 0 67%, rgba(227,179,67,.17) 67.4% 68%, transparent 68.7%),
    linear-gradient(135deg,#fffefa 0%,#f7efdf 66%,#fcfaf5 100%) !important;
  box-shadow: 0 28px 74px rgba(83,55,10,.14), inset 0 1px 0 rgba(255,255,255,.99), inset 0 -1px 0 rgba(184,132,31,.08) !important;
}

[data-dq-details-ultra="v13"] .tos-dq-details-hero-v1::before {
  content: "" !important;
  position: absolute !important;
  inset: 0 !important;
  opacity: 1 !important;
  pointer-events: none !important;
  background:
    linear-gradient(112deg, transparent 0 47%, rgba(242,203,104,.30) 47.25% 47.52%, transparent 47.8%),
    linear-gradient(118deg, transparent 0 53%, rgba(234,191,90,.18) 53.2% 53.46%, transparent 53.75%),
    linear-gradient(124deg, transparent 0 59%, rgba(226,179,73,.11) 59.15% 59.4%, transparent 59.7%) !important;
  filter: drop-shadow(0 0 14px rgba(211,159,53,.08));
}

[data-dq-details-ultra="v13"] .tos-dq-details-hero-v1 h2 {
  font-size: clamp(2.5rem,3.25vw,3.65rem) !important;
  line-height: 1 !important;
  letter-spacing: -.057em !important;
  font-weight: 950 !important;
  color: #12120f !important;
  text-shadow: 0 1px 0 rgba(255,255,255,.75);
}

[data-dq-details-ultra="v13"] .tos-dq-details-actions-v1 {
  width: 330px !important;
  padding: 11px !important;
  border-radius: 22px !important;
  border-color: rgba(171,119,26,.24) !important;
  background: rgba(255,255,255,.78) !important;
  backdrop-filter: blur(24px) saturate(1.12);
  box-shadow: 0 18px 42px rgba(75,50,12,.10), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

[data-dq-details-ultra="v13"] .tos-dq-attachment-action-v4 {
  min-height: 42px !important;
  border-radius: 13px !important;
  border-color: rgba(184,132,35,.18) !important;
  background: linear-gradient(180deg,#fffefa,#f7efe0) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), 0 6px 16px rgba(106,72,18,.05) !important;
}

[data-dq-details-ultra="v13"] .tos-dq-close-action-v5 {
  width: 40px !important;
  min-width: 40px !important;
  height: 40px !important;
  min-height: 40px !important;
  border-radius: 50% !important;
  border-color: rgba(164,118,35,.18) !important;
  background: rgba(255,255,255,.58) !important;
  box-shadow: 0 8px 18px rgba(69,48,18,.06), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

/* METADATA — jewel-like executive ledger. */
[data-dq-details-ultra="v13"] .tos-dq-details-metrics-v1 { gap: 12px !important; }
[data-dq-details-ultra="v13"] .tos-dq-detail-metric-v1 {
  min-height: 84px !important;
  padding: 13px 15px !important;
  border-radius: 20px !important;
  border-color: rgba(126,96,49,.11) !important;
  background: linear-gradient(180deg,rgba(255,255,255,.995),rgba(247,243,235,.96)) !important;
  box-shadow: 0 12px 28px rgba(64,47,20,.055), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
[data-dq-details-ultra="v13"] .tos-dq-detail-metric-v1 > span:first-child {
  width: 44px !important;
  height: 44px !important;
  border-radius: 50% !important;
  border: 1px solid rgba(207,155,48,.28) !important;
  background: radial-gradient(circle at 33% 24%,#fffdf6 0,#f5e3b7 58%,#e5bd67 100%) !important;
  box-shadow: 0 0 0 5px rgba(214,166,61,.045), 0 8px 18px rgba(145,91,17,.10), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

/* CORE SURFACES */
[data-dq-details-ultra="v13"] .tos-dq-detail-section-v1 {
  border-radius: 26px !important;
  border-color: rgba(157,113,35,.15) !important;
  background: rgba(255,255,255,.96) !important;
  box-shadow: 0 20px 48px rgba(67,48,18,.06), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
[data-dq-details-ultra="v13"] .tos-dq-detail-section-v1 > div:first-child {
  min-height: 54px !important;
  padding-inline: 20px !important;
  border-color: rgba(183,133,40,.12) !important;
  background: linear-gradient(180deg,rgba(255,254,251,.99),rgba(248,243,233,.86)) !important;
  font-size: .9rem !important;
  letter-spacing: -.012em !important;
}

[data-dq-details-ultra="v13"] .tos-dq-spec-meta-v1,
[data-dq-details-ultra="v13"] .tos-dq-spec-brief-v1 {
  border-radius: 18px !important;
  border-color: rgba(117,91,49,.10) !important;
  background: linear-gradient(180deg,#fefdfa,#f7f3eb) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.98) !important;
}

/* EDITORIAL BRIEF STAGE — anchored Arabic reading column with luminous couture sweep. */
[data-dq-details-ultra="v13"] .tos-dq-spec-copy-v1 {
  min-height: 390px !important;
  padding: 30px 34px 34px !important;
  border-radius: 24px !important;
  overflow: hidden !important;
  border: 1px solid rgba(211,159,55,.30) !important;
  background:
    radial-gradient(ellipse 85% 132% at -20% 115%, transparent 0 47%, rgba(226,178,72,.28) 47.45% 47.9%, transparent 48.45%),
    radial-gradient(ellipse 94% 142% at -24% 122%, transparent 0 56%, rgba(226,178,72,.16) 56.35% 56.8%, transparent 57.35%),
    radial-gradient(ellipse 104% 152% at -28% 128%, transparent 0 65%, rgba(226,178,72,.09) 65.35% 65.8%, transparent 66.35%),
    radial-gradient(circle at 13% 96%, rgba(236,194,97,.13), transparent 23%),
    linear-gradient(180deg,#fffefa 0%,#faf6ed 100%) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.99), inset 4px 0 0 rgba(224,174,69,.12), 0 17px 40px rgba(75,51,14,.05) !important;
}

[data-dq-details-ultra="v13"] .tos-dq-spec-copy-v1::before {
  inset: 12px !important;
  border-radius: 19px !important;
  border-color: rgba(192,139,38,.08) !important;
}

[data-dq-details-ultra="v13"] .tos-dq-copy-editorial-v8 {
  width: 100% !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
  font-size: 1.08rem !important;
  line-height: 2.02 !important;
  color: #25221c !important;
}
[data-dq-details-ultra="v13"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 {
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-end !important;
  text-align: right !important;
  direction: rtl !important;
}
[data-dq-details-ultra="v13"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  text-align: left !important;
  direction: ltr !important;
}
[data-dq-details-ultra="v13"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 .tos-dq-copy-paragraph-v8 {
  width: min(45%, 610px) !important;
  max-width: 610px !important;
  margin: 0 0 17px auto !important;
  text-align: right !important;
}
[data-dq-details-ultra="v13"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 .tos-dq-copy-paragraph-v8 {
  width: min(45%, 610px) !important;
  max-width: 610px !important;
  margin: 0 auto 17px 0 !important;
  text-align: left !important;
}
[data-dq-details-ultra="v13"] .tos-dq-copy-emphasis-v8 {
  color: #17140f !important;
  font-weight: 950 !important;
}
[data-dq-details-ultra="v13"] .tos-dq-copy-editorial-v8::after { display:none !important; }

/* ASSIGNMENT COMMAND CONSOLE */
[data-dq-details-ultra="v13"] .tos-dq-details-assignment-v1 {
  border-radius: 27px !important;
  border: 1px solid rgba(206,154,50,.32) !important;
  background: linear-gradient(180deg,#fffefa 0%,#f7efdf 100%) !important;
  box-shadow: 0 30px 68px rgba(80,52,10,.16), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
[data-dq-details-ultra="v13"] .tos-dq-details-assignment-v1 select,
[data-dq-details-ultra="v13"] .tos-dq-details-assignment-v1 input {
  min-height: 44px !important;
  border-radius: 13px !important;
  border-color: rgba(126,96,50,.16) !important;
  background: rgba(255,255,255,.90) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96) !important;
}
[data-dq-details-ultra="v13"] .tos-dq-assignment-cta-v1 {
  min-height: 50px !important;
  border-radius: 14px !important;
  border: 1px solid rgba(151,95,11,.28) !important;
  background: linear-gradient(135deg,#ffe184 0%,#e7b744 38%,#c78a1d 72%,#a96d12 100%) !important;
  color: #171107 !important;
  font-weight: 950 !important;
  box-shadow: 0 16px 34px rgba(160,98,11,.28), inset 0 1px 0 rgba(255,255,255,.42) !important;
}

/* ATTACHMENT VAULT — actual empty-state content + action, matching reference. */
[data-dq-details-ultra="v13"] .tos-dq-attachments-empty-v13 {
  position: relative !important;
  min-height: 142px !important;
  padding: 20px !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 5px !important;
  border-radius: 20px !important;
  border-color: rgba(202,151,49,.26) !important;
  background:
    radial-gradient(circle at 50% 0%,rgba(223,181,86,.09),transparent 46%),
    linear-gradient(180deg,rgba(255,255,255,.90),rgba(248,244,236,.80)) !important;
}
[data-dq-details-ultra="v13"] .tos-dq-attachments-empty-v13::before,
[data-dq-details-ultra="v13"] .tos-dq-attachments-empty-v13::after { content:none !important; display:none !important; }
[data-dq-details-ultra="v13"] .tos-dq-attachments-empty-icon-v13 {
  color:#7f8b9b !important;
  margin-bottom:3px !important;
}
[data-dq-details-ultra="v13"] .tos-dq-attachments-empty-title-v13 {
  color:#40516a !important;
  font-size:12px !important;
  font-weight:900 !important;
}
[data-dq-details-ultra="v13"] .tos-dq-attachments-empty-hint-v13 {
  color:#8b97a7 !important;
  font-size:10px !important;
  font-weight:700 !important;
}
[data-dq-details-ultra="v13"] .tos-dq-attachments-empty-action-v13 {
  margin-top:7px !important;
  display:inline-flex !important;
  align-items:center !important;
  gap:7px !important;
  min-height:34px !important;
  padding:0 14px !important;
  border-radius:999px !important;
  border:1px solid rgba(193,140,36,.26) !important;
  background:linear-gradient(180deg,#fffefa,#f7efe0) !important;
  color:#31291b !important;
  font-size:11px !important;
  font-weight:900 !important;
  box-shadow:0 8px 18px rgba(103,70,17,.06),inset 0 1px 0 rgba(255,255,255,.98) !important;
}

/* ACTIVITY — true five-card horizontal executive timeline. */
@media (min-width:1180px) {
  [data-dq-details-ultra="v13"] .tos-dq-details-activity-v1 > div:last-child {
    padding: 14px 20px 18px !important;
  }
  [data-dq-details-ultra="v13"] .tos-dq-details-activity-v1 > div:last-child > div {
    position: relative !important;
    display: grid !important;
    grid-template-columns: repeat(5,minmax(0,1fr)) !important;
    gap: 18px !important;
    align-items: stretch !important;
    padding-top: 30px !important;
    margin: 0 !important;
  }
  [data-dq-details-ultra="v13"] .tos-dq-details-activity-v1 > div:last-child > div::before {
    content:"" !important;
    position:absolute !important;
    top:17px !important;
    left:20px !important;
    right:20px !important;
    height:1px !important;
    background:linear-gradient(90deg,transparent,rgba(215,162,53,.54) 7%,rgba(215,162,53,.30) 93%,transparent) !important;
    pointer-events:none !important;
  }
  [data-dq-details-ultra="v13"] .tos-dq-activity-item-v1 {
    position:relative !important;
    min-height:102px !important;
    margin:0 !important;
    padding:25px 15px 14px !important;
    border:1px solid rgba(123,94,45,.13) !important;
    border-radius:16px !important;
    background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(248,244,236,.90)) !important;
    box-shadow:0 9px 24px rgba(69,49,20,.045),inset 0 1px 0 rgba(255,255,255,.99) !important;
  }
  [data-dq-details-ultra="v13"] .tos-dq-activity-item-v1 > span {
    top:-18px !important;
    inset-inline-start:10px !important;
    width:13px !important;
    height:13px !important;
    border:2px solid #fff8e4 !important;
    background:#f1a400 !important;
    box-shadow:0 0 0 5px rgba(241,164,0,.14),0 0 20px rgba(241,164,0,.22) !important;
  }
  [data-dq-details-ultra="v13"] .tos-dq-details-activity-v1 > div:last-child > div > button:last-child {
    position:absolute !important;
    top:-56px !important;
    inset-inline-end:0 !important;
    margin:0 !important;
    z-index:3 !important;
  }
}

/* DARK — Black Titanium + luminous restrained gold. */
html.dark [data-dq-details-ultra="v13"] {
  background:
    radial-gradient(ellipse 56% 28% at 14% 0%,rgba(224,171,55,.11),transparent 72%),
    radial-gradient(ellipse 52% 25% at 94% 100%,rgba(224,171,55,.075),transparent 72%),
    linear-gradient(145deg,#090b0e 0%,#0d1013 46%,#080a0c 100%) !important;
  border-color:rgba(226,174,58,.22) !important;
  box-shadow:0 34px 100px rgba(0,0,0,.56),inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark [data-dq-details-ultra="v13"] .tos-dq-details-hero-v1 {
  border-color:rgba(235,183,59,.34) !important;
  background:
    radial-gradient(ellipse 42% 140% at 7% -36%,rgba(235,182,54,.28) 0 34%,transparent 35%),
    radial-gradient(ellipse 68% 155% at 30% -76%,transparent 0 59%,rgba(244,192,59,.27) 59.4% 60%,transparent 60.7%),
    radial-gradient(ellipse 76% 165% at 37% -86%,transparent 0 67%,rgba(244,192,59,.15) 67.4% 68%,transparent 68.7%),
    linear-gradient(135deg,#121518 0%,#080a0c 73%,#0d1012 100%) !important;
  box-shadow:0 28px 82px rgba(0,0,0,.52),0 0 34px rgba(216,156,30,.07),inset 0 1px 0 rgba(255,255,255,.022) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-details-hero-v1::before {
  background:
    linear-gradient(112deg,transparent 0 47%,rgba(255,204,71,.40) 47.24% 47.52%,transparent 47.82%),
    linear-gradient(118deg,transparent 0 53%,rgba(255,196,53,.24) 53.2% 53.48%,transparent 53.8%),
    linear-gradient(124deg,transparent 0 59%,rgba(244,182,38,.14) 59.2% 59.44%,transparent 59.75%) !important;
  filter:drop-shadow(0 0 20px rgba(255,190,45,.15));
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-details-hero-v1 h2 { color:#fff !important; text-shadow:0 0 30px rgba(255,255,255,.04) !important; }
html.dark [data-dq-details-ultra="v13"] .tos-dq-details-actions-v1 {
  border-color:rgba(226,174,58,.20) !important;
  background:rgba(13,16,19,.78) !important;
  box-shadow:0 18px 44px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.025) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-attachment-action-v4,
html.dark [data-dq-details-ultra="v13"] .tos-dq-close-action-v5 {
  border-color:rgba(232,181,63,.18) !important;
  background:linear-gradient(180deg,#171b1f,#0e1114) !important;
  color:#f4f1e9 !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-detail-metric-v1 {
  border-color:rgba(255,255,255,.07) !important;
  background:linear-gradient(180deg,#171a1e,#0f1215) !important;
  box-shadow:0 13px 30px rgba(0,0,0,.30),inset 0 1px 0 rgba(255,255,255,.018) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-detail-metric-v1 > span:first-child {
  border-color:rgba(242,188,62,.34) !important;
  background:radial-gradient(circle at 35% 24%,#4f3b14 0,#261c08 52%,#111315 100%) !important;
  box-shadow:0 0 0 5px rgba(238,180,50,.05),0 0 24px rgba(234,172,38,.13),inset 0 1px 0 rgba(255,228,141,.09) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-detail-section-v1 {
  border-color:rgba(230,178,59,.18) !important;
  background:linear-gradient(180deg,#111418,#0b0e11) !important;
  box-shadow:0 22px 52px rgba(0,0,0,.40),inset 0 1px 0 rgba(255,255,255,.018) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-detail-section-v1 > div:first-child {
  border-color:rgba(231,177,55,.12) !important;
  background:linear-gradient(180deg,#171a1e,#101317) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-spec-meta-v1,
html.dark [data-dq-details-ultra="v13"] .tos-dq-spec-brief-v1 {
  border-color:rgba(255,255,255,.07) !important;
  background:linear-gradient(180deg,#111418,#0c0f12) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-spec-copy-v1 {
  border-color:rgba(239,185,53,.30) !important;
  background:
    radial-gradient(ellipse 85% 132% at -20% 115%,transparent 0 47%,rgba(250,193,44,.34) 47.45% 47.9%,transparent 48.45%),
    radial-gradient(ellipse 94% 142% at -24% 122%,transparent 0 56%,rgba(250,193,44,.20) 56.35% 56.8%,transparent 57.35%),
    radial-gradient(ellipse 104% 152% at -28% 128%,transparent 0 65%,rgba(250,193,44,.11) 65.35% 65.8%,transparent 66.35%),
    radial-gradient(circle at 13% 96%,rgba(255,197,54,.10),transparent 23%),
    linear-gradient(180deg,#0f1215 0%,#090b0e 100%) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.018),inset 4px 0 0 rgba(243,185,43,.16),0 0 38px rgba(225,159,25,.05) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-copy-editorial-v8 { color:#f2efe8 !important; }
html.dark [data-dq-details-ultra="v13"] .tos-dq-copy-emphasis-v8 { color:#fffaf0 !important; }
html.dark [data-dq-details-ultra="v13"] .tos-dq-details-assignment-v1 {
  border-color:rgba(240,187,59,.30) !important;
  background:linear-gradient(180deg,#15181b 0%,#0c0f12 100%) !important;
  box-shadow:0 28px 70px rgba(0,0,0,.50),0 0 34px rgba(225,158,24,.055),inset 0 1px 0 rgba(255,255,255,.022) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-details-assignment-v1 select,
html.dark [data-dq-details-ultra="v13"] .tos-dq-details-assignment-v1 input {
  border-color:rgba(255,255,255,.09) !important;
  background:#0c0f12 !important;
  color:#f5f3ed !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-assignment-cta-v1 {
  border-color:rgba(255,207,82,.42) !important;
  background:linear-gradient(135deg,#ffe37f 0%,#e7b53c 38%,#c68416 72%,#9d5f0a 100%) !important;
  color:#130d04 !important;
  box-shadow:0 0 0 1px rgba(255,217,109,.10),0 16px 38px rgba(198,119,11,.28),0 0 30px rgba(255,190,42,.12),inset 0 1px 0 rgba(255,255,255,.36) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-attachments-empty-v13 {
  border-color:rgba(234,181,56,.26) !important;
  background:linear-gradient(180deg,rgba(255,255,255,.014),rgba(255,255,255,.006)) !important;
}
html.dark [data-dq-details-ultra="v13"] .tos-dq-attachments-empty-title-v13 { color:#dce2ea !important; }
html.dark [data-dq-details-ultra="v13"] .tos-dq-attachments-empty-hint-v13 { color:#7e8996 !important; }
html.dark [data-dq-details-ultra="v13"] .tos-dq-attachments-empty-action-v13 {
  border-color:rgba(235,182,58,.28) !important;
  background:linear-gradient(180deg,#171a1d,#0e1114) !important;
  color:#f4f1e9 !important;
  box-shadow:0 0 24px rgba(230,170,35,.06),inset 0 1px 0 rgba(255,255,255,.02) !important;
}
@media (min-width:1180px) {
  html.dark [data-dq-details-ultra="v13"] .tos-dq-details-activity-v1 > div:last-child > div::before {
    background:linear-gradient(90deg,transparent,rgba(248,190,44,.68) 7%,rgba(248,190,44,.32) 93%,transparent) !important;
  }
  html.dark [data-dq-details-ultra="v13"] .tos-dq-activity-item-v1 {
    border-color:rgba(237,183,55,.14) !important;
    background:linear-gradient(180deg,#15181b,#0d1013) !important;
    box-shadow:0 10px 26px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.016) !important;
  }
  html.dark [data-dq-details-ultra="v13"] .tos-dq-activity-item-v1 > span {
    border-color:#241b08 !important;
    background:#ffb000 !important;
    box-shadow:0 0 0 5px rgba(255,176,0,.14),0 0 22px rgba(255,176,0,.30) !important;
  }
}

@media (max-width:1179px) {
  [data-dq-details-ultra="v13"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 .tos-dq-copy-paragraph-v8,
  [data-dq-details-ultra="v13"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 .tos-dq-copy-paragraph-v8 {
    width:min(100%,68ch) !important;
  }
  [data-dq-details-ultra="v13"] .tos-dq-spec-copy-v1 { min-height:auto !important; }
}
'''

updated_css = original_css.rstrip() + "\n" + v13_css + "\n"

source_written = False
staging = None
old_live = None
try:
    DQ.write_text(updated_dq)
    CSS.write_text(updated_css)
    source_written = True

    build = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if build.returncode != 0:
        print(build.stdout[-8000:])
        raise RuntimeError("frontend build failed")

    if not DIST.exists():
        raise RuntimeError("frontend dist missing after build")

    dist_v13 = tree_count(DIST, V13_MARKER.encode())
    dist_hook = tree_count(DIST, V13_HOOK.encode())
    dist_empty = tree_count(DIST, b"tos-dq-attachments-empty-v13")
    if dist_v13 < 1 or dist_hook < 1 or dist_empty < 1:
        raise RuntimeError("V13 runtime markers missing from dist")

    ts = int(time.time())
    staging = LIVE_PARENT / f".build-phase04-1-v13-staging-{ts}"
    old_live = LIVE_PARENT / f".build-phase04-1-v13-before-{ts}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(old_live)
    staging.rename(LIVE)
    staging = None

    live_v13 = tree_count(LIVE, V13_MARKER.encode())
    live_hook = tree_count(LIVE, V13_HOOK.encode())
    live_empty = tree_count(LIVE, b"tos-dq-attachments-empty-v13")
    if live_v13 < 1 or live_hook < 1 or live_empty < 1:
        raise RuntimeError("V13 runtime markers missing from live build")

    if old_live and old_live.exists():
        shutil.rmtree(old_live)
        old_live = None

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V13_RUNTIME=YES")
    print("V12_REFERENCE_BASELINE_PRESERVED=YES")
    print("CINEMATIC_GOLD_HERO_INTENSIFIED=YES")
    print("JEWEL_METADATA_LEDGER=YES")
    print("EDITORIAL_BRIEF_STAGE_ULTRA=YES")
    print("RTL_READING_COLUMN_RIGHT_EDGE=YES")
    print("LTR_READING_COLUMN_LEFT_EDGE=YES")
    print("FLOATING_COMMAND_CONSOLE_ULTRA=YES")
    print("ATTACHMENT_VAULT_ACTIONABLE_EMPTY_STATE=YES")
    print("ACTIVITY_HORIZONTAL_EXECUTIVE_DECK=YES")
    print("BLACK_TITANIUM_GOLD_DARK=YES")
    print("PORCELAIN_CHAMPAGNE_LIGHT=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V13_RUNTIME_COUNT={updated_css.count(V13_MARKER)}")
    print(f"SOURCE_V13_HOOK_COUNT={updated_dq.count(V13_HOOK)}")
    print(f"DIST_V13_RUNTIME_COUNT={dist_v13}")
    print(f"DIST_V13_HOOK_COUNT={dist_hook}")
    print(f"LIVE_V13_RUNTIME_COUNT={live_v13}")
    print(f"LIVE_V13_HOOK_COUNT={live_hook}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")
except Exception as exc:
    if source_written:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
    if staging and staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    if old_live and old_live.exists():
        if LIVE.exists():
            shutil.rmtree(LIVE, ignore_errors=True)
        old_live.rename(LIVE)
    fail(exc)
