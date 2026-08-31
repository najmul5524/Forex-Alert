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
    elif ind_type in ("hma", "hull"):
        period = int(indicator_cfg.get("period", 20))
        return calculate_hma(source, period)
    elif ind_type == "vwap":
        return calculate_vwap(df)
    elif ind_type == "supertrend":
        period = int(indicator_cfg.get("period", 10))
        multiplier = float(indicator_cfg.get("multiplier", 3.0))
        return calculate_supertrend(df, period, multiplier)
    else:
        return calculate_ema(source, 20)

def calculate_hma(series: pd.Series, period: int = 20) -> pd.Series:
    half_period = int(period / 2)
    sqrt_period = int(np.sqrt(period))
    wma_half = calculate_wma(series, half_period)
    wma_full = calculate_wma(series, period)
    diff = 2 * wma_half - wma_full
    return calculate_wma(diff, sqrt_period)

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
    vol = df.get("volume", pd.Series(1.0, index=df.index))
    cum_vol_price = (typical_price * vol).cumsum()
    cum_vol = vol.cumsum()
    return cum_vol_price / cum_vol.replace(0, 1.0)

def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    atr = calculate_atr(df["high"], df["low"], df["close"], period)
    hl2 = (df["high"] + df["low"]) / 2.0
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    supertrend = pd.Series(index=df.index, dtype=float)
    in_uptrend = True
    
    for i in range(len(df)):
        if i == 0:
            supertrend.iloc[i] = lower_band.iloc[i]
            continue
        c = df["close"].iloc[i]
        prev_st = supertrend.iloc[i-1]
        
        if c > prev_st:
            in_uptrend = True
        elif c < prev_st:
            in_uptrend = False
            
        if in_uptrend:
            supertrend.iloc[i] = max(lower_band.iloc[i], prev_st) if in_uptrend else lower_band.iloc[i]
        else:
            supertrend.iloc[i] = min(upper_band.iloc[i], prev_st) if not in_uptrend else upper_band.iloc[i]
            
    return supertrend

def calculate_heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    ha_df = pd.DataFrame(index=df.index)
    ha_close = (df["open"] + df["high"] + df["low"] + df["close"]) / 4.0
    ha_open = pd.Series(index=df.index, dtype=float)
    
    for i in range(len(df)):
        if i == 0:
            ha_open.iloc[i] = (df["open"].iloc[i] + df["close"].iloc[i]) / 2.0
        else:
            ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2.0
            
    ha_high = pd.concat([df["high"], ha_open, ha_close], axis=1).max(axis=1)
    ha_low = pd.concat([df["low"], ha_open, ha_close], axis=1).min(axis=1)
    
    ha_df["time"] = df["time"]
    ha_df["open"] = ha_open
    ha_df["high"] = ha_high
    ha_df["low"] = ha_low
    ha_df["close"] = ha_close
    ha_df["volume"] = df.get("volume", 1.0)
    return ha_df
