import logging
import httpx

logger = logging.getLogger(__name__)

async def send_webhook_alert(url: str, payload_data: dict) -> bool:
    if not url:
        return False
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(url, json=payload_data)
            if resp.status_code < 300:
                logger.info(f"Webhook delivered to {url}")
                return True
            logger.warning(f"Webhook returned status {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"Webhook delivery failed: {e}")
        return False

async def send_discord_alert(webhook_url: str, data: dict) -> bool:
    if not webhook_url:
        return False
    embed = {
        "title": f"Alert: {data.get('symbol')} ({data.get('timeframe')})",
        "description": data.get("summary"),
        "color": 3447003,
        "fields": [
            {"name": "Trigger Price", "value": str(data.get("trigger_price")), "inline": True},
            {"name": "Instrument", "value": str(data.get("symbol")), "inline": True},
            {"name": "Time (UTC)", "value": str(data.get("timestamp")), "inline": True},
        ]
    }
    if data.get("message"):
        embed["fields"].append({"name": "Custom Note", "value": str(data.get("message")), "inline": False})
    
    return await send_webhook_alert(webhook_url, {"embeds": [embed]})

async def send_telegram_alert(bot_token: str, chat_id: str, data: dict) -> bool:
    if not bot_token or not chat_id:
        return False
    text = (
        f"Market Alert Triggered\n\n"
        f"Instrument: {data.get('symbol')}\n"
        f"Condition: {data.get('summary')}\n"
        f"Price: {data.get('trigger_price')}\n"
        f"Timeframe: {data.get('timeframe')}\n"
        f"Time: {data.get('timestamp')} UTC"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(url, json={"chat_id": chat_id, "text": text})
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Telegram alert failed: {e}")
        return False
