---
name: CRO Tick
slug: cro-tick
assignee: cro
project: strategy-testing
recurring: true
---

Run the risk-gating skill. Read pending signals, run the 9 gates in order, size approved signals, write order intents to `state/orders/pending/`. Maintain `state/halt.json`.

Done when:
- Every pending signal has an approval record (`accepted | rejected | resized`) with the deciding gate
- Approved intents written to `state/orders/pending/<id>.json`
- `journal/cro/YYYY-MM-DD.log` has a tick entry
- Halt-flag transitions logged with reason and raiser
