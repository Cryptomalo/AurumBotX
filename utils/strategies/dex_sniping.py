from web3 import Web3
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from utils.strategies.base_strategy import BaseStrategy
from cachetools import TTLCache
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

class DexSnipingStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("DEX Sniping", config)
        self.w3 = Web3(Web3.HTTPProvider(config['rpc_url']))
        # Parametri ottimizzati
        self.min_liquidity = config.get('min_liquidity', 2)  # Ridotto da 5 a 2 ETH
        self.max_buy_tax = config.get('max_buy_tax', 8)     # Ridotto da 10 a 8%
        self.min_holders = config.get('min_holders', 30)    # Ridotto da 50 a 30
        self.dex_url = "https://api.dexscreener.com/latest/dex"
        self.testnet = config.get('testnet', True)

        # Cache ottimizzata con TTL più brevi
        self._contract_cache = TTLCache(maxsize=500, ttl=1800)  # 30 min (ridotto da 1h)
        self._holder_cache = TTLCache(maxsize=500, ttl=180)    # 3 min (ridotto da 5m)
        self._tax_cache = TTLCache(maxsize=500, ttl=180)       # 3 min (ridotto da 5m)

        # Configurazione batch migliorata
        self.batch_size = config.get('batch_size', 25)         # Ridotto da 50 a 25
        self.batch_interval = config.get('batch_interval', 5)   # Ridotto da 10s a 5s
        self._batch_queue = []
        self._last_batch_time = datetime.now()

        # Rate limiting
        self._request_timestamps = []
        self.max_requests_per_minute = 30
        self.request_window = 60  # secondi

    @lru_cache(maxsize=100)
    def _get_contract_abi(self, address: str) -> Dict:
        """Cache ABI per contratti frequentemente utilizzati"""
        try:
            # Implementare logica ABI caching
            return {}
        except Exception as e:
            logger.error(f"ABI retrieval error: {e}")
            return {}

    async def analyze_market(
        self,
        market_data: pd.DataFrame,
        sentiment_data: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Analyzes DEX market with improved efficiency"""
        try:
            if not self._can_make_request():
                logger.warning("Rate limit reached, skipping market analysis")
                return []

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

    def _can_make_request(self) -> bool:
        """Check rate limiting with sliding window"""
        current_time = time.time()
        self._request_timestamps = [
            ts for ts in self._request_timestamps 
            if current_time - ts <= self.request_window
        ]

        if len(self._request_timestamps) >= self.max_requests_per_minute:
            return False

        self._request_timestamps.append(current_time)
        return True

    async def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> bool:
        """Validates trading signal with enhanced risk management"""
        try:
            # Input validation
            if not all(k in signal for k in ['action', 'confidence', 'pair_address']):
                return False

            # Portfolio checks
            min_trade_amount = self.config.get('min_trade_amount', 0.05)  # Ridotto da 0.1
            if portfolio.get('balance', 0) < min_trade_amount:
                logger.info(f"Insufficient balance for minimum trade: {min_trade_amount}")
                return False

            # Risk management
            max_position_size = portfolio.get('balance') * self.config.get('max_position_size', 0.05)
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

            # Add to batch queue
            self._batch_queue.append(signal)
            current_time = datetime.now()

            # Process batch if conditions met
            if (len(self._batch_queue) >= self.batch_size or 
                (current_time - self._last_batch_time).total_seconds() >= self.batch_interval):
                return await self._process_batch()

            return {
                'success': True,
                'pending': True,
                'batch_size': len(self._batch_queue)
            }

        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {'success': False, 'error': str(e)}

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

    async def _process_batch(self) -> Dict[str, Any]:
        """Process batched trades efficiently"""
        if not self._batch_queue:
            return {'success': True, 'message': 'No trades to process'}

        try:
            batch = self._batch_queue
            self._batch_queue = []
            self._last_batch_time = datetime.now()

            # Execute batch transaction
            tx_hash = await self._send_batch_transaction(batch)

            return {
                'success': bool(tx_hash),
                'tx_hash': tx_hash,
                'batch_size': len(batch),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return {'success': False, 'error': str(e)}


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

            # Skip tax check in testnet
            if not self.testnet:
                tax_info = self._tax_cache.get(pair['token'])
                if tax_info is None:
                    tax_info = await self._get_tax_info(pair['token'])
                    self._tax_cache[pair['token']] = tax_info

                if tax_info.get('buy_tax', 100) > self.max_buy_tax:
                    return False

            # Check holders with caching
            holders = self._holder_cache.get(pair['token'])
            if holders is None:
                holders = await self._get_holder_count(pair['token'])
                self._holder_cache[pair['token']] = holders

            if holders < self.min_holders:
                return False

            return True

        except Exception as e:
            logger.error(f"Pair validation error: {e}")
            return False

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
                    return await self._filter_opportunities(data['pairs'])

        except Exception as e:
            logger.error(f"Pair scanning error: {e}")
            return []

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

    async def _validate_contract(self, address: str) -> bool:
        """Validates contract safety with rate limiting"""
        try:
            if self.testnet:
                return True

            # Rate limiting check
            if not self._can_make_request():
                return False

            code = await asyncio.to_thread(self.w3.eth.get_code, address)
            if not code or len(code) < 2:
                return False

            # Optimized contract validations
            results = await asyncio.gather(
                self._is_honeypot(address),
                self._has_dangerous_permissions(address)
            )
            return not any(results)

        except Exception as e:
            logger.error(f"Contract validation error: {e}")
            return False

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

    async def _is_honeypot(self, address: str) -> bool:
        """Verifica se il contratto è un honeypot"""
        try:
            # Implementa la logica per il rilevamento honeypot
            return False
        except Exception as e:
            logger.error(f"Honeypot check error: {e}")
            return True

    async def _has_dangerous_permissions(self, address: str) -> bool:
        """Verifica permessi pericolosi nel contratto"""
        try:
            # Implementa la verifica dei permessi
            return False
        except Exception as e:
            logger.error(f"Permissions check error: {e}")
            return True

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

    async def _get_tax_info(self, address: str) -> Dict[str, float]:
        """Ottiene le informazioni sulle tasse del token"""
        try:
            if self.testnet:
                return {'buy_tax': 5.0, 'sell_tax': 5.0}
            # Implementa la logica per ottenere le informazioni sulle tasse
            return {'buy_tax': 5.0, 'sell_tax': 5.0}
        except Exception as e:
            logger.error(f"Tax info error: {e}")
            return {'buy_tax': 100.0, 'sell_tax': 100.0}

    async def _send_batch_transaction(self, batch: List[Dict]) -> Optional[str]:
        """Sends optimized batch transaction"""
        try:
            # Implement actual batch transaction logic here
            return "0x..." # Placeholder
        except Exception as e:
            logger.error(f"Batch transaction error: {e}")
            return None

    async def _send_transaction(self, signal: Dict) -> Optional[str]:
        """Invia transazione alla blockchain"""
        try:
            # Placeholder for actual transaction logic
            return "0x..."
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            return None