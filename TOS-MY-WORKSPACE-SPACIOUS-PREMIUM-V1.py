#!/usr/bin/env python3
# TOS-MY-WORKSPACE-SPACIOUS-PREMIUM-V1
# Spacious premium My Workspace board + strong KPI motion.
# Frontend-only. Preserves Trello drag/drop, APIs, permissions, Waiting Client gate.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
MARKER = "TOS_MY_WORKSPACE_SPACIOUS_PREMIUM_V1"
REQUIRED_DND_MARKER = "TOS_MY_WORKSPACE_TRELLO_DRAG_DROP_V1"

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

if REQUIRED_DND_MARKER not in source:
    die("required My Workspace Trello drag/drop V1 marker is missing")

backup = TARGET.with_name(
    TARGET.name + f".bak-spacious-premium-v1-{int(time.time())}"
)
shutil.copy2(TARGET, backup)

old_stat = r'''function WorkspaceMiniStat({ label, value, note, tone = "zinc", percent = 0 }) {
  const palette = {
    zinc: { ring: "#27272a", soft: "#f4f4f5", textClass: "text-zinc-950 dark:text-white", noteClass: "text-zinc-600 dark:text-zinc-300" },
    emerald: { ring: "#059669", soft: "#d1fae5", textClass: "text-emerald-700 dark:text-emerald-300", noteClass: "text-emerald-700 dark:text-emerald-300" },
    amber: { ring: "#d97706", soft: "#fef3c7", textClass: "text-amber-700 dark:text-amber-300", noteClass: "text-amber-700 dark:text-amber-300" },
    red: { ring: "#dc2626", soft: "#fee2e2", textClass: "text-red-700 dark:text-red-300", noteClass: "text-red-700 dark:text-red-300" },
    blue: { ring: "#2563eb", soft: "#dbeafe", textClass: "text-blue-700 dark:text-blue-300", noteClass: "text-blue-700 dark:text-blue-300" },
  };
  const current = palette[tone] || palette.zinc;
  const safePercent = Math.max(0, Math.min(100, Math.round(Number(percent) || 0)));
  const ringStyle = { background: `conic-gradient(${current.ring} ${safePercent}%, ${current.soft} 0)` };

  return (
    <div className="grid justify-items-center text-center">
      <div className="relative grid h-20 w-20 shrink-0 place-items-center rounded-full" style={ringStyle}>
        <div className="grid h-[58px] w-[58px] place-items-center rounded-full bg-white shadow-inner dark:bg-zinc-900">
          <span className={`max-w-[54px] text-center text-lg font-black leading-tight ${current.textClass}`}>{value}</span>
        </div>
      </div>
      <div className="mt-2 text-xs font-black text-zinc-950 dark:text-white">{label}</div>
      {note ? <div className={`mt-0.5 text-[11px] font-black ${current.noteClass}`}>{note}</div> : null}
    </div>
  );
}'''

