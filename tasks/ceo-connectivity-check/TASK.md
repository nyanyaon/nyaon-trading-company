---
name: CEO Connectivity Check
slug: ceo-connectivity-check
assignee: ceo
project: connection-check
recurring: false
---

One-shot smoke test owned by CEO. Verifies Binance testnet reachability and confirms every agent role can invoke its allowed `nyaon` CLI commands. Run this:

- Immediately after `paperclipai company import` (first-time setup)
- After any change to `.paperclip.yaml`, `nyaon_trading/`, or env secrets
- Before the week-2 promotion audit
- After any CEO-cleared halt to confirm the system is healthy

Done when `journal/audits/connectivity-<YYYY-MM-DD>.md` lists pass/fail per check.

## Procedure

All steps run from the company root. CEO env must include `NYAON_AGENT_ROLE=ceo`, `BINANCE_TESTNET_API_KEY`, `BINANCE_TESTNET_API_SECRET`.

### 1. Tooling sanity

```bash
which uv                              # /home/nyaon/.local/bin/uv or similar
uv --version                          # 0.11+
uv sync --frozen                      # locked deps install clean
uv run pytest tests/unit -q           # 22 passed
```

### 2. Binance testnet reachability (CEO role)

```bash
uv run nyaon mode show                # prints state/mode.json content
uv run nyaon account                  # returns totalWalletBalance, availableBalance
uv run nyaon klines BTCUSDT 15m 50    # 50 candles, monotonic open_time
uv run nyaon snapshot                 # writes state/snapshots/<ts>.json; exit 0
```

If any of these fail with `MissingSecretError`, the `BINANCE_TESTNET_*` env vars are not reaching the agent — check `.paperclip.yaml > agents.ceo.inputs.env`.

If `account` returns 401 / `-2014` / `-2015`, the testnet API key is invalid or revoked.

### 3. Halt round-trip (CEO can halt + resume)

```bash
uv run nyaon halt --reason "connectivity-check probe"
test -f state/halt.flag && echo "halt OK"
uv run nyaon resume
test ! -f state/halt.flag && echo "resume OK"
```

### 4. Go-live gate (must refuse)

```bash
uv run nyaon mode set live --reason "smoke test — must refuse"
# expect: exit 2, stderr message about missing promotion audit or live secrets
```

Pass condition: command refuses. If it succeeds, the gating is broken — STOP and escalate.

### 5. Per-agent role probe

For each role, simulate the paperclip-injected env and confirm only authorized commands succeed.

```bash
# Quant (read-only + signals)
NYAON_AGENT_ROLE=quant uv run nyaon klines BTCUSDT 15m 10     # ok
NYAON_AGENT_ROLE=quant uv run nyaon account                   # ok
NYAON_AGENT_ROLE=quant uv run nyaon mode set live --reason x  # must refuse

# Trader (place-order + cancel + account)
NYAON_AGENT_ROLE=trader uv run nyaon account                  # ok
NYAON_AGENT_ROLE=trader uv run nyaon mode set live --reason x # must refuse

# Ops (snapshot + halt + account)
NYAON_AGENT_ROLE=ops uv run nyaon snapshot                    # ok (may exit 3 on critical)
NYAON_AGENT_ROLE=ops uv run nyaon halt --reason "ops probe"   # ok (writes flag)
NYAON_AGENT_ROLE=ops uv run nyaon resume                      # mechanically allowed by CLI; policy enforced by paperclip role separation — note in report
NYAON_AGENT_ROLE=ops uv run nyaon mode set live --reason x    # must refuse

# CRO (halt + read-only)
NYAON_AGENT_ROLE=cro uv run nyaon halt --reason "cro probe"   # ok
NYAON_AGENT_ROLE=cro uv run nyaon resume                      # mechanically allowed by CLI; note in report
NYAON_AGENT_ROLE=cro uv run nyaon mode set live --reason x    # must refuse
```

Clean up: `uv run nyaon resume` if any probe left the halt flag set.

### 6. Optional: integration suite against live testnet

```bash
RUN_TESTNET_TESTS=1 uv run pytest tests/integration -q
```

Skip if a position would be undesirable; this places a real 0.002 BTCUSDT testnet round-trip.

### 7. Write report + gate file

Write `journal/audits/connectivity-<YYYY-MM-DD>.md` with one section per numbered step, listing pass/fail and any error output.

**On full pass**: atomically write `state/connection_ok.json` per `state/.schemas/connection_ok.json`:

```bash
cat > state/connection_ok.json.tmp <<EOF
{
  "ts": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
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
EOF
mv state/connection_ok.json.tmp state/connection_ok.json
```

This file unblocks every recurring tick in `strategy-testing` and `month-1-goal`. Without it, those ticks no-op.

**On any failure**: do NOT write `state/connection_ok.json`. Instead:

1. Write `state/incidents/<ts>.json` with the failing step.
2. Raise the halt flag: `uv run nyaon halt --reason "connectivity check failed: <step>"`.
3. Report to the user with the exact failed step + observed error.

## Boundaries

- This task is read-only against Binance except for the optional Step 6 integration test.
- Never run Step 6 in `live` mode — only testnet.
- Do not advance week-2 promotion audit until this task reports all green.
