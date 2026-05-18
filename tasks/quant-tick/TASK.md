---
name: Quant Tick
slug: quant-tick
assignee: quant
project: strategy-testing
recurring: true
---

Run the signal-pipeline skill. Pull universe, apply filters, run trend-pullback-v1 and mean-revert-v1, rank top-3 per strategy, cluster-cap, write signals to `state/signals/<ts>.jsonl`.

Done when:
- `state/signals/<ts>.jsonl` exists with at most 6 signals (3 per strategy, cluster-capped)
- `journal/quant/YYYY-MM-DD.log` has a tick entry
- No exception left unlogged
