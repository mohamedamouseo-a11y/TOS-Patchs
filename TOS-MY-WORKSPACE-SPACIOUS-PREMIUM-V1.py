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

    if