from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class MemeCoinAlert:
    symbol: str
    price_change_24h: float
    volume_24h: float
    confidence: float
    reason: str
    timestamp: str


class MemeCoinHunter:
    def __init__(
        self,
        price_change_threshold: float = 15.0,
        volume_threshold: float = 1_000_000.0,
    ):
        self.price_change_threshold = price_change_threshold
        self.volume_threshold = volume_threshold
        self.watchlist = ["DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "BONKUSDT"]

    def evaluate_coin(self, symbol: str, market_data: Dict) -> Optional[MemeCoinAlert]:
        price_change = float(market_data.get("price_change_24h", 0))
        volume = float(market_data.get("volume_24h", 0))

        if abs(price_change) < self.price_change_threshold or volume < self.volume_threshold:
            return None

        confidence = min(1.0, abs(price_change) / self.price_change_threshold)
        reason = (
            f"{symbol} moved {price_change:+.2f}% with volume {volume:.0f}, "
            f"exceeding thresholds."
        )

        return MemeCoinAlert(
            symbol=symbol,
            price_change_24h=price_change,
            volume_24h=volume,
            confidence=round(confidence, 2),
            reason=reason,
            timestamp=datetime.utcnow().isoformat(),
        )

    def scan_market(self, market_snapshot: Dict[str, Dict]) -> List[MemeCoinAlert]:
        alerts: List[MemeCoinAlert] = []
        for symbol, data in market_snapshot.items():
            if symbol not in self.watchlist:
                continue
            alert = self.evaluate_coin(symbol, data)
            if alert:
                alerts.append(alert)
        return alerts