new_stat = r'''function WorkspaceMiniStat({
  label,
  value,
  note,
  tone = "zinc",
  percent = 0,
  delay = 0,
  animatedNumber = null,
  formatAnimatedValue = null,
}) {
  // TOS_MY_WORKSPACE_SPACIOUS_PREMIUM_V1
  const palette = {
    zinc: {
      ring: "#18181b",
      track: "#e4e4e7",
      glow: "rgba(24,24,27,0.12)",
      textClass: "text-zinc-950 dark:text-white",
      noteClass: "text-zinc-500 dark:text-zinc-400",
      barClass: "bg-zinc-900 dark:bg-zinc-100",
    },
    emerald: {
      ring: "#10b981",
      track: "#d1fae5",
      glow: "rgba(16,185,129,0.16)",
      textClass: "text-emerald-700 dark:text-emerald-300",
      noteClass: "text-emerald-600 dark:text-emerald-300",
      barClass: "bg-emerald-500",
    },
    amber: {
      ring: "#f59e0b",
      track: "#fef3c7",
      glow: "rgba(245,158,11,0.18)",
      textClass: "text-amber-700 dark:text-amber-300",
      noteClass: "text-amber-600 dark:text-amber-300",
      barClass: "bg-amber-500",
    },
    red: {
      ring: "#ef4444",
      track: "#fee2e2",
      glow: "rgba(239,68,68,0.17)",
      textClass: "text-red-700 dark:text-red-300",
      noteClass: "text-red-600 dark:text-red-300",
      barClass: "bg-red-500",
    },
    blue: {
      ring: "#3b82f6",
      track: "#dbeafe",
      glow: "rgba(59,130,246,0.16)",
      textClass: "text-blue-700 dark:text-blue-300",
      noteClass: "text-blue-600 dark:text-blue-300",
      barClass: "bg-blue-500",
    },
  };

  const current = palette[tone] || palette.zinc;
  const safePercent = Math.max(0, Math.min(100, Number(percent) || 0));
  const targetNumber = Number.isFinite(Number(animatedNumber)) ? Number(animatedNumber) : null;
  const [animatedPercent, setAnimatedPercent] = useState(0);
  const [animatedMetric, setAnimatedMetric] = useState(targetNumber ?? 0);
  const [entered, setEntered] = useState(false);

  useEffect(() => {
    let animationFrame = 0;
    let enterTimer = 0;
    let startTimer = 0;
    const reduceMotion = typeof window !== "undefined"
      && window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;

    if (reduceMotion) {
      setEntered(true);
      setAnimatedPercent(safePercent);
      if (targetNumber !== null) setAnimatedMetric(targetNumber);
      return undefined;
    }

    setEntered(false);
    setAnimatedPercent(0);
    if (targetNumber !== null) setAnimatedMetric(0);

    enterTimer = window.setTimeout(() => setEntered(true), Math.max(0, delay));
    startTimer = window.setTimeout(() => {
      const duration = 980;
      const startedAt = performance.now();

      const tick = (now) => {
        const rawProgress = Math.min(1, (now - startedAt) / duration);
        const eased = 1 - Math.pow(1 - rawProgress, 4);
        setAnimatedPercent(safePercent * eased);
        if (targetNumber !== null) setAnimatedMetric(targetNumber * eased);
        if (rawProgress < 1) animationFrame = requestAnimationFrame(tick);
      };

      animationFrame = requestAnimationFrame(tick);
    }, Math.max(0, delay) + 80);

    return () => {
      window.clearTimeout(enterTimer);
      window.clearTimeout(startTimer);
      cancelAnimationFrame(animationFrame);
    };
  }, [safePercent, targetNumber, delay]);

  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - animatedPercent / 100);
  const displayValue = targetNumber === null
    ? value
    : typeof formatAnimatedValue === "function"
      ? formatAnimatedValue(animatedMetric)
      : Math.round(animatedMetric);

  const bars = [42, 66, 52, 88, 74];

  return (
    <div
      className={`group relative min-h-[118px] overflow-hidden rounded-[22px] border border-zinc-100 bg-white/95 px-4 py-3.5 shadow-[0_8px_26px_rgba(15,23,42,0.045)] transition-[transform,box-shadow,border-color,opacity] duration-500 hover:-translate-y-1 hover:border-zinc-200 hover:shadow-[0_18px_44px_rgba(15,23,42,0.09)] dark:border-white/10 dark:bg-zinc-950/90 ${
        entered ? "translate-y-0 opacity-100" : "translate-y-3 opacity-0"
      }`}
      style={{ transitionDelay: `${Math.max(0, delay)}ms` }}
    >
      <div
        className="pointer-events-none absolute -start-10 -top-12 h-24 w-24 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100"
        style={{ background: current.glow }}
      />
      <div className="relative flex items-center gap-3.5">
        <div className="relative h-[74px] w-[74px] shrink-0">
          <svg className="h-full w-full -rotate-90" viewBox="0 0 80 80" aria-hidden="true">
            <circle
              cx="40"
              cy="40"
              r={radius}
              fill="none"
              stroke={current.track}
              strokeWidth="7"
            />
            <circle
              cx="40"
              cy="40"
              r={radius}
              fill="none"
              stroke={current.ring}
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
              style={{
                filter: `drop-shadow(0 0 5px ${current.glow})`,
                transition: "stroke-dashoffset 80ms linear",
              }}
            />
          </svg>
          <div className="absolute inset-[10px] grid place-items-center rounded-full bg-white shadow-[inset_0_1px_5px_rgba(15,23,42,0.08)] dark:bg-zinc-900">
            <span
              className={`max-w-[54px] text-center text-[18px] font-black leading-none tracking-tight ${current.textClass}`}
              style={{
                transform: entered ? "scale(1)" : "scale(0.72)",
                transition: `transform 620ms cubic-bezier(.16,1.35,.3,1) ${Math.max(0, delay) + 160}ms`,
              }}
            >
              {displayValue}
            </span>
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <div className="text-[13px] font-black leading-5 text-zinc-950 dark:text-white">{label}</div>
          {note ? <div className={`mt-0.5 text-[11px] font-bold leading-4 ${current.noteClass}`}>{note}</div> : null}

          <div className="mt-3 flex h-6 items-end gap-1" aria-hidden="true">
            {bars.map((height, index) => (
              <span
                key={`${tone}-${index}`}
                className={`w-1.5 rounded-full ${current.barClass}`}
                style={{
                  height: `${height}%`,
                  opacity: entered ? 0.72 : 0,
                  transform: entered ? "scaleY(1)" : "scaleY(0.05)",
                  transformOrigin: "bottom",
                  transition: `transform 620ms cubic-bezier(.16,1,.3,1) ${Math.max(0, delay) + 240 + (index * 70)}ms, opacity 360ms ease ${Math.max(0, delay) + 240 + (index * 70)}ms`,
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}'''

