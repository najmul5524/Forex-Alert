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
    def __init__(self, symbol: str, max_bars: int = 20000):
        self.symbol = symbol
        self.max_bars = max_bars
        self.timeframe_candles: Dict[str, List[Candle]] = {
            tf: [] for tf in DEFAULT_TIMEFRAME_SECONDS
        }
        self.latest_tick_price: Optional[float] = None
        self.prev_tick_price: Optional[float] = None

    def seed_initial_candles(self, base_price: float = 1.0850, volatility: float = 0.0004):
        now = int(time.time())

        # Timeframe-specific historical depth (1 Year+ for 1h, 4h, 1d, 1w)
        tf_depths = {
            "1w": (320, 604800, volatility * 5.0),    # 320 weeks (~6.1 years)
            "1d": (1200, 86400, volatility * 3.0),    # 1200 days (~3.3 years)
            "4h": (3000, 14400, volatility * 1.8),    # 3000 4h bars (~1.37 years)
            "2h": (4000, 7200, volatility * 1.4),     # 4000 2h bars (~1.0 years)
            "1h": (9000, 3600, volatility * 1.2),     # 9000 1h bars (~1.03 years / 375 days)
            "45m": (2500, 2700, volatility * 1.1),    # 2500 45m bars (~78 days)
            "30m": (3500, 1800, volatility * 1.0),    # 3500 30m bars (~73 days)
            "15m": (3500, 900, volatility * 0.8),     # 3500 15m bars (~36 days)
            "5m": (3500, 300, volatility * 0.6),      # 3500 5m bars (~12 days)
            "3m": (3500, 180, volatility * 0.5),      # 3500 3m bars (~7 days)
            "1m": (3500, 60, volatility * 0.4),       # 3500 1m bars (~2.4 days)
        }

        for tf, (num_bars, sec, tf_vol) in tf_depths.items():
            start_time = (now // sec) * sec - (num_bars * sec)
            curr_p = base_price * (1.0 + (random.uniform(-0.03, 0.03)))
            candles_list: List[Candle] = []

            cycle_len = max(30, num_bars // 20)
            trend = random.choice([-1.0, 1.0])

            for i in range(num_bars):
                bar_time = start_time + (i * sec)
                if i % cycle_len == 0:
                    trend = random.choice([-1.0, 1.0]) * random.uniform(0.7, 1.3)

                # Mean reversion back towards base_price near the end
                progress = i / float(num_bars)
                mean_pull = (base_price - curr_p) * 0.015 * (progress ** 2)

                drift = (trend * tf_vol * 0.2) + mean_pull + ((random.random() - 0.495) * tf_vol)
                open_p = curr_p
                close_p = open_p + drift

                wick_up = abs(random.random() * tf_vol * 0.7)
                wick_down = abs(random.random() * tf_vol * 0.7)
                high_p = max(open_p, close_p) + wick_up
                low_p = min(open_p, close_p) - wick_down
                vol = random.uniform(20.0, 500.0)

                candles_list.append(Candle(bar_time, open_p, high_p, low_p, close_p, vol))
                curr_p = close_p

            # Ensure the very last bar ends right at base_price
            if candles_list:
                candles_list[-1].close = base_price
                candles_list[-1].high = max(candles_list[-1].high, base_price)
                candles_list[-1].low = min(candles_list[-1].low, base_price)

            self.timeframe_candles[tf] = candles_list

        self.latest_tick_price = base_price
        self.prev_tick_price = base_price

    def get_candles(
        self, 
        timeframe: str = "1m", 
        limit: int = 5000, 
        to_time: Optional[int] = None, 
        from_time: Optional[int] = None
    ) -> List[Candle]:
        tf = timeframe.lower().strip()
        sec = parse_timeframe_seconds(tf)

        candles = self.timeframe_candles.get(tf, [])
        if not candles and tf not in DEFAULT_TIMEFRAME_SECONDS:
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
            candles = list(bars_map.values())
            self.timeframe_candles[tf] = candles

        if to_time is not None:
            candles = [c for c in candles if c.time < to_time]
        if from_time is not None:
            candles = [c for c in candles if c.time >= from_time]

        if limit <= 0 or limit >= len(candles):
            return candles
        return candles[-limit:]

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

    def get_or_create_store(self, symbol: str, custom_base_price: Optional[float] = None) -> SymbolCandleStore:
        sym = symbol.upper().replace("/", "").replace("-", "")
        if sym not in self.stores:
            store = SymbolCandleStore(sym)
            base_p = custom_base_price or 1.0850
            vol = 0.0004

            price_map = {
                "EURUSD": (1.1596, 0.0004),
                "GBPUSD": (1.3545, 0.0005),
                "USDJPY": (160.04, 0.06),
                "AUDUSD": (0.7164, 0.0004),
                "USDCAD": (1.3892, 0.0005),
                "USDCHF": (0.8081, 0.0004),
                "NZDUSD": (0.5980, 0.0004),
                "EURGBP": (0.8380, 0.0003),
                "EURJPY": (185.60, 0.08),
                "GBPJPY": (216.80, 0.10),
                "XAUUSD": (4432.0, 1.8),
                "XAGUSD": (54.20, 0.08),
                "USOIL": (78.50, 0.15),
                "SPX500": (5650.0, 4.0),
                "NAS100": (19800.0, 15.0),
                "US30": (41500.0, 30.0),
                "BTCUSDT": (78800.0, 50.0),
                "ETHUSDT": (2650.0, 2.5),
                "SOLUSDT": (145.0, 0.25),
                "BNBUSDT": (540.0, 0.6),
                "XRPUSDT": (0.585, 0.001)
            }

            if sym in price_map:
                base_p, vol = price_map[sym]
            elif "XAU" in sym:
                base_p, vol = 4432.0, 1.8
            elif "BTC" in sym:
                base_p, vol = 78800.0, 50.0

            if custom_base_price is not None:
                base_p = custom_base_price

            store.seed_initial_candles(base_p, vol)
            self.stores[sym] = store
        return self.stores[sym]

    def update_tick(self, symbol: str, price: float, volume: float = 1.0, timestamp: Optional[int] = None) -> Tuple[SymbolCandleStore, List[Tuple[str, bool, Candle]]]:
        store = self.get_or_create_store(symbol)
        events = store.update_tick(price, volume, timestamp)
        return store, events

candle_manager = CandleManager()
