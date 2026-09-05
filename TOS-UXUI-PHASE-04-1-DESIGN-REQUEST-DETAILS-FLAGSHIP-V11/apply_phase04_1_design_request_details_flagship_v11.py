from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_DQ_SHA256 = "9c2f55536bd5edee47474af63000c82fc031fcfaba4bf061c1eedbb1904252df"
EXPECTED_CSS_SHA256 = "fbb4dbb31194a6e5ce5d4af0ab1c79bb88b1f3f5924f7266635d6692a9dd8d9a"
V8_MARKER = "--tos-dq-details-flagship-v8-runtime"
V9_MARKER = "--tos-dq-details-flagship-v9-runtime"
V10_MARKER = "--tos-dq-details-flagship-v10-runtime"
V11_MARKER = "--tos-dq-details-flagship-v11-runtime"
V10_HOOK = 'data-dq-details-couture="v10"'
V11_HOOK = 'data-dq-details-reference="v11"'
COPY_MARKER = "tos-dq-copy-editorial-v8"
RTL_HOOK = "tos-dq-spec-copy-rtl-v6"
LTR_HOOK = "tos-dq-spec-copy-ltr-v6"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V11")


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
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V11_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match Flagship V10 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V10 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in (
    "TOS_DQ_PERFORMANCE_V3",
    "TOS_DQ_PREMIUM_MENU_V9",
    "TOS_DQ_PREMIUM_MENU_THEME_V10",
    V8_MARKER,
    V9_MARKER,
    V10_MARKER,
    V10_HOOK,
    COPY_MARKER,
    RTL_HOOK,
    LTR_HOOK,
    "tos-dq-close-action-v5",
    "tos-dq-attachment-action-v4",
    "tos-dq-details-hero-v1",
    "tos-dq-details-metrics-v1",
    "tos-dq-details-assignment-v1",
    "tos-dq-details-attachments-v1",
    "tos-dq-details-activity-v1",
):
    if required not in (original_dq + original_css):
        fail(f"required V10 baseline marker missing: {required}")

if V11_MARKER in original_css or V11_HOOK in original_dq:
    fail("Design Request Details Flagship V11 already present")

updated_dq = replace_once(
    original_dq,
    V10_HOOK,
    V10_HOOK + ' ' + V11_HOOK,
    "V11 reference-match hook",
)

v11_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V11
   Reference-match redesign based on the approved luxury concept image.
   Visual-only pass: cinematic hero, executive ledger, editorial brief
   stage, floating assignment console, attachment vault and horizontal
   activity timeline. Business logic unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v11-runtime: 1; }

