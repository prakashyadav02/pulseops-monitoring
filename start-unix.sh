#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
[[ -x "$ROOT/.venv/bin/python" && -d "$ROOT/frontend/node_modules" ]] || { echo 'Run ./setup-unix.sh first.'; exit 1; }
(cd "$ROOT/backend" && "$ROOT/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) &
API_PID=$!
(cd "$ROOT/frontend" && npm run dev) &
WEB_PID=$!
cleanup(){ kill "$API_PID" "$WEB_PID" 2>/dev/null || true; wait "$API_PID" "$WEB_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
echo 'PulseOps API: http://127.0.0.1:8000/docs'
echo 'PulseOps Web: http://127.0.0.1:5173'
echo 'Demo: demo@pulseops.dev / Demo@12345'
wait -n "$API_PID" "$WEB_PID" || true
