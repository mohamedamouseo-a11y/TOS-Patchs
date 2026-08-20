#!/usr/bin/env python3
import re
import sys
from pathlib import Path

HUNK_RE = re.compile(r'^(?P<prefix>@@ )-(?P<old_start>\d+)(?:,(?P<old_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))?(?P<suffix> @@.*)$')


def fail(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def main():
    if len(sys.argv) != 3:
        fail("usage: repair_unified_diff.py INPUT.patch OUTPUT.patch", 2)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    if not src.is_file():
        fail(f"input patch not found: {src}", 3)

    raw = src.read_bytes()
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if not any(line.startswith("diff --git ") for line in lines):
        fail("not a git unified diff", 4)

    repaired = list(lines)
    found = 0
    i = 0
    while i < len(lines):
        match = HUNK_RE.match(lines[i])
        if not match:
            i += 1
            continue

        found += 1
        old_actual = 0
        new_actual = 0
        j = i + 1
        while j < len(lines):
            line = lines[j]
            if line.startswith("@@ ") or line.startswith("diff --git "):
                break
            if line.startswith(" "):
                old_actual += 1
                new_actual += 1
            elif line.startswith("-") and not line.startswith("--- "):
                old_actual += 1
            elif line.startswith("+") and not line.startswith("+++ "):
                new_actual += 1
            elif line.startswith("\\ No newline at end of file"):
                pass
            else:
                fail(f"invalid unified-diff body line {j + 1}: {line!r}", 5)
            j += 1

        old_start = match.group("old_start")
        new_start = match.group("new_start")
        suffix = match.group("suffix")
        old_count_declared = int(match.group("old_count") or "1")
        new_count_declared = int(match.group("new_count") or "1")
        before = lines[i]
        after = f"@@ -{old_start},{old_actual} +{new_start},{new_actual}{suffix}"
        repaired[i] = after
        print(
            f"HUNK line={i + 1} old={old_count_declared}->{old_actual} "
            f"new={new_count_declared}->{new_actual}"
        )
        print(f"HEADER_BEFORE={before}")
        print(f"HEADER_AFTER={after}")
        i = j

    if found == 0:
        fail("no unified-diff hunks found", 6)

    output = "\n".join(repaired) + "\n"
    dst.write_text(output, encoding="utf-8", newline="\n")

    # Self-validate the repaired structure.
    check_lines = output.splitlines()
    i = 0
    validated = 0
    while i < len(check_lines):
        match = HUNK_RE.match(check_lines[i])
        if not match:
            i += 1
            continue
        validated += 1
        old_expected = int(match.group("old_count") or "1")
        new_expected = int(match.group("new_count") or "1")
        old_actual = 0
        new_actual = 0
        j = i + 1
        while j < len(check_lines):
            line = check_lines[j]
            if line.startswith("@@ ") or line.startswith("diff --git "):
                break
            if line.startswith(" "):
                old_actual += 1
                new_actual += 1
            elif line.startswith("-") and not line.startswith("--- "):
                old_actual += 1
            elif line.startswith("+") and not line.startswith("+++ "):
                new_actual += 1
            elif line.startswith("\\ No newline at end of file"):
                pass
            else:
                fail(f"repaired diff has invalid body line {j + 1}: {line!r}", 7)
            j += 1
        if old_expected != old_actual or new_expected != new_actual:
            fail(
                f"self-check mismatch at hunk line {i + 1}: "
                f"old {old_expected}!={old_actual}; new {new_expected}!={new_actual}",
                8,
            )
        i = j

    if validated != found:
        fail(f"self-check hunk count changed: {found}->{validated}", 9)
    if not output.endswith("\n"):
        fail("output is missing terminal newline", 10)

    print(f"HUNKS={validated}")
    print(f"OUTPUT_LINES={len(check_lines)}")
    print("TERMINAL_NEWLINE=PASS")
    print("UNIFIED_DIFF_STRUCTURE=PASS")
    print(f"OUTPUT={dst}")


if __name__ == "__main__":
    main()
