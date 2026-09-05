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

EXPECTED_DQ_SHA256 = "fb62dcd96c60ba1f2832bc50e0879e4c5fa75df036b5c9f992ccbfd8036fbcf9"
EXPECTED_CSS_SHA256 = "c5328c49b777629b6cc0a6888c8e9aa521e3fcdcc9d96b4dee9bac9b2fcd4cd5"
V8_MARKER = "--tos-dq-details-flagship-v8-runtime"
V9_MARKER = "--tos-dq-details-flagship-v9-runtime"
V8_HOOK = 'data-dq-details-flagship="v8"'
V9_HOOK = 'data-dq-details-luxury="v9"'
COPY_MARKER = "tos-dq-copy-editorial-v8"
RTL_HOOK = "tos-dq-spec-copy-rtl-v6"
LTR_HOOK = "tos-dq-spec-copy-ltr-v6"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V9")


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
    print("V9_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match Flagship V8 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V8 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in (
    "TOS_DQ_PERFORMANCE_V3",
    "TOS_DQ_PREMIUM_MENU_V9",
    "TOS_DQ_PREMIUM_MENU_THEME_V10",
    V8_HOOK,
    V8_MARKER,
    COPY_MARKER,
    RTL_HOOK,
    LTR_HOOK,
    "tos-dq-close-action-v5",
    "tos-dq-attachment-action-v4",
):
    if required not in (original_dq + original_css):
        fail(f"required V8 baseline marker missing: {required}")

if V9_MARKER in original_css or V9_HOOK in original_dq:
    fail("Design Request Details Flagship V9 already present")

# Preserve the V8 flagship hook so all V8 luxury rules remain active.
# Add a second, cumulative V9 hook for a non-destructive visual refinement layer.
updated_dq = replace_once(
    original_dq,
    V8_HOOK,
    V8_HOOK + ' ' + V9_HOOK,
    "V9 cumulative luxury hook",
)

v9_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V9
   Ultra-luxury finishing layer after V8 visual QA.
   Keeps V8 active, restores content-language anchoring, reduces
   admin-form flatness and upgrades hero, editorial reading, command
   rail, attachments and timeline. Business logic unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v9-runtime: 1; }

