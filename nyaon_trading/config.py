from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

_BASE_URLS = {
    "testnet": "https://testnet.binancefuture.com",
    "live": "https://fapi.binance.com",
}

_SECRET_ENVS = {
    "testnet": ("BINANCE_TESTNET_API_KEY", "BINANCE_TESTNET_API_SECRET"),
    "live": ("BINANCE_LIVE_API_KEY", "BINANCE_LIVE_API_SECRET"),
}


class MissingSecretError(RuntimeError):
    pass


@dataclass(frozen=True)
class Mode:
    name: str
    base_url: str
    key: str
    secret: str
    live_size_multiplier: float


def load_mode(state_dir: Path | None = None) -> Mode:
    state_dir = state_dir or Path.cwd() / "state"
    raw = json.loads((state_dir / "mode.json").read_text())
    name = raw["mode"]
    key_env, secret_env = _SECRET_ENVS[name]
    key = os.environ.get(key_env)
    secret = os.environ.get(secret_env)
    if not key or not secret:
        raise MissingSecretError(f"missing {key_env}/{secret_env} for mode={name}")
    return Mode(
        name=name,
        base_url=_BASE_URLS[name],
        key=key,
        secret=secret,
        live_size_multiplier=float(raw["live_size_multiplier"]),
    )
