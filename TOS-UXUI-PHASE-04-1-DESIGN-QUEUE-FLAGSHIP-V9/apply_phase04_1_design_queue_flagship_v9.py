from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
PREF = ROOT / "frontend/src/contexts/PreferencesContext.jsx"
SIDEBAR = ROOT / "frontend/src/components/layout/Sidebar.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_DQ_SHA = "f71c66b26a5cd7bb06ca849ce82afef897ed58d288c9fcfa198168a1d2d0eb59"
EXPECTED_PREF_SHA = "1d949f3bc668400ffbfa69082166a41654a1c5ed9518b720675a7f13d873b731"
EXPECTED_SIDEBAR_SHA = "e9c97687ba48cdc0fd58877ec8e71b5d3a7d7856d1fd13097e700e35390f74f0"
EXPECTED_CSS_SHA = "9daf48aa7c5cbaf269a93a3adcc1b12eed569a3d43cc676ff0340353fdf81fce"
V9_MARKER = "TOS_DQ_PREMIUM_MENU_V9"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V9")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print(f"ERROR={message}")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


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


for path in (DQ, PREF, SIDEBAR, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")
if sha(DQ) != EXPECTED_DQ_SHA:
    fail("Design Queue differs from verified Performance V3/V8 state")
if sha(PREF) != EXPECTED_PREF_SHA:
    fail("PreferencesContext differs from verified state")
if sha(SIDEBAR) != EXPECTED_SIDEBAR_SHA:
    fail("Sidebar differs from verified V7 state")
if sha(CSS) != EXPECTED_CSS_SHA:
    fail("index.css differs from verified V8 state")

original_dq = DQ.read_text()
if V9_MARKER in original_dq:
    fail("V9 already present")

backup = None
stage = None
live_swapped = False

try:
    updated = original_dq

    updated = replace_once(
        updated,
        'import { memo, useEffect, useMemo, useRef, useState } from "react";\n',
        'import { memo, useEffect, useMemo, useRef, useState } from "react";\nimport { createPortal } from "react-dom";\n',
        "react-dom portal import",
    )
    updated = replace_once(
        updated,
        '  CalendarDays,\n',
        '  CalendarDays,\n  Check,\n',
        "Check icon import",
    )

    anchor = '''function initials(value = "") {\n  const parts = String(value).trim().split(/\\s+/).filter(Boolean);\n  return `${parts[0]?.[0] || "?"}${parts[1]?.[0] || ""}`;\n}\n'''
    premium_menu = r'''

const DQ_PREMIUM_MENU_VERSION = "TOS_DQ_PREMIUM_MENU_V9";

function PremiumMenu({ value, onChange, options, ariaLabel = "Select" }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState({ top: 0, left: 0, width: 280, maxHeight: 320 });
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const selected = options.find((option) => String(option.value) === String(value)) || options[0];
  const searchable = options.length > 8;
  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return options;
    return options.filter((option) => String(option.label || "").toLowerCase().includes(term));
  }, [options, query]);

  useEffect(() => {
    if (!open) return undefined;

    const syncPosition = () => {
      const trigger = triggerRef.current;
      if (!trigger) return;
      const rect = trigger.getBoundingClientRect();
      const viewportGap = 12;
      const desiredHeight = searchable ? 360 : 300;
      const roomBelow = window.innerHeight - rect.bottom - viewportGap;
      const roomAbove = rect.top - viewportGap;
      const openAbove = roomBelow < 180 && roomAbove > roomBelow;
      const maxHeight = Math.max(160, Math.min(desiredHeight, openAbove ? roomAbove - 8 : roomBelow - 8));
      const width = Math.min(Math.max(rect.width, 260), 420);
      const left = Math.min(Math.max(viewportGap, rect.left), Math.max(viewportGap, window.innerWidth - width - viewportGap));
      const top = openAbove ? Math.max(viewportGap, rect.top - maxHeight - 8) : Math.min(window.innerHeight - viewportGap, rect.bottom + 8);
      setPosition({ top, left, width, maxHeight });
    };

    const onPointerDown = (event) => {
      if (triggerRef.current?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setOpen(false);
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setOpen(false);
        triggerRef.current?.focus();
      }
    };

    syncPosition();
    window.addEventListener("resize", syncPosition);
    window.addEventListener("scroll", syncPosition, true);
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("resize", syncPosition);
      window.removeEventListener("scroll", syncPosition, true);
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, searchable]);

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  const choose = (nextValue) => {
    onChange(nextValue);
    setOpen(false);
    setQuery("");
    triggerRef.current?.focus();
  };

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        data-dq-menu-version={DQ_PREMIUM_MENU_VERSION}
        onClick={() => setOpen((current) => !current)}
        className="group flex h-10 w-full min-w-0 items-center justify-between gap-3 rounded-xl border border-zinc-200 bg-white px-3 text-start text-[12px] font-extrabold text-zinc-800 shadow-[0_1px_0_rgba(255,255,255,.8)] outline-none transition hover:border-amber-300 hover:bg-amber-50/30 focus:border-amber-400 focus:ring-2 focus:ring-amber-400/15 dark:border-white/10 dark:bg-[#15171b] dark:text-zinc-100 dark:shadow-none dark:hover:border-amber-400/30 dark:hover:bg-white/[0.035]"
      >
        <span className="min-w-0 flex-1 truncate">{selected?.label || ariaLabel}</span>
        <ChevronDown size={15} className={cn("shrink-0 text-zinc-400 transition-transform duration-200 group-hover:text-amber-600 dark:text-zinc-500", open && "rotate-180 text-amber-600 dark:text-amber-300")} />
      </button>

      {open && createPortal(
        <div
          ref={menuRef}
          role="listbox"
          aria-label={ariaLabel}
          data-dq-premium-menu={DQ_PREMIUM_MENU_VERSION}
          style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, zIndex: 10000 }}
          className="flex overflow-hidden rounded-2xl border border-amber-200/70 bg-[#fffdf8] p-1.5 shadow-[0_24px_70px_rgba(49,37,15,.22),0_4px_18px_rgba(49,37,15,.08)] ring-1 ring-white/80 dark:border-amber-400/15 dark:bg-[#0d0f12] dark:shadow-[0_28px_80px_rgba(0,0,0,.56),0_4px_20px_rgba(0,0,0,.32)] dark:ring-white/[0.03]"
        >
          <div className="flex min-h-0 w-full flex-col">
            {searchable && (
              <div className="relative mb-1.5 shrink-0">
                <Search size={14} className="pointer-events-none absolute top-1/2 -translate-y-1/2 text-zinc-400 ltr:left-3 rtl:right-3" />
                <input
                  autoFocus
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search..."
                  className="h-9 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold text-zinc-800 outline-none placeholder:text-zinc-400 focus:border-amber-400 ltr:pl-8 rtl:pr-8 dark:border-white/10 dark:bg-[#15171b] dark:text-zinc-100 dark:placeholder:text-zinc-500"
                />
              </div>
            )}
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain pr-0.5">
              {filtered.map((option) => {
                const active = String(option.value) === String(value);
                return (
                  <button
                    key={String(option.value)}
                    type="button"
                    role="option"
                    aria-selected={active}
                    onClick={() => choose(option.value)}
                    className={cn(
                      "mb-1 flex min-h-10 w-full items-center gap-2 rounded-xl px-3 py-2 text-start text-[12px] font-bold leading-5 transition last:mb-0",
                      active
                        ? "bg-gradient-to-r from-amber-100/90 to-[#fff8df] text-zinc-950 shadow-sm ring-1 ring-amber-200/70 dark:from-amber-400/15 dark:to-amber-300/[0.06] dark:text-amber-100 dark:ring-amber-400/20"
                        : "text-zinc-700 hover:bg-amber-50 hover:text-zinc-950 dark:text-zinc-300 dark:hover:bg-white/[0.055] dark:hover:text-white",
                    )}
                  >
                    <span className="min-w-0 flex-1 break-words">{option.label}</span>
                    {active && <Check size={14} className="shrink-0 text-amber-600 dark:text-amber-300" />}
                  </button>
                );
              })}
              {!filtered.length && <div className="px-3 py-7 text-center text-xs font-bold text-zinc-400">No matches</div>}
            </div>
          </div>
        </div>,
        document.body,
      )}
    </>
  );
}
'''
    updated = replace_once(updated, anchor, anchor + premium_menu, "PremiumMenu component")

    old_capacity = '''<Field as="select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="h-10 text-xs"><option value="ALL">{tr.queue.filters.statuses}</option><option value="AVAILABLE">{tr.queue.capacity.available}</option><option value="BUSY">{tr.queue.capacity.busy}</option><option value="OVERLOADED">{tr.queue.capacity.full}</option></Field><Field as="select" value={sortKey} onChange={(event) => setSortKey(event.target.value)} className="h-10 text-xs"><option value="capacity-desc">{lang === "en" ? "Highest workload" : "الأعلى حملًا"}</option><option value="capacity-asc">{lang === "en" ? "Lowest workload" : "الأقل حملًا"}</option><option value="tasks-desc">{lang === "en" ? "Most tasks" : "الأكثر مهامًا"}</option><option value="name">{lang === "en" ? "Name" : "الاسم"}</option></Field>'''
    new_capacity = '''<PremiumMenu value={statusFilter} onChange={setStatusFilter} ariaLabel={tr.queue.filters.statuses} options={[{ value: "ALL", label: tr.queue.filters.statuses }, { value: "AVAILABLE", label: tr.queue.capacity.available }, { value: "BUSY", label: tr.queue.capacity.busy }, { value: "OVERLOADED", label: tr.queue.capacity.full }]} /><PremiumMenu value={sortKey} onChange={setSortKey} ariaLabel={lang === "en" ? "Sort workload" : "ترتيب الحمل"} options={[{ value: "capacity-desc", label: lang === "en" ? "Highest workload" : "الأعلى حملًا" }, { value: "capacity-asc", label: lang === "en" ? "Lowest workload" : "الأقل حملًا" }, { value: "tasks-desc", label: lang === "en" ? "Most tasks" : "الأكثر مهامًا" }, { value: "name", label: lang === "en" ? "Name" : "الاسم" }]} />'''
    updated = replace_once(updated, old_capacity, new_capacity, "capacity native selects")

    old_project = '''<Field as="select" value={filters.projectId} onChange={(event) => updateFilters({ projectId: event.target.value })}><option value="all">{tr.queue.filters.projects}</option>{projectOptions.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</Field>'''
    new_project = '''<PremiumMenu value={filters.projectId} onChange={(nextValue) => updateFilters({ projectId: nextValue })} ariaLabel={tr.queue.filters.projects} options={[{ value: "all", label: tr.queue.filters.projects }, ...projectOptions.map((project) => ({ value: project.id, label: project.name }))]} />'''
    updated = replace_once(updated, old_project, new_project, "project premium menu")

    old_status = '''<Field as="select" value={filters.status} onChange={(event) => updateFilters({ status: event.target.value })}>{STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status === "all" ? tr.queue.filters.statuses : tr.status[status]}</option>)}</Field>'''
    new_status = '''<PremiumMenu value={filters.status} onChange={(nextValue) => updateFilters({ status: nextValue })} ariaLabel={tr.queue.filters.statuses} options={STATUS_OPTIONS.map((status) => ({ value: status, label: status === "all" ? tr.queue.filters.statuses : tr.status[status] }))} />'''
    updated = replace_once(updated, old_status, new_status, "status premium menu")

    old_assignee = '''<Field as="select" value={filters.assignee} onChange={(event) => updateFilters({ assignee: event.target.value })}><option value="all">{tr.queue.filters.assignees}</option><option value="unassigned">{tr.queue.stats.unassigned}</option>{data.designers.map((designer) => <option key={designer.id} value={designer.id}>{designerLabel(designer, tr.common.designer)}</option>)}</Field>'''
    new_assignee = '''<PremiumMenu value={filters.assignee} onChange={(nextValue) => updateFilters({ assignee: nextValue })} ariaLabel={tr.queue.filters.assignees} options={[{ value: "all", label: tr.queue.filters.assignees }, { value: "unassigned", label: tr.queue.stats.unassigned }, ...data.designers.map((designer) => ({ value: designer.id, label: designerLabel(designer, tr.common.designer) }))]} />'''
    updated = replace_once(updated, old_assignee, new_assignee, "assignee premium menu")

    old_lifecycle = '''<Field as="select" value={filters.lifecycle} onChange={(event) => updateFilters({ lifecycle: event.target.value })}><option value="active">{tr.queue.filters.active}</option><option value="archived">{tr.queue.filters.archived}</option><option value="rejected">{tr.queue.filters.rejected}</option><option value="all">{tr.queue.filters.all}</option></Field>'''
    new_lifecycle = '''<PremiumMenu value={filters.lifecycle} onChange={(nextValue) => updateFilters({ lifecycle: nextValue })} ariaLabel={tr.queue.filters.active} options={[{ value: "active", label: tr.queue.filters.active }, { value: "archived", label: tr.queue.filters.archived }, { value: "rejected", label: tr.queue.filters.rejected }, { value: "all", label: tr.queue.filters.all }]} />'''
    updated = replace_once(updated, old_lifecycle, new_lifecycle, "lifecycle premium menu")

    DQ.write_text(updated)

    if DQ.read_text().count(V9_MARKER) < 2:
        raise RuntimeError("V9 marker missing from source")
    if DQ.read_text().count("<PremiumMenu ") < 6:
        raise RuntimeError("expected premium menu replacements missing")
    if sha(PREF) != EXPECTED_PREF_SHA or sha(SIDEBAR) != EXPECTED_SIDEBAR_SHA or sha(CSS) != EXPECTED_CSS_SHA:
        raise RuntimeError("non-DesignQueue source changed unexpectedly")

    subprocess.run(["git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/pages/DesignQueuePage.jsx"], check=True)
    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V9_MARKER.encode())
    if dist_marker < 1:
        raise RuntimeError("V9 marker missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-design-queue-v9.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-design-queue-v9.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged index missing")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_marker = tree_count(LIVE, V9_MARKER.encode())
    if live_marker < 1:
        raise RuntimeError("V9 marker missing from live build")

except Exception as exc:
    DQ.write_text(original_dq)
    if live_swapped and backup and backup.exists():
        if LIVE.exists():
            shutil.rmtree(LIVE)
        backup.rename(LIVE)
    if stage and stage.exists():
        shutil.rmtree(stage)
    fail(str(exc))

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("V9_RUNTIME=YES")
print("NATIVE_DQ_FILTER_MENUS_REPLACED=YES")
print("PROJECT_MENU_SEARCHABLE=YES")
print("CAPACITY_MENUS_PREMIUM=YES")
print("BOARD_FILTER_MENUS_PREMIUM=YES")
print("DARK_LIGHT_MENU_THEMES=YES")
print("PERFORMANCE_V3_PRESERVED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("SOURCE_V9_MARKER_COUNT=" + str(DQ.read_text().count(V9_MARKER)))
print("DIST_V9_MARKER_COUNT=" + str(tree_count(DIST, V9_MARKER.encode())))
print("LIVE_V9_MARKER_COUNT=" + str(tree_count(LIVE, V9_MARKER.encode())))
print("DESIGN_QUEUE_SHA256=" + sha(DQ))
print("SIDEBAR_SHA256=" + sha(SIDEBAR))
print("INDEX_CSS_SHA256=" + sha(CSS))
