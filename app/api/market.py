from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Body
import pandas as pd
from app.engine.candle_manager import candle_manager, TIMEFRAME_SECONDS
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
    symbol: str = Query(..., example="EURUSD"),
    timeframe: str = Query(default="1m", example="1m"),
    limit: int = Query(default=300, le=500)
):
    clean_sym = symbol.upper().replace("/", "").replace("-", "")
    if timeframe not in TIMEFRAME_SECONDS:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Allowed: {list(TIMEFRAME_SECONDS.keys())}")
    
    store = candle_manager.get_or_create_store(clean_sym)
    candles = store.timeframe_candles.get(timeframe, [])
    sliced = candles[-limit:] if len(candles) > limit else candles
    return [c.to_dict() for c in sliced]

@router.get("/indicators")
async def get_indicators(
    symbol: str = Query(..., example="EURUSD"),
    timeframe: str = Query(default="1m", example="1m"),
    ind_type: str = Query(default="ema", example="ema"),
    period: int = Query(default=20),
    output: Optional[str] = Query(default=None)
):
    clean_sym = symbol.upper().replace("/", "").replace("-", "")
    store = candle_manager.get_or_create_store(clean_sym)
    df = store.get_dataframe(timeframe)
    if df.empty:
        return []

    cfg: Dict[str, Any] = {"type": ind_type, "period": period}
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
