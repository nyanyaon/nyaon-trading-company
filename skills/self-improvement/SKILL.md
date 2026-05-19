---
name: self-improvement
description: Weekly retro process for the CEO. Reads performance journals, proposes diffs to strategies, risk knobs, and agent prompts, decides testnet-to-live promotion.
---

# self-improvement

CEO weekly retro. Runs every Sunday 23:00 UTC. Drives the company's improvement loop.

## Inputs

- `state/snapshots/` (Ops snapshots over the week)
- `state/signals/` (all signals raised by Quant)
- `state/intents/` (proposed/approved/rejected/filled intents)
- `state/orders/` and `state/strategy_stats/` (placed orders and closed-trade outcomes)
- `state/incidents/` (Ops critical mismatches)
- `state/audits/` (prior promotion-audit results)
- `journal/cro/`, `journal/trader/`, `journal/ops/`, `journal/quant/`

## CLI (read-only checks during the retro)

| Action | Command |
|---|---|
| Confirm current mode | `uv run nyaon mode show` |
| Probe testnet account | `uv run nyaon account` |
| Force a fresh snapshot | `uv run nyaon snapshot` (exit 0 = clean) |

For mode transitions during the retro (week 2 promotion or rollback):

| Action | Command |
|---|---|
| Promote testnet → live | `uv run nyaon mode set live --reason 'week-2 audit pass'` (enforces 5 preconditions) |
| Rollback live → testnet | `uv run nyaon mode set testnet --reason '<event>'` (always allowed) |
| Clear halt after root-cause review | `uv run nyaon resume` |

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

If pass: run `uv run nyaon mode set live --reason 'week-2 audit pass'`. The CLI enforces all 5 preconditions (audit fresh, audit pass, live secrets present, no halt flag, no unresolved incidents) and atomically rewrites `state/mode.json`. Then notify user to rotate API keys and notify Trader/Ops.

If fail: log the failed criteria, extend testnet by one week, propose targeted diffs. Do NOT attempt `nyaon mode set live` — the CLI will refuse and that's the intended safety.

## Agent self-improvement

Each agent's prompt is reviewable. CEO may diff any `agents/*/AGENTS.md` body. Common changes:

- Tighten or loosen execution contract
- Add new boundary
- Update workflow steps to match a process change

Agent prompt diffs follow the same approval flow as risk knobs.
