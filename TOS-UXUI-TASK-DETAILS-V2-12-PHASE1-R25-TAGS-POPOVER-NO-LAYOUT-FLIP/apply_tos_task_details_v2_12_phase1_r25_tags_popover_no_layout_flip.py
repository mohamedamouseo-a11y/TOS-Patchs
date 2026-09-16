from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R25-TAGS-POPOVER-NO-LAYOUT-FLIP"
R24_MARKER = "--tos-task-details-v2-12-phase1-r24-assignee-floating-dropdown-runtime"
R25_MARKER = "--tos-task-details-v2-12-phase1-r25-tags-popover-no-layout-flip-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R24_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R24AssigneeFloatingDropdown.css"
R25_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R25TagsPopoverNoLayoutFlip.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PAYLOAD = Path(__file__).resolve().parent / "taskDetailsV2_12_Phase1R25TagsPopoverNoLayoutFlip.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R24_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r24_source = R24_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R24_MARKER not in r24_source:
    fail("R24 production baseline marker missing")
if R25_STYLE.exists() or R25_MARKER in board_source:
    fail("R25 already appears applied")
if R25_MARKER not in payload_css:
    fail("R25 payload marker missing")

required_contracts = (
    'const [newLabel, setNewLabel] = useState({ name: "", color: "#64748b" });',
    'const canManageLabels = Boolean(cardPermissions.canManageLabels || permissions?.canManageLabels);',
    'async function toggleLabel(label) {',
    'async function createLabel(event) {',
    'className="tos-task-v2-tag-plus"',
    'setTaskMoreDetailsOpen(true); setTaskSidebarExpanded(true);',
    'import "../styles/taskDetailsV2_12_Phase1R24AssigneeFloatingDropdown.css";',
)
for contract in required_contracts:
    if contract not in board_source:
        fail(f"R25 source contract missing: {contract}")

updated = board_source

# 1) Local Tags-popover state. No relation to Advanced/Tracking Time state.
old_state = '  const [newLabel, setNewLabel] = useState({ name: "", color: "#64748b" });'
new_state = '''  const [newLabel, setNewLabel] = useState({ name: "", color: "#64748b" });
  // TOS_TASK_DETAILS_R25_TAGS_POPOVER_NO_LAYOUT_FLIP
  const [tagPopoverOpen, setTagPopoverOpen] = useState(false);
  const [tagQuery, setTagQuery] = useState("");
  const [tagPopoverStyle, setTagPopoverStyle] = useState({});'''
if updated.count(old_state) != 1:
    fail(f"expected one newLabel state anchor, found {updated.count(old_state)}")
updated = updated.replace(old_state, new_state, 1)

# 2) Popover refs live beside existing modal refs.
old_refs = '''  const modalRef = useRef(null);
  const closeButtonRef = useRef(null);
  const taskDetailsBodyRef = useRef(null);'''
new_refs = '''  const modalRef = useRef(null);
  const closeButtonRef = useRef(null);
  const taskDetailsBodyRef = useRef(null);
  const tagPopoverRef = useRef(null);
  const tagPopoverTriggerRef = useRef(null);'''
if updated.count(old_refs) != 1:
    fail(f"expected one modal refs anchor, found {updated.count(old_refs)}")
updated = updated.replace(old_refs, new_refs, 1)

