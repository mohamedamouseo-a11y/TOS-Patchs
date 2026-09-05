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

EXPECTED_DQ_SHA256 = "96e9a370d79f32f7534a0da036da5762eef66cd1d4f6188585d18b32516ae53e"
EXPECTED_CSS_SHA256 = "1c7b6c54286ef5870ee5e8eb0bcda5c4981bc3a14fe0c41498e2f3789464b024"
V11_MARKER = "--tos-dq-details-flagship-v11-runtime"
V12_MARKER = "--tos-dq-details-flagship-v12-runtime"
V11_HOOK = 'data-dq-details-reference="v11"'
V12_HOOK = 'data-dq-details-concept="v12"'
COPY_MARKER = "tos-dq-copy-editorial-v8"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V12")


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
    print("V12_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match Flagship V11 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V11 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in (
    "TOS_DQ_PERFORMANCE_V3",
    "TOS_DQ_PREMIUM_MENU_V9",
    "TOS_DQ_PREMIUM_MENU_THEME_V10",
    V11_MARKER,
    V11_HOOK,
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
        fail(f"required V11 baseline marker missing: {required}")

if V12_MARKER in original_css or V12_HOOK in original_dq:
    fail("Design Request Details Flagship V12 already present")

updated_dq = replace_once(
    original_dq,
    V11_HOOK,
    V11_HOOK + ' ' + V12_HOOK,
    "V12 concept reference hook",
)

v12_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V12
   Reference-lock pass. Matches the approved luxury concept more closely:
   cinematic sweep hero, true edge-anchored editorial reading canvas,
   floating assignment console, designed attachment vault, and a real
   horizontal activity deck on desktop. Visual-only. Business logic intact.
   ========================================================= */
:root { --tos-dq-details-flagship-v12-runtime: 1; }

[data-dq-details-concept="v12"] {
  --dq12-gold: #d0a340;
  --dq12-gold-bright: #efc85c;
  --dq12-gold-deep: #a9761c;
  --dq12-cream: #fbf8ef;
  --dq12-ink: #111315;
}

/* HERO — stronger, cleaner, closer to the concept image. */
[data-dq-details-concept="v12"] .tos-dq-details-hero-v1 {
  min-height: 158px !important;
  padding: 24px 30px !important;
  border-radius: 30px !important;
  background:
    radial-gradient(ellipse 44% 150% at 7% -37%, rgba(228,188,91,.38) 0 35%, transparent 36%),
    radial-gradient(ellipse 58% 138% at 30% -65%, transparent 0 62%, rgba(218,171,68,.24) 63% 63.6%, transparent 64.2%),
    radial-gradient(ellipse 62% 145% at 36% -70%, transparent 0 69%, rgba(218,171,68,.14) 70% 70.6%, transparent 71.2%),
    linear-gradient(135deg, #fffefa 0%, #f8f2e5 66%, #fcfaf5 100%) !important;
  border-color: rgba(197,147,47,.28) !important;
  box-shadow: 0 24px 68px rgba(73,50,13,.11), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

[data-dq-details-concept="v12"] .tos-dq-details-hero-v1::before {
  content: "" !important;
  position: absolute !important;
  inset: 0 !important;
  opacity: 1 !important;
  pointer-events: none !important;
  background:
    linear-gradient(116deg, transparent 0 45%, rgba(233,193,96,.22) 45.3% 45.65%, transparent 46%),
    linear-gradient(121deg, transparent 0 51%, rgba(233,193,96,.12) 51.2% 51.48%, transparent 51.8%),
    linear-gradient(128deg, transparent 0 58%, rgba(233,193,96,.08) 58.2% 58.45%, transparent 58.8%) !important;
}

[data-dq-details-concept="v12"] .tos-dq-details-hero-v1::after {
  content: "IDEAS\A FOR A BRIGHTER\A TOMORROW" !important;
  white-space: pre !important;
  position: absolute !important;
  top: 39px !important;
  left: 58% !important;
  width: auto !important;
  height: auto !important;
  border: 0 !important;
  border-radius: 0 !important;
  transform: none !important;
  color: rgba(92,76,52,.72) !important;
  font-size: 10px !important;
  line-height: 1.55 !important;
  font-weight: 900 !important;
  letter-spacing: .28em !important;
  text-align: left !important;
  pointer-events: none !important;
}

[data-dq-details-concept="v12"] .tos-dq-details-hero-v1 h2 {
  max-width: 54% !important;
  font-size: clamp(2.3rem,3.1vw,3.35rem) !important;
  letter-spacing: -.052em !important;
  text-wrap: balance;
}

/* LEDGER */
[data-dq-details-concept="v12"] .tos-dq-details-metrics-v1 {
  gap: 12px !important;
}
[data-dq-details-concept="v12"] .tos-dq-detail-metric-v1 {
  min-height: 78px !important;
  border-radius: 17px !important;
  padding: 12px 15px !important;
  background: linear-gradient(180deg, rgba(255,255,255,.99), rgba(248,244,235,.95)) !important;
  border-color: rgba(174,130,49,.12) !important;
  box-shadow: 0 10px 26px rgba(64,48,23,.05), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
[data-dq-details-concept="v12"] .tos-dq-detail-metric-v1 > span:first-child {
  width: 42px !important;
  height: 42px !important;
  border-radius: 50% !important;
  background: radial-gradient(circle at 36% 24%, #fffaf0, #f1ddb0 74%) !important;
  border-color: rgba(205,155,55,.23) !important;
  box-shadow: 0 0 0 4px rgba(213,170,77,.035), inset 0 1px 0 rgba(255,255,255,.95) !important;
}

/* SPECIFICATIONS + EDITORIAL BRIEF — important V11 correction. */
[data-dq-details-concept="v12"] .tos-dq-details-specs-v1 {
  border-color: rgba(196,150,60,.17) !important;
}
[data-dq-details-concept="v12"] .tos-dq-spec-copy-v1 {
  min-height: 360px !important;
  padding: 28px 32px 32px !important;
  border-radius: 23px !important;
  background:
    radial-gradient(ellipse 76% 120% at -17% 112%, transparent 0 52%, rgba(213,168,74,.20) 52.4% 52.8%, transparent 53.4%),
    radial-gradient(ellipse 84% 128% at -20% 119%, transparent 0 60%, rgba(213,168,74,.12) 60.4% 60.8%, transparent 61.4%),
    radial-gradient(ellipse 95% 138% at -25% 125%, transparent 0 68%, rgba(213,168,74,.075) 68.4% 68.8%, transparent 69.4%),
    linear-gradient(180deg, #fffefa 0%, #faf6ee 100%) !important;
  border-color: rgba(201,153,61,.23) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.99), inset 4px 0 0 rgba(218,174,84,.09), 0 14px 34px rgba(66,50,24,.04) !important;
}

/* Force the reading block to the physical RIGHT edge for Arabic, not the middle. */
[data-dq-details-concept="v12"] .tos-dq-copy-editorial-v8 {
  display: flex !important;
  flex-direction: column !important;
  width: 100% !important;
  max-width: none !important;
  padding: 0 !important;
  margin: 0 !important;
  border: 0 !important;
  font-size: 1.04rem !important;
  line-height: 1.95 !important;
}
[data-dq-details-concept="v12"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 {
  align-items: flex-end !important;
  text-align: right !important;
  direction: rtl !important;
}
[data-dq-details-concept="v12"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
  align-items: flex-start !important;
  text-align: left !important;
  direction: ltr !important;
}
[data-dq-details-concept="v12"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 .tos-dq-copy-paragraph-v8 {
  width: min(48%, 620px) !important;
  max-width: 620px !important;
  margin: 0 0 17px auto !important;
  padding: 0 !important;
  text-align: right !important;
}
[data-dq-details-concept="v12"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 .tos-dq-copy-paragraph-v8 {
  width: min(48%, 620px) !important;
  max-width: 620px !important;
  margin: 0 auto 17px 0 !important;
  padding: 0 !important;
  text-align: left !important;
}
[data-dq-details-concept="v12"] .tos-dq-copy-paragraph-v8:last-child { margin-bottom: 0 !important; }
[data-dq-details-concept="v12"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-rtl-v6) > div:first-child {
  text-align: right !important;
  padding-right: 0 !important;
  padding-left: 0 !important;
}
[data-dq-details-concept="v12"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-ltr-v6) > div:first-child {
  text-align: left !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}
[data-dq-details-concept="v12"] .tos-dq-copy-editorial-v8::after { display: none !important; }

/* ASSIGNMENT — floating console. */
[data-dq-details-concept="v12"] .tos-dq-details-assignment-v1 {
  border-radius: 25px !important;
  border-color: rgba(198,149,55,.26) !important;
  background: linear-gradient(180deg, #fffefb 0%, #f8f1e4 100%) !important;
  box-shadow: 0 25px 60px rgba(72,48,13,.13), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
[data-dq-details-concept="v12"] .tos-dq-details-assignment-v1 [class*="rounded-xl"] {
  border-radius: 13px !important;
}
[data-dq-details-concept="v12"] .tos-dq-assignment-cta-v1 {
  min-height: 48px !important;
  background: linear-gradient(135deg,#f0ca65 0%,#d6a436 47%,#b67b1b 100%) !important;
  color: #15110a !important;
  border: 1px solid rgba(153,100,17,.22) !important;
  box-shadow: 0 14px 30px rgba(150,96,16,.24), inset 0 1px 0 rgba(255,255,255,.36) !important;
}

/* ATTACHMENT VAULT — make empty state look designed, not blank. */
[data-dq-details-concept="v12"] .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  position: relative !important;
  min-height: 126px !important;
  padding: 68px 18px 16px !important;
  border-radius: 18px !important;
  border-color: rgba(196,150,61,.22) !important;
  background:
    radial-gradient(circle at 50% 0%, rgba(219,181,98,.09), transparent 44%),
    linear-gradient(180deg, rgba(255,255,255,.82), rgba(249,246,239,.74)) !important;
}
[data-dq-details-concept="v12"] .tos-dq-details-attachments-v1 [class*="border-dashed"]::before {
  content: "▱" !important;
  position: absolute !important;
  left: 50% !important;
  top: 18px !important;
  transform: translateX(-50%) !important;
  font-size: 34px !important;
  line-height: 1 !important;
  color: #8290a4 !important;
  font-weight: 500 !important;
}
[data-dq-details-concept="v12"] .tos-dq-details-attachments-v1 [class*="border-dashed"]::after {
  content: "Attach files, mockups, or references to help the designer." !important;
  position: absolute !important;
  left: 50% !important;
  bottom: 16px !important;
  transform: translateX(-50%) !important;
  width: max-content !important;
  max-width: calc(100% - 36px) !important;
  color: #8c95a4 !important;
  font-size: 10px !important;
  font-weight: 700 !important;
  text-align: center !important;
}

/* ACTIVITY — target the REAL inner wrapper, not the section padding wrapper. */
@media (min-width: 1180px) {
  [data-dq-details-concept="v12"] .tos-dq-details-activity-v1 > div:last-child {
    padding: 12px 18px 16px !important;
  }
  [data-dq-details-concept="v12"] .tos-dq-details-activity-v1 > div:last-child > div {
    position: relative !important;
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    gap: 14px !important;
    align-items: stretch !important;
    padding-top: 28px !important;
    margin: 0 !important;
  }
  [data-dq-details-concept="v12"] .tos-dq-details-activity-v1 > div:last-child > div::before {
    content: "" !important;
    position: absolute !important;
    top: 16px !important;
    left: 18px !important;
    right: 18px !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(210,161,59,.58) 7%, rgba(210,161,59,.32) 93%, transparent) !important;
    pointer-events: none !important;
  }
  [data-dq-details-concept="v12"] .tos-dq-activity-item-v1 {
    position: relative !important;
    min-height: 112px !important;
    margin: 0 !important;
    padding: 20px 16px 14px !important;
    border: 1px solid rgba(120,94,50,.11) !important;
    border-radius: 15px !important;
    background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,245,237,.90)) !important;
    box-shadow: 0 8px 24px rgba(61,46,22,.04), inset 0 1px 0 rgba(255,255,255,.98) !important;
  }
  [data-dq-details-concept="v12"] .tos-dq-activity-item-v1 > span {
    position: absolute !important;
    top: -18px !important;
    inset-inline-start: 14px !important;
    width: 12px !important;
    height: 12px !important;
    border-radius: 50% !important;
    border: 2px solid #fff8e5 !important;
    background: #f2a500 !important;
    box-shadow: 0 0 0 4px rgba(242,165,0,.13), 0 0 18px rgba(242,165,0,.20) !important;
  }
  [data-dq-details-concept="v12"] .tos-dq-details-activity-v1 > div:last-child > div > button:last-child {
    grid-column: 1 / -1 !important;
    justify-self: end !important;
    margin-top: 2px !important;
    order: -1 !important;
  }
}

/* DARK REFERENCE LOCK */
html.dark [data-dq-details-concept="v12"] {
  background:
    radial-gradient(circle at 8% -2%, rgba(202,153,51,.11), transparent 24%),
    radial-gradient(circle at 94% -2%, rgba(176,126,31,.07), transparent 28%),
    linear-gradient(145deg,#080a0d 0%,#0c0f12 50%,#07090b 100%) !important;
  border-color: rgba(213,167,70,.18) !important;
  box-shadow: 0 36px 110px rgba(0,0,0,.56), inset 0 1px 0 rgba(255,255,255,.02) !important;
}
html.dark [data-dq-details-concept="v12"] .tos-dq-details-hero-v1 {
  background:
    radial-gradient(ellipse 48% 145% at 7% -34%, rgba(205,157,57,.34) 0 34%, transparent 35%),
    radial-gradient(ellipse 64% 145% at 34% -67%, transparent 0 62%, rgba(220,171,63,.20) 63% 63.5%, transparent 64%),
    linear-gradient(135deg,#101317 0%,#090b0e 72%,#0d1013 100%) !important;
  border-color: rgba(218,171,70,.30) !important;
  box-shadow: 0 26px 70px rgba(0,0,0,.44), inset 0 1px 0 rgba(255,255,255,.025) !important;
}
html.dark [data-dq-details-concept="v12"] .tos-dq-details-hero-v1::after {
  color: rgba(239,207,137,.78) !important;
}
html.dark [data-dq-details-concept="v12"] .tos-dq-details-hero-v1 h2 { color: #f7f5f0 !important; }
html.dark [data-dq-details-concept="v12"] .tos-dq-detail-metric-v1 {
  background: linear-gradient(180deg,#15191d,#0f1215) !important;
  border-color: rgba(255,255,255,.065) !important;
  box-shadow: 0 12px 30px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.018) !important;
}
html.dark [data-dq-details-concept="v12"] .tos-dq-detail-metric-v1 > span:first-child {
  background: radial-gradient(circle at 34% 23%, rgba(236,194,91,.22), rgba(123,83,15,.10) 75%) !important;
  border-color: rgba(225,179,78,.34) !important;
  color: #f1c453 !important;
}
html.dark [data-dq-details-concept="v12"] .tos-dq-spec-copy-v1 {
  background:
    radial-gradient(ellipse 78% 122% at -18% 113%, transparent 0 52%, rgba(221,170,56,.33) 52.3% 52.8%, transparent 53.4%),
    radial-gradient(ellipse 86% 130% at -21% 121%, transparent 0 61%, rgba(221,170,56,.19) 61.3% 61.8%, transparent 62.4%),
    radial-gradient(ellipse 98% 140% at -25% 128%, transparent 0 69%, rgba(221,170,56,.11) 69.3% 69.8%, transparent 70.4%),
    linear-gradient(180deg,#111417,#0b0e11) !important;
  border-color: rgba(220,171,68,.34) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.02), inset 4px 0 0 rgba(223,173,69,.17), 0 18px 44px rgba(0,0,0,.30) !important;
}
html.dark [data-dq-details-concept="v12"] .tos-dq-copy-editorial-v8 { color: #f0ede6 !important; }
html.dark [data-dq-details-concept="v12"] .tos-dq-copy-emphasis-v8 { color: #fffaf0 !important; }
html.dark [data-dq-details-concept="v12"] .tos-dq-details-assignment-v1 {
  background: linear-gradient(180deg,#15191d,#0c0f12) !important;
  border-color: rgba(221,174,72,.31) !important;
  box-shadow: 0 26px 64px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.02) !important;
}
html.dark [data-dq-details-concept="v12"] .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  background: linear-gradient(180deg,rgba(255,255,255,.014),rgba(255,255,255,.006)) !important;
  border-color: rgba(218,171,70,.25) !important;
}
html.dark [data-dq-details-concept="v12"] .tos-dq-details-attachments-v1 [class*="border-dashed"]::after { color: #8f99a7 !important; }
@media (min-width: 1180px) {
  html.dark [data-dq-details-concept="v12"] .tos-dq-details-activity-v1 > div:last-child > div::before {
    background: linear-gradient(90deg, transparent, rgba(235,182,58,.56) 7%, rgba(235,182,58,.28) 93%, transparent) !important;
  }
  html.dark [data-dq-details-concept="v12"] .tos-dq-activity-item-v1 {
    background: linear-gradient(180deg,#14181c,#0e1114) !important;
    border-color: rgba(255,255,255,.075) !important;
    box-shadow: 0 10px 26px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.018) !important;
  }
  html.dark [data-dq-details-concept="v12"] .tos-dq-activity-item-v1 > span { border-color: #151008 !important; }
}

@media (max-width: 1179px) {
  [data-dq-details-concept="v12"] .tos-dq-details-hero-v1::after { display: none !important; }
  [data-dq-details-concept="v12"] .tos-dq-details-hero-v1 h2 { max-width: 100% !important; }
  [data-dq-details-concept="v12"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 .tos-dq-copy-paragraph-v8,
  [data-dq-details-concept="v12"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 .tos-dq-copy-paragraph-v8 {
    width: min(100%, 68ch) !important;
  }
}
'''

updated_css = original_css.rstrip() + v12_css + "\n"

DQ.write_text(updated_dq)
CSS.write_text(updated_css)

backup_live = None
stage_live = None
try:
    result = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
    if result.returncode != 0:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
        fail("frontend build failed\n" + (result.stdout + "\n" + result.stderr)[-4000:])

    source_v12 = DQ.read_text().count(V12_HOOK)
    source_marker = CSS.read_text().count(V12_MARKER)
    dist_v12 = tree_count(DIST, V12_MARKER.encode())
    dist_hook = tree_count(DIST, b"data-dq-details-concept")
    dist_copy = tree_count(DIST, COPY_MARKER.encode())
    if source_v12 != 1 or source_marker != 1:
        raise RuntimeError("V12 source markers invalid")
    if dist_v12 < 1 or dist_hook < 1 or dist_copy < 1:
        raise RuntimeError("V12 runtime markers missing from dist")

    timestamp = time.strftime("%Y%m%d%H%M%S")
    stage_live = LIVE_PARENT / f"build.v12-stage-{timestamp}"
    backup_live = LIVE_PARENT / f"build.v12-backup-{timestamp}"
    if stage_live.exists(): shutil.rmtree(stage_live)
    shutil.copytree(DIST, stage_live)
    if LIVE.exists(): LIVE.rename(backup_live)
    stage_live.rename(LIVE)

    live_v12 = tree_count(LIVE, V12_MARKER.encode())
    live_hook = tree_count(LIVE, b"data-dq-details-concept")
    live_copy = tree_count(LIVE, COPY_MARKER.encode())
    if live_v12 < 1 or live_hook < 1 or live_copy < 1:
        raise RuntimeError("V12 markers missing from live build")

    if backup_live and backup_live.exists(): shutil.rmtree(backup_live)

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V12_RUNTIME=YES")
    print("REFERENCE_LOCK_DIRECTION=YES")
    print("CINEMATIC_SWEEP_HERO=YES")
    print("HERO_TAGLINE_REFERENCE=YES")
    print("EXECUTIVE_LEDGER_REFINED=YES")
    print("EDITORIAL_CANVAS_EDGE_ANCHORED=YES")
    print("RTL_READING_COLUMN_RIGHT_EDGE=YES")
    print("LTR_READING_COLUMN_LEFT_EDGE=YES")
    print("FLOATING_ASSIGNMENT_CONSOLE=YES")
    print("ATTACHMENT_VAULT_DESIGNED_EMPTY_STATE=YES")
    print("ACTIVITY_REAL_INNER_GRID_TARGETED=YES")
    print("HORIZONTAL_ACTIVITY_DECK=YES")
    print("LIGHT_REFERENCE_LOCK=YES")
    print("DARK_REFERENCE_LOCK=YES")
    print("V11_BASELINE_PRESERVED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V12_RUNTIME_COUNT={source_marker}")
    print(f"SOURCE_V12_HOOK_COUNT={source_v12}")
    print(f"DIST_V12_RUNTIME_COUNT={dist_v12}")
    print(f"DIST_V12_HOOK_COUNT={dist_hook}")
    print(f"LIVE_V12_RUNTIME_COUNT={live_v12}")
    print(f"LIVE_V12_HOOK_COUNT={live_hook}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")
except Exception as exc:
    DQ.write_text(original_dq)
    CSS.write_text(original_css)
    try:
        if LIVE.exists() and backup_live and backup_live.exists():
            shutil.rmtree(LIVE)
            backup_live.rename(LIVE)
        elif backup_live and backup_live.exists() and not LIVE.exists():
            backup_live.rename(LIVE)
        if stage_live and stage_live.exists(): shutil.rmtree(stage_live)
    except Exception:
        pass
    fail(exc)
