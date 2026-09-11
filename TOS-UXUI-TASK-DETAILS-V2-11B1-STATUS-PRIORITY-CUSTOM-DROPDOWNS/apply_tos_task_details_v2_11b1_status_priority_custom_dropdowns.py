from pathlib import Path
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11B1"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11B1-STATUS-PRIORITY-CUSTOM-DROPDOWNS"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11B"
MICRO_STEP = "STATUS_PRIORITY_CUSTOM_DROPDOWNS"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11B1StatusPriorityCustomDropdowns.css"

RUNTIME = "--tos-task-details-v2-11b1-status-priority-custom-dropdowns-runtime"
V211B_RUNTIME = "--tos-task-details-v2-11b-four-hero-controls-premium-lock-runtime"
HELPER_MARKER = "function TaskHeroPremiumSelect("

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
    V211B_RUNTIME,
)

HELPER = r'''function TaskHeroPremiumSelect({
  value,
  options = [],
  onChange,
  disabled = false,
  formatOption = (option) => String(option ?? ""),
  tone = "neutral",
  direction = "ltr",
  ariaLabel = "",
}) {
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(() => Math.max(0, options.indexOf(value)));
  const [menuStyle, setMenuStyle] = useState({});

  const chooseOption = (nextValue) => {
    setOpen(false);
    if (nextValue !== value) onChange?.(nextValue);
  };

  useEffect(() => {
    if (!open) return undefined;

    setActiveIndex(Math.max(0, options.indexOf(value)));

    const updateMenuPosition = () => {
      const trigger = triggerRef.current;
      if (!trigger || typeof window === "undefined") return;
      const rect = trigger.getBoundingClientRect();
      const viewportPadding = 12;
      const width = Math.max(190, rect.width);
      const estimatedHeight = Math.max(48, (options.length * 36) + 12);
      const left = Math.min(
        Math.max(viewportPadding, rect.left),
        Math.max(viewportPadding, window.innerWidth - width - viewportPadding),
      );
      const belowTop = rect.bottom + 7;
      const aboveTop = rect.top - estimatedHeight - 7;
      const top = belowTop + estimatedHeight <= window.innerHeight - viewportPadding
        ? belowTop
        : Math.max(viewportPadding, aboveTop);
      setMenuStyle({ top: `${Math.round(top)}px`, left: `${Math.round(left)}px`, width: `${Math.round(width)}px` });
    };

    const handleOutsidePointer = (event) => {
      if (rootRef.current?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setOpen(false);
    };

    const handleGlobalKey = (event) => {
      if (event.key === "Escape") setOpen(false);
    };

    updateMenuPosition();
    document.addEventListener("mousedown", handleOutsidePointer);
    document.addEventListener("scroll", updateMenuPosition, true);
    document.addEventListener("keydown", handleGlobalKey);
    window.addEventListener("resize", updateMenuPosition);

    return () => {
      document.removeEventListener("mousedown", handleOutsidePointer);
      document.removeEventListener("scroll", updateMenuPosition, true);
      document.removeEventListener("keydown", handleGlobalKey);
      window.removeEventListener("resize", updateMenuPosition);
    };
  }, [open, options, value]);

  const handleTriggerKeyDown = (event) => {
    if (disabled || !options.length) return;
    const currentIndex = Math.max(0, options.indexOf(value));

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const directionStep = event.key === "ArrowDown" ? 1 : -1;
      if (!open) {
        setOpen(true);
        setActiveIndex(currentIndex);
        return;
      }
      setActiveIndex((previous) => (previous + directionStep + options.length) % options.length);
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (!open) {
        setOpen(true);
        setActiveIndex(currentIndex);
      } else if (options[activeIndex] !== undefined) {
        chooseOption(options[activeIndex]);
      }
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
    }
  };

  const menu = open && !disabled && typeof document !== "undefined"
    ? createPortal(
      <div
        ref={menuRef}
        className="tos-task-v2-premium-menu"
        data-tone={tone}
        role="listbox"
        aria-label={ariaLabel}
        dir={direction}
        style={menuStyle}
      >
        {options.map((option, index) => {
          const selected = option === value;
          return (
            <button
              key={String(option)}
              type="button"
              role="option"
              aria-selected={selected}
              className="tos-task-v2-premium-option"
              data-active={index === activeIndex ? "true" : "false"}
              data-selected={selected ? "true" : "false"}
              onMouseEnter={() => setActiveIndex(index)}
              onClick={() => chooseOption(option)}
            >
              <span>{formatOption(option)}</span>
              {selected && <span className="tos-task-v2-premium-option-check" aria-hidden="true"><CheckCircle2 /></span>}
            </button>
          );
        })}
      </div>,
      document.body,
    )
    : null;

  return (
    <div ref={rootRef} className="tos-task-v2-premium-select" data-tone={tone}>
      <button
        ref={triggerRef}
        type="button"
        className="tos-task-v2-premium-select-trigger"
        disabled={disabled}
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        onClick={() => !disabled && setOpen((current) => !current)}
        onKeyDown={handleTriggerKeyDown}
      >
        <span>{formatOption(value)}</span>
        <ChevronDown aria-hidden="true" />
      </button>
      {menu}
    </div>
  );
}

'''

