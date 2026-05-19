def test_burst_does_not_ban(client):
    from nyaon_trading.binance.market import klines
    for _ in range(20):
        df = klines(client, "BTCUSDT", "1m", 100)
        assert len(df) == 100
