#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PATCH_NAME = "TOS-AUDIT-LOG-V2-PHASE-3-CORE-OPERATIONS-GIT-GENERATED"
EXPECTED_HEAD = "5c157f20bbc71696a18bced97319cf8eb216f24f"
RAW_BASE = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-AUDIT-LOG-V2-PHASE-3-CORE-OPERATIONS-GIT-GENERATED/payload"

PAYLOADS = {
    "backend/src/middleware/auditV2CoreOperations.js": (
        f"{RAW_BASE}/auditV2CoreOperations.js",
        "7e7fe3394808cbb7db43f6e68bdf8ca5dcc7d549cb5b4259465cfba87b193545",
    ),
    "backend/src/middleware/auditV2CoreOperations.test.js": (
        f"{RAW_BASE}/auditV2CoreOperations.test.js",
        "6a614ab812cac34d735636db3a7f27ac8dc88d8c9286709c9b503dfefa060f18",
    ),
}

MODIFIED_BLOBS = {
    "backend/src/app.js": "51384466ec0d06974cafcedfaddfed448c9dd27f",
}

FOUNDATION_BLOBS = {
    "backend/package.json": "0257b5f042e72ac74f70408623c59f37f4f2172b",
    "backend/prisma/schema.prisma": "8e54719b3496d04fd1fa2a9c085fa6f5e6f59572",
    "backend/src/routes/auditLog.routes.js": "cfde2be53f2654ca98bd792df81253984c56d835",
    "backend/src/middleware/requestContext.js": "0a967751b18240191c2cabdae1703592380b389c",
    "backend/src/services/auditV2.service.js": "70bcbbd1772891fd5626d5d3e341a594c501851a",
    "backend/src/utils/auditRedaction.js": "b94eb6740cdc5e017ed8b541d81a44f7c95be31a",
    "backend/src/services/auditV2.phase2.security.test.js": "4a3b1aab229e0b06b671ce0b763f87c736cc9ea4",
}

NEW_FILES = list(PAYLOADS)
PATCH_PATHS = [*MODIFIED_BLOBS, *NEW_FILES]
EXPECTED_PATCH_PATHS = set(PATCH_PATHS)


def run(cmd, cwd, check=True):
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(cmd)}")
    return result


