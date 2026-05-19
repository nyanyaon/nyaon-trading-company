import json
from pathlib import Path

import pytest

from nyaon_trading.config import load_mode, MissingSecretError


def write_mode(tmp_path: Path, mode: str = "testnet") -> Path:
    state = tmp_path / "state"
    state.mkdir()
    p = state / "mode.json"
    p.write_text(
        json.dumps(
            {
                "mode": mode,
                "set_by": "test",
                "set_at": "2026-05-19T00:00:00Z",
                "reason": "test",
                "live_size_multiplier": 0.5,
            }
        )
    )
    return tmp_path


def test_load_testnet_mode(tmp_path, monkeypatch):
    root = write_mode(tmp_path, "testnet")
    monkeypatch.chdir(root)
    monkeypatch.setenv("BINANCE_TESTNET_API_KEY", "k")
    monkeypatch.setenv("BINANCE_TESTNET_API_SECRET", "s")
    m = load_mode()
    assert m.name == "testnet"
    assert m.base_url == "https://testnet.binancefuture.com"
    assert m.key == "k"
    assert m.secret == "s"
    assert m.live_size_multiplier == 0.5


def test_load_live_mode(tmp_path, monkeypatch):
    root = write_mode(tmp_path, "live")
    monkeypatch.chdir(root)
    monkeypatch.setenv("BINANCE_LIVE_API_KEY", "lk")
    monkeypatch.setenv("BINANCE_LIVE_API_SECRET", "ls")
    m = load_mode()
    assert m.name == "live"
    assert m.base_url == "https://fapi.binance.com"
    assert m.key == "lk"


def test_live_missing_secret_raises(tmp_path, monkeypatch):
    root = write_mode(tmp_path, "live")
    monkeypatch.chdir(root)
    monkeypatch.delenv("BINANCE_LIVE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_LIVE_API_SECRET", raising=False)
    with pytest.raises(MissingSecretError):
        load_mode()
