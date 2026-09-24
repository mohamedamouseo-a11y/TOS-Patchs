#!/usr/bin/env python3
# TOS-MY-WORKSPACE-KPI-LIVE-MOTION-V1
# Continuous premium KPI motion for My Workspace.
# Frontend-only; KPI data/calculations, filters, Kanban, DnD, sticky scrollbar unchanged.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
MARKER = "TOS_MY_WORKSPACE_KPI_LIVE_MOTION_V1"
REQ_PREMIUM = "TOS_MY_WORKSPACE_SPACIOUS_PREMIUM_V1"

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

if REQ_PREMIUM not in source:
    die(f"required marker missing: {REQ_PREMIUM}")

backup = TARGET.with_name(
    TARGET.name + f".bak-kpi-live-motion-v1-{int(time.time())}"
)
shutil.copy2(TARGET, backup)

source = replace_once(
    source,
    '''  const bars = [42, 66, 52, 88, 74];''',
    '''  // TOS_MY_WORKSPACE_KPI_LIVE_MOTION_V1
  const bars = [42, 66, 52, 88, 74];
  const ambientDelay = Math.max(0, delay);''',
    "kpi live motion marker",
)

source = replace_once(
    source,
    '''      <div
        className="pointer-events-none absolute -start-10 -top-12 h-24 w-24 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100"
        style={{ background: current.glow }}
      />''',
    '''      <div
        className="pointer-events-none absolute -start-10 -top-12 h-24 w-24 rounded-full opacity-55 blur-2xl motion-safe:animate-[pulse_3.2s_ease-in-out_infinite] motion-reduce:animate-none"
        style={{
          background: current.glow,
          animationDelay: `${ambientDelay}ms`,
        }}
      />
      <div
        className="pointer-events-none absolute -bottom-12 -end-10 h-24 w-24 rounded-full opacity-35 blur-3xl motion-safe:animate-[pulse_4.4s_ease-in-out_infinite] motion-reduce:animate-none"
        style={{
          background: current.glow,
          animationDelay: `${ambientDelay + 480}ms`,
        }}
      />''',
    "ambient glow",
)

source = replace_once(
    source,
    '''        <div className="relative h-[74px] w-[74px] shrink-0">
          <svg className="h-full w-full -rotate-90" viewBox="0 0 80 80" aria-hidden="true">''',
    '''        <div className="relative h-[74px] w-[74px] shrink-0">
          <span
            className="pointer-events-none absolute inset-[-5px] rounded-full border border-dashed opacity-30 motion-safe:animate-[spin_7s_linear_infinite] motion-reduce:animate-none"
            style={{
              borderColor: current.ring,
              animationDelay: `${ambientDelay}ms`,
            }}
            aria-hidden="true"
          />
          <span
            className="pointer-events-none absolute inset-[-3px] motion-safe:animate-[spin_5.5s_linear_infinite] motion-reduce:animate-none"
            style={{ animationDelay: `${ambientDelay + 160}ms` }}
            aria-hidden="true"
          >
            <span
              className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 rounded-full"
              style={{
                background: current.ring,
                boxShadow: `0 0 10px 2px ${current.glow}`,
              }}
            />
          </span>

          <svg className="h-full w-full -rotate-90" viewBox="0 0 80 80" aria-hidden="true">
            <circle
              cx="40"
              cy="40"
              r="37"
              fill="none"
              stroke={current.ring}
              strokeWidth="1.5"
              strokeDasharray="3 8"
              opacity="0.18"
              className="motion-safe:animate-[spin_9s_linear_infinite] motion-reduce:animate-none"
              style={{
                transformOrigin: "40px 40px",
                animationDelay: `${ambientDelay + 240}ms`,
              }}
            />''',
    "orbit ring",
)

source = replace_once(
    source,
    '''              style={{
                filter: `drop-shadow(0 0 5px ${current.glow})`,
                transition: "stroke-dashoffset 80ms linear",
              }}''',
    '''              className="motion-safe:animate-[pulse_2.8s_ease-in-out_infinite] motion-reduce:animate-none"
              style={{
                filter: `drop-shadow(0 0 6px ${current.glow})`,
                transition: "stroke-dashoffset 80ms linear",
                animationDelay: `${ambientDelay + 320}ms`,
              }}''',
    "progress ring pulse",
)

source = replace_once(
    source,
    '''                className={`w-1.5 rounded-full ${current.barClass}`}
                style={{
                  height: `${height}%`,
                  opacity: entered ? 0.72 : 0,
                  transform: entered ? "scaleY(1)" : "scaleY(0.05)",
                  transformOrigin: "bottom",
                  transition: `transform 620ms cubic-bezier(.16,1,.3,1) ${Math.max(0, delay) + 240 + (index * 70)}ms, opacity 360ms ease ${Math.max(0, delay) + 240 + (index * 70)}ms`,
                }}''',
    '''                className={`w-1.5 rounded-full ${current.barClass} motion-safe:animate-[pulse_1.45s_ease-in-out_infinite] motion-reduce:animate-none`}
                style={{
                  height: `${height}%`,
                  opacity: entered ? 0.78 : 0,
                  transform: entered ? "scaleY(1)" : "scaleY(0.05)",
                  transformOrigin: "bottom",
                  transition: `transform 620ms cubic-bezier(.16,1,.3,1) ${ambientDelay + 240 + (index * 70)}ms, opacity 360ms ease ${ambientDelay + 240 + (index * 70)}ms`,
                  animationDelay: `${ambientDelay + (index * 180)}ms`,
                }}''',
    "bar wave animation",
)

source = replace_once(
    source,
    '''      className={`group relative min-h-[118px] overflow-hidden rounded-[22px] border border-zinc-100 bg-white/95 px-4 py-3.5 shadow-[0_8px_26px_rgba(15,23,42,0.045)] transition-[transform,box-shadow,border-color,opacity] duration-500 hover:-translate-y-1 hover:border-zinc-200 hover:shadow-[0_18px_44px_rgba(15,23,42,0.09)] dark:border-white/10 dark:bg-zinc-950/90 ${''',
    '''      data-tos-my-workspace-kpi-live-motion="v1"
      className={`group relative min-h-[118px] overflow-hidden rounded-[22px] border border-zinc-100 bg-white/95 px-4 py-3.5 shadow-[0_8px_26px_rgba(15,23,42,0.045)] transition-[transform,box-shadow,border-color,opacity] duration-500 hover:-translate-y-1 hover:border-zinc-200 hover:shadow-[0_18px_44px_rgba(15,23,42,0.09)] dark:border-white/10 dark:bg-zinc-950/90 ${''',
    "kpi data marker",
)

TARGET.write_text(source, encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-MY-WORKSPACE-KPI-LIVE-MOTION-V1")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("KPI_ORBIT=ACTIVE")
print("KPI_DOTTED_RING_SPIN=ACTIVE")
print("KPI_GLOW_BREATHING=ACTIVE")
print("KPI_BAR_WAVE=ACTIVE")
print("KPI_PROGRESS_RING_PULSE=ACTIVE")
print("CONTINUOUS_ANIMATION=YES")
print("REDUCED_MOTION_SUPPORTED=YES")
print("KPI_DATA_LOGIC=PRESERVED")
print("FILTERS_UNCHANGED=YES")
print("DRAG_DROP_UNCHANGED=YES")
print("STICKY_SCROLLBAR_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
print("DEPENDENCIES_ADDED=NO")
