---
name: Promotion Audit
slug: promotion-audit
assignee: ceo
project: strategy-testing
recurring: true
---

One-shot intent: audit testnet performance against `RISK_POLICY.md` §6 promotion criteria. Runs weekly as a safety net so missed weeks still get audited.

Read the last 5 trading days from `state/account.json` history, `state/strategy_stats/`, `state/incidents/`, and `journal/`. Compute:

- Hit rate (overall, per strategy)
- Profit factor
- Max drawdown
- Open Ops critical mismatches
- Avg slippage bps

Pass = all five criteria hold. Fail = any one fails.

Done when:
- `journal/audits/YYYY-WW-promotion.md` written with per-criterion pass/fail and the underlying numbers
- On pass: `state/mode.json` set to `{"mode": "live", "promoted_at": "<iso>"}` and user notified to provision live API keys
- On fail: `journal/audits/` notes the failed criteria and the proposed remediation; live ramp slides one week
- Hand-off recorded — pass hands `month-1-goal` the green light; fail keeps `strategy-testing` open

This task auto-completes itself after writing `state/mode.json = live` (no re-audit needed once promoted).
