import os
import uvicorn
from app.config import settings

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT or 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("=" * 60)
    print("🚀 LIVE MARKET ALERT ENGINE")
    print(f"📡 Server running at: http://{host}:{port}")
    print(f"📊 Live Charts & Alerts Dashboard active")
    print("=" * 60)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
