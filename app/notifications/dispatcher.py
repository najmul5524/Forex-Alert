import asyncio
import datetime
import logging
from typing import Dict, Any, List
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.alert import Alert
from app.models.trigger_log import TriggerLog
from app.models.push_subscription import PushSubscription
from app.models.device_token import DeviceToken
from app.notifications.push_service import send_web_push
from app.notifications.email_service import send_email_alert
from app.notifications.fcm_service import send_fcm_notification
from app.notifications.webhook_service import send_webhook_alert, send_discord_alert, send_telegram_alert
from app.config import settings

logger = logging.getLogger(__name__)

ws_broadcast_callback = None

def set_ws_broadcast_callback(cb):
    global ws_broadcast_callback
    ws_broadcast_callback = cb

async def dispatch_alert_notifications(
    alert_id: int,
    symbol: str,
    timeframe: str,
    summary: str,
    trigger_price: float,
    channels: List[str],
    target_email: str = None,
    webhook_url: str = None,
    custom_message: str = None,
    should_deactivate: bool = False,
    current_bar_time: int = 0
):
    now_utc = datetime.datetime.now(datetime.UTC)
    dispatched_channels = []

    payload = {
        "alert_id": alert_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "summary": summary,
        "trigger_price": trigger_price,
        "message": custom_message or "",
        "timestamp": now_utc.strftime("%Y-%m-%d %H:%M:%S")
    }

    # 1. In-App Broadcast via WebSocket
    if "in_app" in channels:
        dispatched_channels.append("in_app")
        if ws_broadcast_callback:
            try:
                await ws_broadcast_callback({
                    "type": "alert_triggered",
                    "data": payload
                })
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")

    # 2. Web Push & Android Notifications
    if "push" in channels:
        try:
            async with AsyncSessionLocal() as session:
                # Dispatch Web Push
                subs = (await session.execute(select(PushSubscription))).scalars().all()
                push_tasks = []
                for sub in subs:
                    sub_info = {
                        "endpoint": sub.endpoint,
                        "keys": {
                            "p256dh": sub.p256dh,
                            "auth": sub.auth
                        }
                    }
                    push_payload = {
                        "title": f"🚨 {symbol} Alert ({timeframe})",
                        "body": f"{summary}\nPrice: {trigger_price}",
                        "icon": "/static/icon.png",
                        "data": {"url": "/", "alert_id": alert_id}
                    }
                    push_tasks.append(send_web_push(sub_info, push_payload))
                
                if push_tasks:
                    results = await asyncio.gather(*push_tasks, return_exceptions=True)
                    if any(r is True for r in results if not isinstance(r, Exception)):
                        dispatched_channels.append("push")

                # Dispatch Android FCM Push
                devices = (await session.execute(select(DeviceToken))).scalars().all()
                if devices:
                    tokens = [d.token for d in devices]
                    fcm_count = await send_fcm_notification(
                        device_tokens=tokens,
                        title=f"🚨 {symbol} Alert ({timeframe})",
                        body=f"{summary} | Price: {trigger_price}",
                        data={
                            "alert_id": str(alert_id),
                            "symbol": symbol,
                            "price": str(trigger_price),
                            "timeframe": timeframe
                        }
                    )
                    if fcm_count > 0 and "android" not in dispatched_channels:
                        dispatched_channels.append("android")
        except Exception as e:
            logger.error(f"Push & Android dispatch error: {e}")

    # 3. Email Alert
    if "email" in channels and target_email:
        subject = f"🚨 Market Alert: {symbol} - {summary}"
        email_sent = await send_email_alert(target_email, subject, payload)
        if email_sent:
            dispatched_channels.append("email")

    # 4. Webhook / Discord / Telegram
    if "webhook" in channels:
        if webhook_url:
            await send_webhook_alert(webhook_url, payload)
            dispatched_channels.append("webhook")
        if settings.DISCORD_WEBHOOK_URL:
            await send_discord_alert(settings.DISCORD_WEBHOOK_URL, payload)
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            await send_telegram_alert(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID, payload)

    # 5. Record Log & Update Alert in DB
    try:
        async with AsyncSessionLocal() as session:
            log = TriggerLog(
                alert_id=alert_id,
                symbol=symbol,
                condition_summary=summary,
                trigger_price=trigger_price,
                timeframe=timeframe,
                channels_sent=dispatched_channels,
                timestamp=now_utc
            )
            session.add(log)

            alert = await session.get(Alert, alert_id)
            if alert:
                alert.last_triggered_at = now_utc
                alert.trigger_count += 1
                alert.last_evaluated_bar_time = current_bar_time
                if should_deactivate:
                    alert.is_active = False
            
            await session.commit()
    except Exception as e:
        logger.error(f"Database error while saving alert trigger: {e}")
