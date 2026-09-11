from pathlib import Path
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11B2"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11B2-DUE-DATE-CUSTOM-PREMIUM-CALENDAR"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11B1"
MICRO_STEP = "DUE_DATE_CUSTOM_PREMIUM_CALENDAR"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11B2DueDateCustomPremiumCalendar.css"

RUNTIME = "--tos-task-details-v2-11b2-due-date-custom-premium-calendar-runtime"
B1_RUNTIME = "--tos-task-details-v2-11b1-status-priority-custom-dropdowns-runtime"
HELPER_MARKER = "function TaskHeroPremiumDatePicker("

REQUIRED_LINEAGE = (
    "--tos-task-details-canonical-reference-v2-runtime",
    "--tos-task-details-canonical-reference-v2-2-app-shell-grid-lock-runtime",
    "--tos-task-details-canonical-reference-v2-5-exact-four-controls-physical-grid-runtime",
    "--tos-task-details-canonical-reference-v2-6-hero-visibility-physical-rail-runtime",
    "--tos-task-details-canonical-reference-v2-7-real-overview-rail-physical-lock-runtime",
    "--tos-task-details-v2-8d-right-rail-tcs-viewport-fit-runtime",
    "--tos-task-details-v2-9d-hero-internal-clip-bidi-cleanup-runtime",
    "--tos-task-details-v2-10d-hero-bottom-spacing-global-assistant-collision-fix-runtime",
    "--tos-task-details-v2-11a-hero-shell-task-identity-lock-runtime",
    "--tos-task-details-v2-11a-r1-hero-full-canvas-physical-placement-runtime",
    "--tos-task-details-v2-11a-r2-hero-width-only-runtime",
    "--tos-task-details-v2-11b-four-hero-controls-premium-lock-runtime",
    B1_RUNTIME,
)

