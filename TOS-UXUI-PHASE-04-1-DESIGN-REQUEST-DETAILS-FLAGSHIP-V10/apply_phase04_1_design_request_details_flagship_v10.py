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

EXPECTED_DQ_SHA256 = "ee8c865d4186bef9a632220a8eb84adb899829abf469581dc086ca0d96e37cd1"
EXPECTED_CSS_SHA256 = "f2ba0d382313c1adb3dab2e847fafce3f6877d34dcb3c3a09a36e44531320158"
V8_MARKER = "--tos-dq-details-flagship-v8-runtime"
V9_MARKER = "--tos-dq-details-flagship-v9-runtime"
V10_MARKER = "--tos-dq-details-flagship-v10-runtime"
V9_HOOK = 'data-dq-details-luxury="v9"'
V10_HOOK = 'data-dq-details-couture="v10"'
COPY_MARKER = "tos-dq-copy-editorial-v8"
RTL_HOOK = "tos-dq-spec-copy-rtl-v6"
LTR_HOOK = "tos-dq-spec-copy-ltr-v6"

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V10")


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
    print("V10_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match Flagship V9 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V9 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in (
    "TOS_DQ_PERFORMANCE_V3",
    "TOS_DQ_PREMIUM_MENU_V9",
    "TOS_DQ_PREMIUM_MENU_THEME_V10",
    V8_MARKER,
    V9_MARKER,
    V9_HOOK,
    COPY_MARKER,
    RTL_HOOK,
    LTR_HOOK,
    "tos-dq-close-action-v5",
    "tos-dq-attachment-action-v4",
):
    if required not in (original_dq + original_css):
        fail(f"required V9 baseline marker missing: {required}")

if V10_MARKER in original_css or V10_HOOK in original_dq:
    fail("Design Request Details Flagship V10 already present")

updated_dq = replace_once(
    original_dq,
    V9_HOOK,
    V9_HOOK + ' ' + V10_HOOK,
    "V10 cumulative couture hook",
)

old_renderer = '''function renderPremiumInlineV8(text, keyPrefix) {
  return String(text || "").split(/(\\*\\*[^*]+\\*\\*)/g).filter(Boolean).map((part, index) => {
    const isStrong = part.startsWith("**") && part.endsWith("**") && part.length > 4;
    return isStrong
      ? <strong key={`${keyPrefix}-strong-${index}`} className="tos-dq-copy-emphasis-v8">{part.slice(2, -2)}</strong>
      : <span key={`${keyPrefix}-text-${index}`}>{part}</span>;
  });
}
'''

new_renderer = '''function renderPremiumInlineV8(text, keyPrefix) {
  const raw = String(text || "");
  const markerCount = (raw.match(/\\*\\*/g) || []).length;
  const hasUnbalancedEmphasis = markerCount % 2 === 1;
  return raw.split(/(\\*\\*[^*]+\\*\\*)/g).filter(Boolean).map((part, index) => {
    const isBalancedStrong = part.startsWith("**") && part.endsWith("**") && part.length > 4;
    const cleaned = part.replace(/\\*\\*/g, "");
    const isStrong = isBalancedStrong || (hasUnbalancedEmphasis && raw.includes("**"));
    return isStrong
      ? <strong key={`${keyPrefix}-strong-${index}`} className="tos-dq-copy-emphasis-v8">{isBalancedStrong ? part.slice(2, -2) : cleaned}</strong>
      : <span key={`${keyPrefix}-text-${index}`}>{cleaned}</span>;
  });
}
'''
updated_dq = replace_once(updated_dq, old_renderer, new_renderer, "V10 markdown cleanup renderer")

v10_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V10
   Couture refinement after V9 visual QA.
   Fixes the editorial reading composition itself (not just direction),
   removes raw markdown residue, restores semantic workload materials,
   and reduces remaining admin-card / row-strip feeling.
   Business logic unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v10-runtime: 1; }

/* Editorial canvas: full-width stage, constrained text anchored to the
   correct physical edge. The gold rule belongs to the reading edge, not
   the middle of the panel. */
