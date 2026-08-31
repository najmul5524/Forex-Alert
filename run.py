import os
import sys

# Auto re-exec with virtualenv python if invoked via mismatched system python on Render
for venv_py in [
    "/opt/render/project/src/.venv/bin/python",
    "/opt/render/project/.venv/bin/python",
    "./.venv/bin/python",
]:
    if os.path.exists(venv_py) and os.path.realpath(sys.executable) != os.path.realpath(venv_py):
        os.execv(venv_py, [venv_py] + sys.argv)

import uvicorn
from app.config import settings

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT or 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("=" * 60)
    print("🚀 LIVE MARKET ALERT ENGINE")
    print(f"📡 Server running at: http://{host}:{port}")
    print("=" * 60)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
