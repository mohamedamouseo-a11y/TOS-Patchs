#!/usr/bin/env python3
import base64
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zlib
from pathlib import Path

CONFIG_COMMIT = "9a75e1501d1554ca66170989583e1c21ad679af1"
CONFIG_BASE = f"https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/{CONFIG_COMMIT}/TOS-LIVE-SLA-PHASE1-4-PRISMA-POSTGRES-GIT-GENERATED"
CONFIG_PARTS = [f"config.part{index:02d}" for index in range(4)]
EXPECTED_PART_LENGTHS = [7000, 7000, 7000, 6148]
CONFIG_SOURCE_BASE_HEAD = "b37edc16ec9a4b10fad90349b489fd6ac123c064"
TARGET_BASE_HEAD = "959257ed59eb7cb9da0214ce8e2fc22286915b86"
EXPECTED_FRONTEND_PATHS = sorted([
    "frontend/src/App.jsx",
    "frontend/src/components/layout/Sidebar.jsx",
    "frontend/src/lib/pageRoutes.js",
    "frontend/src/pages/SlaAdvancedPage.jsx",
    "frontend/src/pages/SlaCenterPage.jsx",
    "frontend/src/pages/SlaInboxPage.jsx",
])


def load_config():
    parts = [
        urllib.request.urlopen(f"{CONFIG_BASE}/{name}", timeout=30).read().decode("utf-8").strip()
        for name in CONFIG_PARTS
    ]

    # The pinned config has one known overlap: config.part00 contains the first
    # characters of config.part01 after its intended 7000-character payload.
    # Repair only if the overlap is exact; otherwise refuse to continue.
    if len(parts[0]) > EXPECTED_PART_LENGTHS[0]:
        extra = parts[0][EXPECTED_PART_LENGTHS[0]:]
        if not extra or not parts[1].startswith(extra):
            raise RuntimeError(
                f"Unexpected config.part00 overflow: length={len(parts[0])}; overlap verification failed"
            )
        parts[0] = parts[0][:EXPECTED_PART_LENGTHS[0]]

    actual_lengths = [len(part) for part in parts]
    if actual_lengths != EXPECTED_PART_LENGTHS:
        raise RuntimeError(
            f"Unexpected config part lengths: {actual_lengths}; expected {EXPECTED_PART_LENGTHS}"
        )

    encoded = "".join(parts)
    if len(encoded) % 4 != 0:
        raise RuntimeError(f"Invalid base64 config length: {len(encoded)}")

    try:
        compressed = base64.b64decode(encoded, validate=True)
        decoded = zlib.decompress(compressed).decode("utf-8")
        cfg = json.loads(decoded)
    except Exception as exc:
        raise RuntimeError(f"Unable to decode pinned SLA config after overlap repair: {exc}") from exc

    if not isinstance(cfg, dict) or not cfg.get("base_head"):
        raise RuntimeError("Decoded SLA config is missing required base_head")
    if cfg["base_head"] != CONFIG_SOURCE_BASE_HEAD:
        raise RuntimeError(
            f"Unexpected config source base: {cfg['base_head']}; expected {CONFIG_SOURCE_BASE_HEAD}"
        )
    return cfg


