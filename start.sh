#!/usr/bin/env bash
# Single entrypoint for Replit (and anywhere else that just wants one
# command to run the whole app): installs deps if needed, builds the
# frontend, then starts the backend which serves both the API and the
# built frontend on one port.
set -e

cd "$(dirname "$0")"

echo "=== Backend: installing dependencies ==="
cd backend
if [ ! -d venv ]; then
  python3 -m venv venv
fi
venv/bin/pip install --quiet --upgrade pip
venv/bin/pip install --quiet -r requirements.txt

echo "=== Frontend: building ==="
cd ../frontend
npm install --silent
npm run build

echo "=== Starting server on port ${PORT:-8000} ==="
cd ../backend
exec venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
