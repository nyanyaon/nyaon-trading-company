---
name: CRO Tick
slug: cro-tick
assignee: cro
project: strategy-testing
recurring: true
---

Run the risk-gating skill. Read proposed intents in `state/intents/`, run the 9 gates in order, size and approve passing ones (update `status` to `approved`), reject failures with `rejection_reason`. Halt via `uv run nyaon halt --reason '...'` (touches `state/halt.flag`).

Done when:
- Every proposed intent in `state/intents/` has `status` flipped to `approved` or `rejected` with deciding gate / reason
- Approved intents have `qty_quote`, `leverage`, `sl_bps`, `tp_bps` filled per `RISK_POLICY.md` §4
- `journal/cro/YYYY-MM-DD.log` has a tick entry
- Halt-flag transitions: presence of `state/halt.flag` and its content (timestamp + reason) recorded in journal
