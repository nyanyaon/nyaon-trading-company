# Binance Connectivity & Strategy Execution — Design

**Date:** 2026-05-19
**Owner:** CEO
**Status:** Approved (brainstorming phase)
**Supersedes:** N/A (first implementation spec)

## 1. Purpose

The Nyaon Trading Company has agent roles (CEO, CRO, Quant, Trader, Ops), governance policy (`RISK_POLICY.md`), skills (`exchange-ops`, `risk-gating`, `signal-pipeline`, `self-improvement`), and project phase docs (`strategy-testing`, `month-1-goal`), but **no executable code**. Agents cannot actually call Binance. This spec adds the missing connectivity layer plus deterministic strategy code so the existing testnet → live workflow can run end-to-end.

## 2. Goals

1. Agents can place, cancel, and reconcile Binance USDT-M futures orders on both **testnet** and **live**, switching modes via a single auditable file.
2. Strategy signal generation is deterministic Python (reproducible from the same klines); the Quant agent only does meta-judgement on top.
3. The testnet → live cutover is gated by hard preconditions in code, not just policy.
4. Every API call, signal, intent, order, and reconciliation diff is recorded on disk for audit.

## 3. Non-goals

- Multi-exchange support.
- Spot or options markets.
- Real-time WebSocket streams (REST polling only for month 1).
- A web UI or dashboard.
- Self-hosted databases (filesystem is the database for month 1).

## 4. Architecture

### 4.1 Repository layout

```
nyaon-trading-company/
├── bin/
│   └── nyaon                          # shebang: #!/usr/bin/env -S uv run python -m nyaon_trading.cli
├── pyproject.toml                     # PEP 621 metadata, uv-managed deps
├── uv.lock                            # committed, reproducible installs
├── .python-version                    # pinned (3.12)
├── nyaon_trading/
│   ├── __init__.py
│   ├── config.py                      # mode + secret resolution
│   ├── binance/
│   │   ├── client.py                  # signed HTTP, retry, time sync, rate limit
│   │   ├── market.py                  # exchangeInfo, klines, ticker
│   │   ├── account.py                 # account, positionRisk, openOrders, income
│   │   ├── orders.py                  # place/cancel/leverage, coid logic
│   │   └── errors.py                  # typed exceptions per Binance error codes
│   ├── strategy/
│   │   ├── trend.py                   # donchian + EMA filter
│   │   ├── mean_reversion.py          # bollinger + RSI
│   │   └── pipeline.py                # universe scan → signals JSON
│   ├── recon/
│   │   └── snapshot.py                # snapshot + diff classifier
│   └── cli/                           # argparse entry points (one per command)
│       ├── __init__.py                # dispatcher
│       ├── klines.py
│       ├── account.py
│       ├── signals.py
│       ├── place_order.py
│       ├── cancel.py
│       ├── snapshot.py
│       ├── mode.py
│       └── halt.py
├── state/                             # source of truth (gitignored except .schemas/)
│   ├── .schemas/                      # committed JSON schemas for all artifacts
│   ├── mode.json
│   ├── signals/<utc_iso>.json
│   ├── intents/<intent_id>.json
│   ├── orders/<coid>.json
│   ├── snapshots/<utc_iso>.json
│   ├── incidents/<utc_iso>.json
│   ├── audits/promotion-<date>.json
│   ├── cache/exchangeInfo.json
│   ├── logs/binance/<date>.jsonl
│   └── halt.flag                      # presence ⇒ global halt
├── tests/
│   ├── unit/
│   └── integration/                   # gated by RUN_TESTNET_TESTS=1
└── docs/superpowers/specs/...
```

### 4.2 Tooling: uv

- Setup: `uv sync`
- Run CLI: `uv run nyaon <cmd>` or `bin/nyaon <cmd>` (shebang already uses `uv run`).
- Tests: `uv run pytest`.
- Add dep: `uv add <pkg>`; upgrade: `uv lock --upgrade-package <pkg>`.
- CI: `uv sync --frozen` (uses `uv.lock` strictly).

### 4.3 Mode switching

`state/mode.json`:

```json
{
  "mode": "testnet",
  "set_by": "ceo",
  "set_at": "2026-05-19T17:00:00Z",
  "reason": "initial",
  "live_size_multiplier": 1.0
}
```

`nyaon_trading.config.load()` reads this on every CLI invocation and returns a `Mode` dataclass with `base_url`, `key_env`, `secret_env`. CLI processes are short-lived, so per-process caching is sufficient; no stale-state risk.

## 5. Components

### 5.1 `config`

- Loads `state/mode.json`.
- Resolves secret env vars (`BINANCE_TESTNET_API_KEY/SECRET` for testnet, `BINANCE_LIVE_*` for live).
- Returns `Mode(name, base_url, key, secret, live_size_multiplier)`.
- Fails with a clear exit-2 error if mode=live but live secrets missing.

### 5.2 `binance.client.BinanceClient`

