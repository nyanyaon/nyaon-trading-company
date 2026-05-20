---
name: Quant R&D
slug: quant-rnd
assignee: quant
project: strategy-testing
recurring: true
---

Weekly R&D cycle. Quant researches new strategy edge, backtests against historical klines, and proposes CEO-reviewed diffs to `nyaon_trading/strategy/*.py`. Runs Friday 18:00 UTC — late enough to include the full trading week, early enough that CEO can review proposals before Sunday's retro.

## Precondition

`state/connection_ok.json` exists with `pass=true`. If missing, skip with a single line in `journal/quant/YYYY-MM-DD.log` and exit cleanly:

```
<ts> skip: connection-check not passed (state/connection_ok.json missing or pass=false)
```

## Body

Run the `strategy-rnd` skill in order. One cycle per fire.

1. **Survey the week**: read the most recent `journal/quant/`, `journal/cro/`, `journal/trader/`, `state/orders/`, `state/snapshots/`. Identify the top 3 issues that strategy-rnd could address (false breakouts, missed reversals, slippage above 5 bps, hit rate < 40%, etc.).

2. **Pick one hypothesis** that targets one of those issues. Be specific. Write it down before touching data.

3. **Pull historical klines** for the symbols and interval relevant to the hypothesis. Use `uv run nyaon klines <SYM> <interval> <limit>` for the live cache or a custom script under `journal/quant/rnd-scripts/<hash>.py` for longer windows. Save to `state/rnd_cache/`.

4. **Implement the variant** as a new file `nyaon_trading/strategy/<name>_v2.py` (NOT in-place edit). Pure function, same dataclass return shape, full unit-test coverage in `tests/unit/test_<name>_v2.py`. Run `uv run pytest tests/unit/test_<name>_v2.py -v` until green.

5. **Backtest** the variant + baseline over the same window. Track hit rate, profit factor, max drawdown, total return, trade count. Use `uv run nyaon backtest <strategy> --symbol <SYM> --interval <I> --from <iso> --to <iso>` if available, else the per-run script.

6. **Apply anti-overfitting checks** (`strategy-rnd` SKILL.md): train/test split, multi-symbol verification, drawdown floor, sample-size floor, walk-forward only.

7. **Write the report** to `journal/quant/rnd-YYYY-WW.md` per the structure in `strategy-rnd` SKILL.md step 6.

8. **Submit proposal** by writing `state/proposals/<YYYY-WW-NN>.json` per `strategy-rnd` step 7. Always status=`proposed`. Quant does NOT change it after submission — CEO updates the status during the Sunday retro.

9. **Log the tick** to `journal/quant/YYYY-MM-DD.log` with hypothesis ID, backtest result, and proposal ID (or "no proposal — hypothesis falsified").

## Apply approved diffs

If CEO has already approved a previous week's proposal (status=`approved` in `state/proposals/`), Quant applies that diff during this tick BEFORE researching new hypotheses:

```bash
# Read the approved proposal
cat state/proposals/<id>.json

# Apply the diff (edit the file path listed in proposal.files)
# For parameter diffs: edit in place.
# For new-strategy diffs: ensure the new file is added to the dispatcher in
#   nyaon_trading/strategy/pipeline.py and tested.

# Verify nothing broke
uv run pytest tests/unit -q                    # 22+ passed
uv run ruff check nyaon_trading/strategy/
uv run pyright nyaon_trading/strategy/

# Mark the proposal applied
# (Edit state/proposals/<id>.json: status="applied", applied_at="<iso>")
```

If any test or lint fails, revert the change, write `state/incidents/<ts>.json` with `kind=proposal_apply_failed`, and escalate to CEO. Do NOT leave the codebase in a broken state.

## Done when

- `journal/quant/rnd-YYYY-WW.md` exists with one or more hypotheses, backtests, and falsification verdicts
- At most one proposal under `state/proposals/` for this week (multiple OK if multiple independent hypotheses fired; usually one per cycle)
- Any previously-approved proposals applied + verified + status flipped to `applied`
- `tests/unit` still green (22+)
- `journal/quant/YYYY-MM-DD.log` has the Friday R&D tick entry

## On failure

- Backtest crashed: write `state/incidents/<ts>.json` with `kind=backtest_failed`, the script path, the stderr. Skip the proposal step for this week.
- Variant test failed: do NOT propose. Falsified hypothesis is a valid outcome — log it and move on.
- Apply-step broke unit tests: REVERT the apply immediately. Then escalate.

## Boundaries

- Quant may modify `nyaon_trading/strategy/*.py` ONLY when applying a CEO-approved proposal. Never on speculation.
- Quant may NOT skip the train/test split, sample-size floor, multi-symbol check, or drawdown floor.
- Quant may NOT delete proposals (CEO is the audit trail). To withdraw, set status=`withdrawn` with reason.
- Quant may NOT touch `RISK_POLICY.md`, `agents/`, `tasks/`, or `.paperclip.yaml` from this task.
- Quant must keep token usage under 60k for the full R&D tick. Backtests run in Python, not in the LLM.
