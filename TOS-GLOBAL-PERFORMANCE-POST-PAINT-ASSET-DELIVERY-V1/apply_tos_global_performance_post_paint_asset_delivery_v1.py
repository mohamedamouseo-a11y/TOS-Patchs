from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
APP = FRONTEND / "src/App.jsx"
INDEX = FRONTEND / "index.html"
INDEX_CSS = FRONTEND / "src/index.css"
RAMZY = FRONTEND / "src/components/RamzyAssistant.jsx"
PROJECTS_HOOK = FRONTEND / "src/hooks/useProjects.js"
TCS_STYLE = FRONTEND / "src/components/tcsFlagshipV1.css"
PUBLIC = FRONTEND / "public"
SOURCE_LOGO = PUBLIC / "logo.png"
SOURCE_RAMZY = PUBLIC / "ramzy-avatar.png"
CRITICAL_DIR = PUBLIC / "assets/critical"
CRITICAL_LOGO = CRITICAL_DIR / "tos-logo-v1.png"
CRITICAL_RAMZY = CRITICAL_DIR / "ramzy-avatar-v1.png"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

# Exact live source after FAST-REFRESH-V1 + CRITICAL-RENDER-V2-R1.
EXPECTED_APP_SHA256 = "6171ef0655bbd25e0e5ee250e1a32ff9a85127e1dbe48d69291e350c37f25071"
EXPECTED_INDEX_SHA256 = "4b142af6f5b8dec2e09b55533c2f645a257c0e8900375bdb14470dc645e54121"
EXPECTED_INDEX_CSS_BLOB_SHA = "9680e7af91efb98b92481c811ab807d84dfc0152"
EXPECTED_RAMZY_BLOB_SHA = "6442209ed3bc827cce45e93ec983bb2502298bf5"
FAST_REFRESH_MARKER = "tos.projects.summary.fast-refresh.v1"
CRITICAL_RENDER_MARKER = "data-tos-critical-render-v2"
TCS_V16_MARKER = "--tos-tcs-flagship-v1-6-premium-menus-voice-search-runtime"
NEW_LOGO_URL = "/assets/critical/tos-logo-v1.png"
NEW_RAMZY_URL = "/assets/critical/ramzy-avatar-v1.png"

