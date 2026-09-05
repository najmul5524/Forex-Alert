from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.alert import Alert
from app.models.trigger_log import TriggerLog
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse
from app.schemas.trigger_log import TriggerLogResponse
from app.notifications.dispatcher import dispatch_alert_notifications
from app.engine.candle_manager import candle_manager
from app.engine.market_feed import market_feed

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    symbol: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).order_by(desc(Alert.created_at))
    if symbol:
        stmt = stmt.where(Alert.symbol == symbol.upper().replace("/", "").replace("-", ""))
    if is_active is not None:
        stmt = stmt.where(Alert.is_active == is_active)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(alert_in: AlertCreate, db: AsyncSession = Depends(get_db)):
    cleaned_symbol = alert_in.symbol.upper().replace("/", "").replace("-", "")
    alert = Alert(
        symbol=cleaned_symbol,
        timeframe=alert_in.timeframe,
        condition_type=alert_in.condition_type,
        params=alert_in.params,
        trigger_frequency=alert_in.trigger_frequency,
        cooldown_minutes=alert_in.cooldown_minutes,
        channels=alert_in.channels,
        target_email=alert_in.target_email,
        webhook_url=alert_in.webhook_url,
        message=alert_in.message,
        is_active=alert_in.is_active
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    await market_feed.reload_alerts_cache()
    return alert

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: int, alert_in: AlertUpdate, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    update_data = alert_in.model_dump(exclude_unset=True)
    if "symbol" in update_data and update_data["symbol"]:
        update_data["symbol"] = update_data["symbol"].upper().replace("/", "").replace("-", "")

    for field, value in update_data.items():
        setattr(alert, field, value)

    await db.commit()
    await db.refresh(alert)
    await market_feed.reload_alerts_cache()
    return alert

@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
    await market_feed.reload_alerts_cache()
    return {"status": "deleted", "id": alert_id}

@router.post("/{alert_id}/toggle", response_model=AlertResponse)
async def toggle_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = not alert.is_active
    await db.commit()
    await db.refresh(alert)
    await market_feed.reload_alerts_cache()
    return alert

@router.post("/{alert_id}/test-trigger")
async def test_trigger_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    store = candle_manager.get_or_create_store(alert.symbol)
    curr_price = store.latest_tick_price or 1.0850
    summary = f"[TEST] {alert.symbol} condition triggered manually for testing"

    await dispatch_alert_notifications(
        alert_id=alert.id,
        symbol=alert.symbol,
        timeframe=alert.timeframe,
        summary=summary,
        trigger_price=curr_price,
        channels=alert.channels or ["in_app"],
        target_email=alert.target_email,
        webhook_url=alert.webhook_url,
        custom_message=alert.message or "Manual test firing from dashboard"
    )
    return {"status": "success", "message": f"Test alert dispatched for {alert.symbol}"}

@router.get("/history/logs", response_model=List[TriggerLogResponse])
async def get_trigger_logs(
    symbol: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(TriggerLog).order_by(desc(TriggerLog.timestamp)).limit(limit)
    if symbol:
        stmt = stmt.where(TriggerLog.symbol == symbol.upper().replace("/", "").replace("-", ""))
    result = await db.execute(stmt)
    return result.scalars().all()
