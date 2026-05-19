# Binance Connectivity & Strategy Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the missing Python connectivity layer so existing agent roles can actually trade on Binance USDT-M futures, with deterministic strategy code, auditable filesystem state, and a hard-gated testnet → live cutover.

**Architecture:** A `uv`-managed Python package (`nyaon_trading`) exposes a single `nyaon` CLI consumed by agents via Bash. Strategy signals are deterministic Python; the Quant agent applies judgement on top. All artifacts (signals, intents, orders, snapshots, incidents, audits) live in `state/` as atomically-written JSON. Mode (`testnet` vs `live`) is a single file that every CLI reads at startup.

**Tech Stack:** Python 3.12, uv, httpx, tenacity, pydantic, pandas, numpy, jsonschema, pytest, ruff, pyright.

**Reference spec:** `docs/superpowers/specs/2026-05-19-binance-connectivity-design.md`

---

## File structure

**Created:**

```
pyproject.toml
uv.lock
.python-version
.gitignore                                  (modified — add state/, .venv/)
bin/nyaon                                   (executable shebang script)
nyaon_trading/__init__.py
nyaon_trading/config.py
nyaon_trading/binance/__init__.py
nyaon_trading/binance/client.py
nyaon_trading/binance/errors.py
nyaon_trading/binance/market.py
nyaon_trading/binance/account.py
nyaon_trading/binance/orders.py
nyaon_trading/strategy/__init__.py
nyaon_trading/strategy/trend.py
nyaon_trading/strategy/mean_reversion.py
nyaon_trading/strategy/pipeline.py
nyaon_trading/recon/__init__.py
nyaon_trading/recon/snapshot.py
nyaon_trading/cli/__init__.py
nyaon_trading/cli/klines.py
nyaon_trading/cli/account.py
nyaon_trading/cli/signals.py
nyaon_trading/cli/place_order.py
nyaon_trading/cli/cancel.py
nyaon_trading/cli/snapshot.py
nyaon_trading/cli/mode.py
nyaon_trading/cli/halt.py
state/.schemas/signal.json
state/.schemas/intent.json
state/.schemas/order.json
state/.schemas/snapshot.json
state/.schemas/mode.json
state/.schemas/incident.json
state/.schemas/promotion-audit.json
state/.gitkeep
tests/__init__.py
tests/unit/__init__.py
tests/unit/test_config.py
tests/unit/test_client_signing.py
tests/unit/test_orders_coid.py
tests/unit/test_trend.py
tests/unit/test_mean_reversion.py
tests/unit/test_snapshot_diff.py
tests/unit/test_halt.py
tests/unit/test_mode_gating.py
tests/unit/fixtures/klines_btc_15m.json
tests/integration/__init__.py
tests/integration/conftest.py
tests/integration/test_account.py
tests/integration/test_klines.py
tests/integration/test_round_trip.py
tests/integration/test_idempotency.py
tests/integration/test_rate_limit.py
```

Each file owns one responsibility; nothing exceeds ~300 LOC.

---

### Task 1: Bootstrap uv project

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore` (or modify existing)
- Create: `nyaon_trading/__init__.py`

- [ ] **Step 1: Pin Python version**

Create `.python-version`:

```
3.12
```

- [ ] **Step 2: Write `pyproject.toml`**

Create `pyproject.toml`:

```toml
[project]
name = "nyaon-trading"
version = "0.1.0"
description = "Nyaon Trading Company — Binance USDT-M connectivity and strategy execution"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",
    "tenacity>=8.2",
    "pydantic>=2.7",
    "pandas>=2.2",
    "numpy>=1.26",
    "jsonschema>=4.22",
]

