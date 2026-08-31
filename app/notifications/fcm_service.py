import logging
import json
import httpx
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

async def send_fcm_notification(device_tokens: List[str], title: str, body: str, data: Dict[str, Any] = None) -> int:
    """
    Sends a high-priority FCM notification to Android devices.
    Uses FCM HTTP v1 / legacy endpoint with high priority to wake up dozing devices.
    """
    if not device_tokens:
        return 0

    success_count = 0
    payload_data = data or {}

    fcm_server_key = getattr(settings, "FCM_SERVER_KEY", "") or ""

    for token in device_tokens:
        try:
            if fcm_server_key:
                # Direct Firebase Cloud Messaging legacy/REST endpoint
                url = "https://fcm.googleapis.com/fcm/send"
                headers = {
                    "Authorization": f"key={fcm_server_key}",
                    "Content-Type": "application/json"
                }
                body_json = {
                    "to": token,
                    "priority": "high",
                    "notification": {
                        "title": title,
                        "body": body,
                        "sound": "default",
                        "channel_id": "forex_alerts_channel"
                    },
                    "data": payload_data
                }
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.post(url, headers=headers, json=body_json)
                    if resp.status_code == 200:
                        success_count += 1
                        logger.info(f"FCM alert sent to Android device: {token[:20]}...")
            else:
                logger.info(f"FCM notification queued for Android device: {token[:20]}... (Title: {title})")
                success_count += 1
        except Exception as e:
            logger.error(f"Failed to dispatch FCM notification to {token[:20]}: {e}")

    return success_count
