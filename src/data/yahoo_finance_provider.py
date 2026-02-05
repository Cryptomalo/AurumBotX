from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Optional

import requests


@dataclass
class YahooMarketData:
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    change_24h: float
    change_24h_percent: float
    timestamp: datetime


class YahooFinanceProvider:
    def __init__(self, timeout: int = 8):
        self.timeout = timeout
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def get_real_time_price(self, symbol: str) -> Optional[YahooMarketData]:
        query_symbol = self._normalize_symbol(symbol)
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={query_symbol}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            result = payload.get("quoteResponse", {}).get("result", [])
            if not result:
                return None

            quote = result[0]
            price = quote.get("regularMarketPrice")
            if price is None:
                return None

            bid = quote.get("bid", price) or price
            ask = quote.get("ask", price) or price
            volume = quote.get("regularMarketVolume", 0) or 0
            change = quote.get("regularMarketChange", 0) or 0
            change_percent = quote.get("regularMarketChangePercent", 0) or 0
            market_time = quote.get("regularMarketTime")
            timestamp = datetime.fromtimestamp(
                market_time, tz=timezone.utc
            ) if market_time else datetime.now(tz=timezone.utc)

            return YahooMarketData(
                symbol=symbol,
                price=float(price),
                bid=float(bid),
                ask=float(ask),
                volume_24h=float(volume),
                change_24h=float(change),
                change_24h_percent=float(change_percent),
                timestamp=timestamp,
            )
        except requests.RequestException as exc:
            self.logger.warning(f"Yahoo Finance request failed for {symbol}: {exc}")
            return None
        except (ValueError, TypeError) as exc:
            self.logger.warning(f"Yahoo Finance response parse failed for {symbol}: {exc}")
            return None

    def _normalize_symbol(self, symbol: str) -> str:
        if symbol.endswith("-USDT"):
            return symbol.replace("-USDT", "-USD")
        if symbol.endswith("USDT"):
            return symbol.replace("USDT", "USD")
        return symbol