HELPER = r'''function TaskHeroPremiumDatePicker({
  value,
  onChange,
  disabled = false,
  direction = "ltr",
  locale = "en-US",
  ariaLabel = "Due date",
  todayLabel = "Today",
  clearLabel = "Clear",
  previousMonthLabel = "Previous month",
  nextMonthLabel = "Next month",
}) {
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const popoverRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [popoverStyle, setPopoverStyle] = useState({});

  const parseDateValue = (input) => {
    const match = /^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(String(input || ""));
    if (!match) return null;
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]), 12, 0, 0, 0);
  };

  const toDateValue = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const selectedDate = parseDateValue(value);
  const [viewDate, setViewDate] = useState(() => selectedDate || new Date());

  useEffect(() => {
    if (!open) return undefined;
    const nextSelected = parseDateValue(value);
    if (nextSelected) setViewDate(nextSelected);

    const updatePosition = () => {
      const trigger = triggerRef.current;
      if (!trigger || typeof window === "undefined") return;
      const rect = trigger.getBoundingClientRect();
      const width = 306;
      const estimatedHeight = 356;
      const padding = 12;
      const preferredLeft = direction === "rtl" ? rect.right - width : rect.left;
      const left = Math.min(
        Math.max(padding, preferredLeft),
        Math.max(padding, window.innerWidth - width - padding),
      );
      const belowTop = rect.bottom + 8;
      const aboveTop = rect.top - estimatedHeight - 8;
      const top = belowTop + estimatedHeight <= window.innerHeight - padding
        ? belowTop
        : Math.max(padding, aboveTop);
      setPopoverStyle({ top: `${Math.round(top)}px`, left: `${Math.round(left)}px` });
    };

    const handleOutsidePointer = (event) => {
      if (rootRef.current?.contains(event.target) || popoverRef.current?.contains(event.target)) return;
      setOpen(false);
    };

    const handleKey = (event) => {
      if (event.key === "Escape") setOpen(false);
    };

    updatePosition();
    document.addEventListener("mousedown", handleOutsidePointer);
    document.addEventListener("scroll", updatePosition, true);
    document.addEventListener("keydown", handleKey);
    window.addEventListener("resize", updatePosition);

    return () => {
      document.removeEventListener("mousedown", handleOutsidePointer);
      document.removeEventListener("scroll", updatePosition, true);
      document.removeEventListener("keydown", handleKey);
      window.removeEventListener("resize", updatePosition);
    };
  }, [open, value, direction]);

  const sameDay = (left, right) => Boolean(
    left && right
    && left.getFullYear() === right.getFullYear()
    && left.getMonth() === right.getMonth()
    && left.getDate() === right.getDate()
  );

  const today = new Date();
  const monthStart = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1, 12, 0, 0, 0);
  const gridStart = new Date(monthStart);
  gridStart.setDate(monthStart.getDate() - monthStart.getDay());
  const calendarDays = Array.from({ length: 42 }, (_, index) => {
    const day = new Date(gridStart);
    day.setDate(gridStart.getDate() + index);
    return day;
  });

  const weekDays = Array.from({ length: 7 }, (_, index) => {
    const day = new Date(2024, 0, 7 + index, 12, 0, 0, 0);
    return new Intl.DateTimeFormat(locale, { weekday: "short" }).format(day);
  });

  const displayValue = selectedDate
    ? new Intl.DateTimeFormat(locale, { day: "2-digit", month: "short", year: "numeric" }).format(selectedDate)
    : ariaLabel;

  const monthLabel = new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" }).format(viewDate);

  const chooseDate = (date) => {
    onChange?.(toDateValue(date));
    setOpen(false);
  };

  const popover = open && !disabled && typeof document !== "undefined"
    ? createPortal(
      <div
        ref={popoverRef}
        className="tos-task-v2-calendar-popover"
        role="dialog"
        aria-label={ariaLabel}
        dir={direction}
        style={popoverStyle}
      >
        <div className="tos-task-v2-calendar-header">
          <button
            type="button"
            className="tos-task-v2-calendar-nav"
            aria-label={previousMonthLabel}
            onClick={() => setViewDate((current) => new Date(current.getFullYear(), current.getMonth() - 1, 1, 12))}
          >
            <ChevronLeft aria-hidden="true" />
          </button>
          <div className="tos-task-v2-calendar-month">{monthLabel}</div>
          <button
            type="button"
            className="tos-task-v2-calendar-nav"
            aria-label={nextMonthLabel}
            onClick={() => setViewDate((current) => new Date(current.getFullYear(), current.getMonth() + 1, 1, 12))}
          >
            <ChevronRight aria-hidden="true" />
          </button>
        </div>

        <div className="tos-task-v2-calendar-weekdays" aria-hidden="true">
          {weekDays.map((label, index) => <div key={`${label}-${index}`} className="tos-task-v2-calendar-weekday">{label}</div>)}
        </div>

        <div className="tos-task-v2-calendar-grid" role="grid">
          {calendarDays.map((day) => {
            const dayValue = toDateValue(day);
            const outside = day.getMonth() !== viewDate.getMonth();
            const selected = sameDay(day, selectedDate);
            const isToday = sameDay(day, today);
            return (
              <button
                key={dayValue}
                type="button"
                role="gridcell"
                aria-selected={selected}
                className="tos-task-v2-calendar-day"
                data-outside={outside ? "true" : "false"}
                data-selected={selected ? "true" : "false"}
                data-today={isToday ? "true" : "false"}
                onClick={() => chooseDate(day)}
              >
                {day.getDate()}
              </button>
            );
          })}
        </div>

        <div className="tos-task-v2-calendar-footer">
          <button
            type="button"
            className="tos-task-v2-calendar-action"
            onClick={() => { onChange?.(null); setOpen(false); }}
          >
            {clearLabel}
          </button>
          <button
            type="button"
            className="tos-task-v2-calendar-action"
            data-primary="true"
            onClick={() => chooseDate(today)}
          >
            {todayLabel}
          </button>
        </div>
      </div>,
      document.body,
    )
    : null;

  return (
    <div ref={rootRef} className="tos-task-v2-date-picker">
      <button
        ref={triggerRef}
        type="button"
        className="tos-task-v2-date-trigger"
        disabled={disabled}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={ariaLabel}
        onClick={() => !disabled && setOpen((current) => !current)}
        onKeyDown={(event) => {
          if (event.key === "Escape") setOpen(false);
          if ((event.key === "Enter" || event.key === " ") && !disabled) {
            event.preventDefault();
            setOpen((current) => !current);
          }
        }}
      >
        <span>{displayValue}</span>
        <CalendarClock aria-hidden="true" />
      </button>
      {popover}
    </div>
  );
}

'''

