---
name: signal-pipeline
description: Binance USDT-M futures universe scan, symbol filter enforcement, strategy interface, top-3 ranking. Used by Quant every 15 minutes.
---

# signal-pipeline

Deterministic signal generation for Nyaon Trading Company. Used by Quant.

## Inputs

- Binance testnet (or live) REST: `GET /fapi/v1/exchangeInfo`, `GET /fapi/v1/klines`, `GET /fapi/v1/ticker/24hr`, `GET /fapi/v1/premiumIndex`
- `RISK_POLICY.md` (filter thresholds, cluster definitions)
- Strategy modules in `strategies/`

## Pipeline steps

1. **Pull universe** — all `TRADING` USDT-M perpetuals from `exchangeInfo`.
2. **Apply filters** (`RISK_POLICY.md` §2):
   - 24h quote volume ≥ $50M
   - Spread ≤ 5 bps (top of book; sampled twice within tick)
   - 0.15% ≤ ATR(14, 15m) / price ≤ 4%
   - |funding| ≤ 0.10% / 8h
   - Listed ≥ 30 days
   - Price ≥ $0.01
3. **Pull OHLCV** for surviving symbols. Cache per tick.
4. **Run strategies**:
   - `trend-pullback-v1` on 15m
   - `mean-revert-v1` on 5m
5. **Rank top-3 per strategy** by `expected_edge_bps × confidence`.
6. **Apply cluster cap** — at most 2 candidates per correlation cluster (`RISK_POLICY.md` §8).
7. **Write signals** to `state/signals/<ts>.jsonl`.

## Signal record

```json
{
  "id": "sig_<ts>_<symbol>_<strategy>",
  "ts": "2026-05-18T12:00:00Z",
  "symbol": "BTCUSDT",
  "strategy": "trend-pullback-v1",
  "side": "long",
  "entry": 68312.5,
  "stop": 67890.0,
  "take_profit": 69157.0,
  "expected_edge_bps": 38,
  "confidence": 0.62,
  "regime_tag": "trend_up",
  "features": { "ema50_slope": 0.0021, "atr_pct": 0.012 }
}
```

## Strategy interface

```python
def generate(symbol: str, ohlcv: pd.DataFrame, params: dict) -> list[Signal]:
    """Return zero or more Signal objects for this symbol."""
```

Each strategy is one file in `strategies/<name>.py` with a `generate` function and a `params` dict. CEO approves all diffs.

## Hit-rate tracking

After every closed position, append outcome to `state/strategy_stats/<strategy>.jsonl`:

```json
{ "id": "sig_...", "outcome": "win|loss|breakeven", "r_multiple": 1.2, "duration_min": 47 }
```

CRO reads rolling 50-signal hit rate (gate 7).

## Cold-start

If fewer than 20 closed signals exist for a strategy, gate 7 is bypassed (grace window).

## Self-improvement hooks

Weekly retro reads:
- Hit rate by strategy, by regime, by cluster
- Edge prediction calibration (predicted vs realized bps)
- Top winning and losing setups

CEO proposes diffs; Quant integrates them in next week's params.

## Implementation

Signal computation is deterministic Python in `nyaon_trading.strategy.pipeline`. Quant agent runs:

```
uv run nyaon signals
```

This writes `state/signals/<utc_iso>.json`. Quant reads the newest file, applies meta-judgement (skip stale, gate by RISK_POLICY caps, dedupe vs open intents), and writes one or more intents to `state/intents/<intent_id>.json` with `status="proposed"`.
