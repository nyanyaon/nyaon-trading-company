---
name: Quant Tick
slug: quant-tick
assignee: quant
project: strategy-testing
recurring: true
---

## Precondition

Before any work, check `state/connection_ok.json` exists and contains `{"pass": true, ...}`. If missing or `pass != true`, **skip the tick** with a single line in `journal/quant/YYYY-MM-DD.log`:

```
<ts> skip: connection-check not passed (state/connection_ok.json missing or pass=false)
```

Exit cleanly (no error). The `connection-check` project must produce that file before any tick does work.

## Body

Run the signal-pipeline skill. Pull universe, apply filters, run trend-pullback-v1 and mean-revert-v1, rank top-3 per strategy, cluster-cap, write signals to `state/signals/<ts>.json`.

Done when:
- `state/signals/<ts>.json` exists with at most 6 signals (3 per strategy, cluster-capped)
- `journal/quant/YYYY-MM-DD.log` has a tick entry
- No exception left unlogged
