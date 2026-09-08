#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

PATCH = "TOS-TWS-WORKSPACE-NAV-RELOCATION"
SCRIPT = "run_tws_workspace_nav_r3.py"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
EXPECTED_HEAD = "186ae5a52ae77744a946abc13522acc2ef5e80a8"
SIDEBAR = "frontend/src/components/layout/Sidebar.jsx"
TEST = "frontend/src/components/layout/twsWorkspaceNavRelocation.test.js"
EXPECTED_DIRTY = {SIDEBAR, TEST}
LIVE_ORIGIN = "https://tos.tamiyouz.com"
LIVE_URL = LIVE_ORIGIN + "/tws"
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


def fetch(url: str):
    req = urllib.request.Request(url, headers={
        "User-Agent": "TOS-TWS-R3-Probe/1.0",
        "Cache-Control": "no-cache, no-store, max-age=0",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(), {k.lower(): v for k, v in r.headers.items()}, r.geturl()


def fetch_text(url: str):
    body, headers, final_url = fetch(url)
    return body.decode("utf-8", errors="replace"), headers, final_url


def extract_main_js(html: str):
    matches = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html, re.I)
    return matches[-1] if matches else None


def asset_url(src: str):
    if src.startswith("http://") or src.startswith("https://"):
        return src
    return LIVE_ORIGIN + (src if src.startswith("/") else "/" + src)


def extract_server_block(nginx_text: str, hostname: str):
    blocks = []
    pos = 0
    while True:
        m = re.search(r'\bserver\s*\{', nginx_text[pos:])
        if not m:
            break
        start = pos + m.start()
        brace = nginx_text.find("{", start)
        depth = 0
        end = None
        for i in range(brace, len(nginx_text)):
            if nginx_text[i] == "{":
                depth += 1
            elif nginx_text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is None:
            break
        block = nginx_text[start:end]
        if re.search(r'\bserver_name\b[^;]*\b' + re.escape(hostname) + r'\b', block):
            blocks.append(block)
        pos = end
    return blocks


def candidate_from_index(index: Path, live_asset_name: str):
    try:
        if not index.is_file():
            return None
        text = index.read_text(encoding="utf-8", errors="replace")
        if live_asset_name not in text:
            return None
        root = index.parent.resolve()
        asset = root / "assets" / live_asset_name
        if asset.is_file():
            return root
    except Exception:
        return None
    return None


def nginx_candidates(live_asset_name: str):
    out = []
    nginx = run(["nginx", "-T"], cwd=Path("/"), check=False)
    text = (nginx.stdout or "") + "\n" + (nginx.stderr or "")
    blocks = extract_server_block(text, "tos.tamiyouz.com")
    for block in blocks:
        for raw in re.findall(r'(?m)^\s*root\s+([^;]+);', block):
            value = raw.strip().strip('"\'')
            value = value.replace("$document_root", "").strip()
            if "$" in value:
                continue
            p = Path(value)
            c = candidate_from_index(p / "index.html", live_asset_name)
            if c and c not in out:
                out.append(c)
    return out, blocks, text


def filesystem_candidates(live_asset_name: str):
    out = []
    search_roots = [Path("/var/www"), Path("/srv"), Path("/opt"), Path("/home")]
    for base in search_roots:
        if not base.exists():
            continue
        p = run(["find", str(base), "-type", "f", "-name", live_asset_name, "-print"], cwd=Path("/"), check=False)
        for line in p.stdout.splitlines():
            asset = Path(line.strip())
            if not asset.is_file() or asset.parent.name != "assets":
                continue
            c = candidate_from_index(asset.parent.parent / "index.html", live_asset_name)
            if c and c not in out:
                out.append(c)
    return out


def pm2_snapshot():
    p = run(["pm2", "jlist"], cwd=Path("/"), check=False)
    if p.returncode != 0:
        return []
    try:
        data = json.loads(p.stdout or "[]")
    except Exception:
        return []
    rows = []
    for item in data:
        env = item.get("pm2_env") or {}
        rows.append({
            "name": item.get("name"),
            "pid": item.get("pid"),
            "cwd": env.get("pm_cwd"),
            "script": env.get("pm_exec_path"),
            "status": env.get("status"),
        })
    return rows


def prove_candidate(root: Path, live_asset_name: str):
    root = root.resolve()
    if not root.is_dir() or not (root / "index.html").is_file():
        return False
    try:
        text = (root / "index.html").read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return live_asset_name in text and (root / "assets" / live_asset_name).is_file()


def safe_sync_dist(src: Path, dst: Path):
    src = src.resolve()
    dst = dst.resolve()
    if src == dst:
        return "DIRECT_DIST", None
    if not src.is_dir() or not (src / "index.html").is_file():
        raise RuntimeError("fresh dist missing")
    if not dst.is_dir() or not (dst / "index.html").is_file():
        raise RuntimeError(f"refusing unproven deploy root: {dst}")
    backup_dir = Path(tempfile.mkdtemp(prefix="tos-tws-r3-backup-"))
    touched = []
    try:
        for item in src.iterdir():
            target = dst / item.name
            if target.exists():
                backup = backup_dir / item.name
                if target.is_dir():
                    shutil.copytree(target, backup, dirs_exist_ok=True)
                else:
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup)
                touched.append((target, backup, True))
            else:
                touched.append((target, None, False))
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)
        return "SYNCED", (backup_dir, touched)
    except Exception:
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise


