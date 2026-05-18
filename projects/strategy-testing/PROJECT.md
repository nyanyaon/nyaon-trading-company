---
name: Strategy Testing
description: Two-week testnet validation harness. Wire pipeline, baseline metrics, prove the system before any live capital touches the exchange.
slug: strategy-testing
owner: ceo
---

# Strategy Testing

Validation phase. Binance USDT-M **testnet** only. No live capital. Outputs are baseline metrics + a pass/fail audit against `RISK_POLICY.md` §6 promotion criteria.

## Scope

| Week | Focus                                                                                              |
| ---- | -------------------------------------------------------------------------------------------------- |
| 1    | Wire the Quant → CRO → Trader → Ops pipeline. Confirm halt flag works. Capture baseline metrics. |
| 2    | Tune strategy params + risk knobs via weekly retro. Run promotion-criteria audit at end of week.  |

## Tasks under this project

- `quant-tick` (15m)
- `cro-tick` (1m)
- `trader-tick` (1m)
- `ops-reconcile` (5m)
- `promotion-audit` (one-shot, end of week 2)

## Success metrics (audit at end of week 2)

All five must hold across the last 5 trading days, per `RISK_POLICY.md` §6:

- Hit rate ≥ 40%
- Profit factor ≥ 1.3
- Max drawdown ≤ 8%
- Zero unresolved Ops critical mismatches
- Avg slippage ≤ 5 bps

## Exit conditions

- **Pass** → CEO writes `state/mode.json` promotion entry. Hands off to `month-1-goal` for the live ramp.
- **Fail** → CEO extends testnet by one week. `month-1-goal` ramp slides one week.

## Out of scope

- Any live trading
- New strategy *code* without user confirmation (knob tuning is fine)
- Multi-exchange
- Spot or options
