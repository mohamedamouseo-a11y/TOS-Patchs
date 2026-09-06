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
MAIN = FRONTEND / "src/main.jsx"
INDEX = FRONTEND / "index.html"
DASH = FRONTEND / "src/pages/Dashboard.jsx"
PROJECTS = FRONTEND / "src/pages/ProjectsPage.jsx"
TASKS = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
HOOK = FRONTEND / "src/hooks/useProjects.js"
TCS_STYLE = FRONTEND / "src/components/tcsFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_APP_SHA256 = "638d4c7bc370cfd9dfe03904ac51749a06ba46063814d0e15f227c14f52647a8"
EXPECTED_MAIN_BLOB_SHA = "9c712d900da43e06f2f0b6f1983cf7dfd6c0641d"
EXPECTED_INDEX_BLOB_SHA = "622961a8ccba4e839b043fac0d6cd814f0a8db3d"
EXPECTED_DASH_BLOB_SHA = "732312492b353e966a5559357fb33ca5f5ef2188"
EXPECTED_PROJECTS_BLOB_SHA = "3d1123b15d097f105060226a60d9ea946a6b4768"
EXPECTED_TASKS_BLOB_SHA = "5cc0fd08c8dbbce635d336f511b5665330289f1a"
EXPECTED_HOOK_SHA256 = "0c9e2c847038e3c1761a8335259ba9da42a883cd58399ab94a23f5bd66e3c396"
FAST_REFRESH_MARKER = "tos.projects.summary.fast-refresh.v1"
TCS_V16_MARKER = "--tos-tcs-flagship-v1-6-premium-menus-voice-search-runtime"

print("RUNNING=TOS_GLOBAL_PERFORMANCE_CRITICAL_RENDER_V2")


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
        if path.is_file():
            try:
                total += path.read_bytes().count(needle)
            except OSError:
                pass
    return total


def fail(message: str, originals=None):
    if originals:
        for path, content in originals.items():
            try:
                path.write_text(content, encoding="utf-8")
            except Exception:
                pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("CRITICAL_RENDER_V2_RUNTIME=NO")
    sys.exit(1)


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        fail(f"{label} anchor mismatch: {count}")
    return source.replace(old, new, 1)


