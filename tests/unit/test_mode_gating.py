import json
import time
from pathlib import Path

import pytest

from nyaon_trading.cli.mode import set_live, GoLiveRefused


def _write_audit(path: Path, pass_: bool, age_s: int = 0):
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - age_s))
    path.write_text(json.dumps({
        "ts": ts,
        "pass": pass_,
        "criteria": {
            "hit_rate": 0.5, "profit_factor": 1.5, "max_drawdown": 0.05,
            "ops_critical_count": 0, "avg_slippage_bps": 3.0,
        }
    }))


def _seed(tmp_path: Path):
    s = tmp_path / "state"
    s.mkdir()
    (s / "mode.json").write_text(json.dumps({
        "mode": "testnet", "set_by": "ceo", "set_at": "2026-05-19T00:00:00Z",
        "reason": "init", "live_size_multiplier": 1.0,
    }))
    return s


def test_refuse_when_audit_missing(tmp_path, monkeypatch):
    _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NYAON_AGENT_ROLE", "ceo")
    monkeypatch.setenv("BINANCE_LIVE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_API_SECRET", "s")
    with pytest.raises(GoLiveRefused):
        set_live("manual ramp")


def test_refuse_when_audit_failed(tmp_path, monkeypatch):
    state = _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_audit(state / "audits" / "promotion-2026-05-19.json", pass_=False)
    monkeypatch.setenv("NYAON_AGENT_ROLE", "ceo")
    monkeypatch.setenv("BINANCE_LIVE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_API_SECRET", "s")
    with pytest.raises(GoLiveRefused):
        set_live("manual ramp")


def test_refuse_when_halt_flag(tmp_path, monkeypatch):
    state = _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_audit(state / "audits" / "promotion-2026-05-19.json", pass_=True)
    (state / "halt.flag").write_text("halted")
    monkeypatch.setenv("NYAON_AGENT_ROLE", "ceo")
    monkeypatch.setenv("BINANCE_LIVE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_API_SECRET", "s")
    with pytest.raises(GoLiveRefused):
        set_live("manual ramp")


def test_refuse_when_not_ceo(tmp_path, monkeypatch):
    state = _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_audit(state / "audits" / "promotion-2026-05-19.json", pass_=True)
    monkeypatch.setenv("NYAON_AGENT_ROLE", "trader")
    monkeypatch.setenv("BINANCE_LIVE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_API_SECRET", "s")
    with pytest.raises(GoLiveRefused):
        set_live("manual ramp")


def test_accept_all_preconditions_met(tmp_path, monkeypatch):
    state = _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_audit(state / "audits" / "promotion-2026-05-19.json", pass_=True)
    monkeypatch.setenv("NYAON_AGENT_ROLE", "ceo")
    monkeypatch.setenv("BINANCE_LIVE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_API_SECRET", "s")
    set_live("week-2 audit pass")
    new = json.loads((state / "mode.json").read_text())
    assert new["mode"] == "live"
    assert new["live_size_multiplier"] == 0.5
