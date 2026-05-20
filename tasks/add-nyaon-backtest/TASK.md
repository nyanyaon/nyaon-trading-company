---
name: Add nyaon backtest subcommand
slug: add-nyaon-backtest
assignee: ceo
project: nyaon-cli
recurring: false
---

Add a deterministic `nyaon backtest` subcommand to the CLI. Quant's `strategy-rnd` skill depends on it for reproducible backtests. Until this lands, Quant uses one-off Python scripts under `journal/quant/rnd-scripts/`.

## Precondition

`create-nyaon-cli` is done — the base package + tests are in the workspace.

## Specification

```
uv run nyaon backtest <strategy> --symbol <SYM> --interval <I> --from <ISO_DATE> --to <ISO_DATE> [--params '{json}'] [--initial-capital <N>]
```

| Arg | Required | Example |
| --- | --- | --- |
| `<strategy>` | yes | `trend` or `mean_reversion` or `trend_v2` |
| `--symbol` | yes | `BTCUSDT` |
| `--interval` | yes | `15m` |
| `--from` | yes | `2026-01-01T00:00:00Z` |
| `--to` | yes | `2026-04-30T00:00:00Z` |
| `--params` | no | `'{"donchian": 25, "ema_fast": 12}'` — JSON overrides for strategy kwargs |
| `--initial-capital` | no | `10000` (default) |

Output to stdout (JSON):

```json
{
  "strategy": "trend",
  "symbol": "BTCUSDT",
  "interval": "15m",
  "from": "2026-01-01T00:00:00Z",
  "to": "2026-04-30T00:00:00Z",
  "params": {"donchian": 20, "ema_fast": 50, "ema_slow": 200},
  "bars": 11520,
  "trades": 47,
  "hit_rate": 0.426,
  "profit_factor": 1.38,
  "max_drawdown": 0.062,
  "sharpe": 1.12,
  "total_return_pct": 8.4,
  "avg_slippage_bps": 3.0,
  "equity_curve_path": "state/rnd_cache/equity_<hash>.csv"
}
```

Exit codes: 0 = success, 2 = bad args, 3 = data pull failed, 4 = insufficient data (< 50 bars).

## Implementation phases

### Phase 1 — New module `nyaon_trading/backtest/engine.py`

Pure walk-forward simulator:

```python
def run(
    strategy_fn: Callable[[pd.DataFrame], BaseSignal | None],
    df: pd.DataFrame,
    initial_capital: float = 10_000.0,
    risk_per_trade: float = 0.01,
    slippage_bps: float = 3.0,
) -> BacktestResult:
    ...
```

`BacktestResult` is a dataclass with the JSON fields above plus an `equity_curve: list[tuple[ts, equity]]`.

Walk-forward semantics:
- For bar `i` from `max(strategy_lookback)` to `len(df) - 1`:
  - Call `strategy_fn(df.iloc[:i+1])` (signal can only see up to current bar's close)
  - If signal fires, simulate market entry at next bar's `open` (no look-ahead)
  - Place virtual SL/TP using `suggested_sl_bps` / `suggested_tp_bps`
  - Walk forward bar-by-bar checking SL/TP/TTL hits
  - Realize PnL when stop or take-profit hits
- Track equity, drawdown, trades

NO real Binance calls in the engine. Pure pandas math.

### Phase 2 — Klines history loader `nyaon_trading/backtest/loader.py`

`def load_klines_range(client, symbol, interval, start_ms, end_ms) -> pd.DataFrame`

Loops `/fapi/v1/klines` with the `startTime` + `endTime` + `limit=1500` pagination. Caches each chunk to `state/rnd_cache/<symbol>_<interval>_<startMs>_<endMs>.json`. Returns a single concatenated DataFrame.

### Phase 3 — CLI wrapper `nyaon_trading/cli/backtest.py`

Argparse, instantiates client, calls `loader.load_klines_range`, resolves the strategy module by name, invokes `engine.run`, prints JSON.

Strategy resolver:

```python
_STRATEGIES = {
    "trend": ("nyaon_trading.strategy.trend", "score"),
    "mean_reversion": ("nyaon_trading.strategy.mean_reversion", "score"),
}
# When new variants land, add to this map (or auto-discover by glob).
```

Apply `--params` JSON via `functools.partial(score, **params)`.

### Phase 4 — Dispatcher entry

Edit `nyaon_trading/cli/__init__.py` to route `backtest` to `cli.backtest.run`.

### Phase 5 — Unit tests `tests/unit/test_backtest_engine.py`

- Test on the existing `tests/unit/fixtures/klines_btc_15m.json` fixture (50 bars, uptrend → mean reversion → uptrend)
- Force the strategy to fire once at a known bar; assert PnL math, equity_curve length, trade count
- Edge case: zero trades → result with trades=0, all metrics zero or NaN, no crash
- Edge case: SL hit before TP, TP hit before SL, neither hit (TTL expires)

### Phase 6 — Cross-link

Update `skills/strategy-rnd/SKILL.md` step 4 to use the new CLI as the default backtest path (already cited as future tool).

Update `agents/quant/AGENTS.md` Tooling: add `uv run nyaon backtest ...` to Quant's allowed commands.

## Verification

```bash
uv run pytest tests/unit -q                  # 22 + new backtest tests pass
uv run nyaon backtest trend --symbol BTCUSDT --interval 15m \
    --from 2026-04-01T00:00:00Z --to 2026-04-30T00:00:00Z
# Expected: JSON to stdout, exit 0
```

## Done when

- New files: `nyaon_trading/backtest/{engine.py,loader.py,__init__.py}`, `nyaon_trading/cli/backtest.py`, `tests/unit/test_backtest_engine.py`
- Dispatcher routes `backtest`
- All unit tests still green
- One real backtest call against testnet data succeeds
- `journal/audits/add-nyaon-backtest-<YYYY-MM-DD>.md` records the verification output

## Boundaries

- Engine must be deterministic: same df + same params → identical result. No random sampling, no Monte Carlo.
- No look-ahead: signal at bar `i` may only use `df.iloc[:i+1]`. Entry fills at `i+1` open.
- No live trading from this task — backtest only.
- Do NOT touch the live strategy code (`trend.py`, `mean_reversion.py`) — read-only here.