OLD_STATUS = r'''                    <label className="rounded-[18px] border border-slate-100 bg-white px-3.5 py-3 shadow-sm dark:border-white/10 dark:bg-zinc-900">
                      <span className="mb-2 flex items-center justify-between gap-2 text-xs font-black text-slate-400 dark:text-zinc-500"><span>{modalUi.status || (isAr ? "الحالة" : "Status")}</span><List size={15} /></span>
                      <select disabled={!canEdit} value={draft.status || "TODO"} onChange={(event) => handleTaskStatusChange(event.target.value)} className={`${referenceSelectClass} w-full`}>
                        {referenceStatusOptions.map((status) => <option key={status} value={status}>{displayTaskSystemName(status, modalUi)}</option>)}
                      </select>
                    </label>'''

NEW_STATUS = r'''                    <div className="tos-task-v2-status-control rounded-[18px] border border-slate-100 bg-white px-3.5 py-3 shadow-sm dark:border-white/10 dark:bg-zinc-900">
                      <div className="tos-task-v2-premium-control-head"><span>{modalUi.status || (isAr ? "الحالة" : "Status")}</span><List size={15} /></div>
                      <TaskHeroPremiumSelect
                        value={draft.status || "TODO"}
                        options={referenceStatusOptions}
                        disabled={!canEdit}
                        onChange={handleTaskStatusChange}
                        formatOption={(status) => displayTaskSystemName(status, modalUi)}
                        tone="status"
                        direction={modalDirection}
                        ariaLabel={modalUi.status || (isAr ? "الحالة" : "Status")}
                      />
                    </div>'''

OLD_PRIORITY = r'''                    <label className="rounded-[18px] border border-amber-100 bg-amber-50/40 px-3.5 py-3 shadow-sm dark:border-amber-400/20 dark:bg-amber-500/10">
                      <span className="mb-2 flex items-center justify-between gap-2 text-xs font-black text-slate-400 dark:text-zinc-500"><span>{modalUi.priority}</span><Flag size={15} /></span>
                      <select disabled={!canEdit} value={draft.priority || "MEDIUM"} onChange={(event) => savePatch({ priority: event.target.value })} className={`${referenceSelectClass} w-full`}>
                        {priorityOptions.map((priority) => <option key={priority} value={priority}>{formatPriorityLabel(priority, modalUi)}</option>)}
                      </select>
                    </label>'''

