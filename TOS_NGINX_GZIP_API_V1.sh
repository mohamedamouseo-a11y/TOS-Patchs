#!/usr/bin/env bash
set -euo pipefail

CONF=/etc/nginx/conf.d/tos-gzip.conf
TMP=$(mktemp)
BAK="${CONF}.bak.$(date +%s)"

cat > "$TMP" <<'EOF'
gzip on;
gzip_proxied any;
gzip_comp_level 6;
gzip_min_length 1024;
gzip_vary on;
gzip_types application/json text/plain text/css application/javascript application/xml image/svg+xml;
EOF

if [ -f "$CONF" ]; then
  cp -a "$CONF" "$BAK"
fi

install -m 0644 "$TMP" "$CONF"
rm -f "$TMP"

if ! nginx -t; then
  if [ -f "$BAK" ]; then
    cp -a "$BAK" "$CONF"
  else
    rm -f "$CONF"
  fi
  nginx -t || true
  echo "NGINX=FAIL"
  echo "ERROR=nginx test failed; rolled back"
  exit 1
fi

systemctl reload nginx

echo "NGINX=PASS"
echo "CONFIG=$CONF"
echo "ERROR=none"
