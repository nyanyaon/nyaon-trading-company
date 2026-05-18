---
name: Nyaon Trading Company
description: Autonomous AI crypto futures trading firm targeting $1000 PnL/month on Binance USDT-M via filtered multi-symbol scanning, self-improving strategies, and testnet-to-live promotion gate
slug: nyaon-trading-company
schema: agentcompanies/v1
version: 0.1.0
license: MIT
authors:
  - name: Nyaon
goals:
  - Hit $1000 cumulative PnL within month 1
  - Trade all eligible symbols, filtered by liquidity, spread, volatility, funding
  - Improve weekly: CEO retro updates strategies, risk knobs, agent prompts
  - Run testnet weeks 1-2, promote to live weeks 3-4 only if RISK_POLICY criteria pass
  - Minimize cost: Haiku 4.5 on high-frequency loops, Sonnet 4.6 on thinking roles
requirements:
  secrets:
    - BINANCE_TESTNET_API_KEY
    - BINANCE_TESTNET_API_SECRET
    - BINANCE_LIVE_API_KEY
    - BINANCE_LIVE_API_SECRET
---

# Nyaon Trading Company

Autonomous 5-agent AI trading firm. Binance USDT-M futures.

## Workflow (pipeline)

```
Quant (15m) → CRO (1m) → Trader (1m) → Ops (5m)
                                       └── weekly CEO retro
```

- **Quant** scans the filtered symbol universe every 15 minutes, runs the two seeded strategies, ranks top-3 candidates, publishes signals.
- **CRO** evaluates each candidate against the 9-gate risk checklist in `RISK_POLICY.md`. Approves, rejects, or sizes down. May raise halt flag.
- **Trader** executes approved orders idempotently (client order IDs). Reads halt flag every tick. Never sizes itself.
- **Ops** reconciles internal state vs exchange every 5 minutes. Critical mismatch → halt.
- **CEO** runs a weekly retro: hit rate, slippage, halt incidents, PnL attribution. Proposes diffs to strategies, risk knobs, or agent prompts. Decides testnet → live promotion. Code changes that require human review escalate to the user.

## Governance

- `RISK_POLICY.md` is the single source of truth. CRO is the sole risk gate.
- CRO or Ops may unilaterally raise the halt flag. Only CEO clears it after a written retro entry.
- Promotion testnet → live requires: ≥40% hit rate, profit factor ≥1.3, max drawdown ≤8%, zero unresolved Ops critical mismatches across 5 trading days.

## Cost discipline

| Role   | Cadence | Model         | Why                                  |
| ------ | ------- | ------------- | ------------------------------------ |
| CEO    | Weekly  | Sonnet 4.6    | Heavy reasoning, infrequent          |
| CRO    | 1m      | Sonnet 4.6    | Risk reasoning, deterministic gates  |
| Quant  | 15m     | Sonnet 4.6    | Strategy thinking, infrequent        |
| Trader | 1m      | Haiku 4.5     | Mechanical execution, high frequency |
| Ops    | 5m      | Haiku 4.5     | Reconciliation diff, high frequency  |

Generated with the [Agent Companies spec](https://agentcompanies.io/specification) for [Paperclip](https://github.com/paperclipai/paperclip).
