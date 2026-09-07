from pathlib import Path
import sys

PATCH_ROOT = Path(__file__).resolve().parents[1]
BASE_R3 = PATCH_ROOT / "TOS-UXUI-SYSTEM-TWS-DASHBOARD-FLAGSHIP-V1-R3-PARTIAL-STATE-CSS-RECONCILE" / "apply_tos_uxui_system_tws_dashboard_flagship_v1_r3_partial_state_css_reconcile.py"

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R4_CSS_AST_EXTRACTION_GUARD_FIX")

if not BASE_R3.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base R3 installer missing: {BASE_R3}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R4_RUNTIME=NO")
    sys.exit(1)

source = BASE_R3.read_text(encoding="utf-8")

OLD_IMPORT = "from pathlib import Path\nimport hashlib\n"
NEW_IMPORT = "from pathlib import Path\nimport ast\nimport hashlib\n"

OLD_RUNNING = 'print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R3_PARTIAL_STATE_CSS_RECONCILE")'
NEW_RUNNING = 'print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R4_CSS_AST_EXTRACTION_GUARD_FIX_INNER")'

OLD_RUNTIME_NO = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R3_RUNTIME=NO")'
NEW_RUNTIME_NO = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R4_RUNTIME=NO")'

OLD_RUNTIME_YES = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R3_RUNTIME=YES")'
NEW_RUNTIME_YES = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R4_RUNTIME=YES")'

OLD_EXTRACT = '''# Extract the exact original V1 CSS payload from the guarded V1 installer.
base_text = BASE_V1.read_text(encoding="utf-8")
start_anchor = "CSS = r\'\'\'"
end_anchor = "\\n\'\'\'\\n\\nprint(\\\"RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1\\\")"
if base_text.count(start_anchor) != 1:
    fail(f"base V1 CSS start anchor mismatch: {base_text.count(start_anchor)}")
start = base_text.index(start_anchor) + len(start_anchor)
end = base_text.find(end_anchor, start)
if end < 0:
    fail("base V1 CSS end anchor missing")
css_text = base_text[start:end]
css_bytes = css_text.encode("utf-8")
css_blob = git_blob_sha_bytes(css_bytes)
if css_blob != EXPECTED_STYLE_GIT_BLOB_SHA:
    fail(f"extracted V1 stylesheet blob mismatch: {css_blob}")
'''

NEW_EXTRACT = '''# Extract the exact Python value of the original V1 CSS assignment.
# AST avoids newline/quote slicing errors and returns the same string V1 would write.
base_text = BASE_V1.read_text(encoding="utf-8")
try:
    base_tree = ast.parse(base_text, filename=str(BASE_V1))
except SyntaxError as exc:
    fail(f"base V1 installer AST parse failed: {exc}")

css_assignments = []
for node in base_tree.body:
    if not isinstance(node, ast.Assign):
        continue
    if any(isinstance(target, ast.Name) and target.id == "CSS" for target in node.targets):
        css_assignments.append(node)

if len(css_assignments) != 1:
    fail(f"base V1 CSS AST assignment mismatch: {len(css_assignments)}")

try:
    css_text = ast.literal_eval(css_assignments[0].value)
except Exception as exc:
    fail(f"base V1 CSS AST literal extraction failed: {exc}")

if not isinstance(css_text, str) or not css_text:
    fail("base V1 CSS AST extraction returned invalid payload")

css_bytes = css_text.encode("utf-8")
css_blob = git_blob_sha_bytes(css_bytes)
if css_blob != EXPECTED_STYLE_GIT_BLOB_SHA:
    fail(f"AST-extracted V1 stylesheet blob mismatch: {css_blob}")
'''

checks = [
    (OLD_IMPORT, 1, "import anchor"),
    (OLD_RUNNING, 1, "RUNNING marker"),
    (OLD_RUNTIME_NO, 1, "runtime NO marker"),
    (OLD_RUNTIME_YES, 1, "runtime YES marker"),
    (OLD_EXTRACT, 1, "R3 extraction block"),
]
for needle, expected, label in checks:
    count = source.count(needle)
    if count != expected:
        print("PASS/FAIL=FAIL")
        print(f"ERROR=R4 wrapper {label} mismatch: expected {expected}, found {count}")
        print("BUILD_RESULT=FAIL_OR_SKIPPED")
        print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
        print("TWS_DASHBOARD_FLAGSHIP_V1_R4_RUNTIME=NO")
        sys.exit(1)

corrected = source
corrected = corrected.replace(OLD_IMPORT, NEW_IMPORT, 1)
corrected = corrected.replace(OLD_RUNNING, NEW_RUNNING, 1)
corrected = corrected.replace(OLD_RUNTIME_NO, NEW_RUNTIME_NO, 1)
corrected = corrected.replace(OLD_RUNTIME_YES, NEW_RUNTIME_YES, 1)
corrected = corrected.replace(OLD_EXTRACT, NEW_EXTRACT, 1)

if OLD_EXTRACT in corrected or "import ast" not in corrected or "ast.literal_eval" not in corrected:
    print("PASS/FAIL=FAIL")
    print("ERROR=R4 in-memory AST extraction correction failed")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R4_RUNTIME=NO")
    sys.exit(1)

# R4 changes only how the already-missing stylesheet payload is extracted.
# All R3 source SHA guards, exact partial-state checks, behavior markers,
# preservation checks, build, cleanup-on-failure, atomic deploy and rollback remain unchanged.
namespace = {
    "__name__": "__main__",
    "__file__": str(BASE_R3),
}
exec(compile(corrected, str(BASE_R3), "exec"), namespace, namespace)
