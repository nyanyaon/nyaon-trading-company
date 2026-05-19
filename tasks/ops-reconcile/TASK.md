---
name: Ops Reconcile
slug: ops-reconcile
assignee: ops
project: strategy-testing
recurring: true
---

## Precondition

Before any work, check `state/connection_ok.json` exists and contains `{"pass": true, ...}`. If missing or `pass != true`, **skip the tick** with a single line in `journal/ops/YYYY-MM-DD.log`:

```
<ts> skip: connection-check not passed (state/connection_ok.json missing or pass=false)
```

Exit cleanly (no error).

## Body

Run `uv run nyaon snapshot`. The CLI pulls account + open orders + position risk + income, builds canonical snapshot, diffs against prior snapshot in `state/snapshots/`, classifies `clean | benign | critical`, and on critical writes incident + touches halt flag.

Done when:
- `state/snapshots/<ts>.json` written atomically (newest sorts last by ISO timestamp)
- CLI exit code: 0 for clean/benign, 3 for critical
- Critical mismatch → `state/incidents/<ts>.json` exists + `state/halt.flag` present
- `journal/ops/YYYY-MM-DD.log` has a tick entry with classification
