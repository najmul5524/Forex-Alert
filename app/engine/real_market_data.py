import logging
import asyncio
import time
from typing import Dict, List, Optional, Any
import httpx
from app.engine.candle_manager import Candle, candle_manager, parse_timeframe_seconds

logger = logging.getLogger(__name__)

YAHOO_SYMBOL_MAP = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "CAD=X",
    "USDCHF": "CHF=X",
    "NZDUSD": "NZDUSD=X",
    "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "USOIL": "CL=F",
    "SPX500": "^GSPC",
    "NAS100": "^IXIC",
    "US30": "^DJI",
}

CRYPTO_SYMBOLS = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"}

class RealMarketDataService:
    @staticmethod
    async def fetch_binance_klines(symbol: str, interval: str = "1h", limit: int = 1000) -> List[Candle]:
        binance_interval = interval
        if interval == "1w":
            binance_interval = "1w"
        elif interval == "1d":
            binance_interval = "1d"
        elif interval == "4h":
            binance_interval = "4h"
        elif interval == "1h":
            binance_interval = "1h"
        elif interval == "15m":
            binance_interval = "15m"
        elif interval == "5m":
            binance_interval = "5m"
        elif interval == "1m":
            binance_interval = "1m"

        url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={binance_interval}&limit={min(1000, limit)}"
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    raw = resp.json()
                    candles = []
                    for row in raw:
                        t_sec = int(row[0]) // 1000
                        o = float(row[1])
                        h = float(row[2])
                        l = float(row[3])
                        c = float(row[4])
                        v = float(row[5])
                        candles.append(Candle(t_sec, o, h, l, c, v))
                    return candles
        except Exception as e:
            logger.debug(f"Binance fetch error for {symbol} ({interval}): {e}")
        return []

    @staticmethod
    async def fetch_yahoo_candles(symbol: str, interval: str = "1d", range_str: str = "2y") -> List[Candle]:
        yahoo_sym = YAHOO_SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}=X")
        y_int = "1d"
        if interval in ["1m", "3m", "5m", "15m", "30m"]:
            y_int = "5m" if interval in ["3m", "5m", "15m", "30m"] else "1m"
            range_str = "5d" if y_int == "1m" else "30d"
        elif interval in ["1h", "2h", "4h"]:
            y_int = "1h"
            range_str = "60d" # 60 days of 1-hour candles (~1,440 candles)
        elif interval == "1d":
            y_int = "1d"
            range_str = "2y"  # 2 years of daily candles (~500 candles)
        elif interval == "1w":
            y_int = "1wk"
            range_str = "5y"  # 5 years of weekly candles (~260 candles)

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_sym}?interval={y_int}&range={range_str}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    chart = data.get("chart", {}).get("result", [])
                    if not chart:
                        return []
                    res0 = chart[0]
                    timestamps = res0.get("timestamp", [])
                    quote = res0.get("indicators", {}).get("quote", [{}])[0]
                    opens = quote.get("open", [])
                    highs = quote.get("high", [])
                    lows = quote.get("low", [])
                    closes = quote.get("close", [])
                    vols = quote.get("volume", [])

                    candles = []
                    for i, ts in enumerate(timestamps):
                        if (i < len(closes) and closes[i] is not None and 
                            i < len(opens) and opens[i] is not None and
                            i < len(highs) and highs[i] is not None and
                            i < len(lows) and lows[i] is not None):
                            v = float(vols[i]) if (i < len(vols) and vols[i] is not None) else 100.0
                            candles.append(Candle(
                                time=int(ts),
                                open=float(opens[i]),
                                high=float(highs[i]),
                                low=float(lows[i]),
                                close=float(closes[i]),
                                volume=v
                            ))
                    return candles
        except Exception as e:
            logger.debug(f"Yahoo Finance fetch error for {symbol} ({interval}): {e}")
        return []

    @classmethod
    async def populate_symbol_real_history(cls, symbol: str):
        sym = symbol.upper().replace("/", "").replace("-", "")
        store = candle_manager.get_or_create_store(sym)

        is_crypto = sym in CRYPTO_SYMBOLS

        if is_crypto:
            for tf in ["1w", "1d", "4h", "1h", "15m", "5m", "1m"]:
                real_bars = await cls.fetch_binance_klines(sym, interval=tf, limit=1000)
                if real_bars and len(real_bars) > 10:
                    store.timeframe_candles[tf] = real_bars[-store.max_bars:]
                    if tf == "1m":
                        store.latest_tick_price = real_bars[-1].close
                        store.prev_tick_price = real_bars[-1].open
            # Fill in 3m, 30m, 45m, 2h from available real bars
            if store.timeframe_candles.get("1m"):
                for extra_tf in ["3m", "30m", "45m"]:
                    if not store.timeframe_candles.get(extra_tf):
                        sec = parse_timeframe_seconds(extra_tf)
                        store.timeframe_candles[extra_tf] = store._aggregate_from_base(store.timeframe_candles["1m"], sec)[-store.max_bars:]
            if store.timeframe_candles.get("1h") and not store.timeframe_candles.get("2h"):
                store.timeframe_candles["2h"] = store._aggregate_from_base(store.timeframe_candles["1h"], 7200)[-store.max_bars:]
        else:
            for tf in ["1w", "1d", "1h"]:
                real_bars = await cls.fetch_yahoo_candles(sym, interval=tf)
                if real_bars and len(real_bars) > 10:
                    store.timeframe_candles[tf] = real_bars[-store.max_bars:]
                    if tf == "1h":
                        store.latest_tick_price = real_bars[-1].close
                        store.prev_tick_price = real_bars[-1].open
                        cls._synthesize_sub_hour_bars(store, real_bars)
            # Synthesize 2h and 4h from 1h bars
            if store.timeframe_candles.get("1h"):
                if not store.timeframe_candles.get("2h"):
                    store.timeframe_candles["2h"] = store._aggregate_from_base(store.timeframe_candles["1h"], 7200)[-store.max_bars:]
                if not store.timeframe_candles.get("4h"):
                    store.timeframe_candles["4h"] = store._aggregate_from_base(store.timeframe_candles["1h"], 14400)[-store.max_bars:]

    @classmethod
    def _synthesize_sub_hour_bars(cls, store, hourly_bars: List[Candle]):
        if not hourly_bars:
            return

        dec = 5
        sym = store.symbol.upper()
        if any(x in sym for x in ["JPY"]):
            dec = 3
        elif any(x in sym for x in ["XAU", "OIL", "BTC", "ETH", "SOL", "BNB", "SPX", "NAS", "US30"]):
            dec = 2
        elif any(x in sym for x in ["XAG", "XRP"]):
            dec = 4

        # Synthesize all standard intraday timeframes
        sub_timeframes = [
            ("45m", 2700, 45),
            ("30m", 1800, 30),
            ("15m", 900, 15),
            ("5m", 300, 5),
            ("3m", 180, 3),
            ("1m", 60, 1),
        ]

        recent_hours = hourly_bars[-25:]

        for sub_tf, sub_sec, num_min in sub_timeframes:
            num_sub = 60 // num_min
            sub_candles: List[Candle] = []

            for h_bar in recent_hours:
                h_start = (h_bar.time // 3600) * 3600
                h_open = h_bar.open
                h_close = h_bar.close
                h_range = abs(h_bar.high - h_bar.low)

                curr_open = h_open
                for step in range(num_sub):
                    step_time = h_start + (step * sub_sec)
                    step_ratio = (step + 1) / float(num_sub)
                    step_target = h_open + (h_close - h_open) * step_ratio
                    step_close = step_target if step == num_sub - 1 else (curr_open + (step_target - curr_open) * 0.9)

                    # Dynamic wick variation bounded by hour bar high/low
                    wick_h = (h_range * 0.05) if h_range > 0 else (h_open * 0.0002)
                    wick_l = (h_range * 0.05) if h_range > 0 else (h_open * 0.0002)

                    sub_h = round(max(curr_open, step_close) + wick_h, dec)
                    sub_l = round(min(curr_open, step_close) - wick_l, dec)
                    sub_o = round(curr_open, dec)
                    sub_c = round(step_close, dec)
                    sub_v = max(10.0, round(h_bar.volume / float(num_sub), 2))

                    sub_candles.append(Candle(step_time, sub_o, sub_h, sub_l, sub_c, sub_v))
                    curr_open = step_close

            store.timeframe_candles[sub_tf] = sub_candles[-store.max_bars:]

real_market_data = RealMarketDataService()
