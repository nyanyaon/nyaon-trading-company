# RISK_POLICY.md

Canonical risk governance for Nyaon Trading Company. CRO is the sole gate. CEO is the only role that can edit this file or clear a halt flag.

## 1. Hard limits

| Limit                          | Value                          |
| ------------------------------ | ------------------------------ |
| Max concurrent positions       | 5                              |
| Max risk per trade             | 1.0% of equity                 |
| Max gross exposure             | 3x equity (notional)           |
| Max leverage per symbol        | 5x                             |
| Daily loss circuit breaker     | -3% equity                     |
| Weekly loss circuit breaker    | -7% equity                     |
| Max correlation cluster weight | 40% of risk budget per cluster |

Breach any → CRO raises `halt_flag = true` immediately.

## 2. Symbol filters (Quant + CRO enforce)

Reject symbols that fail any:

- 24h quote volume < $50M USDT
- Spread > 5 bps at top of book
- ATR(14, 15m) / price < 0.15% (too dead)
- ATR(14, 15m) / price > 4% (too wild)
- Absolute funding rate > 0.10% per 8h
- Listed < 30 days
- Price < $0.01 (precision risk)

## 3. Nine-gate CRO acceptance order

Evaluated in order. Reject on first failure.

1. Halt flag clear
2. Symbol passes filters (section 2)
3. Daily and weekly loss budgets not exhausted
4. Concurrent-position cap not exceeded
5. Correlation cluster within cap
6. Signal age < 90 seconds
7. Strategy-level hit rate over last 50 signals ≥ 35% (cold-start grace: 20 signals)
8. Computed size ≤ 1.0% equity risk and ≤ 5x leverage
9. Spread + expected slippage < 25% of expected edge

## 4. Sizing math

```
risk_budget   = equity * 0.01
stop_distance = entry - stop                (long); reverse for short
qty           = risk_budget / stop_distance
notional      = qty * entry
leverage_used = notional / equity
```

If `leverage_used > 5` → scale qty down. If concentration cap hit → scale qty down to cap.

## 5. Halt logic

`halt_flag = true` blocks all new entries. Trader keeps managing exits.

Raise on:

- Any hard limit breach (section 1)
- Ops critical mismatch (position desync, balance desync, orphan order)
- API auth failure repeated 3x in 5 minutes
- Exchange downtime alert
- Latency > 2s on order placement for 3 consecutive ticks

Clear only via CEO weekly retro or explicit CEO override entry.

## 6. Testnet → live promotion criteria

All five must hold across the last 5 trading days on testnet:

- Hit rate ≥ 40%
- Profit factor ≥ 1.3
- Max drawdown ≤ 8%
- Zero unresolved Ops critical mismatches
- Slippage vs expected fills ≤ 5 bps avg

CEO writes the promotion entry. Trader switches API keys via Paperclip secret rotation.

## 7. Per-symbol cooldown

After a stopped-out trade on a symbol, the symbol is locked for 4 hours.

## 8. Correlation clusters (initial seed)

- L1: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, AVAXUSDT
- Meme: DOGEUSDT, SHIBUSDT, PEPEUSDT, WIFUSDT
- DeFi: UNIUSDT, AAVEUSDT, LDOUSDT, CRVUSDT
- AI: FETUSDT, AGIXUSDT, RNDRUSDT, WLDUSDT

Quant proposes cluster updates in the weekly retro. CEO approves.
