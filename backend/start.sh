#!/bin/bash
# Runs on every container start. Both steps are safe to repeat:
# - `alembic upgrade head` only applies migrations that haven't run yet.
# - `seed_platforms.py` skips any platform slug that already exists.
# This means no manual Shell/SSH access is needed on any host, including
# Render's free tier where Shell access isn't available.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding default platforms..."
python scripts/seed_platforms.py

echo "Starting server..."
# Render (and similar platforms) assign a random $PORT the app must bind to.
# Falls back to 8000 for local docker-compose, which doesn't set $PORT.
if [ "$RELOAD" = "true" ]; then
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
else
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi
