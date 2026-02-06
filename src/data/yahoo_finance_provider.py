#!/usr/bin/env python3
"""
Yahoo Finance provider for real-time price data.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class YahooFinancePrice:
    price: float
    bid: float
    ask: float
    volume_24h: float
    change_24h: float
    change_24h_percent: float
    timestamp: datetime


class YahooFinanceProvider:
    """Fetches price data from Yahoo Finance public endpoints."""

    BASE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"

    def _normalize_symbol(self, symbol: str) -> str:
        if symbol.endswith("USDT"):
            return f"{symbol[:-4]}-USD"
        return symbol

    def get_real_time_price(self, symbol: str) -> Optional[YahooFinancePrice]:
        """Return best-effort real-time price data or None on failure."""
        normalized = self._normalize_symbol(symbol)

        try:
            response = requests.get(
                self.BASE_URL,
                params={"symbols": normalized},
                timeout=5,
            )
            response.raise_for_status()
            payload = response.json()
            results = payload.get("quoteResponse", {}).get("result", [])
            if not results:
                logger.warning("Yahoo Finance: no data for %s", normalized)
                return None

            data = results[0]
            price = data.get("regularMarketPrice")
            if price is None:
                logger.warning("Yahoo Finance: missing price for %s", normalized)
                return None

            bid = data.get("bid") or price
            ask = data.get("ask") or price
            volume = data.get("regularMarketVolume") or 0.0
            change = data.get("regularMarketChange") or 0.0
            change_percent = data.get("regularMarketChangePercent") or 0.0
            timestamp = datetime.now(timezone.utc)

            return YahooFinancePrice(
                price=float(price),
                bid=float(bid),
                ask=float(ask),
                volume_24h=float(volume),
                change_24h=float(change),
                change_24h_percent=float(change_percent),
                timestamp=timestamp,
            )

        except requests.RequestException as exc:
            logger.warning("Yahoo Finance request failed for %s: %s", normalized, exc)
            return None
