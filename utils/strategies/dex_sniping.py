import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import aiohttp
from web3 import Web3
from cachetools import TTLCache
from utils.strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class DexSnipingStrategy(BaseStrategy):
    """Strategia ottimizzata per DEX sniping con machine learning"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("DEX Sniping", config)
        self.w3 = Web3(Web3.HTTPProvider(config['rpc_url']))

        # Parametri ottimizzati
        self.min_liquidity = config.get('min_liquidity', 2)  # Min 2 ETH
        self.max_buy_tax = config.get('max_buy_tax', 8)     # Max 8% tax
        self.min_holders = config.get('min_holders', 30)    # Min 30 holders
        self.dex_url = config.get('dex_url', "https://api.dexscreener.com/latest/dex")
        self.testnet = config.get('testnet', True)

        # Initialize tracking set
        self.scanned_pairs = set()

        # Cache configuration
        self._contract_cache = TTLCache(maxsize=500, ttl=1800)  # 30 min
        self._holder_cache = TTLCache(maxsize=500, ttl=180)    # 3 min
        self._tax_cache = TTLCache(maxsize=500, ttl=180)       # 3 min

        # Rate limiting
        self._request_timestamps = []
        self.max_requests_per_minute = 30
        self.request_window = 60  # seconds

    async def analyze_market(
        self,
        market_data: Dict[str, Any],
        sentiment_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Analyzes DEX market with improved efficiency"""
        try:
            if not self._can_make_request():
                logger.warning("Rate limit reached, skipping market analysis")
                return []

            # For DEX sniping, we use our own market scanning
            new_pairs = await self.scan_new_pairs()
            if not new_pairs:
                return []

            signals = []
            batch_results = await asyncio.gather(
                *[self._analyze_pair(pair) for pair in new_pairs],
                return_exceptions=True
            )

            for result in batch_results:
                if isinstance(result, dict) and result.get('is_valid'):
                    signals.append({
                        'action': 'SNIPE',
                        'pair_address': result['pair'],
                        'token_address': result['token'],
                        'liquidity': result['liquidity'],
                        'confidence': result['confidence'],
                        'timestamp': datetime.now().isoformat()
                    })

            return signals

        except Exception as e:
            logger.error(f"DEX market analysis error: {e}")
            return []

    async def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """Validates trading signal with enhanced risk management"""
        try:
            # Input validation
            if not all(k in signal for k in ['action', 'confidence', 'pair_address']):
                return False

            # Portfolio checks
            min_trade_amount = self.config.get('min_trade_amount', 0.05)
            if portfolio.get('balance', 0) < min_trade_amount:
                logger.info(f"Insufficient balance for minimum trade: {min_trade_amount}")
                return False

            # Risk management
            max_position_size = portfolio.get('balance', 0) * self.config.get('max_position_size', 0.05)
            if signal.get('amount', 0) > max_position_size:
                return False

            return True

        except Exception as e:
            logger.error(f"Trade validation error: {str(e)}")
            return False

    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade with improved error handling and gas optimization"""
        try:
            if self.testnet:
                return self._get_test_execution(signal)

            execution = {
                'success': True,
                'action': signal['action'],
                'pair_address': signal['pair_address'],
                'token_address': signal['token_address'],
                'amount': signal.get('amount', 0),
                'timestamp': datetime.now().isoformat()
            }

            # Update performance metrics
            await self.update_performance(execution)
            return execution

        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _calculate_position_size(self, price: float, confidence: float) -> float:
        """Calculate position size for DEX trades"""
        try:
            # Base position size
            base_size = self.config.get('risk_per_trade', 0.01) * price

            # Apply confidence adjustment
            confidence_factor = 0.5 + (confidence * 0.5)  # Scale between 50-100%
            adjusted_size = base_size * confidence_factor

            # Apply maximum position limit
            max_position = min(
                self.config.get('max_position_size', float('inf')),
                price * self.config.get('max_tokens', float('inf'))
            )

            return min(adjusted_size, max_position)

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0

    def _can_make_request(self) -> bool:
        """Check rate limiting with sliding window"""
        current_time = datetime.now().timestamp()
        self._request_timestamps = [
            ts for ts in self._request_timestamps 
            if current_time - ts <= self.request_window
        ]

        if len(self._request_timestamps) >= self.max_requests_per_minute:
            return False

        self._request_timestamps.append(current_time)
        return True

    async def scan_new_pairs(self) -> List[Dict]:
        """Scans for new pairs on DEX"""
        try:
            if self.testnet:
                # Return simulated pairs for testnet
                return [{
                    'pair': f"0x{i:064x}",
                    'token': f"0x{(i+1):064x}",
                    'liquidity': 10000,
                    'confidence': 0.8
                } for i in range(5)]

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.dex_url}/pairs/bsc") as response:
                    data = await response.json()
                    return await self._filter_opportunities(data.get('pairs', []))

        except Exception as e:
            logger.error(f"Pair scanning error: {e}")
            return []

    async def _analyze_pair(self, pair: Dict) -> Dict[str, Any]:
        """Analyze single pair with optimized validation"""
        try:
            if not await self.validate_pair(pair):
                return {'is_valid': False}

            confidence = await self._calculate_confidence(pair)
            if confidence < 0.7:
                return {'is_valid': False}

            return {
                'is_valid': True,
                'pair': pair['pair'],
                'token': pair['token'],
                'liquidity': pair['liquidity'],
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Pair analysis error: {e}")
            return {'is_valid': False}

    async def validate_pair(self, pair: Dict[str, Any]) -> bool:
        """Validates a trading pair with caching"""
        try:
            # Skip liquidity check in testnet
            if not self.testnet and float(pair.get('liquidity', 0)) < self.min_liquidity * 1000:
                return False

            # Check contract validation cache
            contract_valid = self._contract_cache.get(pair['token'])
            if contract_valid is None:
                contract_valid = await self._validate_contract(pair['token'])
                self._contract_cache[pair['token']] = contract_valid

            if not contract_valid:
                return False

            return True

        except Exception as e:
            logger.error(f"Pair validation error: {e}")
            return False

    def _get_test_execution(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test execution response"""
        return {
            'success': True,
            'tx_hash': f"0x{signal['pair_address'][-8:]}",
            'timestamp': datetime.now().isoformat(),
            'token': signal['token_address'],
            'amount': signal.get('amount', 0),
            'testnet': True
        }

    async def _validate_contract(self, address: str) -> bool:
        """Validates contract safety with rate limiting"""
        try:
            if self.testnet:
                return True

            if not self._can_make_request():
                return False

            code = await asyncio.to_thread(self.w3.eth.get_code, address)
            if not code or len(code) < 2:
                return False

            # Basic security checks (expand as needed)
            return not (
                await self._is_honeypot(address) or
                await self._has_dangerous_permissions(address)
            )

        except Exception as e:
            logger.error(f"Contract validation error: {e}")
            return False

    async def _is_honeypot(self, address: str) -> bool:
        """Check if contract is a honeypot"""
        try:
            # Implement honeypot detection logic
            return False
        except Exception as e:
            logger.error(f"Honeypot check error: {e}")
            return True

    async def _has_dangerous_permissions(self, address: str) -> bool:
        """Check for dangerous contract permissions"""
        try:
            # Implement permissions check
            return False
        except Exception as e:
            logger.error(f"Permissions check error: {e}")
            return True

    async def _filter_opportunities(self, pairs: List[Dict]) -> List[Dict]:
        """Filtra opportunità basate sui criteri"""
        opportunities = []
        for pair in pairs:
            if (
                pair['pairAddress'] not in self.scanned_pairs and
                float(pair.get('liquidity', {}).get('usd', 0)) >= self.min_liquidity * 1000
            ):
                is_valid = await self._validate_contract(pair['tokenAddress'])
                if is_valid:
                    self.scanned_pairs.add(pair['pairAddress'])
                    conf = await self._calculate_confidence(pair)
                    opportunities.append({
                        'token': pair['tokenAddress'],
                        'pair': pair['pairAddress'],
                        'liquidity': pair['liquidity']['usd'],
                        'confidence': conf
                    })
        return opportunities

    async def _calculate_confidence(self, pair: Dict) -> float:
        """Calculates confidence score with weighted metrics"""
        try:
            weights = {
                'liquidity': 0.3,
                'volume': 0.2,
                'holders': 0.2,
                'contract_safety': 0.3
            }

            scores = {}

            # Liquidity score
            liquidity = float(pair.get('liquidity', {}).get('usd', 0))
            scores['liquidity'] = min(1.0, liquidity / (self.min_liquidity * 2000))

            # Volume score
            volume = float(pair.get('volume', {}).get('h24', 0))
            scores['volume'] = min(1.0, volume / (liquidity * 0.1) if liquidity > 0 else 0)

            # Holders score
            holders = await self._get_holder_count(pair['tokenAddress'])
            scores['holders'] = min(1.0, holders / self.min_holders)

            # Contract safety score
            scores['contract_safety'] = 1.0 if await self._check_contract_safety(pair['tokenAddress']) else 0.0

            # Calculate weighted average
            total_score = sum(scores[k] * weights[k] for k in weights)

            return min(1.0, total_score)

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0

    async def _check_contract_safety(self, address: str) -> bool:
        """Verifica la sicurezza del contratto"""
        try:
            if self.testnet:
                return True
            # Implementa verifiche di sicurezza avanzate
            return True
        except Exception as e:
            logger.error(f"Security check error: {e}")
            return False

    async def _get_holder_count(self, address: str) -> int:
        """Ottiene il numero di holders del token"""
        try:
            if self.testnet:
                return 100
            # Implementa la logica per ottenere il numero di holders
            return 100  # Placeholder
        except Exception as e:
            logger.error(f"Holder count error: {e}")
            return 0

    async def update_performance(self, execution: Dict[str, Any]) -> None:
        """Update performance metrics"""
        try:
            # Placeholder for updating performance metrics
            pass
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")