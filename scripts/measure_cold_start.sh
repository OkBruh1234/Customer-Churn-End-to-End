#!/usr/bin/env bash
#
# Measure the backend's cold-start and warm latency.
#
#   ./scripts/measure_cold_start.sh https://your-backend.onrender.com
#
# To measure a genuine cold start, leave the service idle for >15 minutes first
# (or hit "Suspend"/"Resume" in the Render dashboard). Otherwise this reports
# warm numbers, which is also useful as a baseline.

set -uo pipefail

BASE_URL="${1:-}"
if [ -z "$BASE_URL" ]; then
  echo "usage: $0 <backend-base-url>" >&2
  exit 1
fi
BASE_URL="${BASE_URL%/}"

fmt='  dns=%{time_namelookup}s  tcp=%{time_connect}s  tls=%{time_appconnect}s  ttfb=%{time_starttransfer}s  total=%{time_total}s  http=%{http_code}\n'

echo "=== Cold hit: GET $BASE_URL/health ==="
BODY="$(mktemp)"
START=$(date +%s)
curl --silent --show-error --location \
  --max-time 300 --connect-timeout 20 \
  --write-out "$fmt" --output "$BODY" \
  "$BASE_URL/health"
END=$(date +%s)
echo "  wall clock: $((END - START))s"
echo "  body: $(cat "$BODY")"
echo

# model_ready distinguishes "instance booted" from "model finished warming".
# Warm-up runs on a background thread, so the first 200 can legitimately
# arrive before the model is ready.
if grep -q '"model_ready":false' "$BODY"; then
  echo "=== Waiting for background warm-up to finish ==="
  for _ in $(seq 1 60); do
    sleep 1
    if curl --silent --max-time 20 "$BASE_URL/health" | grep -q '"model_ready":true'; then
      echo "  model_ready after $(( $(date +%s) - START ))s total"
      break
    fi
  done
  echo
fi

echo "=== Warm hits: GET $BASE_URL/health ==="
for i in 1 2 3; do
  printf '  hit%s' "$i"
  curl --silent --show-error --max-time 60 \
    --write-out "$fmt" --output /dev/null "$BASE_URL/health"
done
echo

echo "=== End-to-end prediction (register + predict) ==="
USER_JSON="$(curl --silent --max-time 60 -X POST "$BASE_URL/users/register" \
  -H 'Content-Type: application/json' -d '{"name":"Latency Probe"}')"
echo "  register -> $USER_JSON"

USER_ID="$(printf '%s' "$USER_JSON" | sed -n 's/.*"user_id":"\([^"]*\)".*/\1/p')"
if [ -z "$USER_ID" ]; then
  echo "  could not parse user_id; skipping predict" >&2
  exit 1
fi

read -r -d '' PAYLOAD <<EOF
{"user_id":"$USER_ID","customer":{"gender":"Male","senior_citizen":0,"partner":"Yes",
"dependents":"No","phone_service":"Yes","multiple_lines":"No","internet_service":"Fiber optic",
"online_security":"No","online_backup":"No","device_protection":"No","tech_support":"No",
"streaming_tv":"No","streaming_movies":"No","contract":"Month-to-month","paperless_billing":"Yes",
"payment_method":"Electronic check","monthly_charges":70.0,"tenure":12}}
EOF

printf '  predict'
curl --silent --show-error --max-time 60 -X POST "$BASE_URL/predict" \
  -H 'Content-Type: application/json' -d "$PAYLOAD" \
  --write-out "$fmt" --output "$BODY"
echo "  server-side processing_time_ms: $(sed -n 's/.*"processing_time_ms":\([0-9.]*\).*/\1/p' "$BODY")"

rm -f "$BODY"
