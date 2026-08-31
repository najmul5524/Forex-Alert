import pytest
import pandas as pd
import numpy as np
from app.engine.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_stochastic,
    calculate_indicator_value
)

def test_sma_calculation():
    series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    sma = calculate_sma(series, 3)
    assert len(sma) == 5
    assert sma.iloc[-1] == pytest.approx(40.0)

def test_ema_calculation():
    series = pd.Series([10.0, 12.0, 14.0, 16.0, 18.0])
    ema = calculate_ema(series, 3)
    assert len(ema) == 5
    assert ema.iloc[-1] > 16.0

def test_rsi_calculation():
    prices = [100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 106.0, 108.0, 110.0, 112.0, 111.0, 113.0, 115.0, 117.0, 119.0, 121.0]
    series = pd.Series(prices)
    rsi = calculate_rsi(series, period=14)
    assert len(rsi) == len(prices)
    assert rsi.iloc[-1] > 50.0

def test_macd_calculation():
    prices = [100.0 + i + (i % 3) for i in range(40)]
    series = pd.Series(prices, dtype=float)
    macd_l, sig_l, hist = calculate_macd(series, 12, 26, 9)
    assert len(macd_l) == 40
    assert len(sig_l) == 40
    assert len(hist) == 40

def test_bollinger_bands():
    prices = [100.0 + np.sin(i) * 5 for i in range(30)]
    series = pd.Series(prices, dtype=float)
    upper, mid, lower = calculate_bollinger_bands(series, period=20, std_dev=2.0)
    assert upper.iloc[-1] > mid.iloc[-1]
    assert lower.iloc[-1] < mid.iloc[-1]

def test_indicator_value_helper():
    df = pd.DataFrame({
        "time": list(range(30)),
        "open": [100.0 + i for i in range(30)],
        "high": [102.0 + i for i in range(30)],
        "low": [99.0 + i for i in range(30)],
        "close": [101.0 + i for i in range(30)],
        "volume": [1000.0 for _ in range(30)]
    })

    ema_series = calculate_indicator_value(df, {"type": "ema", "period": 10})
    assert len(ema_series) == 30
    assert ema_series.iloc[-1] > 120.0
