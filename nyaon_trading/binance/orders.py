from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nyaon_trading.binance.client import BinanceClient

_ORDERS = Path("state/orders")
_LEV_CACHE: dict[str, int] = {}


def coid_for(intent_id: str, attempt: int) -> str:
    return f"{intent_id}-{attempt}"


def sl_coid(intent_id: str, attempt: int) -> str:
    return f"{coid_for(intent_id, attempt)}-sl"


def tp_coid(intent_id: str, attempt: int) -> str:
    return f"{coid_for(intent_id, attempt)}-tp"


@dataclass
class OrderResult:
    coid: str
    symbol: str
    side: str
    type: str
    status: str
    qty: float
    price: float | None
    stop_price: float | None
    avg_fill_price: float | None
    ts: str
    intent_id: str
    attempt: int


def _persist(o: OrderResult) -> Path:
    _ORDERS.mkdir(parents=True, exist_ok=True)
    path = _ORDERS / f"{o.coid}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(o), indent=2))
    tmp.replace(path)
    return path


def set_leverage(client: BinanceClient, symbol: str, leverage: int) -> None:
    if _LEV_CACHE.get(symbol) == leverage:
        return
    client.post_signed("/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage})
    _LEV_CACHE[symbol] = leverage


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def place_market(
    client: BinanceClient, intent: dict[str, Any], qty: float, attempt: int = 0
) -> OrderResult:
    coid = coid_for(intent["id"], attempt)
    body = client.post_signed(
        "/fapi/v1/order",
        {
            "symbol": intent["symbol"],
            "side": intent["side"],
            "type": "MARKET",
            "quantity": qty,
            "newClientOrderId": coid,
        },
    )
    r = OrderResult(
        coid=coid,
        symbol=intent["symbol"],
        side=intent["side"],
        type="MARKET",
        status=body.get("status", "NEW"),
        qty=qty,
        price=None,
        stop_price=None,
        avg_fill_price=float(body.get("avgPrice", 0)) or None,
        ts=_now(),
        intent_id=intent["id"],
        attempt=attempt,
    )
    _persist(r)
    return r


def place_stop(
    client: BinanceClient, intent: dict[str, Any], stop_price: float, attempt: int = 0
) -> OrderResult:
    coid = sl_coid(intent["id"], attempt)
    opposite = "SELL" if intent["side"] == "BUY" else "BUY"
    body = client.post_signed(
        "/fapi/v1/order",
        {
            "symbol": intent["symbol"],
            "side": opposite,
            "type": "STOP_MARKET",
            "stopPrice": stop_price,
            "closePosition": "true",
            "newClientOrderId": coid,
        },
    )
    r = OrderResult(
        coid=coid,
        symbol=intent["symbol"],
        side=opposite,
        type="STOP_MARKET",
        status=body.get("status", "NEW"),
        qty=0.0,
        price=None,
        stop_price=stop_price,
        avg_fill_price=None,
        ts=_now(),
        intent_id=intent["id"],
        attempt=attempt,
    )
    _persist(r)
    return r


def place_take_profit(
    client: BinanceClient, intent: dict[str, Any], tp_price: float, attempt: int = 0
) -> OrderResult:
    coid = tp_coid(intent["id"], attempt)
    opposite = "SELL" if intent["side"] == "BUY" else "BUY"
    body = client.post_signed(
        "/fapi/v1/order",
        {
            "symbol": intent["symbol"],
            "side": opposite,
            "type": "TAKE_PROFIT_MARKET",
            "stopPrice": tp_price,
            "closePosition": "true",
            "newClientOrderId": coid,
        },
    )
    r = OrderResult(
        coid=coid,
        symbol=intent["symbol"],
        side=opposite,
        type="TAKE_PROFIT_MARKET",
        status=body.get("status", "NEW"),
        qty=0.0,
        price=None,
        stop_price=tp_price,
        avg_fill_price=None,
        ts=_now(),
        intent_id=intent["id"],
        attempt=attempt,
    )
    _persist(r)
    return r


def cancel_order(client: BinanceClient, symbol: str, coid: str) -> dict[str, Any]:
    return client.delete_signed("/fapi/v1/order", {"symbol": symbol, "origClientOrderId": coid})
