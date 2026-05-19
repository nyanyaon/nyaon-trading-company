from __future__ import annotations


from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.binance.market import klines
from nyaon_trading.config import load_mode


def run(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: nyaon klines <symbol> <interval> <limit>", end="\n")
        return 2
    symbol, interval, limit = argv[0], argv[1], int(argv[2])
    mode = load_mode()
    client = BinanceClient(mode)
    df = klines(client, symbol, interval, limit)
    print(df.tail(10).to_json(orient="records"))
    return 0
