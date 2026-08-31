import os
import sys
import glob

# Auto-detect and register Render virtualenv site-packages if invoked via system python
for pattern in [
    "/opt/render/project/src/.venv/lib/python*/site-packages",
    "/opt/render/project/.venv/lib/python*/site-packages",
    "/opt/render/project/src/venv/lib/python*/site-packages",
    os.path.expanduser("~/.local/lib/python*/site-packages"),
    "./venv/Lib/site-packages",
]:
    for path in glob.glob(pattern):
        if path not in sys.path:
            sys.path.insert(0, path)

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("=" * 60)
    print("🚀 LIVE MARKET ALERT ENGINE")
    print(f"📡 Server running at: http://{host}:{port}")
    print("=" * 60)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
