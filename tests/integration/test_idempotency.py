import time

import pytest

from nyaon_trading.binance.errors import BinanceError
from nyaon_trading.binance.orders import place_market, place_stop, place_take_profit, cancel_order, sl_coid, tp_coid


@pytest.mark.timeout(30)
def test_duplicate_coid_rejected(client):
    intent = {"id": f"idem_{int(time.time())}", "symbol": "BTCUSDT", "side": "BUY"}
    first = place_market(client, intent, qty=0.002, attempt=0)
    with pytest.raises(BinanceError):
        place_market(client, intent, qty=0.002, attempt=0)
    close = {**intent, "id": intent["id"] + "_close", "side": "SELL"}
    place_market(client, close, qty=0.002, attempt=0)
