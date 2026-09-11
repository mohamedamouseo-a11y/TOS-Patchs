from pathlib import Path
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11B3"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11B3-ASSIGNEES-CUSTOM-SELECTOR"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11B2"
MICRO_STEP = "ASSIGNEES_CUSTOM_SELECTOR"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11B3AssigneesCustomSelector.css"

RUNTIME = "--tos-task-details-v2-11b3-assignees-custom-selector-runtime"
B2_RUNTIME = "--tos-task-details-v2-11b2-due-date-custom-premium-calendar-runtime"
HELPER_MARKER = "function TaskHeroPremiumAssigneePicker("

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
    "--tos-task-details-v2-11b1-status-priority-custom-dropdowns-runtime",
    B2_RUNTIME,
)

HELPER = r'''function TaskHeroPremiumAssigneePicker({
  selectedIds = [],
  members = [],
  onToggle,
  disabled = false,
  saving = false,
  error = "",
  direction = "ltr",
  isAr = false,
}) {
  const triggerRef = useRef(null);
  const popoverRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [popoverStyle, setPopoverStyle] = useState({});

  const selectedSet = useMemo(() => new Set((selectedIds || []).map((id) => String(id))), [selectedIds]);
  const normalizedQuery = useMemo(() => normalizeTaskAssigneeSearchText(query), [query]);
  const filteredMembers = useMemo(() => {
    const source = Array.isArray(members) ? members : [];
    return source
      .map((member, index) => {
        const memberUser = member?.user;
        const userId = String(memberUser?.id || "");
        if (!userId) return null;
        const name = getPersonLabel(memberUser) || memberUser?.email || (isAr ? "مستخدم" : "User");
        const email = String(memberUser?.email || "");
        const department = String(memberUser?.department || "");
        const role = String(memberUser?.role || member?.role || "");
        const haystack = normalizeTaskAssigneeSearchText([name, email, humanizeEnum(department), humanizeEnum(role)].filter(Boolean).join(" "));
        if (normalizedQuery && !haystack.includes(normalizedQuery)) return null;
        return {
          member,
          user: memberUser,
          userId,
          name,
          index,
          selected: selectedSet.has(userId),
          meta: [email, department ? humanizeEnum(department) : ""].filter(Boolean).join(" · "),
        };
      })
      .filter(Boolean)
      .sort((a, b) => Number(b.selected) - Number(a.selected) || a.name.localeCompare(b.name, undefined, { sensitivity: "base" }) || a.index - b.index);
  }, [members, normalizedQuery, selectedSet, isAr]);

  useEffect(() => {
    if (!open) return undefined;

    const updatePosition = () => {
      const trigger = triggerRef.current;
      if (!trigger || typeof window === "undefined") return;
      const rect = trigger.getBoundingClientRect();
      const width = 336;
      const estimatedHeight = Math.min(480, Math.max(240, filteredMembers.length * 52 + 116));
      const padding = 12;
      const preferredLeft = direction === "rtl" ? rect.right - width : rect.left;
      const left = Math.min(Math.max(padding, preferredLeft), Math.max(padding, window.innerWidth - width - padding));
      const belowTop = rect.bottom + 8;
      const aboveTop = rect.top - estimatedHeight - 8;
      const top = belowTop + estimatedHeight <= window.innerHeight - padding ? belowTop : Math.max(padding, aboveTop);
      setPopoverStyle({ top: `${Math.round(top)}px`, left: `${Math.round(left)}px` });
    };

    const handleOutsidePointer = (event) => {
      if (triggerRef.current?.contains(event.target) || popoverRef.current?.contains(event.target)) return;
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
  }, [open, filteredMembers.length, direction]);

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  const selectedUsers = (selectedIds || []).slice(0, 3).map((id) => {
    const match = (members || []).find((member) => String(member?.user?.id || "") === String(id));
    const memberUser = match?.user;
    const name = getPersonLabel(memberUser) || memberUser?.email || (isAr ? "مستخدم" : "User");
    return { id: String(id), name };
  });

  const popover = open && !disabled && typeof document !== "undefined"
    ? createPortal(
      <div ref={popoverRef} className="tos-task-v2-assignee-popover" dir={direction} style={popoverStyle} role="dialog" aria-label={isAr ? "اختيار المكلفين" : "Select assignees"}>
        <div className="tos-task-v2-assignee-popover-head">
          <div>
            <strong>{isAr ? "المكلفون" : "Assignees"}</strong>
            <span>{selectedSet.size} {isAr ? "محدد" : selectedSet.size === 1 ? "selected" : "selected"}</span>
          </div>
          <Users size={17} aria-hidden="true" />
        </div>
        <label className="tos-task-v2-assignee-search">
          <Search aria-hidden="true" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={isAr ? "ابحث بالاسم أو البريد أو القسم..." : "Search name, email or department..."}
            autoFocus
          />
        </label>
        {saving && <div className="tos-task-v2-assignee-saving">{isAr ? "جارٍ حفظ المكلفين..." : "Saving assignees..."}</div>}
        {error && <div className="tos-task-v2-assignee-error">{error}</div>}
        <div className="tos-task-v2-assignee-list">
          {filteredMembers.length ? filteredMembers.map(({ user, userId, name, selected, meta }) => (
            <button
              key={userId}
              type="button"
              className="tos-task-v2-assignee-option"
              data-selected={selected ? "true" : "false"}
              onClick={() => onToggle?.(userId, !selected)}
              disabled={saving}
            >
              <span className="tos-task-v2-assignee-option-avatar">{getInitials(name)}</span>
              <span className="tos-task-v2-assignee-option-copy">
                <strong>{name}</strong>
                <span>{meta || user?.jobTitle || user?.position || (isAr ? "عضو فريق" : "Team member")}</span>
              </span>
              <span className="tos-task-v2-assignee-option-check" aria-hidden="true">{selected && <CheckCircle2 />}</span>
            </button>
          )) : <div className="tos-task-v2-assignee-empty">{isAr ? "لا توجد نتائج مطابقة." : "No matching team members."}</div>}
        </div>
      </div>,
      document.body,
    )
    : null;

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className="tos-task-v2-assignee-picker-trigger"
        disabled={disabled}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => !disabled && setOpen((current) => !current)}
      >
        <span className="tos-task-v2-assignee-picker-summary">
          <span className="tos-task-v2-avatar-stack" aria-hidden="true">
            {selectedUsers.map(({ id, name }) => <span key={id} className="tos-task-v2-assignee-avatar">{getInitials(name)}</span>)}
            <span className="tos-task-v2-assignee-add">+</span>
          </span>
          <span className="tos-task-v2-assignee-picker-count">{selectedIds.length} {isAr ? "مكلف" : selectedIds.length === 1 ? "assignee" : "assignees"}</span>
        </span>
        <ChevronDown aria-hidden="true" />
      </button>
      {popover}
    </>
  );
}

'''

