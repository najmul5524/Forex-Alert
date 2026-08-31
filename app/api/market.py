from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Body
import pandas as pd
from app.engine.candle_manager import candle_manager, parse_timeframe_seconds
from app.engine.market_feed import SUPPORTED_SYMBOLS, market_feed
from app.engine.indicators import calculate_indicator_value

router = APIRouter(prefix="/api/market", tags=["Market Data"])

@router.get("/symbols")
async def get_supported_symbols():
    symbols_with_prices = []
    for s in SUPPORTED_SYMBOLS:
        sym = s["symbol"]
        store = candle_manager.get_or_create_store(sym)
        price = store.latest_tick_price or s["base_price"]
        symbols_with_prices.append({
            **s,
            "current_price": price
        })
    return symbols_with_prices

@router.get("/candles")
async def get_candles(
    symbol: str = Query(...),
    timeframe: str = Query(default="1m"),
    limit: int = Query(default=10000, le=50000)
):
    clean_sym = symbol.upper().replace("/", "").replace("-", "")
    store = candle_manager.get_or_create_store(clean_sym)
    candles = store.get_candles(timeframe, limit=limit)
    return [c.to_dict() for c in candles]

@router.get("/indicators")
async def get_indicators(
    symbol: str = Query(...),
    timeframe: str = Query(default="1m"),
    ind_type: str = Query(default="ema"),
    period: int = Query(default=20),
    source: str = Query(default="close"),
    std_dev: float = Query(default=2.0),
    fast: int = Query(default=12),
    slow: int = Query(default=26),
    signal: int = Query(default=9),
    k_period: int = Query(default=14),
    d_period: int = Query(default=3),
    smooth_k: int = Query(default=3),
    output: Optional[str] = Query(default=None)
):
    clean_sym = symbol.upper().replace("/", "").replace("-", "")
    store = candle_manager.get_or_create_store(clean_sym)
    df = store.get_dataframe(timeframe, limit=5000)
    if df.empty:
        return []

    cfg: Dict[str, Any] = {
        "type": ind_type,
        "period": period,
        "source": source,
        "std_dev": std_dev,
        "fast": fast,
        "slow": slow,
        "signal": signal,
        "k_period": k_period,
        "d_period": d_period,
        "smooth_k": smooth_k,
    }
    if output:
        cfg["output"] = output
    
    series = calculate_indicator_value(df, cfg)
    result = []
    for t, val in zip(df["time"], series):
        if not pd.isna(val):
            result.append({"time": int(t), "value": round(float(val), 5)})
    return result

@router.post("/tick-override")
async def override_tick(payload: Dict[str, Any] = Body(...)):
    sym = payload.get("symbol", "EURUSD")
    price = float(payload.get("price", 1.0850))
    await market_feed.process_tick(sym, price)
    return {"status": "ok", "symbol": sym, "injected_price": price}
