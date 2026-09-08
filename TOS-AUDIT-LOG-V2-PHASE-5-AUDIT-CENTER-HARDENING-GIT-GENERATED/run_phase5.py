#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PATCH_NAME = "TOS-AUDIT-LOG-V2-PHASE-5-AUDIT-CENTER-HARDENING-GIT-GENERATED"
EXPECTED_HEAD = "8e410d0658a5893309e3a30cd6bab2f99eafb0c6"
RAW_BASE = f"https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/{PATCH_NAME}/payload"

PAYLOADS = {
    "backend/src/services/auditV2.center.js": (f"{RAW_BASE}/auditV2.center.js", "2ffcdcef91fefb0bdb700568fbc07a7f92f2a4ca"),
    "backend/src/services/auditV2.retention.js": (f"{RAW_BASE}/auditV2.retention.js", "4a3b75c97197788c33f57c40385da7f3a6d29cc4"),
    "backend/src/services/auditV2.phase5.hardening.test.js": (f"{RAW_BASE}/auditV2.phase5.hardening.test.js", "d03f69849a7f480c800aec8585004a651521055e"),
    "backend/src/routes/auditLog.routes.js": (f"{RAW_BASE}/auditLog.routes.js", "0e388faa1495462ca92e5f8545cacb91fe9c930e"),
    "backend/prisma/migrations/20260908073000_audit_log_v2_hardening/migration.sql": (f"{RAW_BASE}/migration.sql", "28866af58f7a8cd1eb844f5e8038960067f0552f"),
    "frontend/src/pages/AuditLogPage.jsx": (f"{RAW_BASE}/AuditLogPage.jsx", "b368609eff741cd5afdaba416d7ba75a98d9c163"),
}

MODIFIED_BLOBS = {
    "backend/prisma/schema.prisma": "8e54719b3496d04fd1fa2a9c085fa6f5e6f59572",
    "backend/src/routes/auditLog.routes.js": "cfde2be53f2654ca98bd792df81253984c56d835",
    "frontend/src/lib/api.js": "c9d603aa562ebf913f0f6f3fcc5895fcb5a0ba85",
    "frontend/src/pages/AuditLogPage.jsx": "14cdb8bc2ce2e79eab9747b9f6796febee4ad669",
}

PROTECTED_BLOBS = {
    "backend/package.json": "0257b5f042e72ac74f70408623c59f37f4f2172b",
    "frontend/package.json": "cfc96956b2f98f04fe161c76e60fc73b337a4f23",
    "backend/src/app.js": "909aa0c42e866aa14b08d8c7453fe12d41d85774",
    "backend/src/middleware/requestContext.js": "0a967751b18240191c2cabdae1703592380b389c",
    "backend/src/services/auditV2.service.js": "70bcbbd1772891fd5626d5d3e341a594c501851a",
    "backend/src/services/auditV2.core.js": "3650c2baa3a881abd2abc53b58ac2c7e3942a44f",
    "backend/src/utils/auditRedaction.js": "b94eb6740cdc5e017ed8b541d81a44f7c95be31a",
    "backend/src/services/auditV2.phase2.security.test.js": "4a3b1aab229e0b06b671ce0b763f87c736cc9ea4",
    "backend/src/middleware/auditV2CoreOperations.js": "39e1436d3efb02b74458ef991a4e7ae3d88fe6c6",
    "backend/src/middleware/auditV2CoreOperations.test.js": "e5d05a19f09bfbaa2bf949a658eda9d2c9bc9e43",
    "backend/src/middleware/auditV2SensitiveOperations.js": "4620188e2aa8b1c3d919f02da372bc515e8358cf",
    "backend/src/middleware/auditV2SensitiveOperations.test.js": "db8f865b924d1ecf5e253509eb27da83cba58493",
    "backend/prisma/migrations/20260907194000_audit_log_v2_foundation/migration.sql": "4c80e7e3834c2cb0425fde503640b906d30d4344",
}

NEW_FILES = {
    "backend/src/services/auditV2.center.js",
    "backend/src/services/auditV2.retention.js",
    "backend/src/services/auditV2.phase5.hardening.test.js",
    "backend/prisma/migrations/20260908073000_audit_log_v2_hardening/migration.sql",
}
EXPECTED_PATCH_PATHS = {
    "backend/prisma/schema.prisma",
    "backend/src/routes/auditLog.routes.js",
    "backend/src/services/auditV2.center.js",
    "backend/src/services/auditV2.retention.js",
    "backend/src/services/auditV2.phase5.hardening.test.js",
    "backend/prisma/migrations/20260908073000_audit_log_v2_hardening/migration.sql",
    "frontend/src/lib/api.js",
    "frontend/src/pages/AuditLogPage.jsx",
}

