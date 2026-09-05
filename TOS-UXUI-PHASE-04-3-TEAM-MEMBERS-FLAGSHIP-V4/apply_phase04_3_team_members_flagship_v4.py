from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
TEAM = ROOT / "frontend/src/pages/TeamPage.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_TEAM_SHA256 = "a5a10e517cf760e2d98115955b53828ad649141e0fefe82bcde3842a939511bd"
EXPECTED_CSS_SHA256 = "94928ca3e7017c7df5962eeeb984847e6e725322702f4798779ecb9f900a9a10"
V1_MARKER = "--tos-team-phase04-3-v1-runtime"
V2_MARKER = "--tos-team-phase04-3-v2-runtime"
V3_MARKER = "--tos-team-phase04-3-v3-runtime"
V4_MARKER = "--tos-team-phase04-3-v4-runtime"
PREMIUM_COMPONENT = "TeamPremiumSelectV4"

print("RUNNING=PHASE04_3_TEAM_MEMBERS_FLAGSHIP_V4")


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
    print("V4_RUNTIME=NO")
    sys.exit(1)


for path in (TEAM, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha256(TEAM) != EXPECTED_TEAM_SHA256:
    fail("TeamPage SHA256 differs from Phase 04.3 V3 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css SHA256 differs from Phase 04.3 V3 live source")

original_team = TEAM.read_text()
original_css = CSS.read_text()

for marker in (V1_MARKER, V2_MARKER, V3_MARKER):
    if original_css.count(marker) != 1:
        fail(f"required previous marker missing or duplicated: {marker}")
if V4_MARKER in original_css or PREMIUM_COMPONENT in original_team:
    fail("Phase 04.3 V4 already present")

updated_team = original_team

# Portal import for true premium popup menus that are not clipped by panel overflow.
react_import = 'import { useEffect, useMemo, useRef, useState } from "react";'
portal_import = 'import { createPortal } from "react-dom";'
if updated_team.count(react_import) != 1:
    fail("React import signature not found exactly once")
if portal_import not in updated_team:
    updated_team = updated_team.replace(react_import, react_import + "\n" + portal_import, 1)

# Chevron is used in the premium trigger. CheckCircle2 is already imported and used as the selected indicator.
lucide_anchor = '  CalendarClock,\n  CheckCircle2,'
if updated_team.count(lucide_anchor) != 1:
    fail("lucide import signature not found exactly once")
updated_team = updated_team.replace(lucide_anchor, '  CalendarClock,\n  CheckCircle2,\n  ChevronDown,', 1)

# Add a self-contained accessible premium select component after MiniStat and before ProjectsPopupModal.
component_anchor = '\nfunction ProjectsPopupModal({ userItem, lang = "ar", onClose }) {'
if updated_team.count(component_anchor) != 1:
    fail("ProjectsPopupModal anchor not found exactly once")

premium_component = r'''

function TeamPremiumSelectV4({ value, onChange, options = [], lang = "en", ariaLabel = "Filter" }) {
  const [open, setOpen] = useState(false);
  const [menuStyle, setMenuStyle] = useState({});
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const selected = options.find((option) => option.value === value) || options[0] || { value: "", label: "—" };
  const isRtl = lang !== "en";

  function positionMenu() {
    const trigger = triggerRef.current;
    if (!trigger) return;
    const rect = trigger.getBoundingClientRect();
    const viewportPad = 12;
    const desiredHeight = Math.min(336, Math.max(128, options.length * 44 + 16));
    const roomBelow = window.innerHeight - rect.bottom - viewportPad;
    const openAbove = roomBelow < Math.min(desiredHeight, 190) && rect.top > roomBelow;
    const top = openAbove ? Math.max(viewportPad, rect.top - desiredHeight - 8) : Math.min(window.innerHeight - viewportPad, rect.bottom + 8);
    const width = Math.max(rect.width, 190);
    const left = Math.min(Math.max(viewportPad, rect.left), Math.max(viewportPad, window.innerWidth - width - viewportPad));
    setMenuStyle({ top, left, width, maxHeight: desiredHeight });
  }

  useEffect(() => {
    if (!open) return undefined;
    positionMenu();
    const handlePointerDown = (event) => {
      if (triggerRef.current?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setOpen(false);
    };
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    const handleViewport = () => positionMenu();
    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    window.addEventListener("resize", handleViewport);
    window.addEventListener("scroll", handleViewport, true);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("resize", handleViewport);
      window.removeEventListener("scroll", handleViewport, true);
    };
  }, [open, options.length]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        className={cn("tos-team-filter-trigger-v4 flex min-w-0 items-center justify-between gap-3 rounded-xl px-3.5 py-2.5 text-sm font-bold", open && "is-open")}
      >
        <span className="truncate">{selected.label}</span>
        <ChevronDown size={15} className={cn("shrink-0 transition-transform duration-200", open && "rotate-180")} />
      </button>
      {open && typeof document !== "undefined" && createPortal(
        <div
          ref={menuRef}
          className="tos-team-premium-filter-menu-v4"
          style={menuStyle}
          dir={isRtl ? "rtl" : "ltr"}
          role="listbox"
          aria-label={ariaLabel}
        >
          <div className="tos-team-premium-filter-menu-inner-v4">
            {options.map((option) => {
              const active = option.value === value;
              return (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={active}
                  className={cn("tos-team-premium-filter-option-v4", active && "is-selected")}
                  onClick={() => {
                    onChange?.(option.value);
                    setOpen(false);
                    window.requestAnimationFrame(() => triggerRef.current?.focus());
                  }}
                >
                  <span className="truncate">{option.label}</span>
                  {active && <CheckCircle2 size={15} className="shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
'''
updated_team = updated_team.replace(component_anchor, premium_component + component_anchor, 1)

old_filters = r'''          <select value={departmentFilter} onChange={(e) => setDepartmentFilter(e.target.value)} className="rounded-xl bg-zinc-50 px-3.5 py-2.5 text-sm font-bold outline-none transition focus:ring-2 focus:ring-amber-300/30 dark:bg-zinc-950/60 dark:text-zinc-100">
            <option value="ALL">{lang === "en" ? "All Departments" : "كل الأقسام"}</option>
            {departmentOptions.map((department) => <option key={department.key} value={department.name}>{departmentLabel(department, lang)}</option>)}
          </select>
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="rounded-xl bg-zinc-50 px-3.5 py-2.5 text-sm font-bold outline-none transition focus:ring-2 focus:ring-amber-300/30 dark:bg-zinc-950/60 dark:text-zinc-100">
            <option value="ALL">{lang === "en" ? "All Roles" : "كل الأدوار"}</option>
            <option value="SUPER_ADMIN">{roleLabel("SUPER_ADMIN", lang)}</option>
            <option value="ADMIN">{roleLabel("ADMIN", lang)}</option>
            <option value="MANAGER">{roleLabel("MANAGER", lang)}</option>
            <option value="PROJECT_MANAGER">{roleLabel("PROJECT_MANAGER", lang)}</option>
            <option value="TEAM_MEMBER">{roleLabel("TEAM_MEMBER", lang)}</option>
          </select>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="rounded-xl bg-zinc-50 px-3.5 py-2.5 text-sm font-bold outline-none transition focus:ring-2 focus:ring-amber-300/30 dark:bg-zinc-950/60 dark:text-zinc-100">
            <option value="ALL">{lang === "en" ? "All Statuses" : "كل الحالات"}</option>
            <option value="ACTIVE">{statusLabel("ACTIVE", lang)}</option>
            <option value="PENDING">{statusLabel("PENDING", lang)}</option>
            <option value="DISABLED">{statusLabel("DISABLED", lang)}</option>
          </select>'''

new_filters = r'''          <TeamPremiumSelectV4
            value={departmentFilter}
            onChange={setDepartmentFilter}
            lang={lang}
            ariaLabel={lang === "en" ? "Filter by department" : "تصفية حسب القسم"}
            options={[
              { value: "ALL", label: lang === "en" ? "All Departments" : "كل الأقسام" },
              ...departmentOptions.map((department) => ({ value: department.name, label: departmentLabel(department, lang) })),
            ]}
          />
          <TeamPremiumSelectV4
            value={roleFilter}
            onChange={setRoleFilter}
            lang={lang}
            ariaLabel={lang === "en" ? "Filter by role" : "تصفية حسب الدور"}
            options={[
              { value: "ALL", label: lang === "en" ? "All Roles" : "كل الأدوار" },
              ...["SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER", "TEAM_MEMBER"].map((role) => ({ value: role, label: roleLabel(role, lang) })),
            ]}
          />
          <TeamPremiumSelectV4
            value={statusFilter}
            onChange={setStatusFilter}
            lang={lang}
            ariaLabel={lang === "en" ? "Filter by status" : "تصفية حسب الحالة"}
            options={[
              { value: "ALL", label: lang === "en" ? "All Statuses" : "كل الحالات" },
              ...["ACTIVE", "PENDING", "DISABLED"].map((status) => ({ value: status, label: statusLabel(status, lang) })),
            ]}
          />'''

if updated_team.count(old_filters) != 1:
    fail("All Team native filter select block not found exactly once")
updated_team = updated_team.replace(old_filters, new_filters, 1)

v4_css = r'''

/* =========================================================
   Phase 04.3 — Team Members — Flagship V4
   Premium All Team filter menus. Replaces native browser popup
   menus only; filtering state/business logic remains unchanged.
   ========================================================= */
:root { --tos-team-phase04-3-v4-runtime: 1; }

.tos-team-filter-trigger-v4 {
  width: 100%;
  min-height: 42px;
  border: 1px solid rgba(104,86,57,.16);
  background:
    linear-gradient(180deg, rgba(255,255,255,.98), rgba(250,247,240,.96));
  color: #39352e;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), 0 1px 2px rgba(52,41,23,.025);
  transition: border-color .16s ease, box-shadow .16s ease, background-color .16s ease, transform .16s ease;
}

.tos-team-filter-trigger-v4:hover,
.tos-team-filter-trigger-v4.is-open {
  border-color: rgba(184,137,53,.46);
  background: #fffdf8;
  box-shadow: 0 0 0 3px rgba(184,137,53,.08), inset 0 1px 0 rgba(255,255,255,.98);
}

.tos-team-filter-trigger-v4:focus-visible {
  outline: 2px solid rgba(184,137,53,.56);
  outline-offset: 2px;
}

.tos-team-premium-filter-menu-v4 {
  position: fixed;
  z-index: 160;
  overflow: hidden;
  border: 1px solid rgba(104,86,57,.18);
  border-radius: 16px;
  background:
    radial-gradient(circle at 12% 0%, rgba(213,181,104,.11), transparent 28%),
    linear-gradient(160deg, rgba(255,255,255,.995), rgba(249,245,236,.99));
  box-shadow: 0 22px 54px rgba(47,36,18,.18), 0 4px 14px rgba(47,36,18,.08), inset 0 1px 0 rgba(255,255,255,.96);
  backdrop-filter: blur(18px);
  padding: 6px;
}

.tos-team-premium-filter-menu-inner-v4 {
  max-height: inherit;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: rgba(184,137,53,.38) transparent;
}

.tos-team-premium-filter-option-v4 {
  display: flex;
  width: 100%;
  min-height: 40px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid transparent;
  border-radius: 11px;
  padding: 9px 11px;
  background: transparent;
  color: #3b3730;
  font-size: .78rem;
  font-weight: 800;
  text-align: start;
  transition: background-color .15s ease, color .15s ease, border-color .15s ease, transform .15s ease;
}

.tos-team-premium-filter-option-v4:hover,
.tos-team-premium-filter-option-v4:focus-visible {
  border-color: rgba(184,137,53,.14);
  background: rgba(184,137,53,.075);
  color: #8b641f;
  outline: none;
}

.tos-team-premium-filter-option-v4.is-selected {
  border-color: rgba(184,137,53,.22);
  background: linear-gradient(135deg, rgba(222,194,126,.20), rgba(184,137,53,.10));
  color: #775315;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.68);
}

html.dark .tos-team-filter-trigger-v4 {
  border-color: rgba(255,255,255,.10);
  background: linear-gradient(180deg, #17191e, #121419);
  color: #f0eee8;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}

html.dark .tos-team-filter-trigger-v4:hover,
html.dark .tos-team-filter-trigger-v4.is-open {
  border-color: rgba(213,181,104,.34);
  background: #191a1e;
  box-shadow: 0 0 0 3px rgba(213,181,104,.075), inset 0 1px 0 rgba(255,255,255,.03);
}

html.dark .tos-team-premium-filter-menu-v4 {
  border-color: rgba(213,181,104,.20);
  background:
    radial-gradient(circle at 12% 0%, rgba(213,181,104,.09), transparent 30%),
    linear-gradient(155deg, rgba(24,26,31,.995), rgba(12,14,18,.995));
  box-shadow: 0 26px 64px rgba(0,0,0,.52), 0 5px 18px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.035);
}

html.dark .tos-team-premium-filter-option-v4 {
  color: #d9d8d4;
}

html.dark .tos-team-premium-filter-option-v4:hover,
html.dark .tos-team-premium-filter-option-v4:focus-visible {
  border-color: rgba(213,181,104,.14);
  background: rgba(213,181,104,.075);
  color: #efd994;
}

html.dark .tos-team-premium-filter-option-v4.is-selected {
  border-color: rgba(213,181,104,.26);
  background: linear-gradient(135deg, rgba(213,181,104,.18), rgba(112,86,32,.13));
  color: #f2d98e;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.035);
}

@media (prefers-reduced-motion: reduce) {
  .tos-team-filter-trigger-v4,
  .tos-team-premium-filter-option-v4 {
    transition-duration: .01ms !important;
  }
}
'''

v4_css = "\n".join(line.rstrip() for line in v4_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v4_css

# Patch-owned whitespace checks only; do not fail on unrelated historical whitespace.
if any(line.endswith(" ") or line.endswith("\t") for line in premium_component.splitlines()):
    fail("V4 premium component contains trailing whitespace")
if any(line.endswith(" ") or line.endswith("\t") for line in new_filters.splitlines()):
    fail("V4 filter replacement contains trailing whitespace")
if any(line.endswith(" ") or line.endswith("\t") for line in v4_css.splitlines()):
    fail("V4 CSS contains trailing whitespace")

backup = None
stage = None
live_swapped = False

try:
    TEAM.write_text(updated_team)
    CSS.write_text(updated_css)

    source_team = TEAM.read_text()
    source_css = CSS.read_text()
    if source_team.count(f"function {PREMIUM_COMPONENT}") != 1:
        raise RuntimeError("premium filter component missing or duplicated")
    if source_team.count("<TeamPremiumSelectV4") != 3:
        raise RuntimeError("expected exactly three premium All Team filters")
    if 'value={departmentFilter} onChange={(e) => setDepartmentFilter(e.target.value)}' in source_team:
        raise RuntimeError("native department filter still present")
    if 'value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}' in source_team:
        raise RuntimeError("native role filter still present")
    if 'value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}' in source_team:
        raise RuntimeError("native status filter still present")
    if source_css.count(V4_MARKER) != 1:
        raise RuntimeError("source V4 marker missing or duplicated")
    for marker in (V1_MARKER, V2_MARKER, V3_MARKER):
        if source_css.count(marker) != 1:
            raise RuntimeError(f"previous marker not preserved: {marker}")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_v4 = tree_count(DIST, V4_MARKER.encode())
    component_dist = tree_count(DIST, PREMIUM_COMPONENT.encode())
    if dist_v4 < 1:
        raise RuntimeError("Phase 04.3 V4 marker missing from dist")
    if component_dist < 1:
        raise RuntimeError("premium filter component missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-3-team-v4.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-3-team-v4.backup-{stamp}"
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

    live_v4 = tree_count(LIVE, V4_MARKER.encode())
    component_live = tree_count(LIVE, PREMIUM_COMPONENT.encode())
    if live_v4 < 1 or component_live < 1:
        raise RuntimeError("Phase 04.3 V4 runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V4_RUNTIME=YES")
    print("NATIVE_ALL_TEAM_FILTER_MENUS_REPLACED=YES")
    print("DEPARTMENT_MENU_PREMIUM=YES")
    print("ROLE_MENU_PREMIUM=YES")
    print("STATUS_MENU_PREMIUM=YES")
    print("LIGHT_MENU_THEME=YES")
    print("DARK_MENU_THEME=YES")
    print("V3_EXECUTIVE_KPI_PRESERVED=YES")
    print("V2_DEPARTMENT_FIX_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V4_RUNTIME_COUNT={source_css.count(V4_MARKER)}")
    print(f"SOURCE_PREMIUM_FILTER_COMPONENT_COUNT={source_team.count(f'function {PREMIUM_COMPONENT}')}")
    print(f"SOURCE_PREMIUM_FILTER_INSTANCE_COUNT={source_team.count('<TeamPremiumSelectV4')}")
    print(f"DIST_V4_RUNTIME_COUNT={dist_v4}")
    print(f"LIVE_V4_RUNTIME_COUNT={live_v4}")
    print(f"TEAM_PAGE_SHA256={sha256(TEAM)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        TEAM.write_text(original_team)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-3-team-v4.failed.{int(time.time())}"
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
    print("V4_RUNTIME=NO")
    print(f"TEAM_PAGE_SHA256={sha256(TEAM) if TEAM.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
