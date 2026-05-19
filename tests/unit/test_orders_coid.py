from nyaon_trading.binance.orders import coid_for, sl_coid, tp_coid


def test_coid_deterministic():
    assert coid_for("intent_abc", 0) == "intent_abc-0"
    assert coid_for("intent_abc", 1) == "intent_abc-1"


def test_paired_coids():
    assert sl_coid("intent_abc", 0) == "intent_abc-0-sl"
    assert tp_coid("intent_abc", 0) == "intent_abc-0-tp"