SCHEMA_OLD = '''  @@index([occurredAt])
  @@index([actorId, occurredAt])
  @@index([action, occurredAt])
  @@index([category, occurredAt])
  @@index([entityType, entityId])
  @@index([requestId])
  @@index([legacySource, legacyId])'''

SCHEMA_NEW = '''  @@index([occurredAt])
  @@index([actorId, occurredAt])
  @@index([action, occurredAt])
  @@index([category, occurredAt])
  @@index([entityType, entityId])
  @@index([entityType, entityId, occurredAt])
  @@index([outcome, occurredAt])
  @@index([severity, occurredAt])
  @@index([source, occurredAt])
  @@index([requestId])
  @@index([legacySource, legacyId])'''

API_OLD = '''  auditLog: {
    list: (filters = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          params.set(key, String(value));
        }
      });
      const query = params.toString();
      return request(`/api/audit-log${query ? `?${query}` : ""}`);
    },
  },'''

API_NEW = '''  auditLog: {
    list: (filters = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          params.set(key, String(value));
        }
      });
      const query = params.toString();
      return request(`/api/audit-log${query ? `?${query}` : ""}`);
    },
    v2: (filters = {}) => request(`/api/audit-log/v2${queryString(filters)}`),
    v2Filters: () => request("/api/audit-log/v2/filters"),
    eventV2: (id) => request(`/api/audit-log/v2/${encodeURIComponent(id)}`),
    retention: () => request("/api/audit-log/v2/retention"),
    runRetention: (payload = {}) => request("/api/audit-log/v2/retention/run", { method: "POST", body: JSON.stringify(payload || {}) }),
    exportV2: (filters = {}) => downloadRequest(`/api/audit-log/v2/export${queryString(filters)}`),
  },'''


def run(cmd, cwd, *, check=True, capture=False):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if check and result.returncode != 0:
        detail = ((result.stderr or "") + "\n" + (result.stdout or "")).strip() if capture else ""
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(cmd)}{': ' + detail if detail else ''}")
    return result


def git(repo, *args):
    result = subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def fetch_payload(url, expected_blob):
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    actual = git_blob_sha(data)
    require(actual == expected_blob, f"payload blob mismatch for {url}: {actual}")
    return data


