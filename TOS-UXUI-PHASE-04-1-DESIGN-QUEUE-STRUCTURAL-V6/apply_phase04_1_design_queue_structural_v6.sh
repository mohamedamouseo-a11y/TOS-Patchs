#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE04_1_DESIGN_QUEUE_STRUCTURAL_V6"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/design-queue-structural-v6.css"

DESIGN_TARGET="frontend/src/pages/DesignQueuePage.jsx"
WORKHUB_TARGET="frontend/src/pages/EmployeeWorkHub.jsx"
TEAM_TARGET="frontend/src/pages/TeamPage.jsx"
PERF_TARGET="frontend/src/pages/TeamPerformanceDashboard.jsx"
CSS_TARGET="frontend/src/index.css"

# Exact reviewed V5 worktree hashes.
DESIGN_V5_SHA256="d1a7d362d18506582e61f2a6f552fb88793bebd8174c3b6d60c74a3214a9cb3c"
CSS_V5_SHA256="9e0d0d1c8e762731ea0fb5c8408c5a8e96ac02cb671482bee1c031d76b06fc53"
WORKHUB_SHA256="d86f5553b002b6fd89328c90ab5c369050595cee87695200d89f77a74d292e43"
TEAM_SHA256="d14814aca4482d8c89d7a8a734125703f5b6123f58ccfff7368878ca94b67efe"
PERF_SHA256="36dc277b800dc03129d8fc7feefc7b877906eb6ee9a73712805237326262bcaf"

V1_RUNTIME="--tos-phase04-runtime"
V2_RUNTIME="--tos-phase04-v2-runtime"
V3_RUNTIME="--tos-dq-v3-runtime"
V4_RUNTIME="--tos-dq-v4-runtime"
V5_RUNTIME="--tos-dq-v5-runtime"
V6_RUNTIME="--tos-dq-v6-runtime"
DESIGN_HOOK="tos-core-design-queue-premium"

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase04-1-design-queue-v6.new.$$"
BACKUP="$LIVE_PARENT/build.phase04-1-design-queue-v6.backup-$STAMP"

