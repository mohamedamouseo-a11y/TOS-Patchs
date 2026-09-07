from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SlaAdvancedPage.jsx"
V1_STYLE = FRONTEND / "src/pages/slaAdvancedFlagshipV1.css"
V11_STYLE = FRONTEND / "src/pages/slaAdvancedFlagshipV1_1PremiumSelectsDarkContrast.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "ad1cefe06375c6f486966c0a12a1d6b20c45246c3c7aeb957e3047446f13aa76"
EXPECTED_V1_STYLE_SHA256 = "d1895166fbf68e71b758b585fe551ffe3e9af31a239d6c21678013f291b099fb"
V1_IMPORT = 'import "./slaAdvancedFlagshipV1.css";'
V11_IMPORT = 'import "./slaAdvancedFlagshipV1_1PremiumSelectsDarkContrast.css";'
RUNTIME_MARKER = "--tos-advanced-sla-v1-1-premium-selects-dark-contrast-runtime"

PRESERVE_FILES = [
    V1_STYLE,
    FRONTEND / "src/pages/SlaInboxPage.jsx",
    FRONTEND / "src/pages/slaInboxFlagshipV1.css",
    FRONTEND / "src/pages/slaInboxFlagshipV1_1DarkContrast.css",
    FRONTEND / "src/pages/SlaCenterPage.jsx",
    FRONTEND / "src/pages/slaCenterFlagshipV1.css",
    FRONTEND / "src/pages/slaCenterFlagshipV1_1DarkTableHeader.css",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

CSS = r''':root {
  --tos-advanced-sla-v1-1-premium-selects-dark-contrast-runtime: 1;
}

/* V1.1 premium select system. The native select stays visually hidden only
   to preserve controlled value + required/form semantics. */
.tos-advanced-sla-premium-select {
  position: relative;
  width: 100%;
  isolation: isolate;
}

.tos-advanced-sla-native-select-shadow {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: 0 !important;
  opacity: 0 !important;
  pointer-events: none !important;
  overflow: hidden !important;
  clip: rect(0 0 0 0) !important;
  clip-path: inset(50%) !important;
  white-space: nowrap !important;
}

.tos-advanced-sla-select-trigger {
  width: 100%;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 13px;
  border: 1px solid rgba(201,145,31,.16);
  border-radius: 14px;
  color: #17130d;
  background: #fffdf8;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.92);
  font-size: 14px;
  font-weight: 800;
  text-align: start;
  outline: none;
  transition: border-color 140ms ease, box-shadow 140ms ease, background 140ms ease, transform 140ms ease;
}
.tos-advanced-sla-select-trigger:hover {
  border-color: rgba(201,145,31,.34);
  background: #fffaf1;
}
.tos-advanced-sla-select-trigger:focus-visible,
.tos-advanced-sla-select-trigger[data-open="true"] {
  border-color: rgba(201,145,31,.68);
  box-shadow: 0 0 0 3px rgba(201,145,31,.10), inset 0 1px 0 rgba(255,255,255,.92);
}
.tos-advanced-sla-select-trigger[data-placeholder="true"] .tos-advanced-sla-select-value {
  color: #918575;
}
.tos-advanced-sla-select-value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tos-advanced-sla-select-chevron {
  flex: 0 0 auto;
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(201,145,31,.13);
  border-radius: 8px;
  color: #9d6707;
  background: rgba(201,145,31,.06);
  font-size: 13px;
  line-height: 1;
  transition: transform 150ms ease, background 150ms ease;
}
.tos-advanced-sla-select-trigger[data-open="true"] .tos-advanced-sla-select-chevron {
  transform: rotate(180deg);
  background: rgba(201,145,31,.12);
}

.tos-advanced-sla-select-menu {
  position: absolute;
  z-index: 120;
  inset-inline: 0;
  top: calc(100% + 7px);
  max-height: 270px;
  overflow-y: auto;
  padding: 6px;
  border: 1px solid rgba(201,145,31,.18);
  border-radius: 15px;
  background: rgba(255,253,248,.99);
  box-shadow: 0 22px 52px rgba(55,37,8,.16), inset 0 1px 0 rgba(255,255,255,.96);
  backdrop-filter: blur(18px);
}
.tos-advanced-sla-select-option {
  width: 100%;
  min-height: 39px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 10px;
  border: 0;
  border-radius: 10px;
  color: #2c251b;
  background: transparent;
  font-size: 13px;
  font-weight: 800;
  text-align: start;
  cursor: pointer;
  transition: background 120ms ease, color 120ms ease, transform 120ms ease;
}
.tos-advanced-sla-select-option:hover,
.tos-advanced-sla-select-option:focus-visible {
  color: #6f4704;
  background: rgba(201,145,31,.09);
  outline: none;
}
.tos-advanced-sla-select-option[data-selected="true"] {
  color: #2a1c02;
  background: linear-gradient(145deg, #f6d36f, #dda12a);
  box-shadow: 0 7px 17px rgba(177,116,10,.12);
}
.tos-advanced-sla-select-check {
  font-size: 12px;
  font-weight: 950;
}

/* Escalation cards used overflow:hidden in V1; premium menus must be allowed
   to extend beyond their card without being clipped. */
.tos-advanced-sla-flagship-v1 .tos-advanced-sla-escalation {
  overflow: visible !important;
}
.tos-advanced-sla-flagship-v1 .tos-advanced-sla-escalation:has(.tos-advanced-sla-select-trigger[data-open="true"]) {
  z-index: 40;
}

/* Dark field-value correction: V1 had high-contrast labels but some native
   input values inherited an almost-black browser text color. */
.dark .tos-advanced-sla-flagship-v1 input.tos-advanced-sla-field,
.dark .tos-advanced-sla-flagship-v1 textarea.tos-advanced-sla-field {
  color: #f3eee5 !important;
  -webkit-text-fill-color: #f3eee5 !important;
  caret-color: #e2b352 !important;
}
.dark .tos-advanced-sla-flagship-v1 input.tos-advanced-sla-field::placeholder,
.dark .tos-advanced-sla-flagship-v1 textarea.tos-advanced-sla-field::placeholder {
  color: #837b70 !important;
  -webkit-text-fill-color: #837b70 !important;
  opacity: 1;
}
.dark .tos-advanced-sla-flagship-v1 input[type="time"].tos-advanced-sla-field {
  color-scheme: dark;
}
.dark .tos-advanced-sla-flagship-v1 input[type="number"].tos-advanced-sla-field {
  color-scheme: dark;
}

.dark .tos-advanced-sla-select-trigger {
  color: #f4efe6;
  border-color: rgba(222,179,82,.17);
  background: #181816;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}
.dark .tos-advanced-sla-select-trigger:hover {
  color: #fffaf2;
  border-color: rgba(222,179,82,.30);
  background: #1d1c19;
}
.dark .tos-advanced-sla-select-trigger:focus-visible,
.dark .tos-advanced-sla-select-trigger[data-open="true"] {
  border-color: rgba(222,179,82,.58);
  box-shadow: 0 0 0 3px rgba(222,179,82,.08), inset 0 1px 0 rgba(255,255,255,.025);
}
.dark .tos-advanced-sla-select-trigger[data-placeholder="true"] .tos-advanced-sla-select-value {
  color: #8d8579;
}
.dark .tos-advanced-sla-select-chevron {
  color: #e4b752;
  border-color: rgba(222,179,82,.15);
  background: rgba(222,179,82,.07);
}
.dark .tos-advanced-sla-select-menu {
  border-color: rgba(222,179,82,.17);
  background: rgba(20,20,18,.995);
  box-shadow: 0 24px 58px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.025);
}
.dark .tos-advanced-sla-select-option {
  color: #eee7dc;
}
.dark .tos-advanced-sla-select-option:hover,
.dark .tos-advanced-sla-select-option:focus-visible {
  color: #fff8eb;
  background: rgba(222,179,82,.10);
}
.dark .tos-advanced-sla-select-option[data-selected="true"] {
  color: #241701;
  background: linear-gradient(145deg, #f1cb63, #d99f2b);
}

@media (max-width: 640px) {
  .tos-advanced-sla-select-menu { max-height: 230px; }
}
'''

PREMIUM_SELECT_COMPONENT = r'''
function PremiumSelect({ value, onValueChange, options, placeholder, required = false, ariaLabel }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const selected = options.find((option) => String(option.value) === String(value));

  useEffect(() => {
    if (!open) return undefined;
    const closeOnOutside = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  const choose = (nextValue) => {
    onValueChange(nextValue);
    setOpen(false);
  };

  return (
    <div ref={rootRef} className="tos-advanced-sla-premium-select">
      <select
        className="tos-advanced-sla-native-select-shadow"
        tabIndex={-1}
        aria-hidden="true"
        aria-label={ariaLabel}
        value={value}
        onChange={(event) => onValueChange(event.target.value)}
        required={required}
      >
        {options.map((option) => <option key={String(option.value)} value={option.value}>{option.label}</option>)}
      </select>
      <button
        type="button"
        className="tos-advanced-sla-select-trigger"
        data-open={open ? "true" : "false"}
        data-placeholder={!value ? "true" : "false"}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="tos-advanced-sla-select-value">{selected?.label || placeholder || "—"}</span>
        <span className="tos-advanced-sla-select-chevron" aria-hidden="true">⌄</span>
      </button>
      {open && (
        <div className="tos-advanced-sla-select-menu" role="listbox" aria-label={ariaLabel}>
          {options.map((option) => {
            const isSelected = String(option.value) === String(value);
            return (
              <button
                key={String(option.value)}
                type="button"
                role="option"
                aria-selected={isSelected}
                data-selected={isSelected ? "true" : "false"}
                className="tos-advanced-sla-select-option"
                onClick={() => choose(option.value)}
              >
                <span>{option.label}</span>
                {isSelected && <span className="tos-advanced-sla-select-check" aria-hidden="true">✓</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
'''

print("RUNNING=TOS_UXUI_ADVANCED_SLA_FLAGSHIP_V1_1_PREMIUM_SELECTS_DARK_FIELD_CONTRAST")


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


def fail(message: str, original_page=None):
    if original_page is not None:
        try:
            PAGE.write_text(original_page, encoding="utf-8")
        except Exception:
            pass
    if V11_STYLE.exists():
        try:
            V11_STYLE.unlink()
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("ADVANCED_SLA_FLAGSHIP_V1_1_RUNTIME=NO")
    sys.exit(1)


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        fail(f"{label} guard mismatch: expected 1, found {count}")
    return source.replace(old, new, 1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (FRONTEND, PAGE, V1_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_page_sha = sha256(PAGE)
actual_style_sha = sha256(V1_STYLE)
if actual_page_sha != EXPECTED_PAGE_SHA256:
    fail(f"SlaAdvancedPage.jsx V1 baseline mismatch: {actual_page_sha}")
if actual_style_sha != EXPECTED_V1_STYLE_SHA256:
    fail(f"Advanced SLA V1 stylesheet baseline mismatch: {actual_style_sha}")
if V11_STYLE.exists():
    fail("Advanced SLA V1.1 stylesheet already exists")

original = PAGE.read_text(encoding="utf-8")
if V11_IMPORT in original or "tos-advanced-sla-premium-select" in original or "function PremiumSelect" in original:
    fail("Advanced SLA V1.1 appears already applied")

for token in (
    V1_IMPORT,
    'request("/api/sla/context")',
    'request("/api/sla/policies")',
    'request("/api/sla/history?limit=200")',
    'method: editingId ? "PATCH" : "POST"',
    'method: "DELETE"',
    'if (!context.canManagePolicies) return;',
    'const HISTORY_PAGE_SIZE = 8;',
    'data-sla-advanced-history-pagination="v1"',
    'className="tos-advanced-sla-field w-full',
):
    if token not in original:
        fail(f"required Advanced SLA V1 behavior/style anchor missing: {token}")

preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}
source = original
source = replace_once(source, 'import { useEffect, useMemo, useState } from "react";', 'import { useEffect, useMemo, useRef, useState } from "react";', "useRef import")
source = replace_once(source, V1_IMPORT, V1_IMPORT + "\n" + V11_IMPORT, "V1.1 style import")
source = replace_once(source, '\nexport default function SlaAdvancedPage() {', PREMIUM_SELECT_COMPONENT + '\nexport default function SlaAdvancedPage() {', "premium select component")

SCOPE_OLD = '''                  <label className="space-y-1.5"><span className="text-xs font-black text-muted">{ar ? "النطاق" : "Scope"}</span>
                    <select className={field} value={draft.scopeType} onChange={(e) => setDraft({ ...draft, scopeType: e.target.value })}>
                      <option value="COMPANY">{ar ? "الشركة" : "Company"}</option>
                      <option value="DEPARTMENT">{ar ? "قسم" : "Department"}</option>
                      <option value="CLIENT">{ar ? "عميل" : "Client"}</option>
                    </select>
                  </label>'''
SCOPE_NEW = '''                  <div className="space-y-1.5"><span className="text-xs font-black text-muted">{ar ? "النطاق" : "Scope"}</span>
                    <PremiumSelect
                      value={draft.scopeType}
                      onValueChange={(nextValue) => setDraft({ ...draft, scopeType: nextValue })}
                      ariaLabel={ar ? "النطاق" : "Scope"}
                      options={[
                        { value: "COMPANY", label: ar ? "الشركة" : "Company" },
                        { value: "DEPARTMENT", label: ar ? "قسم" : "Department" },
                        { value: "CLIENT", label: ar ? "عميل" : "Client" },
                      ]}
                    />
                  </div>'''
source = replace_once(source, SCOPE_OLD, SCOPE_NEW, "scope premium select")

DEPARTMENT_OLD = '''                    <label className="space-y-1.5"><span className="text-xs font-black text-muted">{ar ? "القسم" : "Department"}</span>
                      <select className={field} value={draft.department} onChange={(e) => setDraft({ ...draft, department: e.target.value })} required>
                        <option value="">{ar ? "اختر القسم" : "Select department"}</option>
                        {(context.departments || []).map((item) => <option key={item.key || item.name} value={item.name}>{item.name}</option>)}
                      </select>
                    </label>'''
DEPARTMENT_NEW = '''                    <div className="space-y-1.5"><span className="text-xs font-black text-muted">{ar ? "القسم" : "Department"}</span>
                      <PremiumSelect
                        value={draft.department}
                        onValueChange={(nextValue) => setDraft({ ...draft, department: nextValue })}
                        placeholder={ar ? "اختر القسم" : "Select department"}
                        ariaLabel={ar ? "القسم" : "Department"}
                        required
                        options={[
                          { value: "", label: ar ? "اختر القسم" : "Select department" },
                          ...(context.departments || []).map((item) => ({ value: item.name, label: item.name })),
                        ]}
                      />
                    </div>'''
source = replace_once(source, DEPARTMENT_OLD, DEPARTMENT_NEW, "department premium select")

CLIENT_OLD = '''                    <label className="space-y-1.5"><span className="text-xs font-black text-muted">{ar ? "العميل" : "Client"}</span>
                      <select className={field} value={draft.clientId} onChange={(e) => setDraft({ ...draft, clientId: e.target.value })} required>
                        <option value="">{ar ? "اختر العميل" : "Select client"}</option>
                        {(context.clients || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                      </select>
                    </label>'''
CLIENT_NEW = '''                    <div className="space-y-1.5"><span className="text-xs font-black text-muted">{ar ? "العميل" : "Client"}</span>
                      <PremiumSelect
                        value={draft.clientId}
                        onValueChange={(nextValue) => setDraft({ ...draft, clientId: nextValue })}
                        placeholder={ar ? "اختر العميل" : "Select client"}
                        ariaLabel={ar ? "العميل" : "Client"}
                        required
                        options={[
                          { value: "", label: ar ? "اختر العميل" : "Select client" },
                          ...(context.clients || []).map((item) => ({ value: item.id, label: item.name })),
                        ]}
                      />
                    </div>'''
source = replace_once(source, CLIENT_OLD, CLIENT_NEW, "client premium select")

ROLE_OLD = '''                        <label className="mt-3 block space-y-1.5"><span className="text-xs font-black text-muted">{ar ? "الدور المستهدف" : "Target role"}</span>
                          <select className={field} value={draft[roleKey]} onChange={(e) => setDraft({ ...draft, [roleKey]: e.target.value })}>
                            {TARGET_ROLES.map((role) => <option key={role} value={role}>{role}</option>)}
                          </select>
                        </label>'''
ROLE_NEW = '''                        <div className="mt-3 block space-y-1.5"><span className="text-xs font-black text-muted">{ar ? "الدور المستهدف" : "Target role"}</span>
                          <PremiumSelect
                            value={draft[roleKey]}
                            onValueChange={(nextValue) => setDraft({ ...draft, [roleKey]: nextValue })}
                            ariaLabel={`${ar ? "الدور المستهدف" : "Target role"} L${level}`}
                            options={TARGET_ROLES.map((role) => ({ value: role, label: role }))}
                          />
                        </div>'''
source = replace_once(source, ROLE_OLD, ROLE_NEW, "target role premium selects")

# Guard against any user-visible native select that belonged to the V1 form.
for legacy_pattern in (
    '<select className={field} value={draft.scopeType}',
    '<select className={field} value={draft.department}',
    '<select className={field} value={draft.clientId}',
    '<select className={field} value={draft[roleKey]}',
):
    if legacy_pattern in source:
        fail(f"visible native select remains after V1.1 transform: {legacy_pattern}", original)

for token in (
    V11_IMPORT,
    'function PremiumSelect',
    'tos-advanced-sla-premium-select',
    'tos-advanced-sla-native-select-shadow',
    'onValueChange={(nextValue) => setDraft({ ...draft, scopeType: nextValue })}',
    'onValueChange={(nextValue) => setDraft({ ...draft, department: nextValue })}',
    'onValueChange={(nextValue) => setDraft({ ...draft, clientId: nextValue })}',
    'onValueChange={(nextValue) => setDraft({ ...draft, [roleKey]: nextValue })}',
    'const HISTORY_PAGE_SIZE = 8;',
    'data-sla-advanced-history-pagination="v1"',
):
    if token not in source:
        fail(f"transformed source missing V1.1/V1 marker: {token}", original)

# Reconfirm all business behavior anchors byte-semantically remain in the page.
for token in (
    'request("/api/sla/context")',
    'request("/api/sla/policies")',
    'request("/api/sla/history?limit=200")',
    'method: editingId ? "PATCH" : "POST"',
    'method: "DELETE"',
    'if (!context.canManagePolicies) return;',
    'department: draft.scopeType === "DEPARTMENT" ? draft.department || null : null',
    'clientId: draft.scopeType === "CLIENT" ? draft.clientId || null : null',
):
    if token not in source:
        fail(f"Advanced SLA behavior changed unexpectedly: {token}", original)

try:
    PAGE.write_text(source, encoding="utf-8")
    V11_STYLE.write_text(CSS, encoding="utf-8")
except Exception as exc:
    fail(f"source/style write failed: {exc}", original)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", original)

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", original)

for marker in (
    RUNTIME_MARKER.encode(),
    b'tos-advanced-sla-flagship-v1',
    b'tos-advanced-sla-premium-select',
    b'tos-advanced-sla-select-menu',
    b'data-sla-advanced-history-pagination',
    b'Advanced SLA Management',
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing V1.1/V1 marker: {marker.decode(errors='ignore')}", original)

for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope file changed: {path}", original)

# Safe atomic live deploy. No service restart and no Git action in /var/www/TOS.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.advanced-sla-v1-1-premium-selects-candidate-{ts}"
backup = LIVE_PARENT / f"build.advanced-sla-v1-1-premium-selects-backup-{ts}"
failed_live = LIVE_PARENT / f"build.advanced-sla-v1-1-premium-selects-failed-{ts}"
try:
    if candidate.exists() or backup.exists() or failed_live.exists():
        raise RuntimeError("timestamped deployment path already exists")
    shutil.copytree(DIST, candidate)
    if not LIVE.exists():
        raise RuntimeError(f"live build missing: {LIVE}")
    LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists() and backup.exists():
            LIVE.rename(failed_live)
            backup.rename(LIVE)
        elif backup.exists() and not LIVE.exists():
            backup.rename(LIVE)
    finally:
        fail(f"live deployment failed and rollback attempted: {exc}", original)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("ADVANCED_SLA_FLAGSHIP_V1_1_RUNTIME=YES")
print("ADVANCED_SLA_V1_1_SCOPE=PREMIUM_SELECTS_AND_DARK_FIELD_CONTRAST")
print("ADVANCED_SLA_SCOPE_SELECT=PREMIUM_CUSTOM")
print("ADVANCED_SLA_DEPARTMENT_SELECT=PREMIUM_CUSTOM")
print("ADVANCED_SLA_CLIENT_SELECT=PREMIUM_CUSTOM")
print("ADVANCED_SLA_TARGET_ROLE_SELECTS=PREMIUM_CUSTOM")
print("ADVANCED_SLA_NATIVE_VISIBLE_SELECTS_REMAINING=0")
print("ADVANCED_SLA_NATIVE_REQUIRED_SEMANTICS=PRESERVED_HIDDEN_SHADOW_SELECT")
print("ADVANCED_SLA_DARK_FIELD_VALUES=HIGH_CONTRAST")
print("ADVANCED_SLA_DARK_TIME_VALUES=HIGH_CONTRAST")
print("ADVANCED_SLA_DARK_NUMBER_VALUES=HIGH_CONTRAST")
print("ADVANCED_SLA_ESCALATION_MENU_CLIPPING=CORRECTED")
print("ADVANCED_SLA_HISTORY_PAGINATION_V1=PRESERVED")
print("ADVANCED_SLA_CONTEXT_API_CHANGED=NO")
print("ADVANCED_SLA_POLICIES_API_CHANGED=NO")
print("ADVANCED_SLA_HISTORY_API_CHANGED=NO")
print("ADVANCED_SLA_POLICY_CREATE_CHANGED=NO")
print("ADVANCED_SLA_POLICY_EDIT_CHANGED=NO")
print("ADVANCED_SLA_POLICY_DELETE_CHANGED=NO")
print("ADVANCED_SLA_PERMISSION_LOGIC_CHANGED=NO")
print("SLA_INBOX_CHANGED=NO")
print("SLA_CENTER_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"ADVANCED_SLA_PAGE_SHA256={sha256(PAGE)}")
print(f"ADVANCED_SLA_V1_STYLE_SHA256={sha256(V1_STYLE)}")
print(f"ADVANCED_SLA_V11_STYLE_SHA256={sha256(V11_STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")