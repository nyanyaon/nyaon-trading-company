def test_klines_monotonic(client):
    from nyaon_trading.binance.market import klines

    df = klines(client, "BTCUSDT", "15m", 50)
    assert len(df) == 50
    assert df["open_time"].is_monotonic_increasing
