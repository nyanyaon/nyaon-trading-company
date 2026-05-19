from nyaon_trading.recon.snapshot import classify_diff


def test_clean_diff():
    prev = {"equity": 1000, "positions": [], "open_orders": []}
    curr = {"equity": 1000, "positions": [], "open_orders": []}
    assert classify_diff(prev, curr) == "clean"


def test_benign_fee_drift():
    prev = {"equity": 1000.0, "positions": [], "open_orders": []}
    curr = {"equity": 999.6, "positions": [], "open_orders": []}
    assert classify_diff(prev, curr) == "benign"


def test_critical_balance_drift_without_trade():
    prev = {"equity": 1000.0, "positions": [], "open_orders": []}
    curr = {"equity": 994.0, "positions": [], "open_orders": []}
    assert classify_diff(prev, curr) == "critical"


def test_critical_position_mismatch():
    prev = {"equity": 1000.0, "positions": [{"symbol": "BTCUSDT", "qty": 0.01}], "open_orders": []}
    curr = {"equity": 1000.0, "positions": [{"symbol": "BTCUSDT", "qty": 0.03}], "open_orders": []}
    assert classify_diff(prev, curr, recent_trade_qty=0.0) == "critical"
