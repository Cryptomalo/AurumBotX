#!/usr/bin/env python3
"""
AurumBotX Hyperliquid Adapter
Integrazione completa con Hyperliquid DEX per perpetual futures trading
"""

import os
import json
import logging
import requests
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import base64

logger = logging.getLogger(__name__)

class OrderSide(Enum):
    """Lati dell'ordine"""
    BUY = "Buy"
    SELL = "Sell"

class OrderType(Enum):
    """Tipi di ordine"""
    MARKET = "Market"
    LIMIT = "Limit"

@dataclass
class HyperliquidPosition:
    """Struttura per una posizione su Hyperliquid"""
    symbol: str
    side: str  # "Long" o "Short"
    size: float
    entry_price: float
    leverage: float
    liquidation_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    timestamp: datetime

@dataclass
class HyperliquidOrder:
    """Struttura per un ordine su Hyperliquid"""
    order_id: str
    symbol: str
    side: str
    order_type: str
    size: float
    price: float
    status: str
    filled: float
    timestamp: datetime

@dataclass
class HyperliquidTrade:
    """Struttura per un trade eseguito su Hyperliquid"""
    trade_id: str
    symbol: str
    side: str
    size: float
    price: float
    pnl: float
    pnl_percent: float
    timestamp: datetime
    leverage: float

