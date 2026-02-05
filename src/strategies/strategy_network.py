from dataclasses import dataclass
from typing import Dict, List, Optional, Type

from .challenge_growth_strategy_usdt import ChallengeGrowthStrategyUSDT


@dataclass
class StrategyMetadata:
    name: str
    description: str
    supported_pairs: List[str]


class StrategyNetwork:
    def __init__(self):
        self._registry: Dict[str, Type] = {
            "ChallengeGrowthStrategyUSDT": ChallengeGrowthStrategyUSDT,
        }
        self._metadata: Dict[str, StrategyMetadata] = {
            "ChallengeGrowthStrategyUSDT": StrategyMetadata(
                name="ChallengeGrowthStrategyUSDT",
                description="Momentum-based USDT strategy for growth challenges.",
                supported_pairs=["BTC-USDT", "ETH-USDT"],
            )
        }

    def get_available_strategies(self) -> List[StrategyMetadata]:
        return list(self._metadata.values())

    def get_strategy_by_name(self, name: str, config: Optional[Dict] = None):
        strategy_cls = self._registry.get(name)
        if not strategy_cls:
            raise ValueError(f"Strategy '{name}' is not registered.")
        return strategy_cls(config=config) if config is not None else strategy_cls()
