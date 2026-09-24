#!/usr/bin/env python3
# TOS-MY-WORKSPACE-EXECUTIVE-LUXURY-V1
# High-end visual polish for My Workspace only.
# Frontend-only. Preserves KPI motion, premium filters, DnD, sticky scrollbar, refresh logic.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
MARKER = "TOS_MY_WORKSPACE_EXECUTIVE_LUXURY_V1"

REQUIRED = [
    "TOS_MY_WORKSPACE_SPACIOUS_PREMIUM_V1",
    "TOS_MY_WORKSPACE_KPI_LIVE_MOTION_V1",
    "TOS_MY_WORKSPACE_PREMIUM_FILTERS_V1",
    "TOS_MY_WORKSPACE_TRELLO_DRAG_DROP_V1",
    "TOS_MY_WORKSPACE_STICKY_SCROLLBAR_V1_1",
]

def die(message):
    print(f"PATCH=FAIL\nERROR={message}")
    sys.exit(1)

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        die(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)

if not TARGET.exists():
    die(f"missing file: {TARGET}")

source = TARGET.read_text(encoding="utf-8")

if MARKER in source:
    print("PATCH=SKIP_ALREADY_APPLIED")
    sys.exit(0)

for required in REQUIRED:
    if required not in source:
        die(f"required marker missing: {required}")

backup = TARGET.with_name(
    TARGET.name + f".bak-executive-luxury-v1-{int(time.time())}"
)
shutil.copy2(TARGET, backup)

helper_anchor = '''function getTaskProjectName(task, isAr = false) {
  return task?.project?.name || task?.projectName || (isAr ? "مهمة شخصية" : "Personal task");
}
'''

helper_block = '''function getTaskProjectName(task, isAr = false) {
  return task?.project?.name || task?.projectName || (isAr ? "مهمة شخصية" : "Personal task");
}

// TOS_MY_WORKSPACE_EXECUTIVE_LUXURY_V1
function workspaceColumnIcon(columnId) {
  return {
    backlog: Layers3,
    todo: ArrowRight,
    progress: Sparkles,
    waiting_client: TimerReset,
    review: ClipboardCheck,
    done: CheckCircle2,
  }[columnId] || ListChecks;
}

function workspaceColumnLuxury(columnId) {
  const styles = {
    backlog: {
      panel: "bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(255,255,255,0.9))] dark:bg-[linear-gradient(180deg,rgba(30,41,59,0.34),rgba(9,9,11,0.84))]",
      header: "bg-[linear-gradient(135deg,rgba(15,23,42,0.98),rgba(51,65,85,0.88))]",
      icon: "border-white/15 bg-white/10 text-sky-200 shadow-[0_0_22px_rgba(125,211,252,0.18)]",
      title: "text-white",
      meta: "text-slate-300",
    },
    todo: {
      panel: "bg-[linear-gradient(180deg,rgba(239,246,255,0.72),rgba(255,255,255,0.92))] dark:bg-[linear-gradient(180deg,rgba(30,64,175,0.14),rgba(9,9,11,0.84))]",
      header: "bg-[linear-gradient(135deg,rgba(37,99,235,0.96),rgba(14,165,233,0.78))]",
      icon: "border-white/20 bg-white/14 text-white shadow-[0_0_24px_rgba(56,189,248,0.34)]",
      title: "text-white",
      meta: "text-blue-50/90",
    },
    progress: {
      panel: "bg-[linear-gradient(180deg,rgba(245,243,255,0.72),rgba(255,255,255,0.92))] dark:bg-[linear-gradient(180deg,rgba(109,40,217,0.15),rgba(9,9,11,0.84))]",
      header: "bg-[linear-gradient(135deg,rgba(109,40,217,0.96),rgba(168,85,247,0.8))]",
      icon: "border-white/20 bg-white/14 text-white shadow-[0_0_24px_rgba(192,132,252,0.34)]",
      title: "text-white",
      meta: "text-violet-50/90",
    },
    waiting_client: {
      panel: "bg-[linear-gradient(180deg,rgba(255,247,237,0.84),rgba(255,255,255,0.94))] dark:bg-[linear-gradient(180deg,rgba(180,83,9,0.15),rgba(9,9,11,0.84))]",
      header: "bg-[linear-gradient(135deg,rgba(180,83,9,0.98),rgba(245,158,11,0.82))]",
      icon: "border-white/20 bg-white/14 text-white shadow-[0_0_24px_rgba(251,191,36,0.36)]",
      title: "text-white",
      meta: "text-amber-50/90",
    },
    review: {
      panel: "bg-[linear-gradient(180deg,rgba(255,241,242,0.74),rgba(255,255,255,0.94))] dark:bg-[linear-gradient(180deg,rgba(190,24,93,0.14),rgba(9,9,11,0.84))]",
      header: "bg-[linear-gradient(135deg,rgba(190,24,93,0.96),rgba(244,63,94,0.8))]",
      icon: "border-white/20 bg-white/14 text-white shadow-[0_0_24px_rgba(251,113,133,0.34)]",
      title: "text-white",
      meta: "text-rose-50/90",
    },
    done: {
      panel: "bg-[linear-gradient(180deg,rgba(236,253,245,0.72),rgba(255,255,255,0.94))] dark:bg-[linear-gradient(180deg,rgba(5,150,105,0.14),rgba(9,9,11,0.84))]",
      header: "bg-[linear-gradient(135deg,rgba(5,150,105,0.96),rgba(16,185,129,0.78))]",
      icon: "border-white/20 bg-white/14 text-white shadow-[0_0_24px_rgba(52,211,153,0.34)]",
      title: "text-white",
      meta: "text-emerald-50/90",
    },
  };
  return styles[columnId] || styles.backlog;
}
'''

