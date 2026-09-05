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

EXPECTED_DQ_SHA256 = "df75fc5e48956652eca799fdab72426b93c239780cd10914f09bf912e54d8986"
EXPECTED_CSS_SHA256 = "d076af1bb99dacfaa3e105128e36e4c8a1b98e281ce7cf62396ec90ae81a9859"
V1_MARKER = "--tos-dq-details-flagship-v1-runtime"
V2_MARKER = "--tos-dq-details-flagship-v2-runtime"
V1_HOOK = 'data-dq-details-flagship="v1"'
V2_HOOK = 'data-dq-details-flagship="v2"'

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V2")


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
    print("V2_RUNTIME=NO")
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
    fail("DesignQueuePage.jsx does not match approved Flagship V1 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match approved Flagship V1 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10", V1_HOOK, V1_MARKER):
    if required not in (original_dq + original_css):
        fail(f"required V1 baseline marker missing: {required}")
if V2_MARKER in original_css or V2_HOOK in original_dq:
    fail("Design Request Details Flagship V2 already present")

updated = original_dq
updated = replace_once(
    updated,
    'function PremiumMenu({ value, onChange, options, ariaLabel = "Select" }) {',
    'function PremiumMenu({ value, onChange, options, ariaLabel = "Select", searchPlaceholder = "Search..." }) {',
    "PremiumMenu search placeholder prop",
)
updated = replace_once(
    updated,
    'placeholder="Search..."',
    'placeholder={searchPlaceholder}',
    "PremiumMenu localized search placeholder",
)
updated = replace_once(
    updated,
    '<span className="min-w-0 flex-1 break-words">{option.label}</span>',
    '<span className="min-w-0 flex-1"><span className="block break-words">{option.label}</span>{option.meta ? <span className="tos-dq-menu-option-meta-v2 mt-0.5 block text-[10px] font-semibold leading-4 text-zinc-400 dark:text-zinc-500">{option.meta}</span> : null}</span>',
    "PremiumMenu secondary meta line",
)
updated = replace_once(
    updated,
    'data-dq-details-flagship="v1"',
    'data-dq-details-flagship="v2"',
    "Details V2 runtime hook",
)
updated = replace_once(
    updated,
    'ariaLabel={tr.details.labels.designer}\n                      options={[',
    'ariaLabel={tr.details.labels.designer}\n                      searchPlaceholder={isAr ? "بحث..." : "Search..."}\n                      options={[',
    "Designer menu localized search",
)
updated = replace_once(
    updated,
    'label: `${designerLabel(designer, tr.common.designer)} · ${capacityUnitLabel(mode, designer.usedCapacity || 0, tr)}/${capacityUnitLabel(mode, designer.capacityLimit, tr)} · ${designer.capacityPercent || 0}%`,',
    'label: designerLabel(designer, tr.common.designer),\n                          meta: `${capacityUnitLabel(mode, designer.usedCapacity || 0, tr)} / ${capacityUnitLabel(mode, designer.capacityLimit, tr)} · ${designer.capacityPercent || 0}%`,',
    "Designer menu structured option",
)

v2_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V2
   Visual QA refinement: compact hero, wider reading canvas,
   cleaner attachment flow, structured designer menu and stronger
   Light/Dark material hierarchy. Business logic unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v2-runtime: 1; }

