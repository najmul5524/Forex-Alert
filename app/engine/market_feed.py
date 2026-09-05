import asyncio
import datetime
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
    {"symbol": "XAUUSD", "name": "Gold / USD", "type": "metals", "base_price": 4432.0, "decimals": 2, "spread_pips": 2.5},
    {"symbol": "XAGUSD", "name": "Silver / USD", "type": "metals", "base_price": 54.20, "decimals": 3, "spread_pips": 1.8},
    {"symbol": "USOIL", "name": "Crude Oil WTI", "type": "energy", "base_price": 78.50, "decimals": 2, "spread_pips": 3.0},

    # Indices
    {"symbol": "SPX500", "name": "S&P 500 Index", "type": "indices", "base_price": 5650.0, "decimals": 2, "spread_pips": 4.0},
    {"symbol": "NAS100", "name": "Nasdaq 100 Index", "type": "indices", "base_price": 19800.0, "decimals": 2, "spread_pips": 5.0},
    {"symbol": "US30", "name": "Dow Jones 30", "type": "indices", "base_price": 41500.0, "decimals": 2, "spread_pips": 6.0},

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
        self._active_alerts_cache: Dict[str, List[dict]] = {}

    def set_broadcast_callback(self, cb):
        self.ws_broadcast_callback = cb

    async def reload_alerts_cache(self):
        """Loads all active alerts into memory to eliminate per-tick DB queries."""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Alert).where(Alert.is_active == True)
                alerts = (await session.execute(stmt)).scalars().all()
                new_cache: Dict[str, List[dict]] = {}
                for a in alerts:
                    sym = (a.symbol or "").upper().replace("/", "").replace("-", "")
                    alert_dict = {
                        "id": a.id,
                        "condition_type": a.condition_type,
                        "params": a.params or {},
                        "symbol": sym,
                        "timeframe": a.timeframe or "1m",
                        "trigger_frequency": a.trigger_frequency,
                        "cooldown_minutes": a.cooldown_minutes or 5,
                        "last_triggered_at": a.last_triggered_at,
                        "last_evaluated_bar_time": a.last_evaluated_bar_time,
                        "channels": a.channels or ["in_app"],
                        "target_email": a.target_email,
                        "webhook_url": a.webhook_url,
                        "message": a.message
                    }
                    new_cache.setdefault(sym, []).append(alert_dict)
                self._active_alerts_cache = new_cache
                logger.info(f"MarketFeed alert cache refreshed: {sum(len(v) for v in new_cache.values())} active alerts loaded.")
        except Exception as e:
            logger.error(f"Failed to reload alert cache: {e}")

    def update_cached_alert_after_trigger(self, alert_id: int, now_utc, current_bar_time: int, should_deactivate: bool):
        """Update in-memory alert state instantly after a trigger without DB wait."""
        for sym, alerts in self._active_alerts_cache.items():
            for a in alerts:
                if a.get("id") == alert_id:
                    if should_deactivate:
                        alerts.remove(a)
                    else:
                        a["last_triggered_at"] = now_utc
                        a["last_evaluated_bar_time"] = current_bar_time
                    return

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

        # Check in-memory alert cache (Zero SQLite database I/O per tick)
        alerts = self._active_alerts_cache.get(sym)
        if not alerts:
            return

        for alert in list(alerts):
            tf = alert.get("timeframe") or "1m"
            df = store.get_dataframe(tf)
            curr_candle = store.get_latest_candle(tf)
            curr_bar_time = curr_candle.time if curr_candle else int(time.time())

            is_close_event = any(e[0] == tf and e[1] for e in events)

            result = evaluate_alert_condition(
                alert_dict=alert,
                candles_df=df,
                prev_tick_price=store.prev_tick_price,
                current_price=price,
                current_bar_time=curr_bar_time,
                is_bar_close=is_close_event
            )

            if result.triggered:
                logger.info(f"ALERT TRIGGERED: {result.summary}")
                # Instantly reflect in cache to prevent duplicate rapid firings
                self.update_cached_alert_after_trigger(
                    alert_id=alert["id"],
                    now_utc=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
                    current_bar_time=curr_bar_time,
                    should_deactivate=result.should_deactivate
                )
                asyncio.create_task(dispatch_alert_notifications(
                    alert_id=alert["id"],
                    symbol=sym,
                    timeframe=tf,
                    summary=result.summary,
                    trigger_price=price,
                    channels=alert.get("channels") or ["in_app"],
                    target_email=alert.get("target_email"),
                    webhook_url=alert.get("webhook_url"),
                    custom_message=alert.get("message"),
                    should_deactivate=result.should_deactivate,
                    current_bar_time=curr_bar_time
                ))

    async def _binance_stream_worker(self):
        crypto_pairs = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt"]
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
            try:
                # Fetch live real-world exchange rates from Open ER API
                async with httpx.AsyncClient(timeout=8) as client:
                    resp = await client.get("https://open.er-api.com/v6/latest/USD")
                    if resp.status_code == 200:
                        data = resp.json()
                        rates = data.get("rates", {})
                        
                        fx_map = {
                            "EURUSD": round(1.0 / rates.get("EUR", 0.92), 5) if rates.get("EUR") else None,
                            "GBPUSD": round(1.0 / rates.get("GBP", 0.77), 5) if rates.get("GBP") else None,
                            "USDJPY": round(rates.get("JPY", 154.5), 3) if rates.get("JPY") else None,
                            "AUDUSD": round(1.0 / rates.get("AUD", 1.52), 5) if rates.get("AUD") else None,
                            "USDCAD": round(rates.get("CAD", 1.37), 5) if rates.get("CAD") else None,
                            "USDCHF": round(rates.get("CHF", 0.89), 5) if rates.get("CHF") else None,
                            "NZDUSD": round(1.0 / rates.get("NZD", 1.67), 5) if rates.get("NZD") else None,
                            "EURGBP": round(rates.get("GBP", 1) / rates.get("EUR", 1), 5) if rates.get("EUR") and rates.get("GBP") else None,
                            "EURJPY": round(rates.get("JPY", 1) / rates.get("EUR", 1), 3) if rates.get("EUR") and rates.get("JPY") else None,
                            "GBPJPY": round(rates.get("JPY", 1) / rates.get("GBP", 1), 3) if rates.get("GBP") and rates.get("JPY") else None,
                        }

                        for sym, p in fx_map.items():
                            if p is not None:
                                await self.process_tick(sym, p)
            except Exception as e:
                logger.debug(f"Live Forex polling error: {e}")

            await asyncio.sleep(8)

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
                    
                await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"Simulation worker error: {e}")
                await asyncio.sleep(1.5)

    async def _populate_real_history_worker(self):
        try:
            await asyncio.sleep(4) # Let server bind port and start accepting traffic immediately
            from app.engine.real_market_data import real_market_data
            for s in SUPPORTED_SYMBOLS:
                if not self.is_running:
                    break
                sym = s["symbol"]
                try:
                    await real_market_data.populate_symbol_real_history(sym)
                    logger.info(f"Loaded authentic real market history for {sym}")
                except Exception as e:
                    logger.debug(f"Could not load real history for {sym}: {e}")
                await asyncio.sleep(1.0)
        except Exception as e:
            logger.error(f"Error in real history worker: {e}")

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger.info("Starting Market Feed Engine...")
        
        # Load active alerts into memory
        await self.reload_alerts_cache()

        self.tasks.append(asyncio.create_task(self._simulation_worker()))
        self.tasks.append(asyncio.create_task(self._binance_stream_worker()))
        self.tasks.append(asyncio.create_task(self._forex_polling_worker()))
        self.tasks.append(asyncio.create_task(self._populate_real_history_worker()))

    async def stop(self):
        self.is_running = False
        for t in self.tasks:
            t.cancel()
        self.tasks.clear()
        logger.info("Market Feed Engine stopped.")

market_feed = MarketFeedEngine()
