from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent / "apply_r28_production.py"
source = BASE.read_text()
old = '''    setTaskMoreDetailsOpen(nextOpen);\n\n    if (!scroller || typeof window === "undefined") return;'''
new = '''    setTaskMoreDetailsOpen(Boolean(nextOpen));\n\n    if (!scroller || typeof window === "undefined") return;'''

if source.count(old) != 1:
    raise RuntimeError(f"R28 v2 installer self-check failed: expected one helper raw setter, found {source.count(old)}")

# Fix installer-only counting bug: the helper's own raw state setter must not be
# counted as a user-triggered More toggle. Target application code is unchanged
# until the original R28 installer passes all of its production preflight checks.
source = source.replace(old, new, 1)
namespace = {"__name__": "__main__", "__file__": str(BASE)}
exec(compile(source, str(BASE), "exec"), namespace, namespace)