NEW_ASSIGNEE = r'''                    <div className="tos-task-v2-assignees-card">
                      <div className="tos-task-v2-control-label">{isAr ? "المكلفون" : "Assignees"}</div>
                      <TaskHeroPremiumAssigneePicker
                        selectedIds={currentAssigneeIds}
                        members={visibleProjectScopedAssigneeMembers}
                        onToggle={toggleTaskAssignee}
                        disabled={!canManageTaskAssignees}
                        saving={assigneeSaving}
                        error={assigneeSaveError}
                        direction={modalDirection}
                        isAr={isAr}
                      />
                    </div>
'''

ASSIGNEE_START = '                    <div className="tos-task-v2-assignees-card">'
STATUS_START = '                    <div className="tos-task-v2-status-control'


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
    fail("V2.11B3 already applied")
if HELPER_MARKER in board_source:
    fail("V2.11B3 helper already present")

for marker in (
    "function TaskHeroPremiumSelect(",
    "function TaskHeroPremiumDatePicker(",
    "tos-task-v2-status-control",
    "tos-task-v2-priority-control",
    "tos-task-v2-due-date-control",
    "function toggleTaskAssignee(userId, checked)",
    "function enqueueAssigneeSave(nextIds)",
    "visibleProjectScopedAssigneeMembers",
    "currentAssigneeIds",
    "canManageTaskAssignees",
    "assigneeSaving",
    "assigneeSaveError",
):
    if marker not in board_source:
        fail(f"required current Task Details assignee marker missing: {marker}")

