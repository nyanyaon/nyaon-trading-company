from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


@dataclass(frozen=True)
class TrendSignal:
    side: Literal["BUY", "SELL"]
    strength: float
    suggested_sl_bps: int
    suggested_tp_bps: int


def score(
    df: pd.DataFrame, donchian: int = 20, ema_fast: int = 50, ema_slow: int = 200
) -> TrendSignal | None:
    if len(df) < max(donchian, ema_slow):
        return None
    close = df["close"]
    high = df["high"]
    low = df["low"]
    upper = high.iloc[-donchian:-1].max()
    lower = low.iloc[-donchian:-1].min()
    ef = close.ewm(span=ema_fast, adjust=False).mean().iloc[-1]
    es = close.ewm(span=ema_slow, adjust=False).mean().iloc[-1]
    last = close.iloc[-1]
    if last > upper and ef > es:
        strength = min(1.0, (last - upper) / max(upper - lower, 1e-9))
        return TrendSignal("BUY", round(strength, 4), suggested_sl_bps=80, suggested_tp_bps=160)
    if last < lower and ef < es:
        strength = min(1.0, (lower - last) / max(upper - lower, 1e-9))
        return TrendSignal("SELL", round(strength, 4), suggested_sl_bps=80, suggested_tp_bps=160)
    return None
