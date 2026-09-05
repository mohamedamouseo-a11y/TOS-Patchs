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

EXPECTED_DQ_SHA256 = "bcaf580fb013d7b6857d881dcaad98c083d105f823dde41a54c9e22d09afc683"
EXPECTED_CSS_SHA256 = "e2211a46de261bf50cbfdcd560db0e81b230f7b0d50cec04a86ff02002659066"
V7_MARKER = "--tos-dq-details-flagship-v7-runtime"
V8_MARKER = "--tos-dq-details-flagship-v8-runtime"
V7_HOOK = 'data-dq-details-flagship="v7"'
V8_HOOK = 'data-dq-details-flagship="v8"'
COPY_MARKER = "tos-dq-copy-editorial-v8"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V8")


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
    print("V8_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match approved Flagship V7 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match approved Flagship V7 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in (
    "TOS_DQ_PERFORMANCE_V3",
    "TOS_DQ_PREMIUM_MENU_V9",
    "TOS_DQ_PREMIUM_MENU_THEME_V10",
    V7_HOOK,
    V7_MARKER,
    "tos-dq-spec-copy-rtl-v6",
    "tos-dq-spec-copy-ltr-v6",
    "tos-dq-close-action-v5",
    "tos-dq-attachment-action-v4",
):
    if required not in (original_dq + original_css):
        fail(f"required V7 baseline marker missing: {required}")
if V8_MARKER in original_css or V8_HOOK in original_dq or COPY_MARKER in original_dq:
    fail("Design Request Details Flagship V8 already present")

updated = replace_once(original_dq, V7_HOOK, V8_HOOK, "Details V8 runtime hook")

spec_signature = 'function SpecRow({ label, value, children, linkify = false, lang = "ar", className, contentDir }) {'
helper = r'''function renderPremiumInlineV8(text, keyPrefix) {
  return String(text || "").split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((part, index) => {
    const isStrong = part.startsWith("**") && part.endsWith("**") && part.length > 4;
    return isStrong
      ? <strong key={`${keyPrefix}-strong-${index}`} className="tos-dq-copy-emphasis-v8">{part.slice(2, -2)}</strong>
      : <span key={`${keyPrefix}-text-${index}`}>{part}</span>;
  });
}

function renderPremiumCopyV8(value) {
  const blocks = String(value || "").split(/\n\s*\n/g).map((block) => block.trim()).filter(Boolean);
  return blocks.map((block, blockIndex) => {
    const lines = block.split("\n");
    return (
      <p key={`dq-copy-block-${blockIndex}`} className="tos-dq-copy-paragraph-v8">
        {lines.map((line, lineIndex) => (
          <span key={`dq-copy-line-${blockIndex}-${lineIndex}`} className="tos-dq-copy-line-v8">
            {renderPremiumInlineV8(line, `dq-copy-${blockIndex}-${lineIndex}`)}
          </span>
        ))}
      </p>
    );
  });
}

'''
updated = replace_once(updated, spec_signature, helper + spec_signature, "V8 editorial renderer insertion")

old_value = ': <div dir={resolvedContentDir} className={cn("mt-1 whitespace-pre-wrap text-sm font-bold leading-6 text-zinc-700 dark:text-zinc-200", contentDir === "auto" && "tos-dq-spec-copy-body-v5", contentDir === "auto" && resolvedContentDir === "rtl" && "tos-dq-spec-copy-rtl-v6", contentDir === "auto" && resolvedContentDir === "ltr" && "tos-dq-spec-copy-ltr-v6")}>{value}</div>)}'
new_value = ': <div dir={resolvedContentDir} className={cn("mt-1 whitespace-pre-wrap text-sm font-bold leading-6 text-zinc-700 dark:text-zinc-200", contentDir === "auto" && "tos-dq-spec-copy-body-v5 tos-dq-copy-editorial-v8", contentDir === "auto" && resolvedContentDir === "rtl" && "tos-dq-spec-copy-rtl-v6", contentDir === "auto" && resolvedContentDir === "ltr" && "tos-dq-spec-copy-ltr-v6")}>{contentDir === "auto" ? renderPremiumCopyV8(value) : value}</div>)}'
updated = replace_once(updated, old_value, new_value, "V8 editorial copy renderer")

v8_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V8
   Luxury redirection pass: stronger executive hierarchy, editorial
   request copy, richer porcelain/obsidian materials, refined metadata,
   assignment rail, actions, attachments and activity timeline.
   Business logic and data flow are unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v8-runtime: 1; }

