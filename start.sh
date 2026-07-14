#!/usr/bin/env bash
# Single entrypoint for Replit: builds the frontend, then starts the backend
# which serves both the API and the built frontend on one port.
set -e

cd "$(dirname "$0")"

echo "=== Frontend: installing & building ==="
cd frontend
npm install --silent
npm run build

echo "=== Starting server on port ${PORT:-5000} ==="
cd ../backend
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-5000}"
