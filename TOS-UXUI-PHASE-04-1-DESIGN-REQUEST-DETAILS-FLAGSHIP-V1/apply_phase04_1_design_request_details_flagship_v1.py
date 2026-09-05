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

EXPECTED_DQ_BLOB_SHA = "debf95246a422874a7485eda388b4f8013f5f072"
EXPECTED_CSS_BLOB_SHA = "0a9390b126473ade08c744d0593f6198ceb66dbe"
V1_MARKER = "--tos-dq-details-flagship-v1-runtime"
DETAILS_HOOK = 'data-dq-details-flagship="v1"'

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


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
    print("V1_RUNTIME=NO")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


for path in (DQ, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if git_blob_sha(DQ) != EXPECTED_DQ_BLOB_SHA:
    fail("DesignQueuePage.jsx does not match latest pushed TOS source")
if git_blob_sha(CSS) != EXPECTED_CSS_BLOB_SHA:
    fail("index.css does not match latest pushed TOS source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10"):
    if required not in original_dq:
        fail(f"required Design Queue baseline marker missing: {required}")
if V1_MARKER in original_css or DETAILS_HOOK in original_dq:
    fail("Design Request Details Flagship V1 already present")

updated = original_dq

updated = replace_once(
    updated,
    'function SpecRow({ label, value, children, linkify = false, lang = "ar" }) {',
    'function SpecRow({ label, value, children, linkify = false, lang = "ar", className }) {',
    "SpecRow signature",
)
updated = replace_once(
    updated,
    '<div className="rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-2.5 dark:border-white/10 dark:bg-white/5">\n      <div className="text-[10px] font-black uppercase tracking-wide text-zinc-400">{label}</div>',
    '<div className={cn("tos-dq-spec-row-v1 rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-2.5 dark:border-white/10 dark:bg-white/5", className)}>\n      <div className="text-[10px] font-black uppercase tracking-wide text-zinc-400">{label}</div>',
    "SpecRow hook",
)
updated = replace_once(
    updated,
    '<div className="flex min-w-0 items-center gap-2.5 border-b border-slate-100 px-3 py-2.5 last:border-b-0 sm:border-b-0 sm:border-s sm:last:border-s-0 dark:border-white/10">',
    '<div className="tos-dq-detail-metric-v1 flex min-w-0 items-center gap-2.5 border-b border-slate-100 px-3 py-2.5 last:border-b-0 sm:border-b-0 sm:border-s sm:last:border-s-0 dark:border-white/10">',
    "DetailMetric hook",
)
updated = replace_once(
    updated,
    'className={cn("overflow-hidden rounded-[20px] border border-amber-100/80 bg-white shadow-sm shadow-amber-950/[0.03] dark:border-white/10 dark:bg-zinc-950", className)}',
    'className={cn("tos-dq-detail-section-v1 overflow-hidden rounded-[20px] border border-amber-100/80 bg-white shadow-sm shadow-amber-950/[0.03] dark:border-white/10 dark:bg-zinc-950", className)}',
    "DetailSection hook",
)
updated = replace_once(
    updated,
    '<section className="min-h-[calc(100vh-138px)] w-full rounded-[24px] border border-amber-100/80 bg-[#f8f5ee] p-2.5 shadow-[0_16px_52px_rgba(120,83,20,0.07)] dark:border-white/10 dark:bg-zinc-950" dir={isAr ? "rtl" : "ltr"}>',
    '<section data-dq-details-flagship="v1" className="tos-dq-details-flagship-v1 min-h-[calc(100vh-138px)] w-full rounded-[24px] border border-amber-100/80 bg-[#f8f5ee] p-2.5 shadow-[0_16px_52px_rgba(120,83,20,0.07)] dark:border-white/10 dark:bg-zinc-950" dir={isAr ? "rtl" : "ltr"}>',
    "Details root hook",
)
updated = replace_once(
    updated,
    '<header className="relative overflow-hidden rounded-[20px] border border-amber-200/80 bg-[#fffaf0] px-4 py-4 dark:border-amber-400/20 dark:bg-amber-500/[0.06]">',
    '<header className="tos-dq-details-hero-v1 relative overflow-hidden rounded-[20px] border border-amber-200/80 bg-[#fffaf0] px-4 py-4 dark:border-amber-400/20 dark:bg-amber-500/[0.06]">',
    "Hero hook",
)
updated = replace_once(
    updated,
    '<div className="w-full shrink-0 rounded-[18px] border border-amber-200/80 bg-white/90 p-2.5 shadow-sm lg:w-[260px] dark:border-amber-400/20 dark:bg-zinc-900/90">',
    '<div className="tos-dq-details-actions-v1 w-full shrink-0 rounded-[18px] border border-amber-200/80 bg-white/90 p-2.5 shadow-sm lg:w-[260px] dark:border-amber-400/20 dark:bg-zinc-900/90">',
    "Actions hook",
)
updated = replace_once(
    updated,
    '<div className="grid overflow-hidden rounded-[18px] border border-amber-100 bg-white sm:grid-cols-5 dark:border-white/10 dark:bg-zinc-950">',
    '<div className="tos-dq-details-metrics-v1 grid overflow-hidden rounded-[18px] border border-amber-100 bg-white sm:grid-cols-5 dark:border-white/10 dark:bg-zinc-950">',
    "Metrics hook",
)
updated = replace_once(
    updated,
    '<div dir="ltr" className="grid items-start gap-3 xl:grid-cols-[minmax(0,1fr)_290px]">',
    '<div dir="ltr" className="tos-dq-details-layout-v1 grid items-start gap-3 xl:grid-cols-[minmax(0,1fr)_320px]">',
    "Main layout hook",
)
updated = replace_once(
    updated,
    '<div dir={isAr ? "rtl" : "ltr"} className="min-w-0 space-y-3">',
    '<div dir={isAr ? "rtl" : "ltr"} className="tos-dq-details-content-v1 min-w-0 space-y-3">',
    "Content hook",
)
updated = replace_once(
    updated,
    '<DetailSection direction={isAr ? "rtl" : "ltr"} icon={FileText} title={tr.details.sections.specifications}>',
    '<DetailSection className="tos-dq-details-specs-v1" direction={isAr ? "rtl" : "ltr"} icon={FileText} title={tr.details.sections.specifications}>',
    "Specifications section hook",
)
updated = replace_once(
    updated,
    '<SpecRow label={tr.details.labels.designType} value={getDesignTypeLabel(task.designRequest?.designType, lang, task.designRequest)} />',
    '<SpecRow className="tos-dq-spec-meta-v1" label={tr.details.labels.designType} value={getDesignTypeLabel(task.designRequest?.designType, lang, task.designRequest)} />',
    "Design type spec hook",
)
updated = replace_once(
    updated,
    '<SpecRow label={tr.details.labels.platform} value={getDesignPlatformLabel(task.designRequest?.platform, lang, task.designRequest)} />',
    '<SpecRow className="tos-dq-spec-meta-v1" label={tr.details.labels.platform} value={getDesignPlatformLabel(task.designRequest?.platform, lang, task.designRequest)} />',
    "Platform spec hook",
)
updated = replace_once(
    updated,
    '<SpecRow label={tr.details.labels.brief} value={task.designRequest?.brief} linkify lang={lang} />',
    '<SpecRow className="tos-dq-spec-brief-v1" label={tr.details.labels.brief} value={task.designRequest?.brief} linkify lang={lang} />',
    "Brief spec hook",
)
updated = replace_once(
    updated,
    '<SpecRow label={tr.details.labels.requiredText} value={task.designRequest?.requiredText} />',
    '<SpecRow className="tos-dq-spec-copy-v1" label={tr.details.labels.requiredText} value={task.designRequest?.requiredText} />',
    "Required copy hook",
)
updated = replace_once(
    updated,
    '<SpecRow label={tr.details.labels.notes} value={task.designRequest?.notes} linkify lang={lang} />',
    '<SpecRow className="tos-dq-spec-notes-v1" label={tr.details.labels.notes} value={task.designRequest?.notes} linkify lang={lang} />',
    "Notes hook",
)
updated = replace_once(
    updated,
    '<DetailSection direction={isAr ? "rtl" : "ltr"} icon={Paperclip} title={`${tr.details.sections.attachments} (${attachmentFiles.length})`}>',
    '<DetailSection className="tos-dq-details-attachments-v1" direction={isAr ? "rtl" : "ltr"} icon={Paperclip} title={`${tr.details.sections.attachments} (${attachmentFiles.length})`}>',
    "Attachments section hook",
)
updated = replace_once(
    updated,
    '<DetailSection direction={isAr ? "rtl" : "ltr"} icon={MessageCircle} title={tr.details.sections.activity}>',
    '<DetailSection className="tos-dq-details-activity-v1" direction={isAr ? "rtl" : "ltr"} icon={MessageCircle} title={tr.details.sections.activity}>',
    "Activity section hook",
)
updated = replace_once(
    updated,
    'className="relative border-s-2 border-amber-100 ps-5 dark:border-amber-400/20"',
    'className="tos-dq-activity-item-v1 relative border-s-2 border-amber-100 ps-5 dark:border-amber-400/20"',
    "Activity item hook",
)
updated = replace_once(
    updated,
    '<aside dir={isAr ? "rtl" : "ltr"} className="space-y-3 xl:sticky xl:top-3">',
    '<aside dir={isAr ? "rtl" : "ltr"} className="tos-dq-details-rail-v1 space-y-3 xl:sticky xl:top-3">',
    "Sticky rail hook",
)
updated = replace_once(
    updated,
    '<DetailSection direction={isAr ? "rtl" : "ltr"} icon={UserRound} title={tr.details.labels.assignment}>',
    '<DetailSection className="tos-dq-details-assignment-v1" direction={isAr ? "rtl" : "ltr"} icon={UserRound} title={tr.details.labels.assignment}>',
    "Assignment section hook",
)
updated = replace_once(
    updated,
    '<DetailSection direction={isAr ? "rtl" : "ltr"} icon={UserPlus} title={tr.details.labels.selfAssignment}>',
    '<DetailSection className="tos-dq-details-selfassign-v1" direction={isAr ? "rtl" : "ltr"} icon={UserPlus} title={tr.details.labels.selfAssignment}>',
    "Self assignment section hook",
)

old_designer_select = '<label className="block text-xs font-black text-slate-500">{tr.details.labels.designer}<Field as="select" value={draft.assigneeId} onChange={(event) => setDraft((current) => ({ ...current, assigneeId: event.target.value }))} className="mt-2"><option value="">{tr.details.labels.notAssigned}</option>{designers.map((designer) => <option key={designer.id} value={designer.id}>{designerLabel(designer, tr.common.designer)} · {capacityUnitLabel(mode, designer.usedCapacity || 0, tr)}/{capacityUnitLabel(mode, designer.capacityLimit, tr)} · {designer.capacityPercent || 0}%</option>)}</Field></label>'
new_designer_select = '''<label className="block text-xs font-black text-slate-500">
                  <span>{tr.details.labels.designer}</span>
                  <div className="mt-2">
                    <PremiumMenu
                      value={draft.assigneeId}
                      onChange={(value) => setDraft((current) => ({ ...current, assigneeId: value }))}
                      ariaLabel={tr.details.labels.designer}
                      options={[
                        { value: "", label: tr.details.labels.notAssigned },
                        ...designers.map((designer) => ({
                          value: designer.id,
                          label: `${designerLabel(designer, tr.common.designer)} · ${capacityUnitLabel(mode, designer.usedCapacity || 0, tr)}/${capacityUnitLabel(mode, designer.capacityLimit, tr)} · ${designer.capacityPercent || 0}%`,
                        })),
                      ]}
                    />
                  </div>
                </label>'''
updated = replace_once(updated, old_designer_select, new_designer_select, "Designer premium menu")

old_priority = '<Field as="select" value={draft.priority} onChange={(event) => setDraft((current) => ({ ...current, priority: event.target.value }))} className="mt-1">{Object.entries(tr.priority).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</Field>'
new_priority = '<div className="mt-1"><PremiumMenu value={draft.priority} onChange={(value) => setDraft((current) => ({ ...current, priority: value }))} ariaLabel={tr.details.labels.priority} options={Object.entries(tr.priority).map(([value, label]) => ({ value, label }))} /></div>'
updated = replace_once(updated, old_priority, new_priority, "Priority premium menu")

updated = replace_once(
    updated,
    '<div className={cn("mt-3 rounded-xl border px-3 py-2 text-xs font-black", projectedCapacity.percent > 100 ? "border-red-200 bg-red-50 text-red-700" : projectedCapacity.percent > 90 ? "border-orange-200 bg-orange-50 text-orange-700" : "border-emerald-200 bg-emerald-50 text-emerald-700")}>{tr.details.labels.expectedLoad}: {capacityUnitLabel(mode, projectedCapacity.used, tr)} / {capacityUnitLabel(mode, projectedCapacity.limit, tr)} ({projectedCapacity.percent}%)</div>',
    '<div style={{ "--dq-capacity-percent": `${Math.min(100, projectedCapacity.percent)}%` }} className={cn("tos-dq-projected-capacity-v1 mt-3 rounded-xl border px-3 py-2 text-xs font-black", projectedCapacity.percent > 100 ? "border-red-200 bg-red-50 text-red-700" : projectedCapacity.percent > 90 ? "border-orange-200 bg-orange-50 text-orange-700" : "border-emerald-200 bg-emerald-50 text-emerald-700")}>{tr.details.labels.expectedLoad}: {capacityUnitLabel(mode, projectedCapacity.used, tr)} / {capacityUnitLabel(mode, projectedCapacity.limit, tr)} ({projectedCapacity.percent}%)</div>',
    "Projected capacity treatment",
)
updated = replace_once(
    updated,
    '<Button type="button" className="mt-3 w-full justify-center" onClick={onSave} disabled={saving}>',
    '<Button type="button" className="tos-dq-assignment-cta-v1 mt-4 w-full justify-center" onClick={onSave} disabled={saving}>',
    "Assignment CTA hook",
)

hero_chips = '''                  <span className="rounded-lg border border-amber-200 bg-white px-2.5 py-1.5 text-[11px] font-black text-slate-700 dark:border-amber-400/20 dark:bg-zinc-900 dark:text-zinc-200">{tr.details.labels.designType}: {getDesignTypeLabel(task.designRequest?.designType, lang, task.designRequest) || "—"}</span>
                  <span className="rounded-lg border border-amber-200 bg-white px-2.5 py-1.5 text-[11px] font-black text-slate-700 dark:border-amber-400/20 dark:bg-zinc-900 dark:text-zinc-200">{tr.details.labels.platform}: {getDesignPlatformLabel(task.designRequest?.platform, lang, task.designRequest) || "—"}</span>'''
hero_chips_new = hero_chips + '\n                  <Badge tone={PRIORITY_TONES[task.priority] || "neutral"}>{tr.priority[task.priority] || task.priority}</Badge>'
updated = replace_once(updated, hero_chips, hero_chips_new, "Hero priority chip")

v1_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V1
   Premium operational detail workspace. Visual hierarchy only;
   request assignment, attachment and lifecycle logic is unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v1-runtime: 1; }

