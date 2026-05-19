---
name: risk-gating
description: Nine-gate deterministic risk acceptance, sizing math, and halt logic for the CRO. Reads RISK_POLICY.md as source of truth.
---

# risk-gating

CRO's deterministic decision skill. Inputs are proposed intents in `state/intents/` (status=`proposed`) and the newest snapshot in `state/snapshots/<ts>.json`. Output is approved sized intents (status flipped to `approved`) and halt-flag transitions via `uv run nyaon halt`.

## Nine gates (evaluated in order; reject on first failure)

1. **Halt clear** — `state/halt.flag` does not exist.
2. **Symbol passes filters** — `RISK_POLICY.md` §2.
3. **Loss budgets** — daily PnL > -3% equity AND weekly PnL > -7% equity.
4. **Concurrent-position cap** — open positions < 5.
5. **Correlation cluster cap** — adding this symbol keeps cluster ≤ 40% of risk budget.
6. **Signal age** — `now - signal.ts < 90s`.
7. **Strategy hit rate** — rolling 50-signal hit rate ≥ 35% (bypass if < 20 closed signals).
8. **Sizing fit** — computed qty ≤ 1.0% equity risk and ≤ 5x leverage.
9. **Edge vs cost** — `expected_edge_bps > 4 × (spread_bps + expected_slippage_bps)`.

Each rejection writes the failing gate number to the intent's `rejection_reason`.

## Implementation (CLI)

CRO reads + writes intents directly to `state/intents/*.json` (no Binance call needed for gating). For state reads and halt transitions:

| Action | Command |
|---|---|
| Read newest snapshot | `ls -t state/snapshots/*.json \| head -1` then read it |
| Read newest incident | `ls -t state/incidents/*.json \| head -1` then read it |
| Raise halt | `uv run nyaon halt --reason '<gate-or-event>'` |
| Sanity-check exchange | `uv run nyaon account` (read-only) |
| Sanity-check reconciliation | `uv run nyaon snapshot` (read-only sanity; does not replace Ops cadence) |

CRO must not run `uv run nyaon place-order`, `nyaon resume`, or `nyaon mode set ...`.

## Sizing math

```
risk_budget    = equity * 0.01
stop_distance  = |entry - stop|
qty_raw        = risk_budget / stop_distance
notional       = qty_raw * entry
leverage_used  = notional / equity
```

If `leverage_used > 5`: `qty = qty_raw * (5 / leverage_used)`.
If cluster cap would be exceeded: `qty = qty_to_fit_cap`.
Round qty to symbol's step size from `exchangeInfo`.

## Order intent record (matches `state/.schemas/intent.json`)

CRO mutates the same `state/intents/<intent_id>.json` file Quant created — flips `status` from `proposed` to `approved` and fills the sized fields:

```json
{
  "id": "sig_BTCUSDT_long_<hash>",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "qty_quote": 50.0,
  "sl_bps": 80,
  "tp_bps": 160,
  "leverage": 3,
  "ttl": "2026-05-19T17:45:00Z",
  "source_signal": "sig_BTCUSDT_long_<hash>",
  "status": "approved",
  "approved_at": "2026-05-19T17:31:08Z"
}
```

On rejection, set `status: "rejected"` and `rejection_reason: "<gate-N>: <detail>"`. Trader's `uv run nyaon place-order --intent <path>` consumes only `status=approved` intents.

## Halt logic

Raise halt by running `uv run nyaon halt --reason '<event>'`. The CLI writes `state/halt.flag` with a UTC timestamp + reason on the first line. Triggers:

- Hard limit breach (`RISK_POLICY.md` §1)
- Daily or weekly circuit breaker hit
- 3 API auth failures in 5 minutes
- Latency > 2s on order placement for 3 consecutive Trader ticks (Ops reports this)
- Ops critical mismatch event (Ops also halts via `uv run nyaon halt`)

`state/halt.flag` content example:

```
2026-05-18T14:23:10Z daily_loss_breach
```

Only the CEO clears the flag (`uv run nyaon resume`).

## Self-improvement hooks

Weekly retro reads:
- Distribution of which gate fired the most
- False rejects (signals that would have won)
- True saves (signals that would have lost)

CEO tunes thresholds in `RISK_POLICY.md`. Never tune mid-week.