def write_bytes(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def replace_once(path: Path, old: str, new: str, label: str):
    text = path.read_text(encoding="utf-8")
    require(text.count(old) == 1, f"{label} baseline anchor mismatch")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def verify_baseline(repo: Path):
    require(git(repo, "rev-parse", "HEAD") == EXPECTED_HEAD, f"HEAD must equal {EXPECTED_HEAD}")
    require(not git(repo, "status", "--porcelain"), "working tree must be clean before Phase 5")
    for rel, expected in {**MODIFIED_BLOBS, **PROTECTED_BLOBS}.items():
        actual = git(repo, "rev-parse", f"HEAD:{rel}")
        require(actual == expected, f"baseline blob mismatch for {rel}: {actual}")


def prepare_temp(repo: Path, tmp: Path):
    temp_repo = tmp / "repo"
    run(["git", "clone", "--quiet", "--no-hardlinks", str(repo), str(temp_repo)], tmp)
    run(["git", "checkout", "--quiet", EXPECTED_HEAD], temp_repo)

    for rel, (url, blob) in PAYLOADS.items():
        write_bytes(temp_repo / rel, fetch_payload(url, blob))

    replace_once(temp_repo / "backend/prisma/schema.prisma", SCHEMA_OLD, SCHEMA_NEW, "Prisma AuditEventV2 indexes")
    replace_once(temp_repo / "frontend/src/lib/api.js", API_OLD, API_NEW, "frontend audit API")

    run(["git", "add", "--intent-to-add", "--", *sorted(NEW_FILES)], temp_repo)
    names = set(filter(None, git(temp_repo, "diff", "--name-only", "HEAD").splitlines()))
    require(names == EXPECTED_PATCH_PATHS, f"unexpected generated patch paths: {sorted(names)}")
    return temp_repo


def generate_patch(temp_repo: Path, tmp: Path):
    result = subprocess.run(
        ["git", "diff", "--binary", "HEAD", "--", *sorted(EXPECTED_PATCH_PATHS)],
        cwd=temp_repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", "replace"))
    require(result.stdout, "generated patch is empty")
    patch_path = tmp / "phase5.patch"
    patch_path.write_bytes(result.stdout)
    return patch_path, hashlib.sha256(result.stdout).hexdigest()


def validate_actual(repo: Path, patch_path: Path):
    run(["git", "apply", "--check", str(patch_path)], repo)
    print("GIT_APPLY_CHECK=PASS")
    run(["git", "apply", str(patch_path)], repo)
    print("PHASE_5_PATCH_APPLIED=YES")

    run(["git", "diff", "--check"], repo)
    names = set(filter(None, git(repo, "diff", "--name-only", "HEAD").splitlines()))
    require(names == EXPECTED_PATCH_PATHS, f"unexpected Phase 5 working-tree paths: {sorted(names)}")

    for rel, expected in PROTECTED_BLOBS.items():
        actual = git(repo, "hash-object", rel)
        require(actual == expected, f"protected Phase 1-4 file changed: {rel}")

    backend = repo / "backend"
    frontend = repo / "frontend"

    for rel in [
        "src/routes/auditLog.routes.js",
        "src/services/auditV2.center.js",
        "src/services/auditV2.retention.js",
        "src/services/auditV2.phase5.hardening.test.js",
    ]:
        run(["node", "--check", rel], backend)

    run(["npm", "run", "prisma:validate"], backend)
    print("PRISMA_VALIDATE=PASS")
    run(["npm", "run", "prisma:generate"], backend)
    print("PRISMA_GENERATE=PASS")

    tests = [
        "src/utils/auditRedaction.test.js",
        "src/middleware/requestContext.test.js",
        "src/services/auditV2.core.test.js",
        "src/services/auditV2.phase2.security.test.js",
        "src/middleware/auditV2CoreOperations.test.js",
        "src/middleware/auditV2SensitiveOperations.test.js",
        "src/services/auditV2.phase5.hardening.test.js",
    ]
    run(["node", "--test", *tests], backend)
    print("PHASE_1_TESTS=PASS")
    print("PHASE_2_TESTS=PASS")
    print("PHASE_3_TESTS=PASS")
    print("PHASE_4_TESTS=PASS")
    print("PHASE_5_TESTS=PASS")

    build_out = Path(tempfile.mkdtemp(prefix="tos-phase5-frontend-build-"))
    try:
        run(["npm", "run", "build", "--", "--outDir", str(build_out)], frontend)
    finally:
        shutil.rmtree(build_out, ignore_errors=True)
    print("FRONTEND_BUILD=PASS")

    route = (backend / "src/routes/auditLog.routes.js").read_text(encoding="utf-8")
    schema = (backend / "prisma/schema.prisma").read_text(encoding="utf-8")
    migration = (backend / "prisma/migrations/20260908073000_audit_log_v2_hardening/migration.sql").read_text(encoding="utf-8")
    page = (frontend / "src/pages/AuditLogPage.jsx").read_text(encoding="utf-8")
    api = (frontend / "src/lib/api.js").read_text(encoding="utf-8")

    require('router.get("/v2"' in route and 'router.get("/"' in route, "V2 or legacy Audit Center route missing")
    require("prisma.chatAuditLog.findMany" in route and "prisma.taskActivity.findMany" in route, "legacy merged audit behavior missing")
    require("/v2/export" in route and "/v2/retention/run" in route, "Audit Center export/retention endpoints missing")
    require("BEFORE UPDATE OR DELETE" in migration and "app.audit_v2_retention_purge" in migration, "append-only guard missing")
    for marker in [
        "@@index([entityType, entityId, occurredAt])",
        "@@index([outcome, occurredAt])",
        "@@index([severity, occurredAt])",
        "@@index([source, occurredAt])",
    ]:
        require(marker in schema, f"missing Prisma hardening index: {marker}")
    require("Audit Center V2" in page and "APPEND-ONLY" in page, "Audit Center V2 UI missing")
    require("exportV2" in api and "runRetention" in api and "v2Filters" in api, "frontend Audit V2 API missing")

    print("AUDIT_CENTER_V2=PASS")
    print("AUDIT_FILTERS_EXPORT=PASS")
    print("APPEND_ONLY_GUARD=PASS")
    print("RETENTION_POLICY=PASS")
    print("INDEX_HARDENING=PASS")
    print("LEGACY_AUDIT_PRESERVED=YES")
    print("SENSITIVE_REDACTION_PRESERVED=YES")
    print("PHASE_1_2_3_4_FOUNDATION_PRESERVED=YES")
    print("MIGRATION_REQUIRED=YES")
    print(f"PATCH_FILE_COUNT={len(names)}")


def main():
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))
    print(f"PATCH={PATCH_NAME}")
    print(f"REPO={repo}")
    verify_baseline(repo)

    with tempfile.TemporaryDirectory(prefix="tos-audit-v2-phase5-") as tmp_name:
        tmp = Path(tmp_name)
        temp_repo = prepare_temp(repo, tmp)
        patch_path, patch_sha = generate_patch(temp_repo, tmp)
        validate_actual(repo, patch_path)
        print(f"PATCH_SHA256={patch_sha}")

    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_5_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
