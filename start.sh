#!/usr/bin/env bash
PORT="${PORT:-8000}"
echo "Starting Forex Alert Engine on port $PORT..."
exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.main:app --bind "0.0.0.0:$PORT" --timeout 120
