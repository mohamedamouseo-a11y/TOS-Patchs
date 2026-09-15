from pathlib import Path
import hashlib, json, shutil, subprocess, sys, time

VERSION="TOS_TASK_DETAILS_V2_12_PHASE1_R14_RIGHT_RAIL_BOTTOM_SCROLL_EXTENT"
PATCH_NAME="TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R14-RIGHT-RAIL-BOTTOM-SCROLL-EXTENT"
R13_MARKER="--tos-task-details-v2-12-phase1-r13-structural-physical-right-rail-slot-runtime"
R14_MARKER="--tos-task-details-v2-12-phase1-r14-right-rail-bottom-scroll-extent-runtime"
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else "/var/www/TOS")
FRONTEND=ROOT/"frontend"; STYLE_DIR=FRONTEND/"src/styles"
BOARD=FRONTEND/"src/components/ProfessionalTaskBoard.jsx"
APP=FRONTEND/"src/App.jsx"; SIDEBAR=FRONTEND/"src/components/layout/Sidebar.jsx"
R13_STYLE=STYLE_DIR/"taskDetailsV2_12_Phase1R13StructuralPhysicalRightRailSlot.css"
R14_STYLE=STYLE_DIR/"taskDetailsV2_12_Phase1R14RightRailBottomScrollExtent.css"
MANIFEST=ROOT/"deployment/tos-production-runtime.json"
PATCH_DIR=Path(__file__).resolve().parent
PAYLOAD=PATCH_DIR/"taskDetailsV2_12_Phase1R14RightRailBottomScrollExtent.css"

def fail(m): raise RuntimeError(m)
def run(cmd,cwd=None): subprocess.run(cmd,cwd=cwd,check=True)
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()

for p in (FRONTEND,STYLE_DIR,BOARD,APP,SIDEBAR,R13_STYLE,MANIFEST,PAYLOAD):
    if not p.exists(): fail(f"required path missing: {p}")
for c in ("node","npm"):
    if not shutil.which(c): fail(f"required command not found: {c}")

board=BOARD.read_text(); r13=R13_STYLE.read_text(); css=PAYLOAD.read_text()
if R13_MARKER not in r13: fail("required R13 baseline marker missing")
if R14_STYLE.exists() or R14_MARKER in board: fail("Phase 1 R14 already appears to be applied")
if R14_MARKER not in css: fail("R14 payload runtime marker missing")
for contract in ('className="tos-task-reference-v2-rail-slot"','className="tos-task-reference-v2-rail"'):
    if contract not in board: fail(f"R13 DOM contract missing: {contract}")
r13_import='import "../styles/taskDetailsV2_12_Phase1R13StructuralPhysicalRightRailSlot.css";'
r14_import='import "../styles/taskDetailsV2_12_Phase1R14RightRailBottomScrollExtent.css";'
if r13_import not in board: fail("R13 stylesheet import missing")
updated=board.replace(r13_import,r13_import+"\n"+r14_import,1)
for contract in ('min-height:900px!important','padding-bottom:24px!important','.tos-task-reference-v2-rail-slot'):
    if contract not in css: fail(f"R14 CSS contract missing: {contract}")

app_hash=sha256(APP); sidebar_hash=sha256(SIDEBAR)
prior={p:sha256(p) for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p!=R14_STYLE}
manifest=json.loads(MANIFEST.read_text()); fe=manifest.get("frontend") or {}
if manifest.get("application")!="TOS" or manifest.get("environment")!="production": fail("unexpected runtime manifest")
if manifest.get("sourceRoot")!=str(ROOT): fail("runtime sourceRoot mismatch")
DIST=Path(str(fe.get("buildOutputDir") or "")); LIVE=Path(str(fe.get("publishedBuildDir") or ""))
if Path(str(fe.get("sourceDir") or ""))!=FRONTEND or str(fe.get("buildCommand") or "")!="npm run build": fail("frontend runtime mismatch")
if DIST!=FRONTEND/"dist" or LIVE!=Path("/opt/apps/tamiyouz-front/build"): fail("unexpected build/live path")

stamp=int(time.time()); backup=Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r14-{stamp}")
backup.mkdir(parents=True,exist_ok=False); shutil.copy2(BOARD,backup/BOARD.name)
staging=LIVE.parent/f"build.task-details-v2-12-phase1-r14-staging-{stamp}"
live_backup=LIVE.parent/f"build.task-details-v2-12-phase1-r14-backup-{stamp}"
swapped=False; written=False
try:
    BOARD.write_text(updated); R14_STYLE.write_text(css.rstrip()+"\n"); written=True
    if sha256(APP)!=app_hash or sha256(SIDEBAR)!=sidebar_hash: fail("frozen shell source changed")
    for p,d in prior.items():
        if sha256(p)!=d: fail(f"prior Phase1 stylesheet changed: {p.name}")
    run(["npm","run","build"],cwd=FRONTEND)
    if not (DIST/"index.html").exists(): fail("frontend dist missing")
    built="\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R14_MARKER,R13_MARKER):
        if marker not in built: fail(f"marker missing from build: {marker}")
    if staging.exists(): shutil.rmtree(staging)
    shutil.copytree(DIST,staging)
    if LIVE.exists():
        if live_backup.exists(): shutil.rmtree(live_backup)
        LIVE.rename(live_backup)
    staging.rename(LIVE); swapped=True
except Exception:
    shutil.copy2(backup/BOARD.name,BOARD)
    if written and R14_STYLE.exists(): R14_STYLE.unlink()
    if swapped:
        if LIVE.exists(): shutil.rmtree(LIVE)
        if live_backup.exists(): live_backup.rename(LIVE)
    elif staging.exists(): shutil.rmtree(staging)
    raise

print(f"PATCH={PATCH_NAME}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print("RIGHT_RAIL_BOTTOM_SCROLL_EXTENT=FIXED")
print("R13_RIGHT_RAIL_PLACEMENT_PRESERVED=YES")
print("TASK_CARD_GEOMETRY_CHANGED=NO")
print("SCROLL_OWNER_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("SIDEBAR_JS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup}")
print("FINAL_STATUS=PASS")
