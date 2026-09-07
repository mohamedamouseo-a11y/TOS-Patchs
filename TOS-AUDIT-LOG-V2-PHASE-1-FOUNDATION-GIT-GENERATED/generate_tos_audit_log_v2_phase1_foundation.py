#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PATCH_NAME = "TOS-AUDIT-LOG-V2-PHASE-1-FOUNDATION-GIT-GENERATED"
EXPECTED_HEAD = "f6b6f60b57d702e62ed488eca7265bfcde0ca601"
EXPECTED_BLOBS = {
    "backend/prisma/schema.prisma": "3abcb43eeeba95c4142b44da91cdb3d1d884cfa9",
    "backend/src/app.js": "2f67a9ab3c89e9f0e8c1bd4ff3f7e7137abbcd15",
}
MIGRATION_DIR = "backend/prisma/migrations/20260907194000_audit_log_v2_foundation"
OUTPUT_NAME = "tos-audit-log-v2-phase1-foundation.patch"
NEW_FILES = {
    f"{MIGRATION_DIR}/migration.sql": "migration.sql",
    "backend/src/utils/auditRedaction.js": "auditRedaction.js",
    "backend/src/utils/auditRedaction.test.js": "auditRedaction.test.js",
    "backend/src/middleware/requestContext.js": "requestContext.js",
    "backend/src/middleware/requestContext.test.js": "requestContext.test.js",
    "backend/src/services/auditV2.core.js": "auditV2.core.js",
    "backend/src/services/auditV2.core.test.js": "auditV2.core.test.js",
    "backend/src/services/auditV2.service.js": "auditV2.service.js",
}
PATCH_PATHS = ["backend/prisma/schema.prisma", "backend/src/app.js", *NEW_FILES]


def run(cmd, cwd, check=True, capture=True):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if check and result.returncode != 0:
        if capture:
            sys.stderr.write(result.stdout or "")
            sys.stderr.write(result.stderr or "")
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(cmd)}")
    return result


def git(repo, *args):
    return run(["git", *args], repo).stdout.strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main():
    script_dir = Path(__file__).resolve().parent
    payload_dir = script_dir / "payload"
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))

    print(f"PATCH={PATCH_NAME}")
    print(f"REPO={repo}")

    require(git(repo, "rev-parse", "HEAD") == EXPECTED_HEAD, f"HEAD must equal {EXPECTED_HEAD}")
    for rel, expected in EXPECTED_BLOBS.items():
        require((repo / rel).is_file(), f"missing source: {rel}")
        actual = git(repo, "hash-object", rel)
        require(actual == expected, f"blob mismatch for {rel}: expected {expected}, got {actual}")
        require(not git(repo, "status", "--porcelain", "--", rel), f"dirty source: {rel}")

    for rel in NEW_FILES:
        require(not (repo / rel).exists(), f"Phase 1 path already exists: {rel}")
    for payload in ["audit_event_v2_model.prisma", *NEW_FILES.values()]:
        require((payload_dir / payload).is_file(), f"missing payload: {payload}")

    schema = (repo / "backend/prisma/schema.prisma").read_text(encoding="utf-8")
    app = (repo / "backend/src/app.js").read_text(encoding="utf-8")
    model = (payload_dir / "audit_event_v2_model.prisma").read_text(encoding="utf-8")

    schema_anchor = "\nmodel PermissionAuditLog {\n"
    require(schema.count(schema_anchor) == 1, "Prisma schema anchor mismatch")
    require("model AuditEventV2 {" not in schema, "AuditEventV2 already exists")

    import_anchor = 'import { realtimeStateInvalidationMiddleware } from "./services/realtimeState.service.js";\n'
    import_insert = import_anchor + 'import { requestContextMiddleware } from "./middleware/requestContext.js";\n'
    require(app.count(import_anchor) == 1, "app import anchor mismatch")
    require('from "./middleware/requestContext.js"' not in app, "requestContext import already exists")

    middleware_anchor = '  app.use(express.urlencoded({ extended: true, limit: "5mb" }));\n\n  app.use(csrfMiddleware);\n'
    middleware_insert = '  app.use(express.urlencoded({ extended: true, limit: "5mb" }));\n\n  app.use(requestContextMiddleware);\n  app.use(csrfMiddleware);\n'
    require(app.count(middleware_anchor) == 1, "app middleware anchor mismatch")
    require("app.use(requestContextMiddleware);" not in app, "requestContext middleware already registered")

    with tempfile.TemporaryDirectory(prefix="tos-audit-v2-phase1-") as tmp_name:
        tmp = Path(tmp_name)
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "audit-v2-generator@tamiyouz.local"], tmp)
        run(["git", "config", "user.name", "TOS Audit V2 Generator"], tmp)

        for rel in ["backend/prisma/schema.prisma", "backend/src/app.js", "backend/package.json"]:
            target = tmp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / rel, target)
        run(["git", "add", "backend/prisma/schema.prisma", "backend/src/app.js", "backend/package.json"], tmp)
        run(["git", "commit", "-q", "-m", "baseline"], tmp)

        write_text(tmp / "backend/prisma/schema.prisma", schema.replace(schema_anchor, "\n" + model.rstrip() + "\n\n" + schema_anchor.lstrip("\n"), 1))
        write_text(tmp / "backend/src/app.js", app.replace(import_anchor, import_insert, 1).replace(middleware_anchor, middleware_insert, 1))
        for rel, payload in NEW_FILES.items():
            write_text(tmp / rel, (payload_dir / payload).read_text(encoding="utf-8"))

        for rel in [
            "backend/src/utils/auditRedaction.js",
            "backend/src/middleware/requestContext.js",
            "backend/src/services/auditV2.core.js",
            "backend/src/services/auditV2.service.js",
        ]:
            run(["node", "--check", rel], tmp, capture=False)

        run([
            "node", "--test",
            "src/utils/auditRedaction.test.js",
            "src/middleware/requestContext.test.js",
            "src/services/auditV2.core.test.js",
        ], tmp / "backend", capture=False)

        diff = run(["git", "diff", "--binary", "--full-index", "--no-renames", "HEAD", "--", *PATCH_PATHS], tmp).stdout
        require(diff.strip(), "generated patch is empty")
        output = script_dir / OUTPUT_NAME
        output.write_text(diff, encoding="utf-8", newline="\n")

        apply_check = run(["git", "apply", "--check", str(output)], repo, check=False)
        if apply_check.returncode != 0:
            sys.stderr.write(apply_check.stdout or "")
            sys.stderr.write(apply_check.stderr or "")
            raise RuntimeError("git apply --check failed")

        print("PURE_NODE_TESTS=PASS")
        print("GIT_APPLY_CHECK=PASS")
        print(f"PATCH_FILE={output}")
        print(f"PATCH_SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")
        print("LEGACY_AUDIT_ROUTE_CHANGED=NO")
        print("PHASE_1_FOUNDATION_READY=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PASS/FAIL=FAIL")
        print(f"ERROR={exc}")
        sys.exit(1)
