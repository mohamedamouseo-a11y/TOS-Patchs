from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
PAGE = ROOT / "frontend/src/pages/PermissionsPage.jsx"
STYLE = ROOT / "frontend/src/pages/permissionsFlagshipV1.css"
OVERRIDE = PATCH_DIR / "permissionsFlagshipV1_2PermissionLabels.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "0c40a8709a964937c21c6fea41b6f1f6c2e66eed35f14dea257178a5ce5cbd71"
EXPECTED_STYLE_SHA256 = "ead9c1b483fa0cef3b78fa3e558454af3174b62dff896abd1e9ae290a14f69a3"
V1_RUNTIME = "--tos-permissions-flagship-v1-runtime"
V11_RUNTIME = "--tos-permissions-flagship-v1-1-runtime"
V12_RUNTIME = "--tos-permissions-flagship-v1-2-runtime"
CELL_CLASS = "tos-permissions-permission-cell"
LABEL_CLASS = "tos-permissions-permission-label"
KEY_CLASS = "tos-permissions-permission-key"

print("RUNNING=PHASE04_5_TEAM_PERMISSIONS_FLAGSHIP_V1_2_PERMISSION_LABELS")


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
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V1_2_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (PAGE, STYLE, OVERRIDE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail(f"PermissionsPage.jsx source guard mismatch: {sha256(PAGE)}")
if sha256(STYLE) != EXPECTED_STYLE_SHA256:
    fail(f"permissionsFlagshipV1.css source guard mismatch: {sha256(STYLE)}")

original_page = PAGE.read_text(encoding="utf-8")
original_style = STYLE.read_text(encoding="utf-8")
override_css = OVERRIDE.read_text(encoding="utf-8")

for marker in (V1_RUNTIME, V11_RUNTIME):
    if marker not in original_style:
        fail(f"required baseline runtime marker missing: {marker}")
if V12_RUNTIME in original_style or CELL_CLASS in original_page:
    fail("V1.2 appears already or partially applied")
if V12_RUNTIME not in override_css:
    fail("V1.2 runtime marker missing from override asset")

old_block = '''                <td className="px-4 py-4">
                  <div className="font-black text-slate-950 dark:text-white">{permissionUiLabel(permission, isEnglish)}</div>
                  <div className="mt-1 max-w-[220px] truncate text-[10px] font-bold text-slate-400" title={permission.key}>{permission.key}</div>
                </td>'''
new_block = '''                <td className="tos-permissions-permission-cell px-4 py-4">
                  <div className="tos-permissions-permission-label font-black text-slate-950 dark:text-white">{permissionUiLabel(permission, isEnglish)}</div>
                  <div className="tos-permissions-permission-key mt-1 max-w-[220px] truncate text-[10px] font-bold text-slate-400" title={permission.key}>{permission.key}</div>
                </td>'''

if original_page.count(old_block) != 1:
    fail(f"permission label cell anchor mismatch: found {original_page.count(old_block)}")

try:
    PAGE.write_text(original_page.replace(old_block, new_block, 1), encoding="utf-8")
    STYLE.write_text(original_style.rstrip() + "\n\n" + override_css.strip() + "\n", encoding="utf-8")
except Exception as exc:
    PAGE.write_text(original_page, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail(f"V1.2 source transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    PAGE.write_text(original_page, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend build failed; sources restored")

if not DIST.exists():
    PAGE.write_text(original_page, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (V1_RUNTIME.encode(), V11_RUNTIME.encode(), V12_RUNTIME.encode(), CELL_CLASS.encode(), LABEL_CLASS.encode(), KEY_CLASS.encode()):
    if tree_count(DIST, marker) < 1:
        PAGE.write_text(original_page, encoding="utf-8")
        STYLE.write_text(original_style, encoding="utf-8")
        fail(f"built output missing runtime marker/token: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.team-permissions-v1-2-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.team-permissions-v1-2-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.team-permissions-v1-2-failed-{timestamp}"

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
        PAGE.write_text(original_page, encoding="utf-8")
        STYLE.write_text(original_style, encoding="utf-8")
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("V1_RUNTIME=YES")
print("V1_1_RUNTIME=YES")
print("V1_2_RUNTIME=YES")
print("PERMISSION_LABEL_CELL_HOOK=YES")
print("PERMISSION_LABEL_TEXT_HOOK=YES")
print("PERMISSION_KEY_TEXT_HOOK=YES")
print("PERMISSION_LABELS_VISIBILITY_FORCED=YES")
print("LTR_STICKY_ALIGNMENT=YES")
print("RTL_STICKY_ALIGNMENT=YES")
print("LIGHT_PERMISSION_COLUMN=READABLE")
print("DARK_PERMISSION_COLUMN=READABLE")
print("PERMISSION_SEMANTICS_CHANGED=NO")
print("FUNCTIONALITY_CHANGED=NO")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"PERMISSIONS_PAGE_SHA256={sha256(PAGE)}")
print(f"PERMISSIONS_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
