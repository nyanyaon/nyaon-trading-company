from __future__ import annotations

import argparse
import json

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.binance.orders import cancel_order
from nyaon_trading.config import load_mode


def run(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="nyaon cancel")
    p.add_argument("--symbol", required=True)
    p.add_argument("--coid", required=True)
    a = p.parse_args(argv)
    mode = load_mode()
    client = BinanceClient(mode)
    print(json.dumps(cancel_order(client, a.symbol, a.coid)))
    return 0