# 3) Filter + floating lifecycle. Reposition on Task scroll/viewport resize; outside click/Escape close.
old_manage = '  const canManageLabels = Boolean(cardPermissions.canManageLabels || permissions?.canManageLabels);'
new_manage = '''  const canManageLabels = Boolean(cardPermissions.canManageLabels || permissions?.canManageLabels);
  const filteredTaskLabels = useMemo(() => {
    const query = String(tagQuery || "").trim().toLocaleLowerCase();
    const source = Array.isArray(labels) ? labels : [];
    if (!query) return source;
    return source.filter((label) => String(label?.name || "").toLocaleLowerCase().includes(query));
  }, [labels, tagQuery]);

  useEffect(() => {
    if (!tagPopoverOpen) return undefined;

    const handleOutsidePointer = (event) => {
      if (tagPopoverTriggerRef.current?.contains(event.target) || tagPopoverRef.current?.contains(event.target)) return;
      setTagPopoverOpen(false);
    };
    const handleKey = (event) => {
      if (event.key === "Escape") setTagPopoverOpen(false);
    };
    const reposition = () => updateTagPopoverPosition();

    reposition();
    document.addEventListener("mousedown", handleOutsidePointer);
    document.addEventListener("keydown", handleKey);
    document.addEventListener("scroll", reposition, true);
    window.addEventListener("resize", reposition);
    return () => {
      document.removeEventListener("mousedown", handleOutsidePointer);
      document.removeEventListener("keydown", handleKey);
      document.removeEventListener("scroll", reposition, true);
      window.removeEventListener("resize", reposition);
    };
  }, [tagPopoverOpen, filteredTaskLabels.length, modalDirection]);

  useEffect(() => {
    setTagPopoverOpen(false);
    setTagQuery("");
  }, [task?.id]);'''
if updated.count(old_manage) != 1:
    fail(f"expected one canManageLabels anchor, found {updated.count(old_manage)}")
updated = updated.replace(old_manage, new_manage, 1)

# 4) Position/open helpers and create+assign behavior.
old_toggle = '''  async function toggleLabel(label) {
    const hasLabel = draft.labels?.some((item) => item.id === label.id);
    await run(() => hasLabel ? tasksApi.removeLabelFromTask(task.id, label.id) : tasksApi.addLabelToTask(task.id, label.id));
  }

  async function createLabel(event) {
    event.preventDefault();
    if (!newLabel.name.trim() || !canManageLabels) return;
    const label = await tasksApi.createLabel(task.projectId, { ...newLabel, boardId: task.boardId });
    onLabelCreated(label);
    setNewLabel({ name: "", color: "#64748b" });
  }'''
new_toggle = '''  function updateTagPopoverPosition() {
    const trigger = tagPopoverTriggerRef.current;
    if (!trigger || typeof window === "undefined") return;
    const rect = trigger.getBoundingClientRect();
    const padding = 12;
    const width = Math.min(320, Math.max(240, window.innerWidth - (padding * 2)));
    const desiredHeight = Math.min(420, Math.max(220, (filteredTaskLabels.length * 38) + (canManageLabels ? 150 : 102)));
    const preferredLeft = modalDirection === "rtl" ? rect.right - width : rect.left;
    const left = Math.min(Math.max(padding, preferredLeft), Math.max(padding, window.innerWidth - width - padding));
    const spaceBelow = Math.max(0, window.innerHeight - rect.bottom - padding - 8);
    const spaceAbove = Math.max(0, rect.top - padding - 8);
    const openBelow = spaceBelow >= Math.min(desiredHeight, 240) || spaceBelow >= spaceAbove;
    const availableHeight = Math.min(desiredHeight, Math.max(160, openBelow ? spaceBelow : spaceAbove));
    const top = openBelow
      ? Math.max(padding, Math.min(rect.bottom + 8, window.innerHeight - availableHeight - padding))
      : Math.max(padding, rect.top - availableHeight - 8);
    setTagPopoverStyle({
      top: `${Math.round(top)}px`,
      left: `${Math.round(left)}px`,
      width: `${Math.round(width)}px`,
      maxHeight: `${Math.max(160, Math.floor(availableHeight))}px`,
    });
  }

  function openTagPopover(event) {
    tagPopoverTriggerRef.current = event.currentTarget;
    setTagQuery("");
    setTagPopoverOpen(true);
    window.requestAnimationFrame(updateTagPopoverPosition);
  }

  async function toggleLabel(label) {
    const hasLabel = draft.labels?.some((item) => item.id === label.id);
    await run(() => hasLabel ? tasksApi.removeLabelFromTask(task.id, label.id) : tasksApi.addLabelToTask(task.id, label.id));
  }

  async function createLabel(event) {
    event.preventDefault();
    if (!newLabel.name.trim() || !canManageLabels) return;
    const label = await tasksApi.createLabel(task.projectId, { ...newLabel, boardId: task.boardId });
    onLabelCreated(label);
    await run(() => tasksApi.addLabelToTask(task.id, label.id));
    setNewLabel({ name: "", color: "#64748b" });
    setTagQuery("");
  }'''
