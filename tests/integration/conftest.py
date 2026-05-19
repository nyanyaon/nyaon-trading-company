import json
import os
from pathlib import Path

import pytest

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.config import Mode


@pytest.fixture(scope="session", autouse=True)
def _gate():
    if os.environ.get("RUN_TESTNET_TESTS") != "1":
        pytest.skip("set RUN_TESTNET_TESTS=1 to run integration tests")


@pytest.fixture(scope="session")
def mode() -> Mode:
    return Mode(
        name="testnet",
        base_url="https://testnet.binancefuture.com",
        key=os.environ["BINANCE_TESTNET_API_KEY"],
        secret=os.environ["BINANCE_TESTNET_API_SECRET"],
        live_size_multiplier=1.0,
    )


@pytest.fixture(scope="session")
def client(mode) -> BinanceClient:
    return BinanceClient(mode)