source = replace_once(source, helper_anchor, helper_block, "luxury helpers")

source = replace_once(
    source,
    '''className={`group relative min-h-[118px] overflow-hidden rounded-[22px] border border-zinc-100 bg-white/95 px-4 py-3.5 shadow-[0_8px_26px_rgba(15,23,42,0.045)] transition-[transform,box-shadow,border-color,opacity] duration-500 hover:-translate-y-1 hover:border-zinc-200 hover:shadow-[0_18px_44px_rgba(15,23,42,0.09)] dark:border-white/10 dark:bg-zinc-950/90 ${''',
    '''className={`group relative min-h-[126px] overflow-hidden rounded-[24px] border border-white/80 bg-[linear-gradient(145deg,rgba(255,255,255,0.98),rgba(248,250,252,0.92))] px-4.5 py-4 shadow-[0_12px_34px_rgba(15,23,42,0.065),inset_0_1px_0_rgba(255,255,255,0.9)] ring-1 ring-black/[0.025] backdrop-blur-xl transition-[transform,box-shadow,border-color,opacity] duration-500 hover:-translate-y-1.5 hover:border-amber-200/70 hover:shadow-[0_24px_60px_rgba(15,23,42,0.12),0_8px_26px_rgba(217,119,6,0.08)] dark:border-white/10 dark:bg-[linear-gradient(145deg,rgba(24,24,27,0.96),rgba(9,9,11,0.9))] dark:ring-white/5 ${''',
    "kpi luxury card",
)

source = replace_once(
    source,
    '''      <div className="relative flex items-center gap-3.5">''',
    '''      <div className="pointer-events-none absolute inset-x-5 top-0 h-px bg-[linear-gradient(90deg,transparent,rgba(217,119,6,0.38),transparent)]" />
      <div className="pointer-events-none absolute end-3 top-3 grid h-7 w-7 place-items-center rounded-full border border-white/70 bg-white/65 text-amber-500 shadow-sm backdrop-blur dark:border-white/10 dark:bg-white/5 dark:text-amber-300">
        <Sparkles size={12} strokeWidth={2.3} />
      </div>
      <div className="relative flex items-center gap-3.5">''',
    "kpi luxury sparkle",
)