print("RUNNING=TOS_GLOBAL_PERFORMANCE_POST_PAINT_ASSET_DELIVERY_V1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


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


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label} anchor mismatch: {count}")
    return source.replace(old, new, 1)


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("POST_PAINT_ASSET_V1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (FRONTEND, APP, INDEX, INDEX_CSS, RAMZY, PROJECTS_HOOK, TCS_STYLE, PUBLIC, SOURCE_LOGO, SOURCE_RAMZY, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(APP) != EXPECTED_APP_SHA256:
    fail(f"App.jsx Critical Render V2 baseline mismatch: {sha256(APP)}")
if sha256(INDEX) != EXPECTED_INDEX_SHA256:
    fail(f"index.html Critical Render V2 baseline mismatch: {sha256(INDEX)}")
if git_blob_sha(INDEX_CSS) != EXPECTED_INDEX_CSS_BLOB_SHA:
    fail(f"index.css baseline mismatch: {git_blob_sha(INDEX_CSS)}")
if git_blob_sha(RAMZY) != EXPECTED_RAMZY_BLOB_SHA:
    fail(f"RamzyAssistant.jsx baseline mismatch: {git_blob_sha(RAMZY)}")
if FAST_REFRESH_MARKER not in PROJECTS_HOOK.read_text(encoding="utf-8"):
    fail("Fast Refresh V1 marker missing")
if CRITICAL_RENDER_MARKER not in INDEX.read_text(encoding="utf-8"):
    fail("Critical Render V2 marker missing")
if TCS_V16_MARKER not in TCS_STYLE.read_text(encoding="utf-8"):
    fail("TCS V1.6 marker missing")
if CRITICAL_LOGO.exists() or CRITICAL_RAMZY.exists():
    fail("critical v1 asset already exists; refusing non-idempotent reapply")

originals = {
    APP: APP.read_text(encoding="utf-8"),
    INDEX: INDEX.read_text(encoding="utf-8"),
    INDEX_CSS: INDEX_CSS.read_text(encoding="utf-8"),
    RAMZY: RAMZY.read_text(encoding="utf-8"),
}
created_assets = []


def rollback_sources():
    for path, content in originals.items():
        try:
            path.write_text(content, encoding="utf-8")
        except Exception:
            pass
    for path in created_assets:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
    try:
        if CRITICAL_DIR.exists() and not any(CRITICAL_DIR.iterdir()):
            CRITICAL_DIR.rmdir()
    except Exception:
        pass


try:
    CRITICAL_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_LOGO, CRITICAL_LOGO)
    created_assets.append(CRITICAL_LOGO)
    shutil.copy2(SOURCE_RAMZY, CRITICAL_RAMZY)
    created_assets.append(CRITICAL_RAMZY)

    app = originals[APP]
    index = originals[INDEX]
    index_css = originals[INDEX_CSS]
    ramzy = originals[RAMZY]

    # Use the versioned /assets path for the default TOS logo. /assets is already
    # served by the existing immutable static-asset policy, unlike root PNGs.
    app = replace_once(
        app,
        'if (!raw || raw.startsWith("data:")) return "url(\\"/logo.png\\")";',
        'if (!raw || raw.startsWith("data:") || raw === "/logo.png" || raw === "/tamiyouz-logo.png") return "url(\\"/assets/critical/tos-logo-v1.png\\")";',
        "runtime logo fallback",
    )
    index_css = replace_once(
        index_css,
        '--tos-logo-image: url("/logo.png");',
        '--tos-logo-image: url("/assets/critical/tos-logo-v1.png");',
        "central logo variable",
    )

    # Discover the two critical post-paint images from HTML immediately instead
    # of waiting for React.lazy or a CSS background to reveal their URLs.
    old_favicon = '    <link rel="icon" type="image/png" href="/logo.png" />'
    new_favicon = '''    <link rel="icon" type="image/png" href="/assets/critical/tos-logo-v1.png" />
    <link rel="preload" href="/assets/critical/tos-logo-v1.png" as="image" type="image/png" fetchpriority="high" data-tos-critical-logo-preload="v1" />
    <link rel="preload" href="/assets/critical/ramzy-avatar-v1.png" as="image" type="image/png" fetchpriority="high" data-tos-ramzy-avatar-preload="v1" />'''
    index = replace_once(index, old_favicon, new_favicon, "critical asset preloads")

    # Ramzy stays lazy-split. Only its image URL/discovery priority changes.
    old_panel_avatar = '<img src="/ramzy-avatar.png" alt={isEnglish ? "Ramzy" : "رمزي"} />'
    new_panel_avatar = '<img src="/assets/critical/ramzy-avatar-v1.png" alt={isEnglish ? "Ramzy" : "رمزي"} loading="eager" decoding="async" fetchPriority="high" />'
    ramzy = replace_once(ramzy, old_panel_avatar, new_panel_avatar, "Ramzy panel avatar")
    old_launcher_avatar = '<span className="ramzy-avatar-ring"><img src="/ramzy-avatar.png" alt={isEnglish ? "Ramzy" : "رمزي"} draggable="false" /><i /></span>'
    new_launcher_avatar = '<span className="ramzy-avatar-ring"><img src="/assets/critical/ramzy-avatar-v1.png" alt={isEnglish ? "Ramzy" : "رمزي"} draggable="false" loading="eager" decoding="async" fetchPriority="high" /><i /></span>'
    ramzy = replace_once(ramzy, old_launcher_avatar, new_launcher_avatar, "Ramzy launcher avatar")

    for token, source in (
        ('/assets/critical/tos-logo-v1.png', app),
        ('/assets/critical/tos-logo-v1.png', index_css),
        ('data-tos-critical-logo-preload="v1"', index),
        ('data-tos-ramzy-avatar-preload="v1"', index),
        ('/assets/critical/ramzy-avatar-v1.png', ramzy),
        ('fetchPriority="high"', ramzy),
    ):
        if token not in source:
            raise RuntimeError(f"post-transform token missing: {token}")
    if ramzy.count('/assets/critical/ramzy-avatar-v1.png') != 2:
        raise RuntimeError(f"Ramzy critical avatar reference count mismatch: {ramzy.count('/assets/critical/ramzy-avatar-v1.png')}")

    APP.write_text(app, encoding="utf-8")
    INDEX.write_text(index, encoding="utf-8")
    INDEX_CSS.write_text(index_css, encoding="utf-8")
    RAMZY.write_text(ramzy, encoding="utf-8")
