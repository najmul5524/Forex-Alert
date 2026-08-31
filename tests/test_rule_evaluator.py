import pytest
import pandas as pd
from app.engine.rule_evaluator import evaluate_alert_condition, can_trigger_now

def test_price_cross_up():
    alert = {
        "symbol": "EURUSD",
        "timeframe": "1m",
        "condition_type": "price_cross_up",
        "params": {"target_price": 1.08500},
        "trigger_frequency": "only_once"
    }

    result = evaluate_alert_condition(
        alert_dict=alert,
        candles_df=None,
        prev_tick_price=1.08490,
        current_price=1.08510,
        current_bar_time=1000,
        is_bar_close=False
    )
    assert result.triggered is True
    assert result.should_deactivate is True
    assert "crossed ABOVE" in result.summary

    result_no = evaluate_alert_condition(
        alert_dict=alert,
        candles_df=None,
        prev_tick_price=1.08520,
        current_price=1.08530,
        current_bar_time=1000,
        is_bar_close=False
    )
    assert result_no.triggered is False

def test_price_cross_down():
    alert = {
        "symbol": "EURUSD",
        "timeframe": "1m",
        "condition_type": "price_cross_down",
        "params": {"target_price": 1.08500},
        "trigger_frequency": "only_once"
    }

    result = evaluate_alert_condition(
        alert_dict=alert,
        candles_df=None,
        prev_tick_price=1.08510,
        current_price=1.08490,
        current_bar_time=1000,
        is_bar_close=False
    )
    assert result.triggered is True
    assert "crossed BELOW" in result.summary

def test_channel_exit():
    alert = {
        "symbol": "BTCUSDT",
        "timeframe": "5m",
        "condition_type": "channel_exit",
        "params": {"lower_bound": 60000.0, "upper_bound": 65000.0},
        "trigger_frequency": "only_once"
    }

    result = evaluate_alert_condition(
        alert_dict=alert,
        candles_df=None,
        prev_tick_price=64000.0,
        current_price=65500.0,
        current_bar_time=1000,
        is_bar_close=False
    )
    assert result.triggered is True
    assert "EXITED channel" in result.summary

def test_indicator_cross_indicator():
    # 20 flat bars at 100, then sudden spike on last bar causing 3-EMA to cross above 10-EMA
    prices = [100.0] * 25 + [100.0, 115.0]
    df = pd.DataFrame({
        "time": list(range(len(prices))),
        "open": prices,
        "high": [p + 1.0 for p in prices],
        "low": [p - 1.0 for p in prices],
        "close": prices,
        "volume": [100.0] * len(prices)
    })

    alert = {
        "symbol": "EURUSD",
        "timeframe": "1m",
        "condition_type": "indicator_cross_indicator",
        "params": {
            "indicator_1": {"type": "ema", "period": 3},
            "indicator_2": {"type": "ema", "period": 10},
            "direction": "above"
        },
        "trigger_frequency": "only_once"
    }

    result = evaluate_alert_condition(
        alert_dict=alert,
        candles_df=df,
        prev_tick_price=prices[-2],
        current_price=prices[-1],
        current_bar_time=1000,
        is_bar_close=False
    )
    assert result.triggered is True
    assert "crossed ABOVE" in result.summary

def test_frequency_bar_close():
    can_trig = can_trigger_now(
        trigger_frequency="once_per_bar_close",
        cooldown_minutes=5,
        last_triggered_at=None,
        last_evaluated_bar_time=None,
        current_bar_time=1000,
        is_bar_close=False
    )
    assert can_trig is False

    can_trig_close = can_trigger_now(
        trigger_frequency="once_per_bar_close",
        cooldown_minutes=5,
        last_triggered_at=None,
        last_evaluated_bar_time=None,
        current_bar_time=1000,
        is_bar_close=True
    )
    assert can_trig_close is True
