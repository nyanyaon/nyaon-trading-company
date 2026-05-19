from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.binance.orders import (
    place_market,
    place_stop,
    place_take_profit,
    set_leverage,
)
from nyaon_trading.config import load_mode

_HALT = Path("state/halt.flag")
_INTENTS = Path("state/intents")


class HaltedError(RuntimeError):
    pass


def refuse_if_halted() -> None:
    if _HALT.exists():
        raise HaltedError(f"HALTED: {_HALT.read_text().strip()}")


def _ticker_price(client: BinanceClient, symbol: str) -> float:
    body = client.get_public("/fapi/v1/ticker/price", {"symbol": symbol})
    return float(body["price"])


def _qty_from_quote(quote_amount: float, price: float) -> float:
    raw = quote_amount / price
    # round to 3 decimals for major perps; safe default for testnet
    return round(raw, 3)


def run(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="nyaon place-order")
    p.add_argument("--intent", required=True)
    args = p.parse_args(argv)
    try:
        refuse_if_halted()
    except HaltedError as e:
        print(str(e), file=sys.stderr)
        return 2
    mode = load_mode()
    intent_path = Path(args.intent)
    intent = json.loads(intent_path.read_text())
    client = BinanceClient(mode)
    if intent["status"] != "approved":
        print(f"intent status={intent['status']} not approved", file=sys.stderr)
        return 2
    leverage = int(intent.get("leverage", 3))
    set_leverage(client, intent["symbol"], leverage)
    price = _ticker_price(client, intent["symbol"])
    qty_quote = float(intent["qty_quote"]) * mode.live_size_multiplier if mode.name == "live" else float(intent["qty_quote"])
    qty = _qty_from_quote(qty_quote, price)
    entry = place_market(client, intent, qty, attempt=0)
    # poll fill
    avg = entry.avg_fill_price
    for _ in range(5):
        if avg:
            break
        time.sleep(1)
        body = client.get_signed("/fapi/v1/order", {"symbol": intent["symbol"], "origClientOrderId": entry.coid})
        avg = float(body.get("avgPrice", 0)) or None
    if not avg:
        intent["status"] = "failed"
        intent["failed_reason"] = "entry did not fill within 5s"
        intent_path.write_text(json.dumps(intent, indent=2))
        return 3
    bps = lambda x: x / 10_000
    sl_price = avg * (1 - bps(int(intent["sl_bps"]))) if intent["side"] == "BUY" else avg * (1 + bps(int(intent["sl_bps"])))
    tp_price = avg * (1 + bps(int(intent["tp_bps"]))) if intent["side"] == "BUY" else avg * (1 - bps(int(intent["tp_bps"])))
    place_stop(client, intent, round(sl_price, 2), attempt=0)
    place_take_profit(client, intent, round(tp_price, 2), attempt=0)
    intent["status"] = "filled"
    intent["filled_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    intent_path.write_text(json.dumps(intent, indent=2))
    print(json.dumps({"coid": entry.coid, "avg_fill_price": avg, "qty": qty}))
    return 0
