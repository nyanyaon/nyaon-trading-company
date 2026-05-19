from nyaon_trading.binance.client import sign_query


def test_sign_query_known_vector():
    # Reference vector from Binance docs
    secret = "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"
    query = (
        "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC"
        "&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559"
    )
    sig = sign_query(query, secret)
    assert sig == "c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71"
