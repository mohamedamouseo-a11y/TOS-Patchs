from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
BASE_SCRIPT = PATCH_DIR.parent / "TOS-THRS-EXECUTIVE-PREMIUM-V2" / "apply_tos_thrs_executive_premium_v2.py"

print("RUNNING=TOS_THRS_EXECUTIVE_PREMIUM_V2_1_ANCHOR_FIX_WRAPPER")

if not BASE_SCRIPT.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base V2 script missing: {BASE_SCRIPT}")
    sys.exit(1)

source = BASE_SCRIPT.read_text(encoding="utf-8")

old_block = '''    request_shell_old = '<div dir={isAr ? "rtl" : "ltr"} className="rounded-[30px] border border-slate-200/80 bg-white/95 p-5 shadow-sm shadow-slate-200/70 dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-none sm:rounded-[36px]">'\n    request_shell_new = '<div dir={isAr ? "rtl" : "ltr"} className="tos-thrs-request-shell-v2 rounded-[30px] border border-slate-200/80 bg-white/95 p-5 shadow-sm shadow-slate-200/70 dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-none sm:rounded-[36px]">'\n    page = replace_once(page, request_shell_old, request_shell_new, "THRS request premium shell")'''

new_block = '''    request_shell_old = ''' + "'''" + '''<div dir={isAr ? "rtl" : "ltr"} className="rounded-[30px] border border-slate-200/80 bg-white/95 p-5 shadow-sm shadow-slate-200/70 dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-none sm:rounded-[36px]">\n          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">\n            <div>\n              <h2 className="text-xl font-black text-slate-950 dark:text-white">{isAr ? "طلبات THRS" : "THRS Requests"}</h2>''' + "'''" + '''\n    request_shell_new = ''' + "'''" + '''<div dir={isAr ? "rtl" : "ltr"} className="tos-thrs-request-shell-v2 rounded-[30px] border border-slate-200/80 bg-white/95 p-5 shadow-sm shadow-slate-200/70 dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-none sm:rounded-[36px]">\n          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">\n            <div>\n              <h2 className="text-xl font-black text-slate-950 dark:text-white">{isAr ? "طلبات THRS" : "THRS Requests"}</h2>''' + "'''" + '''\n    page = replace_once(page, request_shell_old, request_shell_new, "THRS request premium shell scoped to THRS Requests heading")'''

count = source.count(old_block)
if count != 1:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base V2 patch shape changed; expected old request-shell transform once, found {count}")
    sys.exit(1)

source = source.replace(old_block, new_block, 1)
source = source.replace('print("RUNNING=TOS_THRS_EXECUTIVE_PREMIUM_V2")', 'print("RUNNING=TOS_THRS_EXECUTIVE_PREMIUM_V2_1")', 1)

# Execute the guarded V2 patch in-memory while preserving __file__ as the original
# V2 script path so its PATCH_DIR continues to resolve its own source assets.
namespace = {
    "__name__": "__main__",
    "__file__": str(BASE_SCRIPT),
}
old_argv = sys.argv[:]
try:
    sys.argv = [str(BASE_SCRIPT), str(ROOT)]
    exec(compile(source, str(BASE_SCRIPT), "exec"), namespace, namespace)
finally:
    sys.argv = old_argv
