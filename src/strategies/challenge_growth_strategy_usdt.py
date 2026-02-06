# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class TradingPhase(Enum):
    SEED = "seed"
    GROWTH = "growth"
    ACCELERATION = "acceleration"
    PROTECT = "protect"


@dataclass
class TradingSignal:
    symbol: str
    side: str
    confidence: float
    reason: str
    phase: TradingPhase
    timestamp: str


class ChallengeGrowthStrategyUSDT:
    def __init__(self, config: Optional[Dict] = None):
        self.trading_pairs = ["BTC-USDT", "ETH-USDT"]
        self.config = config or {}
        self.phase_thresholds = self.config.get(
            "phase_thresholds",
            {
                TradingPhase.SEED: 0,
                TradingPhase.GROWTH: 150,
                TradingPhase.ACCELERATION: 400,
                TradingPhase.PROTECT: 800,
            },
        )
        self.momentum_threshold = self.config.get("momentum_threshold", 1.2)
        self.volume_threshold = self.config.get("volume_threshold", 150000)
        self.min_confidence = self.config.get("min_confidence", 0.55)
        self.last_signal: Optional[TradingSignal] = None

    def analyze_market_opportunity(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        price_change = float(market_data.get("price_change_24h", 0))
        volume = float(market_data.get("volume_24h", 0))
        confidence = min(1.0, abs(price_change) / self.momentum_threshold)
        if volume >= self.volume_threshold:
            confidence = min(1.0, confidence + 0.1)

        if abs(price_change) < self.momentum_threshold or confidence < self.min_confidence:
            return None

        side = "buy" if price_change > 0 else "sell"
        phase = self._resolve_phase()
        reason = (
            f"Momentum {price_change:+.2f}% with volume {volume:.0f} "
            f"exceeds threshold {self.momentum_threshold:.2f}%"
        )

        signal = TradingSignal(
            symbol=symbol,
            side=side,
            confidence=round(confidence, 2),
            reason=reason,
            phase=phase,
            timestamp=datetime.utcnow().isoformat(),
        )
        self.last_signal = signal
        return signal

    def get_strategy_status(self, current_balance_usdt: float) -> Dict:
        phase = self._resolve_phase(current_balance_usdt)
        return {
            "strategy": "ChallengeGrowthStrategyUSDT",
            "phase": phase.value,
            "trading_pairs": self.trading_pairs,
            "momentum_threshold": self.momentum_threshold,
            "volume_threshold": self.volume_threshold,
            "min_confidence": self.min_confidence,
            "current_balance_usdt": current_balance_usdt,
            "last_signal": self.last_signal.__dict__ if self.last_signal else None,
        }

    def _resolve_phase(self, current_balance_usdt: Optional[float] = None) -> TradingPhase:
        balance = current_balance_usdt if current_balance_usdt is not None else 0
        if balance >= self.phase_thresholds[TradingPhase.PROTECT]:
            return TradingPhase.PROTECT
        if balance >= self.phase_thresholds[TradingPhase.ACCELERATION]:
            return TradingPhase.ACCELERATION
        if balance >= self.phase_thresholds[TradingPhase.GROWTH]:
            return TradingPhase.GROWTH
        return TradingPhase.SEED
