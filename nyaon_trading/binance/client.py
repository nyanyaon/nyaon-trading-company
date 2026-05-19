from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.parse
from pathlib import Path
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from nyaon_trading.config import Mode
from nyaon_trading.binance.errors import (
    BinanceError,
    RateLimitError,
    TimestampSkewError,
)

_LOG_DIR = Path("state/logs/binance")


def sign_query(query: str, secret: str) -> str:
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()


class BinanceClient:
    def __init__(self, mode: Mode, http: httpx.Client | None = None):
        self.mode = mode
        self.http = http or httpx.Client(base_url=mode.base_url, timeout=10.0)
        self._time_offset_ms: int = 0
        self._offset_ts: float = 0.0

    def _now_ms(self) -> int:
        return int(time.time() * 1000) + self._time_offset_ms

    def _refresh_time(self) -> None:
        r = self.http.get("/fapi/v1/time")
        r.raise_for_status()
        server_ms = int(r.json()["serverTime"])
        self._time_offset_ms = server_ms - int(time.time() * 1000)
        self._offset_ts = time.time()

    def _signed_query(self, params: dict[str, Any]) -> str:
        if time.time() - self._offset_ts > 1800:
            self._refresh_time()
        params = {**params, "timestamp": self._now_ms(), "recvWindow": 5000}
        q = urllib.parse.urlencode(params)
        sig = sign_query(q, self.mode.secret)
        return f"{q}&signature={sig}"

    def _headers(self) -> dict[str, str]:
        return {"X-MBX-APIKEY": self.mode.key}

    def _check(self, r: httpx.Response) -> Any:
        if r.status_code >= 400:
            try:
                body = r.json()
                code = int(body.get("code", -1))
                msg = body.get("msg", r.text)
            except Exception:
                code, msg = -1, r.text
            if code == -1021:
                raise TimestampSkewError(code, msg)
            if code in (-1003, -1015):
                raise RateLimitError(code, msg)
            raise BinanceError(code, msg)
        self._log(r)
        return r.json()

    def _log(self, r: httpx.Response) -> None:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        date = time.strftime("%Y-%m-%d", time.gmtime())
        line = json.dumps(
            {
                "ts": time.time(),
                "method": r.request.method,
                "path": r.request.url.path,
                "status": r.status_code,
                "weight": r.headers.get("X-MBX-USED-WEIGHT-1m"),
                "latency_ms": int(r.elapsed.total_seconds() * 1000),
            }
        )
        with (_LOG_DIR / f"{date}.jsonl").open("a") as f:
            f.write(line + "\n")

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, TimestampSkewError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        reraise=True,
    )
    def get_signed(self, path: str, params: dict[str, Any] | None = None) -> Any:
        q = self._signed_query(params or {})
        r = self.http.get(f"{path}?{q}", headers=self._headers())
        return self._check(r)

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, TimestampSkewError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        reraise=True,
    )
    def post_signed(self, path: str, params: dict[str, Any]) -> Any:
        q = self._signed_query(params)
        r = self.http.post(f"{path}?{q}", headers=self._headers())
        return self._check(r)

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, TimestampSkewError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        reraise=True,
    )
    def delete_signed(self, path: str, params: dict[str, Any]) -> Any:
        q = self._signed_query(params)
        r = self.http.delete(f"{path}?{q}", headers=self._headers())
        return self._check(r)

    def get_public(self, path: str, params: dict[str, Any] | None = None) -> Any:
        r = self.http.get(path, params=params or {})
        return self._check(r)