if updated.count(old_toggle) != 1:
    fail(f"expected one label functions block, found {updated.count(old_toggle)}")
updated = updated.replace(old_toggle, new_toggle, 1)

# 5) Add Tag / plus open only the Tags portal. They no longer mutate Advanced/Tracking Time layout state.
old_handler = 'onClick={() => { setTaskMoreDetailsOpen(true); setTaskSidebarExpanded(true); }}'
handler_count = updated.count(old_handler)
if handler_count != 2:
    fail(f"expected exactly two Add Tag advanced-rail handlers, found {handler_count}")
updated = updated.replace(old_handler, 'onClick={openTagPopover}', 2)

# 6) Render portal in document.body so it cannot change Task Details geometry.
root_anchor = '    <div className="tos-task-details-fullpage tos-task-details-reference-v1 tos-task-details-reference-v2 fixed inset-0 z-50 overflow-hidden bg-gradient-to-br from-[#fafaf9] via-white to-amber-50/20 p-0 dark:from-zinc-950 dark:via-zinc-950 dark:to-amber-950/10" dir={modalDirection} data-content-dir={modalDirection}>'
portal_block = '''    <div className="tos-task-details-fullpage tos-task-details-reference-v1 tos-task-details-reference-v2 fixed inset-0 z-50 overflow-hidden bg-gradient-to-br from-[#fafaf9] via-white to-amber-50/20 p-0 dark:from-zinc-950 dark:via-zinc-950 dark:to-amber-950/10" dir={modalDirection} data-content-dir={modalDirection}>
      {tagPopoverOpen && typeof document !== "undefined" ? createPortal(
        <div ref={tagPopoverRef} className="tos-task-v2-tags-popover" dir={modalDirection} style={tagPopoverStyle} role="dialog" aria-label={isAr ? "إدارة الوسوم" : "Manage tags"}>
          <div className="tos-task-v2-tags-popover-head">
            <div><strong>{isAr ? "وسوم المهمة" : "Task tags"}</strong><span>{(draft.labels || []).length} {isAr ? "محدد" : "selected"}</span></div>
            <span>{isAr ? "اختر أو أنشئ وسمًا" : "Select or create"}</span>
          </div>
          <label className="tos-task-v2-tags-search">
            <Search aria-hidden="true" />
            <input value={tagQuery} onChange={(event) => setTagQuery(event.target.value)} placeholder={isAr ? "ابحث عن وسم..." : "Search tags..."} autoFocus />
          </label>
          <div className="tos-task-v2-tags-options">
            {filteredTaskLabels.length ? filteredTaskLabels.map((label) => {
              const selected = Boolean(draft.labels?.some((item) => item.id === label.id));
              return (
                <button key={label.id || label.name} type="button" className="tos-task-v2-tags-option" data-selected={selected ? "true" : "false"} disabled={saving} onClick={() => toggleLabel(label)}>
                  <span className="tos-task-v2-tags-option-label"><span className="tos-task-v2-tags-dot" style={{ "--tos-tag-color": label.color || "#94a3b8" }} />{label.name || "Tag"}</span>
                  {selected && <CheckCircle2 className="tos-task-v2-tags-check" aria-hidden="true" />}
                </button>
              );
            }) : <div className="tos-task-v2-tags-empty">{isAr ? "لا توجد وسوم مطابقة." : "No matching tags."}</div>}
          </div>
          {canManageLabels && (
            <form className="tos-task-v2-tags-create" onSubmit={createLabel}>
              <input type="color" value={newLabel.color} onChange={(event) => setNewLabel((current) => ({ ...current, color: event.target.value }))} aria-label={isAr ? "لون الوسم" : "Tag color"} />
              <input type="text" value={newLabel.name} onChange={(event) => setNewLabel((current) => ({ ...current, name: event.target.value }))} placeholder={isAr ? "وسم جديد..." : "New tag..."} />
              <button type="submit" disabled={saving || !newLabel.name.trim()}>{isAr ? "إنشاء" : "Create"}</button>
            </form>
          )}
        </div>,
        document.body,
      ) : null}'''
