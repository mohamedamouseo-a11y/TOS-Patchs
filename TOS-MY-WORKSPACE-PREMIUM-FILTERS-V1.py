#!/usr/bin/env python3
# TOS-MY-WORKSPACE-PREMIUM-FILTERS-V1
# Premium custom search + dropdown filter controls for My Workspace.
# Frontend-only; filter logic, Trello DnD, sticky scrollbar and APIs unchanged.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
MARKER = "TOS_MY_WORKSPACE_PREMIUM_FILTERS_V1"
REQ_STICKY = "TOS_MY_WORKSPACE_STICKY_SCROLLBAR_V1_1"
REQ_PREMIUM = "TOS_MY_WORKSPACE_SPACIOUS_PREMIUM_V1"
REQ_DND = "TOS_MY_WORKSPACE_TRELLO_DRAG_DROP_V1"

def die(message):
    print(f"PATCH=FAIL\\nERROR={message}")
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

for required in (REQ_STICKY, REQ_PREMIUM, REQ_DND):
    if required not in source:
        die(f"required marker missing: {required}")

backup = TARGET.with_name(
    TARGET.name + f".bak-premium-filters-v1-{int(time.time())}"
)
shutil.copy2(TARGET, backup)

source = replace_once(
    source,
    """  Check,
  CheckCircle2,""",
    """  Check,
  CheckCircle2,
  CalendarDays,
  ChevronDown,""",
    "calendar/chevron imports",
)

source = replace_once(
    source,
    """  Link2,
  ListChecks,""",
    """  Link2,
  ListChecks,
  Layers3,
  ArrowUpDown,""",
    "layers/sort imports",
)

component_anchor = """function WorkspaceMiniStat({"""

premium_component = r"""function PremiumFilterSelect({
  value,
  options = [],
  placeholder,
  label,
  icon: Icon,
  onChange,
  isAr = false,
  minMenuWidth = 220,
}) {
  // TOS_MY_WORKSPACE_PREMIUM_FILTERS_V1
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const selectedOption = options.find((option) => String(option.value) === String(value));
  const displayLabel = selectedOption?.label || placeholder;

  useEffect(() => {
    if (!open || typeof document === "undefined") return undefined;

    const handlePointerDown = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    const handleKeyDown = (event) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative min-w-0" data-premium-filter-select="v1">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        className={`group flex h-[52px] w-full items-center gap-3 rounded-[16px] border bg-white/95 px-3 text-start shadow-[0_5px_16px_rgba(15,23,42,0.045)] outline-none transition-all duration-200 dark:bg-zinc-950/95 ${
          open
            ? "border-amber-300 ring-4 ring-amber-100/70 shadow-[0_12px_30px_rgba(217,119,6,0.10)] dark:border-amber-400/45 dark:ring-amber-500/10"
            : "border-zinc-200/80 hover:-translate-y-[1px] hover:border-amber-200 hover:shadow-[0_10px_24px_rgba(15,23,42,0.07)] dark:border-white/10 dark:hover:border-amber-400/30"
        }`}
      >
        <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-[11px] border transition ${
          open
            ? "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-400/20 dark:bg-amber-500/10 dark:text-amber-300"
            : "border-zinc-100 bg-zinc-50 text-zinc-500 group-hover:border-amber-100 group-hover:bg-amber-50/70 group-hover:text-amber-700 dark:border-white/10 dark:bg-white/5 dark:text-zinc-400"
        }`}>
          {Icon ? <Icon size={15} strokeWidth={2.2} /> : null}
        </span>

        <span className="min-w-0 flex-1">
          <span className="block text-[9px] font-black uppercase tracking-[0.12em] text-zinc-400 dark:text-zinc-500">
            {label}
          </span>
          <span className={`mt-0.5 block truncate text-[12px] font-black ${
            value ? "text-zinc-900 dark:text-zinc-100" : "text-zinc-600 dark:text-zinc-300"
          }`}>
            {displayLabel}
          </span>
        </span>

        <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-full text-zinc-400 transition duration-200 ${
          open ? "rotate-180 bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-300" : "bg-zinc-50 dark:bg-white/5"
        }`}>
          <ChevronDown size={14} strokeWidth={2.4} />
        </span>
      </button>

      {open ? (
        <div
          className={`absolute top-[calc(100%+8px)] z-[110] overflow-hidden rounded-[18px] border border-zinc-200/80 bg-white/98 p-1.5 shadow-[0_24px_60px_rgba(15,23,42,0.18)] ring-1 ring-black/[0.02] backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/98 dark:ring-white/5 ${
            isAr ? "right-0" : "left-0"
          }`}
          style={{ minWidth: `${minMenuWidth}px`, width: "max(100%, min-content)" }}
        >
          <div className="max-h-[290px] overflow-y-auto overscroll-contain p-1">
            {options.map((option) => {
              const active = String(option.value) === String(value);
              return (
                <button
                  key={`${label}-${option.value}`}
                  type="button"
                  onClick={() => {
                    onChange?.(option.value);
                    setOpen(false);
                  }}
                  className={`group/item flex w-full items-center gap-2.5 rounded-[12px] px-3 py-2.5 text-start transition ${
                    active
                      ? "bg-amber-50 text-amber-800 shadow-[inset_0_0_0_1px_rgba(245,158,11,0.13)] dark:bg-amber-500/10 dark:text-amber-200"
                      : "text-zinc-700 hover:bg-zinc-50 hover:text-zinc-950 dark:text-zinc-300 dark:hover:bg-white/[0.06] dark:hover:text-white"
                  }`}
                >
                  <span className={`grid h-5 w-5 shrink-0 place-items-center rounded-full transition ${
                    active
                      ? "bg-amber-500 text-white"
                      : "bg-zinc-100 text-transparent group-hover/item:bg-zinc-200 dark:bg-white/5 dark:group-hover/item:bg-white/10"
                  }`}>
                    <Check size={12} strokeWidth={3} />
                  </span>
                  <span className="min-w-0 flex-1 truncate text-[12px] font-bold">{option.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function WorkspaceMiniStat({"""

source = replace_once(
    source,
    component_anchor,
    premium_component,
    "premium select component",
)

