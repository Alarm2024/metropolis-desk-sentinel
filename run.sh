#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment in .venv ..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python -c "import fastapi" 2>/dev/null; then
  echo "Installing dependencies..."
  python -m pip install -q -r requirements.txt
fi

PORT="${PORT:-8080}"
echo "Starting Morning Light Desk Sentinel on http://127.0.0.1:${PORT}"
exec python -m uvicorn server.app:app --host 127.0.0.1 --port "${PORT}" --reload
