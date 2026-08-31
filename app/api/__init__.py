from app.api.alerts import router as alerts_router
from app.api.market import router as market_router
from app.api.notifications import router as notifications_router
from app.api.settings import router as settings_router

__all__ = [alerts_router, market_router, notifications_router, settings_router]
