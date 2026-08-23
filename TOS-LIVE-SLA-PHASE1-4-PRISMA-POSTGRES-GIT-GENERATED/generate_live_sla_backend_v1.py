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


def load_config():
    parts = [
        urllib.request.urlopen(f"{CONFIG_BASE}/{name}", timeout=30).read().decode("utf-8").strip()
        for name in CONFIG_PARTS
    ]

    # The pinned config has a known, exact overlap: config.part00 contains the
    # beginning of config.part01 appended after its intended 7000 characters.
    # Repair only when that overlap is verified byte-for-byte.
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


def is_backend(rel):
    return str(rel).startswith("backend/")


def main():
    cfg = load_config()
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "/var/tmp/TOS_LIVE_SLA_BACKEND_V1.patch").resolve()
    base_head = cfg["base_head"]

    branch = run(["git", "branch", "--show-current"], repo).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    if branch != "main":
        raise RuntimeError(f"Expected branch main, found {branch}")
    if head != base_head:
        raise RuntimeError(f"Expected HEAD {base_head}, found {head}")

    backend_replacements = {
        rel: replacements
        for rel, replacements in cfg.get("replacements", {}).items()
        if is_backend(rel)
    }
    backend_new_files = {
        rel: content
        for rel, content in cfg.get("new_files", {}).items()
        if is_backend(rel)
    }
    expected_paths = sorted([*backend_replacements.keys(), *backend_new_files.keys()])

    if not expected_paths:
        raise RuntimeError("Pinned SLA config contains no backend targets")
    if any(not is_backend(rel) for rel in expected_paths):
        raise RuntimeError(f"Non-backend path escaped backend-only filter: {expected_paths}")

    # Validate only backend tracked targets. Legacy root stack and unknown
    # frontend producer files are deliberately excluded from this patch.
    for rel, expected in cfg.get("expected_blobs", {}).items():
        if not is_backend(rel):
            continue
        path = repo / rel
        if not path.is_file():
            raise RuntimeError(f"Missing live backend target: {rel}")
        actual = run(["git", "hash-object", "--", rel], repo).stdout.strip()
        if actual != expected:
            raise RuntimeError(f"Live backend target drift for {rel}: expected {expected}, found {actual}")

    for rel in backend_new_files:
        if (repo / rel).exists():
            raise RuntimeError(f"New live backend SLA target already exists in production working tree: {rel}")

    temp_root = Path(tempfile.mkdtemp(prefix="tos-live-sla-backend-v1-"))
    worktree = temp_root / "worktree"
    try:
        run(["git", "worktree", "add", "--detach", str(worktree), base_head], repo)

        for rel, replacements in backend_replacements.items():
            for old, new in replacements:
                replace_once(worktree / rel, old, new)

        for rel, content in backend_new_files.items():
            target = worktree / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            run(["git", "add", "-N", "--", rel], worktree)

        changed = sorted(run(["git", "diff", "--name-only", "--", "backend"], worktree).stdout.strip().splitlines())
        if changed != expected_paths:
            raise RuntimeError(f"Unexpected backend-only SLA patch scope: {changed}; expected {expected_paths}")

        patch = run(["git", "diff", "--binary", "--", *expected_paths], worktree).stdout
        if not patch.strip():
            raise RuntimeError("Generated backend-only SLA patch is empty")
        if "diff --git a/frontend/" in patch or "diff --git a/client/" in patch or "diff --git a/server/" in patch or "diff --git a/drizzle/" in patch:
            raise RuntimeError("Backend-only patch unexpectedly contains frontend or legacy stack paths")

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
        print(f"BASE_HEAD={base_head}")
        print(f"CONFIG_COMMIT={CONFIG_COMMIT}")
        print("BACKEND_ONLY=YES")
        print("FILES=")
        for rel in expected_paths:
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
