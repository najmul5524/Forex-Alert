import datetime
from typing import Dict, Any, Optional
import pandas as pd
from app.engine.indicators import calculate_indicator_value

class RuleEvaluationResult:
    def __init__(self, triggered: bool, summary: str = "", current_val: float = 0.0, target_val: float = 0.0, should_deactivate: bool = False):
        self.triggered = triggered
        self.summary = summary
        self.current_val = current_val
        self.target_val = target_val
        self.should_deactivate = should_deactivate

def can_trigger_now(
    trigger_frequency: str,
    cooldown_minutes: int,
    last_triggered_at: Optional[datetime.datetime],
    last_evaluated_bar_time: Optional[int],
    current_bar_time: int,
    is_bar_close: bool
) -> bool:
    now = datetime.datetime.utcnow()

    if trigger_frequency == "once_per_bar_close" and not is_bar_close:
        return False

    if trigger_frequency in ("once_per_bar", "once_per_bar_close"):
        if last_evaluated_bar_time == current_bar_time:
            return False

    if trigger_frequency == "every_time" and last_triggered_at:
        elapsed = (now - last_triggered_at).total_seconds() / 60.0
        if elapsed < cooldown_minutes:
            return False

    return True

def evaluate_alert_condition(
    alert_dict: Dict[str, Any],
    candles_df: Optional[pd.DataFrame],
    prev_tick_price: Optional[float],
    current_price: float,
    current_bar_time: int,
    is_bar_close: bool
) -> RuleEvaluationResult:
    condition_type = alert_dict.get("condition_type", "")
    params = alert_dict.get("params", {})
    symbol = alert_dict.get("symbol", "")
    timeframe = alert_dict.get("timeframe", "1m")
    freq = alert_dict.get("trigger_frequency", "only_once")
    cooldown = alert_dict.get("cooldown_minutes", 5)
    last_trig = alert_dict.get("last_triggered_at")
    last_bar = alert_dict.get("last_evaluated_bar_time")

    if not can_trigger_now(freq, cooldown, last_trig, last_bar, current_bar_time, is_bar_close):
        return RuleEvaluationResult(triggered=False)

    if candles_df is None or len(candles_df) < 2:
        prev_p = prev_tick_price if prev_tick_price is not None else current_price
    else:
        prev_p = prev_tick_price if prev_tick_price is not None else float(candles_df["close"].iloc[-2])

    curr_p = current_price

    if condition_type == "price_cross_up":
        target = float(params.get("target_price", 0.0))
        if prev_p <= target and curr_p > target:
            summary = f"{symbol} crossed ABOVE {target:.5f} (Current: {curr_p:.5f})"
            return RuleEvaluationResult(
                triggered=True,
                summary=summary,
                current_val=curr_p,
                target_val=target,
                should_deactivate=(freq == "only_once")
            )

    elif condition_type == "price_cross_down":
        target = float(params.get("target_price", 0.0))
        if prev_p >= target and curr_p < target:
            summary = f"{symbol} crossed BELOW {target:.5f} (Current: {curr_p:.5f})"
            return RuleEvaluationResult(
                triggered=True,
                summary=summary,
                current_val=curr_p,
                target_val=target,
                should_deactivate=(freq == "only_once")
            )

    elif condition_type == "price_greater":
        target = float(params.get("target_price", 0.0))
        if curr_p >= target:
            summary = f"{symbol} is GREATER than {target:.5f} (Current: {curr_p:.5f})"
            return RuleEvaluationResult(
                triggered=True,
                summary=summary,
                current_val=curr_p,
                target_val=target,
                should_deactivate=(freq == "only_once")
            )

    elif condition_type == "price_less":
        target = float(params.get("target_price", 0.0))
        if curr_p <= target:
            summary = f"{symbol} is LESS than {target:.5f} (Current: {curr_p:.5f})"
            return RuleEvaluationResult(
                triggered=True,
                summary=summary,
                current_val=curr_p,
                target_val=target,
                should_deactivate=(freq == "only_once")
            )

    elif condition_type == "price_cross_indicator":
        ind_cfg = params.get("indicator", {})
        direction = params.get("direction", "above")
        if candles_df is not None and len(candles_df) >= 2:
            ind_series = calculate_indicator_value(candles_df, ind_cfg)
            prev_ind = float(ind_series.iloc[-2])
            curr_ind = float(ind_series.iloc[-1])
            prev_candle_p = float(candles_df["close"].iloc[-2])
            curr_candle_p = curr_p

            ind_name = f"{ind_cfg.get('type', '').upper()} ({ind_cfg.get('period', '')})"
            
            if direction in ("above", "up", "cross_up"):
                if prev_candle_p <= prev_ind and curr_candle_p > curr_ind:
                    summary = f"{symbol} price ({curr_candle_p:.5f}) crossed ABOVE {ind_name} ({curr_ind:.5f})"
                    return RuleEvaluationResult(
                        triggered=True,
                        summary=summary,
                        current_val=curr_candle_p,
                        target_val=curr_ind,
                        should_deactivate=(freq == "only_once")
                    )
            else:
                if prev_candle_p >= prev_ind and curr_candle_p < curr_ind:
                    summary = f"{symbol} price ({curr_candle_p:.5f}) crossed BELOW {ind_name} ({curr_ind:.5f})"
                    return RuleEvaluationResult(
                        triggered=True,
                        summary=summary,
                        current_val=curr_candle_p,
                        target_val=curr_ind,
                        should_deactivate=(freq == "only_once")
                    )

    elif condition_type == "indicator_cross_indicator":
        ind1_cfg = params.get("indicator_1", {})
        ind2_cfg = params.get("indicator_2", {})
        direction = params.get("direction", "above")

        if candles_df is not None and len(candles_df) >= 2:
            ind1_series = calculate_indicator_value(candles_df, ind1_cfg)
            ind2_series = calculate_indicator_value(candles_df, ind2_cfg)

            prev_i1 = float(ind1_series.iloc[-2])
            curr_i1 = float(ind1_series.iloc[-1])
            prev_i2 = float(ind2_series.iloc[-2])
            curr_i2 = float(ind2_series.iloc[-1])

            name1 = f"{ind1_cfg.get('type', '').upper()}({ind1_cfg.get('period', '')})"
            name2 = f"{ind2_cfg.get('type', '').upper()}({ind2_cfg.get('period', '')})"

            if direction in ("above", "up", "cross_up"):
                if prev_i1 <= prev_i2 and curr_i1 > curr_i2:
                    summary = f"{symbol} {name1} ({curr_i1:.4f}) crossed ABOVE {name2} ({curr_i2:.4f})"
                    return RuleEvaluationResult(
                        triggered=True,
                        summary=summary,
                        current_val=curr_i1,
                        target_val=curr_i2,
                        should_deactivate=(freq == "only_once")
                    )
            else:
                if prev_i1 >= prev_i2 and curr_i1 < curr_i2:
                    summary = f"{symbol} {name1} ({curr_i1:.4f}) crossed BELOW {name2} ({curr_i2:.4f})"
                    return RuleEvaluationResult(
                        triggered=True,
                        summary=summary,
                        current_val=curr_i1,
                        target_val=curr_i2,
                        should_deactivate=(freq == "only_once")
                    )

    elif condition_type == "indicator_cross_value":
        ind_cfg = params.get("indicator", {})
        threshold = float(params.get("threshold", 70.0))
        direction = params.get("direction", "above")

        if candles_df is not None and len(candles_df) >= 2:
            ind_series = calculate_indicator_value(candles_df, ind_cfg)
            prev_ind = float(ind_series.iloc[-2])
            curr_ind = float(ind_series.iloc[-1])

            ind_name = f"{ind_cfg.get('type', '').upper()} ({ind_cfg.get('period', '')})"

            if direction in ("above", "up", "cross_up"):
                if prev_ind <= threshold and curr_ind > threshold:
                    summary = f"{symbol} {ind_name} ({curr_ind:.2f}) crossed ABOVE {threshold:.2f}"
                    return RuleEvaluationResult(
                        triggered=True,
                        summary=summary,
                        current_val=curr_ind,
                        target_val=threshold,
                        should_deactivate=(freq == "only_once")
                    )
            else:
                if prev_ind >= threshold and curr_ind < threshold:
                    summary = f"{symbol} {ind_name} ({curr_ind:.2f}) crossed BELOW {threshold:.2f}"
                    return RuleEvaluationResult(
                        triggered=True,
                        summary=summary,
                        current_val=curr_ind,
                        target_val=threshold,
                        should_deactivate=(freq == "only_once")
                    )

    elif condition_type == "channel_exit":
        lower = float(params.get("lower_bound", 0.0))
        upper = float(params.get("upper_bound", 0.0))
        if curr_p < lower or curr_p > upper:
            summary = f"{symbol} EXITED channel [{lower:.5f}, {upper:.5f}] at {curr_p:.5f}"
            return RuleEvaluationResult(
                triggered=True,
                summary=summary,
                current_val=curr_p,
                target_val=upper if curr_p > upper else lower,
                should_deactivate=(freq == "only_once")
            )

    elif condition_type == "channel_enter":
        lower = float(params.get("lower_bound", 0.0))
        upper = float(params.get("upper_bound", 0.0))
        if prev_p < lower or prev_p > upper:
            if lower <= curr_p <= upper:
                summary = f"{symbol} ENTERED channel [{lower:.5f}, {upper:.5f}] at {curr_p:.5f}"
                return RuleEvaluationResult(
                    triggered=True,
                    summary=summary,
                    current_val=curr_p,
                    target_val=curr_p,
                    should_deactivate=(freq == "only_once")
                )

    return RuleEvaluationResult(triggered=False)
