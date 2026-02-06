#!/usr/bin/env python3
"""
Strategy registry and discovery for AurumBotX.
"""

from typing import Dict, List, Type

from .challenge_growth_strategy_usdt import ChallengeGrowthStrategyUSDT


class StrategyNetwork:
    """Simple registry for available strategies."""

    def __init__(self) -> None:
        self._strategies: Dict[str, Type] = {
            "challenge_growth_usdt": ChallengeGrowthStrategyUSDT,
        }

    def get_available_strategies(self) -> List[str]:
        """Return list of registered strategy keys."""
        return list(self._strategies.keys())

    def get_strategy(self, name: str):
        """Return strategy class by name."""
        return self._strategies.get(name)