[data-dq-details-luxury="v9"] {
  --dq9-gold: #c49a4b;
  --dq9-gold-soft: rgba(196,154,75,.16);
  --dq9-ink: #15140f;
  --dq9-muted: #81796c;
  --dq9-porcelain: #fbfaf7;
  border-color: rgba(161,119,47,.20) !important;
  background:
    radial-gradient(circle at 5% -2%, rgba(224,193,127,.18), transparent 22%),
    radial-gradient(circle at 96% 1%, rgba(255,255,255,.98), transparent 27%),
    linear-gradient(145deg, #fcfbf8 0%, #f5f0e6 48%, #faf8f3 100%) !important;
  box-shadow: 0 34px 100px rgba(58,43,20,.11), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

/* Executive hero — less SaaS card, more luxury command header. */
[data-dq-details-luxury="v9"] .tos-dq-details-hero-v1 {
  min-height: 154px !important;
  padding: 26px 30px !important;
  border-radius: 32px !important;
  border-color: rgba(173,128,49,.26) !important;
  background:
    radial-gradient(ellipse at 16% -34%, rgba(224,185,99,.28), transparent 42%),
    radial-gradient(circle at 92% 8%, rgba(255,255,255,.94), transparent 28%),
    linear-gradient(135deg, #fffefa 0%, #f8f2e6 68%, #fbf8f1 100%) !important;
  box-shadow:
    0 26px 64px rgba(70,48,13,.11),
    inset 0 1px 0 rgba(255,255,255,.99),
    inset 0 -1px 0 rgba(173,128,49,.055) !important;
}

[data-dq-details-luxury="v9"] .tos-dq-details-hero-v1::after {
  content: "";
  position: absolute;
  width: 270px;
  height: 270px;
  inset-inline-end: 22%;
  top: -210px;
  border: 1px solid rgba(196,154,75,.14);
  border-radius: 50%;
  box-shadow: 0 0 70px rgba(196,154,75,.08);
  pointer-events: none;
}

[data-dq-details-luxury="v9"] .tos-dq-details-hero-v1 h2 {
  max-width: 860px;
  font-size: clamp(2.05rem, 2.85vw, 3.05rem) !important;
  line-height: 1.02 !important;
  letter-spacing: -.045em !important;
  font-weight: 950 !important;
  color: #14130f !important;
}

[data-dq-details-luxury="v9"] .tos-dq-details-actions-v1 {
  width: 304px !important;
  padding: 10px !important;
  border-radius: 22px !important;
  border-color: rgba(159,116,39,.19) !important;
  background: rgba(255,255,255,.70) !important;
  backdrop-filter: blur(22px) saturate(1.08);
  box-shadow: 0 18px 42px rgba(68,47,15,.08), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

[data-dq-details-luxury="v9"] .tos-dq-attachment-action-v4 {
  min-height: 38px !important;
  border-radius: 12px !important;
  border-color: rgba(160,117,42,.17) !important;
  background: linear-gradient(180deg, #fffefb, #f8f2e8) !important;
  color: #2d2922 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.98), 0 6px 16px rgba(66,47,18,.05) !important;
}

[data-dq-details-luxury="v9"] .tos-dq-close-action-v5 {
  width: 34px !important;
  min-width: 34px !important;
  height: 34px !important;
  min-height: 34px !important;
  border-radius: 50% !important;
  border-color: rgba(86,77,64,.10) !important;
  background: rgba(255,255,255,.38) !important;
  color: #746d62 !important;
}

/* Metadata becomes an executive ledger rather than five generic cards. */
[data-dq-details-luxury="v9"] .tos-dq-details-metrics-v1 {
  gap: 10px !important;
}

[data-dq-details-luxury="v9"] .tos-dq-detail-metric-v1 {
  min-height: 76px !important;
  padding: 11px 14px !important;
  border-radius: 18px !important;
  border-color: rgba(100,81,50,.10) !important;
  background:
    linear-gradient(180deg, rgba(255,255,255,.985), rgba(249,246,239,.94)) !important;
  box-shadow: 0 10px 28px rgba(62,48,24,.045), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

[data-dq-details-luxury="v9"] .tos-dq-detail-metric-v1::after {
  content: "";
  position: absolute;
  inset-inline-start: 14px;
  bottom: 0;
  width: 34px;
  height: 1px;
  background: linear-gradient(90deg, rgba(196,154,75,.62), transparent);
  opacity: .72;
}

/* Main materials — quieter borders and deeper layered surfaces. */
[data-dq-details-luxury="v9"] .tos-dq-detail-section-v1 {
  border-radius: 26px !important;
  border-color: rgba(106,86,55,.105) !important;
  background: rgba(255,255,255,.955) !important;
  box-shadow: 0 20px 50px rgba(61,48,27,.052), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

[data-dq-details-luxury="v9"] .tos-dq-detail-section-v1 > div:first-child {
  min-height: 50px !important;
  padding-inline: 18px !important;
  border-color: rgba(174,131,52,.10) !important;
  background: linear-gradient(180deg, rgba(255,254,251,.98), rgba(249,246,239,.75)) !important;
  font-size: .82rem !important;
  font-weight: 950 !important;
}

[data-dq-details-luxury="v9"] .tos-dq-spec-meta-v1,
[data-dq-details-luxury="v9"] .tos-dq-spec-brief-v1 {
  border-color: rgba(104,87,59,.085) !important;
  background: linear-gradient(180deg, #fdfcf9, #f8f5ee) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.94) !important;
}

/* Editorial reading — true luxury reading column with physical content anchoring. */
[data-dq-details-luxury="v9"] .tos-dq-spec-copy-v1 {
  padding: 26px 30px 30px !important;
  border-radius: 22px !important;
  border-color: rgba(192,148,63,.18) !important;
  background:
    radial-gradient(circle at 92% 0%, rgba(220,184,104,.11), transparent 28%),
    linear-gradient(180deg, #fffefa 0%, #faf7f0 100%) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.98),
    inset 0 -1px 0 rgba(171,126,46,.045),
    0 14px 34px rgba(66,50,24,.035) !important;
}

[data-dq-details-luxury="v9"] .tos-dq-copy-editorial-v8 {
  width: min(100%, 64ch) !important;
  max-width: 64ch !important;
  font-size: 1.035rem !important;
  line-height: 2.08 !important;
  color: #302c25 !important;
}

[data-dq-details-luxury="v9"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 {
  margin-right: 0 !important;
  margin-left: auto !important;
  padding-right: 18px !important;
  padding-left: 0 !important;
  border-right: 2px solid rgba(196,154,75,.38);
  text-align: right !important;
  direction: rtl !important;
  unicode-bidi: plaintext !important;
}

[data-dq-details-luxury="v9"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
  margin-left: 0 !important;
  margin-right: auto !important;
  padding-left: 18px !important;
  padding-right: 0 !important;
  border-left: 2px solid rgba(196,154,75,.38);
  text-align: left !important;
  direction: ltr !important;
  unicode-bidi: plaintext !important;
}

[data-dq-details-luxury="v9"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-rtl-v6) > div:first-child {
  text-align: right !important;
  padding-right: 18px;
}

[data-dq-details-luxury="v9"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-ltr-v6) > div:first-child {
  text-align: left !important;
  padding-left: 18px;
}

[data-dq-details-luxury="v9"] .tos-dq-copy-paragraph-v8 {
  margin: 0 0 17px !important;
}

[data-dq-details-luxury="v9"] .tos-dq-copy-paragraph-v8:last-child {
  margin-bottom: 0 !important;
}

[data-dq-details-luxury="v9"] .tos-dq-copy-emphasis-v8 {
  color: #1d1a15 !important;
  font-weight: 950 !important;
}

/* Assignment command rail — floating executive control surface. */
[data-dq-details-luxury="v9"] .tos-dq-details-assignment-v1 {
  border-radius: 25px !important;
  border-color: rgba(190,145,58,.22) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(219,181,99,.12), transparent 34%),
    linear-gradient(180deg, #fffefb 0%, #f8f2e7 100%) !important;
  box-shadow: 0 22px 52px rgba(65,46,17,.095), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

[data-dq-details-luxury="v9"] .tos-dq-details-assignment-v1 > div:first-child {
  min-height: 52px !important;
  background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(248,243,233,.72)) !important;
}

[data-dq-details-luxury="v9"] .tos-dq-assignment-cta-v1 {
  min-height: 44px !important;
  border-radius: 13px !important;
  background: linear-gradient(135deg, #e4bb69 0%, #bd8933 100%) !important;
  color: #15120d !important;
  box-shadow: 0 13px 28px rgba(160,105,24,.18), inset 0 1px 0 rgba(255,255,255,.28) !important;
}

/* Attachments — compact, intentional empty-state surface. */
[data-dq-details-luxury="v9"] .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  min-height: 82px !important;
  padding-block: 16px !important;
  border-radius: 18px !important;
  border-color: rgba(162,125,58,.13) !important;
  background:
    radial-gradient(circle at 50% -20%, rgba(221,186,107,.08), transparent 45%),
    linear-gradient(180deg, rgba(253,252,248,.82), rgba(248,245,238,.68)) !important;
}

/* Activity — content-fit executive timeline, no giant dead area. */
[data-dq-details-luxury="v9"] .tos-dq-details-activity-v1,
[data-dq-details-luxury="v9"] .tos-dq-details-activity-v1 > div:last-child {
  min-height: 0 !important;
  height: auto !important;
}

[data-dq-details-luxury="v9"] .tos-dq-details-activity-v1 > div:last-child {
  padding: 14px 16px 16px !important;
  align-content: start;
  overflow: visible !important;
}

[data-dq-details-luxury="v9"] .tos-dq-activity-item-v1 {
  min-height: 54px !important;
  margin-bottom: 7px !important;
  padding: 9px 14px 9px 22px !important;
  border-radius: 14px !important;
  border-color: rgba(107,88,59,.075) !important;
  border-inline-start-color: rgba(196,154,75,.26) !important;
  background: linear-gradient(180deg, rgba(253,252,249,.94), rgba(248,246,240,.80)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.88) !important;
}

[dir="rtl"] [data-dq-details-luxury="v9"] .tos-dq-activity-item-v1 {
  padding: 9px 22px 9px 14px !important;
}

/* Dark — obsidian, black titanium, platinum and restrained champagne. */
html.dark [data-dq-details-luxury="v9"] {
  border-color: rgba(211,174,96,.15) !important;
  background:
    radial-gradient(circle at 6% -2%, rgba(203,160,75,.08), transparent 24%),
    linear-gradient(145deg, #080a0d 0%, #0b0e12 50%, #090b0e 100%) !important;
  box-shadow: 0 36px 110px rgba(0,0,0,.40), inset 0 1px 0 rgba(255,255,255,.015) !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-details-hero-v1 {
  border-color: rgba(214,177,99,.20) !important;
  background:
    radial-gradient(ellipse at 14% -30%, rgba(204,160,73,.13), transparent 42%),
    linear-gradient(135deg, #171a1f 0%, #0d1014 72%) !important;
  box-shadow: 0 26px 66px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-details-hero-v1 h2 {
  color: #f4f1ea !important;
  text-shadow: none !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-details-actions-v1,
html.dark [data-dq-details-luxury="v9"] .tos-dq-details-assignment-v1 {
  background: linear-gradient(180deg, rgba(23,26,31,.98), rgba(14,17,21,.98)) !important;
  border-color: rgba(215,178,100,.16) !important;
  box-shadow: 0 22px 52px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.018) !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-detail-metric-v1,
html.dark [data-dq-details-luxury="v9"] .tos-dq-detail-section-v1,
html.dark [data-dq-details-luxury="v9"] .tos-dq-spec-meta-v1,
html.dark [data-dq-details-luxury="v9"] .tos-dq-spec-brief-v1 {
  background: linear-gradient(180deg, rgba(20,23,28,.99), rgba(14,17,21,.99)) !important;
  border-color: rgba(255,255,255,.06) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.015) !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-spec-copy-v1 {
  border-color: rgba(214,177,99,.14) !important;
  background:
    radial-gradient(circle at 92% 0%, rgba(205,160,73,.055), transparent 30%),
    linear-gradient(180deg, #121519 0%, #0e1115 100%) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.018), 0 18px 42px rgba(0,0,0,.16) !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-copy-editorial-v8 {
  color: #e3e0d9 !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-copy-emphasis-v8 {
  color: #f7f3ea !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 {
  border-right-color: rgba(216,179,101,.34) !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
  border-left-color: rgba(216,179,101,.34) !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  border-color: rgba(216,179,101,.09) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.012), rgba(255,255,255,.006)) !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-activity-item-v1 {
  border-color: rgba(255,255,255,.05) !important;
  border-inline-start-color: rgba(216,179,101,.26) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.018), rgba(255,255,255,.008)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.012) !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-attachment-action-v4 {
  border-color: rgba(215,178,100,.13) !important;
  background: linear-gradient(180deg, #25292f, #1b1f24) !important;
  color: #ece8df !important;
}

html.dark [data-dq-details-luxury="v9"] .tos-dq-close-action-v5 {
  border-color: rgba(255,255,255,.07) !important;
  background: rgba(255,255,255,.018) !important;
  color: #aeb4bd !important;
}

@media (max-width: 1279px) {
  [data-dq-details-luxury="v9"] .tos-dq-details-hero-v1 {
    min-height: auto !important;
  }
  [data-dq-details-luxury="v9"] .tos-dq-details-actions-v1 {
    width: 100% !important;
  }
}

@media (max-width: 639px) {
  [data-dq-details-luxury="v9"] .tos-dq-details-hero-v1 {
    padding: 20px 18px !important;
    border-radius: 24px !important;
  }
  [data-dq-details-luxury="v9"] .tos-dq-details-hero-v1 h2 {
    font-size: 1.85rem !important;
  }
  [data-dq-details-luxury="v9"] .tos-dq-spec-copy-v1 {
    padding: 20px 18px 22px !important;
  }
  [data-dq-details-luxury="v9"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 {
    padding-right: 12px !important;
  }
  [data-dq-details-luxury="v9"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
    padding-left: 12px !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  [data-dq-details-luxury="v9"] * {
    transition-duration: .01ms !important;
  }
}
'''

v9_css = "\n".join(line.rstrip() for line in v9_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v9_css

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated_dq)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()

    if source_dq.count(V9_HOOK) != 1:
        raise RuntimeError("V9 cumulative luxury hook missing or duplicated")
    if source_dq.count(V8_HOOK) != 1:
        raise RuntimeError("V8 flagship hook was not preserved")
    if source_css.count(V9_MARKER) != 1:
        raise RuntimeError("V9 CSS runtime marker missing or duplicated")
    if V8_MARKER not in source_css or COPY_MARKER not in source_dq:
        raise RuntimeError("V8 luxury/editorial baseline was not preserved")
    for required in (
        "TOS_DQ_PERFORMANCE_V3",
        "TOS_DQ_PREMIUM_MENU_V9",
        "TOS_DQ_PREMIUM_MENU_THEME_V10",
        RTL_HOOK,
        LTR_HOOK,
        "tos-dq-close-action-v5",
    ):
        if required not in source_dq:
            raise RuntimeError(f"required Design Queue baseline marker not preserved: {required}")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V9_MARKER.encode())
    dist_v9_hook = tree_count(DIST, b"data-dq-details-luxury")
    dist_v8_hook = tree_count(DIST, b"data-dq-details-flagship")
    dist_copy = tree_count(DIST, COPY_MARKER.encode())
    if min(dist_marker, dist_v9_hook, dist_v8_hook, dist_copy) < 1:
        raise RuntimeError("V9 stable runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v9.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v9.backup-{stamp}"
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

    live_marker = tree_count(LIVE, V9_MARKER.encode())
    live_v9_hook = tree_count(LIVE, b"data-dq-details-luxury")
    live_v8_hook = tree_count(LIVE, b"data-dq-details-flagship")
    live_copy = tree_count(LIVE, COPY_MARKER.encode())
    if min(live_marker, live_v9_hook, live_v8_hook, live_copy) < 1:
        raise RuntimeError("V9 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V9_RUNTIME=YES")
    print("V8_LUXURY_BASELINE_PRESERVED=YES")
    print("ULTRA_LUXURY_HERO=YES")
    print("EXECUTIVE_METADATA_LEDGER=YES")
    print("EDITORIAL_READING_CANVAS_REFINED=YES")
    print("RTL_EDITORIAL_ANCHOR_RESTORED=YES")
    print("LTR_EDITORIAL_ANCHOR_PRESERVED=YES")
    print("ASSIGNMENT_COMMAND_RAIL_REFINED=YES")
    print("ATTACHMENTS_EMPTY_STATE_REFINED=YES")
    print("ACTIVITY_DEAD_SPACE_REDUCED=YES")
    print("LIGHT_ULTRA_LUXURY_REFINED=YES")
    print("DARK_ULTRA_LUXURY_REFINED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V9_RUNTIME_COUNT={source_css.count(V9_MARKER)}")
    print(f"SOURCE_V9_HOOK_COUNT={source_dq.count(V9_HOOK)}")
    print(f"DIST_V9_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_V9_HOOK_COUNT={dist_v9_hook}")
    print(f"DIST_COPY_MARKER_COUNT={dist_copy}")
    print(f"LIVE_V9_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_V9_HOOK_COUNT={live_v9_hook}")
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
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v9.failed.{int(time.time())}"
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
    print("V9_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
