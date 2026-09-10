from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
SETTINGS = FRONTEND / "src/pages/SettingsPage.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
ROUTES = FRONTEND / "src/lib/pageRoutes.js"
TGWS_PAGE = FRONTEND / "src/pages/TgwsPage.jsx"
TGWS_SETTINGS_COMPONENT = FRONTEND / "src/components/settings/TgwsSettingsAdmin.jsx"
TGWS_API = FRONTEND / "src/api/tgwsApi.js"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_BLOBS = {
    SETTINGS: "71e818372e1eee6ed08b1394ff3801bb88a5de90",
    APP: "344fd9ccf5417b83f1a0b30a3cdfce4ec48c2dd0",
    SIDEBAR: "65da272b02dbf06c726a1a0ac9e56be896b1cf88",
    ROUTES: "ddd73a59a7876c18259dc70a707c941cc5659a9c",
}


def fail(message):
    raise RuntimeError(message)


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        fail(f"{label} marker count changed unexpectedly: {count}")
    return source.replace(old, new, 1)


for path, expected in EXPECTED_BLOBS.items():
    if not path.exists():
        fail(f"required source file missing: {path}")
    actual = git_blob_sha(path)
    if actual != expected:
        fail(f"baseline changed for {path}: expected={expected} actual={actual}")

for path in (TGWS_PAGE, TGWS_SETTINGS_COMPONENT, TGWS_API):
    if not path.exists():
        fail(f"TGWS dormant implementation file missing unexpectedly: {path}")

# Preserve implementation/backend-facing modules in this phase. Only remove frontend runtime entry points.
dormant_hashes = {path: sha256(path) for path in (TGWS_PAGE, TGWS_SETTINGS_COMPONENT, TGWS_API)}

settings = SETTINGS.read_text()
app = APP.read_text()
sidebar = SIDEBAR.read_text()
routes = ROUTES.read_text()

# Settings entry points
settings = replace_once(
    settings,
    'import { TgwsSettingsAdmin } from "../components/settings/TgwsSettingsAdmin";\n',
    "",
    "Settings TGWS import",
)
settings = replace_once(
    settings,
    '  { key: "tgws", labelAr: "TGWS", labelEn: "TGWS", hintAr: "إنشاء ملفات Google الأصلية وسياسات الوصول", hintEn: "Native Google files and access policies", icon: Cloud },\n',
    "",
    "Settings TGWS section",
)
settings = replace_once(
    settings,
    '      case "tgws":\n        return <TgwsSettingsAdmin user={user} />;\n',
    "",
    "Settings TGWS render case",
)

# App runtime page entry points
app = replace_once(
    app,
    'const TgwsPage = lazy(() => import("./pages/TgwsPage").then(mod => ({ default: mod.TgwsPage })));\n',
    "",
    "App TGWS lazy import",
)
app = replace_once(
    app,
    'const PROJECT_LOADING_BLOCKED_PAGES = new Set(["dashboard", "teamPerformance", "projects", "tasks", "myWorkspace", "chat", "files", "tws", "tgws"]);',
    'const PROJECT_LOADING_BLOCKED_PAGES = new Set(["dashboard", "teamPerformance", "projects", "tasks", "myWorkspace", "chat", "files", "tws"]);',
    "App TGWS blocked-page membership",
)
app = replace_once(
    app,
    '    if (active === "tgws" && !hasWorkHubAccess) {\n      setActive("dashboard");\n    }\n',
    "",
    "App TGWS access redirect",
)
app = replace_once(
    app,
    '      case "tgws":     return { title: "TGWS", subtitle: "Tamiyouz Google Workspace" };\n',
    "",
    "App TGWS title metadata",
)
app = replace_once(
    app,
    '            {!loading && active === "tgws" && hasWorkHubAccess && <TgwsPage user={user} projects={projects} />}\n',
    "",
    "App TGWS page render",
)

# Sidebar + Settings sub-navigation entry points
sidebar = replace_once(
    sidebar,
    '  designQueue: Paintbrush, tws: FileText, tgws: HardDrive,  workHub: Briefcase, team: UsersRound, permissions: KeyRound,',
    '  designQueue: Paintbrush, tws: FileText, workHub: Briefcase, team: UsersRound, permissions: KeyRound,',
    "Sidebar TGWS icon map",
)
sidebar = replace_once(
    sidebar,
    '  { id: "workspaceGroup", labelAr: "مساحة العمل", labelEn: "Workspace", icon: ClipboardList, children: ["projects", "tasks", "myWorkspace", "designQueue", "tws", "tgws"] },',
    '  { id: "workspaceGroup", labelAr: "مساحة العمل", labelEn: "Workspace", icon: ClipboardList, children: ["projects", "tasks", "myWorkspace", "designQueue", "tws"] },',
    "Sidebar TGWS workspace child",
)
sidebar = replace_once(
    sidebar,
    '  { id: "tgws", labelAr: "TGWS", labelEn: "TGWS", icon: CloudUpload, superOnly: true },\n',
    "",
    "Sidebar TGWS Settings subnav",
)
sidebar = replace_once(
    sidebar,
    '  if (id === "tgws") return TOS_STAFF_ROLES.has(role);\n',
    "",
    "Sidebar TGWS access rule",
)
sidebar = replace_once(
    sidebar,
    '  if (id === "tgws") return lang === "en" ? "TGWS" : "TGWS — ملفات Google";\n',
    "",
    "Sidebar TGWS label",
)

