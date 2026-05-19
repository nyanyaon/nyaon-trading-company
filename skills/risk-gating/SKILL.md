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

Each rejection writes the failing gate number to the approval record.

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

## Order intent record

```json
{
  "id": "ord_<signal-id>",
  "signal_id": "sig_...",
  "symbol": "BTCUSDT",
  "side": "buy",
  "qty": 0.012,
  "entry": 68312.5,
  "stop": 67890.0,
  "take_profit": 69157.0,
  "leverage": 3,
  "client_order_id_prefix": "ord_<signal-id>"
}
```

## Halt logic

Raise `halt_flag = true` on any of:

- Hard limit breach (`RISK_POLICY.md` §1)
- Daily or weekly circuit breaker hit
- 3 API auth failures in 5 minutes
- Latency > 2s on order placement for 3 consecutive Trader ticks (Ops reports this)
- Ops critical mismatch event

Halt-flag transitions:

```json
{
  "halt_flag": true,
  "raised_at": "2026-05-18T14:23:10Z",
  "raised_by": "cro",
  "reason": "daily_loss_breach",
  "cleared_at": null,
  "cleared_by": null
}
```

## Self-improvement hooks

Weekly retro reads:
- Distribution of which gate fired the most
- False rejects (signals that would have won)
- True saves (signals that would have lost)

CEO tunes thresholds in `RISK_POLICY.md`. Never tune mid-week.