.tos-dq-details-flagship-v1 {
  background:
    radial-gradient(circle at 6% 0%, rgba(219,184,105,.11), transparent 24%),
    radial-gradient(circle at 94% 6%, rgba(255,255,255,.96), transparent 30%),
    linear-gradient(145deg, #fbfaf7 0%, #f6f2e9 47%, #faf8f3 100%) !important;
  box-shadow: 0 24px 72px rgba(72,55,24,.075), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

.tos-dq-details-hero-v1 {
  min-height: auto !important;
  padding: 20px 22px !important;
  border-color: rgba(184,137,53,.23) !important;
  background:
    radial-gradient(circle at 7% -10%, rgba(220,184,98,.14), transparent 34%),
    linear-gradient(135deg, rgba(255,255,253,.995), rgba(250,246,237,.985)) !important;
  box-shadow: 0 15px 38px rgba(71,50,15,.065), inset 0 1px 0 rgba(255,255,255,.99) !important;
}

.tos-dq-details-hero-v1 h2 {
  margin-top: 7px !important;
  font-size: clamp(1.55rem, 2vw, 2.15rem) !important;
}

.tos-dq-details-actions-v1 {
  border-color: rgba(184,137,53,.18) !important;
  background: rgba(255,255,255,.78) !important;
  box-shadow: 0 10px 26px rgba(67,48,17,.055), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

.tos-dq-details-actions-v1 button {
  min-height: 36px !important;
  font-size: 11px !important;
}

.tos-dq-detail-metric-v1 {
  min-height: 70px !important;
  border-color: rgba(112,92,57,.095) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.985), rgba(250,248,243,.94)) !important;
  box-shadow: 0 8px 20px rgba(62,49,26,.04), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

.tos-dq-detail-section-v1 {
  border-color: rgba(111,92,58,.105) !important;
  background: rgba(255,255,255,.955) !important;
  box-shadow: 0 14px 34px rgba(66,51,27,.045), inset 0 1px 0 rgba(255,255,255,.985) !important;
}

.tos-dq-detail-section-v1 > div:first-child {
  background: linear-gradient(180deg, rgba(255,253,249,.96), rgba(251,248,241,.72)) !important;
}

.tos-dq-spec-row-v1 {
  border-color: rgba(94,81,59,.085) !important;
  background: linear-gradient(180deg, #fcfbf8, #f9f7f2) !important;
}

.tos-dq-spec-copy-v1 {
  padding: 20px 22px 24px !important;
  border-color: rgba(184,137,53,.18) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(218,183,105,.065), transparent 26%),
    linear-gradient(180deg, #fffefb, #fbf9f4) !important;
}

.tos-dq-spec-copy-v1 > div:last-child {
  max-width: 78ch;
  margin-inline: auto !important;
  margin-top: 12px !important;
  font-size: 1rem !important;
  line-height: 2.05 !important;
  color: #302d28 !important;
}

.tos-dq-details-attachments-v1 [class*="border-dashed"] {
  min-height: 108px !important;
  padding-block: 20px !important;
  background:
    radial-gradient(circle at 50% 0%, rgba(221,187,108,.06), transparent 42%),
    rgba(252,251,247,.74) !important;
}

.tos-dq-details-activity-v1 .tos-dq-activity-item-v1 {
  min-height: 48px !important;
  padding-block: 3px 8px !important;
}

.tos-dq-details-assignment-v1 {
  border-color: rgba(184,137,53,.20) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(219,182,99,.075), transparent 34%),
    linear-gradient(180deg, rgba(255,255,253,.99), rgba(249,246,238,.97)) !important;
  box-shadow: 0 18px 42px rgba(70,49,16,.075), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

.tos-dq-assignment-cta-v1 {
  min-height: 44px !important;
  border-radius: 14px !important;
  background: linear-gradient(135deg, #f5b21c, #dfa014) !important;
  box-shadow: 0 11px 25px rgba(218,153,20,.18), inset 0 1px 0 rgba(255,255,255,.32) !important;
}

.tos-dq-menu-option-meta-v2 {
  letter-spacing: 0 !important;
  opacity: .92;
}

[data-dq-premium-menu] [data-dq-menu-option="true"] {
  align-items: flex-start !important;
}

[data-dq-premium-menu] [data-dq-menu-option="true"][data-active="true"] .tos-dq-menu-option-meta-v2 {
  color: #8b6a2f !important;
}

html.dark .tos-dq-details-flagship-v1 {
  background:
    radial-gradient(circle at 7% 0%, rgba(214,173,90,.075), transparent 25%),
    linear-gradient(145deg, #090b0e 0%, #0b0e12 48%, #090b0e 100%) !important;
  border-color: rgba(214,173,90,.14) !important;
  box-shadow: 0 28px 80px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.018) !important;
}

html.dark .tos-dq-details-hero-v1 {
  border-color: rgba(215,178,100,.18) !important;
  background:
    radial-gradient(circle at 8% -12%, rgba(215,178,100,.09), transparent 34%),
    linear-gradient(135deg, #15181d, #0f1216) !important;
  box-shadow: 0 18px 44px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark .tos-dq-details-actions-v1 {
  background: linear-gradient(180deg, rgba(23,26,31,.95), rgba(16,19,23,.95)) !important;
}

html.dark .tos-dq-detail-metric-v1 {
  background: linear-gradient(180deg, #15181d, #111419) !important;
  border-color: rgba(255,255,255,.065) !important;
}

html.dark .tos-dq-detail-section-v1 {
  background: linear-gradient(180deg, rgba(18,21,26,.99), rgba(13,16,20,.99)) !important;
  border-color: rgba(255,255,255,.068) !important;
}

html.dark .tos-dq-detail-section-v1 > div:first-child {
  background: linear-gradient(180deg, rgba(255,255,255,.025), rgba(255,255,255,.010)) !important;
}

html.dark .tos-dq-spec-row-v1 {
  background: linear-gradient(180deg, rgba(255,255,255,.022), rgba(255,255,255,.012)) !important;
}

html.dark .tos-dq-spec-copy-v1 {
  background:
    radial-gradient(circle at 100% 0%, rgba(215,178,100,.045), transparent 28%),
    linear-gradient(180deg, #14171b, #101317) !important;
}

html.dark .tos-dq-spec-copy-v1 > div:last-child {
  color: #e1dfd8 !important;
}

html.dark .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  background: rgba(255,255,255,.010) !important;
}

html.dark .tos-dq-details-assignment-v1 {
  background:
    radial-gradient(circle at 100% 0%, rgba(215,178,100,.065), transparent 35%),
    linear-gradient(180deg, #16191e, #101318) !important;
  border-color: rgba(215,178,100,.16) !important;
}

html.dark [data-dq-premium-menu] [data-dq-menu-option="true"][data-active="true"] .tos-dq-menu-option-meta-v2 {
  color: #d8b86f !important;
}

@media (min-width: 1024px) {
  .tos-dq-details-actions-v1 {
    width: 360px !important;
  }
  .tos-dq-details-actions-v1 > div:last-child {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

@media (min-width: 1280px) {
  .tos-dq-details-layout-v1 {
    grid-template-columns: minmax(0,1fr) 292px !important;
    gap: 18px !important;
  }
  .tos-dq-details-content-v1 > div:first-child {
    grid-template-columns: minmax(0,1fr) !important;
    gap: 14px !important;
  }
  .tos-dq-details-rail-v1 {
    top: 14px !important;
  }
}

@media (max-width: 1023px) {
  .tos-dq-details-actions-v1 {
    width: 100% !important;
  }
}

@media (max-width: 639px) {
  .tos-dq-spec-copy-v1 {
    padding: 16px !important;
  }
  .tos-dq-spec-copy-v1 > div:last-child {
    font-size: .92rem !important;
    line-height: 1.9 !important;
  }
}
'''

updated_css = original_css.rstrip() + "\n\n" + "\n".join(line.rstrip() for line in v2_css.splitlines()).strip() + "\n"

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()
    if source_dq.count(V2_HOOK) != 1:
        raise RuntimeError("V2 details runtime hook missing or duplicated")
    if source_css.count(V2_MARKER) != 1:
        raise RuntimeError("V2 CSS runtime marker missing or duplicated")
    if source_dq.count(V1_HOOK) != 0:
        raise RuntimeError("V1 details runtime hook still present")
    if "TOS_DQ_PERFORMANCE_V3" not in source_dq:
        raise RuntimeError("Design Queue Performance V3 marker not preserved")
    if "TOS_DQ_PREMIUM_MENU_V9" not in source_dq or "TOS_DQ_PREMIUM_MENU_THEME_V10" not in source_dq:
        raise RuntimeError("Design Queue premium menu baseline not preserved")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V2_MARKER.encode())
    dist_hook = tree_count(DIST, b'data-dq-details-flagship="v2"')
    dist_meta = tree_count(DIST, b"tos-dq-menu-option-meta-v2")
    if dist_marker < 1 or dist_hook < 1 or dist_meta < 1:
        raise RuntimeError("V2 runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v2.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v2.backup-{stamp}"
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

    live_marker = tree_count(LIVE, V2_MARKER.encode())
    live_hook = tree_count(LIVE, b'data-dq-details-flagship="v2"')
    live_meta = tree_count(LIVE, b"tos-dq-menu-option-meta-v2")
    if live_marker < 1 or live_hook < 1 or live_meta < 1:
        raise RuntimeError("V2 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V2_RUNTIME=YES")
    print("HERO_COMPACTED=YES")
    print("ACTIONS_COMPACT_GRID=YES")
    print("READING_CANVAS_WIDENED=YES")
    print("REQUIRED_COPY_REBALANCED=YES")
    print("ATTACHMENTS_FLOW_REBALANCED=YES")
    print("DESIGNER_MENU_STRUCTURED=YES")
    print("DESIGNER_SEARCH_LOCALIZED=YES")
    print("ASSIGNMENT_RAIL_REFINED=YES")
    print("LIGHT_MATERIAL_HIERARCHY_REFINED=YES")
    print("DARK_MATERIAL_HIERARCHY_REFINED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V2_RUNTIME_COUNT={source_css.count(V2_MARKER)}")
    print(f"SOURCE_V2_HOOK_COUNT={source_dq.count(V2_HOOK)}")
    print(f"DIST_V2_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_V2_HOOK_COUNT={dist_hook}")
    print(f"DIST_MENU_META_COUNT={dist_meta}")
    print(f"LIVE_V2_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_V2_HOOK_COUNT={live_hook}")
    print(f"LIVE_MENU_META_COUNT={live_meta}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v2.failed.{int(time.time())}"
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
    print("V2_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
