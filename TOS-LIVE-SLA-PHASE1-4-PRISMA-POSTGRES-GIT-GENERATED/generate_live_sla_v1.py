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


def load_config():
    encoded = "".join(
        urllib.request.urlopen(f"{CONFIG_BASE}/{name}", timeout=30).read().decode("utf-8").strip()
        for name in CONFIG_PARTS
    )
    return json.loads(zlib.decompress(base64.b64decode(encoded)).decode("utf-8"))


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


def main():
    cfg = load_config()
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "/var/tmp/TOS_LIVE_SLA_V1.patch").resolve()
    base_head = cfg["base_head"]

    branch = run(["git", "branch", "--show-current"], repo).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    if branch != "main":
        raise RuntimeError(f"Expected branch main, found {branch}")
    if head != base_head:
        raise RuntimeError(f"Expected HEAD {base_head}, found {head}")

    # Validate only the live backend/frontend targets. Existing dirty legacy SLA files
    # under root client/server/drizzle are intentionally tolerated and not touched here.
    for rel, expected in cfg["expected_blobs"].items():
        path = repo / rel
        if not path.is_file():
            raise RuntimeError(f"Missing live-stack target: {rel}")
        actual = run(["git", "hash-object", "--", rel], repo).stdout.strip()
        if actual != expected:
            raise RuntimeError(f"Live-stack target drift for {rel}: expected {expected}, found {actual}")

    for rel in cfg["new_files"]:
        if (repo / rel).exists():
            raise RuntimeError(f"New live SLA target already exists in production working tree: {rel}")

    temp_root = Path(tempfile.mkdtemp(prefix="tos-live-sla-v1-"))
    worktree = temp_root / "worktree"
    try:
        run(["git", "worktree", "add", "--detach", str(worktree), base_head], repo)

        for rel, replacements in cfg["replacements"].items():
            for old, new in replacements:
                replace_once(worktree / rel, old, new)

        for rel, content in cfg["new_files"].items():
            target = worktree / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            run(["git", "add", "-N", "--", rel], worktree)

        expected_paths = sorted([*cfg["replacements"].keys(), *cfg["new_files"].keys()])
        changed = sorted(run(["git", "diff", "--name-only"], worktree).stdout.strip().splitlines())
        if changed != expected_paths:
            raise RuntimeError(f"Unexpected live SLA patch scope: {changed}; expected {expected_paths}")

        patch = run(["git", "diff", "--binary", "--", *expected_paths], worktree).stdout
        if not patch.strip():
            raise RuntimeError("Generated live SLA patch is empty")
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
