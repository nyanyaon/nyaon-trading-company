from __future__ import annotations

import json

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.config import load_mode
from nyaon_trading.strategy.pipeline import run as run_pipeline


def run(argv: list[str]) -> int:
    mode = load_mode()
    client = BinanceClient(mode)
    path = run_pipeline(mode, client)
    print(json.dumps({"path": str(path)}))
    return 0
