#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! python3 -c "import fastapi" 2>/dev/null; then
  echo "Installing dependencies..."
  python3 -m pip install -q -r requirements.txt
fi

echo "Starting Morning Light Desk Sentinel on http://127.0.0.1:8080"
exec python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8080 --reload
