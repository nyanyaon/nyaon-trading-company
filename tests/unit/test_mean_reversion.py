import numpy as np
import pandas as pd

from nyaon_trading.strategy.mean_reversion import score


def _frame(closes: list[float]) -> pd.DataFrame:
    n = len(closes)
    return pd.DataFrame({
        "open_time": pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC"),
        "open": closes,
        "high": [c + 1 for c in closes],
        "low": [c - 1 for c in closes],
        "close": closes,
        "volume": [100.0] * n,
    })


def test_mean_reversion_buy_on_lower_band_with_oversold_rsi():
    base = [100.0] * 30
    crash = list(np.linspace(100, 80, 10))
    df = _frame(base + crash)
    s = score(df)
    assert s is not None
    assert s.side == "BUY"


def test_mean_reversion_no_signal_when_in_band():
    df = _frame([100.0 + (i % 3 - 1) * 0.1 for i in range(40)])
    s = score(df)
    assert s is None
