from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_STATE = Path("state")
_MODE = _STATE / "mode.json"
_HALT = _STATE / "halt.flag"
_AUDITS = _STATE / "audits"
_INCIDENTS = _STATE / "incidents"
_SNAPSHOTS = _STATE / "snapshots"


class GoLiveRefused(RuntimeError):
    pass


def _latest_audit() -> dict | None:
    if not _AUDITS.exists():
        return None
    files = sorted(_AUDITS.glob("promotion-*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text())


def _audit_age_s(audit: dict) -> float:
    t = time.strptime(audit["ts"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
    return time.time() - time.mktime(t) + time.timezone


def _has_unresolved_incident() -> bool:
    if not _INCIDENTS.exists():
        return False
    inc_files = sorted(_INCIDENTS.glob("*.json"))
    snap_files = sorted(_SNAPSHOTS.glob("*.json"))
    if not inc_files:
        return False
    if not snap_files:
        return True
    return inc_files[-1].stat().st_mtime > snap_files[-1].stat().st_mtime


def set_live(reason: str) -> None:
    if os.environ.get("NYAON_AGENT_ROLE") != "ceo":
        raise GoLiveRefused("only ceo may set live")
    current = json.loads(_MODE.read_text())
    if current["mode"] != "testnet":
        raise GoLiveRefused(f"current mode is {current['mode']}, expected testnet")
    if not os.environ.get("BINANCE_LIVE_API_KEY") or not os.environ.get("BINANCE_LIVE_API_SECRET"):
        raise GoLiveRefused("BINANCE_LIVE_API_KEY/SECRET not set")
    audit = _latest_audit()
    if audit is None:
        raise GoLiveRefused("no promotion audit found")
    if not audit.get("pass"):
        raise GoLiveRefused("latest audit pass=false")
    if _audit_age_s(audit) > 24 * 3600:
        raise GoLiveRefused("latest audit older than 24h")
    if _HALT.exists():
        raise GoLiveRefused("halt.flag present")
    if _has_unresolved_incident():
        raise GoLiveRefused("unresolved incident newer than latest snapshot")
    new = {
        "mode": "live",
        "set_by": "ceo",
        "set_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reason": reason,
        "live_size_multiplier": 0.5,
    }
    tmp = _MODE.with_suffix(".tmp")
    tmp.write_text(json.dumps(new, indent=2))
    tmp.replace(_MODE)


def set_testnet(reason: str) -> None:
    current = json.loads(_MODE.read_text())
    new = {
        "mode": "testnet",
        "set_by": os.environ.get("NYAON_AGENT_ROLE", "unknown"),
        "set_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reason": reason,
        "live_size_multiplier": float(current.get("live_size_multiplier", 1.0)),
    }
    tmp = _MODE.with_suffix(".tmp")
    tmp.write_text(json.dumps(new, indent=2))
    tmp.replace(_MODE)


def run(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="nyaon mode")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    set_p = sub.add_parser("set")
    set_p.add_argument("target", choices=["testnet", "live"])
    set_p.add_argument("--reason", required=True)
    a = p.parse_args(argv)
    if a.cmd == "show":
        print(_MODE.read_text())
        return 0
    try:
        if a.target == "live":
            set_live(a.reason)
        else:
            set_testnet(a.reason)
    except GoLiveRefused as e:
        print(str(e), file=sys.stderr)
        return 2
    print(f"mode set to {a.target}")
    return 0
