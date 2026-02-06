#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
Trade Executor Fixed - orchestrazione di esecuzione con risk manager.
"""
import logging
from typing import Dict, Optional

from utils.risk_manager_v2 import RiskManagerV2

logger = logging.getLogger(__name__)


class TradeExecutorFixed:
    def __init__(self, exchange_manager, risk_manager: Optional[RiskManagerV2] = None):
        self.exchange = exchange_manager
        self.risk_manager = risk_manager or RiskManagerV2()

    async def execute(self, signal: Dict) -> Optional[Dict]:
        validation = self.risk_manager.validate(signal)
        if not validation["valid"]:
            logger.warning(f"Trade blocked: {validation['errors']}")
            return None

        action = signal.get("action")
        symbol = signal.get("symbol")
        amount = signal.get("amount", 0.0001)

        if action == "buy":
            return await self.exchange.create_market_buy_order(symbol=symbol, amount=amount)
        if action == "sell":
            return await self.exchange.create_market_sell_order(symbol=symbol, amount=amount)
        logger.error("Invalid action in signal")
        return None