def run(args, cwd, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(args)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def replace_once(path, old, new):
    source = path.read_text()
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one anchor in {path}, found {count}: {old[:120]!r}")
    path.write_text(source.replace(old, new, 1))


def is_frontend(rel):
    return str(rel).startswith("frontend/")


def main():
    cfg = load_config()
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "/var/tmp/TOS_LIVE_SLA_FRONTEND_V1.patch").resolve()

    branch = run(["git", "branch", "--show-current"], repo).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    if branch != "main":
        raise RuntimeError(f"Expected branch main, found {branch}")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"Expected HEAD {TARGET_BASE_HEAD}, found {head}")

    # The backend-only SLA commit moved the repository from CONFIG_SOURCE_BASE_HEAD
    # to TARGET_BASE_HEAD. Refuse to reuse the older frontend payload unless Git
    # proves that frontend/** did not change between those two commits.
    frontend_drift = run(
        ["git", "diff", "--name-only", f"{CONFIG_SOURCE_BASE_HEAD}..{TARGET_BASE_HEAD}", "--", "frontend"],
        repo,
    ).stdout.strip().splitlines()
    if frontend_drift:
        raise RuntimeError(
            f"frontend/** changed between config base and target base; refusing stale payload: {frontend_drift}"
        )

    frontend_replacements = {
        rel: replacements
        for rel, replacements in cfg.get("replacements", {}).items()
        if is_frontend(rel)
    }
    frontend_new_files = {
        rel: content
        for rel, content in cfg.get("new_files", {}).items()
        if is_frontend(rel)
    }
    expected_paths = sorted([*frontend_replacements.keys(), *frontend_new_files.keys()])

    if expected_paths != EXPECTED_FRONTEND_PATHS:
        raise RuntimeError(
            f"Unexpected frontend SLA scope: {expected_paths}; expected exactly {EXPECTED_FRONTEND_PATHS}"
        )

    # Validate tracked frontend anchors against the pinned config's original blobs.
    # This also protects against dirty frontend source in the production checkout.
    for rel, expected in cfg.get("expected_blobs", {}).items():
        if not is_frontend(rel):
            continue
        path = repo / rel
        if not path.is_file():
            raise RuntimeError(f"Missing frontend source target: {rel}")
        actual = run(["git", "hash-object", "--", rel], repo).stdout.strip()
        if actual != expected:
            raise RuntimeError(f"Frontend target drift for {rel}: expected {expected}, found {actual}")

    for rel in frontend_new_files:
        if (repo / rel).exists():
            raise RuntimeError(f"New SLA frontend target already exists in working tree: {rel}")

    temp_root = Path(tempfile.mkdtemp(prefix="tos-live-sla-frontend-v1-"))
    worktree = temp_root / "worktree"
    try:
        run(["git", "worktree", "add", "--detach", str(worktree), TARGET_BASE_HEAD], repo)

        for rel, replacements in frontend_replacements.items():
            for old, new in replacements:
                replace_once(worktree / rel, old, new)

        for rel, content in frontend_new_files.items():
            target = worktree / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            run(["git", "add", "-N", "--", rel], worktree)

        changed = sorted(
            run(["git", "diff", "--name-only", "--", "frontend"], worktree).stdout.strip().splitlines()
        )
        if changed != EXPECTED_FRONTEND_PATHS:
            raise RuntimeError(
                f"Unexpected frontend-only SLA patch scope: {changed}; expected {EXPECTED_FRONTEND_PATHS}"
            )

        patch = run(["git", "diff", "--binary", "--", *EXPECTED_FRONTEND_PATHS], worktree).stdout
        if not patch.strip():
            raise RuntimeError("Generated frontend-only SLA patch is empty")

        forbidden_prefixes = [
            "diff --git a/backend/",
            "diff --git a/client/",
            "diff --git a/server/",
            "diff --git a/drizzle/",
        ]
        if any(prefix in patch for prefix in forbidden_prefixes):
            raise RuntimeError("Frontend-only patch unexpectedly contains backend or legacy stack paths")

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(patch)

        apply_check = subprocess.run(
            ["git", "apply", "--check", str(output)],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if apply_check.returncode != 0:
            raise RuntimeError(f"git apply --check failed against production working tree:\n{apply_check.stderr}")

        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        print(f"PATCH={output}")
        print(f"SHA256={digest}")
        print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
        print(f"CONFIG_SOURCE_BASE_HEAD={CONFIG_SOURCE_BASE_HEAD}")
        print(f"CONFIG_COMMIT={CONFIG_COMMIT}")
        print("FRONTEND_ONLY=YES")
        print("BACKEND_INCLUDED=NO")
        print("LEGACY_STACK_INCLUDED=NO")
        print("FILES=")
        for rel in EXPECTED_FRONTEND_PATHS:
            print(rel)
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