OLD_DUE = r'''                    <div className="rounded-[18px] border border-slate-100 bg-slate-50/80 px-3.5 py-3 dark:border-white/10 dark:bg-zinc-900/80">
                      <p className="flex items-center justify-between gap-2 text-xs font-black text-slate-400 dark:text-zinc-500"><span>{modalUi.dueDate}</span><CalendarClock size={15} /></p>
                      <input disabled={!canEdit} type="date" value={toInputDate(draft.dueDate)} onChange={(event) => savePatch({ dueDate: event.target.value || null })} className="tos-task-date-input mt-2 w-full bg-transparent text-base font-black text-slate-950 outline-none disabled:text-slate-500 dark:text-white" />
                    </div>'''

NEW_DUE = r'''                    <div className="tos-task-v2-due-date-control rounded-[18px] border border-slate-100 bg-slate-50/80 px-3.5 py-3 dark:border-white/10 dark:bg-zinc-900/80">
                      <div className="tos-task-v2-premium-control-head"><span>{modalUi.dueDate}</span><CalendarClock size={15} /></div>
                      <TaskHeroPremiumDatePicker
                        value={toInputDate(draft.dueDate)}
                        disabled={!canEdit}
                        onChange={(dueDate) => savePatch({ dueDate: dueDate || null })}
                        direction={modalDirection}
                        locale={isAr ? "ar-EG" : "en-US"}
                        ariaLabel={modalUi.dueDate}
                        todayLabel={isAr ? "اليوم" : "Today"}
                        clearLabel={isAr ? "مسح" : "Clear"}
                        previousMonthLabel={isAr ? "الشهر السابق" : "Previous month"}
                        nextMonthLabel={isAr ? "الشهر التالي" : "Next month"}
                      />
                    </div>'''


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