source = replace_once(
    source,
    '''<div className="tos-my-workspace mx-auto w-full max-w-[1800px]" dir={isAr ? "rtl" : "ltr"}>''',
    '''<div
      data-tos-my-workspace-executive-luxury="v1"
      className="tos-my-workspace relative isolate mx-auto w-full max-w-[1800px]"
      dir={isAr ? "rtl" : "ltr"}
    >
      <div aria-hidden="true" className="pointer-events-none absolute -inset-x-2 -top-4 -z-10 h-64 overflow-hidden rounded-[34px]">
        <div className="absolute -start-16 -top-24 h-64 w-64 rounded-full bg-amber-200/18 blur-3xl motion-safe:animate-[pulse_5s_ease-in-out_infinite] motion-reduce:animate-none dark:bg-amber-500/8" />
        <div className="absolute end-10 top-0 h-44 w-44 rounded-full bg-blue-200/12 blur-3xl motion-safe:animate-[pulse_6s_ease-in-out_infinite] motion-reduce:animate-none dark:bg-blue-500/8" />
      </div>''',
    "workspace shell",
)

source = replace_once(
    source,
    '''<div className={`mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5 ${isAr ? "direction-rtl" : "direction-ltr"}`}>''',
    '''<div className={`mb-5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 xl:grid-cols-5 ${isAr ? "direction-rtl" : "direction-ltr"}`}>''',
    "kpi grid spacing",
)

source = replace_once(
    source,
    '''<section className="rounded-[24px] border border-zinc-100 bg-white/[0.96] p-4 shadow-[0_14px_44px_rgba(15,23,42,0.06)] dark:border-white/10 dark:bg-zinc-950/95">''',
    '''<section className="relative overflow-hidden rounded-[30px] border border-white/80 bg-[linear-gradient(145deg,rgba(255,255,255,0.985),rgba(250,250,249,0.94))] p-4.5 shadow-[0_22px_70px_rgba(15,23,42,0.085),inset_0_1px_0_rgba(255,255,255,0.95)] ring-1 ring-black/[0.025] backdrop-blur-xl dark:border-white/10 dark:bg-[linear-gradient(145deg,rgba(24,24,27,0.97),rgba(9,9,11,0.94))] dark:ring-white/5">
      <div aria-hidden="true" className="pointer-events-none absolute -end-24 -top-28 h-72 w-72 rounded-full border border-amber-200/20 bg-amber-100/10 blur-[1px] dark:border-amber-400/10 dark:bg-amber-500/5" />
      <div aria-hidden="true" className="pointer-events-none absolute end-10 top-2 h-24 w-72 -rotate-6 rounded-[100%] border-t border-amber-300/25 opacity-70 dark:border-amber-400/15" />''',
    "workspace executive panel",
)

source = replace_once(
    source,
    '''<div className="flex flex-col gap-3 border-b border-zinc-100 pb-4 dark:border-white/10 sm:flex-row sm:items-start sm:justify-between">''',
    '''<div className="relative z-10 flex flex-col gap-3 border-b border-zinc-100/80 pb-5 dark:border-white/10 sm:flex-row sm:items-start sm:justify-between">''',
    "workspace header layer",
)

source = replace_once(
    source,
    '''className="mb-2 inline-flex rounded-full border border-amber-100 bg-amber-50 px-3 py-1 text-[11px] font-black text-amber-700 dark:border-amber-400/20 dark:bg-amber-500/10 dark:text-amber-200"''',
    '''className="mb-2 inline-flex items-center rounded-full border border-amber-200/80 bg-[linear-gradient(135deg,rgba(255,251,235,0.98),rgba(254,243,199,0.82))] px-3.5 py-1.5 text-[10px] font-black uppercase tracking-[0.12em] text-amber-800 shadow-[0_5px_16px_rgba(217,119,6,0.10)] dark:border-amber-400/20 dark:bg-amber-500/10 dark:text-amber-200"''',
    "workspace pill",
)

source = replace_once(
    source,
    '''<h2 className="text-xl font-black tracking-tight text-zinc-950 dark:text-white">''',
    '''<h2 className="text-[24px] font-black tracking-[-0.035em] text-zinc-950 dark:text-white">''',
    "workspace title",
)

