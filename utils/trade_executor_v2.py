#!/usr/bin/env python3
"""
Trade Executor V2 con retry logic e validazione completa.
"""
import asyncio
import logging
from typing import Dict, Optional


class RobustTradeExecutor:
    def __init__(self, exchange_manager):
        self.exchange = exchange_manager
        self.logger = logging.getLogger('TradeExecutor')
        self.max_retries = 3
        self.retry_delay = 2

    async def execute_trade(self, signal: Dict) -> Optional[Dict]:
        """Esegue trade con retry automatico."""
        if not self._validate_signal(signal):
            self.logger.warning(f"Segnale non valido: {signal}")
            return None

        if not self._check_risk_limits(signal):
            self.logger.warning("Limiti di rischio superati")
            return None

        for attempt in range(self.max_retries):
            try:
                order = await self._place_order(signal)
                if order and order.get('status') in {'FILLED', 'filled'}:
                    self.logger.info(f"✅ Trade eseguito: {order.get('id')}")
                    return order
            except Exception as e:
                self.logger.error(f"Tentativo {attempt + 1} fallito: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        return None

    def _validate_signal(self, signal: Dict) -> bool:
        required_keys = ['action', 'symbol', 'confidence']
        if not all(key in signal for key in required_keys):
            return False
        if signal['action'] not in ['buy', 'sell']:
            return False
        if not (0 <= signal['confidence'] <= 1):
            return False
        return True

    def _check_risk_limits(self, signal: Dict) -> bool:
        min_confidence = 0.65
        return signal['confidence'] >= min_confidence

    async def _place_order(self, signal: Dict) -> Optional[Dict]:
        try:
            if signal['action'] == 'buy':
                return await self.exchange.create_market_buy_order(
                    symbol=signal['symbol'],
                    amount=signal.get('amount', 0.0001)
                )
            return await self.exchange.create_market_sell_order(
                symbol=signal['symbol'],
                amount=signal.get('amount', 0.0001)
            )
        except Exception as e:
            self.logger.error(f"Errore piazzamento ordine: {e}")
            raise
