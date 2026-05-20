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
- `state/proposals/*.json` with `status=proposed` (Quant R&D proposals awaiting CEO review)
- `journal/cro/`, `journal/trader/`, `journal/ops/`, `journal/quant/` (including `journal/quant/rnd-YYYY-WW.md`)

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

Two streams of proposed diffs converge during the Sunday retro:

1. **CEO-authored diffs** (own analysis): edit files directly.
2. **Quant R&D proposals** (`state/proposals/*.json` with `status=proposed`): read each one in turn.

For each Quant proposal:

- Read `state/proposals/<id>.json` and follow `rationale` to the linked `journal/quant/rnd-YYYY-WW.md` section. Inspect the backtest table and equity curve.
- Sanity-check the anti-overfitting story: train/test split honored? multi-symbol verified? sample-size floor met? drawdown floor met?
- Decision:
  - **Approve** (`kind=parameter`): update `status="approved"`, fill `reviewed_by="ceo"`, `reviewed_at`, `review_notes`. Quant applies the diff during the next Friday R&D tick.
  - **Approve** (`kind=code` / new strategy file): also escalate to the user per `agents/ceo/AGENTS.md` boundaries. Diff does not apply until user confirms.
  - **Reject**: `status="rejected"` + `review_notes`. Quant logs in next R&D cycle as learning material.
  - **Needs revision**: `status="needs_revision"` + `review_notes` with the specific gap. Quant rewrites the proposal next Friday.

For CEO-authored diffs:

- Parameter change (numeric thresholds, weights) → CEO edits directly during the retro.
- Logic change (new strategy code, new gate) → CEO writes an escalation message to the user with the diff and the reason. Wait for human confirmation before applying.

All approved diffs land before the next Monday 00:00 UTC. Diffs that miss the window roll to the following week.

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
