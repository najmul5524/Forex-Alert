import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api.alerts import router as alerts_router
from app.api.market import router as market_router
from app.api.notifications import router as notifications_router
from app.api.settings import router as settings_router
from app.api.download import router as download_router
from app.api.websocket import ws_manager
from app.engine.market_feed import market_feed
from app.notifications.dispatcher import set_ws_broadcast_callback

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ForexAlertApp")

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()

    logger.info("Wiring WebSocket broadcasting callbacks...")
    set_ws_broadcast_callback(ws_manager.broadcast)
    market_feed.set_broadcast_callback(ws_manager.broadcast)

    logger.info("Starting background market feed engine...")
    await market_feed.start()

    yield

    logger.info("Shutting down market feed engine...")
    await market_feed.stop()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(alerts_router)
app.include_router(market_router)
app.include_router(notifications_router)
app.include_router(settings_router)
app.include_router(download_router)

@app.get("/health")
@app.get("/ping")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"vapid_public_key": settings.VAPID_PUBLIC_KEY}
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                if data == "ping" or '"ping"' in data:
                    await websocket.send_text("pong")
            except Exception:
                pass
    except (WebSocketDisconnect, Exception) as e:
        logger.debug(f"WebSocket client disconnected/error: {e}")
    finally:
        ws_manager.disconnect(websocket)