class HyperliquidAdapter:
    """Adapter per l'integrazione con Hyperliquid DEX"""
    
    # Hyperliquid API endpoints
    BASE_URL = "https://api.hyperliquid.xyz"
    TESTNET_URL = "https://testnet.hyperliquid.xyz"
    
    # Supported perpetual futures pairs
    SUPPORTED_PAIRS = [
        "BTC", "ETH", "SOL", "BNB", "DOGE", "XRP", "ADA", "AVAX", "ARB", "OP"
    ]
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = True):
        """
        Inizializza l'adapter Hyperliquid
        
        Args:
            api_key: Chiave API di Hyperliquid
            secret_key: Chiave segreta di Hyperliquid
            testnet: Usa testnet se True, mainnet se False
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.base_url = self.TESTNET_URL if testnet else self.BASE_URL
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "AurumBotX/1.0"
        })
        
        self.positions: Dict[str, HyperliquidPosition] = {}
        self.orders: Dict[str, HyperliquidOrder] = {}
        self.account_value = 0.0
        self.available_balance = 0.0
        
        logger.info(f"HyperliquidAdapter inizializzato - Mode: {'TESTNET' if testnet else 'MAINNET'}")
    
    def _sign_request(self, payload: Dict) -> str:
        """Firma una richiesta con HMAC-SHA256"""
        message = json.dumps(payload)
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Esegue una richiesta HTTP all'API di Hyperliquid"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url, params=data, timeout=10)
            elif method == "POST":
                headers = self.session.headers.copy()
                headers["Authorization"] = f"Bearer {self.api_key}"
                response = self.session.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {"error": str(e)}
    
    def get_account_info(self) -> Dict:
        """Ottiene le informazioni dell'account"""
        response = self._make_request("/info/user", method="GET", data={"user": self.api_key})
        
        if "error" not in response:
            self.account_value = response.get("accountValue", 0.0)
            self.available_balance = response.get("marginUsed", 0.0)
            
            logger.info(f"Account Value: ${self.account_value:.2f}")
            logger.info(f"Available Balance: ${self.available_balance:.2f}")
        
        return response
    
    def get_positions(self) -> Dict[str, HyperliquidPosition]:
        """Ottiene tutte le posizioni aperte"""
        response = self._make_request("/info/user/positions", method="GET", data={"user": self.api_key})
        
        self.positions = {}
        
        if "error" not in response:
            for pos_data in response.get("positions", []):
                symbol = pos_data.get("coin")
                side = pos_data.get("szi", 0)
                
                if side != 0:  # Solo posizioni aperte
                    position = HyperliquidPosition(
                        symbol=symbol,
                        side="Long" if side > 0 else "Short",
                        size=abs(side),
                        entry_price=pos_data.get("entryPx", 0.0),
                        leverage=pos_data.get("leverage", 1.0),
                        liquidation_price=pos_data.get("liquidationPx", 0.0),
                        unrealized_pnl=pos_data.get("unrealizedPnl", 0.0),
                        unrealized_pnl_percent=pos_data.get("unrealizedPnlPercent", 0.0),
                        timestamp=datetime.now()
                    )
                    self.positions[symbol] = position
                    logger.info(f"Position: {symbol} {position.side} {position.size} @ {position.entry_price}")
        
        return self.positions
    
    def get_market_data(self, symbol: str) -> Dict:
        """Ottiene i dati di mercato per un simbolo"""
        response = self._make_request(f"/info/candles", method="GET", data={
            "coin": symbol,
            "interval": "1h",
            "startTime": int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
        })
        
        return response
    
    def place_market_order(self, symbol: str, side: str, size: float, leverage: float = 1.0) -> Dict:
        """Piazza un ordine di mercato"""
        
        if leverage < 1 or leverage > 20:
            logger.error(f"Invalid leverage: {leverage}. Must be between 1 and 20")
            return {"error": "Invalid leverage"}
        
        order_data = {
            "coin": symbol,
            "side": side,  # "Buy" o "Sell"
            "sz": size,
            "orderType": "Market",
            "leverage": leverage,
            "reduceOnly": False
        }
        
        response = self._make_request("/exchange/placeOrder", method="POST", data=order_data)
        
        if "error" not in response:
            order = HyperliquidOrder(
                order_id=response.get("orderId"),
                symbol=symbol,
                side=side,
                order_type="Market",
                size=size,
                price=response.get("price", 0.0),
                status="Filled",
                filled=size,
                timestamp=datetime.now()
            )
            self.orders[order.order_id] = order
            logger.info(f"Market Order Placed: {symbol} {side} {size} @ Leverage {leverage}x")
        
        return response
    
    def place_limit_order(self, symbol: str, side: str, size: float, price: float, leverage: float = 1.0) -> Dict:
        """Piazza un ordine limite"""
        
        if leverage < 1 or leverage > 20:
            logger.error(f"Invalid leverage: {leverage}. Must be between 1 and 20")
            return {"error": "Invalid leverage"}
        
        order_data = {
            "coin": symbol,
            "side": side,
            "sz": size,
            "px": price,
            "orderType": "Limit",
            "leverage": leverage,
            "reduceOnly": False
        }
        
        response = self._make_request("/exchange/placeOrder", method="POST", data=order_data)
        
        if "error" not in response:
            order = HyperliquidOrder(
                order_id=response.get("orderId"),
                symbol=symbol,
                side=side,
                order_type="Limit",
                size=size,
                price=price,
                status="Open",
                filled=0.0,
                timestamp=datetime.now()
            )
            self.orders[order.order_id] = order
            logger.info(f"Limit Order Placed: {symbol} {side} {size} @ ${price} with {leverage}x leverage")
        
        return response
    
    def close_position(self, symbol: str, leverage: float = 1.0) -> Dict:
        """Chiude una posizione"""
        
        if symbol not in self.positions:
            logger.warning(f"No open position for {symbol}")
            return {"error": "No open position"}
        
        position = self.positions[symbol]
        close_side = "Sell" if position.side == "Long" else "Buy"
        
        response = self.place_market_order(symbol, close_side, position.size, leverage)
        
        if "error" not in response:
            del self.positions[symbol]
            logger.info(f"Position Closed: {symbol}")
        
        return response
    
    def set_stop_loss(self, symbol: str, stop_price: float) -> Dict:
        """Imposta uno stop loss per una posizione"""
        
        if symbol not in self.positions:
            logger.warning(f"No open position for {symbol}")
            return {"error": "No open position"}
        
        position = self.positions[symbol]
        close_side = "Sell" if position.side == "Long" else "Buy"
        
        order_data = {
            "coin": symbol,
            "side": close_side,
            "sz": position.size,
            "px": stop_price,
            "orderType": "Stop",
            "stopPx": stop_price,
            "reduceOnly": True
        }
        
        response = self._make_request("/exchange/placeOrder", method="POST", data=order_data)
        logger.info(f"Stop Loss Set: {symbol} @ ${stop_price}")
        
        return response
    
    def set_take_profit(self, symbol: str, tp_price: float) -> Dict:
        """Imposta un take profit per una posizione"""
        
        if symbol not in self.positions:
            logger.warning(f"No open position for {symbol}")
            return {"error": "No open position"}
        
        position = self.positions[symbol]
        close_side = "Sell" if position.side == "Long" else "Buy"
        
        order_data = {
            "coin": symbol,
            "side": close_side,
            "sz": position.size,
            "px": tp_price,
            "orderType": "Limit",
            "reduceOnly": True
        }
        
        response = self._make_request("/exchange/placeOrder", method="POST", data=order_data)
        logger.info(f"Take Profit Set: {symbol} @ ${tp_price}")
        
        return response
    
    def get_funding_rate(self, symbol: str) -> Dict:
        """Ottiene il funding rate per un simbolo"""
        response = self._make_request("/info/fundingRate", method="GET", data={"coin": symbol})
        
        if "error" not in response:
            logger.info(f"Funding Rate for {symbol}: {response.get('fundingRate', 0)}")
        
        return response
    
    def calculate_position_size(self, account_value: float, position_size_percent: float, leverage: float = 1.0) -> float:
        """Calcola la dimensione della posizione in base al capitale e al leverage"""
        position_value = account_value * (position_size_percent / 100)
        position_size = position_value * leverage
        return position_size
    
    def get_trading_fees(self) -> Dict:
        """Ottiene le fee di trading"""
        return {
            "maker_fee": 0.0002,  # 0.02%
            "taker_fee": 0.0005,  # 0.05%
            "funding_fee": "Variable"
        }
    
    def calculate_pnl(self, entry_price: float, exit_price: float, size: float, side: str, leverage: float = 1.0) -> Tuple[float, float]:
        """Calcola il P&L di un trade"""
        
        if side == "Long":
            pnl = (exit_price - entry_price) * size * leverage
        else:  # Short
            pnl = (entry_price - exit_price) * size * leverage
        
        pnl_percent = ((exit_price - entry_price) / entry_price * 100) if side == "Long" else ((entry_price - exit_price) / entry_price * 100)
        
        return pnl, pnl_percent
    
    def get_account_summary(self) -> Dict:
        """Ottiene un riepilogo dell'account"""
        self.get_account_info()
        self.get_positions()
        
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        return {
            "account_value": self.account_value,
            "available_balance": self.available_balance,
            "open_positions": len(self.positions),
            "total_unrealized_pnl": total_unrealized_pnl,
            "positions": {symbol: {
                "side": pos.side,
                "size": pos.size,
                "entry_price": pos.entry_price,
                "leverage": pos.leverage,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_percent": pos.unrealized_pnl_percent
            } for symbol, pos in self.positions.items()}
        }

