#!/usr/bin/env python3
"""
AurumBotX - Real Exchange API Module
Gestisce connessioni API reali con exchange crypto (MEXC, Bybit, OKX, etc.)
usando libreria CCXT
"""

import ccxt
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class ExchangeAPI:
    """
    Classe per gestire API reali di exchange crypto
    Supporta MEXC, Bybit, OKX, Binance, Gate.io, Kraken via CCXT
    """
    
    def __init__(self, exchange_name: str, api_key: str = None, api_secret: str = None, 
                 testnet: bool = False, demo_mode: bool = True):
        """
        Inizializza connessione exchange
        
        Args:
            exchange_name: Nome exchange ('mexc', 'bybit', 'okx', etc.)
            api_key: API key (opzionale per demo mode)
            api_secret: API secret (opzionale per demo mode)
            testnet: Usa testnet/sandbox se disponibile
            demo_mode: Se True, simula operazioni senza API reali
        """
        self.exchange_name = exchange_name.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.demo_mode = demo_mode
        
        # Setup logging
        self.logger = logging.getLogger(f"ExchangeAPI.{exchange_name}")
        
        # Inizializza exchange
        if not demo_mode:
            self._init_exchange()
        else:
            self.exchange = None
            self.logger.info(f"Demo mode attivo per {exchange_name} - nessuna API reale")
    
    def _init_exchange(self):
        """Inizializza connessione exchange via CCXT"""
        try:
            # Ottieni classe exchange
            exchange_class = getattr(ccxt, self.exchange_name)
            
            # Configurazione
            config = {
                'enableRateLimit': True,  # Rate limiting automatico
                'timeout': 30000,  # 30 secondi timeout
            }
            
            # Aggiungi API keys se fornite
            if self.api_key and self.api_secret:
                config['apiKey'] = self.api_key
                config['secret'] = self.api_secret
            
            # Testnet/Sandbox
            if self.testnet:
                config['options'] = {'defaultType': 'future'}  # Alcuni exchange
                if self.exchange_name == 'bybit':
                    config['options'] = {'testnet': True}
            
            # Crea istanza
            self.exchange = exchange_class(config)
            
            # Verifica connessione
            self.exchange.load_markets()
            
            self.logger.info(f"✅ Connesso a {self.exchange_name}")
            self.logger.info(f"Markets disponibili: {len(self.exchange.markets)}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore connessione {self.exchange_name}: {e}")
            raise
    
    def get_balance(self) -> Dict[str, float]:
        """
        Ottieni saldo account
        
        Returns:
            Dict con saldi per asset (es: {'USDT': 25.0, 'BTC': 0.001})
        """
        if self.demo_mode:
            self.logger.warning("Demo mode: ritorno saldo simulato")
            return {'USDT': 1000.0}
        
        try:
            balance = self.exchange.fetch_balance()
            
            # Estrai solo saldi non zero
            balances = {}
            for currency, amount in balance['total'].items():
                if amount > 0:
                    balances[currency] = amount
            
            return balances
            
        except Exception as e:
            self.logger.error(f"Errore fetch balance: {e}")
            return {}
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Ottieni prezzo corrente e info ticker
        
        Args:
            symbol: Coppia trading (es: 'BTC/USDT')
        
        Returns:
            Dict con bid, ask, last, volume, etc.
        """
        if self.demo_mode:
            # Simula ticker
            import random
            base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
            return {
                'symbol': symbol,
                'bid': base_price * (1 - random.uniform(0.001, 0.003)),
                'ask': base_price * (1 + random.uniform(0.001, 0.003)),
                'last': base_price,
                'volume': random.uniform(1000, 10000),
                'timestamp': int(time.time() * 1000)
            }
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            self.logger.error(f"Errore fetch ticker {symbol}: {e}")
            return None
    
    def create_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """
        Crea ordine market
        
        Args:
            symbol: Coppia trading (es: 'BTC/USDT')
            side: 'buy' o 'sell'
            amount: Quantità da tradare
        
        Returns:
            Dict con info ordine (id, status, filled, etc.)
        """
        if self.demo_mode:
            self.logger.info(f"[DEMO] Market {side} {amount} {symbol}")
            return {
                'id': f"demo_{int(time.time())}",
                'symbol': symbol,
                'type': 'market',
                'side': side,
                'amount': amount,
                'filled': amount,
                'status': 'closed',
                'timestamp': int(time.time() * 1000)
            }
        
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            self.logger.info(f"✅ Ordine creato: {side} {amount} {symbol} - ID: {order['id']}")
            return order
        except Exception as e:
            self.logger.error(f"❌ Errore creazione ordine: {e}")
            return None
    
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """
        Crea ordine limit
        
        Args:
            symbol: Coppia trading
            side: 'buy' o 'sell'
            amount: Quantità
            price: Prezzo limite
        
        Returns:
            Dict con info ordine
        """
        if self.demo_mode:
            self.logger.info(f"[DEMO] Limit {side} {amount} {symbol} @ {price}")
            return {
                'id': f"demo_{int(time.time())}",
                'symbol': symbol,
                'type': 'limit',
                'side': side,
                'amount': amount,
                'price': price,
                'filled': 0,
                'status': 'open',
                'timestamp': int(time.time() * 1000)
            }
        
        try:
            order = self.exchange.create_limit_order(symbol, side, amount, price)
            self.logger.info(f"✅ Limit order: {side} {amount} {symbol} @ {price}")
            return order
        except Exception as e:
            self.logger.error(f"❌ Errore limit order: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancella ordine
        
        Args:
            order_id: ID ordine da cancellare
            symbol: Coppia trading
        
        Returns:
            True se successo
        """
        if self.demo_mode:
            self.logger.info(f"[DEMO] Cancel order {order_id}")
            return True
        
        try:
            self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"✅ Ordine {order_id} cancellato")
            return True
        except Exception as e:
            self.logger.error(f"❌ Errore cancellazione ordine: {e}")
            return False
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """
        Ottieni ordini aperti
        
        Args:
            symbol: Coppia specifica (None = tutti)
        
        Returns:
            Lista ordini aperti
        """
        if self.demo_mode:
            return []
        
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            self.logger.error(f"Errore fetch open orders: {e}")
            return []
    
    def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """
        Verifica stato ordine
        
        Args:
            order_id: ID ordine
            symbol: Coppia trading
        
        Returns:
            Dict con stato ordine
        """
        if self.demo_mode:
            return {'id': order_id, 'status': 'closed', 'filled': 100}
        
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            self.logger.error(f"Errore fetch order status: {e}")
            return None
    
    def get_trading_fees(self, symbol: str = None) -> Dict:
        """
        Ottieni fee trading
        
        Args:
            symbol: Coppia specifica (None = default)
        
        Returns:
            Dict con maker/taker fees
        """
        if self.demo_mode:
            # Fee simulate per MEXC
            return {'maker': 0.0005, 'taker': 0.0005}  # 0.05%
        
        try:
            if symbol:
                market = self.exchange.market(symbol)
                return {
                    'maker': market.get('maker', 0.001),
                    'taker': market.get('taker', 0.001)
                }
            else:
                # Fee default
                return {
                    'maker': self.exchange.fees.get('trading', {}).get('maker', 0.001),
                    'taker': self.exchange.fees.get('trading', {}).get('taker', 0.001)
                }
        except Exception as e:
            self.logger.error(f"Errore fetch fees: {e}")
            return {'maker': 0.001, 'taker': 0.001}
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[List]:
        """
        Ottieni dati candlestick (OHLCV)
        
        Args:
            symbol: Coppia trading
            timeframe: Timeframe ('1m', '5m', '1h', '1d', etc.)
            limit: Numero candele
        
        Returns:
            Lista [timestamp, open, high, low, close, volume]
        """
        if self.demo_mode:
            self.logger.warning("Demo mode: OHLCV non disponibile")
            return []
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            self.logger.error(f"Errore fetch OHLCV: {e}")
            return []
    
    def get_markets(self) -> List[str]:
        """
        Ottieni lista mercati disponibili
        
        Returns:
            Lista simboli (es: ['BTC/USDT', 'ETH/USDT', ...])
        """
        if self.demo_mode:
            return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'XRP/USDT']
        
        try:
            markets = list(self.exchange.markets.keys())
            return markets
        except Exception as e:
            self.logger.error(f"Errore fetch markets: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Testa connessione exchange
        
        Returns:
            True se connessione OK
        """
        if self.demo_mode:
            self.logger.info("Demo mode: connessione simulata OK")
            return True
        
        try:
            # Test con fetch time
            server_time = self.exchange.fetch_time()
            local_time = int(time.time() * 1000)
            diff = abs(server_time - local_time)
            
            self.logger.info(f"✅ Connessione OK - Time diff: {diff}ms")
            
            if diff > 5000:
                self.logger.warning(f"⚠️ Time diff elevato: {diff}ms - possibili problemi")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test connessione fallito: {e}")
            return False


# Factory function per creare istanza exchange
def create_exchange(exchange_name: str, api_key: str = None, api_secret: str = None, 
                   testnet: bool = False, demo_mode: bool = True) -> ExchangeAPI:
    """
    Factory per creare istanza ExchangeAPI
    
    Args:
        exchange_name: Nome exchange ('mexc', 'bybit', 'okx', etc.)
        api_key: API key
        api_secret: API secret
        testnet: Usa testnet
        demo_mode: Modalità demo (senza API reali)
    
    Returns:
        Istanza ExchangeAPI configurata
    """
    return ExchangeAPI(exchange_name, api_key, api_secret, testnet, demo_mode)


# Test rapido
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("TEST EXCHANGE API MODULE")
    print("=" * 80)
    print()
    
    # Test MEXC in demo mode
    print("1. Test MEXC (demo mode)")
    mexc = create_exchange('mexc', demo_mode=True)
    
    # Test metodi
    print(f"   Balance: {mexc.get_balance()}")
    print(f"   BTC/USDT ticker: {mexc.get_ticker('BTC/USDT')}")
    print(f"   Trading fees: {mexc.get_trading_fees()}")
    print(f"   Markets: {len(mexc.get_markets())} disponibili")
    print(f"   Connection test: {mexc.test_connection()}")
    
    # Test ordine simulato
    order = mexc.create_market_order('BTC/USDT', 'buy', 0.001)
    print(f"   Test order: {order['id']} - Status: {order['status']}")
    
    print()
    print("=" * 80)
    print("✅ Test completato con successo!")
    print("=" * 80)

