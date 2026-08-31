import time
import math
import random
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

TIMEFRAME_SECONDS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}

class Candle:
    def __init__(self, time: int, open: float, high: float, low: float, close: float, volume: float = 0.0):
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time": self.time,
            "open": round(self.open, 5),
            "high": round(self.high, 5),
            "low": round(self.low, 5),
            "close": round(self.close, 5),
            "volume": round(self.volume, 2)
        }

class SymbolCandleStore:
    def __init__(self, symbol: str, max_bars: int = 500):
        self.symbol = symbol
        self.max_bars = max_bars
        self.timeframe_candles: Dict[str, List[Candle]] = {
            tf: [] for tf in TIMEFRAME_SECONDS
        }
        self.latest_tick_price: Optional[float] = None
        self.prev_tick_price: Optional[float] = None

    def seed_initial_candles(self, base_price: float = 1.0850, volatility: float = 0.0005):
        now = int(time.time())
        start_time = now - (150 * 60)
        curr_price = base_price

        for i in range(150):
            bar_time = start_time + (i * 60)
            drift = (random.random() - 0.49) * volatility
            open_p = curr_price
            close_p = open_p + drift
            high_p = max(open_p, close_p) + abs(random.random() * volatility * 0.5)
            low_p = min(open_p, close_p) - abs(random.random() * volatility * 0.5)
            vol = random.uniform(10.0, 150.0)

            c = Candle(bar_time, open_p, high_p, low_p, close_p, vol)
            self.timeframe_candles["1m"].append(c)
            curr_price = close_p

        self.latest_tick_price = curr_price
        self.prev_tick_price = curr_price

        for tf in ["5m", "15m", "1h", "4h", "1d"]:
            sec = TIMEFRAME_SECONDS[tf]
            bars_map = {}
            for c in self.timeframe_candles["1m"]:
                bucket = (c.time // sec) * sec
                if bucket not in bars_map:
                    bars_map[bucket] = Candle(bucket, c.open, c.high, c.low, c.close, c.volume)
                else:
                    b = bars_map[bucket]
                    b.high = max(b.high, c.high)
                    b.low = min(b.low, c.low)
                    b.close = c.close
                    b.volume += c.volume
            self.timeframe_candles[tf] = list(bars_map.values())

    def update_tick(self, price: float, volume: float = 1.0, timestamp: Optional[int] = None) -> List[Tuple[str, bool, Candle]]:
        if timestamp is None:
            timestamp = int(time.time())

        self.prev_tick_price = self.latest_tick_price
        self.latest_tick_price = price

        events = []

        for tf, sec in TIMEFRAME_SECONDS.items():
            bucket_time = (timestamp // sec) * sec
            candles = self.timeframe_candles[tf]

            if not candles:
                c = Candle(bucket_time, price, price, price, price, volume)
                candles.append(c)
                events.append((tf, False, c))
                continue

            last_c = candles[-1]
            if last_c.time == bucket_time:
                last_c.high = max(last_c.high, price)
                last_c.low = min(last_c.low, price)
                last_c.close = price
                last_c.volume += volume
                events.append((tf, False, last_c))
            else:
                events.append((tf, True, last_c))
                new_c = Candle(bucket_time, price, price, price, price, volume)
                candles.append(new_c)
                if len(candles) > self.max_bars:
                    candles.pop(0)
                events.append((tf, False, new_c))

        return events

    def get_dataframe(self, timeframe: str = "1m") -> pd.DataFrame:
        candles = self.timeframe_candles.get(timeframe, [])
        if not candles:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        
        data = {
            "time": [c.time for c in candles],
            "open": [c.open for c in candles],
            "high": [c.high for c in candles],
            "low": [c.low for c in candles],
            "close": [c.close for c in candles],
            "volume": [c.volume for c in candles],
        }
        return pd.DataFrame(data)

    def get_latest_candle(self, timeframe: str = "1m") -> Optional[Candle]:
        candles = self.timeframe_candles.get(timeframe, [])
        return candles[-1] if candles else None

class CandleManager:
    def __init__(self):
        self.stores: Dict[str, SymbolCandleStore] = {}
        self.default_baselines = {
            "EURUSD": 1.08500,
            "GBPUSD": 1.29500,
            "USDJPY": 154.500,
            "XAUUSD": 2500.00,
            "AUDUSD": 0.65500,
            "USDCAD": 1.36500,
            "BTCUSDT": 64500.00,
            "ETHUSDT": 2650.00,
            "SOLUSDT": 145.00
        }

    def get_or_create_store(self, symbol: str) -> SymbolCandleStore:
        sym = symbol.upper().replace("/", "").replace("-", "")
        if sym not in self.stores:
            store = SymbolCandleStore(sym)
            base = self.default_baselines.get(sym, 100.0)
            vol = base * 0.0003
            store.seed_initial_candles(base_price=base, volatility=vol)
            self.stores[sym] = store
        return self.stores[sym]

    def update_tick(self, symbol: str, price: float, volume: float = 1.0, timestamp: Optional[int] = None) -> Tuple[SymbolCandleStore, List[Tuple[str, bool, Candle]]]:
        store = self.get_or_create_store(symbol)
        events = store.update_tick(price, volume, timestamp)
        return store, events

candle_manager = CandleManager()
