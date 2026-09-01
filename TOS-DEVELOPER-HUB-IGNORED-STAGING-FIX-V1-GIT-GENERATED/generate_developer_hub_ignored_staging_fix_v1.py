#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "63f59932776e29e32bacdf5214744d2662a3b8e3"
TARGET = "backend/src/services/githubAdvanced.service.js"
EXPECTED_BLOB = "8b02edc0ff82af6f2362ac98a055def69549a36c"
START_MARKER = "async function stageSafeChanges(repoPath, operationId) {"
END_MARKER = "\nfunction validGitSha(value) {"

NEW_FUNCTION = r'''async function stageSafeChanges(repoPath, operationId) {
  const status = await runGitRaw(repoPath, ["status", "--porcelain=v1", "-z"], { timeout: 15_000, raw: true });
  const entries = parsePorcelainZ(status.stdout);
  const safe = [];
  const blocked = [];
  const excluded = [];
  for (const entry of entries) {
    const automaticExclusion = await getAutomaticExclusion(repoPath, entry);
    if (automaticExclusion) {
      excluded.push(automaticExclusion);
      continue;
    }
    const reason = await scanLocalEntry(repoPath, entry);
    if (reason) blocked.push({ path: entry.path, reason });
    else {
      safe.push(entry.path);
      if (entry.originalPath) safe.push(entry.originalPath);
    }
  }
  if (blocked.length) throw new AppError(`Sensitive or blocked files detected: ${blocked.map((item) => item.path).join(", ")}`, 409);

  // Preserve deletions that are already staged while the same runtime file still exists
  // locally under a newly-added .gitignore rule. Re-running `git add -A -- <path>` for
  // such a path makes Git try to re-add the ignored worktree copy and abort the push.
  const stagedBefore = parseNameStatusZ((await runGitRaw(
    repoPath,
    ["diff", "--cached", "--name-status", "-z"],
    { timeout: 15_000, raw: true },
  )).stdout, "local");
  const stagedDeletionPaths = new Set();
  for (const entry of stagedBefore) {
    if (!cleanText(entry.status).startsWith("D")) continue;
    stagedDeletionPaths.add(normalizeRelativePath(entry.path));
    if (entry.originalPath) stagedDeletionPaths.add(normalizeRelativePath(entry.originalPath));
  }

  const safeToStage = [];
  const preservedIgnoredDeletions = [];
  for (const candidate of [...new Set(safe.map(normalizeRelativePath).filter(Boolean))]) {
    if (stagedDeletionPaths.has(candidate)) {
      const ignored = await runGitRaw(repoPath, ["check-ignore", "-q", "--", candidate], {
        timeout: 15_000,
        allowFailure: true,
      });
      if (ignored.code === 0) {
        preservedIgnoredDeletions.push(candidate);
        continue;
      }
    }
    safeToStage.push(candidate);
  }

  if (!safeToStage.length && !stagedBefore.length) throw new AppError("No safe source changes to commit", 409);
  if (preservedIgnoredDeletions.length) {
    await appendOperationLog(
      operationId,
      "info",
      `Preserving ${preservedIgnoredDeletions.length} staged deletion(s) for ignored runtime paths: ${preservedIgnoredDeletions.join(", ")}`,
      `تم الاحتفاظ بحذف ${preservedIgnoredDeletions.length} ملف/ملفات runtime متجاهلة من Git بدون إعادة إضافتها`,
    );
  }

  for (let index = 0; index < safeToStage.length; index += 100) {
    await runOperationGit(repoPath, ["add", "-A", "--", ...safeToStage.slice(index, index + 100)], await getSettings(), operationId, { timeout: 60_000 });
  }
  const staged = parseNameStatusZ((await runGitRaw(repoPath, ["diff", "--cached", "--name-status", "-z"], { timeout: 15_000, raw: true })).stdout, "local");
  if (!staged.length) throw new AppError("No source changes to commit", 409);
  for (const entry of staged) {
    const reason = await scanLocalEntry(repoPath, entry);
    if (reason) {
      await runGitRaw(repoPath, ["reset", "--", entry.path], { timeout: 30_000, allowFailure: true });
      throw new AppError(`Refused to stage ${entry.path}: ${reason}`, 409);
    }
  }
  return { files: staged, excluded, preservedIgnoredDeletions };
}
'''


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if check and proc.returncode:
        die(f"command failed rc={proc.returncode}: {' '.join(args)}", 90)
    return proc


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 3:
        die("usage: generate_developer_hub_ignored_staging_fix_v1.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET

    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)
    if not target.is_file():
        die(f"target missing: {TARGET}", 4)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 5)

    blob = run(["git", "hash-object", TARGET], root).stdout.strip()
    print(f"SOURCE_BLOB={blob}")
    if blob != EXPECTED_BLOB:
        die(f"target blob mismatch expected={EXPECTED_BLOB} actual={blob}", 6)

    if run(["git", "diff", "--cached", "--", TARGET], root).stdout.strip():
        die("target has staged changes", 7)
    if run(["git", "diff", "--", TARGET], root).stdout.strip():
        die("target has tracked local changes", 8)
    print("TARGET_CLEAN=YES")

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF source detected", 9)
    had_terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    if text.count(START_MARKER) != 1:
        die(f"expected exactly one start marker, found {text.count(START_MARKER)}", 10)
    if text.count(END_MARKER) != 1:
        die(f"expected exactly one end marker, found {text.count(END_MARKER)}", 11)

    start = text.index(START_MARKER)
    end = text.index(END_MARKER, start)
    old_function = text[start:end]
    if 'runOperationGit(repoPath, ["add", "-A", "--", ...safe.slice(index, index + 100)]' not in old_function:
        die("expected vulnerable git add -A staging pattern not found", 12)

    updated = text[:start] + NEW_FUNCTION.rstrip("\n") + text[end:]

    tmp = Path(tempfile.mkdtemp(prefix="tos-github-stage-fix-v1-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "developer-hub-fix@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Developer Hub Staging Fix"], tmp)

        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)

        encoded = updated.encode("utf-8")
        if had_terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not had_terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        run(["node", "--check", str(tmp_target)], tmp)
        print("NODE_CHECK=PASS")

        proc = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", TARGET],
            cwd=tmp,
            text=True,
            capture_output=True,
        )
        if proc.returncode:
            die(f"git diff failed rc={proc.returncode}", 40)
        if not proc.stdout.strip():
            die("generated patch is empty", 41)

        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if parsed_paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 42)
        print("PATCH_PATH_CHECK=PASS")

        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("FIX_MODE=PRESERVE_STAGED_IGNORED_DELETIONS")
        print("FORCE_ADD_USED=NO")
        print("DEVELOPER_HUB_IGNORED_STAGING_FIX_V1_GENERATOR=PASS")
        print(f"TARGET_PATH={TARGET}")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
