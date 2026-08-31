#!/usr/bin/env bash
PORT="${PORT:-8000}"
echo "Starting Forex Alert Engine on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers --forwarded-allow-ips="*" --ws-ping-interval 20 --ws-ping-timeout 30
