---
name: Trader Tick
slug: trader-tick
assignee: trader
project: strategy-testing
recurring: true
---

## Precondition

Before any work, check `state/connection_ok.json` exists and contains `{"pass": true, ...}`. If missing or `pass != true`, **skip the tick** with a single line in `journal/trader/YYYY-MM-DD.log`:

```
<ts> skip: connection-check not passed (state/connection_ok.json missing or pass=false)
```

Exit cleanly (no error).

## Body

Run the exchange-ops skill (execution side). Check `state/halt.flag` — if present, skip new entries (manage exits only). For each `state/intents/<intent_id>.json` with `status=approved`, run `uv run nyaon place-order --intent state/intents/<intent_id>.json`. The CLI places entry with deterministic `coid`, polls fill, then places paired SL/TP. Order audit lands in `state/orders/<coid>.json`.

Done when:
- Every approved intent has `status` flipped to `filled` or `failed` (with `failed_reason`)
- Every filled entry has its paired SL/TP coids in `state/orders/`
- `journal/trader/YYYY-MM-DD.log` has a tick entry with per-order slippage in bps
- If `state/halt.flag` exists, no new entries are placed (exits still managed via `uv run nyaon cancel`)