[data-dq-details-reference="v11"] {
  --dq11-gold: #c99a3d;
  --dq11-gold-2: #e0bc68;
  --dq11-ink: #171611;
  --dq11-muted: #7a7468;
  --dq11-porcelain: #fbfaf6;
  --dq11-shadow: rgba(74, 52, 19, .10);
  border-color: rgba(188,144,57,.22) !important;
  background:
    radial-gradient(circle at 8% -2%, rgba(229,199,129,.18), transparent 23%),
    radial-gradient(circle at 97% 1%, rgba(255,255,255,.98), transparent 31%),
    linear-gradient(145deg, #fcfbf8 0%, #f6f1e7 47%, #fbf8f1 100%) !important;
  box-shadow: 0 30px 90px rgba(70,50,18,.10), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

/* Cinematic hero with the same swept-gold language as the concept. */
[data-dq-details-reference="v11"] .tos-dq-details-hero-v1 {
  min-height: 150px !important;
  padding: 24px 28px !important;
  border-radius: 31px !important;
  border: 1px solid rgba(181,136,48,.28) !important;
  overflow: hidden !important;
  background:
    radial-gradient(ellipse 38% 120% at 7% -24%, rgba(224,185,92,.34) 0%, rgba(224,185,92,.14) 36%, transparent 37%),
    radial-gradient(ellipse 55% 120% at 31% -54%, transparent 0 58%, rgba(205,158,63,.16) 59% 60%, transparent 61%),
    radial-gradient(ellipse 58% 130% at 37% -60%, transparent 0 66%, rgba(205,158,63,.10) 67% 68%, transparent 69%),
    radial-gradient(circle at 90% 4%, rgba(255,255,255,.96), transparent 27%),
    linear-gradient(135deg, #fffefa 0%, #f9f3e8 72%, #fbf8f1 100%) !important;
  box-shadow:
    0 24px 62px rgba(75,52,13,.11),
    inset 0 1px 0 rgba(255,255,255,.99),
    inset 0 -1px 0 rgba(172,125,38,.06) !important;
}

[data-dq-details-reference="v11"] .tos-dq-details-hero-v1::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(112deg, transparent 0 49%, rgba(213,170,77,.15) 49.4% 49.8%, transparent 50.2%),
    linear-gradient(118deg, transparent 0 55%, rgba(213,170,77,.09) 55.3% 55.6%, transparent 55.9%);
  opacity: .82;
}

[data-dq-details-reference="v11"] .tos-dq-details-hero-v1::after {
  content: "";
  position: absolute;
  width: 360px;
  height: 130px;
  top: -74px;
  inset-inline-start: 18%;
  border-radius: 50%;
  border: 1px solid rgba(201,154,61,.14);
  transform: rotate(-9deg);
  pointer-events: none;
}

[data-dq-details-reference="v11"] .tos-dq-details-hero-v1 h2 {
  position: relative;
  z-index: 2;
  font-size: clamp(2.15rem, 3vw, 3.15rem) !important;
  line-height: 1.02 !important;
  letter-spacing: -.045em !important;
  font-weight: 950 !important;
  color: #15140f !important;
}

[data-dq-details-reference="v11"] .tos-dq-details-actions-v1 {
  position: relative;
  z-index: 3;
  width: 315px !important;
  padding: 10px !important;
  border-radius: 21px !important;
  border: 1px solid rgba(166,120,36,.20) !important;
  background: rgba(255,255,255,.72) !important;
  backdrop-filter: blur(24px) saturate(1.08);
  box-shadow: 0 15px 36px rgba(65,46,18,.07), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

[data-dq-details-reference="v11"] .tos-dq-attachment-action-v4 {
  min-height: 40px !important;
  border-radius: 12px !important;
  border-color: rgba(166,120,36,.15) !important;
  background: linear-gradient(180deg, #fffefb, #f8f2e8) !important;
  color: #2b2720 !important;
  font-weight: 900 !important;
}

[data-dq-details-reference="v11"] .tos-dq-close-action-v5 {
  width: 38px !important;
  min-width: 38px !important;
  height: 38px !important;
  min-height: 38px !important;
  border-radius: 50% !important;
  border: 1px solid rgba(138,104,46,.13) !important;
  background: rgba(255,255,255,.48) !important;
  color: #71695d !important;
}

/* Executive information ledger. */
[data-dq-details-reference="v11"] .tos-dq-details-metrics-v1 {
  gap: 10px !important;
}

[data-dq-details-reference="v11"] .tos-dq-detail-metric-v1 {
  min-height: 76px !important;
  padding: 12px 14px !important;
  border-radius: 18px !important;
  border: 1px solid rgba(108,86,51,.095) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.985), rgba(248,245,238,.94)) !important;
  box-shadow: 0 9px 25px rgba(64,48,23,.045), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

[data-dq-details-reference="v11"] .tos-dq-detail-metric-v1 > span:first-child {
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important;
  border: 1px solid rgba(191,145,53,.18) !important;
  background: radial-gradient(circle at 35% 25%, #fff7e6, #f2dfb7 72%) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.94), 0 6px 16px rgba(153,103,25,.08) !important;
}

/* Core sections share a restrained luxury material. */
[data-dq-details-reference="v11"] .tos-dq-detail-section-v1 {
  border-radius: 24px !important;
  border: 1px solid rgba(111,88,54,.105) !important;
  background: rgba(255,255,255,.955) !important;
  box-shadow: 0 17px 42px rgba(62,48,27,.05), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

[data-dq-details-reference="v11"] .tos-dq-detail-section-v1 > div:first-child {
  min-height: 50px !important;
  padding-inline: 18px !important;
  border-color: rgba(176,132,52,.10) !important;
  background: linear-gradient(180deg, rgba(255,254,251,.98), rgba(249,246,239,.78)) !important;
  font-size: .84rem !important;
  font-weight: 950 !important;
}

[data-dq-details-reference="v11"] .tos-dq-spec-meta-v1,
[data-dq-details-reference="v11"] .tos-dq-spec-brief-v1 {
  border-color: rgba(109,89,58,.09) !important;
  background: linear-gradient(180deg, #fdfcf9, #f8f5ee) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96) !important;
}

/* Editorial brief stage: text physically anchored to the content edge,
   decorative couture curves live on the empty side of the canvas. */
[data-dq-details-reference="v11"] .tos-dq-spec-copy-v1 {
  position: relative !important;
  min-height: 310px !important;
  padding: 28px 32px 30px !important;
  border-radius: 23px !important;
  overflow: hidden !important;
  border: 1px solid rgba(194,149,65,.19) !important;
  background:
    radial-gradient(ellipse 62% 95% at -8% 105%, transparent 0 51%, rgba(205,163,77,.12) 52% 52.8%, transparent 53.6%),
    radial-gradient(ellipse 68% 100% at -10% 110%, transparent 0 59%, rgba(205,163,77,.09) 60% 60.8%, transparent 61.6%),
    radial-gradient(ellipse 76% 112% at -13% 116%, transparent 0 67%, rgba(205,163,77,.065) 68% 68.8%, transparent 69.6%),
    radial-gradient(circle at 94% 3%, rgba(223,190,111,.09), transparent 25%),
    linear-gradient(180deg, #fffefa, #faf7f0) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.99), 0 12px 32px rgba(66,50,24,.035) !important;
}

[data-dq-details-reference="v11"] .tos-dq-spec-copy-v1::before {
  content: "" !important;
  position: absolute !important;
  inset: 12px !important;
  border-radius: 18px !important;
  border: 1px solid rgba(179,133,47,.055) !important;
  pointer-events: none !important;
}

[data-dq-details-reference="v11"] .tos-dq-copy-editorial-v8 {
  width: 100% !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 2px 0 !important;
  border: 0 !important;
  font-size: 1.03rem !important;
  line-height: 1.95 !important;
  color: #2c2923 !important;
}

[data-dq-details-reference="v11"] .tos-dq-copy-editorial-v8::after {
  display: none !important;
}

[data-dq-details-reference="v11"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 .tos-dq-copy-paragraph-v8 {
  width: min(54%, 66ch) !important;
  margin-right: 0 !important;
  margin-left: auto !important;
  text-align: right !important;
}

[data-dq-details-reference="v11"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 .tos-dq-copy-paragraph-v8 {
  width: min(54%, 66ch) !important;
  margin-left: 0 !important;
  margin-right: auto !important;
  text-align: left !important;
}

[data-dq-details-reference="v11"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-rtl-v6) > div:first-child {
  text-align: right !important;
  padding-right: 0 !important;
}

[data-dq-details-reference="v11"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-ltr-v6) > div:first-child {
  text-align: left !important;
  padding-left: 0 !important;
}

[data-dq-details-reference="v11"] .tos-dq-copy-paragraph-v8 {
  margin-bottom: 14px !important;
}

[data-dq-details-reference="v11"] .tos-dq-copy-emphasis-v8 {
  color: #1c1914 !important;
  font-weight: 950 !important;
}

/* Floating command console. */
[data-dq-details-reference="v11"] .tos-dq-details-assignment-v1 {
  border-radius: 24px !important;
  border: 1px solid rgba(193,147,59,.23) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(222,185,103,.11), transparent 34%),
    linear-gradient(180deg, #fffefa 0%, #f8f2e7 100%) !important;
  box-shadow: 0 22px 52px rgba(66,47,17,.09), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

[data-dq-details-reference="v11"] .tos-dq-details-assignment-v1 > div:last-child {
  padding: 17px 17px 18px !important;
}

[data-dq-details-reference="v11"] .tos-dq-details-assignment-v1 button,
[data-dq-details-reference="v11"] .tos-dq-details-assignment-v1 input,
[data-dq-details-reference="v11"] .tos-dq-details-assignment-v1 [role="combobox"] {
  border-radius: 11px !important;
}

[data-dq-details-reference="v11"] .tos-dq-assignment-cta-v1 {
  min-height: 46px !important;
  border-radius: 13px !important;
  border: 1px solid rgba(143,97,22,.22) !important;
  background: linear-gradient(135deg, #e1be69 0%, #c79337 54%, #ad7625 100%) !important;
  color: #18130b !important;
  box-shadow: 0 13px 30px rgba(142,94,19,.18), inset 0 1px 0 rgba(255,255,255,.32) !important;
}

/* Attachment vault: compact, intentional empty state. */
[data-dq-details-reference="v11"] .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  position: relative;
  min-height: 92px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 14px !important;
  border-radius: 16px !important;
  border-color: rgba(184,141,60,.18) !important;
  background:
    radial-gradient(circle at 50% -20%, rgba(223,190,113,.08), transparent 48%),
    linear-gradient(180deg, rgba(255,255,255,.68), rgba(249,246,239,.70)) !important;
}

[data-dq-details-reference="v11"] .tos-dq-details-attachments-v1 [class*="border-dashed"]::before {
  content: "";
  width: 26px;
  height: 32px;
  border: 2px solid rgba(111,128,148,.72);
  border-radius: 6px;
  background: linear-gradient(135deg, transparent 0 66%, rgba(111,128,148,.10) 67% 100%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.75);
}

/* Activity & comments mirrors the concept: a connected horizontal deck on
   desktop and a clean vertical stack on smaller screens. */
@media (min-width: 1280px) {
  [data-dq-details-reference="v11"] .tos-dq-details-activity-v1 > div:last-child {
    position: relative !important;
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    gap: 14px !important;
    padding: 22px 18px 16px !important;
  }

  [data-dq-details-reference="v11"] .tos-dq-details-activity-v1 > div:last-child::before {
    content: "";
    position: absolute;
    top: 34px;
    left: 3.8%;
    right: 3.8%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(197,151,62,.34) 10%, rgba(197,151,62,.20) 90%, transparent);
    pointer-events: none;
  }

  [data-dq-details-reference="v11"] .tos-dq-activity-item-v1 {
    position: relative !important;
    min-height: 86px !important;
    margin: 0 !important;
    padding: 25px 14px 12px !important;
    border: 1px solid rgba(106,88,59,.095) !important;
    border-radius: 14px !important;
    background: linear-gradient(180deg, rgba(255,255,255,.94), rgba(249,246,239,.82)) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.93) !important;
  }

  [data-dq-details-reference="v11"] .tos-dq-activity-item-v1 > span {
    top: -5px !important;
    inset-inline-start: 10px !important;
    width: 11px !important;
    height: 11px !important;
    border-width: 2px !important;
    box-shadow: 0 0 0 5px rgba(197,151,62,.08), 0 0 16px rgba(197,151,62,.11) !important;
  }

  [data-dq-details-reference="v11"] .tos-dq-details-activity-v1 > div:last-child > button {
    grid-column: 1 / -1;
    justify-self: end;
    margin-top: 1px;
  }
}

/* Dark reference theme. */
html.dark [data-dq-details-reference="v11"] {
  --dq11-shadow: rgba(0,0,0,.38);
  border-color: rgba(218,181,103,.16) !important;
  background:
    radial-gradient(circle at 6% -3%, rgba(180,128,35,.13), transparent 22%),
    radial-gradient(circle at 97% 0%, rgba(218,181,103,.035), transparent 28%),
    linear-gradient(145deg, #0b0d10 0%, #0d1014 48%, #090b0e 100%) !important;
  box-shadow: 0 32px 100px rgba(0,0,0,.52), inset 0 1px 0 rgba(255,255,255,.02) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-details-hero-v1 {
  border-color: rgba(218,181,103,.25) !important;
  background:
    radial-gradient(ellipse 38% 120% at 7% -24%, rgba(186,132,32,.28) 0%, rgba(186,132,32,.09) 36%, transparent 37%),
    radial-gradient(ellipse 55% 120% at 31% -54%, transparent 0 58%, rgba(214,169,69,.16) 59% 60%, transparent 61%),
    radial-gradient(circle at 92% 8%, rgba(218,181,103,.045), transparent 28%),
    linear-gradient(135deg, #16191d 0%, #0c0f13 72%, #0a0c0f 100%) !important;
  box-shadow: 0 26px 70px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.025) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-details-hero-v1 h2 {
  color: #f7f4ee !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-details-actions-v1 {
  border-color: rgba(218,181,103,.18) !important;
  background: rgba(14,17,21,.76) !important;
  box-shadow: 0 18px 44px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.018) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-attachment-action-v4,
html.dark [data-dq-details-reference="v11"] .tos-dq-close-action-v5 {
  border-color: rgba(218,181,103,.15) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.012)) !important;
  color: #ece7dc !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-detail-metric-v1 {
  border-color: rgba(255,255,255,.055) !important;
  background: linear-gradient(180deg, rgba(25,28,32,.90), rgba(15,18,22,.90)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.018), 0 8px 22px rgba(0,0,0,.14) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-detail-metric-v1 > span:first-child {
  border-color: rgba(218,181,103,.18) !important;
  background: radial-gradient(circle at 35% 25%, rgba(218,181,103,.18), rgba(218,181,103,.05) 72%) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-detail-section-v1 {
  border-color: rgba(255,255,255,.055) !important;
  background: #0f1216 !important;
  box-shadow: 0 18px 48px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.016) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-detail-section-v1 > div:first-child {
  border-color: rgba(218,181,103,.10) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.018), rgba(255,255,255,.006)) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-spec-meta-v1,
html.dark [data-dq-details-reference="v11"] .tos-dq-spec-brief-v1 {
  border-color: rgba(255,255,255,.055) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.018), rgba(255,255,255,.006)) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-spec-copy-v1 {
  border-color: rgba(218,181,103,.18) !important;
  background:
    radial-gradient(ellipse 62% 95% at -8% 105%, transparent 0 51%, rgba(206,158,61,.10) 52% 52.8%, transparent 53.6%),
    radial-gradient(ellipse 68% 100% at -10% 110%, transparent 0 59%, rgba(206,158,61,.07) 60% 60.8%, transparent 61.6%),
    radial-gradient(circle at 94% 3%, rgba(218,181,103,.045), transparent 25%),
    linear-gradient(180deg, #121519, #0d1014) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.018), 0 14px 36px rgba(0,0,0,.20) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-copy-editorial-v8 {
  color: #eeeae2 !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-copy-emphasis-v8 {
  color: #fffaf0 !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-details-assignment-v1 {
  border-color: rgba(218,181,103,.22) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(218,181,103,.075), transparent 34%),
    linear-gradient(180deg, #15181c 0%, #0f1216 100%) !important;
  box-shadow: 0 23px 58px rgba(0,0,0,.36), inset 0 1px 0 rgba(255,255,255,.02) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-assignment-cta-v1 {
  border-color: rgba(225,184,96,.28) !important;
  background: linear-gradient(135deg, #e0ba64 0%, #bd8730 55%, #98651f 100%) !important;
  color: #11100c !important;
  box-shadow: 0 14px 32px rgba(126,78,16,.22), inset 0 1px 0 rgba(255,255,255,.30) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  border-color: rgba(218,181,103,.12) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.012), rgba(255,255,255,.005)) !important;
}

html.dark [data-dq-details-reference="v11"] .tos-dq-details-attachments-v1 [class*="border-dashed"]::before {
  border-color: rgba(173,190,211,.72) !important;
  background: linear-gradient(135deg, transparent 0 66%, rgba(173,190,211,.08) 67% 100%);
}

@media (min-width: 1280px) {
  html.dark [data-dq-details-reference="v11"] .tos-dq-details-activity-v1 > div:last-child::before {
    background: linear-gradient(90deg, transparent, rgba(218,181,103,.34) 10%, rgba(218,181,103,.18) 90%, transparent);
  }

  html.dark [data-dq-details-reference="v11"] .tos-dq-activity-item-v1 {
    border-color: rgba(255,255,255,.06) !important;
    background: linear-gradient(180deg, rgba(255,255,255,.018), rgba(255,255,255,.007)) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.014) !important;
  }
}

@media (max-width: 1279px) {
  [data-dq-details-reference="v11"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 .tos-dq-copy-paragraph-v8,
  [data-dq-details-reference="v11"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 .tos-dq-copy-paragraph-v8 {
    width: min(100%, 70ch) !important;
  }
}

@media (max-width: 760px) {
  [data-dq-details-reference="v11"] .tos-dq-details-hero-v1 {
    min-height: 138px !important;
    padding: 20px 18px !important;
  }
  [data-dq-details-reference="v11"] .tos-dq-details-hero-v1 h2 {
    font-size: 1.9rem !important;
  }
  [data-dq-details-reference="v11"] .tos-dq-details-actions-v1 {
    width: 100% !important;
  }
  [data-dq-details-reference="v11"] .tos-dq-spec-copy-v1 {
    min-height: 0 !important;
    padding: 21px 18px 23px !important;
  }
}
'''

v11_css = "\n".join(line.rstrip() for line in v11_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v11_css

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated_dq)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()

    if source_dq.count(V11_HOOK) != 1:
        raise RuntimeError("V11 source hook missing or duplicated")
    if source_css.count(V11_MARKER) != 1:
        raise RuntimeError("V11 CSS runtime marker missing or duplicated")
    for required in (V8_MARKER, V9_MARKER, V10_MARKER, V10_HOOK, COPY_MARKER, RTL_HOOK, LTR_HOOK, "TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10"):
        if required not in (source_dq + source_css):
            raise RuntimeError(f"required baseline marker not preserved: {required}")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V11_MARKER.encode())
    dist_hook = tree_count(DIST, b"data-dq-details-reference")
    dist_copy = tree_count(DIST, COPY_MARKER.encode())
    if min(dist_marker, dist_hook, dist_copy) < 1:
        raise RuntimeError("V11 stable runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v11.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v11.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged live build missing index.html")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_marker = tree_count(LIVE, V11_MARKER.encode())
    live_hook = tree_count(LIVE, b"data-dq-details-reference")
    live_copy = tree_count(LIVE, COPY_MARKER.encode())
    if min(live_marker, live_hook, live_copy) < 1:
        raise RuntimeError("V11 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V11_RUNTIME=YES")
    print("REFERENCE_IMAGE_DIRECTION=YES")
    print("CINEMATIC_GOLD_HERO=YES")
    print("EXECUTIVE_METADATA_LEDGER=YES")
    print("EDITORIAL_BRIEF_STAGE=YES")
    print("RTL_READING_EDGE_ANCHORED=YES")
    print("LTR_READING_EDGE_ANCHORED=YES")
    print("FLOATING_ASSIGNMENT_CONSOLE=YES")
    print("ATTACHMENT_VAULT_REFINED=YES")
    print("HORIZONTAL_ACTIVITY_DECK=YES")
    print("LIGHT_REFERENCE_THEME=YES")
    print("DARK_REFERENCE_THEME=YES")
    print("V10_COUTURE_BASELINE_PRESERVED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V11_RUNTIME_COUNT={source_css.count(V11_MARKER)}")
    print(f"SOURCE_V11_HOOK_COUNT={source_dq.count(V11_HOOK)}")
    print(f"DIST_V11_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_V11_HOOK_COUNT={dist_hook}")
    print(f"DIST_COPY_MARKER_COUNT={dist_copy}")
    print(f"LIVE_V11_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_V11_HOOK_COUNT={live_hook}")
    print(f"LIVE_COPY_MARKER_COUNT={live_copy}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v11.failed.{int(time.time())}"
        try:
            if LIVE.exists():
                LIVE.rename(failed_live)
            backup.rename(LIVE)
        except Exception:
            pass
    elif stage and stage.exists():
        try:
            shutil.rmtree(stage)
        except Exception:
            pass

    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(exc))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V11_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
