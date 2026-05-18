---
name: exchange-ops
description: Binance USDT-M futures order placement, position management, and reconciliation primitives. Used by Trader (execution) and Ops (reconciliation).
---

# exchange-ops

Shared Binance USDT-M REST helpers. Used by Trader and Ops.

## Endpoints used

| Purpose                 | Endpoint                       | Caller |
| ----------------------- | ------------------------------ | ------ |
| Place order             | `POST /fapi/v1/order`          | Trader |
| Cancel order            | `DELETE /fapi/v1/order`        | Trader |
| Set leverage            | `POST /fapi/v1/leverage`       | Trader |
| Account snapshot        | `GET /fapi/v2/account`         | Ops    |
| Open orders             | `GET /fapi/v1/openOrders`      | Ops    |
| Position risk           | `GET /fapi/v2/positionRisk`    | Ops    |
| Income history          | `GET /fapi/v1/income`          | Ops    |

## Idempotency

Every Trader call must include a deterministic `newClientOrderId`:

```
coid = f"{order_intent_id}-{attempt}"
```

On retry, reuse the same `attempt` counter for the same logical order until ack confirms; then increment for the paired stop/take-profit.

## Order placement sequence

1. Set leverage for symbol (idempotent — only if different from cached).
2. Place market or limit entry with `reduceOnly = false` and `coid`.
3. On fill, place stop-loss `STOP_MARKET` with `closePosition = true` and `coid + "-sl"`.
4. Place take-profit `TAKE_PROFIT_MARKET` with `closePosition = true` and `coid + "-tp"`.

## Reconciliation (Ops)

Snapshot fields:

```json
{
  "ts": "2026-05-18T12:05:00Z",
  "equity": 10000.0,
  "available": 9420.5,
  "positions": [
    { "symbol": "BTCUSDT", "qty": 0.012, "entry": 68312.5, "unrealized": 12.3 }
  ],
  "open_orders": [
    { "coid": "ord_sig_.._-0-sl", "symbol": "BTCUSDT", "type": "STOP_MARKET", "price": 67890.0 }
  ],
  "daily_pnl": 24.5,
  "weekly_pnl": 138.7
}
```

Diff vs prior snapshot. Classify:

- `clean` — no changes outside known order/fill events.
- `benign` — fees, funding, small unrealized drift.
- `critical` — position qty mismatch, orphan reduce-only order, balance delta > 0.5% without a matching trade.

Critical → `state/incidents/<ts>.json` + halt.

## Rate limits

Binance enforces request-weight limits. Cache:

- `exchangeInfo` for 12 hours
- 15m klines for 14 minutes
- 5m klines for 4 minutes
- `account` snapshot per Ops tick (no extra calls)

## Auth

Read API key/secret from env:
- Testnet: `BINANCE_TESTNET_API_KEY`, `BINANCE_TESTNET_API_SECRET`, base URL `https://testnet.binancefuture.com`
- Live: `BINANCE_LIVE_API_KEY`, `BINANCE_LIVE_API_SECRET`, base URL `https://fapi.binance.com`

Mode switch is driven by `state/mode.json` (set by CEO promotion entry).

## Error handling

- 4xx auth → log, count toward auth-failure halt threshold.
- 5xx / timeout → retry with same `coid` (idempotent).
- `-1021` (timestamp) → resync server time, retry once.
- Anything unrecognized → escalate to Ops.
