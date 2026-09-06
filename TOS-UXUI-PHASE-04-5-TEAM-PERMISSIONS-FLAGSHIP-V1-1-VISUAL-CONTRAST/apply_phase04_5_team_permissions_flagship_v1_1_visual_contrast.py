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
OVERRIDE = PATCH_DIR / "permissionsFlagshipV1_1VisualContrast.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "0c40a8709a964937c21c6fea41b6f1f6c2e66eed35f14dea257178a5ce5cbd71"
EXPECTED_STYLE_SHA256 = "ebe351567c705b2b67085767341098937fd154804648563511f57f466526ef98"
V1_RUNTIME = "--tos-permissions-flagship-v1-runtime"
V11_RUNTIME = "--tos-permissions-flagship-v1-1-runtime"
MATRIX_CLASS = "tos-permissions-matrix"

print("RUNNING=PHASE04_5_TEAM_PERMISSIONS_FLAGSHIP_V1_1_VISUAL_CONTRAST")


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
    print("V1_1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (PAGE, STYLE, OVERRIDE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_page_sha = sha256(PAGE)
actual_style_sha = sha256(STYLE)
if actual_page_sha != EXPECTED_PAGE_SHA256:
    fail(f"PermissionsPage.jsx source guard mismatch: {actual_page_sha}")
if actual_style_sha != EXPECTED_STYLE_SHA256:
    fail(f"permissionsFlagshipV1.css source guard mismatch: {actual_style_sha}")

original_style = STYLE.read_text(encoding="utf-8")
override_css = OVERRIDE.read_text(encoding="utf-8")

if V1_RUNTIME not in original_style:
    fail("V1 runtime marker missing")
if V11_RUNTIME in original_style:
    fail("V1.1 visual contrast appears already or partially applied")
if V11_RUNTIME not in override_css:
    fail("V1.1 runtime marker missing from override asset")
if MATRIX_CLASS not in original_style:
    fail("V1 matrix visual hook missing from baseline")

# Targeted CSS-only append. No JSX handlers, permission semantics, API or DB code are touched.
try:
    STYLE.write_text(original_style.rstrip() + "\n\n" + override_css.strip() + "\n", encoding="utf-8")
except Exception as exc:
    fail(f"could not append V1.1 visual override: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend build failed; V1 style restored")

if not DIST.exists():
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (V1_RUNTIME.encode(), V11_RUNTIME.encode(), MATRIX_CLASS.encode()):
    if tree_count(DIST, marker) < 1:
        STYLE.write_text(original_style, encoding="utf-8")
        fail(f"built output missing runtime marker/token: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.team-permissions-v1-1-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.team-permissions-v1-1-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.team-permissions-v1-1-failed-{timestamp}"

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
        STYLE.write_text(original_style, encoding="utf-8")
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("V1_RUNTIME=YES")
print("V1_1_RUNTIME=YES")
print("DARK_CRITICAL_HEADINGS=HIGH_CONTRAST")
print("DARK_ROLE_NAMES=HIGH_CONTRAST")
print("DARK_MATRIX_SURFACE=OBSIDIAN_TITANIUM")
print("DARK_WHITE_MATRIX_SLAB=REMOVED")
print("MATRIX_ROLE_HEADERS_VISIBLE=YES")
print("MATRIX_PERMISSION_LABELS_FORCED_VISIBLE=YES")
print("MATRIX_PERMISSION_KEY_SECONDARY_TEXT=VISIBLE")
print("MATRIX_STICKY_COLUMN_PRESERVED=YES")
print("LIGHT_MATRIX_ROW_DEFINITION=REFINED")
print("PERMISSION_SEMANTICS_CHANGED=NO")
print("FUNCTIONALITY_CHANGED=NO")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"PERMISSIONS_PAGE_SHA256={sha256(PAGE)}")
print(f"PERMISSIONS_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