- Single class wrapping `httpx`.
- Methods: `get_public`, `get_signed`, `post_signed`, `delete_signed`.
- HMAC-SHA256 signing on query string + body; `recvWindow=5000`.
- Time sync: caches `serverTime` offset for 30 minutes; refreshes on `-1021` and retries once.
- Retry: `tenacity`, exponential backoff, max 3 attempts, only on 5xx, timeouts, and `-1021`. 4xx other than `-1021` is terminal.
- Rate limit: in-process token bucket reading `X-MBX-USED-WEIGHT-1m` headers; throttles below 80% of cap.
- Logging: each request appended to `state/logs/binance/<date>.jsonl` (`{ts, method, path, status, weight, latency_ms, coid?}`). Secrets and full bodies redacted; only path + status + weight kept.

### 5.3 `binance.market`

- `exchange_info()` — cached on disk for 12 hours at `state/cache/exchangeInfo.json`.
- `klines(symbol, interval, limit)` — cached on disk: 14 minutes for 15m, 4 minutes for 5m.
- `ticker_price(symbol)`, `book_ticker(symbol)` — uncached.

### 5.4 `binance.account`

- `account_snapshot()` → equity, available, positions list.
- `position_risk()`, `open_orders(symbol=None)`, `income(since)`.

### 5.5 `binance.orders`

- `set_leverage(symbol, leverage)` — idempotent; consults cached current value before calling API.
- `place_order(intent: Intent)` → entry; `coid = f"{intent.id}-{attempt}"`.
- `place_stop(intent, fill_price)` → `STOP_MARKET` with `closePosition=true`, `coid + "-sl"`.
- `place_take_profit(intent, fill_price)` → `TAKE_PROFIT_MARKET` with `closePosition=true`, `coid + "-tp"`.
- `cancel_order(symbol, coid)`.
- Returns typed `OrderResult` dataclass; persists to `state/orders/<coid>.json` atomically.

### 5.6 `strategy.pipeline.run()`

1. Read `exchange_info` (cached).
2. Filter symbols: quote = USDT, status = TRADING, 24h quote volume ≥ $50M (threshold configurable in `state/mode.json` later).
3. For each symbol: fetch 15m klines (limit 200), compute `trend.score` and `mean_reversion.score`.
4. Combine into zero or more `Signal(symbol, side, strength, suggested_sl_bps, suggested_tp_bps, ttl)` records.
5. Write `state/signals/<utc_iso>.json` as one bundle.

### 5.7 `strategy.trend`

Donchian breakout (N=20) gated by EMA(50) > EMA(200) trend filter. Pure function of a klines DataFrame; same input always yields same score.

### 5.8 `strategy.mean_reversion`

Bollinger Bands (window=20, σ=2) re-entry filtered by RSI(14). No signal when the trend filter strongly opposes. Also pure.

### 5.9 `recon.snapshot`

- Pulls `account` + `positionRisk` + `openOrders` + `income(since=last_snapshot_ts)`.
- Builds a snapshot matching `exchange-ops` SKILL.md schema.
- Diffs against the previous snapshot in `state/snapshots/`.
- Classification: `clean` (no changes beyond known order events), `benign` (fees, funding, small unrealized drift), `critical` (position quantity mismatch, orphan reduce-only order, balance delta > 0.5% without matching trade).
- `critical` writes `state/incidents/<ts>.json` and touches `state/halt.flag`.

### 5.10 CLI surface

| Command | Module | Caller |
|---|---|---|
| `nyaon mode show` / `nyaon mode set testnet\|live` | `cli.mode` | CEO only |
| `nyaon signals` | `cli.signals` | `quant-tick` |
| `nyaon place-order --intent <path>` | `cli.place_order` | `trader-tick` |
| `nyaon cancel --symbol --coid` | `cli.cancel` | `trader-tick` |
| `nyaon snapshot` | `cli.snapshot` | `ops-reconcile` |
| `nyaon halt --reason '...'` / `nyaon resume` | `cli.halt` | CRO halt, CEO resume |
| `nyaon klines <sym> <interval> <limit>` | `cli.klines` | ad-hoc |
| `nyaon account` | `cli.account` | ad-hoc |

All CLIs print JSON to stdout, errors to stderr, exit non-zero on failure.

## 6. Data flow (one full cycle, testnet)

```
T+0:00  quant-tick fires
        └─> uv run nyaon signals
            ├─> state/mode.json → testnet base URL + testnet secrets
            ├─> exchange_info (cached) + klines for filtered universe
            ├─> compute trend + mean_reversion scores
            └─> state/signals/<ts>.json
        └─> Quant agent reads latest signals/<ts>.json
            └─> writes state/intents/<intent_id>.json with status=proposed

T+0:01  cro-tick fires
        └─> CRO agent scans intents with status=proposed
            └─> nine-gate risk-gating skill check
            └─> approved → status=approved + risk fields filled
            └─> rejected → status=rejected + reason

T+0:02  trader-tick fires
        └─> Trader scans intents with status=approved
            └─> uv run nyaon place-order --intent state/intents/<id>.json
            └─> intent.status → filled | failed

T+0:05  ops-reconcile fires
        └─> uv run nyaon snapshot
            ├─> account + positionRisk + openOrders + income(since=last)
            ├─> diff vs prior snapshot
            ├─> clean/benign → write state/snapshots/<ts>.json
            └─> critical → state/incidents/<ts>.json + touch state/halt.flag
```