[project.scripts]
nyaon = "nyaon_trading.cli:main"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.5",
    "pyright>=1.1",
    "respx>=0.21",   # httpx mock
    "freezegun>=1.5",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["nyaon_trading"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q"
```

- [ ] **Step 3: Create or update `.gitignore`**

Append (or create) `.gitignore`:

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
# state is runtime data; schemas committed separately
state/*
!state/.schemas/
!state/.gitkeep
```

- [ ] **Step 4: Create package marker**

Create `nyaon_trading/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 5: Sync deps**

Run: `uv sync`
Expected: creates `.venv/`, installs deps, writes `uv.lock`.

- [ ] **Step 6: Verify uv-only**

Run: `uv run python -c "import httpx, tenacity, pydantic, pandas, numpy, jsonschema; print('ok')"`
Expected: `ok`

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock .python-version .gitignore nyaon_trading/__init__.py
git commit -m "feat: bootstrap uv project for nyaon_trading"
```

---

### Task 2: State schemas

**Files:**
- Create: `state/.schemas/mode.json`
- Create: `state/.schemas/signal.json`
- Create: `state/.schemas/intent.json`
- Create: `state/.schemas/order.json`
- Create: `state/.schemas/snapshot.json`
- Create: `state/.schemas/incident.json`
- Create: `state/.schemas/promotion-audit.json`
- Create: `state/.gitkeep`

- [ ] **Step 1: Create `state/.gitkeep` (empty)**

Run: `touch state/.gitkeep && mkdir -p state/.schemas`

- [ ] **Step 2: Write `state/.schemas/mode.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["mode", "set_by", "set_at", "reason", "live_size_multiplier"],
  "properties": {
    "mode": { "enum": ["testnet", "live"] },
    "set_by": { "type": "string" },
    "set_at": { "type": "string", "format": "date-time" },
    "reason": { "type": "string" },
    "live_size_multiplier": { "type": "number", "minimum": 0, "maximum": 1 }
  },
  "additionalProperties": false
}
```

- [ ] **Step 3: Write `state/.schemas/signal.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["ts", "signals"],
  "properties": {
    "ts": { "type": "string", "format": "date-time" },
    "signals": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["symbol", "side", "strength", "suggested_sl_bps", "suggested_tp_bps", "ttl", "source"],
        "properties": {
          "symbol": { "type": "string" },
          "side": { "enum": ["BUY", "SELL"] },
          "strength": { "type": "number", "minimum": 0, "maximum": 1 },
          "suggested_sl_bps": { "type": "integer", "minimum": 1 },
          "suggested_tp_bps": { "type": "integer", "minimum": 1 },
          "ttl": { "type": "string", "format": "date-time" },
          "source": { "enum": ["trend", "mean_reversion"] }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Write `state/.schemas/intent.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["id", "symbol", "side", "qty_quote", "sl_bps", "tp_bps", "ttl", "source_signal", "status"],
  "properties": {
    "id": { "type": "string" },
    "symbol": { "type": "string" },
    "side": { "enum": ["BUY", "SELL"] },
    "qty_quote": { "type": "number", "exclusiveMinimum": 0 },
    "sl_bps": { "type": "integer", "minimum": 1 },
    "tp_bps": { "type": "integer", "minimum": 1 },
    "ttl": { "type": "string", "format": "date-time" },
    "source_signal": { "type": "string" },
    "status": { "enum": ["proposed", "approved", "rejected", "filled", "failed"] },
    "rejection_reason": { "type": "string" },
    "leverage": { "type": "integer", "minimum": 1, "maximum": 20 },
    "approved_at": { "type": "string", "format": "date-time" },
    "filled_at": { "type": "string", "format": "date-time" },
    "failed_reason": { "type": "string" }
  },
  "additionalProperties": false
}
```

- [ ] **Step 5: Write `state/.schemas/order.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["coid", "symbol", "side", "type", "status", "qty", "ts"],
  "properties": {
    "coid": { "type": "string" },
    "symbol": { "type": "string" },
    "side": { "enum": ["BUY", "SELL"] },
    "type": { "enum": ["MARKET", "LIMIT", "STOP_MARKET", "TAKE_PROFIT_MARKET"] },
    "status": { "enum": ["NEW", "FILLED", "CANCELED", "REJECTED", "EXPIRED"] },
    "qty": { "type": "number" },
    "price": { "type": ["number", "null"] },
    "stop_price": { "type": ["number", "null"] },
    "avg_fill_price": { "type": ["number", "null"] },
    "ts": { "type": "string", "format": "date-time" },
    "intent_id": { "type": "string" },
    "attempt": { "type": "integer", "minimum": 0 }
  },
  "additionalProperties": false
}
```

- [ ] **Step 6: Write `state/.schemas/snapshot.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["ts", "equity", "available", "positions", "open_orders", "daily_pnl", "weekly_pnl"],
  "properties": {
    "ts": { "type": "string", "format": "date-time" },
    "equity": { "type": "number" },
    "available": { "type": "number" },
    "positions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["symbol", "qty", "entry", "unrealized"],
        "properties": {
          "symbol": { "type": "string" },
          "qty": { "type": "number" },
          "entry": { "type": "number" },
          "unrealized": { "type": "number" }
        },
        "additionalProperties": false
      }
    },
    "open_orders": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["coid", "symbol", "type", "price"],
        "properties": {
          "coid": { "type": "string" },
          "symbol": { "type": "string" },
          "type": { "type": "string" },
          "price": { "type": "number" }
        },
        "additionalProperties": false
      }
    },
    "daily_pnl": { "type": "number" },
    "weekly_pnl": { "type": "number" }
  },
  "additionalProperties": false
}
```

- [ ] **Step 7: Write `state/.schemas/incident.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["ts", "kind", "detail"],
  "properties": {
    "ts": { "type": "string", "format": "date-time" },
    "kind": { "type": "string" },
    "detail": { "type": "object" }
  },
  "additionalProperties": false
}
```

- [ ] **Step 8: Write `state/.schemas/promotion-audit.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["ts", "pass", "criteria"],
  "properties": {
    "ts": { "type": "string", "format": "date-time" },
    "pass": { "type": "boolean" },
    "criteria": {
      "type": "object",
      "required": ["hit_rate", "profit_factor", "max_drawdown", "ops_critical_count", "avg_slippage_bps"],
      "properties": {
        "hit_rate": { "type": "number" },
        "profit_factor": { "type": "number" },
        "max_drawdown": { "type": "number" },
        "ops_critical_count": { "type": "integer" },
        "avg_slippage_bps": { "type": "number" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 9: Commit**

```bash
git add state/.schemas/ state/.gitkeep
git commit -m "feat: add JSON schemas for state artifacts"
```

---

### Task 3: Config + mode loader (TDD)

**Files:**
- Create: `tests/__init__.py` (empty)
- Create: `tests/unit/__init__.py` (empty)
- Create: `tests/unit/test_config.py`
- Create: `nyaon_trading/config.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_config.py`:

```python
import json
import os
from pathlib import Path

import pytest

from nyaon_trading.config import load_mode, MissingSecretError


def write_mode(tmp_path: Path, mode: str = "testnet") -> Path:
    state = tmp_path / "state"
    state.mkdir()
    p = state / "mode.json"
    p.write_text(json.dumps({
        "mode": mode,
        "set_by": "test",
        "set_at": "2026-05-19T00:00:00Z",
        "reason": "test",
        "live_size_multiplier": 0.5,
    }))
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
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/unit/test_config.py -v`
Expected: ImportError (module not found).

- [ ] **Step 3: Implement `config.py`**

Create `nyaon_trading/config.py`:

```python
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
```

- [ ] **Step 4: Run — expect PASS**

Run: `uv run pytest tests/unit/test_config.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/__init__.py tests/unit/__init__.py tests/unit/test_config.py nyaon_trading/config.py
git commit -m "feat: config + mode loader with secret resolution"
```

---

### Task 4: Binance HTTP client + signing (TDD)

**Files:**
- Create: `nyaon_trading/binance/__init__.py` (empty)
- Create: `nyaon_trading/binance/errors.py`
- Create: `nyaon_trading/binance/client.py`
- Create: `tests/unit/test_client_signing.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_client_signing.py`:

```python
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
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/unit/test_client_signing.py -v`
Expected: ImportError.

- [ ] **Step 3: Write `errors.py`**

Create `nyaon_trading/binance/errors.py`:

```python
class BinanceError(RuntimeError):
    def __init__(self, code: int, msg: str):
        super().__init__(f"binance[{code}]: {msg}")
        self.code = code
        self.msg = msg


class TimestampSkewError(BinanceError):
    pass


class RateLimitError(BinanceError):
    pass
```

- [ ] **Step 4: Write `client.py`**

Create `nyaon_trading/binance/client.py`:

```python
from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.parse
from pathlib import Path
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from nyaon_trading.config import Mode
from nyaon_trading.binance.errors import (
    BinanceError,
    RateLimitError,
    TimestampSkewError,
)

_LOG_DIR = Path("state/logs/binance")


def sign_query(query: str, secret: str) -> str:
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()


class BinanceClient:
    def __init__(self, mode: Mode, http: httpx.Client | None = None):
        self.mode = mode
        self.http = http or httpx.Client(base_url=mode.base_url, timeout=10.0)
        self._time_offset_ms: int = 0
        self._offset_ts: float = 0.0

    def _now_ms(self) -> int:
        return int(time.time() * 1000) + self._time_offset_ms

    def _refresh_time(self) -> None:
        r = self.http.get("/fapi/v1/time")
        r.raise_for_status()
        server_ms = int(r.json()["serverTime"])
        self._time_offset_ms = server_ms - int(time.time() * 1000)
        self._offset_ts = time.time()

    def _signed_query(self, params: dict[str, Any]) -> str:
        if time.time() - self._offset_ts > 1800:
            self._refresh_time()
        params = {**params, "timestamp": self._now_ms(), "recvWindow": 5000}
        q = urllib.parse.urlencode(params)
        sig = sign_query(q, self.mode.secret)
        return f"{q}&signature={sig}"

    def _headers(self) -> dict[str, str]:
        return {"X-MBX-APIKEY": self.mode.key}

    def _check(self, r: httpx.Response) -> Any:
        if r.status_code >= 400:
            try:
                body = r.json()
                code = int(body.get("code", -1))
                msg = body.get("msg", r.text)
            except Exception:
                code, msg = -1, r.text
            if code == -1021:
                raise TimestampSkewError(code, msg)
            if code in (-1003, -1015):
                raise RateLimitError(code, msg)
            raise BinanceError(code, msg)
        self._log(r)
        return r.json()

    def _log(self, r: httpx.Response) -> None:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        date = time.strftime("%Y-%m-%d", time.gmtime())
        line = json.dumps({
            "ts": time.time(),
            "method": r.request.method,
            "path": r.request.url.path,
            "status": r.status_code,
            "weight": r.headers.get("X-MBX-USED-WEIGHT-1m"),
            "latency_ms": int(r.elapsed.total_seconds() * 1000),
        })
        (_LOG_DIR / f"{date}.jsonl").open("a").write(line + "\n")

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, TimestampSkewError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        reraise=True,
    )
    def get_signed(self, path: str, params: dict[str, Any] | None = None) -> Any:
        q = self._signed_query(params or {})
        r = self.http.get(f"{path}?{q}", headers=self._headers())
        return self._check(r)

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, TimestampSkewError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        reraise=True,
    )
    def post_signed(self, path: str, params: dict[str, Any]) -> Any:
        q = self._signed_query(params)
        r = self.http.post(f"{path}?{q}", headers=self._headers())
        return self._check(r)

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, TimestampSkewError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        reraise=True,
    )
    def delete_signed(self, path: str, params: dict[str, Any]) -> Any:
        q = self._signed_query(params)
        r = self.http.delete(f"{path}?{q}", headers=self._headers())
        return self._check(r)

    def get_public(self, path: str, params: dict[str, Any] | None = None) -> Any:
        r = self.http.get(path, params=params or {})
        return self._check(r)
```

- [ ] **Step 5: Run — expect PASS**

Run: `uv run pytest tests/unit/test_client_signing.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add nyaon_trading/binance/__init__.py nyaon_trading/binance/errors.py nyaon_trading/binance/client.py tests/unit/test_client_signing.py
git commit -m "feat: signed Binance HTTP client with retry and logging"
```

---

### Task 5: Market data module + klines fixture

**Files:**
- Create: `nyaon_trading/binance/market.py`
- Create: `tests/unit/fixtures/klines_btc_15m.json`

- [ ] **Step 1: Write deterministic klines fixture**

Create `tests/unit/fixtures/klines_btc_15m.json` with 50 candles (a simple uptrend then mean reversion). Use this exact content:

```json
[
  [1716000000000,"68000","68200","67900","68100","100",1716000899999,"6810000",500,"60","4086000","0"],
  [1716000900000,"68100","68300","68000","68200","105",1716001799999,"7161000",520,"63","4296600","0"],
  [1716001800000,"68200","68400","68100","68300","110",1716002699999,"7513000",540,"66","4507800","0"],
  [1716002700000,"68300","68500","68200","68400","115",1716003599999,"7866000",560,"69","4720000","0"],
  [1716003600000,"68400","68600","68300","68500","120",1716004499999,"8220000",580,"72","4932000","0"],
  [1716004500000,"68500","68700","68400","68600","125",1716005399999,"8575000",600,"75","5145000","0"],
  [1716005400000,"68600","68800","68500","68700","130",1716006299999,"8931000",620,"78","5358800","0"],
  [1716006300000,"68700","68900","68600","68800","135",1716007199999,"9288000",640,"81","5573200","0"],
  [1716007200000,"68800","69000","68700","68900","140",1716008099999,"9646000",660,"84","5788400","0"],
  [1716008100000,"68900","69100","68800","69000","145",1716008999999,"10005000",680,"87","6004200","0"],
  [1716009000000,"69000","69200","68900","69100","150",1716009899999,"10365000",700,"90","6219000","0"],
  [1716009900000,"69100","69300","69000","69200","155",1716010799999,"10726000",720,"93","6437600","0"],
  [1716010800000,"69200","69400","69100","69300","160",1716011699999,"11088000",740,"96","6652800","0"],
  [1716011700000,"69300","69500","69200","69400","165",1716012599999,"11451000",760,"99","6868600","0"],
  [1716012600000,"69400","69600","69300","69500","170",1716013499999,"11815000",780,"102","7085000","0"],
  [1716013500000,"69500","69700","69400","69600","175",1716014399999,"12180000",800,"105","7302000","0"],
  [1716014400000,"69600","69800","69500","69700","180",1716015299999,"12546000",820,"108","7519600","0"],
  [1716015300000,"69700","69900","69600","69800","185",1716016199999,"12913000",840,"111","7737800","0"],
  [1716016200000,"69800","70000","69700","69900","190",1716017099999,"13281000",860,"114","7956600","0"],
  [1716017100000,"69900","70100","69800","70000","195",1716017999999,"13650000",880,"117","8176000","0"],
  [1716018000000,"70000","70200","69900","70100","200",1716018899999,"14020000",900,"120","8396000","0"],
  [1716018900000,"70100","70300","70000","70200","205",1716019799999,"14391000",920,"123","8616600","0"],
  [1716019800000,"70200","70400","70100","70300","210",1716020699999,"14763000",940,"126","8837800","0"],
  [1716020700000,"70300","70500","70200","70400","215",1716021599999,"15136000",960,"129","9059600","0"],
  [1716021600000,"70400","70600","70300","70500","220",1716022499999,"15510000",980,"132","9282000","0"],
  [1716022500000,"70500","70300","70200","70300","225",1716023399999,"15820000",1000,"135","9492000","0"],
  [1716023400000,"70300","70200","70000","70100","230",1716024299999,"16100000",1020,"138","9659000","0"],
  [1716024300000,"70100","70000","69800","69900","235",1716025199999,"16400000",1040,"141","9846000","0"],
  [1716025200000,"69900","69800","69600","69700","240",1716026099999,"16700000",1060,"144","10030000","0"],
  [1716026100000,"69700","69600","69400","69500","245",1716026999999,"17000000",1080,"147","10210000","0"],
  [1716027000000,"69500","69400","69200","69300","250",1716027899999,"17300000",1100,"150","10395000","0"],
  [1716027900000,"69300","69200","69000","69100","255",1716028799999,"17615000",1120,"153","10580000","0"],
  [1716028800000,"69100","69000","68800","68900","260",1716029699999,"17934000",1140,"156","10770000","0"],
  [1716029700000,"68900","68800","68600","68700","265",1716030599999,"18238000",1160,"159","10956000","0"],
  [1716030600000,"68700","68600","68400","68500","270",1716031499999,"18549000",1180,"162","11147000","0"],
  [1716031500000,"68500","68400","68200","68300","275",1716032399999,"18790000",1200,"165","11335000","0"],
  [1716032400000,"68300","68400","68200","68350","280",1716033299999,"19138000",1220,"168","11537000","0"],
  [1716033300000,"68350","68500","68300","68450","285",1716034199999,"19508250",1240,"171","11733000","0"],
  [1716034200000,"68450","68600","68400","68550","290",1716035099999,"19879500",1260,"174","11923000","0"],
  [1716035100000,"68550","68700","68500","68650","295",1716035999999,"20251750",1280,"177","12121500","0"],
  [1716036000000,"68650","68800","68600","68750","300",1716036899999,"20625000",1300,"180","12303000","0"],
  [1716036900000,"68750","68900","68700","68850","305",1716037799999,"20999250",1320,"183","12484500","0"],
  [1716037800000,"68850","69000","68800","68950","310",1716038699999,"21374500",1340,"186","12660000","0"],
  [1716038700000,"68950","69100","68900","69050","315",1716039599999,"21750750",1360,"189","12831000","0"],
  [1716039600000,"69050","69200","69000","69150","320",1716040499999,"22128000",1380,"192","12990000","0"],
  [1716040500000,"69150","69300","69100","69250","325",1716041399999,"22506250",1400,"195","13145000","0"],
  [1716041400000,"69250","69400","69200","69350","330",1716042299999,"22885500",1420,"198","13290000","0"],
  [1716042300000,"69350","69500","69300","69450","335",1716043199999,"23265750",1440,"201","13427000","0"],
  [1716043200000,"69450","69600","69400","69550","340",1716044099999,"23647000",1460,"204","13559000","0"],
  [1716044100000,"69550","69700","69500","69650","345",1716044999999,"24029250",1480,"207","13680000","0"]
]
```

- [ ] **Step 2: Implement `market.py`**

Create `nyaon_trading/binance/market.py`:

```python
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from nyaon_trading.binance.client import BinanceClient

_CACHE = Path("state/cache")
_EXCHANGE_INFO_TTL = 12 * 3600
_KLINE_TTL = {"15m": 14 * 60, "5m": 4 * 60, "1m": 50}


def _read_cache(path: Path, ttl: int) -> Any | None:
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl:
        return None
    return json.loads(path.read_text())


def _write_cache(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(path)


def exchange_info(client: BinanceClient) -> dict[str, Any]:
    path = _CACHE / "exchangeInfo.json"
    cached = _read_cache(path, _EXCHANGE_INFO_TTL)
    if cached is not None:
        return cached
    data = client.get_public("/fapi/v1/exchangeInfo")
    _write_cache(path, data)
    return data


def klines(client: BinanceClient, symbol: str, interval: str, limit: int) -> pd.DataFrame:
    path = _CACHE / f"klines_{symbol}_{interval}_{limit}.json"
    ttl = _KLINE_TTL.get(interval, 60)
    data = _read_cache(path, ttl)
    if data is None:
        data = client.get_public(
            "/fapi/v1/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )
        _write_cache(path, data)
    return _to_frame(data)


def _to_frame(raw: list[list[Any]]) -> pd.DataFrame:
    cols = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_base", "taker_quote", "ignore",
    ]
    df = pd.DataFrame(raw, columns=cols)
    for c in ("open", "high", "low", "close", "volume", "quote_volume"):
        df[c] = df[c].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


def load_fixture(path: Path) -> pd.DataFrame:
    return _to_frame(json.loads(path.read_text()))
```

- [ ] **Step 3: Commit**

```bash
git add nyaon_trading/binance/market.py tests/unit/fixtures/klines_btc_15m.json
git commit -m "feat: market data module with disk-cached klines + fixture"
```

---

### Task 6: Trend strategy (TDD)

**Files:**
- Create: `tests/unit/test_trend.py`
- Create: `nyaon_trading/strategy/__init__.py` (empty)
- Create: `nyaon_trading/strategy/trend.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_trend.py`:

```python
from pathlib import Path

from nyaon_trading.binance.market import load_fixture
from nyaon_trading.strategy.trend import score


def test_trend_score_uptrend_returns_buy_signal():
    df = load_fixture(Path("tests/unit/fixtures/klines_btc_15m.json"))
    s = score(df)
    assert s is not None
    assert s.side == "BUY"
    assert 0 < s.strength <= 1


def test_trend_score_needs_min_bars():
    df = load_fixture(Path("tests/unit/fixtures/klines_btc_15m.json")).iloc[:10]
    s = score(df)
    assert s is None
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/unit/test_trend.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `trend.py`**

Create `nyaon_trading/strategy/__init__.py` (empty) and `nyaon_trading/strategy/trend.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


@dataclass(frozen=True)
class TrendSignal:
    side: Literal["BUY", "SELL"]
    strength: float
    suggested_sl_bps: int
    suggested_tp_bps: int


def score(df: pd.DataFrame, donchian: int = 20, ema_fast: int = 50, ema_slow: int = 200) -> TrendSignal | None:
    if len(df) < max(donchian, ema_slow):
        return None
    close = df["close"]
    high = df["high"]
    low = df["low"]
    upper = high.iloc[-donchian:-1].max()
    lower = low.iloc[-donchian:-1].min()
    ef = close.ewm(span=ema_fast, adjust=False).mean().iloc[-1]
    es = close.ewm(span=ema_slow, adjust=False).mean().iloc[-1]
    last = close.iloc[-1]
    if last > upper and ef > es:
        strength = min(1.0, (last - upper) / max(upper - lower, 1e-9))
        return TrendSignal("BUY", round(strength, 4), suggested_sl_bps=80, suggested_tp_bps=160)
    if last < lower and ef < es:
        strength = min(1.0, (lower - last) / max(upper - lower, 1e-9))
        return TrendSignal("SELL", round(strength, 4), suggested_sl_bps=80, suggested_tp_bps=160)
    return None
```

- [ ] **Step 4: Adjust ema_slow to fit 50-row fixture**

The fixture only has 50 bars. Update the test to pass `ema_slow=30` to `score`:

Edit `tests/unit/test_trend.py` first test:

```python
def test_trend_score_uptrend_returns_buy_signal():
    df = load_fixture(Path("tests/unit/fixtures/klines_btc_15m.json"))
    s = score(df, ema_slow=30)
    assert s is not None
    assert s.side == "BUY"
    assert 0 < s.strength <= 1
```

- [ ] **Step 5: Run — expect PASS**

Run: `uv run pytest tests/unit/test_trend.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add nyaon_trading/strategy/__init__.py nyaon_trading/strategy/trend.py tests/unit/test_trend.py
git commit -m "feat: deterministic trend (donchian + EMA) strategy"
```

---

### Task 7: Mean-reversion strategy (TDD)

**Files:**
- Create: `tests/unit/test_mean_reversion.py`
- Create: `nyaon_trading/strategy/mean_reversion.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_mean_reversion.py`:

```python
import numpy as np
import pandas as pd

from nyaon_trading.strategy.mean_reversion import score


def _frame(closes: list[float]) -> pd.DataFrame:
    n = len(closes)
    return pd.DataFrame({
        "open_time": pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC"),
        "open": closes,
        "high": [c + 1 for c in closes],
        "low": [c - 1 for c in closes],
        "close": closes,
        "volume": [100.0] * n,
    })


def test_mean_reversion_buy_on_lower_band_with_oversold_rsi():
    base = [100.0] * 30
    crash = list(np.linspace(100, 80, 10))
    df = _frame(base + crash)
    s = score(df)
    assert s is not None
    assert s.side == "BUY"


def test_mean_reversion_no_signal_when_in_band():
    df = _frame([100.0 + (i % 3 - 1) * 0.1 for i in range(40)])
    s = score(df)
    assert s is None
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/unit/test_mean_reversion.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `mean_reversion.py`**

Create `nyaon_trading/strategy/mean_reversion.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


@dataclass(frozen=True)
class MRSignal:
    side: Literal["BUY", "SELL"]
    strength: float
    suggested_sl_bps: int
    suggested_tp_bps: int


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def score(df: pd.DataFrame, window: int = 20, sigma: float = 2.0) -> MRSignal | None:
    if len(df) < max(window, 14) + 1:
        return None
    close = df["close"]
    mean = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = mean + sigma * std
    lower = mean - sigma * std
    rsi = _rsi(close)
    last = close.iloc[-1]
    if last < lower.iloc[-1] and rsi.iloc[-1] < 30:
        strength = min(1.0, float((lower.iloc[-1] - last) / max(std.iloc[-1], 1e-9)))
        return MRSignal("BUY", round(strength, 4), suggested_sl_bps=60, suggested_tp_bps=90)
    if last > upper.iloc[-1] and rsi.iloc[-1] > 70:
        strength = min(1.0, float((last - upper.iloc[-1]) / max(std.iloc[-1], 1e-9)))
        return MRSignal("SELL", round(strength, 4), suggested_sl_bps=60, suggested_tp_bps=90)
    return None
```

- [ ] **Step 4: Run — expect PASS**

Run: `uv run pytest tests/unit/test_mean_reversion.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add nyaon_trading/strategy/mean_reversion.py tests/unit/test_mean_reversion.py
git commit -m "feat: mean-reversion (bollinger + RSI) strategy"
```

---

### Task 8: Pipeline + signals CLI

**Files:**
- Create: `nyaon_trading/strategy/pipeline.py`
- Create: `nyaon_trading/cli/__init__.py`
- Create: `nyaon_trading/cli/signals.py`

- [ ] **Step 1: Write `pipeline.py`**

Create `nyaon_trading/strategy/pipeline.py`:

```python
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.binance.market import exchange_info, klines
from nyaon_trading.config import Mode
from nyaon_trading.strategy import mean_reversion, trend

_OUT = Path("state/signals")
_MIN_QUOTE_VOL_24H = 50_000_000


def _eligible_symbols(info: dict[str, Any]) -> list[str]:
    return [
        s["symbol"]
        for s in info.get("symbols", [])
        if s.get("status") == "TRADING"
        and s.get("quoteAsset") == "USDT"
        and s.get("contractType") == "PERPETUAL"
    ]


def run(mode: Mode, client: BinanceClient, max_symbols: int = 20) -> Path:
    info = exchange_info(client)
    symbols = _eligible_symbols(info)[:max_symbols]
    signals: list[dict[str, Any]] = []
    ts = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
    for sym in symbols:
        try:
            df = klines(client, sym, "15m", 200)
        except Exception:
            continue
        for src_name, mod in (("trend", trend), ("mean_reversion", mean_reversion)):
            s = mod.score(df)
            if s is None:
                continue
            ttl = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 15 * 60)
            )
            signals.append({
                "symbol": sym,
                "side": s.side,
                "strength": s.strength,
                "suggested_sl_bps": s.suggested_sl_bps,
                "suggested_tp_bps": s.suggested_tp_bps,
                "ttl": ttl,
                "source": src_name,
            })
    _OUT.mkdir(parents=True, exist_ok=True)
    path = _OUT / f"{ts}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ts": ts, "signals": signals}, indent=2))
    tmp.replace(path)
    return path
```

- [ ] **Step 2: Write dispatcher and signals CLI**

Create `nyaon_trading/cli/__init__.py`:

```python
from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: nyaon <command> [args]", file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "signals":
        from nyaon_trading.cli.signals import run
        return run(rest)
    if cmd == "klines":
        from nyaon_trading.cli.klines import run
        return run(rest)
    if cmd == "account":
        from nyaon_trading.cli.account import run
        return run(rest)
    if cmd == "snapshot":
        from nyaon_trading.cli.snapshot import run
        return run(rest)
    if cmd == "place-order":
        from nyaon_trading.cli.place_order import run
        return run(rest)
    if cmd == "cancel":
        from nyaon_trading.cli.cancel import run
        return run(rest)
    if cmd == "mode":
        from nyaon_trading.cli.mode import run
        return run(rest)
    if cmd in ("halt", "resume"):
        from nyaon_trading.cli.halt import run
        return run([cmd, *rest])
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `nyaon_trading/cli/signals.py`:

```python
from __future__ import annotations

import json

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.config import load_mode
from nyaon_trading.strategy.pipeline import run as run_pipeline


def run(argv: list[str]) -> int:
    mode = load_mode()
    client = BinanceClient(mode)
    path = run_pipeline(mode, client)
    print(json.dumps({"path": str(path)}))
    return 0
```

- [ ] **Step 3: Commit**

```bash
git add nyaon_trading/strategy/pipeline.py nyaon_trading/cli/__init__.py nyaon_trading/cli/signals.py
git commit -m "feat: signal pipeline + signals CLI entry"
```

---

### Task 9: Account + klines + snapshot CLIs

**Files:**
- Create: `nyaon_trading/binance/account.py`
- Create: `nyaon_trading/cli/account.py`
- Create: `nyaon_trading/cli/klines.py`
- Create: `nyaon_trading/recon/__init__.py` (empty)
- Create: `nyaon_trading/recon/snapshot.py`
- Create: `nyaon_trading/cli/snapshot.py`
- Create: `tests/unit/test_snapshot_diff.py`

- [ ] **Step 1: Implement `account.py`**

Create `nyaon_trading/binance/account.py`:

```python
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
```

- [ ] **Step 2: Account + klines CLIs**

Create `nyaon_trading/cli/account.py`:

```python
from __future__ import annotations

import json

from nyaon_trading.binance.account import account
from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.config import load_mode


def run(argv: list[str]) -> int:
    mode = load_mode()
    client = BinanceClient(mode)
    print(json.dumps(account(client), indent=2))
    return 0
```

Create `nyaon_trading/cli/klines.py`:

```python
from __future__ import annotations

import json

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.binance.market import klines
from nyaon_trading.config import load_mode


def run(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: nyaon klines <symbol> <interval> <limit>", end="\n")
        return 2
    symbol, interval, limit = argv[0], argv[1], int(argv[2])
    mode = load_mode()
    client = BinanceClient(mode)
    df = klines(client, symbol, interval, limit)
    print(df.tail(10).to_json(orient="records"))
    return 0
```

- [ ] **Step 3: Write snapshot diff test**

Create `tests/unit/test_snapshot_diff.py`:

```python
from nyaon_trading.recon.snapshot import classify_diff


def test_clean_diff():
    prev = {"equity": 1000, "positions": [], "open_orders": []}
    curr = {"equity": 1000, "positions": [], "open_orders": []}
    assert classify_diff(prev, curr) == "clean"


def test_benign_fee_drift():
    prev = {"equity": 1000.0, "positions": [], "open_orders": []}
    curr = {"equity": 999.6, "positions": [], "open_orders": []}
    assert classify_diff(prev, curr) == "benign"


def test_critical_balance_drift_without_trade():
    prev = {"equity": 1000.0, "positions": [], "open_orders": []}
    curr = {"equity": 994.0, "positions": [], "open_orders": []}
    assert classify_diff(prev, curr) == "critical"


def test_critical_position_mismatch():
    prev = {"equity": 1000.0, "positions": [{"symbol": "BTCUSDT", "qty": 0.01}], "open_orders": []}
    curr = {"equity": 1000.0, "positions": [{"symbol": "BTCUSDT", "qty": 0.03}], "open_orders": []}
    assert classify_diff(prev, curr, recent_trade_qty=0.0) == "critical"
```

- [ ] **Step 4: Run — expect FAIL**

Run: `uv run pytest tests/unit/test_snapshot_diff.py -v`
Expected: ImportError.

- [ ] **Step 5: Implement `snapshot.py`**

Create `nyaon_trading/recon/__init__.py` (empty) and `nyaon_trading/recon/snapshot.py`:

```python
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
    if eq_drift > 0.001:
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
    tmp.write_text(json.dumps({"ts": curr["ts"], "kind": "recon_critical", "detail": {"reason": reason, "snapshot": curr}}, indent=2))
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
```

- [ ] **Step 6: Run — expect PASS**

Run: `uv run pytest tests/unit/test_snapshot_diff.py -v`
Expected: 4 passed.

- [ ] **Step 7: Snapshot CLI**

Create `nyaon_trading/cli/snapshot.py`:

```python
from __future__ import annotations

import json

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.config import load_mode
from nyaon_trading.recon.snapshot import run_full


def run(argv: list[str]) -> int:
    mode = load_mode()
    client = BinanceClient(mode)
    cls, path = run_full(client)
    print(json.dumps({"classification": cls, "path": str(path)}))
    return 0 if cls != "critical" else 3
```

- [ ] **Step 8: Commit**

```bash
git add nyaon_trading/binance/account.py nyaon_trading/cli/account.py nyaon_trading/cli/klines.py nyaon_trading/recon/__init__.py nyaon_trading/recon/snapshot.py nyaon_trading/cli/snapshot.py tests/unit/test_snapshot_diff.py
git commit -m "feat: account, klines, snapshot CLIs and recon diff"
```

---

### Task 10: Orders module + coid (TDD)

**Files:**
- Create: `tests/unit/test_orders_coid.py`
- Create: `nyaon_trading/binance/orders.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_orders_coid.py`:

```python
from nyaon_trading.binance.orders import coid_for, sl_coid, tp_coid


def test_coid_deterministic():
    assert coid_for("intent_abc", 0) == "intent_abc-0"
    assert coid_for("intent_abc", 1) == "intent_abc-1"


def test_paired_coids():
    assert sl_coid("intent_abc", 0) == "intent_abc-0-sl"
    assert tp_coid("intent_abc", 0) == "intent_abc-0-tp"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/unit/test_orders_coid.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `orders.py`**

Create `nyaon_trading/binance/orders.py`:

```python
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nyaon_trading.binance.client import BinanceClient

_ORDERS = Path("state/orders")
_LEV_CACHE: dict[str, int] = {}


def coid_for(intent_id: str, attempt: int) -> str:
    return f"{intent_id}-{attempt}"


def sl_coid(intent_id: str, attempt: int) -> str:
    return f"{coid_for(intent_id, attempt)}-sl"


def tp_coid(intent_id: str, attempt: int) -> str:
    return f"{coid_for(intent_id, attempt)}-tp"


@dataclass
class OrderResult:
    coid: str
    symbol: str
    side: str
    type: str
    status: str
    qty: float
    price: float | None
    stop_price: float | None
    avg_fill_price: float | None
    ts: str
    intent_id: str
    attempt: int


def _persist(o: OrderResult) -> Path:
    _ORDERS.mkdir(parents=True, exist_ok=True)
    path = _ORDERS / f"{o.coid}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(o), indent=2))
    tmp.replace(path)
    return path


def set_leverage(client: BinanceClient, symbol: str, leverage: int) -> None:
    if _LEV_CACHE.get(symbol) == leverage:
        return
    client.post_signed("/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage})
    _LEV_CACHE[symbol] = leverage


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def place_market(client: BinanceClient, intent: dict[str, Any], qty: float, attempt: int = 0) -> OrderResult:
    coid = coid_for(intent["id"], attempt)
    body = client.post_signed("/fapi/v1/order", {
        "symbol": intent["symbol"],
        "side": intent["side"],
        "type": "MARKET",
        "quantity": qty,
        "newClientOrderId": coid,
    })
    r = OrderResult(
        coid=coid,
        symbol=intent["symbol"],
        side=intent["side"],
        type="MARKET",
        status=body.get("status", "NEW"),
        qty=qty,
        price=None,
        stop_price=None,
        avg_fill_price=float(body.get("avgPrice", 0)) or None,
        ts=_now(),
        intent_id=intent["id"],
        attempt=attempt,
    )
    _persist(r)
    return r


def place_stop(client: BinanceClient, intent: dict[str, Any], stop_price: float, attempt: int = 0) -> OrderResult:
    coid = sl_coid(intent["id"], attempt)
    opposite = "SELL" if intent["side"] == "BUY" else "BUY"
    body = client.post_signed("/fapi/v1/order", {
        "symbol": intent["symbol"],
        "side": opposite,
        "type": "STOP_MARKET",
        "stopPrice": stop_price,
        "closePosition": "true",
        "newClientOrderId": coid,
    })
    r = OrderResult(
        coid=coid,
        symbol=intent["symbol"],
        side=opposite,
        type="STOP_MARKET",
        status=body.get("status", "NEW"),
        qty=0.0,
        price=None,
        stop_price=stop_price,
        avg_fill_price=None,
        ts=_now(),
        intent_id=intent["id"],
        attempt=attempt,
    )
    _persist(r)
    return r


def place_take_profit(client: BinanceClient, intent: dict[str, Any], tp_price: float, attempt: int = 0) -> OrderResult:
    coid = tp_coid(intent["id"], attempt)
    opposite = "SELL" if intent["side"] == "BUY" else "BUY"
    body = client.post_signed("/fapi/v1/order", {
        "symbol": intent["symbol"],
        "side": opposite,
        "type": "TAKE_PROFIT_MARKET",
        "stopPrice": tp_price,
        "closePosition": "true",
        "newClientOrderId": coid,
    })
    r = OrderResult(
        coid=coid,
        symbol=intent["symbol"],
        side=opposite,
        type="TAKE_PROFIT_MARKET",
        status=body.get("status", "NEW"),
        qty=0.0,
        price=None,
        stop_price=tp_price,
        avg_fill_price=None,
        ts=_now(),
        intent_id=intent["id"],
        attempt=attempt,
    )
    _persist(r)
    return r


def cancel_order(client: BinanceClient, symbol: str, coid: str) -> dict[str, Any]:
    return client.delete_signed("/fapi/v1/order", {"symbol": symbol, "origClientOrderId": coid})
```

- [ ] **Step 4: Run — expect PASS**

Run: `uv run pytest tests/unit/test_orders_coid.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add nyaon_trading/binance/orders.py tests/unit/test_orders_coid.py
git commit -m "feat: orders module with deterministic coid and SL/TP pairing"
```

---

### Task 11: Halt flag + place-order CLI (TDD)

**Files:**
- Create: `tests/unit/test_halt.py`
- Create: `nyaon_trading/cli/place_order.py`
- Create: `nyaon_trading/cli/cancel.py`
- Create: `nyaon_trading/cli/halt.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_halt.py`:

```python
import json
from pathlib import Path

import pytest

from nyaon_trading.cli.place_order import refuse_if_halted, HaltedError


def test_refuse_when_halt_flag_present(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "halt.flag").write_text("halted for test\n")
    with pytest.raises(HaltedError):
        refuse_if_halted()


def test_allow_when_no_halt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    refuse_if_halted()  # no raise
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/unit/test_halt.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement place-order CLI**

Create `nyaon_trading/cli/place_order.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.binance.orders import (
    place_market,
    place_stop,
    place_take_profit,
    set_leverage,
)
from nyaon_trading.config import load_mode

_HALT = Path("state/halt.flag")
_INTENTS = Path("state/intents")


class HaltedError(RuntimeError):
    pass


def refuse_if_halted() -> None:
    if _HALT.exists():
        raise HaltedError(f"HALTED: {_HALT.read_text().strip()}")


def _ticker_price(client: BinanceClient, symbol: str) -> float:
    body = client.get_public("/fapi/v1/ticker/price", {"symbol": symbol})
    return float(body["price"])


def _qty_from_quote(quote_amount: float, price: float) -> float:
    raw = quote_amount / price
    # round to 3 decimals for major perps; safe default for testnet
    return round(raw, 3)


def run(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="nyaon place-order")
    p.add_argument("--intent", required=True)
    args = p.parse_args(argv)
    try:
        refuse_if_halted()
    except HaltedError as e:
        print(str(e), file=sys.stderr)
        return 2
    mode = load_mode()
    intent_path = Path(args.intent)
    intent = json.loads(intent_path.read_text())
    client = BinanceClient(mode)
    if intent["status"] != "approved":
        print(f"intent status={intent['status']} not approved", file=sys.stderr)
        return 2
    leverage = int(intent.get("leverage", 3))
    set_leverage(client, intent["symbol"], leverage)
    price = _ticker_price(client, intent["symbol"])
    qty_quote = float(intent["qty_quote"]) * mode.live_size_multiplier if mode.name == "live" else float(intent["qty_quote"])
    qty = _qty_from_quote(qty_quote, price)
    entry = place_market(client, intent, qty, attempt=0)
    # poll fill
    avg = entry.avg_fill_price
    for _ in range(5):
        if avg:
            break
        time.sleep(1)
        body = client.get_signed("/fapi/v1/order", {"symbol": intent["symbol"], "origClientOrderId": entry.coid})
        avg = float(body.get("avgPrice", 0)) or None
    if not avg:
        intent["status"] = "failed"
        intent["failed_reason"] = "entry did not fill within 5s"
        intent_path.write_text(json.dumps(intent, indent=2))
        return 3
    bps = lambda x: x / 10_000
    sl_price = avg * (1 - bps(int(intent["sl_bps"]))) if intent["side"] == "BUY" else avg * (1 + bps(int(intent["sl_bps"])))
    tp_price = avg * (1 + bps(int(intent["tp_bps"]))) if intent["side"] == "BUY" else avg * (1 - bps(int(intent["tp_bps"])))
    place_stop(client, intent, round(sl_price, 2), attempt=0)
    place_take_profit(client, intent, round(tp_price, 2), attempt=0)
    intent["status"] = "filled"
    intent["filled_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    intent_path.write_text(json.dumps(intent, indent=2))
    print(json.dumps({"coid": entry.coid, "avg_fill_price": avg, "qty": qty}))
    return 0
```

- [ ] **Step 4: Cancel + halt CLIs**

Create `nyaon_trading/cli/cancel.py`:

```python
from __future__ import annotations

import argparse
import json

from nyaon_trading.binance.client import BinanceClient
from nyaon_trading.binance.orders import cancel_order
from nyaon_trading.config import load_mode


def run(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="nyaon cancel")
    p.add_argument("--symbol", required=True)
    p.add_argument("--coid", required=True)
    a = p.parse_args(argv)
    mode = load_mode()
    client = BinanceClient(mode)
    print(json.dumps(cancel_order(client, a.symbol, a.coid)))
    return 0
```

Create `nyaon_trading/cli/halt.py`:

```python
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_HALT = Path("state/halt.flag")


def run(argv: list[str]) -> int:
    cmd = argv[0]
    rest = argv[1:]
    if cmd == "halt":
        p = argparse.ArgumentParser(prog="nyaon halt")
        p.add_argument("--reason", required=True)
        a = p.parse_args(rest)
        _HALT.parent.mkdir(parents=True, exist_ok=True)
        _HALT.write_text(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {a.reason}\n")
        print(f"halted: {a.reason}")
        return 0
    if cmd == "resume":
        if _HALT.exists():
            _HALT.unlink()
            print("resumed")
        else:
            print("not halted", file=sys.stderr)
        return 0
    print(f"unknown subcommand: {cmd}", file=sys.stderr)
    return 2
```

- [ ] **Step 5: Run — expect PASS**

Run: `uv run pytest tests/unit/test_halt.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add nyaon_trading/cli/place_order.py nyaon_trading/cli/cancel.py nyaon_trading/cli/halt.py tests/unit/test_halt.py
git commit -m "feat: place-order with halt enforcement + cancel + halt/resume CLIs"
```

---

### Task 12: Mode CLI with go-live gating (TDD)

**Files:**
- Create: `tests/unit/test_mode_gating.py`
- Create: `nyaon_trading/cli/mode.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_mode_gating.py`:

```python
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
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/unit/test_mode_gating.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `mode.py`**

Create `nyaon_trading/cli/mode.py`:

```python
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
```

- [ ] **Step 4: Run — expect PASS**

Run: `uv run pytest tests/unit/test_mode_gating.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add nyaon_trading/cli/mode.py tests/unit/test_mode_gating.py
git commit -m "feat: mode CLI with hard-gated testnet -> live cutover"
```

---

### Task 13: `bin/nyaon` shebang + smoke test

**Files:**
- Create: `bin/nyaon`

- [ ] **Step 1: Write `bin/nyaon`**

Create `bin/nyaon`:

```bash
#!/usr/bin/env -S uv run python -m nyaon_trading.cli
```

(Yes — that one-liner is the whole file. The shebang invokes `uv run` which auto-syncs deps and executes the package's `__main__`-equivalent dispatcher.)

- [ ] **Step 2: Make executable**

Run: `chmod +x bin/nyaon`

- [ ] **Step 3: Smoke test**

Run from project root:

```bash
mkdir -p state
cat > state/mode.json <<'EOF'
{"mode":"testnet","set_by":"bootstrap","set_at":"2026-05-19T00:00:00Z","reason":"init","live_size_multiplier":1.0}
EOF
BINANCE_TESTNET_API_KEY=dummy BINANCE_TESTNET_API_SECRET=dummy ./bin/nyaon mode show
```

Expected: prints the mode.json contents.

- [ ] **Step 4: Commit**

```bash
git add bin/nyaon
git commit -m "feat: bin/nyaon uv-run shebang entry"
```

---

### Task 14: Integration test scaffold (testnet)

**Files:**
- Create: `tests/integration/__init__.py` (empty)
- Create: `tests/integration/conftest.py`
- Create: `tests/integration/test_account.py`
- Create: `tests/integration/test_klines.py`
- Create: `tests/integration/test_round_trip.py`
- Create: `tests/integration/test_idempotency.py`
- Create: `tests/integration/test_rate_limit.py`

- [ ] **Step 1: Write `conftest.py`**

Create `tests/integration/conftest.py`:

```python
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
```

- [ ] **Step 2: Write `test_account.py`**

```python
def test_account_returns_balance(client):
    from nyaon_trading.binance.account import account
    a = account(client)
    assert "totalWalletBalance" in a
    assert float(a["availableBalance"]) >= 0
```

- [ ] **Step 3: Write `test_klines.py`**

```python
def test_klines_monotonic(client):
    from nyaon_trading.binance.market import klines
    df = klines(client, "BTCUSDT", "15m", 50)
    assert len(df) == 50
    assert df["open_time"].is_monotonic_increasing
```

- [ ] **Step 4: Write `test_round_trip.py`**

```python
import time

import pytest

from nyaon_trading.binance.orders import (
    cancel_order, place_market, place_stop, place_take_profit, set_leverage, sl_coid, tp_coid,
)


@pytest.mark.timeout(30)
def test_market_round_trip(client):
    intent = {
        "id": f"itest_{int(time.time())}",
        "symbol": "BTCUSDT",
        "side": "BUY",
    }
    set_leverage(client, "BTCUSDT", 3)
    entry = place_market(client, intent, qty=0.002, attempt=0)
    assert entry.coid.startswith(intent["id"])
    # paired protective orders
    place_stop(client, intent, stop_price=1.0, attempt=0)
    place_take_profit(client, intent, tp_price=10_000_000.0, attempt=0)
    # cancel them so we don't leave open orders
    cancel_order(client, "BTCUSDT", sl_coid(intent["id"], 0))
    cancel_order(client, "BTCUSDT", tp_coid(intent["id"], 0))
    # close the position by placing opposite market
    close_intent = {**intent, "id": intent["id"] + "_close", "side": "SELL"}
    place_market(client, close_intent, qty=0.002, attempt=0)
```

- [ ] **Step 5: Write `test_idempotency.py`**

```python
import time

import pytest

from nyaon_trading.binance.errors import BinanceError
from nyaon_trading.binance.orders import place_market, place_stop, place_take_profit, cancel_order, sl_coid, tp_coid


@pytest.mark.timeout(30)
def test_duplicate_coid_rejected(client):
    intent = {"id": f"idem_{int(time.time())}", "symbol": "BTCUSDT", "side": "BUY"}
    first = place_market(client, intent, qty=0.002, attempt=0)
    with pytest.raises(BinanceError):
        place_market(client, intent, qty=0.002, attempt=0)  # same coid -> reject
    # cleanup
    close = {**intent, "id": intent["id"] + "_close", "side": "SELL"}
    place_market(client, close, qty=0.002, attempt=0)
```

- [ ] **Step 6: Write `test_rate_limit.py`**

```python
def test_burst_does_not_ban(client):
    from nyaon_trading.binance.market import klines
    for _ in range(20):
        df = klines(client, "BTCUSDT", "1m", 100)
        assert len(df) == 100
```

- [ ] **Step 7: Commit**

```bash
git add tests/integration/
git commit -m "test: integration suite scaffolded against Binance testnet (gated)"
```

---

### Task 15: Wire skills, tasks, and README

**Files:**
- Modify: `skills/exchange-ops/SKILL.md` (append "Implementation" section pointing at `nyaon` CLI)
- Modify: `skills/signal-pipeline/SKILL.md` (point Quant at `nyaon signals` + reading `state/signals/<ts>.json`)
- Modify: `agents/trader/AGENTS.md` (Trader runs `uv run nyaon place-order --intent <path>`)
- Modify: `agents/ops/AGENTS.md` (Ops runs `uv run nyaon snapshot`)
- Modify: `agents/quant/AGENTS.md` (Quant runs `uv run nyaon signals` then reads latest `state/signals/*.json`)
- Modify: `agents/cro/AGENTS.md` (CRO can run `uv run nyaon halt --reason '...'`)
- Modify: `agents/ceo/AGENTS.md` (CEO sole role for `uv run nyaon mode set live/testnet`)
- Modify: `tasks/promotion-audit/TASK.md` (must run `uv run pytest` + audit script + write `state/audits/promotion-<date>.json`)
- Modify: `README.md` (add "Code & tooling" section + `uv sync` quickstart)

- [ ] **Step 1: Append to `skills/exchange-ops/SKILL.md`**

Append at end of file:

```markdown
## Implementation

All endpoints in this skill are implemented in the `nyaon_trading` Python package. Agents call them via the `nyaon` CLI (see `bin/nyaon`). Build/run with `uv`:

| Action | Command |
|---|---|
| Account snapshot | `uv run nyaon account` |
| Klines | `uv run nyaon klines <SYM> <interval> <limit>` |
| Place order | `uv run nyaon place-order --intent state/intents/<id>.json` |
| Cancel order | `uv run nyaon cancel --symbol <SYM> --coid <coid>` |
| Reconcile | `uv run nyaon snapshot` |
| Halt / resume | `uv run nyaon halt --reason '...'` / `uv run nyaon resume` |
| Mode switch | `uv run nyaon mode show` / `uv run nyaon mode set testnet\|live --reason '...'` |

All CLIs emit JSON on stdout and exit non-zero on failure. Mode + secrets resolved from `state/mode.json` and env at every invocation.
```

- [ ] **Step 2: Append to `skills/signal-pipeline/SKILL.md`**

Append:

```markdown
## Implementation

Signal computation is deterministic Python in `nyaon_trading.strategy.pipeline`. Quant agent runs:

```
uv run nyaon signals
```

This writes `state/signals/<utc_iso>.json`. Quant reads the newest file, applies meta-judgement (skip stale, gate by RISK_POLICY caps, dedupe vs open intents), and writes one or more intents to `state/intents/<intent_id>.json` with `status="proposed"`.
```

- [ ] **Step 3: Update each agent AGENTS.md**

For each of `agents/{quant,trader,ops,cro,ceo}/AGENTS.md`, append a "Tooling" section naming the exact `uv run nyaon ...` commands that role is allowed to invoke. The CEO file additionally states `NYAON_AGENT_ROLE=ceo` is set in the paperclip agent env so `nyaon mode set live` is permitted only here.

Example for `agents/trader/AGENTS.md`:

```markdown
## Tooling

Trader may invoke:
- `uv run nyaon place-order --intent <intent-path>`
- `uv run nyaon cancel --symbol <SYM> --coid <coid>`

Trader must not invoke `nyaon mode set ...` (CEO only) or `nyaon halt` (CRO/Ops only).
```

Mirror the pattern for the other four agents, each listing only the commands appropriate to its role.

- [ ] **Step 4: Update `tasks/promotion-audit/TASK.md`**

Append a "Procedure" section:

```markdown
## Procedure (executed by promotion-audit task)

1. `uv sync --frozen`
2. `uv run pytest tests/unit -q` — must pass.
3. `RUN_TESTNET_TESTS=1 uv run pytest tests/integration -q` — must pass.
4. Compute metrics from `state/orders/*.json` and `state/snapshots/*.json` for the last 5 trading days.
5. Write `state/audits/promotion-<YYYY-MM-DD>.json` per `state/.schemas/promotion-audit.json`.
6. CEO reads the audit on Sunday retro. If `pass=true` and ≤24h old, CEO may run `uv run nyaon mode set live --reason 'week-2 audit pass'`.
```

- [ ] **Step 5: Update `README.md`**

Append a "Code & tooling" section:

```markdown
## Code & tooling

The trading code lives in `nyaon_trading/` and is exposed as the `nyaon` CLI. The package is managed exclusively by [`uv`](https://docs.astral.sh/uv/) — no `pip`, `poetry`, `conda`, `pyenv`, or `pipx`.

### Quickstart

```bash
uv sync                                  # install deps from uv.lock
uv run pytest tests/unit -q              # unit tests, no network

# Integration (testnet):
export BINANCE_TESTNET_API_KEY=...
export BINANCE_TESTNET_API_SECRET=...
RUN_TESTNET_TESTS=1 uv run pytest tests/integration -q

# Run CLIs:
./bin/nyaon mode show
./bin/nyaon signals
./bin/nyaon snapshot
```

### Adding dependencies

```bash
uv add <package>          # also updates uv.lock
uv lock --upgrade-package <package>
```
```

- [ ] **Step 6: Commit**

```bash
git add skills/exchange-ops/SKILL.md skills/signal-pipeline/SKILL.md agents/*/AGENTS.md tasks/promotion-audit/TASK.md README.md
git commit -m "docs: point existing skills/agents/tasks at the new nyaon CLI"
```

---

### Task 16: Lint, type, and full unit run

- [ ] **Step 1: Run lint + format check**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: zero violations. Fix any reported issues inline (whitespace, imports).

- [ ] **Step 2: Run type checker**

Run: `uv run pyright nyaon_trading`
Expected: zero errors. If any unresolved imports report, fix the offending file.

- [ ] **Step 3: Full unit suite**

Run: `uv run pytest tests/unit -v`
Expected: all tests pass (config 3, signing 1, trend 2, mean_reversion 2, orders_coid 2, snapshot_diff 4, halt 2, mode_gating 5 = 21 tests).

- [ ] **Step 4: Commit any fixes**

```bash
git add -u
git commit -m "chore: lint and type-check pass"
```

(Skip this commit if step 1-3 found nothing.)

---

## Self-review

**Spec coverage:**
- §4 Architecture → Tasks 1, 13 (bootstrap, bin shebang)
- §5 Components (config) → Task 3
- §5 Components (client) → Task 4
- §5 Components (market) → Task 5
- §5 Components (account) → Task 9
- §5 Components (orders) → Task 10
- §5 Components (strategy.pipeline / trend / mean_reversion) → Tasks 6, 7, 8
- §5 Components (recon.snapshot) → Task 9
- §5 Components (CLI surface) → Tasks 8, 9, 11, 12, 13
- §6 Data flow (intents, orders, snapshots, atomic writes) → Tasks 8-11
- §6.1 Halt semantics → Task 11
- §6.2 Idempotency (coid + attempt) → Tasks 10, 14
- §6.3 State directory + schemas → Task 2
- §7 Testing (unit + integration + CI surface) → Tasks 3, 4, 6, 7, 9-12, 14, 16
- §7.4 Pre-promotion gate procedure → Task 15
- §8 Go-live gating (preconditions, role check, ramp multiplier, rollback) → Task 12
- §9 Dependencies → Task 1
- Agent/skill/task wiring → Task 15

**Placeholder scan:** No "TBD", "TODO", or "implement later" in any step. Every code block is concrete and runnable.

**Type consistency:**
- `Mode` dataclass fields (`name`, `base_url`, `key`, `secret`, `live_size_multiplier`) match across `config.py` and `tests/integration/conftest.py`.
- `OrderResult` fields match schema in Task 2 and usage in Task 10.
- `coid_for`, `sl_coid`, `tp_coid` signatures consistent between Task 10 (definition) and Tasks 11, 14 (consumers).
- `classify_diff` signature `(prev, curr, recent_trade_qty=0.0)` consistent between Task 9 test and implementation.
- `set_live(reason: str)` raises `GoLiveRefused` — consistent between Task 12 test and implementation.

Plan ready for execution.