.tos-dq-details-flagship-v1 {
  --dq-detail-champagne: #c99a3d;
  --dq-detail-champagne-soft: rgba(201,154,61,.13);
  --dq-detail-ink: #181713;
  --dq-detail-muted: #746f65;
  position: relative;
  isolation: isolate;
  border-color: rgba(178,135,53,.20) !important;
  background:
    radial-gradient(circle at 7% 0%, rgba(224,193,121,.16), transparent 25%),
    radial-gradient(circle at 96% 8%, rgba(255,255,255,.92), transparent 28%),
    linear-gradient(145deg, #f8f4eb 0%, #f4f0e7 48%, #f8f6f0 100%) !important;
  box-shadow: 0 24px 70px rgba(72,55,24,.09), inset 0 1px 0 rgba(255,255,255,.92) !important;
}

.tos-dq-details-hero-v1 {
  min-height: 178px;
  border-radius: 28px !important;
  border-color: rgba(184,137,53,.28) !important;
  background:
    radial-gradient(circle at 10% 0%, rgba(226,194,122,.19), transparent 34%),
    linear-gradient(135deg, rgba(255,254,250,.995), rgba(249,244,232,.98)) !important;
  box-shadow: 0 18px 44px rgba(71,50,15,.08), inset 0 1px 0 rgba(255,255,255,.98) !important;
  padding: 24px 26px !important;
}

.tos-dq-details-hero-v1::after {
  content: "";
  position: absolute;
  inset-inline: 26px;
  top: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(201,154,61,.62), transparent);
  pointer-events: none;
}