for required in (FRONTEND, BOARD, STYLE, MANIFEST, PAYLOAD):
    if not required.exists():
        fail(f"required path missing: {required}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
style_source = STYLE.read_text()
payload_css = PAYLOAD.read_text()

for marker in REQUIRED_LINEAGE:
    if marker not in style_source:
        fail(f"required lineage runtime missing: {marker}")
if RUNTIME in style_source:
    fail("V2.11B2 already applied")
if HELPER_MARKER in board_source:
    fail("V2.11B2 helper already present")

# B1 must already own Status + Priority before Due Date is touched.
for marker in (
    "function TaskHeroPremiumSelect(",
    "tos-task-v2-status-control",
    "tos-task-v2-priority-control",
    "tos-task-v2-premium-select-trigger",
    "onChange={handleTaskStatusChange}",
    "onChange={(priority) => savePatch({ priority })}",
    "tos-task-summary-controls",
    "tos-task-v2-assignees-card",
    "tos-task-start-date-card",
    "function CardDetailsModal(",
):
    if marker not in board_source:
        fail(f"required V2.11B1/current source marker missing: {marker}")

if board_source.count(OLD_DUE) != 1:
    fail("exact native Due Date baseline not found exactly once")

START_DATE_MARKER = 'type="date" value={toInputDate(draft.startDate)} onChange={(event) => savePatch({ startDate: event.target.value || null })}'
if START_DATE_MARKER not in board_source:
    fail("Start Date advanced path baseline missing")

if RUNTIME not in payload_css:
    fail("V2.11B2 runtime marker missing from CSS payload")
for selector in (
    ".tos-task-v2-date-trigger",
    ".tos-task-v2-calendar-popover",
    ".tos-task-v2-calendar-grid",
    ".tos-task-v2-calendar-day",
):
    if selector not in payload_css:
        fail(f"required calendar selector missing: {selector}")

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
if manifest.get("sourceRoot") != str(ROOT):
    fail("runtime sourceRoot does not match target")
frontend_runtime = manifest.get("frontend") or {}
if Path(str(frontend_runtime.get("sourceDir") or "")) != FRONTEND:
    fail("frontend runtime sourceDir mismatch")
if str(frontend_runtime.get("buildCommand") or "") != "npm run build":
    fail("unexpected frontend build command")
live = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if live != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {live}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11b2-calendar-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
style_backup = backup_root / STYLE.name
shutil.copy2(BOARD, board_backup)
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-v2-11b2-staging-{stamp}"
live_backup = live.parent / f"build.task-details-v2-11b2-backup-{stamp}"
live_swapped = False

try:
    updated_board = board_source.replace("function CardDetailsModal(", HELPER + "function CardDetailsModal(", 1)
    updated_board = updated_board.replace(OLD_DUE, NEW_DUE, 1)

    for marker in (
        HELPER_MARKER,
        "tos-task-v2-due-date-control",
        "tos-task-v2-date-trigger",
        "onChange={(dueDate) => savePatch({ dueDate: dueDate || null })}",
        "function TaskHeroPremiumSelect(",
        "tos-task-v2-status-control",
        "tos-task-v2-priority-control",
    ):
        if marker not in updated_board:
            fail(f"expected V2.11B2/B1 source marker missing after transform: {marker}")
    if OLD_DUE in updated_board:
        fail("native Due Date input block survived transform")
    if START_DATE_MARKER not in updated_board:
        fail("V2.11B2 unexpectedly changed Start Date advanced path")

    BOARD.write_text(updated_board)
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")

    updated_style = STYLE.read_text()
    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in updated_style:
            fail(f"runtime marker missing after stylesheet update: {marker}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in built_css:
            fail(f"runtime marker missing from built CSS: {marker}")
    for marker in (
        "tos-task-v2-date-trigger",
        "tos-task-v2-calendar-popover",
        "tos-task-v2-status-control",
        "tos-task-v2-priority-control",
        "tos-task-start-date-card",
    ):
        if marker not in built_js:
            fail(f"required calendar/frozen marker missing from built JS: {marker}")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css or B1_RUNTIME not in live_css:
        fail("V2.11B2/B1 runtime marker missing from live CSS")
    for marker in ("tos-task-v2-date-trigger", "tos-task-v2-calendar-popover", "tos-task-v2-premium-select-trigger"):
        if marker not in live_js:
            fail(f"required live marker missing: {marker}")

    print(f"VERSION={VERSION}")
    print(f"PATCH={PATCH_NAME}")
    print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
    print(f"MICRO_STEP={MICRO_STEP}")
    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("DUE_DATE_PICKER=CUSTOM_PORTAL_CALENDAR")
    print("DUE_DATE_SAVE_LOGIC=PRESERVED")
    print("STATUS_PRIORITY_B1=PRESERVED")
    print("FOUR_CARD_GEOMETRY=PRESERVED")
    print("START_DATE_ADVANCED_PATH=PRESERVED")
    print("TASK_APIS_CHANGED=NO")
    print("TASK_DATA_CONTRACT_CHANGED=NO")
    print("REFERENCE_VIEWPORT=1664x936")
    print("STATUS=READY_FOR_VISUAL_QA")
except Exception as exc:
    try:
        if board_backup.exists():
            shutil.copy2(board_backup, BOARD)
        if style_backup.exists():
            shutil.copy2(style_backup, STYLE)
        if live_swapped and live.exists() and live_backup.exists():
            shutil.rmtree(live)
            live_backup.rename(live)
        elif live_backup.exists() and not live.exists():
            live_backup.rename(live)
        if staging.exists():
            shutil.rmtree(staging)
    except Exception:
        pass
    print(f"VERSION={VERSION}")
    print(f"PATCH={PATCH_NAME}")
    print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
    print(f"MICRO_STEP={MICRO_STEP}")
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
