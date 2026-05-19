---
name: Month 1 Goal — $1000 PnL
description: Overarching month-1 outcome. Reach $1000 cumulative PnL by end of week 4. Depends on strategy-testing passing the promotion audit.
slug: month-1-goal
owner: ceo
---

# Month 1 Goal — $1000 PnL

Overarching outcome for month 1. The validation work lives in `strategy-testing`; this project owns the *outcome*, the live ramp, and the weekly governance loop.

## Goal

Cumulative PnL ≥ $1000 by end of week 4.

## Phase plan (live phase)

| Week | Venue                          | Focus                                                | PnL target |
| ---- | ------------------------------ | ---------------------------------------------------- | ---------- |
| 3    | Live (if promotion passes)     | Small live trades. CRO unchanged. Watch slippage.    | ~$400      |
| 4    | Live                           | Scale within risk caps.                              | ~$600      |

If the week-2 promotion audit fails: live phase shifts to weeks 4-5 (no shortcut — capital does not move while criteria are unmet).

## Tasks under this project

- `ceo-weekly-retro` (Sunday 23:00 UTC) — governance + diff approval + live-ramp checkpoints

## Success metrics

- Cumulative PnL ≥ $1000
- Max drawdown ≤ 8%
- Profit factor ≥ 1.3
- Zero unresolved Ops critical mismatches
- ≤ 1 unscheduled halt per week by week 4

## Dependencies

- `connection-check` must produce `state/connection_ok.json` with `pass=true` (gating every tick).
- `strategy-testing` must produce a green promotion audit before any live order is placed.
- Live API secrets (`BINANCE_LIVE_API_KEY` / `BINANCE_LIVE_API_SECRET`) must be provisioned by the user before week 3.
- The dependency chain is strict: `connection-check` → `strategy-testing` → `month-1-goal`.

## Out of scope

- Multi-exchange
- Spot or options
- Manual overrides during a trading day (changes only via CEO retro)
