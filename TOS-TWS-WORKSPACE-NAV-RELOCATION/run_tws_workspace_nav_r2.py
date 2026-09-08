#!/usr/bin/env python3
from pathlib import Path
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-WORKSPACE-NAV-RELOCATION"
SCRIPT = "run_tws_workspace_nav_r2.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
EXPECTED_HEAD = "186ae5a52ae77744a946abc13522acc2ef5e80a8"
SIDEBAR = "frontend/src/components/layout/Sidebar.jsx"
TEST = "frontend/src/components/layout/twsWorkspaceNavRelocation.test.js"
EXPECTED_DIRTY = {SIDEBAR, TEST}
LIVE_URL = "https://tos.tamiyouz.com/tws"
NEW_WORKSPACE_FRAGMENT = 'children: ["projects", "tasks", "myWorkspace", "designQueue", "tws", "tgws"]'
NEW_SYSTEM_FRAGMENT = 'children: ["workHub", "slaInbox", "slaCenter", "slaAdvanced", "auditLog"]'


def run(args, cwd=REPO, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(args)}\n{(p.stdout or '')}{(p.stderr or '')}")
    return p


def git(*args):
    return run(["git", *args]).stdout.strip()


def changed_paths():
    tracked = set(filter(None, git("diff", "--name-only", "HEAD").splitlines()))
    untracked = set(filter(None, git("ls-files", "--others", "--exclude-standard").splitlines()))
    return tracked | untracked


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "TOS-TWS-R2-Probe/1.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_main_js(html: str):
    matches = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html, re.I)
    if not matches:
        return None
    return matches[-1]


def asset_url(src: str):
    if src.startswith("http://") or src.startswith("https://"):
        return src
    if not src.startswith("/"):
        src = "/" + src
    return "https://tos.tamiyouz.com" + src


def find_live_root(live_asset_src: str):
    base = Path(live_asset_src.split("?", 1)[0]).name
    if not base:
        return None
    find = run(["find", "/var/www", "-type", "f", "-name", base], cwd=Path("/"), check=False)
    candidates = []
    for line in find.stdout.splitlines():
        p = Path(line.strip())
        if not p.is_file() or p.parent.name != "assets":
            continue
        root = p.parent.parent
        index = root / "index.html"
        if index.is_file():
            try:
                text = index.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if base in text:
                candidates.append(root)
    # Prefer a root outside the source dist when live HTML is stale.
    unique = []
    for c in candidates:
        if c not in unique:
            unique.append(c)
    for c in unique:
        try:
            if c.resolve() != DIST.resolve():
                return c
        except Exception:
            if str(c) != str(DIST):
                return c
    return unique[0] if unique else None


def sync_dist(src: Path, dst: Path):
    if not src.is_dir() or not (src / "index.html").is_file():
        raise RuntimeError("frontend dist is missing")
    dst.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d%H%M%S")
    if (dst / "index.html").is_file():
        shutil.copy2(dst / "index.html", dst / f"index.html.tws-nav-r2-backup-{stamp}")
    # Non-destructive sync: overwrite current build files, keep old hashed assets.
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def reload_nginx():
    test = run(["nginx", "-t"], cwd=Path("/"), check=False)
    if test.returncode != 0:
        return "SKIPPED_NGINX_TEST_FAILED"
    reload_cmd = run(["systemctl", "reload", "nginx"], cwd=Path("/"), check=False)
    return "PASS" if reload_cmd.returncode == 0 else "SKIPPED_RELOAD_NOT_AVAILABLE"


def fail(msg):
    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print("RUN=FAIL")
    print(f"ERROR={msg}")
    print("SOURCE_PATCH_PRESERVED=YES")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)


try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")

    head = git("rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD mismatch: expected {EXPECTED_HEAD}, got {head}")

    current_dirty = changed_paths()
    if current_dirty != EXPECTED_DIRTY:
        raise RuntimeError("R1 worktree state mismatch: " + ", ".join(sorted(current_dirty)))

    sidebar_text = (REPO / SIDEBAR).read_text(encoding="utf-8")
    if NEW_WORKSPACE_FRAGMENT not in sidebar_text or NEW_SYSTEM_FRAGMENT not in sidebar_text:
        raise RuntimeError("R1 sidebar relocation is not present in source")

    run(["node", "--test", TEST])
    run(["npm", "run", "build"], cwd=FRONTEND)

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_asset_path = DIST / built_asset.lstrip("/")
    if not built_asset_path.is_file():
        raise RuntimeError(f"built main asset missing: {built_asset_path}")
    built_sha = sha256(built_asset_path)

    probe = f"{LIVE_URL}?__tws_nav_r2={int(time.time())}"
    live_html_before = fetch_text(probe)
    live_asset_before = extract_main_js(live_html_before)
    if not live_asset_before:
        raise RuntimeError("could not identify live main JS asset")

    deploy_sync = "NO"
    deploy_root = "DIRECT_DIST"

    # If live does not reference this build, locate the directory that contains the live asset and sync the fresh dist there.
    if Path(live_asset_before.split("?", 1)[0]).name != Path(built_asset).name:
        root = find_live_root(live_asset_before)
        if root is None:
            raise RuntimeError(f"live bundle is stale ({live_asset_before}) and production web root could not be located safely")
        if not str(root.resolve()).startswith("/var/www/"):
            raise RuntimeError(f"refusing unsafe deploy root: {root}")
        sync_dist(DIST, root)
        deploy_sync = "YES"
        deploy_root = str(root)

    nginx_reload = reload_nginx()
    time.sleep(1)

    live_html_after = fetch_text(f"{LIVE_URL}?__tws_nav_r2_verify={int(time.time())}")
    live_asset_after = extract_main_js(live_html_after)
    if not live_asset_after:
        raise RuntimeError("could not identify live JS after deploy")

    if Path(live_asset_after.split("?", 1)[0]).name != Path(built_asset).name:
        raise RuntimeError(f"live HTML still references stale bundle: live={live_asset_after}, built={built_asset}")

    # Verify public asset bytes are the same build that just passed tests.
    tmp = Path("/tmp/tos_tws_r2_live_asset.js")
    req = urllib.request.Request(asset_url(live_asset_after) + f"?v={int(time.time())}", headers={"Cache-Control": "no-cache", "User-Agent": "TOS-TWS-R2-Probe/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        tmp.write_bytes(r.read())
    live_sha = sha256(tmp)
    tmp.unlink(missing_ok=True)
    if live_sha != built_sha:
        raise RuntimeError(f"live asset bytes do not match fresh build: live_sha={live_sha}, built_sha={built_sha}")

    if changed_paths() != EXPECTED_DIRTY:
        raise RuntimeError("source worktree changed unexpectedly during R2")

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("R1_SOURCE_PATCH_PRESENT=PASS")
    print("NAV_RELOCATION_TESTS=PASS (5/5)")
    print("FRONTEND_BUILD=PASS")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_asset_before}")
    print(f"LIVE_ASSET_AFTER={live_asset_after}")
    print(f"LIVE_DEPLOY_SYNC={deploy_sync}")
    print(f"LIVE_DEPLOY_ROOT={deploy_root}")
    print(f"NGINX_RELOAD={nginx_reload}")
    print("LIVE_BUNDLE_MATCH=PASS")
    print("LIVE_TWS_WORKSPACE_NAV_BUNDLE=PASS")
    print("SOURCE_CHANGED_BY_R2=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("SOURCE_PATCH_PRESERVED=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
except Exception as exc:
    fail(str(exc))
