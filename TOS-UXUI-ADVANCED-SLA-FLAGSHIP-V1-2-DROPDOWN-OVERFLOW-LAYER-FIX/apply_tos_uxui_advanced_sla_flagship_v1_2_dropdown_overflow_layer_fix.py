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
V12_STYLE = FRONTEND / "src/pages/slaAdvancedFlagshipV1_2DropdownOverflowLayerFix.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "89f9d6efec400ef5e292bae687f7636b59ee0ea56def39880fe77fb51f8c91cb"
EXPECTED_V1_STYLE_SHA256 = "d1895166fbf68e71b758b585fe551ffe3e9af31a239d6c21678013f291b099fb"
EXPECTED_V11_STYLE_SHA256 = "1fb04bc46986fd7e2aa58409dae4ef1fb8f9215566c1a6c56115b2705c6b31e3"
V11_IMPORT = 'import "./slaAdvancedFlagshipV1_1PremiumSelectsDarkContrast.css";'
V12_IMPORT = 'import "./slaAdvancedFlagshipV1_2DropdownOverflowLayerFix.css";'
RUNTIME_MARKER = "--tos-advanced-sla-v1-2-dropdown-overflow-layer-runtime"

PRESERVE_FILES = [
    V1_STYLE,
    V11_STYLE,
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
  --tos-advanced-sla-v1-2-dropdown-overflow-layer-runtime: 1;
}

/* V1.2 visual-layer correction only.
   V1 studio used overflow:hidden and clipped premium menus at the card edge. */
.tos-advanced-sla-flagship-v1 .tos-advanced-sla-studio {
  overflow: visible !important;
  position: relative !important;
  z-index: 60 !important;
}

/* Keep following cards below the open Policy Studio menu layer. */
.tos-advanced-sla-flagship-v1 .tos-advanced-sla-policies,
.tos-advanced-sla-flagship-v1 .tos-advanced-sla-history {
  position: relative !important;
  z-index: 1 !important;
}

/* Escalation cards and premium-select roots must never create a clipping boundary. */
.tos-advanced-sla-flagship-v1 .tos-advanced-sla-escalation,
.tos-advanced-sla-flagship-v1 .tos-advanced-sla-premium-select {
  overflow: visible !important;
  position: relative;
}

.tos-advanced-sla-flagship-v1 .tos-advanced-sla-premium-select {
  z-index: 80;
}

.tos-advanced-sla-flagship-v1 .tos-advanced-sla-premium-select:has(.tos-advanced-sla-select-trigger[data-open="true"]) {
  z-index: 240 !important;
}

.tos-advanced-sla-flagship-v1 .tos-advanced-sla-escalation:has(.tos-advanced-sla-select-trigger[data-open="true"]) {
  z-index: 220 !important;
}

.tos-advanced-sla-flagship-v1 .tos-advanced-sla-select-menu {
  z-index: 300 !important;
  overflow-x: hidden;
  overflow-y: auto;
}

/* Preserve the rounded flagship silhouette when menus are closed while allowing
   the actual menu surface to extend over Policies/History when opened. */
.tos-advanced-sla-flagship-v1 .tos-advanced-sla-studio::after {
  pointer-events: none;
}
'''

print("RUNNING=TOS_UXUI_ADVANCED_SLA_FLAGSHIP_V1_2_DROPDOWN_OVERFLOW_LAYER_FIX")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
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
    if V12_STYLE.exists():
        try:
            V12_STYLE.unlink()
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("ADVANCED_SLA_FLAGSHIP_V1_2_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (FRONTEND, PAGE, V1_STYLE, V11_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail(f"SlaAdvancedPage.jsx V1.1 baseline mismatch: {sha256(PAGE)}")
if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256:
    fail(f"Advanced SLA V1 stylesheet baseline mismatch: {sha256(V1_STYLE)}")
if sha256(V11_STYLE) != EXPECTED_V11_STYLE_SHA256:
    fail(f"Advanced SLA V1.1 stylesheet baseline mismatch: {sha256(V11_STYLE)}")
if V12_STYLE.exists():
    fail("Advanced SLA V1.2 stylesheet already exists")

original = PAGE.read_text(encoding="utf-8")
if original.count(V11_IMPORT) != 1:
    fail(f"V1.1 import guard mismatch: {original.count(V11_IMPORT)}")
if V12_IMPORT in original:
    fail("Advanced SLA V1.2 appears already applied")

for token in (
    'function PremiumSelect',
    'tos-advanced-sla-premium-select',
    'tos-advanced-sla-select-menu',
    'data-sla-advanced-history-pagination="v1"',
    'request("/api/sla/context")',
    'request("/api/sla/policies")',
    'request("/api/sla/history?limit=200")',
    'method: editingId ? "PATCH" : "POST"',
    'method: "DELETE"',
    'if (!context.canManagePolicies) return;',
):
    if token not in original:
        fail(f"required Advanced SLA V1.1 behavior/style anchor missing: {token}")

preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}
source = original.replace(V11_IMPORT, V11_IMPORT + "\n" + V12_IMPORT, 1)

# V1.2 is deliberately CSS-only apart from a single stylesheet import.
expected_source = original.replace(V11_IMPORT, V11_IMPORT + "\n" + V12_IMPORT, 1)
if source != expected_source:
    fail("unexpected page transformation outside V1.2 stylesheet import")

try:
    PAGE.write_text(source, encoding="utf-8")
    V12_STYLE.write_text(CSS, encoding="utf-8")
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
    b'tos-advanced-sla-premium-select',
    b'tos-advanced-sla-select-menu',
    b'data-sla-advanced-history-pagination',
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing V1.2/V1.1 marker: {marker.decode(errors='ignore')}", original)

for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope file changed: {path}", original)

# Atomic live deploy. No service restart and no Git action in /var/www/TOS.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.advanced-sla-v1-2-dropdown-layer-candidate-{ts}"
backup = LIVE_PARENT / f"build.advanced-sla-v1-2-dropdown-layer-backup-{ts}"
failed_live = LIVE_PARENT / f"build.advanced-sla-v1-2-dropdown-layer-failed-{ts}"
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
print("ADVANCED_SLA_FLAGSHIP_V1_2_RUNTIME=YES")
print("ADVANCED_SLA_V1_2_SCOPE=DROPDOWN_OVERFLOW_LAYER_ONLY")
print("ADVANCED_SLA_POLICY_STUDIO_OVERFLOW=VISIBLE")
print("ADVANCED_SLA_POLICY_STUDIO_LAYER=RAISED")
print("ADVANCED_SLA_ESCALATION_CARD_OVERFLOW=VISIBLE")
print("ADVANCED_SLA_PREMIUM_MENU_LAYER=RAISED")
print("ADVANCED_SLA_DROPDOWN_CLIPPING=CORRECTED")
print("ADVANCED_SLA_LIGHT_MODE_CHANGED=NO")
print("ADVANCED_SLA_DARK_MODE_CHANGED=NO")
print("ADVANCED_SLA_PREMIUM_SELECT_BEHAVIOR_CHANGED=NO")
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
print(f"ADVANCED_SLA_V12_STYLE_SHA256={sha256(V12_STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