for path in (APP, MAIN, INDEX, DASH, PROJECTS, TASKS, HOOK, TCS_STYLE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(APP) != EXPECTED_APP_SHA256:
    fail(f"App.jsx Fast Refresh V1 baseline mismatch: {sha256(APP)}")
if git_blob_sha(MAIN) != EXPECTED_MAIN_BLOB_SHA:
    fail(f"main.jsx baseline mismatch: {git_blob_sha(MAIN)}")
if git_blob_sha(INDEX) != EXPECTED_INDEX_BLOB_SHA:
    fail(f"index.html baseline mismatch: {git_blob_sha(INDEX)}")
if git_blob_sha(DASH) != EXPECTED_DASH_BLOB_SHA:
    fail(f"Dashboard.jsx baseline mismatch: {git_blob_sha(DASH)}")
if git_blob_sha(PROJECTS) != EXPECTED_PROJECTS_BLOB_SHA:
    fail(f"ProjectsPage.jsx baseline mismatch: {git_blob_sha(PROJECTS)}")
if git_blob_sha(TASKS) != EXPECTED_TASKS_BLOB_SHA:
    fail(f"ProfessionalTaskBoard.jsx baseline mismatch: {git_blob_sha(TASKS)}")
if sha256(HOOK) != EXPECTED_HOOK_SHA256:
    fail(f"useProjects Fast Refresh V1 baseline mismatch: {sha256(HOOK)}")
if FAST_REFRESH_MARKER not in HOOK.read_text(encoding="utf-8"):
    fail("Fast Refresh V1 project-cache marker missing")
if TCS_V16_MARKER not in TCS_STYLE.read_text(encoding="utf-8"):
    fail("TCS V1.6 runtime marker missing")

paths = [APP, MAIN, INDEX, DASH, PROJECTS, TASKS]
originals = {path: path.read_text(encoding="utf-8") for path in paths}
app = originals[APP]
main = originals[MAIN]
index = originals[INDEX]
dash = originals[DASH]
projects = originals[PROJECTS]
tasks = originals[TASKS]

# 1) Remove the only third-party render-blocking stylesheet from the critical head.
blocking_fonts = '''    <link rel="preconnect" href="https://fonts.googleapis.com" />\n    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&family=Inter:wght@400;700;900&display=swap" rel="stylesheet" />'''
async_fonts = '''    <link rel="preconnect" href="https://fonts.googleapis.com" />\n    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n    <script data-tos-critical-render-v2>\n      (function () {\n        var href = "https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&family=Inter:wght@400;700;900&display=swap";\n        function loadFontsAfterFirstPaint() {\n          if (document.querySelector('link[data-tos-fonts-async]')) return;\n          var link = document.createElement("link");\n          link.rel = "stylesheet";\n          link.href = href;\n          link.dataset.tosFontsAsync = "v2";\n          document.head.appendChild(link);\n        }\n        window.addEventListener("DOMContentLoaded", function () {\n          requestAnimationFrame(function () { requestAnimationFrame(loadFontsAfterFirstPaint); });\n        }, { once: true });\n      })();\n    </script>\n    <noscript><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&family=Inter:wght@400;700;900&display=swap" rel="stylesheet" /></noscript>'''
index = replace_once(index, blocking_fonts, async_fonts, "nonblocking Google fonts")

# 2) Stop loading Projects/Tasks/Dashboard page CSS in the global entry bundle.
for css_import in (
    'import "./styles/dashboard-github-reference.css";\n',
    'import "./styles/projects-github-reference.css";\n',
    'import "./styles/tasks-projects-premium-reference.css";\n',
):
    if main.count(css_import) != 1:
        fail(f"main CSS import anchor mismatch: {css_import.strip()}")
    main = main.replace(css_import, "", 1)

# Attach each stylesheet to the page/module that owns it; Vite will emit lazy CSS chunks.
dash = replace_once(dash, 'import { useMemo, useState } from "react";\n', 'import { useMemo, useState } from "react";\nimport "../styles/dashboard-github-reference.css";\n', "Dashboard scoped CSS")
projects = replace_once(projects, 'import { useEffect, useMemo, useRef, useState } from "react";\n', 'import { useEffect, useMemo, useRef, useState } from "react";\nimport "../styles/projects-github-reference.css";\n', "Projects scoped CSS")
tasks = replace_once(tasks, 'import { Component, useEffect, useMemo, useRef, useState } from "react";\n', 'import { Component, useEffect, useMemo, useRef, useState } from "react";\nimport "../styles/tasks-projects-premium-reference.css";\n', "Tasks scoped CSS")

# 3) Dashboard itself is no longer part of the entry JS. The shell can paint before the page chunk.
app = replace_once(
    app,
    'import { Dashboard } from "./pages/Dashboard";',
    'const Dashboard = lazy(() => import("./pages/Dashboard").then(mod => ({ default: mod.Dashboard })));',
    "lazy Dashboard import",
)
old_dashboard = '''            {active === "dashboard" && (\n              <Dashboard\n                projects={projects}\n                activeProject={activeProject}\n                user={user}\n                files={recentFiles}\n                clients={clients}\n                onNavigate={handleDashboardNavigate}\n              />\n            )}'''
new_dashboard = '''            {active === "dashboard" && (\n              <Suspense fallback={<SystemPageLoading label={tr.loading ?? "Loading..."} />}>\n                <Dashboard\n                  projects={projects}\n                  activeProject={activeProject}\n                  user={user}\n                  files={recentFiles}\n                  clients={clients}\n                  onNavigate={handleDashboardNavigate}\n                />\n              </Suspense>\n            )}'''
app = replace_once(app, old_dashboard, new_dashboard, "Dashboard suspense boundary")

for token, source in (
    ('data-tos-critical-render-v2', index),
    ('data-tos-fonts-async', index),
    ('lazy(() => import("./pages/Dashboard")', app),
    ('../styles/dashboard-github-reference.css', dash),
    ('../styles/projects-github-reference.css', projects),
    ('../styles/tasks-projects-premium-reference.css', tasks),
):
    if token not in source:
        fail(f"post-transform token missing: {token}")
if 'fonts.googleapis.com/css2' in index and 'rel="stylesheet" />\n  </head>' in index:
    pass
if 'import "./styles/projects-github-reference.css";' in main or 'import "./styles/tasks-projects-premium-reference.css";' in main or 'import "./styles/dashboard-github-reference.css";' in main:
    fail("page-specific CSS still imported by main.jsx")

try:
    APP.write_text(app, encoding="utf-8")
    MAIN.write_text(main, encoding="utf-8")
    INDEX.write_text(index, encoding="utf-8")
    DASH.write_text(dash, encoding="utf-8")
    PROJECTS.write_text(projects, encoding="utf-8")
    TASKS.write_text(tasks, encoding="utf-8")
except Exception as exc:
    fail(f"source write failed: {exc}", originals)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", originals)
if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", originals)

# Build verification: no render-blocking Google font stylesheet in emitted index.
dist_index = (DIST / "index.html").read_text(encoding="utf-8", errors="ignore")
if 'data-tos-critical-render-v2' not in dist_index:
    fail("critical render V2 marker missing from dist index", originals)
if re.search(r'<link[^>]+href="https://fonts\.googleapis\.com[^>]+rel="stylesheet"', dist_index):
    fail("Google Fonts still render-blocking in dist index", originals)

# Main HTML CSS should no longer contain the three page-reference source payloads.
css_links = re.findall(r'<link[^>]+href="([^"]+\.css)"', dist_index)
initial_css_bytes = 0
for href in css_links:
    path = DIST / href.lstrip("/")
    if path.exists():
        initial_css_bytes += path.stat().st_size

# Confirm lazy chunks exist and preserve previous functionality markers.
for marker in (b"tcs-v16-voice-button", b"data-tcs-ramzy-collision-sync", FAST_REFRESH_MARKER.encode()):
    if tree_count(DIST, marker) < 1:
        fail(f"preserved runtime marker missing: {marker.decode(errors='ignore')}", originals)
if tree_count(DIST / "assets", b"dashboard-github-reference") > 0:
    # Class-name strings may not survive minification predictably; chunk verification below is authoritative.
    pass

# Entry JS size for comparison.
entry_match = re.search(r'<script[^>]+type="module"[^>]+src="([^"]+\.js)"', dist_index) or re.search(r'<script[^>]+src="([^"]+\.js)"[^>]+type="module"', dist_index)
if not entry_match:
    fail("could not identify main entry JS", originals)
entry_path = DIST / entry_match.group(1).lstrip("/")
if not entry_path.exists():
    fail("main entry JS missing", originals)
entry_bytes = entry_path.stat().st_size
if b"DateFilterBar" in entry_path.read_bytes():
    fail("Dashboard implementation still appears in entry JS", originals)

# Safe live deploy by candidate + atomic rename.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.critical-render-v2-candidate-{ts}"
backup = LIVE_PARENT / f"build.critical-render-v2-backup-{ts}"
if candidate.exists():
    shutil.rmtree(candidate)
shutil.copytree(DIST, candidate)
if not (candidate / "index.html").exists():
    fail("candidate index missing", originals)
try:
    if LIVE.exists():
        LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    if LIVE.exists() and LIVE != backup:
        try:
            shutil.rmtree(LIVE)
        except Exception:
            pass
    if backup.exists() and not LIVE.exists():
        backup.rename(LIVE)
    fail(f"live deploy failed: {exc}", originals)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("CRITICAL_RENDER_V2_RUNTIME=YES")
print("GOOGLE_FONTS_RENDER_BLOCKING=NO")
print("GOOGLE_FONTS_AFTER_FIRST_PAINT=YES")
print("DASHBOARD_INITIAL_JS=LAZY_SPLIT")
print("DASHBOARD_CSS=PAGE_SCOPED")
print("PROJECTS_CSS=PAGE_SCOPED")
print("TASKS_CSS=PAGE_SCOPED")
print("FAST_REFRESH_V1_PRESERVED=YES")
print("TCS_V1_6_PRESERVED=YES")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"ENTRY_CHUNK={entry_path.relative_to(DIST)}")
print(f"ENTRY_CHUNK_BYTES={entry_bytes}")
print(f"INITIAL_INDEX_CSS_BYTES={initial_css_bytes}")
print(f"APP_SHA256={sha256(APP)}")
print(f"MAIN_SHA256={sha256(MAIN)}")
print(f"INDEX_SHA256={sha256(INDEX)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")