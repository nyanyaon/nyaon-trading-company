---
name: Nyaon CLI
description: Ship the nyaon CLI portably into the paperclip workspace and author a canonical skill documenting its full command surface. Phase minus-one — runs before connection-check.
slug: nyaon-cli
owner: ceo
---

# Nyaon CLI

Phase −1. Pre-day-zero. Solves the paperclip-import gap: when a company is imported, only spec-recognized files (COMPANY.md, .paperclip.yaml, agents/, skills/, tasks/, projects/) are bundled. The `nyaon` CLI source (`bin/`, `nyaon_trading/`, `pyproject.toml`, `uv.lock`, `state/.schemas/`, `tests/`) is NOT bundled, so agents can't run `uv run nyaon ...` until those files reach the workspace.

This project owns two outputs:

1. A working `nyaon` CLI installation inside the paperclip workspace (via `create-nyaon-cli`).
2. A canonical, agent-readable skill at `skills/nyaon-cli/SKILL.md` authored by the CEO via the `skill-creator` skill (via `nyaon-cli-skill-author`).

## Scope

| Task | Owner | Output |
| ---- | ----- | ------ |
| `create-nyaon-cli` | CEO | CLI reachable from workspace; `which nyaon` (or equivalent) returns a working path |
| `nyaon-cli-skill-author` | CEO | `skills/nyaon-cli/SKILL.md` covers every `nyaon` subcommand with role permissions, exit codes, state-file effects |

## Pass criteria

Both tasks completed AND:

- `uv run nyaon mode show` succeeds from the paperclip workspace as every agent role.
- `skills/nyaon-cli/SKILL.md` exists and was written by the CEO using `skill-creator`.
- The new skill is referenced from `agents/<role>/AGENTS.md` Tooling sections (replaces or complements per-agent ad-hoc command lists).

## Exit conditions

- **Pass** → hand-off to `connection-check`. CEO runs `ceo-connectivity-check` next.
- **Fail** → halt; do not start `connection-check`. CEO escalates the port problem to the user.

## Dependencies

- Canonical source available at <https://github.com/nyanyaon/nyaon-trading-company> (CEO can `git clone` or `curl raw.githubusercontent.com/...` for the design spec, plan, and reference code)
- `uv` on PATH for the agent subprocess
- `skill-creator` skill available in the agent's Claude Code session

## Strict project chain

```
nyaon-cli  →  connection-check  →  strategy-testing  →  month-1-goal
```

## Out of scope

- Trading logic changes
- Strategy validation
- Live ramp
