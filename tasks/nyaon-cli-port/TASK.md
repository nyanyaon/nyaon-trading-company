---
name: Nyaon CLI Port
slug: nyaon-cli-port
assignee: ceo
project: nyaon-cli
recurring: false
---

Make the `nyaon` CLI reachable from the paperclip workspace. The CLI source lives in the imported repo at `/home/nyaon/nyaon-trading-company` (`bin/`, `nyaon_trading/`, `pyproject.toml`, `uv.lock`, `state/.schemas/`, `tests/`), but paperclip's `company import` does NOT bundle those files because they're not part of the agentcompanies/v1 spec.

CEO picks one of three port strategies and executes.

## Decision: which strategy?

| Option | When to use | Effort | Portability |
| ------ | ----------- | ------ | ----------- |
| 1. Symlink | Single host; want live edits from source repo to reach workspace | 5 min | Single host only |
| 2. uv tool install --from path | Same host; want `nyaon` on PATH globally without symlinks | 10 min | Single host |
| 3. Publish to PyPI as `nyaon-trading` | Multi-host or sharing | 30 min + maintenance | Anywhere with PyPI |

Default: **Option 2** (`uv tool install`). Pick another only if you have a reason.

## Procedure — Option 1 (symlink)

```bash
SRC=/home/nyaon/nyaon-trading-company
DEST="$(paperclipai company path nyaon-trading-company)"  # or wherever paperclip placed the workspace
ln -s "$SRC/bin"             "$DEST/bin"
ln -s "$SRC/nyaon_trading"   "$DEST/nyaon_trading"
ln -s "$SRC/pyproject.toml"  "$DEST/pyproject.toml"
ln -s "$SRC/uv.lock"         "$DEST/uv.lock"
ln -s "$SRC/.python-version" "$DEST/.python-version"
ln -s "$SRC/state"           "$DEST/state"
ln -s "$SRC/tests"           "$DEST/tests"
cd "$DEST" && uv sync --frozen
```

Verify:

```bash
cd "$DEST"
uv run nyaon mode show          # prints state/mode.json
uv run nyaon account            # returns balances (testnet)
```

## Procedure — Option 2 (uv tool install) — DEFAULT

Install the package as a globally-callable `nyaon` binary:

```bash
SRC=/home/nyaon/nyaon-trading-company
uv tool install --from "$SRC" nyaon-trading
which nyaon                      # ~/.local/share/uv/tools/nyaon-trading/bin/nyaon
nyaon mode show                  # works without `uv run`
```

After install, agents call `nyaon ...` directly (no `uv run` prefix). Update `agents/<role>/AGENTS.md` Tooling sections accordingly OR keep `uv run nyaon` (both work).

`nyaon` reads `state/mode.json` from the current working directory, so agents must `cd "$DEST"` before invoking.

## Procedure — Option 3 (PyPI publish) — only with user approval

1. CEO escalates to user: confirm PyPI account, package name, version policy.
2. Build: `uv build`
3. Publish: `uv publish` (needs `UV_PUBLISH_TOKEN`).
4. Install per workspace: `uv tool install nyaon-trading`

## Verification (all options)

Run this checklist as CEO:

```bash
nyaon mode show              # or `uv run nyaon mode show`
nyaon account                # returns testnet balances
nyaon klines BTCUSDT 15m 50  # returns 50 candles
```

If all three return non-empty JSON without `MissingSecretError`, port is done.

## Done when

- `nyaon` (or `uv run nyaon`) is invocable from the paperclip workspace cwd
- All three verification commands succeed for the CEO role
- `journal/audits/nyaon-cli-port-<YYYY-MM-DD>.md` records which option was chosen and the verification output

## On failure

- Capture the exact error (stderr).
- Write `state/incidents/<ts>.json` with `kind=nyaon_cli_port_failed`.
- Escalate to the user with the chosen option, command, and error. Do NOT start `ceo-connectivity-check` until this task passes.

## Boundaries

- No code changes to `nyaon_trading/` from this task — port only.
- No live API keys involved (testnet only at this phase).
- Do not invoke any agent skill that requires `nyaon` (`risk-gating`, `exchange-ops`, `signal-pipeline`) until this task reports done.
