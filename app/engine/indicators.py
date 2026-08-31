import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

def get_source_series(df: pd.DataFrame, source: str = "close") -> pd.Series:
    src = source.lower().strip()
    if src == "open" and "open" in df.columns: return df["open"]
    if src == "high" and "high" in df.columns: return df["high"]
    if src == "low" and "low" in df.columns: return df["low"]
    if src == "hl2" and "high" in df.columns and "low" in df.columns:
        return (df["high"] + df["low"]) / 2.0
    if src == "hlc3" and "high" in df.columns and "low" in df.columns and "close" in df.columns:
        return (df["high"] + df["low"] + df["close"]) / 3.0
    if src == "ohlc4" and "open" in df.columns and "high" in df.columns and "low" in df.columns and "close" in df.columns:
        return (df["open"] + df["high"] + df["low"] + df["close"]) / 4.0
    return df["close"] if "close" in df.columns else pd.Series(dtype=float)

def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=1).mean()

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def calculate_wma(series: pd.Series, period: int) -> pd.Series:
    weights = np.arange(1, period + 1)
    def wma_calc(window):
        if len(window) < period:
            w = np.arange(1, len(window) + 1)
            return np.dot(window, w) / w.sum()
        return np.dot(window, weights) / weights.sum()
    return series.rolling(window=period, min_periods=1).apply(wma_calc, raw=True)

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    fast_ema = calculate_ema(series, fast)
    slow_ema = calculate_ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    middle = calculate_sma(series, period)
    std = series.rolling(window=period, min_periods=1).std().fillna(0)
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean().fillna(0)

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3, smooth_k: int = 3) -> Tuple[pd.Series, pd.Series]:
    lowest_low = low.rolling(window=k_period, min_periods=1).min()
    highest_high = high.rolling(window=k_period, min_periods=1).max()
    raw_k = 100 * ((close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan))
    raw_k = raw_k.fillna(50.0)
    k = calculate_sma(raw_k, smooth_k)
    d = calculate_sma(k, d_period)
    return k, d

def calculate_indicator_value(df: pd.DataFrame, indicator_cfg: Dict[str, Any]) -> pd.Series:
    ind_type = indicator_cfg.get("type", "ema").lower()
    source_name = indicator_cfg.get("source", "close")
    source = get_source_series(df, source_name)

    if ind_type == "sma":
        period = int(indicator_cfg.get("period", 20))
        return calculate_sma(source, period)
    elif ind_type == "ema":
        period = int(indicator_cfg.get("period", 20))
        return calculate_ema(source, period)
    elif ind_type == "wma":
        period = int(indicator_cfg.get("period", 20))
        return calculate_wma(source, period)
    elif ind_type == "rsi":
        period = int(indicator_cfg.get("period", 14))
        return calculate_rsi(source, period)
    elif ind_type == "macd":
        fast = int(indicator_cfg.get("fast", 12))
        slow = int(indicator_cfg.get("slow", 26))
        signal = int(indicator_cfg.get("signal", 9))
        output = indicator_cfg.get("output", "macd").lower()
        macd_l, sig_l, hist = calculate_macd(source, fast, slow, signal)
        if output == "signal":
            return sig_l
        elif output in ("hist", "histogram"):
            return hist
        return macd_l
    elif ind_type in ("bollinger", "bb"):
        period = int(indicator_cfg.get("period", 20))
        std_dev = float(indicator_cfg.get("std_dev", 2.0))
        output = indicator_cfg.get("output", "upper").lower()
        upper, mid, lower = calculate_bollinger_bands(source, period, std_dev)
        if output == "lower":
            return lower
        elif output in ("middle", "mid"):
            return mid
        return upper
    elif ind_type == "atr":
        period = int(indicator_cfg.get("period", 14))
        return calculate_atr(df["high"], df["low"], df["close"], period)
    elif ind_type in ("stochastic", "stoch"):
        k_period = int(indicator_cfg.get("k_period", 14))
        d_period = int(indicator_cfg.get("d_period", 3))
        smooth_k = int(indicator_cfg.get("smooth_k", 3))
        output = indicator_cfg.get("output", "k").lower()
        k, d = calculate_stochastic(df["high"], df["low"], df["close"], k_period, d_period, smooth_k)
        return d if output == "d" else k
    else:
        return calculate_ema(source, 20)
