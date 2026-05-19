from __future__ import annotations

import json

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.config import load_mode
from nyaon_trading.recon.snapshot import run_full


def run(argv: list[str]) -> int:
    mode = load_mode()
    client = BinanceClient(mode)
    cls, path = run_full(client)
    print(json.dumps({"classification": cls, "path": str(path)}))
    return 0 if cls != "critical" else 3
