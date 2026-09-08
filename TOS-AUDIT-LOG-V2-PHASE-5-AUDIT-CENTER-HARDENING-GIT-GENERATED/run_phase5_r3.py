#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import urllib.request
from pathlib import Path

RUNNER_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-AUDIT-LOG-V2-PHASE-5-AUDIT-CENTER-HARDENING-GIT-GENERATED/run_phase5.py"
EXPECTED_HEAD = "8e410d0658a5893309e3a30cd6bab2f99eafb0c6"
OLD_CENTER_BLOB = "2ffcdcef91fefb0bdb700568fbc07a7f92f2a4ca"
NEW_CENTER_BLOB = "9bff6d40c8c5c8a684eb75453575d21a59ac969b"

TRACKED_PHASE5 = {
    "backend/prisma/schema.prisma",
    "backend/src/routes/auditLog.routes.js",
    "frontend/src/lib/api.js",
    "frontend/src/pages/AuditLogPage.jsx",
}
UNTRACKED_PHASE5 = {
    "backend/src/services/auditV2.center.js",
    "backend/src/services/auditV2.retention.js",
    "backend/src/services/auditV2.phase5.hardening.test.js",
    "backend/prisma/migrations/20260908073000_audit_log_v2_hardening/migration.sql",
}

OLD_API = '''    v2: (filters = {}) => request(`/api/audit-log/v2${queryString(filters)}`),
    v2Filters: () => request("/api/audit-log/v2/filters"),
    eventV2: (id) => request(`/api/audit-log/v2/${encodeURIComponent(id)}`),
    retention: () => request("/api/audit-log/v2/retention"),
    runRetention: (payload = {}) => request("/api/audit-log/v2/retention/run", { method: "POST", body: JSON.stringify(payload || {}) }),
    exportV2: (filters = {}) => downloadRequest(`/api/audit-log/v2/export${queryString(filters)}`),'''
NEW_API = '''    v2: (filters = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
      });
      const query = params.toString();
      return request(`/api/audit-log/v2${query ? `?${query}` : ""}`);
    },
    v2Filters: () => request("/api/audit-log/v2/filters"),
    eventV2: (id) => request(`/api/audit-log/v2/${encodeURIComponent(id)}`),
    retention: () => request("/api/audit-log/v2/retention"),
    runRetention: (payload = {}) => request("/api/audit-log/v2/retention/run", { method: "POST", body: JSON.stringify(payload || {}) }),
    exportV2: (filters = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
      });
      const query = params.toString();
      return downloadRequest(`/api/audit-log/v2/export${query ? `?${query}` : ""}`);
    },'''

OLD_VALIDATE = '''    names = set(filter(None, git(repo, "diff", "--name-only", "HEAD").splitlines()))
    require(names == EXPECTED_PATCH_PATHS, f"unexpected Phase 5 working-tree paths: {sorted(names)}")'''
NEW_VALIDATE = '''    names = set(filter(None, git(repo, "diff", "--name-only", "HEAD").splitlines()))
    names.update(filter(None, git(repo, "ls-files", "--others", "--exclude-standard").splitlines()))
    require(names == EXPECTED_PATCH_PATHS, f"unexpected Phase 5 working-tree paths: {sorted(names)}")'''


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def recover_r2_applied_tree(repo: Path) -> None:
    head = git(repo, "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise SystemExit(f"PHASE_5_R3=FAIL: HEAD must equal {EXPECTED_HEAD}, got {head}")

    tracked = set(filter(None, git(repo, "diff", "--name-only", "HEAD").splitlines()))
    untracked = set(filter(None, git(repo, "ls-files", "--others", "--exclude-standard").splitlines()))

    if not tracked and not untracked:
        return

    if tracked != TRACKED_PHASE5 or untracked != UNTRACKED_PHASE5:
        raise SystemExit(
            "PHASE_5_R3=FAIL: refusing recovery because dirty tree is not exactly the R2-applied Phase 5 set; "
            f"tracked={sorted(tracked)} untracked={sorted(untracked)}"
        )

    subprocess.run(["git", "restore", "--source=HEAD", "--", *sorted(TRACKED_PHASE5)], cwd=repo, check=True)
    for rel in sorted(UNTRACKED_PHASE5):
        path = repo / rel
        if path.exists():
            path.unlink()

    if git(repo, "status", "--porcelain"):
        raise SystemExit("PHASE_5_R3=FAIL: recovery did not return working tree to clean baseline")
    print("R2_APPLIED_TREE_RECOVERED=YES")


repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))
recover_r2_applied_tree(repo)

with urllib.request.urlopen(RUNNER_URL, timeout=30) as response:
    source = response.read().decode("utf-8")

for old, label in [
    (OLD_CENTER_BLOB, "center payload guard"),
    (OLD_API, "audit API transform"),
    (OLD_VALIDATE, "post-apply untracked validation"),
]:
    if source.count(old) != 1:
        raise SystemExit(f"PHASE_5_R3=FAIL: {label} mismatch")

source = source.replace(OLD_CENTER_BLOB, NEW_CENTER_BLOB, 1)
source = source.replace(OLD_API, NEW_API, 1)
source = source.replace(OLD_VALIDATE, NEW_VALIDATE, 1)

exec(compile(source, "run_phase5_r3_inner.py", "exec"), {"__name__": "__main__"})
