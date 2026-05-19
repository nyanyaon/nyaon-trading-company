def test_account_returns_balance(client):
    from nyaon_trading.binance.account import account
    a = account(client)
    assert "totalWalletBalance" in a
    assert float(a["availableBalance"]) >= 0