source = replace_once(source, old_stat, new_stat, "premium animated KPI component")

source = replace_once(
    source,
    'const titleClass = "line-clamp-2 text-start text-sm font-black leading-6 text-blue-700 underline-offset-4 transition group-hover:underline dark:text-blue-300";',
    'const titleClass = "line-clamp-3 text-start text-[15px] font-black leading-6 text-blue-700 underline-offset-4 transition group-hover:underline dark:text-blue-300";',
    "larger card title",
)

source = replace_once(
    source,
    'className="relative grid min-h-[116px] max-h-[220px] place-items-center overflow-hidden bg-zinc-50 dark:bg-zinc-900"',
    'className="relative grid min-h-[148px] max-h-[260px] place-items-center overflow-hidden bg-zinc-50 dark:bg-zinc-900"',
    "larger attachment preview shell",
)

source = replace_once(
    source,
    'className="block max-h-[220px] w-full object-contain"',
    'className="block max-h-[260px] w-full object-contain"',
    "larger attachment preview image",
)

old_card_classes = r'''      className={`group relative rounded-[16px] border bg-white px-2.5 py-2.5 shadow-sm transition-[border-color,box-shadow,transform,opacity] duration-150 dark:bg-zinc-950 dark:shadow-black/20 ${
        canDrag ? "cursor-grab active:cursor-grabbing" : ""
      } ${
        isDragging
          ? "scale-[0.985] border-amber-300 opacity-45 shadow-lg shadow-amber-100/40 dark:border-amber-400/50"
          : "border-zinc-100 shadow-zinc-200/35 hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-md hover:shadow-amber-100/35 dark:border-white/10 dark:hover:border-amber-400/40"
      }`}'''

new_card_classes = r'''      className={`group relative rounded-[18px] border bg-white px-3.5 py-3.5 shadow-sm transition-[border-color,box-shadow,transform,opacity] duration-150 dark:bg-zinc-950 dark:shadow-black/20 ${
        canDrag ? "cursor-grab active:cursor-grabbing" : ""
      } ${
        isDragging
          ? "scale-[0.985] border-amber-300 opacity-45 shadow-lg shadow-amber-100/40 dark:border-amber-400/50"
          : "border-zinc-100 shadow-zinc-200/35 hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-[0_12px_28px_rgba(15,23,42,0.08)] hover:shadow-amber-100/25 dark:border-white/10 dark:hover:border-amber-400/40"
      }`}'''

source = replace_once(source, old_card_classes, new_card_classes, "spacious task card")

