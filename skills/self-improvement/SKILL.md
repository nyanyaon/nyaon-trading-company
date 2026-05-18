---
name: self-improvement
description: Weekly retro process for the CEO. Reads performance journals, proposes diffs to strategies, risk knobs, and agent prompts, decides testnet-to-live promotion.
---

# self-improvement

CEO weekly retro. Runs every Sunday 23:00 UTC. Drives the company's improvement loop.

## Inputs

- `state/account.json` history (Ops snapshots over the week)
- `state/signals/` (all signals raised by Quant)
- `state/orders/filled/` and `state/strategy_stats/` (closed trades and outcomes)
- `state/incidents/` (Ops critical mismatches)
- `journal/cro/`, `journal/trader/`, `journal/ops/`, `journal/quant/`

## Retro outline

Write `journal/retros/YYYY-WW.md`:

1. **Headline metrics**
   - Cumulative PnL vs $1000 month-1 goal
   - Hit rate (overall, per strategy, per regime, per cluster)
   - Profit factor, max drawdown, Sharpe (informational)
   - Avg slippage bps
2. **Halt incidents** — every halt with root cause + clear time
3. **Gate-firing histogram** — which CRO gates rejected most signals
4. **Top winners / losers** — by absolute PnL and by R multiple
5. **Edge calibration** — predicted vs realized bps per strategy
6. **Proposed diffs**
   - Strategy params (`strategies/*.py`)
   - Risk knobs (`RISK_POLICY.md`)
   - Agent prompts (`agents/*/AGENTS.md`)
   - New correlation clusters (`RISK_POLICY.md` §8)
7. **Promotion decision** (end of week 2 only) — pass/fail each criterion in `RISK_POLICY.md` §6

## Diff approval

For each proposed diff:

- If it's a parameter change (numeric thresholds, weights) → CEO applies directly.
- If it's a logic change (new strategy code, new gate) → CEO writes an escalation message to the user with the diff and the reason. Wait for human confirmation before applying.
- All diffs land before the next Monday 00:00 UTC.

## Promotion decision

End of week 2: audit `RISK_POLICY.md` §6. Required, all five must pass over the prior 5 trading days:

- Hit rate ≥ 40%
- Profit factor ≥ 1.3
- Max drawdown ≤ 8%
- Zero unresolved Ops critical mismatches
- Avg slippage ≤ 5 bps

If pass: write a promotion entry in `state/mode.json` (`{"mode": "live", "promoted_at": "..."}`), notify user to rotate API keys, then notify Trader/Ops.

If fail: log the failed criteria, extend testnet by one week, propose targeted diffs.

## Agent self-improvement

Each agent's prompt is reviewable. CEO may diff any `agents/*/AGENTS.md` body. Common changes:

- Tighten or loosen execution contract
- Add new boundary
- Update workflow steps to match a process change

Agent prompt diffs follow the same approval flow as risk knobs.
