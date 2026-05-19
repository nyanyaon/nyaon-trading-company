# Nyaon Trading Company

Autonomous AI crypto futures trading firm. 5 agents, Binance USDT-M, self-improving.

**Month-1 goal:** $1000 cumulative PnL. **Phase plan:** port the CLI (`nyaon-cli`), day-0 connectivity gate (`connection-check`), testnet weeks 1-2 (`strategy-testing`), conditional promotion to live weeks 3-4 (`month-1-goal`).

## Projects

| Project            | Phase            | Owns                                                                 |
| ------------------ | ---------------- | -------------------------------------------------------------------- |
| `nyaon-cli`        | Phase −1         | `nyaon-cli-port`, `nyaon-cli-skill-author` — make CLI reachable + author canonical skill |
| `connection-check` | Day 0            | `ceo-connectivity-check` — writes `state/connection_ok.json` gate    |
| `strategy-testing` | Wk 1-2 testnet   | Pipeline ticks (quant/cro/trader/ops) + week-2 `promotion-audit`     |
| `month-1-goal`     | Outcome / Wk 3-4 | `ceo-weekly-retro`, live ramp, $1000 PnL target                      |

Strict dependency chain: `nyaon-cli` → `connection-check` → `strategy-testing` → `month-1-goal`. `nyaon-cli` fixes the paperclip-import gap (CLI source isn't bundled by `paperclipai company import`) by porting the CLI into the workspace and authoring a definitive skill via `skill-creator`. Every tick in `strategy-testing` (and `month-1-goal`) checks for `state/connection_ok.json` at the top of its run and no-ops cleanly when missing. `month-1-goal` additionally requires `strategy-testing`'s `promotion-audit` to pass before any live order is placed.

## Workflow

Pipeline:

```
Quant (15m) → CRO (1m) → Trader (1m) → Ops (5m)
                                       └── weekly CEO retro
```

- **Quant** scans all USDT-M perpetuals, applies liquidity/spread/volatility/funding filters, runs two seeded strategies, publishes top-3 candidates per strategy.
- **CRO** runs nine deterministic risk gates (`RISK_POLICY.md` §3), sizes accepted signals, may halt unilaterally.
- **Trader** executes idempotent orders on Binance; never sizes itself.
- **Ops** reconciles internal state vs exchange every 5 minutes; raises halt on critical mismatch.
- **CEO** runs a Sunday retro; tunes risk knobs and strategy params; decides testnet → live promotion.

## Org chart

| Agent  | Title                    | Reports to | Model        | Cadence | Skills                          |
| ------ | ------------------------ | ---------- | ------------ | ------- | ------------------------------- |
| CEO    | Chief Executive Officer  | —          | Sonnet 4.6   | weekly  | self-improvement                |
| CRO    | Chief Risk Officer       | CEO        | Sonnet 4.6   | 1m      | risk-gating                     |
| Quant  | Quant Analyst            | CEO        | Sonnet 4.6   | 15m     | signal-pipeline                 |
| Trader | Execution Trader         | CRO        | Haiku 4.5    | 1m      | exchange-ops                    |
| Ops    | Ops Monitor              | CEO        | Haiku 4.5    | 5m      | exchange-ops                    |

## Cost discipline

- Haiku 4.5 on every high-frequency loop (Trader, Ops).
- Sonnet 4.6 only on thinking roles (CEO, CRO, Quant).
- Deterministic gates and reconciliation paths — no free-form reasoning where math will do.
- Per-tick token budgets are noted in each agent's AGENTS.md.

## Self-improvement

- Strategies, risk knobs, agent prompts are all editable by the CEO via weekly retro.
- Parameter diffs apply directly. Code-level diffs (new strategy logic, new gate) escalate to the user for human review.
- Hit-rate, profit factor, slippage, and halt incidents drive every change.

## Governance

`RISK_POLICY.md` is the single source of truth. CRO is the sole risk gate. CRO or Ops may unilaterally raise the halt flag; only the CEO can clear it.

## Getting started

```bash
paperclipai company import --from /home/nyaon/nyaon-trading-company
```

Then provision secrets:

- `BINANCE_TESTNET_API_KEY` / `BINANCE_TESTNET_API_SECRET` — required from day one. Get a key at https://testnet.binancefuture.com.
- `BINANCE_LIVE_API_KEY` / `BINANCE_LIVE_API_SECRET` — only after CEO writes a promotion entry (end of week 2 at earliest).

Start the schedules and watch the first 24h of Ops reconcile output before enabling full filtering.

## Code & tooling

The trading code lives in `nyaon_trading/` and is exposed as the `nyaon` CLI. The package is managed exclusively by [`uv`](https://docs.astral.sh/uv/) — no `pip`, `poetry`, `conda`, `pyenv`, or `pipx`.

### Quickstart

```bash
uv sync                                  # install deps from uv.lock
uv run pytest tests/unit -q              # unit tests, no network

# Integration (testnet):
export BINANCE_TESTNET_API_KEY=...
export BINANCE_TESTNET_API_SECRET=...
RUN_TESTNET_TESTS=1 uv run pytest tests/integration -q

# Run CLIs:
./bin/nyaon mode show
./bin/nyaon signals
./bin/nyaon snapshot
```

### Adding dependencies

```bash
uv add <package>          # also updates uv.lock
uv lock --upgrade-package <package>
```

## References

- Agent Companies spec: https://agentcompanies.io/specification
- Paperclip: https://github.com/paperclipai/paperclip
- Paperclip self-host: https://paperclip.ing/llms.txt

## License

MIT — see `LICENSE`.