source = replace_once(
    source,
    'className="mt-2 inline-flex max-w-full items-center gap-1.5 rounded-full bg-zinc-50 px-2.5 py-1 text-[10px] font-black text-zinc-500 ring-1 ring-zinc-100 dark:bg-white/5 dark:text-zinc-300 dark:ring-white/10"',
    'className="mt-2.5 inline-flex max-w-full items-center gap-1.5 rounded-full bg-zinc-50 px-3 py-1.5 text-[11px] font-black text-zinc-500 ring-1 ring-zinc-100 dark:bg-white/5 dark:text-zinc-300 dark:ring-white/10"',
    "larger project chip",
)

source = replace_once(
    source,
    'className="mt-2.5 flex items-center justify-between gap-2 border-t border-zinc-100 pt-2.5 text-[10px] font-black dark:border-white/10"',
    'className="mt-3 flex items-center justify-between gap-2 border-t border-zinc-100 pt-3 text-[11px] font-black dark:border-white/10"',
    "larger card footer",
)

old_stats = r'''    <div className="tos-my-workspace mx-auto w-full max-w-[1580px]" dir={isAr ? "rtl" : "ltr"}>
      <div className={`mb-4 grid grid-cols-2 gap-3 md:grid-cols-5 ${isAr ? "direction-rtl" : "direction-ltr"}`}>
        <WorkspaceMiniStat label={isAr ? "نسبة الإنجاز" : "Completion rate"} value={`${completionRate}%`} note={isAr ? "من إجمالي المهام" : "Of total tasks"} tone="amber" percent={completionRate} />
        <WorkspaceMiniStat label={isAr ? "إجمالي المهام" : "Total tasks"} value={totalCount} note={isAr ? "الشخصية والمشاريع" : "Personal and projects"} tone="zinc" percent={tasks.length ? 100 : 0} />
        <WorkspaceMiniStat label={isAr ? "المهام المكتملة" : "Completed tasks"} value={doneCount} note={isAr ? "هذا الشهر" : "Completed"} tone="emerald" percent={(doneCount / totalForStats) * 100} />
        <WorkspaceMiniStat label={isAr ? "إجمالي التقديرات" : "Total estimates"} value={formatHoursValue(estimatedHours, isAr)} note={isAr ? "وقت تقديري" : "Estimated time"} tone="blue" percent={estimatedHours ? 100 : 0} />
        <WorkspaceMiniStat label={isAr ? "المهام المتأخرة" : "Overdue tasks"} value={overdueCount} note={isAr ? "تحتاج انتباهك" : "Need attention"} tone="red" percent={(overdueCount / totalForStats) * 100} />
      </div>'''

new_stats = r'''    <div className="tos-my-workspace mx-auto w-full max-w-[1800px]" dir={isAr ? "rtl" : "ltr"}>
      <div className={`mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5 ${isAr ? "direction-rtl" : "direction-ltr"}`}>
        <WorkspaceMiniStat
          label={isAr ? "نسبة الإنجاز" : "Completion rate"}
          value={`${completionRate}%`}
          animatedNumber={completionRate}
          formatAnimatedValue={(number) => `${Math.round(number)}%`}
          note={isAr ? "من إجمالي المهام" : "Of total tasks"}
          tone="amber"
          percent={completionRate}
          delay={0}
        />
        <WorkspaceMiniStat
          label={isAr ? "إجمالي المهام" : "Total tasks"}
          value={totalCount}
          animatedNumber={totalCount}
          note={isAr ? "الشخصية والمشاريع" : "Personal and projects"}
          tone="zinc"
          percent={tasks.length ? 100 : 0}
          delay={90}
        />
        <WorkspaceMiniStat
          label={isAr ? "المهام المكتملة" : "Completed tasks"}
          value={doneCount}
          animatedNumber={doneCount}
          note={isAr ? "هذا الشهر" : "Completed"}
          tone="emerald"
          percent={(doneCount / totalForStats) * 100}
          delay={180}
        />
        <WorkspaceMiniStat
          label={isAr ? "إجمالي التقديرات" : "Total estimates"}
          value={formatHoursValue(estimatedHours, isAr)}
          animatedNumber={estimatedHours}
          formatAnimatedValue={(number) => formatHoursValue(number, isAr)}
          note={isAr ? "وقت تقديري" : "Estimated time"}
          tone="blue"
          percent={estimatedHours ? 100 : 0}
          delay={270}
        />
        <WorkspaceMiniStat
          label={isAr ? "المهام المتأخرة" : "Overdue tasks"}
          value={overdueCount}
          animatedNumber={overdueCount}
          note={isAr ? "تحتاج انتباهك" : "Need attention"}
          tone="red"
          percent={(overdueCount / totalForStats) * 100}
          delay={360}
        />
      </div>'''

