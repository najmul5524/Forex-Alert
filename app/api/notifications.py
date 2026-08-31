import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.config import settings
from app.models.push_subscription import PushSubscription
from app.models.device_token import DeviceToken
from app.schemas.push import PushSubscriptionCreate
from app.schemas.device_token import DeviceTokenRegister, DeviceTokenResponse
from app.notifications.push_service import send_web_push
from app.notifications.email_service import send_email_alert
from app.notifications.fcm_service import send_fcm_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("/vapid-public-key")
async def get_vapid_public_key():
    return {"publicKey": settings.VAPID_PUBLIC_KEY}

@router.post("/subscribe")
async def subscribe_push(sub_in: PushSubscriptionCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(PushSubscription).where(PushSubscription.endpoint == sub_in.endpoint)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    
    if existing:
        existing.p256dh = sub_in.keys.p256dh
        existing.auth = sub_in.keys.auth
    else:
        new_sub = PushSubscription(
            endpoint=sub_in.endpoint,
            p256dh=sub_in.keys.p256dh,
            auth=sub_in.keys.auth
        )
        db.add(new_sub)
    
    await db.commit()
    return {"status": "subscribed"}

@router.post("/register-device", response_model=DeviceTokenResponse)
async def register_android_device(device_in: DeviceTokenRegister, db: AsyncSession = Depends(get_db)):
    """Registers an Android device FCM token for background smartphone notifications."""
    stmt = select(DeviceToken).where(DeviceToken.token == device_in.token)
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing:
        existing.device_name = device_in.device_name
        existing.platform = device_in.platform
        await db.commit()
        await db.refresh(existing)
        return existing
    
    new_device = DeviceToken(
        token=device_in.token,
        device_name=device_in.device_name,
        platform=device_in.platform
    )
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)
    return new_device

@router.post("/test-android-push")
async def test_android_push(db: AsyncSession = Depends(get_db)):
    """Sends a test push notification to all registered Android devices."""
    stmt = select(DeviceToken)
    devices = (await db.execute(stmt)).scalars().all()
    if not devices:
        raise HTTPException(status_code=400, detail="No Android devices registered yet. Open the Android app to register your phone.")

    tokens = [d.token for d in devices]
    count = await send_fcm_notification(
        device_tokens=tokens,
        title="⚡ Forex Alert: EURUSD (1m)",
        body="EURUSD crossed ABOVE 1.08550! (Test Mobile Alert)",
        data={"type": "test_alert", "symbol": "EURUSD", "price": "1.08550"}
    )
    return {"status": "success", "sent_to_android_devices": count}

@router.post("/test-push")
async def test_push_notification(db: AsyncSession = Depends(get_db)):
    stmt = select(PushSubscription)
    subs = (await db.execute(stmt)).scalars().all()
    if not subs:
        raise HTTPException(status_code=400, detail="No browser push subscriptions registered yet.")
    
    sent_count = 0
    payload = {
        "title": "⚡ Market Alert Notification Test",
        "body": "Your browser push alerts are connected and functioning properly!",
        "icon": "/static/icon.png",
        "data": {"url": "/"}
    }
    for sub in subs:
        sub_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth
            }
        }
        res = await send_web_push(sub_info, payload)
        if res:
            sent_count += 1
            
    return {"status": "success", "sent_to_devices": sent_count}

@router.post("/test-email")
async def test_email(payload: dict = Body(...)):
    target_email = payload.get("email")
    if not target_email:
        raise HTTPException(status_code=400, detail="Target email is required")
    
    data = {
        "symbol": "EURUSD",
        "timeframe": "1m",
        "summary": "This is a test notification from your Live Forex Alert Engine",
        "trigger_price": "1.08520",
        "timestamp": "Now",
        "message": "If you are reading this, your email configuration is working perfectly!"
    }
    res = await send_email_alert(target_email, "⚡ Test Alert: Live Market Alert System", data)
    if not res:
        raise HTTPException(status_code=500, detail="Failed to send email. Check SMTP settings.")
    return {"status": "success", "message": f"Test email sent to {target_email}"}
