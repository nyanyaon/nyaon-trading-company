---
name: strategy-rnd
description: Hypothesis → backtest → proposal cycle for trading strategies. Used by Quant to research new edge, measure it against historical klines, and propose CEO-approved diffs to the strategy code under nyaon_trading/strategy/.
---

# strategy-rnd

Quant's R&D skill. Used weekly (Friday) and ad-hoc when a regime shift or losing streak prompts investigation. Produces backtest reports and proposed code/parameter diffs. Never modifies `nyaon_trading/strategy/*.py` without CEO approval — the diff sits in `journal/quant/rnd-YYYY-WW.md` until the Sunday retro signs off.

## Process (one full cycle)

1. **Frame a hypothesis** in one sentence.
   - Example: "Adding a 50-period ADX > 25 filter to `trend-pullback-v1` should reduce false breakouts when realized volatility is low."
   - Hypothesis must be falsifiable. It must name: the strategy, the proposed change, the metric that would prove or disprove it, and the dataset window.

2. **Gather data deterministically.**
   - Use `uv run nyaon klines <SYM> <interval> <limit>` to print recent candles.
   - For longer windows, write a one-off Python script under `journal/quant/rnd-scripts/<hash>.py` that loops `client.get_public("/fapi/v1/klines", ...)` over a date range.
   - Cache pulls to `state/rnd_cache/<symbol>_<interval>_<from>_<to>.json` so repeat runs are cheap and reproducible.

3. **Implement the variant** as a NEW file `nyaon_trading/strategy/<name>_v2.py` (never edit the live strategy in-place during R&D). The variant must:
   - Be a pure function of a klines DataFrame (no I/O, no globals).
   - Return the same `TrendSignal | MRSignal | None` dataclass shape as the existing strategy.
   - Have full unit-test coverage matching the existing test patterns in `tests/unit/test_<strategy>.py`.

4. **Backtest** against the cached data:
   - Walk forward bar-by-bar. For each bar, call `score(df.iloc[:i+1])`. When a signal fires, simulate the entry + SL/TP using the suggested bps.
   - Track: total trades, hit rate, profit factor, max drawdown, Sharpe (informational), avg slippage assumption, total bars in test.
   - Use `uv run nyaon backtest <strategy> --symbol BTCUSDT --interval 15m --from <iso> --to <iso>` once the `nyaon-backtest` task lands. Until then, the per-run Python script does it.

5. **Compare** against the baseline (current production strategy run over the identical window). The variant must win on **all four** of: hit rate, profit factor, max drawdown, total return — OR have a documented qualitative reason (e.g. "halves drawdown at the cost of 3 fewer trades — acceptable risk reduction"). One-metric wins are usually overfitting.

6. **Document** in `journal/quant/rnd-YYYY-WW.md`:
   - Hypothesis (verbatim from step 1)
   - Dataset window + symbols + bar count
   - Baseline vs variant metrics table
   - Walk-forward equity curve as ASCII or saved to `journal/quant/rnd-charts/<hash>.png`
   - Falsification check: does the data support the hypothesis? Yes / No / Inconclusive
   - Proposed diff: file path + before/after code blocks OR parameter changes
   - Confidence: low / medium / high (be honest)
   - Open questions for CEO

7. **Propose** to CEO. Add a one-line entry to `state/proposals/<YYYY-WW-NN>.json`:

```json
{
  "id": "rnd_2026-21_01",
  "ts": "2026-05-22T18:00:00Z",
  "author": "quant",
  "title": "Add ADX volatility filter to trend-pullback-v1",
  "kind": "code",
  "files": ["nyaon_trading/strategy/trend.py"],
  "rationale": "journal/quant/rnd-2026-21.md#hypothesis-1",
  "expected_impact": "+12% profit factor, -30% drawdown on BTC 15m last 90 days",
  "risk": "May reduce trade count by ~25% — could underperform in trending markets",
  "status": "proposed"
}
```

Set `status` to `proposed`. CEO updates to `approved`, `rejected`, or `needs_revision` during retro.

## Approval workflow

| Diff kind | Path | Approval |
| --- | --- | --- |
| Parameter only (numeric thresholds, EMA periods, RSI cutoffs) | edits to existing `nyaon_trading/strategy/*.py` | CEO direct approval in weekly retro |
| New strategy variant file (`*_v2.py`, etc.) | adds to `nyaon_trading/strategy/` + tests | CEO approval **and** user escalation (code-level diff per `agents/ceo/AGENTS.md` boundaries) |
| Deleting or replacing a live strategy | overwrites production file | User confirmation required, even after CEO approval |

Approved diffs apply before Monday 00:00 UTC. Rejected diffs stay in the journal as future inspiration. `needs_revision` returns to Quant with the CEO's note.

## Anti-overfitting rules

- **Train/test split**: backtest only on data NOT used to develop the hypothesis. If you developed on Jan-Mar, test on Apr-Jun.
- **No metric chasing**: do not iterate the variant against the same test window until it looks good. One shot per hypothesis. If it fails, write a new hypothesis.
- **Multi-symbol check**: a variant must beat baseline on at least 3 symbols, not just BTC.
- **Drawdown floor**: any variant with max DD > 12% is automatically rejected regardless of return.
- **Sample-size floor**: < 20 trades in the test window is not enough evidence. Extend the window.
- **Walk-forward only**: never use future information (close > some_lookback_max), even by accident. Slice indices carefully.

## Tooling

| Action | Command |
| --- | --- |
| Pull recent klines | `uv run nyaon klines <SYM> <interval> <limit>` |
| Read live strategy | `cat nyaon_trading/strategy/trend.py` |
| Read existing tests for patterns | `cat tests/unit/test_trend.py` |
| Run a custom backtest script | `uv run python journal/quant/rnd-scripts/<hash>.py` |
| Run formal backtest (once available) | `uv run nyaon backtest <strategy> --symbol <SYM> --interval <I> --from <iso> --to <iso>` |
| Lint a proposed variant | `uv run ruff check nyaon_trading/strategy/<file>.py` |
| Type-check | `uv run pyright nyaon_trading/strategy/<file>.py` |
| Unit-test a variant | `uv run pytest tests/unit/test_<strategy>_v2.py -v` |

## Done conditions for one R&D cycle

- One or more hypotheses written, backtested, documented
- `journal/quant/rnd-YYYY-WW.md` exists with the full report
- Zero, one, or more proposals written to `state/proposals/`
- No modifications to live `nyaon_trading/strategy/*.py` in this cycle (modifications happen post-approval, in a follow-up step)
- The week's standard `quant-tick` runs continued uninterrupted

## Boundaries

- Quant may NOT modify `nyaon_trading/strategy/*.py` mid-week. Only after CEO approval.
- Quant may NOT introduce strategies that trade outside the symbol filter in `RISK_POLICY.md` §2.
- Quant may NOT bypass the train/test split or sample-size floor.
- Quant may NOT propose a variant whose backtest used live (post-fill) data leakage.
- All cached data and scripts live under `journal/quant/rnd-*` and `state/rnd_cache/` — never in the production code path until approved.
