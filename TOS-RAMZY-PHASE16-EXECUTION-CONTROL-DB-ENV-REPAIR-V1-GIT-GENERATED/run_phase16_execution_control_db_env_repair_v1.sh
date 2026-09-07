#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
BACKEND_ROOT="$TOS_ROOT/backend"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
VERIFIER="$PATCH_DIR/01_execution_control_db_acceptance.mjs"
BASELINE="f6b6f60b57d702e62ed488eca7265bfcde0ca601"
DOMAIN="https://tos.tamiyouz.com"

fail() {
  echo "PASS/FAIL=FAIL"
  echo "RAMZY_EXECUTION_CONTROL_DB_ENV_REPAIR_V1=FAIL"
  echo "REASON=$1"
  exit 1
}

public_code() {
  local method="${1:-GET}"
  local path="${2:-/}"
  if [[ "$method" == "PATCH" ]]; then
    curl -ksS -X PATCH -H 'Content-Type: application/json' -d '{}' -o /dev/null -w '%{http_code}' "$DOMAIN$path" || true
  else
    curl -ksS -o /dev/null -w '%{http_code}' "$DOMAIN$path" || true
  fi
}

echo "RUNNING=RAMZY_PHASE16_EXECUTION_CONTROL_DB_ENV_REPAIR_V1"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD" || fail "BASELINE_NOT_ANCESTOR"

[[ -f "$VERIFIER" ]] || fail "DB_VERIFIER_NOT_FOUND"
grep -q 'RAMZY_EXECUTION_CONTROL_V1' backend/src/agency-operator/services/ramzyExecutionControl.service.js || fail "EXECUTION_CONTROL_SOURCE_NOT_APPLIED"
grep -q 'key: "ramzy.execute_actions"' backend/src/services/permissions.service.js || fail "EXECUTION_PERMISSION_SOURCE_NOT_APPLIED"
grep -q 'assertRamzyActionExecutionAllowed(req.user, { settings })' backend/src/routes/agent.routes.js || fail "ROUTE_EXECUTION_GATE_MISSING"
grep -q 'assertRamzyActionExecutionAllowed(user, { settings })' backend/src/agency-operator/services/taskCommands.service.js || fail "TASK_EXECUTION_GATE_MISSING"
grep -q 'delete input.readOnlyMode' backend/src/routes/agent.routes.js || fail "SUPER_ADMIN_EMERGENCY_LOCK_BOUNDARY_MISSING"
grep -q 'status.executionControl' frontend/src/components/RamzyAssistant.jsx || fail "RAMZY_EXECUTION_STATUS_UI_MISSING"
grep -q 'تشغيل إجراءات رمزي' frontend/src/pages/PermissionsPage.jsx || fail "PERMISSIONS_DASHBOARD_LABEL_MISSING"
grep -q 'actionExecutionFromVoice: false' backend/src/agency-operator/services/ramzyVoice.service.js || fail "VOICE_PERMISSION_GUARD_LOST"
echo "SOURCE_CONTRACTS=PASS"

SOURCE_STATE_BEFORE="$(git status --short)"
SOURCE_DIFF_BEFORE="$(git diff --binary | sha256sum | awk '{print $1}')"

node --test backend/src/agency-operator/tests/ramzyExecutionControlPhase16.test.js
echo "FOCUSED_EXECUTION_CONTROL_TEST=PASS (6/6 expected)"

DB_LOG="$(mktemp)"
DB_PM2_LOG="$(mktemp)"
trap 'rm -f "$DB_LOG" "$DB_PM2_LOG"' EXIT

# First use the backend working directory so dotenv/config resolves backend/.env exactly
# as the production backend does when its PM2 cwd points there.
if (cd "$BACKEND_ROOT" && TOS_BACKEND_ROOT="$BACKEND_ROOT" node "$VERIFIER") >"$DB_LOG" 2>&1; then
  cat "$DB_LOG"
  echo "DB_ENV_SOURCE=BACKEND_CWD_DOTENV_OR_SHELL"
else
  echo "BACKEND_CWD_DB_ENV=UNAVAILABLE_TRYING_PM2_RUNTIME_ENV"
  # Fallback: launch the verifier with the existing PM2 process environment without
  # printing or materializing any secret values.
  if python3 - "$BACKEND_ROOT" "$VERIFIER" >"$DB_PM2_LOG" 2>&1 <<'PY'
import json, os, subprocess, sys
backend_root, verifier = sys.argv[1], sys.argv[2]
try:
    raw = subprocess.check_output(["pm2", "jlist"], text=True)
    processes = json.loads(raw)
except Exception as exc:
    print(f"PM2_ENV_DISCOVERY_ERROR={type(exc).__name__}")
    raise SystemExit(2)

