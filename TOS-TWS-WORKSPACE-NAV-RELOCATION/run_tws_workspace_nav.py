#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import urllib.request

PATCH = "TOS-TWS-WORKSPACE-NAV-RELOCATION"
REPO = Path("/var/www/TOS")
EXPECTED_HEAD = "186ae5a52ae77744a946abc13522acc2ef5e80a8"
SIDEBAR = "frontend/src/components/layout/Sidebar.jsx"
TEST = "frontend/src/components/layout/twsWorkspaceNavRelocation.test.js"
EXPECTED_SIDEBAR_BLOB = "36883fe915d1d981d481108839fe7583a3903366"
TEST_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-WORKSPACE-NAV-RELOCATION/payload/twsWorkspaceNavRelocation.test.js"
EXPECTED_TEST_BLOB = "660c5c92d623f7729723f9855c007374eb09b4a2"
SCOPE = {SIDEBAR, TEST}

OLD_WORKSPACE = '  { id: "workspaceGroup", labelAr: "مساحة العمل", labelEn: "Workspace", icon: ClipboardList, children: ["projects", "tasks", "myWorkspace", "designQueue", "tgws"] },'
NEW_WORKSPACE = '  { id: "workspaceGroup", labelAr: "مساحة العمل", labelEn: "Workspace", icon: ClipboardList, children: ["projects", "tasks", "myWorkspace", "designQueue", "tws", "tgws"] },'
OLD_SYSTEM = '  { id: "systemGroup", labelAr: "النظام", labelEn: "System", icon: ShieldCheck, children: ["workHub", "slaInbox", "slaCenter", "slaAdvanced", "tws", "auditLog"] },'
NEW_SYSTEM = '  { id: "systemGroup", labelAr: "النظام", labelEn: "System", icon: ShieldCheck, children: ["workHub", "slaInbox", "slaCenter", "slaAdvanced", "auditLog"] },'


def run(args, cwd=REPO, check=True, capture=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=capture)
    if check and result.returncode != 0:
        detail = (result.stdout or "") + (result.stderr or "")
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args)}\n{detail.strip()}")
    return result


def git(*args, check=True):
    return run(["git", *args], check=check).stdout.strip()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def file_fingerprint(path: str) -> str:
    target = REPO / path
    if not target.exists():
        return "MISSING"
    if target.is_file():
        return "FILE:" + hashlib.sha256(target.read_bytes()).hexdigest()
    hashes = []
    for child in sorted(p for p in target.rglob("*") if p.is_file()):
        hashes.append(f"{child.relative_to(target)}:{hashlib.sha256(child.read_bytes()).hexdigest()}")
    return "DIR:" + hashlib.sha256("\n".join(hashes).encode()).hexdigest()


def status_paths():
    raw = git("status", "--porcelain=v1", "--untracked-files=all")
    paths = set()
    if not raw:
        return paths
    for line in raw.splitlines():
        if len(line) < 4:
            continue
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        paths.add(value)
    return paths


def rollback():
    run(["git", "checkout", "HEAD", "--", SIDEBAR], check=False)
    target = REPO / TEST
    if target.exists():
        target.unlink()


applied = False
pre_fingerprints = None


def fail(message):
    global applied
    if applied:
        rollback()
    if pre_fingerprints is not None:
        changed = [p for p, fp in pre_fingerprints.items() if file_fingerprint(p) != fp]
        print(f"PREEXISTING_DIRTY_STATE_PRESERVED={'NO' if changed else 'YES'}")
        if changed:
            print("PREEXISTING_DIRTY_CHANGED=" + ",".join(sorted(changed)))
    print(f"PATCH={PATCH}")
    print("RUN=FAIL")
    print(f"ERROR={message}")
    print("READY_FOR_GIT_PUSH=NO")
    sys.exit(1)


