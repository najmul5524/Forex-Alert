import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db

@pytest.mark.asyncio
async def test_api_symbols_and_alerts_flow():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Test symbols endpoint
        res = await ac.get("/api/market/symbols")
        assert res.status_code == 200
        symbols = res.json()
        assert len(symbols) > 0
        assert any(s["symbol"] == "EURUSD" for s in symbols)

        # 2. Test create alert
        alert_payload = {
            "symbol": "EURUSD",
            "timeframe": "1m",
            "condition_type": "price_cross_up",
            "params": {"target_price": 1.08600},
            "trigger_frequency": "only_once",
            "channels": ["in_app", "push"],
            "is_active": True
        }
        res_create = await ac.post("/api/alerts", json=alert_payload)
        assert res_create.status_code == 201
        created_alert = res_create.json()
        alert_id = created_alert["id"]
        assert created_alert["symbol"] == "EURUSD"
        assert created_alert["is_active"] is True

        # 3. Test list alerts
        res_list = await ac.get("/api/alerts")
        assert res_list.status_code == 200
        alerts = res_list.json()
        assert any(a["id"] == alert_id for a in alerts)

        # 4. Test toggle alert
        res_toggle = await ac.post(f"/api/alerts/{alert_id}/toggle")
        assert res_toggle.status_code == 200
        assert res_toggle.json()["is_active"] is False

        # 5. Test test-trigger alert
        res_trigger = await ac.post(f"/api/alerts/{alert_id}/test-trigger")
        assert res_trigger.status_code == 200

        # 6. Test delete alert
        res_del = await ac.delete(f"/api/alerts/{alert_id}")
        assert res_del.status_code == 200

@pytest.mark.asyncio
async def test_android_device_registration():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        device_payload = {
            "token": "test_fcm_token_12345",
            "device_name": "Samsung Galaxy S23",
            "platform": "android"
        }
        res = await ac.post("/api/notifications/register-device", json=device_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["token"] == "test_fcm_token_12345"
        assert data["device_name"] == "Samsung Galaxy S23"

        # Test Android push test dispatch
        res_push = await ac.post("/api/notifications/test-android-push")
        assert res_push.status_code == 200
        assert res_push.json()["status"] == "success"
