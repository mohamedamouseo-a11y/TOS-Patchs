#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
BASELINE="7e98d03108b80c8d881fcf50e62217db42f3027f"
GENERATOR="$PATCH_DIR/01_phase11_voice_input_output.py"
TEST_FIX="$PATCH_DIR/02_phase11_test_path_fix.py"

TARGET_FILES=(
  "backend/src/routes/agent.routes.js"
  "backend/src/agency-operator/services/ramzyVoice.service.js"
  "backend/src/agency-operator/tests/ramzyVoicePhase11.static.test.js"
  "frontend/src/lib/api.js"
  "frontend/src/components/RamzyAssistant.jsx"
  "frontend/src/components/ramzyVoicePhase11.css"
)

fail() {
  echo "PHASE11_VOICE_IO=FAIL"
  echo "REASON=$1"
  exit 1
}

is_target() {
  local path="$1"
  for file in "${TARGET_FILES[@]}"; do
    [[ "$path" == "$file" ]] && return 0
  done
  return 1
}

cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
if ! git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD"; then
  fail "PHASE11_BASELINE_NOT_ANCESTOR"
fi

PRE_STATUS="$(git status --short)"
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  path="${line:3}"
  if is_target "$path"; then
    fail "PHASE11_TARGET_FILE_ALREADY_DIRTY:$path"
  fi
done <<< "$PRE_STATUS"

echo "PRE_STATE=TARGET_FILES_CLEAN"
[[ -f "$GENERATOR" ]] || fail "GENERATOR_NOT_FOUND"
[[ -f "$TEST_FIX" ]] || fail "TEST_FIX_NOT_FOUND"
python3 "$GENERATOR"
python3 "$TEST_FIX"
echo "PATCH_APPLY=PASS"

# Contract checks before build/reload.
grep -q 'RAMZY_VOICE_IO_V1' backend/src/agency-operator/services/ramzyVoice.service.js || fail "VOICE_SERVICE_MARKER_MISSING"
grep -q 'router.get("/voice/status"' backend/src/routes/agent.routes.js || fail "VOICE_STATUS_ROUTE_MISSING"
grep -q 'router.post("/voice/transcribe"' backend/src/routes/agent.routes.js || fail "VOICE_TRANSCRIBE_ROUTE_MISSING"
grep -q 'router.post("/voice/synthesize"' backend/src/routes/agent.routes.js || fail "VOICE_SYNTHESIZE_ROUTE_MISSING"
grep -q 'RAMZY_VOICE_MODE_STORAGE_PREFIX' frontend/src/components/RamzyAssistant.jsx || fail "VOICE_MODE_UI_MISSING"
grep -q 'voice-conversation' frontend/src/components/RamzyAssistant.jsx || fail "VOICE_CONVERSATION_MODE_MISSING"
grep -q 'api.agent.transcribeVoice' frontend/src/components/RamzyAssistant.jsx || fail "API_TRANSCRIBE_UI_MISSING"
grep -q 'api.agent.synthesizeVoice' frontend/src/components/RamzyAssistant.jsx || fail "API_TTS_UI_MISSING"
grep -q 'window.speechSynthesis' frontend/src/components/RamzyAssistant.jsx || fail "BROWSER_TTS_FALLBACK_MISSING"
grep -q 'SpeechRecognition' frontend/src/components/RamzyAssistant.jsx || fail "BROWSER_STT_FALLBACK_MISSING"
grep -q 'if (listening) { stopVoiceInput(); return; }' frontend/src/components/RamzyAssistant.jsx || fail "VOICE_NO_AUTOSEND_GUARD_MISSING"
echo "CONTRACT_CHECKS=PASS"

npm --prefix backend run test:ramzy
echo "BACKEND_TESTS=PASS"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check -- "${TARGET_FILES[@]}"
echo "GIT_DIFF_CHECK=PASS"

POST_STATUS="$(git status --short)"
filter_non_targets() {
  local status="$1"
  printf '%s\n' "$status" | while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local path="${line:3}"
    if ! is_target "$path"; then printf '%s\n' "$line"; fi
  done | sort
}
if [[ "$(filter_non_targets "$PRE_STATUS")" != "$(filter_non_targets "$POST_STATUS")" ]]; then
  fail "UNRELATED_WORKTREE_CHANGED"
fi
for file in "${TARGET_FILES[@]}"; do
  if ! printf '%s\n' "$POST_STATUS" | grep -Fq " $file"; then
    fail "EXPECTED_PHASE11_FILE_NOT_CHANGED:$file"
  fi
done
echo "EXPECTED_CHANGED_FILES=PASS"
echo "UNRELATED_WORK_PRESERVED=YES"

# Deploy frontend using the existing production path.
rm -rf /opt/apps/tamiyouz-front/build/*
cp -a /var/www/TOS/frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend
sleep 1
pm2 describe tamiyouz-frontend | grep -qi 'online' || fail "FRONTEND_PM2_NOT_ONLINE"
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
sleep 2
pm2 describe "$BACKEND_PM2" | grep -qi 'online' || fail "BACKEND_PM2_NOT_ONLINE"
echo "BACKEND_RELOAD=PASS"

for url in "/health" "/dashboard" "/team-performance" "/tasks"; do
  code="$(curl -ksS -o /dev/null -w '%{http_code}' "https://tos.tamiyouz.com${url}")"
  echo "HTTP_${url//\//_}=$code"
  [[ "$code" == "200" ]] || fail "HTTP_SMOKE_FAILED:${url}:${code}"
done

VOICE_STATUS_AUTH="$(curl -ksS -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/api/agent/voice/status)"
VOICE_TTS_AUTH="$(curl -ksS -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data '{"text":"hello"}' https://tos.tamiyouz.com/api/agent/voice/synthesize)"
echo "VOICE_STATUS_UNAUTH_HTTP=$VOICE_STATUS_AUTH"
echo "VOICE_TTS_UNAUTH_HTTP=$VOICE_TTS_AUTH"
[[ "$VOICE_STATUS_AUTH" == "401" ]] || fail "VOICE_STATUS_AUTH_BOUNDARY_FAILED:$VOICE_STATUS_AUTH"
[[ "$VOICE_TTS_AUTH" == "401" ]] || fail "VOICE_TTS_AUTH_BOUNDARY_FAILED:$VOICE_TTS_AUTH"
echo "AUTH_BOUNDARY_E2E=PASS"

if ! diff -qr /var/www/TOS/frontend/dist /opt/apps/tamiyouz-front/build >/dev/null; then
  fail "DEPLOYED_DIST_MISMATCH"
fi
echo "DEPLOYED_DIST_MATCH=PASS"

echo "HTTP_SMOKE=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE11_VOICE_IO=PASS"
echo "--- git status --short ---"
git status --short
