#!/usr/bin/env bash
set -u

DOMAIN="tos.tamiyouz.com"
BASE="https://${DOMAIN}"
LIVE="/opt/apps/tamiyouz-front/build"
INDEX="${LIVE}/index.html"

echo "RUNNING=TOS_GLOBAL_PERFORMANCE_BOOT_DIAGNOSTICS_V2"
echo "MODE=READ_ONLY"
echo "DATE_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "--- SYSTEM ---"
uptime || true
free -h || true
df -h / /opt/apps 2>/dev/null || true

echo "--- LIVE BUILD ---"
if [ -f "$INDEX" ]; then
  echo "LIVE_INDEX=YES"
  stat -c 'INDEX_BYTES=%s INDEX_MTIME=%y' "$INDEX" 2>/dev/null || true
  JS_ASSETS=$(grep -oE '/?assets/[^"'"' ]+\.js' "$INDEX" | sed 's#^/##' | sort -u || true)
  CSS_ASSETS=$(grep -oE '/?assets/[^"'"' ]+\.css' "$INDEX" | sed 's#^/##' | sort -u || true)
  echo "INDEX_JS_ASSETS=$(printf '%s\n' "$JS_ASSETS" | sed '/^$/d' | wc -l)"
  echo "INDEX_CSS_ASSETS=$(printf '%s\n' "$CSS_ASSETS" | sed '/^$/d' | wc -l)"
  echo "TOP_LIVE_ASSETS_BY_SIZE:"
  find "$LIVE/assets" -maxdepth 1 -type f -printf '%s %f\n' 2>/dev/null | sort -nr | head -25 || true
else
  echo "LIVE_INDEX=NO"
  JS_ASSETS=""
  CSS_ASSETS=""
fi

curl_timing() {
  local label="$1" url="$2"
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
  local label="$1" url="$2"
  echo "HEADERS_BEGIN=${label}"
  curl -k -L -sS -D - -o /dev/null --connect-timeout 10 --max-time 30 "$url" \
    | grep -iE '^(HTTP/|server:|content-type:|content-length:|content-encoding:|cache-control:|etag:|last-modified:|age:|vary:|x-cache:|cf-cache-status:)' || true
  echo "HEADERS_END=${label}"
}

echo "--- PUBLIC DOCUMENT TIMINGS ---"
curl_timing ROOT "${BASE}/"
curl_timing CHAT "${BASE}/chat"
header_probe ROOT "${BASE}/"

if [ -n "${JS_ASSETS:-}" ]; then
  FIRST_JS=$(printf '%s\n' "$JS_ASSETS" | sed '/^$/d' | head -1)
  [ -n "$FIRST_JS" ] && curl_timing ENTRY_JS "${BASE}/${FIRST_JS}"
  [ -n "$FIRST_JS" ] && header_probe ENTRY_JS "${BASE}/${FIRST_JS}"
fi
if [ -n "${CSS_ASSETS:-}" ]; then
  FIRST_CSS=$(printf '%s\n' "$CSS_ASSETS" | sed '/^$/d' | head -1)
  [ -n "$FIRST_CSS" ] && curl_timing ENTRY_CSS "${BASE}/${FIRST_CSS}"
  [ -n "$FIRST_CSS" ] && header_probe ENTRY_CSS "${BASE}/${FIRST_CSS}"
fi

echo "--- LOOPBACK NGINX TIMINGS ---"
for path in / /chat; do
  echo "LOOPBACK_PATH=${path}"
  curl -k -sS -o /dev/null --resolve "${DOMAIN}:443:127.0.0.1" \
    --connect-timeout 5 --max-time 30 \
    -w 'HTTP=%{http_code} CONNECT=%{time_connect} TLS=%{time_appconnect} TTFB=%{time_starttransfer} TOTAL=%{time_total} SIZE=%{size_download}\n' \
    "${BASE}${path}" || echo "LOOPBACK_HTTPS_FAILED=$?"
done

echo "--- API EDGE TIMINGS (NO AUTH, READ ONLY) ---"
for path in /api/health /api/me; do
  echo "API_PATH=${path}"
  curl -k -sS -o /dev/null --connect-timeout 5 --max-time 30 \
    -w 'HTTP=%{http_code} DNS=%{time_namelookup} CONNECT=%{time_connect} TLS=%{time_appconnect} TTFB=%{time_starttransfer} TOTAL=%{time_total} SIZE=%{size_download}\n' \
    "${BASE}${path}" || echo "API_PROBE_FAILED=$?"
done

echo "--- NGINX EFFECTIVE CONFIG SUMMARY ---"
if command -v nginx >/dev/null 2>&1; then
  nginx -T 2>&1 | grep -iE 'server_name|root |try_files|gzip|brotli|expires|cache-control|proxy_pass|keepalive|http2' | head -220 || true
else
  echo "NGINX_COMMAND=NOT_FOUND"
fi

echo "--- PROCESS STATUS ---"
if command -v pm2 >/dev/null 2>&1; then
  pm2 list || true
else
  echo "PM2=NOT_FOUND"
fi

echo "--- RECENT NGINX ACCESS SAMPLE ---"
for log in /var/log/nginx/access.log /var/log/nginx/tos.access.log /var/log/nginx/tos.tamiyouz.com.access.log; do
  if [ -r "$log" ]; then
    echo "ACCESS_LOG=${log}"
    tail -n 80 "$log" | tail -n 40 || true
  fi
done

echo "PASS/FAIL=PASS"
echo "CHANGES_MADE=NO"
echo "STATUS=DIAGNOSTICS_READY"
