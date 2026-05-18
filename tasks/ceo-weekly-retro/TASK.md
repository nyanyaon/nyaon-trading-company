---
name: CEO Weekly Retro
slug: ceo-weekly-retro
assignee: ceo
project: month-1-goal
schedule:
  timezone: UTC
  startsAt: 2026-05-24T23:00:00Z
  recurrence:
    frequency: weekly
    interval: 1
    weekdays:
      - sunday
    time:
      hour: 23
      minute: 0
---

Run the self-improvement skill. Read the week's journals, signals, fills, incidents. Write `journal/retros/YYYY-WW.md` with headline metrics, halt incidents, gate-firing histogram, top winners/losers, edge calibration, proposed diffs. Apply approved parameter diffs. Escalate code-level diffs to the user.

End of week 2 only: audit `RISK_POLICY.md` §6 promotion criteria. Write `state/mode.json` if all five pass; otherwise extend testnet.

Done when:
- `journal/retros/YYYY-WW.md` written
- Parameter diffs applied to the relevant files
- Code-level diffs sent to the user with full context
- Promotion decision recorded (weeks 2, 3, 4)