.tos-dq-details-hero-v1 h2 {
  max-width: 880px;
  font-size: clamp(1.65rem, 2.2vw, 2.35rem) !important;
  line-height: 1.18 !important;
  letter-spacing: -.025em;
}

.tos-dq-details-hero-v1 [class*="rounded-lg"][class*="border-amber"] {
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px !important;
  border-color: rgba(184,137,53,.22) !important;
  background: rgba(255,255,255,.74) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.88);
}

.tos-dq-details-actions-v1 {
  border-radius: 20px !important;
  border-color: rgba(184,137,53,.20) !important;
  background: rgba(255,255,255,.66) !important;
  backdrop-filter: blur(16px);
  box-shadow: 0 12px 30px rgba(67,48,17,.06), inset 0 1px 0 rgba(255,255,255,.92) !important;
}

.tos-dq-details-actions-v1 button {
  min-height: 38px;
  border-radius: 12px !important;
  justify-content: flex-start;
  font-weight: 850;
}

.tos-dq-details-metrics-v1 {
  gap: 0;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.tos-dq-detail-metric-v1 {
  margin: 0 4px;
  min-height: 76px;
  border: 1px solid rgba(112,92,57,.11) !important;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255,255,255,.94), rgba(250,247,240,.88));
  box-shadow: 0 9px 24px rgba(62,49,26,.045), inset 0 1px 0 rgba(255,255,255,.96);
}

