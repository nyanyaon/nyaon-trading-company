---
name: Ops Reconcile
slug: ops-reconcile
assignee: ops
project: strategy-testing
recurring: true
---

Run the exchange-ops skill (reconciliation side). Pull account + open orders + position risk. Build canonical `state/account.json`. Diff against prior snapshot and against Trader's internal `state/positions/` and `state/orders/`.

Done when:
- `state/account.json` updated atomically
- Diff classified as `clean | benign | critical`
- Critical mismatch → `state/incidents/<ts>.json` written + `halt_flag = true`
- `journal/ops/YYYY-MM-DD.log` has a tick entry
