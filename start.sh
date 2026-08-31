#!/usr/bin/env bash
if [ -d "/opt/render/project/src/.venv" ]; then
    source /opt/render/project/src/.venv/bin/activate
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
