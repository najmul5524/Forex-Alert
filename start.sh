#!/usr/bin/env bash
set -e

if [ -f "/opt/render/project/src/.venv/bin/python" ]; then
    exec /opt/render/project/src/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
elif [ -f "/opt/render/project/.venv/bin/python" ]; then
    exec /opt/render/project/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
else
    exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi
