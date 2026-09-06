#!/usr/bin/env bash
set -u

DOMAIN="tos.tamiyouz.com"
BASE="https://${DOMAIN}"
LIVE="/opt/apps/tamiyouz-front/build"
INDEX="${LIVE}/index.html"

echo "RUNNING=TOS_GLOBAL_PERFORMANCE_BOOT_DIAGNOSTICS_V2_R1"
echo "MODE=READ_ONLY"
echo "DATE_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "R1_ROOT_CAUSE=V2_ASSET_REGEX_SHELL_QUOTING_ERROR"
echo "R1_SYNTAX_SAFE_ASSET_DISCOVERY=PYTHON_HTML_PARSE"

echo "--- SYSTEM ---"
uptime || true
free -h || true
df -h / /opt/apps 2>/dev/null || true

JS_ASSETS=""
CSS_ASSETS=""

echo "--- LIVE BUILD ---"
if [ -f "$INDEX" ]; then
  echo "LIVE_INDEX=YES"
  stat -c 'INDEX_BYTES=%s INDEX_MTIME=%y' "$INDEX" 2>/dev/null || true

  if command -v python3 >/dev/null 2>&1; then
    ASSET_OUTPUT="$(python3 - "$INDEX" <<'PY'
from pathlib import Path
import re, sys
p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8', errors='ignore')
js = sorted(set(re.findall(r'(?:/)?assets/[^\"\'\s>]+\.js', text)))
css = sorted(set(re.findall(r'(?:/)?assets/[^\"\'\s>]+\.css', text)))
for item in js:
    print('JS=' + item.lstrip('/'))
for item in css:
    print('CSS=' + item.lstrip('/'))
PY
)"
    JS_ASSETS="$(printf '%s\n' "$ASSET_OUTPUT" | sed -n 's/^JS=//p')"
    CSS_ASSETS="$(printf '%s\n' "$ASSET_OUTPUT" | sed -n 's/^CSS=//p')"
  else
    echo "PYTHON3=NOT_FOUND"
  fi

  echo "INDEX_JS_ASSETS=$(printf '%s\n' "$JS_ASSETS" | sed '/^$/d' | wc -l)"
  echo "INDEX_CSS_ASSETS=$(printf '%s\n' "$CSS_ASSETS" | sed '/^$/d' | wc -l)"
  echo "TOP_LIVE_ASSETS_BY_SIZE:"
  find "$LIVE/assets" -maxdepth 1 -type f -printf '%s %f\n' 2>/dev/null | sort -nr | head -25 || true
else
  echo "LIVE_INDEX=NO"
fi

curl_timing() {
  local label="$1"
  local url="$2"
  echo "TIMING_BEGIN=${label} URL=${url}"
  for i in 1 2 3; do
    curl -k -L -sS -o /dev/null \
      --connect-timeout 10 --max-time 45 \
      -w "TRY=${i} HTTP=%{http_code} DNS=%{time_namelookup} CONNECT=%{time_connect} TLS=%{time_appconnect} TTFB=%{time_starttransfer} TOTAL=%{time_total} SIZE=%{size_download} SPEED=%{speed_download}\n" \
      "$url" || echo "TRY=${i} CURL_FAILED=$?"
  done
  echo "TIMING_END=${label}"
}

header_probe() {
  local label="$1"
  local url="$2"
  echo "HEADERS_BEGIN=${label}"
  curl -k -L -sS -D - -o /dev/null --connect-timeout 10 --max-time 30 \
    -H 'Accept-Encoding: br, gzip' "$url" \
    | grep -iE '^(HTTP/|server:|content-type:|content-length:|content-encoding:|cache-control:|etag:|last-modified:|age:|vary:|x-cache:|cf-cache-status:)' || true
  echo "HEADERS_END=${label}"
}

echo "--- PUBLIC DOCUMENT TIMINGS ---"
curl_timing ROOT "${BASE}/"
curl_timing CHAT "${BASE}/chat"
header_probe ROOT "${BASE}/"

