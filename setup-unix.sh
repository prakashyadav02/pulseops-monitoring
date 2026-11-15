#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
command -v python3 >/dev/null || { echo 'Python 3.11+ is required'; exit 1; }
command -v npm >/dev/null || { echo 'Node.js 22 LTS / npm is required'; exit 1; }
if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r backend/requirements.txt
[[ -f backend/.env ]] || cp backend/.env.example backend/.env
[[ -f frontend/.env ]] || cp frontend/.env.example frontend/.env
(cd frontend && npm install)
exec "$ROOT/start-unix.sh"