NEW_PRIORITY = r'''                    <div className="tos-task-v2-priority-control rounded-[18px] border border-amber-100 bg-amber-50/40 px-3.5 py-3 shadow-sm dark:border-amber-400/20 dark:bg-amber-500/10">
                      <div className="tos-task-v2-premium-control-head"><span>{modalUi.priority}</span><Flag size={15} /></div>
                      <TaskHeroPremiumSelect
                        value={draft.priority || "MEDIUM"}
                        options={priorityOptions}
                        disabled={!canEdit}
                        onChange={(priority) => savePatch({ priority })}
                        formatOption={(priority) => formatPriorityLabel(priority, modalUi)}
                        tone="priority"
                        direction={modalDirection}
                        ariaLabel={modalUi.priority}
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
    fail("V2.11B1 already applied")
if HELPER_MARKER in board_source:
    fail("V2.11B1 helper already present")

for marker in (
    "tos-task-summary-controls",
    "tos-task-v2-assignees-card",
    "tos-task-date-input",
    "tos-task-start-date-card",
    "referenceStatusOptions",
    "handleTaskStatusChange",
    "priorityOptions",
    "savePatch",
    "function CardDetailsModal(",
):
    if marker not in board_source:
        fail(f"required current Task Details source marker missing: {marker}")

if board_source.count(OLD_STATUS) != 1:
    fail("exact native Status select baseline not found exactly once")
if board_source.count(OLD_PRIORITY) != 1:
    fail("exact native Priority select baseline not found exactly once")
if RUNTIME not in payload_css:
    fail("V2.11B1 runtime marker missing from CSS payload")

# Frozen controls that must remain native/unchanged in this micro-step.
DUE_DATE_MARKER = 'type="date" value={toInputDate(draft.dueDate)} onChange={(event) => savePatch({ dueDate: event.target.value || null })}'
START_DATE_MARKER = 'type="date" value={toInputDate(draft.startDate)} onChange={(event) => savePatch({ startDate: event.target.value || null })}'
if DUE_DATE_MARKER not in board_source or START_DATE_MARKER not in board_source:
    fail("Due Date / Start Date frozen baseline marker missing")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11b1-dropdowns-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
style_backup = backup_root / STYLE.name
shutil.copy2(BOARD, board_backup)
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-v2-11b1-staging-{stamp}"
live_backup = live.parent / f"build.task-details-v2-11b1-backup-{stamp}"
live_swapped = False

try:
    updated_board = board_source.replace("function CardDetailsModal(", HELPER + "function CardDetailsModal(", 1)
    updated_board = updated_board.replace(OLD_STATUS, NEW_STATUS, 1)
    updated_board = updated_board.replace(OLD_PRIORITY, NEW_PRIORITY, 1)

    if HELPER_MARKER not in updated_board:
        fail("custom dropdown helper insertion failed")
    for marker in (
        "tos-task-v2-status-control",
        "tos-task-v2-priority-control",
        "tos-task-v2-premium-select-trigger",
        "onChange={handleTaskStatusChange}",
        "onChange={(priority) => savePatch({ priority })}",
    ):
        if marker not in updated_board:
            fail(f"expected V2.11B1 source marker missing after transform: {marker}")
    if OLD_STATUS in updated_board or OLD_PRIORITY in updated_board:
        fail("native Status/Priority select block survived transform")
    if DUE_DATE_MARKER not in updated_board or START_DATE_MARKER not in updated_board:
        fail("V2.11B1 unexpectedly changed Due Date / Start Date logic")

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
        "tos-task-v2-premium-select-trigger",
        "tos-task-v2-premium-menu",
        "tos-task-v2-status-control",
        "tos-task-v2-priority-control",
        "tos-task-date-input",
    ):
        if marker not in built_js:
            fail(f"required V2.11B1 marker missing from built JS: {marker}")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css or V211B_RUNTIME not in live_css:
        fail("V2.11B1/V2.11B runtime marker missing from live CSS")
    for marker in (
        "tos-task-v2-premium-select-trigger",
        "tos-task-v2-premium-menu",
        "tos-task-v2-status-control",
        "tos-task-v2-priority-control",
    ):
        if marker not in live_js:
            fail(f"required V2.11B1 marker missing from live JS: {marker}")

    print(f"VERSION={VERSION}")
    print(f"PATCH={PATCH_NAME}")
    print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
    print(f"MICRO_STEP={MICRO_STEP}")
    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("STATUS_DROPDOWN=CUSTOM_PORTAL_LISTBOX")
    print("PRIORITY_DROPDOWN=CUSTOM_PORTAL_LISTBOX")
    print("OUTSIDE_CLICK=SUPPORTED")
    print("ESCAPE_CLOSE=SUPPORTED")
    print("KEYBOARD_ARROWS_ENTER=SUPPORTED")
    print("STATUS_SAVE_LOGIC=PRESERVED_HANDLE_TASK_STATUS_CHANGE")
    print("PRIORITY_SAVE_LOGIC=PRESERVED_SAVE_PATCH")
    print("DUE_DATE_CHANGED=NO")
    print("START_DATE_CHANGED=NO")
    print("HERO_SHELL_CHANGED=NO")
    print("FOUR_CARD_GEOMETRY_CHANGED=NO")
    print("APIS_CHANGED=NO")
    print("DB_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
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
