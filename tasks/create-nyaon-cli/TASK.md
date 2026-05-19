---
name: Create Nyaon CLI
slug: create-nyaon-cli
assignee: ceo
project: nyaon-cli
recurring: false
---

Create the `nyaon` CLI inside the paperclip workspace so every other agent role can invoke `uv run nyaon ...` from this directory.

Paperclip's `company import` does NOT bundle the implementation code — only `COMPANY.md`, `.paperclip.yaml`, `agents/`, `skills/`, `tasks/`, `projects/`, `README.md`, and `LICENSE` are copied. The Python package (`bin/`, `nyaon_trading/`, `pyproject.toml`, `uv.lock`, `.python-version`, `state/.schemas/`, `tests/`) must be authored or pulled into the workspace by this task.

The canonical source already exists at `/home/nyaon/nyaon-trading-company/` on this host. CEO uses it as reference; the workspace gets its own copy or symlink.

## Reference material

| Artifact | Source path |
| --- | --- |
| Design spec | `/home/nyaon/nyaon-trading-company/docs/superpowers/specs/2026-05-19-binance-connectivity-design.md` |
| Implementation plan | `/home/nyaon/nyaon-trading-company/docs/superpowers/plans/2026-05-19-binance-connectivity.md` |
| Working code | `/home/nyaon/nyaon-trading-company/nyaon_trading/` + `/home/nyaon/nyaon-trading-company/bin/nyaon` |
| Schemas | `/home/nyaon/nyaon-trading-company/state/.schemas/` |
| Tests | `/home/nyaon/nyaon-trading-company/tests/unit/` |

## Decision tree

Pick the lowest-effort option that works for this host.

| Option | When to pick | Effort |
| --- | --- | --- |
| A. **Symlink from source** | Same host, source repo is the canonical artifact | 5 min |
| B. **Copy from source** | Same host, want workspace independent of source | 10 min |
| C. **`uv tool install --from source`** | Want `nyaon` on global PATH, no `uv run` prefix | 10 min |
| D. **Re-author from spec + plan** | Source repo unavailable on this host | 2–4 hours |

Default: **Option A** (symlink). Pick another only with a reason.

## Procedure — Option A (symlink)

```bash
SRC=/home/nyaon/nyaon-trading-company
DEST="$(pwd)"   # paperclip workspace root; CEO must be in workspace cwd
ln -s "$SRC/bin"              "$DEST/bin"
ln -s "$SRC/nyaon_trading"    "$DEST/nyaon_trading"
ln -s "$SRC/pyproject.toml"   "$DEST/pyproject.toml"
ln -s "$SRC/uv.lock"          "$DEST/uv.lock"
ln -s "$SRC/.python-version"  "$DEST/.python-version"
mkdir -p state
ln -s "$SRC/state/.schemas"   "$DEST/state/.schemas"
ln -s "$SRC/tests"            "$DEST/tests"
uv sync --frozen
```

## Procedure — Option B (copy)

```bash
SRC=/home/nyaon/nyaon-trading-company
cp -r "$SRC/bin" "$SRC/nyaon_trading" "$SRC/tests" .
cp "$SRC/pyproject.toml" "$SRC/uv.lock" "$SRC/.python-version" .
mkdir -p state/.schemas && cp "$SRC/state/.schemas/"*.json state/.schemas/
uv sync --frozen
```

## Procedure — Option C (uv tool install)

```bash
SRC=/home/nyaon/nyaon-trading-company
uv tool install --from "$SRC" nyaon-trading
which nyaon                    # ~/.local/share/uv/tools/nyaon-trading/bin/nyaon
```

After install, drop the `uv run` prefix — call `nyaon ...` directly. CEO still must `cd` to the workspace before invoking so `state/mode.json` resolves correctly.

## Procedure — Option D (re-author from spec)

Only if source repo is unreachable. CEO reads the design spec and implementation plan (paths above) and writes the package by hand following the 16-task plan. This task expands to roughly 2–4 hours and should escalate to the user before starting. Do NOT begin Option D without explicit user approval.

## Verification (all options)

```bash
uv run pytest tests/unit -q                      # 22 passed
uv run nyaon mode show                           # prints state/mode.json content
uv run nyaon                                     # prints usage, exits 2 — proves dispatcher reachable
```

If `state/mode.json` doesn't exist yet, bootstrap it:

```bash
cat > state/mode.json <<'EOF'
{"mode":"testnet","set_by":"bootstrap","set_at":"2026-05-20T00:00:00Z","reason":"init","live_size_multiplier":1.0}
EOF
```

Then re-run `uv run nyaon mode show` and confirm output.

## Done when

- `uv run nyaon mode show` (or `nyaon mode show` for Option C) succeeds from the workspace cwd
- `uv run pytest tests/unit -q` reports `22 passed`
- `journal/audits/create-nyaon-cli-<YYYY-MM-DD>.md` records the chosen option, the commands run, and the verification output

## On failure

- Capture the exact error.
- Write `state/incidents/<ts>.json` with `kind=create_nyaon_cli_failed`.
- Escalate to user with the option, command, and stderr. Do NOT start `nyaon-cli-skill-author` or `ceo-connectivity-check` until this task passes.

## Boundaries

- This task does not modify trading logic. It is plumbing only.
- Live API keys are NOT required at this stage. Testnet keys are sufficient for verification (`nyaon mode show` doesn't even hit Binance).
- Do NOT invoke any tick (`quant-tick`, `cro-tick`, `trader-tick`, `ops-reconcile`) until this task reports done.