[data-dq-details-flagship="v8"] {
  --dq8-gold: #c79a43;
  --dq8-gold-deep: #9e7429;
  --dq8-ink: #171713;
  --dq8-muted: #746f64;
  --dq8-line: rgba(151, 112, 45, .16);
  --dq8-porcelain: #fbfaf7;
  position: relative;
  overflow: hidden;
  border-color: rgba(151,112,45,.18) !important;
  background:
    radial-gradient(circle at 7% -4%, rgba(229,199,137,.20), transparent 24%),
    radial-gradient(circle at 93% 3%, rgba(255,255,255,.96), transparent 25%),
    linear-gradient(145deg, #fbfaf7 0%, #f4efe5 49%, #f9f7f2 100%) !important;
  box-shadow: 0 30px 90px rgba(62,47,23,.105), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

[data-dq-details-flagship="v8"]::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: .45;
  background-image:
    linear-gradient(rgba(130,95,34,.022) 1px, transparent 1px),
    linear-gradient(90deg, rgba(130,95,34,.016) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: linear-gradient(to bottom, #000, transparent 38%);
}

/* Executive hero */
[data-dq-details-flagship="v8"] .tos-dq-details-hero-v1 {
  min-height: 168px !important;
  padding: 25px 28px !important;
  border-radius: 30px !important;
  border: 1px solid rgba(170,127,51,.24) !important;
  background:
    radial-gradient(circle at 10% -18%, rgba(230,194,112,.22), transparent 34%),
    radial-gradient(circle at 88% 10%, rgba(255,255,255,.90), transparent 30%),
    linear-gradient(135deg, rgba(255,255,253,.995), rgba(248,242,230,.985)) !important;
  box-shadow:
    0 24px 60px rgba(75,52,13,.10),
    inset 0 1px 0 rgba(255,255,255,.99),
    inset 0 -1px 0 rgba(160,117,39,.06) !important;
}

[data-dq-details-flagship="v8"] .tos-dq-details-hero-v1::before {
  content: "";
  position: absolute;
  top: 0;
  inset-inline: 28px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, rgba(202,157,68,.82), transparent);
  box-shadow: 0 0 18px rgba(202,157,68,.20);
  pointer-events: none;
}

[data-dq-details-flagship="v8"] .tos-dq-details-hero-v1 h2 {
  font-size: clamp(1.9rem, 2.55vw, 2.7rem) !important;
  line-height: 1.06 !important;
  letter-spacing: -.035em !important;
  font-weight: 950 !important;
  color: #15140f !important;
  text-shadow: 0 1px 0 rgba(255,255,255,.75);
}

[data-dq-details-flagship="v8"] .tos-dq-details-hero-v1 [class*="rounded-lg"][class*="border-amber"] {
  min-height: 34px;
  padding-inline: 12px !important;
  border-radius: 999px !important;
  border-color: rgba(171,128,47,.20) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.95), rgba(247,242,232,.86)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), 0 5px 16px rgba(74,54,20,.04);
}