except Exception as exc:
    rollback_sources()
    fail(f"source transform failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    rollback_sources()
    fail("frontend build failed; source rolled back")

if not DIST.exists() or not (DIST / "index.html").exists():
    rollback_sources()
    fail("dist/index.html missing after build")

dist_index = (DIST / "index.html").read_text(encoding="utf-8", errors="ignore")
for token in (
    'data-tos-critical-logo-preload="v1"',
    'data-tos-ramzy-avatar-preload="v1"',
    NEW_LOGO_URL,
    NEW_RAMZY_URL,
    CRITICAL_RENDER_MARKER,
):
    if token not in dist_index:
        rollback_sources()
        fail(f"dist index verification token missing: {token}")

for rel, source in (
    ("assets/critical/tos-logo-v1.png", SOURCE_LOGO),
    ("assets/critical/ramzy-avatar-v1.png", SOURCE_RAMZY),
):
    emitted = DIST / rel
    if not emitted.exists():
        rollback_sources()
        fail(f"critical emitted asset missing: {rel}")
    if sha256(emitted) != sha256(source):
        rollback_sources()
        fail(f"critical emitted asset content mismatch: {rel}")

# Preserve the previous performance/TCS runtime state and prove Ramzy still lives
# outside the entry chunk while the avatar URL is available from HTML immediately.
for marker in (
    FAST_REFRESH_MARKER.encode(),
    b"tcs-v16-voice-button",
    b"data-tcs-ramzy-collision-sync",
    NEW_RAMZY_URL.encode(),
):
    if tree_count(DIST, marker) < 1:
        rollback_sources()
        fail(f"preserved/runtime marker missing from dist: {marker.decode(errors='ignore')}")

entry_match = re.search(r'<script[^>]+type="module"[^>]+src="([^"]+\\.js)"', dist_index) or re.search(r'<script[^>]+src="([^"]+\\.js)"[^>]+type="module"', dist_index)
if not entry_match:
    rollback_sources()
    fail("could not identify entry JS")
entry_path = DIST / entry_match.group(1).lstrip("/")
if not entry_path.exists():
    rollback_sources()
    fail("entry JS missing")
if b"tos.ramzy.position" in entry_path.read_bytes():
    rollback_sources()
    fail("Ramzy implementation regressed into entry JS")

# Safe live deploy: candidate + atomic rename, no service restart.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.post-paint-assets-v1-candidate-{ts}"
backup = LIVE_PARENT / f"build.post-paint-assets-v1-backup-{ts}"
if candidate.exists():
    shutil.rmtree(candidate)
shutil.copytree(DIST, candidate)
if not (candidate / "index.html").exists():
    rollback_sources()
    fail("candidate index missing")
try:
    if LIVE.exists():
        LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists():
            shutil.rmtree(LIVE)
    except Exception:
        pass
    try:
        if backup.exists() and not LIVE.exists():
            backup.rename(LIVE)
    except Exception:
        pass
    rollback_sources()
    fail(f"live deploy failed: {exc}")

# Read-only post-deploy header verification. Failure to reach the public URL is
# reported as UNVERIFIED rather than mutating Nginx or restarting anything.
def cache_header(url: str) -> str:
    try:
        result = subprocess.run(
            ["curl", "-sSIL", "--max-time", "8", url],
            text=True,
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            return "UNAVAILABLE"
        values = []
        for line in result.stdout.splitlines():
            if line.lower().startswith("cache-control:"):
                values.append(line.split(":", 1)[1].strip())
        return values[-1] if values else "MISSING"
    except Exception:
        return "UNAVAILABLE"

logo_cache = cache_header("https://tos.tamiyouz.com/assets/critical/tos-logo-v1.png")
ramzy_cache = cache_header("https://tos.tamiyouz.com/assets/critical/ramzy-avatar-v1.png")
cache_verified = all("max-age" in value.lower() and "no-store" not in value.lower() for value in (logo_cache, ramzy_cache))

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("POST_PAINT_ASSET_V1_RUNTIME=YES")
print("CRITICAL_LOGO_URL=" + NEW_LOGO_URL)
print("CRITICAL_RAMZY_AVATAR_URL=" + NEW_RAMZY_URL)
print("CRITICAL_LOGO_HTML_PRELOAD=YES")
print("CRITICAL_RAMZY_HTML_PRELOAD=YES")
print("RAMZY_JS_LAZY_SPLIT_PRESERVED=YES")
print("RAMZY_AVATAR_WATERFALL=EARLY_IMAGE_DISCOVERY")
print("RAMZY_AVATAR_FETCH_PRIORITY=HIGH")
print("RAMZY_AVATAR_DECODING=ASYNC")
print("ROOT_LOGO_DEFAULT_REFERENCE=REMOVED_FROM_THEME_FALLBACK")
print("ROOT_RAMZY_REFERENCE=REMOVED_FROM_COMPONENT")
print("CRITICAL_ASSET_VERSIONED_PATH=YES")
print(f"CRITICAL_LOGO_CACHE_CONTROL={logo_cache}")
print(f"CRITICAL_RAMZY_CACHE_CONTROL={ramzy_cache}")
print("CRITICAL_ASSET_CACHE_POLICY=" + ("VERIFIED_CACHEABLE" if cache_verified else "UNVERIFIED"))
print("FAST_REFRESH_V1_PRESERVED=YES")
print("CRITICAL_RENDER_V2_PRESERVED=YES")
print("TCS_V1_6_PRESERVED=YES")
print("RAMZY_FUNCTIONALITY_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("AUTH_CHANGED=NO")
print(f"ENTRY_CHUNK_BYTES={entry_path.stat().st_size}")
print(f"APP_SHA256={sha256(APP)}")
print(f"INDEX_SHA256={sha256(INDEX)}")
print(f"INDEX_CSS_SHA256={sha256(INDEX_CSS)}")
print(f"RAMZY_SHA256={sha256(RAMZY)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")