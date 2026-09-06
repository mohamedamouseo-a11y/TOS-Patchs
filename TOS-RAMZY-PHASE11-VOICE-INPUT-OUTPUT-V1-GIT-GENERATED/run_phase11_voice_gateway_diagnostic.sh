#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
DOMAIN="https://tos.tamiyouz.com"
LOCAL="http://127.0.0.1:4000"

echo "RUNNING=RAMZY_PHASE11_VOICE_GATEWAY_DIAGNOSTIC"
cd "$TOS_ROOT"
echo "CURRENT_TOS_HEAD=$(git rev-parse HEAD)"

echo "--- PHASE11 FILE MARKERS ---"
grep -q 'RAMZY_VOICE_IO_V1' backend/src/agency-operator/services/ramzyVoice.service.js && echo "VOICE_SERVICE=PASS" || echo "VOICE_SERVICE=FAIL"
grep -q 'router.get("/voice/status"' backend/src/routes/agent.routes.js && echo "VOICE_ROUTE_STATUS=PASS" || echo "VOICE_ROUTE_STATUS=FAIL"
grep -q 'router.post("/voice/synthesize"' backend/src/routes/agent.routes.js && echo "VOICE_ROUTE_TTS=PASS" || echo "VOICE_ROUTE_TTS=FAIL"

BACKEND_PM2=""
if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-system"
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-backend"
fi

echo "BACKEND_PM2=${BACKEND_PM2:-NOT_FOUND}"
if [[ -n "$BACKEND_PM2" ]]; then
  pm2 describe "$BACKEND_PM2" | sed -n '1,90p' || true
fi

echo "--- LOCAL AUTH BOUNDARY ---"
for path in "/api/agent/status" "/api/agent/voice/status"; do
  code="$(curl -sS -o /tmp/phase11_local_body -w '%{http_code}' "$LOCAL$path" || true)"
  echo "LOCAL_${path//\//_}_HTTP=$code"
  head -c 300 /tmp/phase11_local_body 2>/dev/null | tr '\n' ' ' || true
  echo
 done

code="$(curl -sS -o /tmp/phase11_local_tts_body -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data '{"text":"hello"}' "$LOCAL/api/agent/voice/synthesize" || true)"
echo "LOCAL_VOICE_TTS_HTTP=$code"
head -c 300 /tmp/phase11_local_tts_body 2>/dev/null | tr '\n' ' ' || true
echo

echo "--- PUBLIC AUTH BOUNDARY ---"
for path in "/api/agent/status" "/api/agent/voice/status"; do
  code="$(curl -ksS -o /tmp/phase11_public_body -w '%{http_code}' "$DOMAIN$path" || true)"
  echo "PUBLIC_${path//\//_}_HTTP=$code"
  head -c 300 /tmp/phase11_public_body 2>/dev/null | tr '\n' ' ' || true
  echo
 done

code="$(curl -ksS -o /tmp/phase11_public_tts_body -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data '{"text":"hello"}' "$DOMAIN/api/agent/voice/synthesize" || true)"
echo "PUBLIC_VOICE_TTS_HTTP=$code"
head -c 300 /tmp/phase11_public_tts_body 2>/dev/null | tr '\n' ' ' || true
echo

echo "--- BACKEND PORT ---"
ss -ltnp 2>/dev/null | grep -E '(:4000\b|node)' | head -20 || true

echo "--- ROUTE IMPORT CHECK ---"
(
  cd backend
  node -e "import('./src/routes/agent.routes.js').then(()=>console.log('AGENT_ROUTE_IMPORT=PASS')).catch(e=>{console.error(e);process.exit(1)})"
) || echo "AGENT_ROUTE_IMPORT=FAIL"

echo "--- PM2 RECENT LOGS ---"
if [[ -n "$BACKEND_PM2" ]]; then
  pm2 logs "$BACKEND_PM2" --lines 120 --nostream 2>&1 | tail -160 || true
fi

echo "--- NGINX VOICE/AGENT MATCHES ---"
if command -v nginx >/dev/null 2>&1; then
  nginx -T 2>&1 | grep -nE 'location|proxy_pass|agent|voice|api/' | tail -180 || true
else
  echo "NGINX_NOT_AVAILABLE"
fi

echo "NO_SOURCE_CHANGES=YES"
echo "NO_COMMIT_OR_PUSH=YES"
echo "DIAGNOSTIC_COMPLETE=YES"
git status --short