source = replace_once(
    source,
    '''className="inline-flex items-center justify-center gap-2 rounded-2xl bg-zinc-950 px-4 py-2.5 text-xs font-black text-white transition hover:bg-amber-600 dark:bg-amber-500 dark:text-zinc-950"''',
    '''className="group inline-flex items-center justify-center gap-2 rounded-[16px] border border-zinc-900 bg-[linear-gradient(135deg,#18181b,#09090b)] px-5 py-3 text-xs font-black text-white shadow-[0_10px_28px_rgba(9,9,11,0.22),0_0_0_1px_rgba(255,255,255,0.04)_inset] transition-all hover:-translate-y-0.5 hover:border-amber-500 hover:shadow-[0_14px_34px_rgba(9,9,11,0.28),0_0_24px_rgba(217,119,6,0.16)] dark:border-amber-400/25 dark:bg-[linear-gradient(135deg,#f59e0b,#d97706)] dark:text-zinc-950"''',
    "new task luxury button",
)

source = replace_once(
    source,
    '''className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 bg-white px-4 py-2.5 text-xs font-black text-zinc-700 transition hover:bg-zinc-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100"''',
    '''className="inline-flex items-center justify-center gap-2 rounded-[16px] border border-zinc-200/80 bg-white/88 px-4.5 py-3 text-xs font-black text-zinc-700 shadow-[0_8px_22px_rgba(15,23,42,0.06)] backdrop-blur transition-all hover:-translate-y-0.5 hover:border-amber-200 hover:bg-amber-50/40 hover:text-amber-800 dark:border-white/10 dark:bg-zinc-900/80 dark:text-zinc-100 dark:hover:border-amber-400/25"''',
    "refresh luxury button",
)

source = replace_once(
    source,
    '''className="mt-4 rounded-[22px] border border-zinc-200/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.98),rgba(250,250,250,0.92))] p-2.5 shadow-[0_10px_30px_rgba(15,23,42,0.045)] ring-1 ring-white/70 dark:border-white/10 dark:bg-[linear-gradient(135deg,rgba(24,24,27,0.96),rgba(9,9,11,0.92))] dark:ring-white/5"''',
    '''className="relative z-20 mt-4 rounded-[24px] border border-white/90 bg-[linear-gradient(135deg,rgba(255,255,255,0.98),rgba(250,250,249,0.91))] p-2.5 shadow-[0_14px_38px_rgba(15,23,42,0.065),inset_0_1px_0_rgba(255,255,255,0.9)] ring-1 ring-black/[0.025] backdrop-blur-xl dark:border-white/10 dark:bg-[linear-gradient(135deg,rgba(24,24,27,0.96),rgba(9,9,11,0.92))] dark:ring-white/5"''',
    "filter shell luxury",
)

source = replace_once(
    source,
    '''              const manualDragEnabled = !filters.sort;
              return (''',
    '''              const manualDragEnabled = !filters.sort;
              const luxuryColumn = workspaceColumnLuxury(column.id);
              const ColumnIcon = workspaceColumnIcon(column.id);
              return (''',
    "column luxury vars",
)

source = replace_once(
    source,
    '''className={`w-[340px] shrink-0 overflow-hidden rounded-[22px] border bg-white/[0.82] shadow-sm transition-[border-color,box-shadow,transform,background-color] duration-150 2xl:w-[360px] dark:bg-zinc-900/70 dark:shadow-black/20 ${''',
    '''className={`w-[340px] shrink-0 overflow-hidden rounded-[26px] border border-white/80 shadow-[0_16px_42px_rgba(15,23,42,0.075),inset_0_1px_0_rgba(255,255,255,0.8)] ring-1 ring-black/[0.02] backdrop-blur-md transition-[border-color,box-shadow,transform,background-color] duration-200 2xl:w-[360px] dark:border-white/10 dark:shadow-black/25 ${luxuryColumn.panel} ${''',
    "column panel luxury",
)