if updated.count(root_anchor) != 1:
    fail(f"expected one Task Details root anchor, found {updated.count(root_anchor)}")
updated = updated.replace(root_anchor, portal_block, 1)

# 7) Runtime stylesheet import after R24.
r24_import = 'import "../styles/taskDetailsV2_12_Phase1R24AssigneeFloatingDropdown.css";'
r25_import = 'import "../styles/taskDetailsV2_12_Phase1R25TagsPopoverNoLayoutFlip.css";'
if updated.count(r24_import) != 1:
    fail(f"expected one R24 import, found {updated.count(r24_import)}")
if r25_import in updated:
    fail("R25 import already exists")
updated = updated.replace(r24_import, r24_import + "\n" + r25_import, 1)

# Contract checks.
for contract in (
    'TOS_TASK_DETAILS_R25_TAGS_POPOVER_NO_LAYOUT_FLIP',
    'className="tos-task-v2-tags-popover"',
    'onClick={openTagPopover}',
    'await run(() => tasksApi.addLabelToTask(task.id, label.id));',
    r25_import,
):
    if contract not in updated:
        fail(f"R25 source contract missing after edit: {contract}")
if updated.count('onClick={() => { setTaskMoreDetailsOpen(true); setTaskSidebarExpanded(true); }}') != 0:
    fail("Add Tag still opens Advanced/Tracking Time rail")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R25_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
frontend_runtime = manifest.get("frontend") or {}
DIST = Path(str(frontend_runtime.get("buildOutputDir") or FRONTEND / "dist"))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or "/opt/apps/tamiyouz-front/build"))
if str(frontend_runtime.get("buildCommand") or "npm run build") != "npm run build":
    fail("unexpected frontend build command")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r25-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)
LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-r25-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-r25-backup-{stamp}"
live_swapped = False
r25_written = False

try:
    BOARD.write_text(updated)
    R25_STYLE.write_text(payload_css.rstrip() + "\n")
    r25_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R25_MARKER not in built_css or R24_MARKER not in built_css:
        fail("R24/R25 runtime marker missing from build")
    if "tos-task-v2-tags-popover" not in built_js:
        fail("R25 Tags portal missing from build")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        if live_backup.exists():
            shutil.rmtree(live_backup)
        LIVE.rename(live_backup)
    staging.rename(LIVE)
    live_swapped = True

    live_css = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.css"))
    live_js = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.js"))
    if R25_MARKER not in live_css or R24_MARKER not in live_css:
        fail("R24/R25 runtime marker missing from live build")
    if "tos-task-v2-tags-popover" not in live_js:
        fail("R25 Tags portal missing from live build")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r25_written and R25_STYLE.exists():
        R25_STYLE.unlink()
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"PATCH_APPLIED={PATCH}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print("ADD_TAG_FLOATING_POPOVER=YES")
print("ADD_TAG_OPENS_ADVANCED_RAIL=NO")
print("TRACKING_TIME_REMAINS_INDEPENDENT=YES")
print("TASK_LAYOUT_REFLOW_ON_TAGS=NO")
print("TAG_SEARCH=YES")
print("TAG_CREATE_AND_ASSIGN=YES")
print("R24_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