# Browser route entry point
routes = replace_once(
    routes,
    '  tgws: "/tgws",\n',
    "",
    "TGWS browser route",
)

# Fail-fast post-transform checks on all runtime entry-point files.
for label, source in [
    ("SettingsPage", settings),
    ("App", app),
    ("Sidebar", sidebar),
    ("pageRoutes", routes),
]:
    if "tgws" in source.lower():
        fail(f"unexpected TGWS runtime reference remains in {label}")

# Neighboring features that must remain untouched/present.
for source, markers, label in [
    (settings, [
        'key: "drive"',
        'key: "thrs"',
        'case "drive"',
        'case "thrs"',
        '<Cloud className="crm-pro-flow-node__cloud" />',
    ], "Settings"),
    (app, [
        'const TwsPage = lazy(() => import("./pages/tws/TwsPage")',
        'active === "tws"',
        'case "tws"',
        'active === "workHub"',
    ], "App"),
    (sidebar, [
        'designQueue: Paintbrush, tws: FileText, workHub: Briefcase',
        'children: ["projects", "tasks", "myWorkspace", "designQueue", "tws"]',
        '{ id: "drive", labelAr: "Google Drive"',
        '{ id: "thrs", labelAr: "THRS"',
    ], "Sidebar"),
    (routes, [
        'tws: "/tws"',
        'settings: "/settings"',
        'workHub: "/thrs"',
    ], "pageRoutes"),
]:
    for marker in markers:
        if marker not in source:
            fail(f"protected neighboring {label} marker missing after transform: {marker}")

stamp = int(time.time())
backups = {}
live_backup = None
staging = None
deployed = False

try:
    for path, new_source in [
        (SETTINGS, settings),
        (APP, app),
        (SIDEBAR, sidebar),
        (ROUTES, routes),
    ]:
        backup = path.with_name(f"{path.name}.tgws-frontend-r1-backup-{stamp}")
        shutil.copy2(path, backup)
        backups[path] = backup
        path.write_text(new_source)

    for path, expected_hash in dormant_hashes.items():
        if sha256(path) != expected_hash:
            fail(f"dormant TGWS implementation file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    tgws_chunks = [p.name for p in (DIST / "assets").glob("TgwsPage-*.js")]
    if tgws_chunks:
        fail(f"TGWS page chunk still emitted after full frontend decommission: {tgws_chunks}")

    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for signature in [
        "Tamiyouz Google Workspace",
        "Native Google files and access policies",
        "TGWS — ملفات Google",
    ]:
        if signature in built_js:
            fail(f"TGWS runtime signature still present in production bundle: {signature}")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.tgws-frontend-r1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.tgws-frontend-r1-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)
    deployed = True

    live_chunks = [p.name for p in (LIVE / "assets").glob("TgwsPage-*.js")]
    if live_chunks:
        fail(f"TGWS page chunk still present in live build: {live_chunks}")

    live_js = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.js"))
    for signature in [
        "Tamiyouz Google Workspace",
        "Native Google files and access policies",
        "TGWS — ملفات Google",
    ]:
        if signature in live_js:
            fail(f"TGWS runtime signature still present in live bundle: {signature}")

    for path, expected_hash in dormant_hashes.items():
        if sha256(path) != expected_hash:
            fail(f"dormant TGWS implementation file changed after deploy: {path}")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TGWS_FRONTEND_DECOMMISSION_R1_RUNTIME=YES")
    print("TGWS_SETTINGS_ENTRY_POINTS_REMOVED=YES")
    print("TGWS_SIDEBAR_ENTRY_REMOVED=YES")
    print("TGWS_APP_RENDER_PATH_REMOVED=YES")
    print("TGWS_BROWSER_ROUTE_REMOVED=YES")
    print("TGWS_PAGE_CHUNK_EMITTED=NO")
    print("TGWS_DIRECT_ROUTE_RUNTIME=DISABLED")
    print("TGWS_DORMANT_SOURCE_FILES_PRESERVED=YES")
    print("TGWS_BACKEND_CHANGED=NO")
    print("TGWS_DATABASE_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("GOOGLE_DRIVE_CHANGED=NO")
    print(f"SETTINGS_SHA256_AFTER={sha256(SETTINGS)}")
    print(f"APP_SHA256_AFTER={sha256(APP)}")
    print(f"SIDEBAR_SHA256_AFTER={sha256(SIDEBAR)}")
    print(f"ROUTES_SHA256_AFTER={sha256(ROUTES)}")
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")

except Exception as exc:
    if deployed:
        try:
            if LIVE.exists():
                shutil.rmtree(LIVE)
            if live_backup and live_backup.exists():
                live_backup.rename(LIVE)
        except Exception as rollback_exc:
            print(f"LIVE_ROLLBACK_ERROR={rollback_exc}")
    elif staging and staging.exists():
        shutil.rmtree(staging, ignore_errors=True)

    for path, backup in backups.items():
        try:
            if backup.exists():
                shutil.copy2(backup, path)
        except Exception as rollback_exc:
            print(f"SOURCE_ROLLBACK_ERROR={path}:{rollback_exc}")

    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise
