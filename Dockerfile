# Multi-stage build: Node to build the frontend, Python to run the backend
# (which serves the built frontend as static files). See README.md for the
# non-Docker equivalent of these same two steps.

FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
ENV NPM_CONFIG_UPDATE_NOTIFIER=false
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund || npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
