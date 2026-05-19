---
name: Promotion Audit
slug: promotion-audit
assignee: ceo
project: strategy-testing
recurring: true
---

One-shot intent: audit testnet performance against `RISK_POLICY.md` §6 promotion criteria. Runs weekly as a safety net so missed weeks still get audited.

Read the last 5 trading days from `state/snapshots/`, `state/orders/`, `state/strategy_stats/`, `state/incidents/`, and `journal/`. Compute:

- Hit rate (overall, per strategy)
- Profit factor
- Max drawdown
- Open Ops critical mismatches
- Avg slippage bps

Pass = all five criteria hold. Fail = any one fails.

Done when:
- `journal/audits/YYYY-WW-promotion.md` written with per-criterion pass/fail and the underlying numbers
- On pass: write `state/audits/promotion-<YYYY-MM-DD>.json` with `pass=true`; CEO runs `uv run nyaon mode set live --reason '...'` (which enforces all 5 preconditions before writing `state/mode.json`); user notified to provision live API keys
- On fail: `journal/audits/` notes the failed criteria and the proposed remediation; live ramp slides one week
- Hand-off recorded — pass hands `month-1-goal` the green light; fail keeps `strategy-testing` open

This task auto-completes itself after writing `state/mode.json = live` (no re-audit needed once promoted).

## Procedure (executed by promotion-audit task)

1. `uv sync --frozen`
2. `uv run pytest tests/unit -q` — must pass.
3. `RUN_TESTNET_TESTS=1 uv run pytest tests/integration -q` — must pass.
4. Compute metrics from `state/orders/*.json` and `state/snapshots/*.json` for the last 5 trading days.
5. Write `state/audits/promotion-<YYYY-MM-DD>.json` per `state/.schemas/promotion-audit.json`.
6. CEO reads the audit on Sunday retro. If `pass=true` and ≤24h old, CEO may run `uv run nyaon mode set live --reason 'week-2 audit pass'`.
