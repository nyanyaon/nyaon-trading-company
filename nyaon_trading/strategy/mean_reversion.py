from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


@dataclass(frozen=True)
class MRSignal:
    side: Literal["BUY", "SELL"]
    strength: float
    suggested_sl_bps: int
    suggested_tp_bps: int


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def score(df: pd.DataFrame, window: int = 20, sigma: float = 2.0) -> MRSignal | None:
    if len(df) < max(window, 14) + 1:
        return None
    close = df["close"]
    mean = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = mean + sigma * std
    lower = mean - sigma * std
    rsi = _rsi(close)
    last = close.iloc[-1]
    if last < lower.iloc[-1] and rsi.iloc[-1] < 30:
        strength = min(1.0, float((lower.iloc[-1] - last) / max(std.iloc[-1], 1e-9)))
        return MRSignal("BUY", round(strength, 4), suggested_sl_bps=60, suggested_tp_bps=90)
    if last > upper.iloc[-1] and rsi.iloc[-1] > 70:
        strength = min(1.0, float((last - upper.iloc[-1]) / max(std.iloc[-1], 1e-9)))
        return MRSignal("SELL", round(strength, 4), suggested_sl_bps=60, suggested_tp_bps=90)
    return None
