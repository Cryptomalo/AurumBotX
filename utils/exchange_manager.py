import logging
import ccxt
from typing import Dict, Optional

class ExchangeManager:
    def __init__(self, exchange_id: str, api_key: str = None, api_secret: str = None, testnet: bool = True):
        self.logger = logging.getLogger(__name__)
        self.exchange_id = exchange_id
        self.testnet = testnet
        
        # Initialize exchange
        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                }
            })
            
            # Configure testnet if enabled
            if testnet and hasattr(self.exchange, 'set_sandbox_mode'):
                self.exchange.set_sandbox_mode(True)
                self.logger.info(f"Initialized {exchange_id} in testnet mode")
            else:
                self.logger.info(f"Initialized {exchange_id} in live mode")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize exchange: {str(e)}")
            raise
            
    async def place_order(self, symbol: str, order_type: str, side: str, amount: float, price: Optional[float] = None) -> Dict:
        """Place an order on the exchange"""
        try:
            if order_type == 'market':
                order = await self.exchange.create_market_order(symbol, side, amount)
            elif order_type == 'limit':
                if price is None:
                    raise ValueError("Price required for limit orders")
                order = await self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
                
            self.logger.info(f"Order placed: {order}")
            return order
            
        except Exception as e:
            error_msg = f"Error placing {order_type} {side} order: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
    async def get_balance(self, currency: str = None) -> Dict:
        """Get account balance"""
        try:
            balance = await self.exchange.fetch_balance()
            if currency:
                return {
                    'free': balance[currency]['free'] if currency in balance else 0,
                    'used': balance[currency]['used'] if currency in balance else 0,
                    'total': balance[currency]['total'] if currency in balance else 0
                }
            return balance
            
        except Exception as e:
            error_msg = f"Error fetching balance: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
    async def get_market_price(self, symbol: str) -> float:
        """Get current market price"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker['last']
            
        except Exception as e:
            error_msg = f"Error fetching price for {symbol}: {str(e)}"
            self.logger.error(error_msg)
            return None
            
    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an existing order"""
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Order {order_id} cancelled")
            return result
            
        except Exception as e:
            error_msg = f"Error cancelling order {order_id}: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def close(self):
        """Close exchange connection"""
        try:
            if hasattr(self.exchange, 'close'):
                self.exchange.close()
                self.logger.info("Exchange connection closed")
        except Exception as e:
            self.logger.error(f"Error closing exchange connection: {str(e)}")
