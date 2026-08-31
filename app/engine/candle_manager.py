import time
import math
import random
import re
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

DEFAULT_TIMEFRAME_SECONDS = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "45m": 2700,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "1d": 86400,
    "1w": 604800,
}

TIMEFRAME_SECONDS = DEFAULT_TIMEFRAME_SECONDS

def parse_timeframe_seconds(tf_str: str) -> int:
    tf = tf_str.lower().strip()
    if tf in DEFAULT_TIMEFRAME_SECONDS:
        return DEFAULT_TIMEFRAME_SECONDS[tf]
    
    match = re.match(r"^(\d+)([mhdwd])$", tf)
    if match:
        val, unit = int(match.group(1)), match.group(2)
        if unit == "m": return val * 60
        if unit == "h": return val * 3600
        if unit == "d": return val * 86400
        if unit == "w": return val * 604800
    
    return 60

class Candle:
    def __init__(self, time: int, open: float, high: float, low: float, close: float, volume: float = 0.0):
        self.time = int(time)
        self.open = float(open)
        self.high = float(high)
        self.low = float(low)
        self.close = float(close)
        self.volume = float(volume)

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
    def __init__(self, symbol: str, max_bars: int = 1500):
        self.symbol = symbol
        self.max_bars = max_bars
        self.timeframe_candles: Dict[str, List[Candle]] = {
            tf: [] for tf in DEFAULT_TIMEFRAME_SECONDS
        }
        self.latest_tick_price: Optional[float] = None
        self.prev_tick_price: Optional[float] = None

    def seed_initial_candles(self, base_price: float = 1.0850, volatility: float = 0.0004):
        now = int(time.time())
        total_1m_bars = 1200
        start_time = now - (total_1m_bars * 60)
        curr_price = base_price
        
        cycle_len = 180
        trend_direction = 1.0

        for i in range(total_1m_bars):
            bar_time = start_time + (i * 60)
            
            # Multi-wave sinusoidal trend simulation for realistic charts
            if i % cycle_len == 0:
                trend_direction = random.choice([-1.0, 1.0]) * random.uniform(0.5, 1.5)

            trend_bias = (math.sin(i / 30.0) + math.cos(i / 75.0)) * volatility * 0.4
            noise = (random.random() - 0.498) * volatility
            drift = (trend_direction * volatility * 0.15) + trend_bias + noise

            open_p = curr_price
            close_p = open_p + drift
            
            wick_up = abs(random.random() * volatility * 0.6)
            wick_down = abs(random.random() * volatility * 0.6)
            high_p = max(open_p, close_p) + wick_up
            low_p = min(open_p, close_p) - wick_down
            vol = random.uniform(15.0, 250.0)

            c = Candle(bar_time, open_p, high_p, low_p, close_p, vol)
            self.timeframe_candles["1m"].append(c)
            curr_price = close_p

        self.latest_tick_price = curr_price
        self.prev_tick_price = curr_price

        # Aggregate for all standard higher timeframes
        for tf, sec in DEFAULT_TIMEFRAME_SECONDS.items():
            if tf == "1m":
                continue
            bars_map: Dict[int, Candle] = {}
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

    def get_candles(self, timeframe: str = "1m", limit: int = 500) -> List[Candle]:
        tf = timeframe.lower().strip()
        sec = parse_timeframe_seconds(tf)

        if tf in self.timeframe_candles and self.timeframe_candles[tf]:
            return self.timeframe_candles[tf][-limit:]

        # On-the-fly dynamic aggregation for custom arbitrary timeframes (e.g. 7m, 3h)
        base_1m = self.timeframe_candles.get("1m", [])
        if not base_1m:
            return []

        bars_map: Dict[int, Candle] = {}
        for c in base_1m:
            bucket = (c.time // sec) * sec
            if bucket not in bars_map:
                bars_map[bucket] = Candle(bucket, c.open, c.high, c.low, c.close, c.volume)
            else:
                b = bars_map[bucket]
                b.high = max(b.high, c.high)
                b.low = min(b.low, c.low)
                b.close = c.close
                b.volume += c.volume
        
        aggregated = list(bars_map.values())
        self.timeframe_candles[tf] = aggregated
        return aggregated[-limit:]

    def update_tick(self, price: float, volume: float = 1.0, timestamp: Optional[int] = None) -> List[Tuple[str, bool, Candle]]:
        if timestamp is None:
            timestamp = int(time.time())

        self.prev_tick_price = self.latest_tick_price
        self.latest_tick_price = price

        events = []

        for tf, sec in list(DEFAULT_TIMEFRAME_SECONDS.items()):
            bucket_time = (timestamp // sec) * sec
            candles = self.timeframe_candles.setdefault(tf, [])

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
            elif bucket_time > last_c.time:
                events.append((tf, True, last_c)) # Bar close event
                new_c = Candle(bucket_time, price, price, price, price, volume)
                candles.append(new_c)
                if len(candles) > self.max_bars:
                    candles.pop(0)
                events.append((tf, False, new_c))

        return events

    def get_latest_candle(self, timeframe: str = "1m") -> Optional[Candle]:
        candles = self.get_candles(timeframe, limit=1)
        return candles[-1] if candles else None

    def get_dataframe(self, timeframe: str = "1m", limit: int = 500) -> pd.DataFrame:
        candles = self.get_candles(timeframe, limit=limit)
        if not candles:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        
        data = [{
            "time": c.time,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume
        } for c in candles]
        
        df = pd.DataFrame(data)
        df["datetime"] = pd.to_datetime(df["time"], unit="s")
        return df

class CandleManager:
    def __init__(self):
        self.stores: Dict[str, SymbolCandleStore] = {}

    def get_or_create_store(self, symbol: str) -> SymbolCandleStore:
        sym = symbol.upper().replace("/", "").replace("-", "")
        if sym not in self.stores:
            store = SymbolCandleStore(sym)
            base_p = 1.0850
            vol = 0.0004
            if "USD" in sym and "JPY" in sym:
                base_p = 154.50
                vol = 0.06
            elif "XAU" in sym:
                base_p = 2500.0
                vol = 1.2
            elif "BTC" in sym:
                base_p = 64500.0
                vol = 35.0
            elif "ETH" in sym:
                base_p = 2650.0
                vol = 2.5
            elif "SOL" in sym:
                base_p = 145.0
                vol = 0.25
            store.seed_initial_candles(base_p, vol)
            self.stores[sym] = store
        return self.stores[sym]

    def update_tick(self, symbol: str, price: float, volume: float = 1.0, timestamp: Optional[int] = None) -> Tuple[SymbolCandleStore, List[Tuple[str, bool, Candle]]]:
        store = self.get_or_create_store(symbol)
        events = store.update_tick(price, volume, timestamp)
        return store, events

candle_manager = CandleManager()
