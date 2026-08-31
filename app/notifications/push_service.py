import json
import logging
from pywebpush import webpush, WebPushException
from app.config import settings

logger = logging.getLogger(__name__)

async def send_web_push(subscription_info: dict, payload_data: dict) -> bool:
    if not settings.VAPID_PRIVATE_KEY:
        logger.warning("VAPID private key is not configured. Web push skipped.")
        return False

    try:
        data_json = json.dumps(payload_data)
        webpush(
            subscription_info=subscription_info,
            data=data_json,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_CLAIM_EMAIL}
        )
        logger.info(f"Web push successfully sent to endpoint: {subscription_info.get('endpoint', '')[:40]}...")
        return True
    except WebPushException as ex:
        logger.error(f"WebPush failed: {ex}")
        return False
    except Exception as e:
        logger.error(f"Unexpected WebPush error: {e}")
        return False
