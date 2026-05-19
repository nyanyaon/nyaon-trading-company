from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from nyaon_trading.binance.account import account, income, open_orders, position_risk
from nyaon_trading.binance.client import BinanceClient

_SNAP_DIR = Path("state/snapshots")
_INC_DIR = Path("state/incidents")
_HALT = Path("state/halt.flag")


def _latest_snapshot() -> dict[str, Any] | None:
    if not _SNAP_DIR.exists():
        return None
    files = sorted(_SNAP_DIR.glob("*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text())


def build(client: BinanceClient) -> dict[str, Any]:
    acct = account(client)
    pr = position_risk(client)
    oo = open_orders(client)
    since = int(time.time() * 1000) - 24 * 3600 * 1000
    inc = income(client, since)
    positions = [
        {
            "symbol": p["symbol"],
            "qty": float(p["positionAmt"]),
            "entry": float(p["entryPrice"]),
            "unrealized": float(p["unRealizedProfit"]),
        }
        for p in pr
        if float(p["positionAmt"]) != 0.0
    ]
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "equity": float(acct["totalWalletBalance"]),
        "available": float(acct["availableBalance"]),
        "positions": positions,
        "open_orders": [
            {
                "coid": o.get("clientOrderId", ""),
                "symbol": o["symbol"],
                "type": o["type"],
                "price": float(o.get("stopPrice") or o.get("price") or 0),
            }
            for o in oo
        ],
        "daily_pnl": sum(float(x["income"]) for x in inc if x["incomeType"] == "REALIZED_PNL"),
        "weekly_pnl": 0.0,
    }


def classify_diff(prev: dict[str, Any], curr: dict[str, Any], recent_trade_qty: float = 0.0) -> str:
    eq_drift = abs(curr["equity"] - prev["equity"]) / max(prev["equity"], 1e-9)
    prev_pos = {p["symbol"]: p["qty"] for p in prev.get("positions", [])}
    curr_pos = {p["symbol"]: p["qty"] for p in curr.get("positions", [])}
    syms = set(prev_pos) | set(curr_pos)
    for s in syms:
        diff = curr_pos.get(s, 0.0) - prev_pos.get(s, 0.0)
        if abs(diff) > 1e-9 and abs(diff - recent_trade_qty) > 1e-6:
            return "critical"
    if eq_drift > 0.005:
        return "critical"
    if eq_drift > 0.0001:
        return "benign"
    return "clean"


def write_snapshot(curr: dict[str, Any]) -> Path:
    _SNAP_DIR.mkdir(parents=True, exist_ok=True)
    name = curr["ts"].replace(":", "-")
    path = _SNAP_DIR / f"{name}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(curr, indent=2))
    tmp.replace(path)
    return path


def write_incident(curr: dict[str, Any], reason: str) -> Path:
    _INC_DIR.mkdir(parents=True, exist_ok=True)
    name = curr["ts"].replace(":", "-")
    path = _INC_DIR / f"{name}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(
            {
                "ts": curr["ts"],
                "kind": "recon_critical",
                "detail": {"reason": reason, "snapshot": curr},
            },
            indent=2,
        )
    )
    tmp.replace(path)
    _HALT.write_text(f"recon critical at {curr['ts']}: {reason}\n")
    return path


def run_full(client: BinanceClient) -> tuple[str, Path]:
    prev = _latest_snapshot()
    curr = build(client)
    cls = "clean" if prev is None else classify_diff(prev, curr)
    if cls == "critical":
        write_incident(curr, "diff classified critical")
    path = write_snapshot(curr)
    return cls, path
