import time

import pytest

from nyaon_trading.binance.orders import (
    cancel_order, place_market, place_stop, place_take_profit, set_leverage, sl_coid, tp_coid,
)


@pytest.mark.timeout(30)
def test_market_round_trip(client):
    intent = {
        "id": f"itest_{int(time.time())}",
        "symbol": "BTCUSDT",
        "side": "BUY",
    }
    set_leverage(client, "BTCUSDT", 3)
    entry = place_market(client, intent, qty=0.002, attempt=0)
    assert entry.coid.startswith(intent["id"])
    place_stop(client, intent, stop_price=1.0, attempt=0)
    place_take_profit(client, intent, tp_price=10_000_000.0, attempt=0)
    cancel_order(client, "BTCUSDT", sl_coid(intent["id"], 0))
    cancel_order(client, "BTCUSDT", tp_coid(intent["id"], 0))
    close_intent = {**intent, "id": intent["id"] + "_close", "side": "SELL"}
    place_market(client, close_intent, qty=0.002, attempt=0)