fail(){ echo "PHASE04_1_DESIGN_QUEUE_STRUCTURAL_V6=FAIL"; echo "ERROR=$1" >&2; exit "${2:-1}"; }
sha256(){ sha256sum "$ROOT/$1" | awk '{print $1}'; }

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V6 CSS source missing" 4
[ -d "$LIVE" ] || fail "Live frontend root missing" 5
for path in "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 6
done

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7
CURRENT_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n' "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$PERF_TARGET" "$TEAM_TARGET" | sort)"
[ "$CURRENT_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected worktree shape before V6" 8

[ "$(sha256 "$DESIGN_TARGET")" = "$DESIGN_V5_SHA256" ] || fail "Design Queue differs from reviewed V5 state" 9
[ "$(sha256 "$CSS_TARGET")" = "$CSS_V5_SHA256" ] || fail "index.css differs from reviewed V5 state" 10
[ "$(sha256 "$WORKHUB_TARGET")" = "$WORKHUB_SHA256" ] || fail "THRS changed since reviewed state" 11
[ "$(sha256 "$TEAM_TARGET")" = "$TEAM_SHA256" ] || fail "Team Members changed since reviewed state" 12
[ "$(sha256 "$PERF_TARGET")" = "$PERF_SHA256" ] || fail "Team Performance changed since reviewed state" 13

for marker in "$V1_RUNTIME" "$V2_RUNTIME" "$V3_RUNTIME" "$V4_RUNTIME" "$V5_RUNTIME"; do
  [ "$(grep -Fc -- "$marker" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Required runtime missing/duplicated: $marker" 14
done
[ "$(grep -Fc -- "$V6_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "V6 already present" 15
[ "$(grep -Fc -- "$DESIGN_HOOK" "$ROOT/$DESIGN_TARGET" || true)" = "2" ] || fail "Design Queue premium hooks missing" 16

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V6 CSS differs from TOS-Patchs HEAD" 17

python3 - "$ROOT/$DESIGN_TARGET" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()

replacements = []

old = '''function QueueStatRing({ label, value, total, tone = "zinc", note }) {
  const numeric = Number(value) || 0;
  const denominator = Math.max(1, Number(total) || numeric || 1);
  const percent = Math.min(100, Math.round((numeric / denominator) * 100));
  const color = { zinc: "#18181b", red: "#ef4444", amber: "#f59e0b", blue: "#3b82f6", violet: "#8b5cf6", green: "#10b981" }[tone] || "#18181b";
  return (
    <div className="flex min-w-[102px] flex-1 flex-col items-center text-center">
      <div className="relative grid h-16 w-16 place-items-center rounded-full" style={{ background: `conic-gradient(${color} ${percent * 3.6}deg, #e4e4e7 0deg)` }}>
        <div className="grid h-11 w-11 place-items-center rounded-full bg-white text-base font-black text-zinc-950 shadow-inner dark:bg-zinc-950 dark:text-white">{numeric}</div>
      </div>
      <div className="mt-1.5 text-[11px] font-black text-zinc-800 dark:text-zinc-100">{label}</div>
      <div className="mt-0.5 text-[9px] font-bold text-zinc-400">{percent}% {note}</div>
    </div>
  );
}'''
new = '''function QueueStatRing({ label, value, total, tone = "zinc", note }) {
  const numeric = Number(value) || 0;
  const denominator = Math.max(1, Number(total) || numeric || 1);
  const percent = Math.min(100, Math.round((numeric / denominator) * 100));
  const color = { zinc: "#85878d", red: "#ef4444", amber: "#d89b26", blue: "#4f86e8", violet: "#8b5cf6", green: "#10b981" }[tone] || "#85878d";
  return (
    <div className={cn("tos-dq-stat-card", `tos-dq-stat-${tone}`)}>
      <div className="tos-dq-stat-orbit" style={{ background: `conic-gradient(${color} ${percent * 3.6}deg, rgba(161,161,170,.22) 0deg)` }}>
        <div className="tos-dq-stat-orbit-inner">{numeric}</div>
      </div>
      <div className="tos-dq-stat-copy">
        <div className="tos-dq-stat-label">{label}</div>
        <div className="tos-dq-stat-note">{percent}% {note}</div>
      </div>
    </div>
  );
}'''
replacements.append((old,new,'QueueStatRing'))

replacements += [
('''<button type="button" onClick={() => onSelect(task.id)} className="w-full rounded-[16px] border border-zinc-100 bg-white p-2.5 text-start shadow-sm transition hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-md dark:border-white/10 dark:bg-zinc-950">''',
 '''<button type="button" onClick={() => onSelect(task.id)} className="tos-dq-task-card w-full rounded-[16px] border border-zinc-100 bg-white p-2.5 text-start shadow-sm transition hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-md dark:border-white/10 dark:bg-zinc-950">''','TaskCard hook'),
('''<section key={column.id} className="flex h-full min-w-0 flex-col overflow-hidden rounded-[18px] border border-zinc-100 bg-zinc-50/80 dark:border-white/10 dark:bg-white/[0.03]">''',
 '''<section key={column.id} className={cn("tos-dq-kanban-column flex h-full min-w-0 flex-col overflow-hidden rounded-[18px] border border-zinc-100 bg-zinc-50/80 dark:border-white/10 dark:bg-white/[0.03]", `tos-dq-column-${column.id}`)}>''','Kanban column hook'),
('''<div className="border-b border-zinc-100 bg-white px-3 py-2.5 dark:border-white/10 dark:bg-zinc-950"><div className="flex items-center justify-between gap-2">''',
 '''<div className="tos-dq-column-header border-b border-zinc-100 bg-white px-3 py-2.5 dark:border-white/10 dark:bg-zinc-950"><div className="flex items-center justify-between gap-2">''','Kanban header hook'),
('''<Card className="overflow-hidden p-0">''', '''<Card className="tos-dq-capacity overflow-hidden p-0">''','Capacity hook'),
('''<div className="flex flex-wrap justify-between gap-4 px-2 py-2">''', '''<div className="tos-dq-stats-grid">''','Stats grid hook'),
('''<Card className="p-3">''', '''<Card className="tos-dq-command p-3">''','Command hook'),
('''<Card className="h-[calc(100vh-350px)] min-h-[640px] overflow-hidden p-0">''', '''<Card className="tos-dq-board h-[calc(100vh-350px)] min-h-[640px] overflow-hidden p-0">''','Board hook'),
('''<div className="flex items-center justify-between gap-3 border-b border-zinc-100 px-4 py-2.5 dark:border-white/10">''', '''<div className="tos-dq-board-header flex items-center justify-between gap-3 border-b border-zinc-100 px-4 py-2.5 dark:border-white/10">''','Board header hook'),
]

for old,new,label in replacements:
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label} expected once, found {count}")
    s = s.replace(old,new,1)

required = [
    'tos-dq-stat-card','tos-dq-task-card','tos-dq-kanban-column','tos-dq-column-header',
    'tos-dq-capacity','tos-dq-stats-grid','tos-dq-command','tos-dq-board','tos-dq-board-header'
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing marker after patch: {marker}")

p.write_text(s)
PY

printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$V6_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V6 runtime missing/duplicated after append" 18
for marker in tos-dq-stat-card tos-dq-task-card tos-dq-kanban-column tos-dq-column-header tos-dq-capacity tos-dq-stats-grid tos-dq-command tos-dq-board tos-dq-board-header; do
  grep -Fq -- "$marker" "$ROOT/$DESIGN_TARGET" || fail "Design Queue V6 JSX marker missing: $marker" 19
done

# Other Phase04 screens must remain byte-identical.
[ "$(sha256 "$WORKHUB_TARGET")" = "$WORKHUB_SHA256" ] || fail "THRS changed unexpectedly" 20
[ "$(sha256 "$TEAM_TARGET")" = "$TEAM_SHA256" ] || fail "Team Members changed unexpectedly" 21
[ "$(sha256 "$PERF_TARGET")" = "$PERF_SHA256" ] || fail "Team Performance changed unexpectedly" 22

git -C "$ROOT" diff --check -- "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 23
grep -RFlq -- "$V6_RUNTIME" "$DIST/assets" || fail "V6 runtime missing from dist" 24
grep -RFlq -- "tos-dq-stat-card" "$DIST/assets" || fail "V6 structural marker missing from dist" 25

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V6_RUNTIME" "$STAGE/assets" || fail "V6 runtime missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V6; rollback attempted" 28
fi
if ! grep -RFlq -- "$V6_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V6 runtime missing; rolled back" 29
fi
systemctl is-active --quiet nginx || fail "Nginx inactive after deploy" 30

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V6" 31
POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
[ "$POST_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected tracked files changed after V6" 32

[ "$(sha256 "$WORKHUB_TARGET")" = "$WORKHUB_SHA256" ] || fail "THRS changed after build" 33
[ "$(sha256 "$TEAM_TARGET")" = "$TEAM_SHA256" ] || fail "Team Members changed after build" 34
[ "$(sha256 "$PERF_TARGET")" = "$PERF_SHA256" ] || fail "Team Performance changed after build" 35

echo "PHASE04_1_DESIGN_QUEUE_STRUCTURAL_V6=PASS"
echo "SCREEN=Design_Queue_ONLY"
echo "STRUCTURAL_VISUAL_MARKUP_CHANGED=YES"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DESIGN_QUEUE_SHA256=$(sha256 "$DESIGN_TARGET")"
echo "INDEX_CSS_SHA256=$(sha256 "$CSS_TARGET")"
echo "THRS_SHA256=$(sha256 "$WORKHUB_TARGET")"
echo "TEAM_SHA256=$(sha256 "$TEAM_TARGET")"
echo "TEAM_PERFORMANCE_SHA256=$(sha256 "$PERF_TARGET")"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
