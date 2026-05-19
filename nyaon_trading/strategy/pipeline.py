from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.binance.market import exchange_info, klines
from nyaon_trading.config import Mode
from nyaon_trading.strategy import mean_reversion, trend

_OUT = Path("state/signals")
_MIN_QUOTE_VOL_24H = 50_000_000


def _eligible_symbols(info: dict[str, Any]) -> list[str]:
    return [
        s["symbol"]
        for s in info.get("symbols", [])
        if s.get("status") == "TRADING"
        and s.get("quoteAsset") == "USDT"
        and s.get("contractType") == "PERPETUAL"
    ]


def run(mode: Mode, client: BinanceClient, max_symbols: int = 20) -> Path:
    info = exchange_info(client)
    symbols = _eligible_symbols(info)[:max_symbols]
    signals: list[dict[str, Any]] = []
    ts = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
    for sym in symbols:
        try:
            df = klines(client, sym, "15m", 200)
        except Exception:
            continue
        for src_name, mod in (("trend", trend), ("mean_reversion", mean_reversion)):
            s = mod.score(df)
            if s is None:
                continue
            ttl = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 15 * 60)
            )
            signals.append({
                "symbol": sym,
                "side": s.side,
                "strength": s.strength,
                "suggested_sl_bps": s.suggested_sl_bps,
                "suggested_tp_bps": s.suggested_tp_bps,
                "ttl": ttl,
                "source": src_name,
            })
    _OUT.mkdir(parents=True, exist_ok=True)
    path = _OUT / f"{ts}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ts": ts, "signals": signals}, indent=2))
    tmp.replace(path)
    return path