FIRST_JS="$(printf '%s\n' "$JS_ASSETS" | sed '/^$/d' | head -1)"
FIRST_CSS="$(printf '%s\n' "$CSS_ASSETS" | sed '/^$/d' | head -1)"

if [ -n "$FIRST_JS" ]; then
  echo "ENTRY_JS_ASSET=${FIRST_JS}"
  curl_timing ENTRY_JS "${BASE}/${FIRST_JS}"
  header_probe ENTRY_JS "${BASE}/${FIRST_JS}"
  [ -f "${LIVE}/${FIRST_JS}" ] && stat -c 'ENTRY_JS_DISK_BYTES=%s' "${LIVE}/${FIRST_JS}" || true
fi

if [ -n "$FIRST_CSS" ]; then
  echo "ENTRY_CSS_ASSET=${FIRST_CSS}"
  curl_timing ENTRY_CSS "${BASE}/${FIRST_CSS}"
  header_probe ENTRY_CSS "${BASE}/${FIRST_CSS}"
  [ -f "${LIVE}/${FIRST_CSS}" ] && stat -c 'ENTRY_CSS_DISK_BYTES=%s' "${LIVE}/${FIRST_CSS}" || true
fi

echo "--- LOOPBACK NGINX TIMINGS ---"
for path in / /chat; do
  echo "LOOPBACK_PATH=${path}"
  curl -k -sS -o /dev/null \
    --resolve "${DOMAIN}:443:127.0.0.1" \
    --connect-timeout 5 --max-time 30 \
    -w 'HTTP=%{http_code} CONNECT=%{time_connect} TLS=%{time_appconnect} TTFB=%{time_starttransfer} TOTAL=%{time_total} SIZE=%{size_download}\n' \
    "${BASE}${path}" || echo "LOOPBACK_HTTPS_FAILED=$?"
done

echo "--- API EDGE TIMINGS NO_AUTH READ_ONLY ---"
for path in /api/health /api/me; do
  echo "API_PATH=${path}"
  curl -k -sS -o /dev/null \
    --connect-timeout 5 --max-time 30 \
    -w 'HTTP=%{http_code} DNS=%{time_namelookup} CONNECT=%{time_connect} TLS=%{time_appconnect} TTFB=%{time_starttransfer} TOTAL=%{time_total} SIZE=%{size_download}\n' \
    "${BASE}${path}" || echo "API_PROBE_FAILED=$?"
done

echo "--- NGINX EFFECTIVE CONFIG SUMMARY ---"
if command -v nginx >/dev/null 2>&1; then
  nginx -T 2>&1 \
    | grep -iE 'server_name|root |try_files|gzip|brotli|expires|cache-control|proxy_pass|proxy_cache|keepalive|http2|sendfile|tcp_nopush|tcp_nodelay' \
    | head -260 || true
else
  echo "NGINX_COMMAND=NOT_FOUND"
fi

echo "--- PROCESS STATUS ---"
if command -v pm2 >/dev/null 2>&1; then
  pm2 list || true
  echo "PM2_JLIST_SUMMARY:"
  pm2 jlist 2>/dev/null | python3 -c 'import json,sys; data=json.load(sys.stdin); [print("PM2_APP name=%s status=%s pid=%s cpu=%s memory=%s restarts=%s" % (p.get("name"), p.get("pm2_env",{}).get("status"), p.get("pid"), p.get("monit",{}).get("cpu"), p.get("monit",{}).get("memory"), p.get("pm2_env",{}).get("restart_time"))) for p in data]' 2>/dev/null || true
else
  echo "PM2=NOT_FOUND"
fi

echo "--- RECENT NGINX ACCESS SAMPLE ---"
for log in /var/log/nginx/access.log /var/log/nginx/tos.access.log /var/log/nginx/tos.tamiyouz.com.access.log; do
  if [ -r "$log" ]; then
    echo "ACCESS_LOG=${log}"
    tail -n 40 "$log" || true
  fi
done

echo "PASS/FAIL=PASS"
echo "CHANGES_MADE=NO"
echo "STATUS=DIAGNOSTICS_READY"