### 6.1 Halt semantics

- `state/halt.flag` present ⇒ `nyaon place-order` refuses immediately (exit 2, stderr `HALTED`).
- CRO can halt directly via `nyaon halt --reason '...'`.
- Only CEO can clear (`nyaon resume`).
- Ops critical mismatch always halts.

### 6.2 Idempotency

- Trader retries reuse the same `coid`. Binance rejects duplicate `coid` within 24 hours ⇒ safe.
- `attempt` counter increments only when Binance returns a terminal error for the prior attempt (e.g. `INVALID_QUANTITY`); never on network errors or 5xx.

### 6.3 State directory contract

- All JSON files written atomically (`*.tmp` then `rename`).
- Filenames sort lexically by UTC ISO timestamp; readers take newest via `sorted()[-1]`.
- `state/` is gitignored except `state/.schemas/` which is committed and used by tests + jsonschema validators inside the CLIs.

## 7. Testing

### 7.1 Unit (`tests/unit/`, no network)

- Signing: known key/payload yields the expected HMAC.
- `coid` generator: deterministic and stable.
- `trend.score`, `mean_reversion.score`: fixed klines fixtures → fixed outputs.
- Snapshot diff classifier: synthetic before/after pairs → expected classification.
- Mode switch: mocked `mode.json` produces correct base URL and secret env names.
- Halt flag: `place-order` refuses when flag is present.

### 7.2 Integration (`tests/integration/`, gated by `RUN_TESTNET_TESTS=1`)

- `test_account.py` — testnet `account` returns valid schema.
- `test_klines.py` — BTCUSDT 15m klines schema valid, time monotonic.
- `test_round_trip.py` — places a tiny BTCUSDT market order (qty 0.001), polls fill, cancels paired SL/TP, asserts `coid` recorded and reconcile diff is benign.
- `test_idempotency.py` — re-submits the same `coid` twice; asserts exactly one position opened.
- `test_rate_limit.py` — bursts 50 calls; asserts throttle engages and no `-1003` ban.

### 7.3 CI

- Lint (`ruff check`), format (`ruff format --check`), types (`pyright`), unit tests on every push.
- Integration tests run nightly or on-demand with secret env vars; never on PRs from forks.

### 7.4 Pre-promotion gate

The `promotion-audit` task at end of week 2 runs:

1. Full integration suite against testnet.
2. Full unit suite.
3. Last 5 trading days of `state/orders/` + `state/snapshots/` → computes hit rate, profit factor, max drawdown, slippage, Ops critical count.
4. Writes `state/audits/promotion-<date>.json` with pass/fail per criterion and a single overall `pass=true|false`.

`RISK_POLICY.md` §6 criteria must all pass for the audit to clear.

## 8. Go-live gating

`nyaon mode set live` enforces these hard preconditions atomically; all must hold:

1. `state/mode.json` exists, current mode = `testnet`.
2. `BINANCE_LIVE_API_KEY` and `BINANCE_LIVE_API_SECRET` are present in env.
3. Latest `state/audits/promotion-<date>.json` has `pass=true` and is ≤ 24h old.
4. No `state/halt.flag` is present.
5. No unresolved `state/incidents/*.json` newer than the most recent clean snapshot.

Only the CEO agent role may invoke `nyaon mode set live`; paperclip task config and the CLI both enforce this (env var `NYAON_AGENT_ROLE=ceo` checked).

### 8.1 Ramp safety after switch

- First 48 hours live: `state/mode.json.live_size_multiplier = 0.5`. Trader reads multiplier each tick and scales position size.
- After 48 hours with zero critical incidents and zero halts, CEO retro may set multiplier to 1.0.

### 8.2 Rollback

- Any critical incident in live → `state/halt.flag` + `state/incidents/<ts>.json`.
- CEO may run `nyaon mode set testnet` at any time; the safe direction requires no audit.

## 9. Dependencies

Pinned via `uv` in `pyproject.toml`:

- `httpx` — HTTP client.
- `tenacity` — retry policy.
- `pydantic` — typed config + intent/signal/order dataclasses with validation.
- `pandas`, `numpy` — klines DataFrame + indicators.
- `jsonschema` — validate state artifacts against `state/.schemas/`.
- Dev: `pytest`, `ruff`, `pyright`.

## 10. Open questions

None blocking implementation. Future considerations (not in scope for month 1):

- Switch klines to WebSocket streaming for lower latency.
- Move state to SQLite for richer queries.
- Per-strategy capital allocation (current pipeline uses single risk budget).
