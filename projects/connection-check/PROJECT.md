---
name: Connection Check
description: Phase-zero gate. Verify Binance testnet reachability and per-role CLI access before any trading routine fires. Blocks strategy-testing until passed.
slug: connection-check
owner: ceo
---

# Connection Check

Phase-zero. Runs once after `paperclipai company import` (and again after any change to `.paperclip.yaml`, `nyaon_trading/`, env secrets, or `state/.schemas/`). Outputs a single file: `state/connection_ok.json`. Every recurring tick (`quant-tick`, `cro-tick`, `trader-tick`, `ops-reconcile`) checks for this file and skips its work if missing.

## Scope

Day 0. Strictly pre-trading. No orders placed. No live capital. Single CEO-owned task.

## Tasks under this project

- `ceo-connectivity-check` (one-shot, owner CEO)

## Pass criteria

All seven steps in `ceo-connectivity-check` report `ok` and `state/connection_ok.json` is written with:

```json
{
  "ts": "2026-05-20T05:00:00Z",
  "pass": true,
  "checks": {
    "tooling": "ok",
    "account": "ok",
    "klines": "ok",
    "snapshot": "ok",
    "halt_round_trip": "ok",
    "go_live_refused": "ok",
    "per_role_probe": "ok"
  }
}
```

## Exit conditions

- **Pass** → `state/connection_ok.json` exists with `pass=true`. Hand-off to `strategy-testing` is automatic — its ticks start passing the precondition check on their next scheduled fire.
- **Fail** → no `state/connection_ok.json` written (or `pass=false`). All `strategy-testing` ticks remain no-ops. CEO writes a remediation entry in `journal/audits/connectivity-<date>.md` and re-runs after the fix.

## Out of scope

- Live trading (handled by `month-1-goal`)
- Strategy validation (handled by `strategy-testing`)
- Promotion audit (handled by `promotion-audit` inside `strategy-testing`)

## Dependencies

- `paperclipai company import` succeeded
- `BINANCE_TESTNET_API_KEY` / `BINANCE_TESTNET_API_SECRET` provisioned
- `uv` on PATH for the agent subprocess

## Re-run cadence

One-shot by design. Re-run on demand whenever:

- `.paperclip.yaml` is edited
- `nyaon_trading/` package code changes
- Binance testnet keys are rotated
- A `state/halt.flag` has been cleared and CEO wants to confirm the system is healthy before resuming ticks
- The week-2 `promotion-audit` is about to run
