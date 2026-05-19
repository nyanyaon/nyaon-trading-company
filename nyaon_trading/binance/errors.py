class BinanceError(RuntimeError):
    def __init__(self, code: int, msg: str):
        super().__init__(f"binance[{code}]: {msg}")
        self.code = code
        self.msg = msg


class TimestampSkewError(BinanceError):
    pass


class RateLimitError(BinanceError):
    pass