def git(repo, *args):
    result = subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def fetch_payload(url, expected_sha256):
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    actual = hashlib.sha256(data).hexdigest()
    require(actual == expected_sha256, f"payload checksum mismatch for {url}: {actual}")
    return data.decode("utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_app(text):
    text = replace_once(
        text,
        'import { requestContextMiddleware } from "./middleware/requestContext.js";',
        'import { requestContextMiddleware } from "./middleware/requestContext.js";\n'
        'import { coreOperationsAuditMiddleware } from "./middleware/auditV2CoreOperations.js";',
        "app import",
    )
    return replace_once(
        text,
        '  app.use(requestContextMiddleware);\n  app.use(csrfMiddleware);',
        '  app.use(requestContextMiddleware);\n'
        '  app.use(coreOperationsAuditMiddleware);\n'
        '  app.use(csrfMiddleware);',
        "app middleware mount",
    )


def validate_temp_patch_paths(tmp):
    changed = {
        line.strip()
        for line in git(tmp, "diff", "--name-only", "HEAD", "--", *PATCH_PATHS).splitlines()
        if line.strip()
    }
    require(changed == EXPECTED_PATCH_PATHS, f"patch paths mismatch: {sorted(changed)}")
    statuses = git(tmp, "diff", "--name-status", "HEAD", "--", *PATCH_PATHS).splitlines()
    added = {
        line.split("\t", 1)[1]
        for line in statuses
        if line.startswith("A\t") and "\t" in line
    }
    require(added == set(NEW_FILES), f"new-file paths mismatch: {sorted(added)}")


def validate_actual_paths(repo):
    tracked = {
        line.strip()
        for line in git(repo, "diff", "--name-only", "HEAD", "--").splitlines()
        if line.strip()
    }
    actual = set(tracked)
    for rel in NEW_FILES:
        if (repo / rel).is_file():
            actual.add(rel)
    require(actual == EXPECTED_PATCH_PATHS, f"working-tree paths mismatch: {sorted(actual)}")


def main():
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))
    print(f"PATCH={PATCH_NAME}")
    print(f"REPO={repo}")

    require(git(repo, "rev-parse", "HEAD") == EXPECTED_HEAD, f"HEAD must equal {EXPECTED_HEAD}")
    require(subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=repo).returncode == 0, "tracked working tree must be clean before Phase 3")
    require(subprocess.run(["git", "diff", "--cached", "--quiet", "HEAD", "--"], cwd=repo).returncode == 0, "index must be clean before Phase 3")

    for rel, expected in {**MODIFIED_BLOBS, **FOUNDATION_BLOBS}.items():
        require((repo / rel).is_file(), f"missing guarded source: {rel}")
        actual = git(repo, "hash-object", rel)
        require(actual == expected, f"blob mismatch for {rel}: expected {expected}, got {actual}")

    for rel in NEW_FILES:
        require(not (repo / rel).exists(), f"Phase 3 path already exists: {rel}")

    payload_text = {rel: fetch_payload(url, sha) for rel, (url, sha) in PAYLOADS.items()}

    with tempfile.TemporaryDirectory(prefix="tos-audit-v2-phase3-") as tmp_name:
        tmp = Path(tmp_name)
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "audit-v2-phase3@tamiyouz.local"], tmp)
        run(["git", "config", "user.name", "TOS Audit V2 Phase 3"], tmp)

        baseline = ["backend/src/app.js", "backend/package.json"]
        for rel in baseline:
            target = tmp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / rel, target)

        write_text(tmp / "backend/src/services/auditV2.service.js", "export async function writeAuditEvent() { return null; }\n")
        baseline.append("backend/src/services/auditV2.service.js")
        run(["git", "add", "--", *baseline], tmp)
        run(["git", "commit", "-q", "-m", "baseline"], tmp)

        app_path = tmp / "backend/src/app.js"
        write_text(app_path, patch_app(app_path.read_text(encoding="utf-8")))
        for rel, content in payload_text.items():
            write_text(tmp / rel, content)

        run(["node", "--check", "backend/src/app.js"], tmp)
        for rel in NEW_FILES:
            run(["node", "--check", rel], tmp)
        run(["node", "--test", "src/middleware/auditV2CoreOperations.test.js"], tmp / "backend")

        middleware_text = (tmp / NEW_FILES[0]).read_text(encoding="utf-8")
        require("writeAuditEvent" in middleware_text, "central writer import missing")
        require("auditEventV2.create" not in middleware_text, "direct AuditEventV2 persistence is forbidden")
        require("DESIGN_QUEUE.REQUEST_CREATED" in middleware_text, "design queue instrumentation missing")
        require("TRELLO.SYNC_TRIGGERED" in middleware_text, "Trello integration instrumentation missing")
        require("PHASE_4_PATH_PATTERN" in middleware_text, "Phase 4 scope exclusion guard missing")

        run(["git", "add", "--intent-to-add", "--", *NEW_FILES], tmp)
        validate_temp_patch_paths(tmp)

        patch_text = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--no-renames", "HEAD", "--", *PATCH_PATHS],
            cwd=tmp, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout
        require(patch_text.strip(), "generated patch is empty")
        for rel in PATCH_PATHS:
            require(f"diff --git a/{rel} b/{rel}" in patch_text, f"patch missing {rel}")
        for rel in FOUNDATION_BLOBS:
            require(f"diff --git a/{rel} b/{rel}" not in patch_text, f"protected path leaked into patch: {rel}")

        patch_file = tmp / "tos-audit-log-v2-phase3-core-operations.patch"
        patch_file.write_text(patch_text, encoding="utf-8", newline="\n")
        patch_sha = hashlib.sha256(patch_file.read_bytes()).hexdigest()

        run(["git", "apply", "--check", str(patch_file)], repo)
        print("GIT_APPLY_CHECK=PASS")
        run(["git", "apply", str(patch_file)], repo)
        print("PHASE_3_PATCH_APPLIED=YES")

    run(["git", "diff", "--check"], repo)

    backend = repo / "backend"
    run(["npm", "run", "prisma:validate"], backend)
    print("PRISMA_VALIDATE=PASS")
    run(["npm", "run", "prisma:generate"], backend)
    print("PRISMA_GENERATE=PASS")

    run(["node", "--check", "src/app.js"], backend)
    run(["node", "--check", "src/middleware/auditV2CoreOperations.js"], backend)
    run(["node", "--check", "src/middleware/auditV2CoreOperations.test.js"], backend)

    run([
        "node", "--test",
        "src/utils/auditRedaction.test.js",
        "src/middleware/requestContext.test.js",
        "src/services/auditV2.core.test.js",
        "src/services/auditV2.phase2.security.test.js",
        "src/middleware/auditV2CoreOperations.test.js",
    ], backend)
    print("PHASE_1_TESTS=PASS")
    print("PHASE_2_TESTS=PASS")
    print("PHASE_3_TESTS=PASS")

    validate_actual_paths(repo)

    for rel in FOUNDATION_BLOBS:
        require(not git(repo, "diff", "--", rel), f"protected foundation file changed: {rel}")

    middleware_actual = (repo / NEW_FILES[0]).read_text(encoding="utf-8")
    require("PROJECT.CREATED" in middleware_actual and "PROJECT.STATUS_CHANGED" in middleware_actual, "project events incomplete")
    require("TASK.CREATED" in middleware_actual and "TASK.STATUS_CHANGED" in middleware_actual, "task events incomplete")
    require("DESIGN_QUEUE.REQUEST_CREATED" in middleware_actual and "DESIGN_QUEUE.ASSIGNMENT_CHANGED" in middleware_actual, "design queue events incomplete")
    require("TRELLO.SYNC_TRIGGERED" in middleware_actual and "INTEGRATION.SYNC_TRIGGERED" in middleware_actual, "integration events incomplete")
    require("auditEventV2.create" not in middleware_actual, "direct AuditEventV2 write detected")

    print("PATCH_FILES_VALIDATED=PASS")
    print(f"PATCH_FILE_COUNT={len(PATCH_PATHS)}")
    print(f"PATCH_NEW_FILE_COUNT={len(NEW_FILES)}")
    print("PROJECT_CORE_EVENTS=PASS")
    print("TASK_CORE_EVENTS=PASS")
    print("DESIGN_QUEUE_EVENTS=PASS")
    print("TRELLO_INTEGRATION_EVENTS=PASS")
    print("CENTRAL_AUDIT_WRITER_ONLY=PASS")
    print("PHASE_4_SCOPE_EXCLUDED=YES")
    print("LEGACY_AUDIT_ROUTE_CHANGED=NO")
    print("PRISMA_SCHEMA_CHANGED=NO")
    print("PHASE_1_2_FOUNDATION_PRESERVED=YES")
    print("MIGRATION_REQUIRED=NO")
    print(f"PATCH_SHA256={patch_sha}")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_3_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
