from pathlib import Path

from nyaon_trading.binance.market import load_fixture
from nyaon_trading.strategy.trend import score


def test_trend_score_uptrend_returns_buy_signal():
    df = load_fixture(Path("tests/unit/fixtures/klines_btc_15m.json"))
    s = score(df, ema_fast=10, ema_slow=30)
    assert s is not None
    assert s.side == "BUY"
    assert 0 < s.strength <= 1


def test_trend_score_needs_min_bars():
    df = load_fixture(Path("tests/unit/fixtures/klines_btc_15m.json")).iloc[:10]
    s = score(df)
    assert s is None