try:
    if not REPO.is_dir():
        raise RuntimeError(f"repo not found: {REPO}")

    head = git("rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD mismatch: expected {EXPECTED_HEAD}, got {head}")

    sidebar_blob = git("hash-object", SIDEBAR)
    if sidebar_blob != EXPECTED_SIDEBAR_BLOB:
        raise RuntimeError(f"Sidebar baseline blob mismatch: {sidebar_blob}")

    tracked_test = run(["git", "cat-file", "-e", f"HEAD:{TEST}"], check=False)
    if tracked_test.returncode == 0:
        raise RuntimeError(f"unexpected baseline test file already tracked: {TEST}")

    pre_paths = status_paths()
    overlap = sorted(pre_paths & SCOPE)
    if overlap:
        raise RuntimeError("pre-existing dirty state overlaps patch scope: " + ", ".join(overlap))
    pre_fingerprints = {path: file_fingerprint(path) for path in pre_paths}

    payload = urllib.request.urlopen(TEST_URL, timeout=30).read()
    if git_blob_sha(payload) != EXPECTED_TEST_BLOB:
        raise RuntimeError("test payload integrity mismatch")

    sidebar_path = REPO / SIDEBAR
    source = sidebar_path.read_text(encoding="utf-8")
    if source.count(OLD_WORKSPACE) != 1 or source.count(OLD_SYSTEM) != 1:
        raise RuntimeError("expected sidebar group definitions were not found exactly once")

    applied = True
    source = source.replace(OLD_WORKSPACE, NEW_WORKSPACE, 1).replace(OLD_SYSTEM, NEW_SYSTEM, 1)
    sidebar_path.write_text(source, encoding="utf-8")

    test_path = REPO / TEST
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_bytes(payload)

    run(["git", "diff", "--check"])
    run(["node", "--test", TEST])
    run(["npm", "run", "build"], cwd=REPO / "frontend")

    for path, fingerprint in pre_fingerprints.items():
        if file_fingerprint(path) != fingerprint:
            raise RuntimeError(f"pre-existing dirty path changed: {path}")

    after_paths = status_paths()
    added_by_patch = after_paths - pre_paths
    missing_preexisting = pre_paths - after_paths
    if added_by_patch != SCOPE:
        raise RuntimeError("unexpected changed paths: " + ", ".join(sorted(added_by_patch)))
    if missing_preexisting:
        raise RuntimeError("pre-existing dirty paths disappeared: " + ", ".join(sorted(missing_preexisting)))

    final_source = sidebar_path.read_text(encoding="utf-8")
    if NEW_WORKSPACE not in final_source or NEW_SYSTEM not in final_source:
        raise RuntimeError("final sidebar ownership verification failed")

    print(f"PATCH={PATCH}")
    print(f"REPO={REPO}")
    print(f"HEAD={head}")
    print("PRECHECK_WORKTREE=" + ("CLEAN" if not pre_paths else "DIRTY_UNRELATED_ALLOWED"))
    print(f"PREEXISTING_DIRTY_PATHS={len(pre_paths)}")
    print("FILES_PATCHED=2")
    print("BASELINE_BLOB_GUARD=PASS")
    print("PAYLOAD_INTEGRITY=PASS")
    print("TWS_WORKSPACE_GROUP=PASS")
    print("TWS_REMOVED_FROM_SYSTEM_GROUP=PASS")
    print("TWS_ROUTE_PRESERVED=PASS")
    print("ACTIVE_GROUP_RESOLUTION_PRESERVED=PASS")
    print("NAV_RELOCATION_TESTS=PASS (5/5)")
    print("FRONTEND_BUILD=PASS")
    print("PERMISSIONS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("PREEXISTING_DIRTY_STATE_PRESERVED=YES")
    print("CHANGED_PATHS_EXACT=YES")
    print("PATCH_APPLIED=YES")
    print("READY_FOR_GIT_PUSH=YES")
except Exception as exc:
    fail(str(exc))
