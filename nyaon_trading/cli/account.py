from __future__ import annotations

import json

from nyaon_trading.binance.account import account
from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.config import load_mode


def run(argv: list[str]) -> int:
    mode = load_mode()
    client = BinanceClient(mode)
    print(json.dumps(account(client), indent=2))
    return 0