.tos-dq-detail-metric-v1 > span:first-child {
  border-radius: 14px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.75);
}

.tos-dq-details-layout-v1 {
  gap: 16px !important;
}

.tos-dq-detail-section-v1 {
  border-radius: 24px !important;
  border-color: rgba(111,92,58,.12) !important;
  background: rgba(255,255,255,.88) !important;
  box-shadow: 0 16px 40px rgba(66,51,27,.055), inset 0 1px 0 rgba(255,255,255,.95) !important;
  backdrop-filter: blur(10px);
}

.tos-dq-detail-section-v1 > div:first-child {
  min-height: 48px;
  border-color: rgba(184,137,53,.14) !important;
  background: linear-gradient(180deg, rgba(253,250,244,.90), rgba(250,246,237,.58));
  padding-inline: 17px !important;
  font-size: .82rem !important;
  letter-spacing: -.01em;
}

.tos-dq-detail-section-v1 > div:last-child {
  padding: 16px !important;
}

.tos-dq-spec-row-v1 {
  border-color: rgba(94,81,59,.10) !important;
  background: linear-gradient(180deg, rgba(250,249,246,.96), rgba(247,245,240,.78)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.85);
}

.tos-dq-spec-meta-v1 {
  min-height: 70px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.tos-dq-spec-brief-v1,
.tos-dq-spec-notes-v1 {
  padding: 15px 16px !important;
}

.tos-dq-spec-copy-v1 {
  padding: 18px 18px 20px !important;
  border-color: rgba(184,137,53,.19) !important;
  background:
    linear-gradient(180deg, rgba(255,254,250,.98), rgba(250,247,240,.92)) !important;
  box-shadow: inset 3px 0 0 rgba(201,154,61,.30), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

[dir="rtl"] .tos-dq-spec-copy-v1 {
  box-shadow: inset -3px 0 0 rgba(201,154,61,.30), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

.tos-dq-spec-copy-v1 > div:last-child {
  margin-top: 10px !important;
  font-size: .95rem !important;
  line-height: 1.95 !important;
  font-weight: 750 !important;
  color: #39352f !important;
}

.tos-dq-details-attachments-v1 [class*="border-dashed"] {
  min-height: 160px;
  display: grid;
  place-items: center;
  border-radius: 18px !important;
  background:
    radial-gradient(circle at 50% 0%, rgba(221,187,108,.08), transparent 42%),
    rgba(251,249,244,.55);
}

.tos-dq-details-activity-v1 .tos-dq-activity-item-v1 {
  min-height: 54px;
  padding-block: 4px 10px;
  border-color: rgba(201,154,61,.20) !important;
}

.tos-dq-details-activity-v1 .tos-dq-activity-item-v1 > span {
  box-shadow: 0 0 0 4px rgba(201,154,61,.07);
}

.tos-dq-details-rail-v1 {
  align-self: start;
}

.tos-dq-details-assignment-v1 {
  border-color: rgba(184,137,53,.24) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(221,187,108,.11), transparent 34%),
    rgba(255,255,255,.92) !important;
  box-shadow: 0 20px 44px rgba(63,46,16,.085), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

.tos-dq-details-assignment-v1 input,
.tos-dq-details-assignment-v1 select {
  min-height: 42px;
  border-radius: 13px !important;
}

.tos-dq-projected-capacity-v1 {
  position: relative;
  overflow: hidden;
  padding-bottom: 13px !important;
}

.tos-dq-projected-capacity-v1::after {
  content: "";
  position: absolute;
  inset-inline-start: 10px;
  bottom: 6px;
  width: var(--dq-capacity-percent, 0%);
  max-width: calc(100% - 20px);
  height: 3px;
  border-radius: 999px;
  background: currentColor;
  opacity: .55;
}

.tos-dq-assignment-cta-v1 {
  min-height: 44px !important;
  border: 1px solid rgba(184,137,53,.58) !important;
  background: linear-gradient(135deg, #e1b85f, #c89533) !important;
  color: #17140e !important;
  box-shadow: 0 12px 26px rgba(179,128,37,.18), inset 0 1px 0 rgba(255,255,255,.38) !important;
}

.tos-dq-assignment-cta-v1:hover {
  filter: brightness(1.025);
  transform: translateY(-1px);
}

html.dark .tos-dq-details-flagship-v1 {
  --dq-detail-champagne: #d7b264;
  --dq-detail-champagne-soft: rgba(215,178,100,.10);
  --dq-detail-ink: #f1efe9;
  --dq-detail-muted: #9298a2;
  border-color: rgba(215,178,100,.14) !important;
  background:
    radial-gradient(circle at 9% 0%, rgba(215,178,100,.08), transparent 24%),
    radial-gradient(circle at 92% 8%, rgba(113,95,58,.045), transparent 24%),
    linear-gradient(145deg, #0a0c0f 0%, #0e1014 52%, #090b0e 100%) !important;
  box-shadow: 0 26px 80px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark .tos-dq-details-hero-v1 {
  border-color: rgba(215,178,100,.19) !important;
  background:
    radial-gradient(circle at 12% 0%, rgba(215,178,100,.10), transparent 36%),
    linear-gradient(135deg, #15171b, #101216) !important;
  box-shadow: 0 22px 50px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.028) !important;
}

html.dark .tos-dq-details-hero-v1 [class*="rounded-lg"][class*="border-amber"] {
  border-color: rgba(215,178,100,.16) !important;
  background: rgba(255,255,255,.028) !important;
  color: #e6e2d8 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}

html.dark .tos-dq-details-actions-v1 {
  border-color: rgba(215,178,100,.16) !important;
  background: rgba(15,17,21,.80) !important;
  box-shadow: 0 16px 36px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.024) !important;
}

html.dark .tos-dq-detail-metric-v1 {
  border-color: rgba(255,255,255,.075) !important;
  background: linear-gradient(180deg, #15181d, #111419) !important;
  box-shadow: 0 12px 28px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.025);
}

html.dark .tos-dq-detail-section-v1 {
  border-color: rgba(255,255,255,.075) !important;
  background: linear-gradient(180deg, rgba(20,23,28,.985), rgba(14,17,21,.985)) !important;
  box-shadow: 0 20px 44px rgba(0,0,0,.27), inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark .tos-dq-detail-section-v1 > div:first-child {
  border-color: rgba(255,255,255,.065) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.026), rgba(255,255,255,.012));
}

html.dark .tos-dq-spec-row-v1 {
  border-color: rgba(255,255,255,.065) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.026), rgba(255,255,255,.016)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.018);
}

html.dark .tos-dq-spec-copy-v1 {
  border-color: rgba(215,178,100,.16) !important;
  background:
    radial-gradient(circle at 8% 0%, rgba(215,178,100,.045), transparent 32%),
    linear-gradient(180deg, #15181c, #111418) !important;
}

html.dark .tos-dq-spec-copy-v1 > div:last-child {
  color: #d9d8d3 !important;
}

html.dark .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  border-color: rgba(215,178,100,.16) !important;
  background: rgba(255,255,255,.012) !important;
}

html.dark .tos-dq-details-assignment-v1 {
  border-color: rgba(215,178,100,.18) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(215,178,100,.075), transparent 36%),
    linear-gradient(180deg, #17191e, #111419) !important;
  box-shadow: 0 22px 48px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.025) !important;
}

html.dark .tos-dq-details-assignment-v1 input,
html.dark .tos-dq-details-assignment-v1 select {
  border-color: rgba(255,255,255,.10) !important;
  background: #0d0f12 !important;
  color: #f1efe9 !important;
}

html.dark .tos-dq-details-selfassign-v1 {
  border-color: rgba(16,185,129,.14) !important;
}

@media (min-width: 1280px) {
  .tos-dq-details-actions-v1 {
    width: 300px !important;
  }
  .tos-dq-details-rail-v1 {
    top: 14px !important;
  }
}

@media (max-width: 1279px) {
  .tos-dq-details-layout-v1 {
    grid-template-columns: minmax(0,1fr) !important;
  }
  .tos-dq-details-rail-v1 {
    position: static !important;
  }
}

@media (max-width: 639px) {
  .tos-dq-details-hero-v1 {
    padding: 18px !important;
    min-height: auto;
  }
  .tos-dq-detail-metric-v1 {
    margin: 3px 0;
  }
  .tos-dq-spec-copy-v1 > div:last-child {
    font-size: .9rem !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  .tos-dq-details-flagship-v1 *,
  .tos-dq-details-flagship-v1 *::before,
  .tos-dq-details-flagship-v1 *::after {
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
  }
}
'''

v1_css = "\n".join(line.rstrip() for line in v1_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v1_css

for owned_name, owned_text in (
    ("updated DesignQueuePage", updated),
    ("V1 CSS", v1_css),
):
    if any(line.endswith(" ") or line.endswith("\t") for line in owned_text.splitlines()):
        fail(f"{owned_name} contains trailing whitespace")

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()

    if source_dq.count(DETAILS_HOOK) != 1:
        raise RuntimeError("Design Request Details V1 source hook missing or duplicated")
    if source_css.count(V1_MARKER) != 1:
        raise RuntimeError("Design Request Details V1 CSS marker missing or duplicated")
    if source_dq.count("<PremiumMenu") < original_dq.count("<PremiumMenu") + 2:
        raise RuntimeError("premium assignment menus were not added")
    for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10"):
        if required not in source_dq:
            raise RuntimeError(f"required Design Queue baseline marker not preserved: {required}")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V1_MARKER.encode())
    dist_hook = tree_count(DIST, b"data-dq-details-flagship")
    if dist_marker < 1:
        raise RuntimeError("Design Request Details V1 CSS marker missing from dist")
    if dist_hook < 1:
        raise RuntimeError("Design Request Details V1 runtime hook missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v1.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v1.backup-{stamp}"
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

    live_marker = tree_count(LIVE, V1_MARKER.encode())
    live_hook = tree_count(LIVE, b"data-dq-details-flagship")
    if live_marker < 1 or live_hook < 1:
        raise RuntimeError("Design Request Details V1 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V1_RUNTIME=YES")
    print("PREMIUM_DETAIL_WORKSPACE=YES")
    print("EXECUTIVE_HERO_REFINED=YES")
    print("METADATA_STRIP_REFINED=YES")
    print("SPECIFICATIONS_REFINED=YES")
    print("REQUIRED_COPY_REFINED=YES")
    print("ATTACHMENTS_REFINED=YES")
    print("ACTIVITY_TIMELINE_REFINED=YES")
    print("STICKY_ASSIGNMENT_RAIL=YES")
    print("ASSIGNMENT_MENUS_PREMIUM=YES")
    print("LIGHT_FLAGSHIP_THEME=YES")
    print("DARK_FLAGSHIP_THEME=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V1_RUNTIME_COUNT={source_css.count(V1_MARKER)}")
    print(f"SOURCE_DETAILS_HOOK_COUNT={source_dq.count(DETAILS_HOOK)}")
    print(f"DIST_V1_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_DETAILS_HOOK_COUNT={dist_hook}")
    print(f"LIVE_V1_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_DETAILS_HOOK_COUNT={live_hook}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v1.failed.{int(time.time())}"
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
    print("V1_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