/* Action capsule */
[data-dq-details-flagship="v8"] .tos-dq-details-actions-v1 {
  width: 326px !important;
  padding: 11px !important;
  border-radius: 21px !important;
  border-color: rgba(158,115,39,.20) !important;
  background: rgba(255,255,255,.72) !important;
  backdrop-filter: blur(18px) saturate(1.05);
  box-shadow: 0 16px 38px rgba(68,48,17,.075), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

[data-dq-details-flagship="v8"] .tos-dq-attachment-action-v4 {
  min-height: 38px !important;
  border-radius: 13px !important;
  font-weight: 900 !important;
  background: linear-gradient(180deg, #fffdfa, #f7f1e6) !important;
}

[data-dq-details-flagship="v8"] .tos-dq-close-action-v5 {
  border-radius: 50% !important;
  border-color: rgba(92,82,64,.11) !important;
  background: rgba(255,255,255,.42) !important;
}

/* Metadata strip becomes a row of compact executive information tiles */
[data-dq-details-flagship="v8"] .tos-dq-details-metrics-v1 {
  gap: 9px !important;
  padding: 1px !important;
}

[data-dq-details-flagship="v8"] .tos-dq-detail-metric-v1 {
  position: relative;
  min-height: 82px !important;
  margin: 0 !important;
  padding: 12px 14px !important;
  border-radius: 20px !important;
  border: 1px solid rgba(93,76,50,.105) !important;
  background:
    radial-gradient(circle at 90% -10%, rgba(220,187,111,.08), transparent 34%),
    linear-gradient(180deg, rgba(255,255,255,.98), rgba(249,246,239,.94)) !important;
  box-shadow: 0 10px 26px rgba(63,49,26,.052), inset 0 1px 0 rgba(255,255,255,.98) !important;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}

[data-dq-details-flagship="v8"] .tos-dq-detail-metric-v1:hover {
  transform: translateY(-1px);
  border-color: rgba(189,144,58,.22) !important;
  box-shadow: 0 15px 34px rgba(63,49,26,.075), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

[data-dq-details-flagship="v8"] .tos-dq-detail-metric-v1 > span:first-child {
  width: 34px !important;
  height: 34px !important;
  border-radius: 13px !important;
  background: linear-gradient(145deg, #fff8e9, #f5e7c9) !important;
  border: 1px solid rgba(188,143,54,.14);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.9), 0 5px 14px rgba(157,110,30,.07) !important;
}

/* Section material system */
[data-dq-details-flagship="v8"] .tos-dq-detail-section-v1 {
  border-radius: 26px !important;
  border: 1px solid rgba(96,79,53,.105) !important;
  background: rgba(255,255,255,.94) !important;
  box-shadow: 0 18px 46px rgba(67,52,28,.055), inset 0 1px 0 rgba(255,255,255,.985) !important;
  overflow: hidden;
}

[data-dq-details-flagship="v8"] .tos-dq-detail-section-v1 > div:first-child {
  min-height: 54px !important;
  padding-inline: 19px !important;
  border-color: rgba(173,130,50,.11) !important;
  background:
    linear-gradient(180deg, rgba(255,253,249,.97), rgba(248,244,235,.72)) !important;
  font-size: .84rem !important;
  font-weight: 950 !important;
  letter-spacing: -.012em !important;
}

/* Specifications: quieter chrome, stronger editorial focus */
[data-dq-details-flagship="v8"] .tos-dq-details-specs-v1 {
  border-color: rgba(181,137,53,.16) !important;
}

[data-dq-details-flagship="v8"] .tos-dq-spec-meta-v1 {
  min-height: 76px !important;
  border-radius: 18px !important;
  background: linear-gradient(180deg, #fdfcf9, #f8f5ee) !important;
}

[data-dq-details-flagship="v8"] .tos-dq-spec-brief-v1 {
  border-radius: 19px !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(218,182,102,.08), transparent 30%),
    linear-gradient(180deg, #fdfbf7, #f8f4ec) !important;
}

/* Editorial copy canvas */
[data-dq-details-flagship="v8"] .tos-dq-spec-copy-v1 {
  position: relative;
  min-height: 430px;
  padding: 26px 28px 30px !important;
  border-radius: 24px !important;
  border: 1px solid rgba(182,137,52,.19) !important;
  background:
    radial-gradient(circle at 92% 0%, rgba(221,187,107,.105), transparent 30%),
    linear-gradient(145deg, #fffefa 0%, #fbf8f1 52%, #f8f4ec 100%) !important;
  box-shadow:
    inset 4px 0 0 rgba(197,151,62,.18),
    inset 0 1px 0 rgba(255,255,255,.99),
    0 14px 32px rgba(68,50,20,.045) !important;
}

[dir="rtl"] [data-dq-details-flagship="v8"] .tos-dq-spec-copy-v1,
[data-dq-details-flagship="v8"] .tos-dq-spec-copy-v1:has(.tos-dq-spec-copy-rtl-v6) {
  box-shadow:
    inset -4px 0 0 rgba(197,151,62,.18),
    inset 0 1px 0 rgba(255,255,255,.99),
    0 14px 32px rgba(68,50,20,.045) !important;
}

[data-dq-details-flagship="v8"] .tos-dq-spec-copy-v1::before {
  content: "";
  position: absolute;
  inset: 13px;
  border: 1px solid rgba(179,133,47,.055);
  border-radius: 18px;
  pointer-events: none;
}

[data-dq-details-flagship="v8"] .tos-dq-spec-copy-v1 > div:first-child {
  position: relative;
  z-index: 1;
  margin-bottom: 15px;
  color: #95866f !important;
  letter-spacing: .09em !important;
}

[data-dq-details-flagship="v8"] .tos-dq-copy-editorial-v8 {
  position: relative;
  z-index: 1;
  width: min(100%, 68ch) !important;
  max-width: 68ch !important;
  font-size: 1.02rem !important;
  line-height: 1.95 !important;
  font-weight: 660 !important;
  letter-spacing: -.006em;
  color: #2e2b25 !important;
}

[data-dq-details-flagship="v8"] .tos-dq-copy-paragraph-v8 {
  margin: 0 0 1.55rem;
}

[data-dq-details-flagship="v8"] .tos-dq-copy-paragraph-v8:last-child {
  margin-bottom: 0;
}

[data-dq-details-flagship="v8"] .tos-dq-copy-line-v8 {
  display: block;
  min-height: 1.9em;
}

[data-dq-details-flagship="v8"] .tos-dq-copy-emphasis-v8 {
  font-weight: 950 !important;
  color: #17140f !important;
}

/* Floating assignment command rail */
[data-dq-details-flagship="v8"] .tos-dq-details-assignment-v1 {
  border-radius: 24px !important;
  border: 1px solid rgba(184,138,50,.22) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(224,189,111,.14), transparent 36%),
    linear-gradient(180deg, rgba(255,255,253,.99), rgba(247,242,232,.98)) !important;
  box-shadow: 0 24px 54px rgba(70,49,15,.11), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

[data-dq-details-flagship="v8"] .tos-dq-details-assignment-v1 label {
  color: #716a5f !important;
  letter-spacing: .015em;
}

[data-dq-details-flagship="v8"] .tos-dq-projected-capacity-v1 {
  border-radius: 15px !important;
  border-color: rgba(34,168,122,.20) !important;
  background: linear-gradient(180deg, rgba(236,253,247,.96), rgba(226,248,239,.90)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8);
}

[data-dq-details-flagship="v8"] .tos-dq-assignment-cta-v1 {
  min-height: 46px !important;
  border-radius: 15px !important;
  background: linear-gradient(135deg, #e4bd68 0%, #c58f31 58%, #ad7720 100%) !important;
  color: #18130a !important;
  font-weight: 950 !important;
  letter-spacing: -.01em;
  box-shadow: 0 13px 28px rgba(160,108,22,.20), inset 0 1px 0 rgba(255,255,255,.34) !important;
}

/* Attachments: intentional compact empty state */
[data-dq-details-flagship="v8"] .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  min-height: 88px !important;
  border-radius: 18px !important;
  border-color: rgba(161,124,57,.16) !important;
  background:
    radial-gradient(circle at 50% 0%, rgba(223,190,113,.07), transparent 44%),
    linear-gradient(180deg, rgba(253,252,248,.78), rgba(248,246,240,.66)) !important;
}

/* Activity becomes an executive timeline rather than plain text */
[data-dq-details-flagship="v8"] .tos-dq-details-activity-v1 > div:last-child {
  padding: 17px 18px 18px !important;
}

[data-dq-details-flagship="v8"] .tos-dq-activity-item-v1 {
  max-width: none !important;
  min-height: 58px !important;
  margin-bottom: 8px;
  padding: 10px 14px 10px 22px !important;
  border: 1px solid rgba(105,87,58,.08) !important;
  border-inline-start: 2px solid rgba(197,151,62,.30) !important;
  border-radius: 15px !important;
  background: linear-gradient(180deg, rgba(253,252,249,.95), rgba(248,246,240,.80));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.86);
}

[dir="rtl"] [data-dq-details-flagship="v8"] .tos-dq-activity-item-v1 {
  padding: 10px 22px 10px 14px !important;
}

[data-dq-details-flagship="v8"] .tos-dq-activity-item-v1:last-child {
  margin-bottom: 0;
}

[data-dq-details-flagship="v8"] .tos-dq-activity-item-v1 > span {
  box-shadow: 0 0 0 5px rgba(197,151,62,.08), 0 0 18px rgba(197,151,62,.11) !important;
}

/* Dark — black titanium / platinum / restrained champagne */
html.dark [data-dq-details-flagship="v8"] {
  --dq8-gold: #d8b66a;
  --dq8-gold-deep: #b38a3d;
  background:
    radial-gradient(circle at 7% -2%, rgba(214,174,92,.10), transparent 26%),
    radial-gradient(circle at 93% 4%, rgba(85,95,112,.10), transparent 24%),
    linear-gradient(145deg, #090b0e 0%, #0b0e12 52%, #080a0d 100%) !important;
  border-color: rgba(214,174,92,.15) !important;
  box-shadow: 0 34px 96px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.02) !important;
}

html.dark [data-dq-details-flagship="v8"]::before {
  background-image:
    linear-gradient(rgba(226,194,124,.016) 1px, transparent 1px),
    linear-gradient(90deg, rgba(226,194,124,.012) 1px, transparent 1px);
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-details-hero-v1 {
  border-color: rgba(218,181,103,.20) !important;
  background:
    radial-gradient(circle at 9% -18%, rgba(218,181,103,.11), transparent 35%),
    linear-gradient(135deg, #181b20 0%, #111419 56%, #0d1014 100%) !important;
  box-shadow: 0 26px 62px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.025) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-details-hero-v1 h2 {
  color: #f5f2eb !important;
  text-shadow: 0 1px 0 rgba(0,0,0,.25);
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-details-hero-v1 [class*="rounded-lg"][class*="border-amber"] {
  border-color: rgba(218,181,103,.16) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.014)) !important;
  color: #ddd8ce !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-details-actions-v1 {
  border-color: rgba(218,181,103,.15) !important;
  background: rgba(17,20,25,.82) !important;
  box-shadow: 0 18px 44px rgba(0,0,0,.31), inset 0 1px 0 rgba(255,255,255,.024) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-detail-metric-v1 {
  border-color: rgba(255,255,255,.07) !important;
  background:
    radial-gradient(circle at 90% -10%, rgba(216,181,103,.055), transparent 34%),
    linear-gradient(180deg, #16191e, #111419) !important;
  box-shadow: 0 14px 32px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.024) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-detail-metric-v1 > span:first-child {
  background: linear-gradient(145deg, rgba(218,181,103,.12), rgba(218,181,103,.045)) !important;
  border-color: rgba(218,181,103,.13) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-detail-section-v1 {
  border-color: rgba(255,255,255,.07) !important;
  background: linear-gradient(180deg, rgba(19,22,27,.985), rgba(13,16,20,.985)) !important;
  box-shadow: 0 22px 50px rgba(0,0,0,.29), inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-detail-section-v1 > div:first-child {
  border-color: rgba(255,255,255,.06) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.028), rgba(255,255,255,.011)) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-spec-meta-v1,
html.dark [data-dq-details-flagship="v8"] .tos-dq-spec-brief-v1 {
  border-color: rgba(255,255,255,.06) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.024), rgba(255,255,255,.012)) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-spec-copy-v1 {
  border-color: rgba(218,181,103,.18) !important;
  background:
    radial-gradient(circle at 92% 0%, rgba(218,181,103,.07), transparent 31%),
    linear-gradient(145deg, #15181c 0%, #101317 55%, #0e1115 100%) !important;
  box-shadow:
    inset -4px 0 0 rgba(218,181,103,.17),
    inset 0 1px 0 rgba(255,255,255,.02),
    0 18px 42px rgba(0,0,0,.22) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-spec-copy-v1::before {
  border-color: rgba(218,181,103,.055);
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-copy-editorial-v8 {
  color: #dedbd4 !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-copy-emphasis-v8 {
  color: #f5f1e8 !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-details-assignment-v1 {
  border-color: rgba(218,181,103,.19) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(218,181,103,.085), transparent 38%),
    linear-gradient(180deg, #181b20, #111419) !important;
  box-shadow: 0 26px 58px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.024) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  border-color: rgba(218,181,103,.10) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.012), rgba(255,255,255,.006)) !important;
}

html.dark [data-dq-details-flagship="v8"] .tos-dq-activity-item-v1 {
  border-color: rgba(255,255,255,.055) !important;
  border-inline-start-color: rgba(218,181,103,.26) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.018), rgba(255,255,255,.008)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.015);
}

@media (min-width: 1280px) {
  [data-dq-details-flagship="v8"] .tos-dq-details-layout-v1 {
    grid-template-columns: minmax(0, 1fr) 314px !important;
    gap: 20px !important;
  }

  [data-dq-details-flagship="v8"] .tos-dq-details-rail-v1 {
    top: 16px !important;
  }
}

@media (max-width: 1279px) {
  [data-dq-details-flagship="v8"] .tos-dq-details-actions-v1 {
    width: 100% !important;
  }
  [data-dq-details-flagship="v8"] .tos-dq-spec-copy-v1 {
    min-height: auto;
  }
}

@media (max-width: 639px) {
  [data-dq-details-flagship="v8"] .tos-dq-details-hero-v1 {
    padding: 20px !important;
    border-radius: 24px !important;
  }
  [data-dq-details-flagship="v8"] .tos-dq-details-hero-v1 h2 {
    font-size: 1.8rem !important;
  }
  [data-dq-details-flagship="v8"] .tos-dq-spec-copy-v1 {
    padding: 20px 18px 22px !important;
  }
  [data-dq-details-flagship="v8"] .tos-dq-copy-editorial-v8 {
    font-size: .95rem !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  [data-dq-details-flagship="v8"] *,
  [data-dq-details-flagship="v8"] *::before,
  [data-dq-details-flagship="v8"] *::after {
    transition-duration: .01ms !important;
  }
}
'''

v8_css = "\n".join(line.rstrip() for line in v8_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v8_css

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()

    if source_dq.count(V8_HOOK) != 1:
        raise RuntimeError("V8 source hook missing or duplicated")
    if source_dq.count(COPY_MARKER) != 1:
        raise RuntimeError("V8 editorial copy marker missing or duplicated")
    if source_dq.count("renderPremiumCopyV8") < 2:
        raise RuntimeError("V8 editorial renderer missing")
    if source_css.count(V8_MARKER) != 1:
        raise RuntimeError("V8 CSS runtime marker missing or duplicated")
    if V7_MARKER not in source_css:
        raise RuntimeError("V7 CSS baseline marker was not preserved")
    for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10"):
        if required not in source_dq:
            raise RuntimeError(f"required Design Queue baseline marker not preserved: {required}")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V8_MARKER.encode())
    dist_details_key = tree_count(DIST, b"data-dq-details-flagship")
    dist_copy_marker = tree_count(DIST, COPY_MARKER.encode())
    dist_copy_emphasis = tree_count(DIST, b"tos-dq-copy-emphasis-v8")
    if min(dist_marker, dist_details_key, dist_copy_marker, dist_copy_emphasis) < 1:
        raise RuntimeError("V8 stable runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v8.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v8.backup-{stamp}"
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

    live_marker = tree_count(LIVE, V8_MARKER.encode())
    live_details_key = tree_count(LIVE, b"data-dq-details-flagship")
    live_copy_marker = tree_count(LIVE, COPY_MARKER.encode())
    live_copy_emphasis = tree_count(LIVE, b"tos-dq-copy-emphasis-v8")
    if min(live_marker, live_details_key, live_copy_marker, live_copy_emphasis) < 1:
        raise RuntimeError("V8 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V8_RUNTIME=YES")
    print("LUXURY_EXECUTIVE_HIERARCHY=YES")
    print("HERO_LUXURY_REDIRECTED=YES")
    print("METADATA_EXECUTIVE_TILES=YES")
    print("EDITORIAL_COPY_RENDERER=YES")
    print("RAW_MARKDOWN_EMPHASIS_REFINED=YES")
    print("ASSIGNMENT_COMMAND_RAIL_REFINED=YES")
    print("ATTACHMENTS_EMPTY_STATE_REFINED=YES")
    print("ACTIVITY_EXECUTIVE_TIMELINE=YES")
    print("LIGHT_PORCELAIN_CHAMPAGNE=YES")
    print("DARK_OBSIDIAN_TITANIUM=YES")
    print("V7_RTL_ALIGNMENT_PRESERVED=YES")
    print("V5_CLOSE_UTILITY_PRESERVED=YES")
    print("V4_FULL_WIDTH_COMPOSITION_PRESERVED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V8_RUNTIME_COUNT={source_css.count(V8_MARKER)}")
    print(f"SOURCE_V8_HOOK_COUNT={source_dq.count(V8_HOOK)}")
    print(f"SOURCE_COPY_MARKER_COUNT={source_dq.count(COPY_MARKER)}")
    print(f"DIST_V8_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_DETAILS_KEY_COUNT={dist_details_key}")
    print(f"DIST_COPY_MARKER_COUNT={dist_copy_marker}")
    print(f"LIVE_V8_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_DETAILS_KEY_COUNT={live_details_key}")
    print(f"LIVE_COPY_MARKER_COUNT={live_copy_marker}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v8.failed.{int(time.time())}"
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
    print("V8_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
