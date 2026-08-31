import asyncio
import json
import logging
import random
import time
import websockets
import httpx
from typing import List, Dict, Set
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.alert import Alert
from app.engine.candle_manager import candle_manager, TIMEFRAME_SECONDS
from app.engine.rule_evaluator import evaluate_alert_condition
from app.notifications.dispatcher import dispatch_alert_notifications
from app.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_SYMBOLS = [
    # Major Forex Pairs
    {"symbol": "EURUSD", "name": "EUR / USD", "type": "forex", "base_price": 1.0850, "decimals": 5, "spread_pips": 1.2},
    {"symbol": "GBPUSD", "name": "GBP / USD", "type": "forex", "base_price": 1.2950, "decimals": 5, "spread_pips": 1.5},
    {"symbol": "USDJPY", "name": "USD / JPY", "type": "forex", "base_price": 154.50, "decimals": 3, "spread_pips": 1.4},
    {"symbol": "AUDUSD", "name": "AUD / USD", "type": "forex", "base_price": 0.6550, "decimals": 5, "spread_pips": 1.6},
    {"symbol": "USDCAD", "name": "USD / CAD", "type": "forex", "base_price": 1.3650, "decimals": 5, "spread_pips": 1.8},
    {"symbol": "USDCHF", "name": "USD / CHF", "type": "forex", "base_price": 0.8920, "decimals": 5, "spread_pips": 1.7},
    {"symbol": "NZDUSD", "name": "NZD / USD", "type": "forex", "base_price": 0.5980, "decimals": 5, "spread_pips": 2.0},
    {"symbol": "EURGBP", "name": "EUR / GBP", "type": "forex", "base_price": 0.8380, "decimals": 5, "spread_pips": 1.5},
    {"symbol": "EURJPY", "name": "EUR / JPY", "type": "forex", "base_price": 167.60, "decimals": 3, "spread_pips": 1.9},
    {"symbol": "GBPJPY", "name": "GBP / JPY", "type": "forex", "base_price": 200.10, "decimals": 3, "spread_pips": 2.2},

    # Metals & Energy
    {"symbol": "XAUUSD", "name": "Gold / USD", "type": "metals", "base_price": 2500.0, "decimals": 2, "spread_pips": 2.5},
    {"symbol": "XAGUSD", "name": "Silver / USD", "type": "metals", "base_price": 29.50, "decimals": 3, "spread_pips": 1.8},
    {"symbol": "USOIL", "name": "Crude Oil WTI", "type": "energy", "base_price": 74.20, "decimals": 2, "spread_pips": 3.0},

    # Indices
    {"symbol": "SPX500", "name": "S&P 500 Index", "type": "indices", "base_price": 5600.0, "decimals": 2, "spread_pips": 4.0},
    {"symbol": "NAS100", "name": "Nasdaq 100 Index", "type": "indices", "base_price": 19500.0, "decimals": 2, "spread_pips": 5.0},
    {"symbol": "US30", "name": "Dow Jones 30", "type": "indices", "base_price": 41200.0, "decimals": 2, "spread_pips": 6.0},

    # Crypto Assets
    {"symbol": "BTCUSDT", "name": "Bitcoin / USDT", "type": "crypto", "base_price": 64500.0, "decimals": 2, "spread_pips": 1.0},
    {"symbol": "ETHUSDT", "name": "Ethereum / USDT", "type": "crypto", "base_price": 2650.0, "decimals": 2, "spread_pips": 1.0},
    {"symbol": "SOLUSDT", "name": "Solana / USDT", "type": "crypto", "base_price": 145.0, "decimals": 2, "spread_pips": 0.5},
    {"symbol": "BNBUSDT", "name": "BNB / USDT", "type": "crypto", "base_price": 540.0, "decimals": 2, "spread_pips": 0.5},
    {"symbol": "XRPUSDT", "name": "XRP / USDT", "type": "crypto", "base_price": 0.5850, "decimals": 4, "spread_pips": 0.8}
]

