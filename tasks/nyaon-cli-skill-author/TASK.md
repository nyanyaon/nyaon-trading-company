---
name: Nyaon CLI Skill Author
slug: nyaon-cli-skill-author
assignee: ceo
project: nyaon-cli
recurring: false
---

Author a canonical agent skill at `skills/nyaon-cli/SKILL.md` covering the complete `nyaon` CLI surface. CEO performs this task using the `skill-creator` skill so the result follows the same shape and quality bar as other Anthropic-grade skills.

This skill becomes the single source of truth that every agent role's `AGENTS.md` Tooling section references. It replaces (or supersedes) the scattered Implementation tables currently embedded in `skills/exchange-ops/SKILL.md` and `skills/signal-pipeline/SKILL.md`.

## Precondition

`nyaon-cli-port` task is done. `nyaon mode show` works from the workspace.

## Procedure

1. **Invoke skill-creator.** In CEO's Claude Code session:

   ```
   Use the skill-creator skill to author a new skill named `nyaon-cli` at `skills/nyaon-cli/SKILL.md`.
   ```

   `skill-creator` will prompt for skill metadata. Use:
   - **name**: `nyaon-cli`
   - **description**: `Definitive reference for the nyaon CLI. Every subcommand, expected arguments, exit codes, state-file side effects, and per-role permissions for the Binance USDT-M trading pipeline.`
   - **trigger hints**: invoked whenever an agent calls `nyaon ...` and needs to know which subcommand to use, what flags it takes, what files it reads/writes, or whether the agent's role is allowed to call it.

2. **Source material.** The new skill MUST cover every subcommand currently implemented in `nyaon_trading/cli/`. Read each module:

   - `nyaon_trading/cli/mode.py` → `nyaon mode show`, `nyaon mode set testnet|live --reason '...'`
   - `nyaon_trading/cli/signals.py` → `nyaon signals`
   - `nyaon_trading/cli/klines.py` → `nyaon klines <SYM> <interval> <limit>`
   - `nyaon_trading/cli/account.py` → `nyaon account`
   - `nyaon_trading/cli/place_order.py` → `nyaon place-order --intent <path>`
   - `nyaon_trading/cli/cancel.py` → `nyaon cancel --symbol <SYM> --coid <coid>`
   - `nyaon_trading/cli/snapshot.py` → `nyaon snapshot`
   - `nyaon_trading/cli/halt.py` → `nyaon halt --reason '...'`, `nyaon resume`

3. **Required sections in the authored skill.** skill-creator will scaffold; ensure all of the following land in `skills/nyaon-cli/SKILL.md`:

   - **Purpose** — one-liner: which CLI, who calls it, what it gates.
   - **Invocation** — `uv run nyaon ...` (and `nyaon ...` if Option 2 of `nyaon-cli-port` was used).
   - **Mode resolution** — every call reads `state/mode.json`; secrets resolved from env per mode (`BINANCE_TESTNET_*` or `BINANCE_LIVE_*`).
   - **Per-role permission matrix** — table mapping each subcommand to allowed roles (CEO, CRO, Quant, Trader, Ops). Mark mechanically-enforced vs paperclip-env-enforced.
   - **Command reference** — one section per subcommand:
     - Synopsis (exact flags)
     - Behavior (what it reads, what it writes, what API it hits)
     - Exit codes (0 normal, 2 user error / halted, 3 critical snapshot diff)
     - State-file side effects (which `state/...` files are read or written)
     - Errors it may surface (`MissingSecretError`, `HaltedError`, `GoLiveRefused`, `BinanceError`, `TimestampSkewError`, `RateLimitError`)
     - Example call + expected stdout JSON
   - **State-file contract** — link to each schema under `state/.schemas/` and explain atomic-write pattern.
   - **Halt semantics** — flag presence blocks `place-order`; CRO + Ops may halt, only CEO clears.
   - **Go-live gating** — five preconditions of `nyaon mode set live`, citing `state/.schemas/promotion-audit.json`.
   - **Common pitfalls** — running in wrong cwd, missing `NYAON_AGENT_ROLE`, stale `state/connection_ok.json`.

4. **Cross-link the new skill.** After authoring, update every `agents/<role>/AGENTS.md` Tooling section to add a single line near the top:

   ```markdown
   For the complete CLI reference, exit codes, and role permissions, read `skills/nyaon-cli/SKILL.md`.
   ```

   Keep the existing per-role command list — the cross-link is additive.

5. **Sanity check.** Open `skills/nyaon-cli/SKILL.md` and confirm:
   - Every subcommand has its own section.
   - The per-role permission matrix matches actual code behavior (run `grep -n "NYAON_AGENT_ROLE\|HaltedError\|GoLiveRefused" nyaon_trading/cli/*.py` to verify).
   - No invented flags. Every `--flag` cited matches an `argparse.add_argument` in the corresponding `cli/*.py`.

## Done when

- `skills/nyaon-cli/SKILL.md` exists, authored via skill-creator.
- All 9 subcommands documented with full synopsis + exit codes + state effects.
- Per-role permission matrix present and matches code.
- Every `agents/*/AGENTS.md` Tooling section adds the cross-link line.
- `journal/audits/nyaon-cli-skill-<YYYY-MM-DD>.md` records the skill-creator invocation and the final file path.

## Boundaries

- Do NOT invent CLI flags or behaviors that don't exist in `nyaon_trading/cli/`.
- Do NOT delete the Implementation sections in `skills/exchange-ops/SKILL.md` or `skills/signal-pipeline/SKILL.md` in this task — those are reduced to "see skills/nyaon-cli/SKILL.md" later, not now.
- Stay under skill-creator's recommended skill size (one focused responsibility).

## On failure

- Capture skill-creator's error or refusal reason.
- Write `state/incidents/<ts>.json` with `kind=nyaon_cli_skill_author_failed`.
- Escalate to user with the exact step that failed.
