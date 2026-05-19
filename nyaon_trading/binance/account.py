from __future__ import annotations

from typing import Any

from nyaon_trading.binance.client import BinanceClient


def account(client: BinanceClient) -> dict[str, Any]:
    return client.get_signed("/fapi/v2/account")


def position_risk(client: BinanceClient) -> list[dict[str, Any]]:
    return client.get_signed("/fapi/v2/positionRisk")


def open_orders(client: BinanceClient, symbol: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if symbol:
        params["symbol"] = symbol
    return client.get_signed("/fapi/v1/openOrders", params)


def income(client: BinanceClient, start_ms: int) -> list[dict[str, Any]]:
    return client.get_signed("/fapi/v1/income", {"startTime": start_ms, "limit": 1000})