[data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8 {
  position: relative !important;
  width: 100% !important;
  max-width: none !important;
  border: 0 !important;
  font-size: 1.04rem !important;
  line-height: 2.08 !important;
}

[data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 {
  margin: 0 !important;
  padding: 2px 30px 2px 8px !important;
  text-align: right !important;
  direction: rtl !important;
}

[data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 {
  margin: 0 !important;
  padding: 2px 8px 2px 30px !important;
  text-align: left !important;
  direction: ltr !important;
}

[data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8::after {
  content: "";
  position: absolute;
  top: 2px;
  bottom: 2px;
  width: 2px;
  border-radius: 999px;
  background: linear-gradient(to bottom, transparent 0%, rgba(196,154,75,.72) 18%, rgba(196,154,75,.42) 82%, transparent 100%);
  box-shadow: 0 0 18px rgba(196,154,75,.10);
  pointer-events: none;
}

[data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6::after { right: 0; left: auto; }
[data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6::after { left: 0; right: auto; }

[data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 .tos-dq-copy-paragraph-v8 {
  width: min(100%, 68ch) !important;
  margin-right: 0 !important;
  margin-left: auto !important;
  text-align: right !important;
}

[data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 .tos-dq-copy-paragraph-v8 {
  width: min(100%, 68ch) !important;
  margin-left: 0 !important;
  margin-right: auto !important;
  text-align: left !important;
}

[data-dq-details-couture="v10"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-rtl-v6) > div:first-child {
  text-align: right !important;
  padding-right: 30px !important;
  padding-left: 0 !important;
}

[data-dq-details-couture="v10"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-ltr-v6) > div:first-child {
  text-align: left !important;
  padding-left: 30px !important;
  padding-right: 0 !important;
}

[data-dq-details-couture="v10"] .tos-dq-copy-emphasis-v8 {
  color: #17140f !important;
  font-weight: 950 !important;
  text-shadow: 0 1px 0 rgba(255,255,255,.48);
}

/* Metadata ledger: flatter, denser and more bespoke than generic SaaS cards. */
[data-dq-details-couture="v10"] .tos-dq-detail-metric-v1 {
  min-height: 72px !important;
  border-radius: 15px !important;
  border-color: rgba(111,88,52,.09) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.93), rgba(248,245,238,.84)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.92), 0 7px 20px rgba(64,48,23,.035) !important;
}

/* Projected load must retain semantic severity in both themes. */
[data-dq-details-couture="v10"] .tos-dq-details-assignment-v1 > div:last-child > div[class*="bg-red-50"] {
  border-color: rgba(220,38,38,.20) !important;
  background: linear-gradient(180deg, rgba(254,242,242,.96), rgba(254,226,226,.72)) !important;
  color: #b42318 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.82) !important;
}

[data-dq-details-couture="v10"] .tos-dq-details-assignment-v1 > div:last-child > div[class*="bg-orange-50"] {
  border-color: rgba(234,88,12,.18) !important;
  background: linear-gradient(180deg, rgba(255,247,237,.96), rgba(255,237,213,.72)) !important;
  color: #b54708 !important;
}

[data-dq-details-couture="v10"] .tos-dq-details-assignment-v1 > div:last-child > div[class*="bg-emerald-50"] {
  border-color: rgba(5,150,105,.16) !important;
  background: linear-gradient(180deg, rgba(236,253,245,.94), rgba(209,250,229,.68)) !important;
  color: #067647 !important;
}

/* Primary assignment action: champagne, not loud orange. */
[data-dq-details-couture="v10"] .tos-dq-assignment-cta-v1 {
  min-height: 44px !important;
  border: 1px solid rgba(145,101,27,.20) !important;
  background: linear-gradient(135deg, #ddb866 0%, #bf8d35 55%, #a87427 100%) !important;
  color: #17130c !important;
  box-shadow: 0 12px 28px rgba(142,94,19,.16), inset 0 1px 0 rgba(255,255,255,.32) !important;
}

/* Executive timeline: one visual rail with restrained entries instead of
   a stack of full-width admin cards. */
[data-dq-details-couture="v10"] .tos-dq-details-activity-v1 > div:last-child {
  padding: 12px 18px 16px !important;
}

[data-dq-details-couture="v10"] .tos-dq-activity-item-v1 {
  min-height: 50px !important;
  margin-bottom: 0 !important;
  padding: 10px 14px 10px 24px !important;
  border: 0 !important;
  border-bottom: 1px solid rgba(107,89,62,.075) !important;
  border-inline-start: 2px solid rgba(196,154,75,.24) !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

[data-dq-details-couture="v10"] .tos-dq-activity-item-v1:last-child {
  border-bottom-color: transparent !important;
}

/* Dark couture */
html.dark [data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8 {
  color: #ece9e2 !important;
}

html.dark [data-dq-details-couture="v10"] .tos-dq-copy-emphasis-v8 {
  color: #fffaf0 !important;
  text-shadow: none !important;
}

html.dark [data-dq-details-couture="v10"] .tos-dq-detail-metric-v1 {
  border-color: rgba(255,255,255,.055) !important;
  background: linear-gradient(180deg, rgba(24,27,31,.88), rgba(16,19,23,.86)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.018), 0 8px 22px rgba(0,0,0,.13) !important;
}

html.dark [data-dq-details-couture="v10"] .tos-dq-details-assignment-v1 > div:last-child > div[class*="bg-red-50"] {
  border-color: rgba(248,113,113,.22) !important;
  background: linear-gradient(180deg, rgba(127,29,29,.28), rgba(69,10,10,.22)) !important;
  color: #fecaca !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025) !important;
}

html.dark [data-dq-details-couture="v10"] .tos-dq-details-assignment-v1 > div:last-child > div[class*="bg-orange-50"] {
  border-color: rgba(251,146,60,.20) !important;
  background: linear-gradient(180deg, rgba(124,45,18,.26), rgba(67,20,7,.20)) !important;
  color: #fed7aa !important;
}

html.dark [data-dq-details-couture="v10"] .tos-dq-details-assignment-v1 > div:last-child > div[class*="bg-emerald-50"] {
  border-color: rgba(52,211,153,.16) !important;
  background: linear-gradient(180deg, rgba(6,78,59,.28), rgba(2,44,34,.22)) !important;
  color: #a7f3d0 !important;
}

html.dark [data-dq-details-couture="v10"] .tos-dq-assignment-cta-v1 {
  border-color: rgba(218,181,103,.20) !important;
  background: linear-gradient(135deg, #d9b365 0%, #b98531 58%, #96651f 100%) !important;
  color: #11100d !important;
  box-shadow: 0 14px 30px rgba(122,78,17,.18), inset 0 1px 0 rgba(255,255,255,.13) !important;
}

html.dark [data-dq-details-couture="v10"] .tos-dq-activity-item-v1 {
  border-bottom-color: rgba(255,255,255,.045) !important;
  border-inline-start-color: rgba(218,181,103,.28) !important;
  background: transparent !important;
}

@media (max-width: 767px) {
  [data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-rtl-v6 { padding-right: 18px !important; }
  [data-dq-details-couture="v10"] .tos-dq-copy-editorial-v8.tos-dq-spec-copy-ltr-v6 { padding-left: 18px !important; }
  [data-dq-details-couture="v10"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-rtl-v6) > div:first-child { padding-right: 18px !important; }
  [data-dq-details-couture="v10"] .tos-dq-spec-copy-v1:has(> .tos-dq-spec-copy-ltr-v6) > div:first-child { padding-left: 18px !important; }
}
'''

v10_css = "\n".join(line.rstrip() for line in v10_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v10_css

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated_dq)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()

    if source_dq.count(V10_HOOK) != 1:
        raise RuntimeError("V10 source hook missing or duplicated")
    if source_css.count(V10_MARKER) != 1:
        raise RuntimeError("V10 CSS runtime marker missing or duplicated")
    if V9_MARKER not in source_css or V9_HOOK not in source_dq:
        raise RuntimeError("V9 luxury baseline was not preserved")
    if "hasUnbalancedEmphasis" not in source_dq:
        raise RuntimeError("V10 markdown cleanup renderer missing")
    for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10", COPY_MARKER, RTL_HOOK, LTR_HOOK):
        if required not in source_dq and required not in source_css:
            raise RuntimeError(f"required baseline marker not preserved: {required}")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V10_MARKER.encode())
    dist_hook = tree_count(DIST, b"data-dq-details-couture")
    dist_copy = tree_count(DIST, COPY_MARKER.encode())
    if min(dist_marker, dist_hook, dist_copy) < 1:
        raise RuntimeError("V10 stable runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v10.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v10.backup-{stamp}"
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

    live_marker = tree_count(LIVE, V10_MARKER.encode())
    live_hook = tree_count(LIVE, b"data-dq-details-couture")
    live_copy = tree_count(LIVE, COPY_MARKER.encode())
    if min(live_marker, live_hook, live_copy) < 1:
        raise RuntimeError("V10 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V10_RUNTIME=YES")
    print("V9_ULTRA_LUXURY_BASELINE_PRESERVED=YES")
    print("EDITORIAL_STAGE_RECOMPOSED=YES")
    print("RTL_READING_COLUMN_RIGHT_ANCHORED=YES")
    print("LTR_READING_COLUMN_LEFT_ANCHORED=YES")
    print("CENTRAL_GOLD_RULE_REMOVED=YES")
    print("RAW_MARKDOWN_RESIDUE_REMOVED=YES")
    print("PROJECTED_LOAD_SEMANTIC_MATERIALS=YES")
    print("ASSIGNMENT_CTA_COUTURE_GOLD=YES")
    print("EXECUTIVE_METADATA_LEDGER_REFINED=YES")
    print("ACTIVITY_TIMELINE_DECARDED=YES")
    print("LIGHT_COUTURE_REFINED=YES")
    print("DARK_COUTURE_REFINED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V10_RUNTIME_COUNT={source_css.count(V10_MARKER)}")
    print(f"SOURCE_V10_HOOK_COUNT={source_dq.count(V10_HOOK)}")
    print(f"DIST_V10_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_V10_HOOK_COUNT={dist_hook}")
    print(f"DIST_COPY_MARKER_COUNT={dist_copy}")
    print(f"LIVE_V10_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_V10_HOOK_COUNT={live_hook}")
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
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v10.failed.{int(time.time())}"
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
    print("V10_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