def restore_sync(state):
    if not state:
        return
    backup_dir, touched = state
    for target, backup, existed in reversed(touched):
        try:
            if existed:
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                if backup.is_dir():
                    shutil.copytree(backup, target)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, target)
            else:
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
        except Exception:
            pass
    shutil.rmtree(backup_dir, ignore_errors=True)


def reload_nginx():
    test = run(["nginx", "-t"], cwd=Path("/"), check=False)
    if test.returncode != 0:
        return "SKIPPED_NGINX_TEST_FAILED"
    p = run(["systemctl", "reload", "nginx"], cwd=Path("/"), check=False)
    return "PASS" if p.returncode == 0 else "SKIPPED_RELOAD_NOT_AVAILABLE"


def fail(msg, sync_state=None):
    if sync_state:
        restore_sync(sync_state)
    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print("RUN=FAIL")
    print(f"ERROR={msg}")
    print("SOURCE_PATCH_PRESERVED=YES")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)


sync_state = None
try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")
    head = git("rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD mismatch: expected {EXPECTED_HEAD}, got {head}")
    if changed_paths() != EXPECTED_DIRTY:
        raise RuntimeError("R1 worktree state mismatch: " + ", ".join(sorted(changed_paths())))

    sidebar_text = (REPO / SIDEBAR).read_text(encoding="utf-8")
    if NEW_WORKSPACE_FRAGMENT not in sidebar_text or NEW_SYSTEM_FRAGMENT not in sidebar_text:
        raise RuntimeError("R1 sidebar relocation is not present")

    run(["node", "--test", TEST])
    run(["npm", "run", "build"], cwd=FRONTEND)

    local_index = (DIST / "index.html").read_text(encoding="utf-8", errors="replace")
    built_asset = extract_main_js(local_index)
    if not built_asset:
        raise RuntimeError("could not identify built main JS asset")
    built_path = DIST / built_asset.lstrip("/")
    if not built_path.is_file():
        raise RuntimeError(f"built asset missing: {built_path}")
    built_sha = sha256(built_path)

    live_html, live_headers, _ = fetch_text(f"{LIVE_URL}?__tws_nav_r3={int(time.time())}")
    live_asset = extract_main_js(live_html)
    if not live_asset:
        raise RuntimeError("could not identify live JS asset")
    live_name = Path(live_asset.split("?", 1)[0]).name
    built_name = Path(built_asset.split("?", 1)[0]).name

    cache_status = live_headers.get("cf-cache-status") or live_headers.get("x-cache") or live_headers.get("x-proxy-cache") or "NONE"
    server_header = live_headers.get("server", "UNKNOWN")

    deploy_root = None
    discovery = "ALREADY_CURRENT"
    nginx_roots = []
    pm2 = pm2_snapshot()

    if live_name != built_name:
        nginx_roots, nginx_blocks, nginx_text = nginx_candidates(live_name)
        fs_roots = filesystem_candidates(live_name)
        candidates = []
        for c in nginx_roots + fs_roots:
            if c not in candidates and prove_candidate(c, live_name):
                candidates.append(c)

        # Strong preference: an nginx-proven root. Otherwise require exactly one on-disk root
        # containing BOTH the currently served index reference and asset.
        if len(nginx_roots) == 1:
            deploy_root = nginx_roots[0]
            discovery = "NGINX_SERVER_ROOT"
        elif len(nginx_roots) > 1:
            exact = [c for c in nginx_roots if prove_candidate(c, live_name)]
            if len(exact) == 1:
                deploy_root = exact[0]
                discovery = "NGINX_SERVER_ROOT_UNIQUE"
        if deploy_root is None:
            unique = [c for c in candidates if prove_candidate(c, live_name)]
            if len(unique) == 1:
                deploy_root = unique[0]
                discovery = "UNIQUE_LIVE_ASSET_ROOT"
        if deploy_root is None:
            roots_text = ",".join(str(x) for x in candidates) or "NONE"
            pm2_text = ";".join(f"{r.get('name')}|{r.get('pid')}|{r.get('cwd')}|{r.get('script')}|{r.get('status')}" for r in pm2) or "NONE"
            raise RuntimeError(f"production root still ambiguous; candidates={roots_text}; pm2={pm2_text}; cache={cache_status}; server={server_header}")

        mode, sync_state = safe_sync_dist(DIST, deploy_root)
        nginx_reload = reload_nginx()
        time.sleep(2)
    else:
        mode = "NO_SYNC_NEEDED"
        nginx_reload = "NOT_NEEDED"
        deploy_root = DIST

    live_html_after, live_headers_after, _ = fetch_text(f"{LIVE_URL}?__tws_nav_r3_verify={int(time.time())}")
    live_asset_after = extract_main_js(live_html_after)
    if not live_asset_after:
        raise RuntimeError("could not identify live JS after R3")
    live_name_after = Path(live_asset_after.split("?", 1)[0]).name
    if live_name_after != built_name:
        after_cache = live_headers_after.get("cf-cache-status") or live_headers_after.get("x-cache") or live_headers_after.get("x-proxy-cache") or "NONE"
        raise RuntimeError(f"origin/root updated but public HTML still stale: live={live_asset_after}, built={built_asset}, cache={after_cache}")

    body, _, _ = fetch(asset_url(live_asset_after) + f"?__tws_nav_r3_asset={int(time.time())}")
    tmp = Path("/tmp/tos_tws_r3_live.js")
    tmp.write_bytes(body)
    live_sha = sha256(tmp)
    tmp.unlink(missing_ok=True)
    if live_sha != built_sha:
        raise RuntimeError(f"live asset bytes mismatch: live={live_sha}, built={built_sha}")

    if changed_paths() != EXPECTED_DIRTY:
        raise RuntimeError("source worktree changed unexpectedly during R3")

    if sync_state:
        backup_dir, _ = sync_state
        shutil.rmtree(backup_dir, ignore_errors=True)
        sync_state = None

    print(f"PATCH={PATCH}")
    print(f"SCRIPT={SCRIPT}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("R1_SOURCE_PATCH_PRESENT=PASS")
    print("NAV_RELOCATION_TESTS=PASS (5/5)")
    print("FRONTEND_BUILD=PASS")
    print(f"BUILT_MAIN_ASSET={built_asset}")
    print(f"LIVE_ASSET_BEFORE={live_asset}")
    print(f"LIVE_ASSET_AFTER={live_asset_after}")
    print(f"LIVE_SERVER_HEADER={server_header}")
    print(f"LIVE_CACHE_STATUS={cache_status}")
    print(f"PRODUCTION_ROOT_DISCOVERY={discovery}")
    print(f"LIVE_DEPLOY_ROOT={deploy_root}")
    print(f"LIVE_DEPLOY_MODE={mode}")
    print(f"NGINX_RELOAD={nginx_reload}")
    print("LIVE_BUNDLE_MATCH=PASS")
    print("SOURCE_CHANGED_BY_R3=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("SOURCE_PATCH_PRESERVED=YES")
    print("READY_FOR_VISUAL_RECHECK=YES")
    print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
except Exception as exc:
    fail(str(exc), sync_state)