def test_hyperliquid_adapter():
    """Test dell'adapter Hyperliquid"""
    
    # Carica le credenziali da variabili d'ambiente
    api_key = os.getenv("HYPERLIQUID_API_KEY", "test_key")
    secret_key = os.getenv("HYPERLIQUID_SECRET_KEY", "test_secret")
    
    # Crea l'adapter in modalità testnet
    adapter = HyperliquidAdapter(api_key, secret_key, testnet=True)
    
    print("\n" + "="*100)
    print("HYPERLIQUID ADAPTER TEST")
    print("="*100)
    
    # Test 1: Account Info
    print("\n1. Fetching Account Info...")
    account_info = adapter.get_account_info()
    print(f"   Account Value: ${adapter.account_value:.2f}")
    print(f"   Available Balance: ${adapter.available_balance:.2f}")
    
    # Test 2: Get Positions
    print("\n2. Fetching Open Positions...")
    positions = adapter.get_positions()
    print(f"   Open Positions: {len(positions)}")
    
    # Test 3: Market Data
    print("\n3. Fetching Market Data for BTC...")
    market_data = adapter.get_market_data("BTC")
    print(f"   Market Data Retrieved: {len(market_data) if isinstance(market_data, list) else 'Error'}")
    
    # Test 4: Trading Fees
    print("\n4. Trading Fees:")
    fees = adapter.get_trading_fees()
    print(f"   Maker Fee: {fees['maker_fee']*100:.2f}%")
    print(f"   Taker Fee: {fees['taker_fee']*100:.2f}%")
    
    # Test 5: Position Size Calculation
    print("\n5. Position Size Calculation:")
    position_size = adapter.calculate_position_size(10000, 15, leverage=2.0)
    print(f"   Account: $10,000, Position %: 15%, Leverage: 2x")
    print(f"   Position Size: {position_size:.4f}")
    
    # Test 6: P&L Calculation
    print("\n6. P&L Calculation:")
    pnl, pnl_percent = adapter.calculate_pnl(50000, 52000, 0.1, "Long", leverage=2.0)
    print(f"   Entry: $50,000, Exit: $52,000, Size: 0.1 BTC, Leverage: 2x")
    print(f"   P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)")
    
    # Test 7: Account Summary
    print("\n7. Account Summary:")
    summary = adapter.get_account_summary()
    print(f"   Account Value: ${summary['account_value']:.2f}")
    print(f"   Open Positions: {summary['open_positions']}")
    print(f"   Total Unrealized P&L: ${summary['total_unrealized_pnl']:.2f}")
    
    print("\n" + "="*100)
    print("HYPERLIQUID ADAPTER TEST COMPLETED")
    print("="*100 + "\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_hyperliquid_adapter()

