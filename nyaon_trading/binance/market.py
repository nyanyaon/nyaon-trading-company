from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from nyaon_trading.binance.client import BinanceClient

_CACHE = Path("state/cache")
_EXCHANGE_INFO_TTL = 12 * 3600
_KLINE_TTL = {"15m": 14 * 60, "5m": 4 * 60, "1m": 50}


def _read_cache(path: Path, ttl: int) -> Any | None:
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl:
        return None
    return json.loads(path.read_text())


def _write_cache(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(path)


def exchange_info(client: BinanceClient) -> dict[str, Any]:
    path = _CACHE / "exchangeInfo.json"
    cached = _read_cache(path, _EXCHANGE_INFO_TTL)
    if cached is not None:
        return cached
    data = client.get_public("/fapi/v1/exchangeInfo")
    _write_cache(path, data)
    return data


def klines(client: BinanceClient, symbol: str, interval: str, limit: int) -> pd.DataFrame:
    path = _CACHE / f"klines_{symbol}_{interval}_{limit}.json"
    ttl = _KLINE_TTL.get(interval, 60)
    data = _read_cache(path, ttl)
    if data is None:
        data = client.get_public(
            "/fapi/v1/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )
        _write_cache(path, data)
    return _to_frame(data)


def _to_frame(raw: list[list[Any]]) -> pd.DataFrame:
    cols = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trades",
        "taker_base",
        "taker_quote",
        "ignore",
    ]
    df = pd.DataFrame(raw, columns=cols)
    for c in ("open", "high", "low", "close", "volume", "quote_volume"):
        df[c] = df[c].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


def load_fixture(path: Path) -> pd.DataFrame:
    return _to_frame(json.loads(path.read_text()))
