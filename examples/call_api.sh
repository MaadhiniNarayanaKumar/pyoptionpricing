#!/usr/bin/env bash
# Call the running API with the JSON files in examples/requests, no Swagger needed.
#
#   1. Start the backend:  uvicorn backend.main:app --reload
#   2. In another terminal, from the project root:
#        ./examples/call_api.sh                 # run every endpoint
#        ./examples/call_api.sh price           # run one endpoint
#        API_URL=http://localhost:9000 ./examples/call_api.sh
#
# Each request body lives in examples/requests/<name>.json. Edit those files to
# try other inputs, or point curl at your own file:
#   curl -X POST "$API_URL/price" -H "Content-Type: application/json" -d @my.json

set -u

API_URL="${API_URL:-http://localhost:8000}"
DIR="$(cd "$(dirname "$0")/requests" && pwd)"

pretty() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -m json.tool 2>/dev/null || cat
  else
    cat
  fi
}

get() {
  echo "=== GET /$1 ==="
  curl -sS "$API_URL/$1" | pretty
  echo
}

post() {
  local name="$1" file="${2:-$1}"
  echo "=== POST /$name  ($file.json) ==="
  local out status body
  out=$(curl -sS -w "\n%{http_code}" -X POST "$API_URL/$name" \
    -H "Content-Type: application/json" \
    -d @"$DIR/$file.json")
  status="${out##*$'\n'}"
  body="${out%$'\n'*}"
  echo "$body" | pretty
  echo "HTTP $status"
  echo
}

run() {
  case "$1" in
    health|models) get "$1" ;;
    price|greeks|compare|convergence|payoff|paths|implied-vol|vol-surface) post "$1" ;;
    invalid) post price invalid ;;
    *) echo "Unknown endpoint '$1'. Try: health models price greeks compare convergence payoff paths implied-vol vol-surface invalid" >&2; exit 1 ;;
  esac
}

if [ "$#" -gt 0 ]; then
  for name in "$@"; do run "$name"; done
else
  for name in health models price greeks compare convergence payoff paths implied-vol vol-surface invalid; do
    run "$name"
  done
fi
