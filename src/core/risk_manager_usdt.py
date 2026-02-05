from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Dict, List, Optional


class RiskLevel(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class RiskProfile:
    risk_level: RiskLevel
    max_trade_pct: float
    max_daily_loss_pct: float
    max_open_positions: int
    min_trade_usdt: float


class RiskManagerUSDT:
    def __init__(self, risk_level: RiskLevel = RiskLevel.CONSERVATIVE):
        self.profile = self._build_profile(risk_level)
        self._daily_metrics: Dict[int, Dict] = {}

    def validate_trade(
        self,
        symbol: str,
        side: str,
        amount_usdt: float,
        current_balance_usdt: float,
        user_id: int,
    ) -> Dict:
        errors: List[str] = []
        metrics = self._get_daily_metrics(user_id)

        if amount_usdt <= 0:
            errors.append("Trade amount must be greater than zero.")

        if side not in {"buy", "sell"}:
            errors.append("Trade side must be 'buy' or 'sell'.")

        max_trade = current_balance_usdt * self.profile.max_trade_pct
        if amount_usdt > max_trade:
            errors.append(
                f"Trade amount exceeds max allowed size ({max_trade:.2f} USDT)."
            )

        if amount_usdt < self.profile.min_trade_usdt:
            errors.append(
                f"Trade amount below minimum trade size ({self.profile.min_trade_usdt:.2f} USDT)."
            )

        if metrics["daily_loss_usdt"] >= current_balance_usdt * self.profile.max_daily_loss_pct:
            errors.append("Daily loss limit reached.")

        risk_score = self._calculate_risk_score(metrics, current_balance_usdt)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "risk_score": risk_score,
            "risk_level": self.profile.risk_level.value,
        }

    def calculate_optimal_position_size(
        self,
        symbol: str,
        balance_usdt: float,
        confidence: float,
        volatility: float,
    ) -> Dict:
        max_trade = balance_usdt * self.profile.max_trade_pct
        confidence_factor = max(0.2, min(confidence, 1.0))
        volatility_penalty = 1 - min(volatility, 0.05) / 0.05
        position_size = max_trade * confidence_factor * max(volatility_penalty, 0.2)
        trade_viable = position_size >= self.profile.min_trade_usdt

        estimated_risk = position_size * self.profile.max_daily_loss_pct
        return {
            "trade_viable": trade_viable,
            "recommended_size_usdt": round(position_size, 2),
            "estimated_risk_usdt": round(estimated_risk, 2),
            "confidence_used": round(confidence_factor, 2),
            "volatility_penalty": round(volatility_penalty, 2),
            "symbol": symbol,
        }

    def get_risk_summary(self, user_id: int) -> Dict:
        metrics = self._get_daily_metrics(user_id)
        return {
            "user_id": user_id,
            "risk_level": self.profile.risk_level.value,
            "daily_summary": metrics,
            "emergency_stop_active": metrics["daily_loss_usdt"] > 0,
            "circuit_breaker_active": metrics["daily_loss_usdt"]
            >= metrics["starting_balance_usdt"] * self.profile.max_daily_loss_pct,
            "alerts_count": len(metrics["alerts"]),
        }

    def record_trade_result(
        self, user_id: int, pnl_usdt: float, starting_balance_usdt: Optional[float] = None
    ) -> None:
        metrics = self._get_daily_metrics(user_id)
        metrics["trades"] += 1
        if pnl_usdt < 0:
            metrics["daily_loss_usdt"] += abs(pnl_usdt)
            metrics["alerts"].append(f"Loss recorded: {abs(pnl_usdt):.2f} USDT")
        else:
            metrics["daily_profit_usdt"] += pnl_usdt
        if starting_balance_usdt is not None:
            metrics["starting_balance_usdt"] = starting_balance_usdt

    def _build_profile(self, risk_level: RiskLevel) -> RiskProfile:
        profiles = {
            RiskLevel.CONSERVATIVE: RiskProfile(
                risk_level=RiskLevel.CONSERVATIVE,
                max_trade_pct=0.05,
                max_daily_loss_pct=0.05,
                max_open_positions=1,
                min_trade_usdt=5,
            ),
            RiskLevel.MODERATE: RiskProfile(
                risk_level=RiskLevel.MODERATE,
                max_trade_pct=0.1,
                max_daily_loss_pct=0.08,
                max_open_positions=2,
                min_trade_usdt=5,
            ),
            RiskLevel.AGGRESSIVE: RiskProfile(
                risk_level=RiskLevel.AGGRESSIVE,
                max_trade_pct=0.15,
                max_daily_loss_pct=0.12,
                max_open_positions=3,
                min_trade_usdt=5,
            ),
        }
        return profiles[risk_level]

    def _get_daily_metrics(self, user_id: int) -> Dict:
        metrics = self._daily_metrics.get(user_id)
        today = date.today().isoformat()
        if not metrics or metrics["date"] != today:
            metrics = {
                "date": today,
                "trades": 0,
                "daily_loss_usdt": 0.0,
                "daily_profit_usdt": 0.0,
                "starting_balance_usdt": 0.0,
                "alerts": [],
                "risk_score": 0.0,
            }
            self._daily_metrics[user_id] = metrics
        metrics["risk_score"] = self._calculate_risk_score(metrics, metrics["starting_balance_usdt"])
        return metrics

    def _calculate_risk_score(self, metrics: Dict, starting_balance_usdt: float) -> float:
        if starting_balance_usdt <= 0:
            return 0.0
        loss_ratio = metrics["daily_loss_usdt"] / (starting_balance_usdt or 1)
        return round(min(loss_ratio / self.profile.max_daily_loss_pct, 1.0), 2)