proc = next((p for p in processes if p.get("name") in ("tamiyouz-system", "tamiyouz-backend")), None)
if not proc:
    print("PM2_BACKEND_PROCESS_NOT_FOUND")
    raise SystemExit(3)

pm2_env = proc.get("pm2_env") or {}
env = os.environ.copy()
for container_key in ("env", "env_production"):
    values = pm2_env.get(container_key)
    if isinstance(values, dict):
        for key, value in values.items():
            if value is not None:
                env[str(key)] = str(value)
for key, value in pm2_env.items():
    if isinstance(key, str) and key.isupper() and value is not None and not isinstance(value, (dict, list)):
        env[key] = str(value)

env["TOS_BACKEND_ROOT"] = backend_root
result = subprocess.run(["node", verifier], cwd=backend_root, env=env)
raise SystemExit(result.returncode)
PY
  then
    cat "$DB_PM2_LOG"
    echo "DB_ENV_SOURCE=PM2_RUNTIME_ENV"
  else
    echo "--- backend cwd DB verification ---"
    cat "$DB_LOG"
    echo "--- PM2 runtime DB verification ---"
    cat "$DB_PM2_LOG"
    fail "DATABASE_ENVIRONMENT_UNAVAILABLE_OR_DB_VERIFICATION_FAILED"
  fi
fi

echo "DATABASE_EXECUTION_CONTROL_STATE=PASS"

# Rebuild/deploy because the original V1 stopped before frontend/backend deployment.
npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"
rm -rf /opt/apps/tamiyouz-front/build/*
cp -a frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend
sleep 3
pm2 describe tamiyouz-frontend | grep -qi online || fail "FRONTEND_PM2_NOT_ONLINE"
echo "FRONTEND_DEPLOY=PASS"

BACKEND_PM2=""
if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-system"
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-backend"
else
  fail "BACKEND_PM2_NOT_FOUND"
fi
pm2 reload "$BACKEND_PM2"
echo "BACKEND_RELOAD=PASS"

READY=0
for attempt in $(seq 1 20); do
  code="$(curl -ksS -o /dev/null -w '%{http_code}' http://127.0.0.1:5006/api/agent/settings || true)"
  if [[ "$code" == "401" ]]; then
    READY=1
    break
  fi
  sleep 1
done
[[ "$READY" == "1" ]] || fail "BACKEND_AGENT_ROUTE_NOT_READY"
echo "BACKEND_AGENT_ROUTE_READY=PASS"

for url in /health /dashboard /team-performance /tasks; do
  code="$(curl -ksS -o /dev/null -w '%{http_code}' "$DOMAIN$url" || true)"
  echo "HTTP_${url//\//_}=$code"
  [[ "$code" == "200" ]] || fail "HTTP_SMOKE_FAILED:${url}:${code}"
done
echo "HTTP_SMOKE=PASS"

GET_UNAUTH="$(public_code GET /api/agent/settings)"
PATCH_NO_CSRF="$(public_code PATCH /api/agent/settings)"
echo "RAMZY_SETTINGS_GET_UNAUTH_HTTP=$GET_UNAUTH"
echo "RAMZY_SETTINGS_PATCH_NO_CSRF_HTTP=$PATCH_NO_CSRF"
[[ "$GET_UNAUTH" == "401" ]] || fail "SETTINGS_GET_AUTH_BOUNDARY_FAILED:$GET_UNAUTH"
[[ "$PATCH_NO_CSRF" == "403" ]] || fail "SETTINGS_PATCH_CSRF_BOUNDARY_FAILED:$PATCH_NO_CSRF"
echo "AUTH_CSRF_BOUNDARY=PASS"

SOURCE_STATE_AFTER="$(git status --short)"
SOURCE_DIFF_AFTER="$(git diff --binary | sha256sum | awk '{print $1}')"
[[ "$SOURCE_STATE_BEFORE" == "$SOURCE_STATE_AFTER" ]] || fail "SOURCE_WORKTREE_CHANGED_DURING_REPAIR"
[[ "$SOURCE_DIFF_BEFORE" == "$SOURCE_DIFF_AFTER" ]] || fail "SOURCE_DIFF_CHANGED_DURING_REPAIR"

echo "SOURCE_CHANGES_THIS_REPAIR=NO"
echo "RAMZY_EXECUTION_PERMISSION=ramzy.execute_actions"
echo "ADMIN_DEFAULT_EXECUTION=ENABLED"
echo "EMERGENCY_LOCK=SUPER_ADMIN_ONLY"
echo "TOS_RBAC_RECHECK_AT_EXECUTION=YES"
echo "VOICE_INDEPENDENT_PERMISSION=NO"
echo "NO_COMMIT_OR_PUSH=YES"
echo "RAMZY_EXECUTION_CONTROL_DB_ENV_REPAIR_V1=PASS"
echo "PASS/FAIL=PASS"
echo "--- git status --short ---"
git status --short