if board_source.count(ASSIGNEE_START) != 1:
    fail("Assignees card start marker not found exactly once")
if board_source.count(STATUS_START) != 1:
    fail("B1 Status control marker not found exactly once")
assignee_start = board_source.index(ASSIGNEE_START)
status_start = board_source.index(STATUS_START, assignee_start)
if status_start <= assignee_start:
    fail("invalid Assignees/Status source ordering")
old_assignee_block = board_source[assignee_start:status_start]
for marker in ("tos-task-v2-assignee-content", "tos-task-v2-avatar-stack", "setTaskSidebarExpanded(true)"):
    if marker not in old_assignee_block:
        fail(f"unexpected Assignees baseline; missing {marker}")

if RUNTIME not in payload_css:
    fail("V2.11B3 runtime marker missing from CSS payload")
for selector in (".tos-task-v2-assignee-picker-trigger", ".tos-task-v2-assignee-popover", ".tos-task-v2-assignee-option"):
    if selector not in payload_css:
        fail(f"required V2.11B3 selector missing: {selector}")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11b3-assignees-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
style_backup = backup_root / STYLE.name
shutil.copy2(BOARD, board_backup)
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-v2-11b3-staging-{stamp}"
live_backup = live.parent / f"build.task-details-v2-11b3-backup-{stamp}"
live_swapped = False

try:
    updated_board = board_source.replace("function CardDetailsModal(", HELPER + "function CardDetailsModal(", 1)
    updated_board = updated_board[:assignee_start + len(HELPER)] if False else updated_board
    # Recalculate markers after helper insertion; helper is before CardDetailsModal and therefore before the card.
    new_assignee_start = updated_board.index(ASSIGNEE_START)
    new_status_start = updated_board.index(STATUS_START, new_assignee_start)
    updated_board = updated_board[:new_assignee_start] + NEW_ASSIGNEE + updated_board[new_status_start:]

    for marker in (
        HELPER_MARKER,
        "tos-task-v2-assignee-picker-trigger",
        "tos-task-v2-assignee-popover",
        "members={visibleProjectScopedAssigneeMembers}",
        "onToggle={toggleTaskAssignee}",
        "function TaskHeroPremiumSelect(",
        "function TaskHeroPremiumDatePicker(",
    ):
        if marker not in updated_board:
            fail(f"expected V2.11B3 source marker missing after transform: {marker}")
    if "setTaskSidebarExpanded(true)" in updated_board[new_assignee_start:updated_board.index(STATUS_START, new_assignee_start)]:
        fail("legacy Assignees add-button interaction survived V2.11B3 card transform")

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
    for marker in ("tos-task-v2-assignee-picker-trigger", "tos-task-v2-assignee-popover", "tos-task-v2-status-control", "tos-task-v2-due-date-control"):
        if marker not in built_js:
            fail(f"required runtime source marker missing from built JS: {marker}")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css or B2_RUNTIME not in live_css:
        fail("V2.11B3/B2 runtime marker missing from live CSS")
    for marker in ("tos-task-v2-assignee-picker-trigger", "tos-task-v2-assignee-popover", "tos-task-v2-premium-select-trigger", "tos-task-v2-date-trigger"):
        if marker not in live_js:
            fail(f"required live JS marker missing: {marker}")

    print(f"VERSION={VERSION}")
    print(f"PATCH={PATCH_NAME}")
    print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
    print(f"MICRO_STEP={MICRO_STEP}")
    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("ASSIGNEES_SELECTOR=CUSTOM_PORTAL_SELECTOR")
    print("ASSIGNEE_SAVE_LOGIC=PRESERVED")
    print("STATUS_PRIORITY_B1=PRESERVED")
    print("DUE_DATE_B2=PRESERVED")
    print("STATUS=READY_FOR_VISUAL_QA")
except Exception as exc:
    try:
        shutil.copy2(board_backup, BOARD)
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