class MarketFeedEngine:
    def __init__(self):
        self.is_running = False
        self.tasks: List[asyncio.Task] = []
        self.active_symbols: Set[str] = {s["symbol"] for s in SUPPORTED_SYMBOLS}
        self.ws_broadcast_callback = None
        self._symbol_map = {s["symbol"]: s for s in SUPPORTED_SYMBOLS}

    def set_broadcast_callback(self, cb):
        self.ws_broadcast_callback = cb

    async def process_tick(self, symbol: str, price: float, volume: float = 1.0):
        sym = symbol.upper().replace("/", "").replace("-", "")
        store, events = candle_manager.update_tick(sym, price, volume)

        s_meta = self._symbol_map.get(sym, {"decimals": 5, "spread_pips": 1.5, "type": "forex"})
        dec = s_meta.get("decimals", 5)
        pip_unit = 0.0001 if s_meta.get("type") == "forex" and dec >= 4 else (0.01 if dec <= 3 else 0.0001)
        spread_val = round((s_meta.get("spread_pips", 1.5) * pip_unit), dec)
        bid = round(price - (spread_val / 2.0), dec)
        ask = round(price + (spread_val / 2.0), dec)

        if self.ws_broadcast_callback:
            try:
                latest_1m = store.get_latest_candle("1m")
                await self.ws_broadcast_callback({
                    "type": "tick",
                    "data": {
                        "symbol": sym,
                        "price": price,
                        "bid": bid,
                        "ask": ask,
                        "spread": spread_val,
                        "decimals": dec,
                        "timestamp": int(time.time()),
                        "candle_1m": latest_1m.to_dict() if latest_1m else None
                    }
                })
            except Exception as e:
                logger.debug(f"Broadcast tick error: {e}")

        async with AsyncSessionLocal() as session:
            stmt = select(Alert).where(Alert.symbol == sym, Alert.is_active == True)
            alerts = (await session.execute(stmt)).scalars().all()
            if not alerts:
                return

            for alert in alerts:
                tf = alert.timeframe or "1m"
                df = store.get_dataframe(tf)
                curr_candle = store.get_latest_candle(tf)
                curr_bar_time = curr_candle.time if curr_candle else int(time.time())

                is_close_event = any(e[0] == tf and e[1] for e in events)

                alert_dict = {
                    "condition_type": alert.condition_type,
                    "params": alert.params or {},
                    "symbol": sym,
                    "timeframe": tf,
                    "trigger_frequency": alert.trigger_frequency,
                    "cooldown_minutes": alert.cooldown_minutes,
                    "last_triggered_at": alert.last_triggered_at,
                    "last_evaluated_bar_time": alert.last_evaluated_bar_time
                }

                result = evaluate_alert_condition(
                    alert_dict=alert_dict,
                    candles_df=df,
                    prev_tick_price=store.prev_tick_price,
                    current_price=price,
                    current_bar_time=curr_bar_time,
                    is_bar_close=is_close_event
                )

                if result.triggered:
                    logger.info(f"ALERT TRIGGERED: {result.summary}")
                    asyncio.create_task(dispatch_alert_notifications(
                        alert_id=alert.id,
                        symbol=sym,
                        timeframe=tf,
                        summary=result.summary,
                        trigger_price=price,
                        channels=alert.channels or ["in_app"],
                        target_email=alert.target_email,
                        webhook_url=alert.webhook_url,
                        custom_message=alert.message,
                        should_deactivate=result.should_deactivate,
                        current_bar_time=curr_bar_time
                    ))

    async def _binance_stream_worker(self):
        crypto_pairs = ["btcusdt", "ethusdt", "solusdt"]
        stream_names = "/".join([f"{p}@ticker" for p in crypto_pairs])
        urls = [
            f"wss://stream.binance.com:9443/ws/{stream_names}",
            f"wss://stream.binance.us:9443/ws/{stream_names}"
        ]

        url_idx = 0
        while self.is_running:
            url = urls[url_idx % len(urls)]
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    logger.info(f"Connected to crypto market feed: {url}")
                    while self.is_running:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        sym = data.get("s", "").upper()
                        price_str = data.get("c")
                        vol_str = data.get("v", "1")
                        if sym and price_str:
                            await self.process_tick(sym, float(price_str), float(vol_str))
            except Exception as e:
                err_msg = str(e)
                if "451" in err_msg or "rejected" in err_msg:
                    url_idx += 1
                    logger.info(f"Switching crypto feed host (reconnecting in 15s)...")
                    await asyncio.sleep(15)
                else:
                    await asyncio.sleep(10)

    async def _forex_polling_worker(self):
        while self.is_running:
            if settings.TWELVE_DATA_API_KEY:
                try:
                    symbols_param = "EUR/USD,GBP/USD,USD/JPY,XAU/USD,AUD/USD,USD/CAD"
                    url = f"https://api.twelvedata.com/price?symbol={symbols_param}&apikey={settings.TWELVE_DATA_API_KEY}"
                    async with httpx.AsyncClient(timeout=5) as client:
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            data = resp.json()
                            for pair_key, val in data.items():
                                if "price" in val:
                                    clean_sym = pair_key.replace("/", "").upper()
                                    await self.process_tick(clean_sym, float(val["price"]))
                except Exception as e:
                    logger.debug(f"TwelveData polling error: {e}")
            await asyncio.sleep(4)

    async def _simulation_worker(self):
        for s in SUPPORTED_SYMBOLS:
            candle_manager.get_or_create_store(s["symbol"])

        while self.is_running:
            try:
                for s in SUPPORTED_SYMBOLS:
                    sym = s["symbol"]
                    store = candle_manager.get_or_create_store(sym)
                    curr_p = store.latest_tick_price or s["base_price"]
                    dec = s["decimals"]
                    
                    vol = curr_p * (0.00015 if s["type"] == "forex" else 0.0004)
                    change = (random.random() - 0.498) * vol
                    new_p = round(curr_p + change, dec)
                    
                    vol_amt = random.uniform(1.0, 20.0)
                    await self.process_tick(sym, new_p, vol_amt)
                    
                await asyncio.sleep(1.2)
            except Exception as e:
                logger.error(f"Simulation worker error: {e}")
                await asyncio.sleep(1)

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger.info("Starting Market Feed Engine...")
        
        self.tasks.append(asyncio.create_task(self._simulation_worker()))
        self.tasks.append(asyncio.create_task(self._binance_stream_worker()))
        self.tasks.append(asyncio.create_task(self._forex_polling_worker()))

    async def stop(self):
        self.is_running = False
        for t in self.tasks:
            t.cancel()
        self.tasks.clear()
        logger.info("Market Feed Engine stopped.")

market_feed = MarketFeedEngine()