source = replace_once(source, old_stats, new_stats, "spacious KPI row")

source = replace_once(
    source,
    '<div className="mt-4 overflow-x-auto pb-1">\n          <div className="grid min-w-[1180px] grid-cols-6 gap-2.5">',
    '<div data-tos-my-workspace-spacious-premium="v1" className="tos-my-workspace-board-scroll mt-4 overflow-x-auto overscroll-x-contain pb-3 pt-1">\n          <div className="flex w-max min-w-full gap-4">',
    "horizontal premium board",
)

old_section_class = r'''                  className={`overflow-hidden rounded-[20px] border bg-white/[0.82] shadow-sm transition-[border-color,box-shadow,transform,background-color] duration-150 dark:bg-zinc-900/70 dark:shadow-black/20 ${
                    isDropTarget
                      ? "scale-[1.008] border-amber-300 bg-amber-50/45 shadow-lg shadow-amber-100/60 ring-2 ring-amber-200/70 dark:border-amber-400/50 dark:bg-amber-500/10 dark:ring-amber-400/20"
                      : "border-zinc-100 shadow-zinc-200/50 dark:border-white/10"
                  }`}'''

new_section_class = r'''                  className={`w-[340px] shrink-0 overflow-hidden rounded-[22px] border bg-white/[0.82] shadow-sm transition-[border-color,box-shadow,transform,background-color] duration-150 2xl:w-[360px] dark:bg-zinc-900/70 dark:shadow-black/20 ${
                    isDropTarget
                      ? "scale-[1.008] border-amber-300 bg-amber-50/45 shadow-lg shadow-amber-100/60 ring-2 ring-amber-200/70 dark:border-amber-400/50 dark:bg-amber-500/10 dark:ring-amber-400/20"
                      : "border-zinc-100 shadow-zinc-200/50 dark:border-white/10"
                  }`}'''

source = replace_once(source, old_section_class, new_section_class, "fixed spacious columns")

source = replace_once(
    source,
    '<header className="flex items-center justify-between gap-2.5 px-3 py-2.5">',
    '<header className="flex items-center justify-between gap-3 px-4 py-3.5">',
    "spacious column header",
)

source = replace_once(
    source,
    'className={`text-base font-black ${column.toneClass.split(" ").filter((part) => part.startsWith("text-") || part.startsWith("dark:text-")).join(" ")}`}',
    'className={`text-[17px] font-black tracking-tight ${column.toneClass.split(" ").filter((part) => part.startsWith("text-") || part.startsWith("dark:text-")).join(" ")}`}',
    "larger column title",
)

source = replace_once(
    source,
    'className="min-h-[120px] max-h-[660px] space-y-2.5 overflow-y-auto border-t border-zinc-100 p-2.5 dark:border-white/10"',
    'className="min-h-[160px] max-h-[720px] space-y-3 overflow-y-auto border-t border-zinc-100 p-3.5 dark:border-white/10"',
    "spacious column task stack",
)

TARGET.write_text(source, encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-MY-WORKSPACE-SPACIOUS-PREMIUM-V1")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("BOARD_COLUMNS_WIDTH=340PX_360PX_2XL")
print("BOARD_HORIZONTAL_SCROLL=ACTIVE")
print("TASK_CARDS_SPACIOUS=ACTIVE")
print("KPI_SVG_RING_ANIMATION=ACTIVE")
print("KPI_COUNT_UP_ANIMATION=ACTIVE")
print("KPI_STAGGER=ACTIVE")
print("KPI_MINI_BARS_ANIMATION=ACTIVE")
print("PREFERS_REDUCED_MOTION=RESPECTED")
print("MY_WORKSPACE_DRAG_DROP=PRESERVED")
print("WAITING_CLIENT_GATE=PRESERVED")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
print("DEPENDENCIES_ADDED=NO")
print("NEXT=build frontend, deploy atomically, verify My Workspace visually + drag/drop")
