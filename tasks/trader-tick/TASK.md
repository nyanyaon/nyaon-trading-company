---
name: Trader Tick
slug: trader-tick
assignee: trader
project: strategy-testing
recurring: true
---

Run the exchange-ops skill (execution side). Read `state/halt.json`. For each `state/orders/pending/<id>.json`, place the entry order with deterministic clientOrderId. On fill, place paired stop-loss and take-profit reduce-only orders. Update `state/positions/` and `state/orders/filled/`.

Done when:
- Every pending intent has either a placed order ack or a logged failure with reason
- Every filled entry has its paired stop and take-profit registered
- `journal/trader/YYYY-MM-DD.log` has a tick entry with per-order slippage in bps
- If halt is on, no new entries are placed (exits still managed)