source = replace_once(
    source,
    '''                  <div className={`h-1.5 ${column.topClass}`} />
                  <header className="flex items-center justify-between gap-3 px-4 py-3.5">
                    <div>
                      <h3 className={`text-[17px] font-black tracking-tight ${column.toneClass.split(" ").filter((part) => part.startsWith("text-") || part.startsWith("dark:text-")).join(" ")}`}>{isAr ? column.labelAr : column.labelEn}</h3>
                      <p className="mt-1 text-[11px] font-bold text-slate-400 dark:text-zinc-500">
                        {manualDragEnabled
                          ? (isAr ? "اسحب الكروت لنقلها أو ترتيبها" : "Drag cards to move or reorder")
                          : (isAr ? "ألغِ ترتيب التاريخ لتفعيل السحب" : "Clear date sorting to enable drag")}
                      </p>
                    </div>
                    <span className={`grid h-9 min-w-9 place-items-center rounded-full px-2 text-xs font-black ring-1 ${column.pillClass}`}>{columnTasks.length}</span>
                  </header>''',
    '''                  <div className={`h-1 ${column.topClass}`} />
                  <header className={`relative overflow-hidden px-4 py-4 ${luxuryColumn.header}`}>
                    <div aria-hidden="true" className="pointer-events-none absolute -end-8 -top-10 h-24 w-24 rounded-full border border-white/10 bg-white/5 blur-[0.5px]" />
                    <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-white/10" />
                    <div className="relative flex items-center justify-between gap-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-[13px] border backdrop-blur ${luxuryColumn.icon}`}>
                          <ColumnIcon size={18} strokeWidth={2.25} />
                        </span>
                        <div className="min-w-0">
                          <h3 className={`truncate text-[16px] font-black tracking-tight ${luxuryColumn.title}`}>{isAr ? column.labelAr : column.labelEn}</h3>
                          <p className={`mt-1 truncate text-[10px] font-bold ${luxuryColumn.meta}`}>
                            {manualDragEnabled
                              ? (isAr ? "اسحب الكروت لنقلها أو ترتيبها" : "Drag cards to move or reorder")
                              : (isAr ? "ألغِ ترتيب التاريخ لتفعيل السحب" : "Clear date sorting to enable drag")}
                          </p>
                        </div>
                      </div>
                      <span className="grid h-9 min-w-9 shrink-0 place-items-center rounded-full border border-white/20 bg-white/90 px-2 text-xs font-black text-zinc-900 shadow-[0_5px_16px_rgba(15,23,42,0.16)] backdrop-blur">
                        {columnTasks.length}
                      </span>
                    </div>
                  </header>''',
    "luxury column header",
)

source = replace_once(
    source,
    '''className={`group relative rounded-[18px] border bg-white px-3.5 py-3.5 shadow-sm transition-[border-color,box-shadow,transform,opacity] duration-150 dark:bg-zinc-950 dark:shadow-black/20 ${''',
    '''className={`group relative rounded-[20px] border bg-white/96 px-3.5 py-3.5 shadow-[0_8px_22px_rgba(15,23,42,0.055),inset_0_1px_0_rgba(255,255,255,0.88)] ring-1 ring-black/[0.015] backdrop-blur-sm transition-[border-color,box-shadow,transform,opacity] duration-200 dark:bg-zinc-950/96 dark:shadow-black/25 dark:ring-white/[0.03] ${''',
    "task card luxury",
)

TARGET.write_text(source, encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-MY-WORKSPACE-EXECUTIVE-LUXURY-V1")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("EXECUTIVE_LUXURY_SHELL=ACTIVE")
print("KPI_LUXURY_SURFACE=ACTIVE")
print("KPI_LIVE_MOTION=PRESERVED")
print("WORKSPACE_GOLD_ATMOSPHERE=ACTIVE")
print("PREMIUM_FILTERS=PRESERVED")
print("KANBAN_GRADIENT_HEADERS=ACTIVE")
print("KANBAN_STATUS_ICONS=ACTIVE")
print("TASK_CARD_POLISH=ACTIVE")
print("DRAG_DROP=PRESERVED")
print("STICKY_SCROLLBAR=PRESERVED")
print("REFRESH_LOGIC=PRESERVED")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
print("DEPENDENCIES_ADDED=NO")
