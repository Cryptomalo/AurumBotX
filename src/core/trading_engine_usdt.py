#!/usr/bin/env python3
"""
AurumBotX Trading Engine - USDT Native
Sistema completo di trading automatico per USDT pairs

Author: AurumBotX Team
Date: 11 Settembre 2025
Version: 2.0 - USDT Native
"""

import logging
import json
import sqlite3
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid

# Import our custom modules
from ..strategies.challenge_growth_strategy_usdt import ChallengeGrowthStrategyUSDT, TradingPhase
from .risk_manager_usdt import RiskManagerUSDT, RiskLevel
from ..exchanges.binance_adapter import BinanceAdapter
from ..data.yahoo_finance_provider import YahooFinanceProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Order types for trading"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderStatus(Enum):
    """Order status tracking"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class TradeDirection(Enum):
    """Trade direction"""
    BUY = "buy"
    SELL = "sell"

@dataclass
class MarketData:
    """Real-time market data structure"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    price_change_24h: float
    price_change_percentage_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    spread_percentage: float
    liquidity_score: float

@dataclass
class TradingOrder:
    """Trading order data structure"""
    order_id: str
    symbol: str
    side: TradeDirection
    order_type: OrderType
    amount_usdt: float
    price: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    filled_amount_usdt: float
    average_fill_price: float
    fees_usdt: float
    strategy_id: str
    user_id: int
    metadata: Dict

@dataclass
class TradeExecution:
    """Trade execution result"""
    trade_id: str
    order_id: str
    symbol: str
    side: TradeDirection
    amount_usdt: float
    execution_price: float
    fees_usdt: float
    net_amount_usdt: float
    execution_time: datetime
    slippage_percentage: float
    success: bool
    error_message: Optional[str]

@dataclass
class Position:
    """Trading position tracking"""
    position_id: str
    symbol: str
    side: TradeDirection
    amount_usdt: float
    entry_price: float
    current_price: float
    unrealized_pnl_usdt: float
    stop_loss_price: float
    take_profit_price: float
    opened_at: datetime
    updated_at: datetime
    strategy_id: str
    user_id: int

class TradingEngineUSDT:
    """
    Advanced Trading Engine for USDT-based cryptocurrency trading
    
    Features:
    - Real-time market data processing
    - Automated order execution
    - Position management
    - Risk-aware trading
    - Strategy integration
    - Performance tracking
    - Multi-exchange ready
    """
    
    def __init__(self, db_path: str = "data/trading_engine.db", 
                 binance_api_key: str = None, binance_api_secret: str = None):
        """Initialize USDT Trading Engine"""
        
        self.db_path = db_path
        self.base_currency = 'USDT'
        
        # Initialize components
        self.strategy = ChallengeGrowthStrategyUSDT()
        self.risk_manager = RiskManagerUSDT()
        
        # Initialize BinanceAdapter with credentials (if provided)
        if binance_api_key and binance_api_secret:
            self.binance_adapter = BinanceAdapter(binance_api_key, binance_api_secret)  # ✅ REAL TRADING
            logger.info("🚀 BinanceAdapter initialized for REAL TRADING")
        else:
            # For testing/demo, create a mock adapter or skip initialization
            self.binance_adapter = None
            logger.warning("⚠️ BinanceAdapter not initialized - No API credentials provided")
            
        self.yahoo_provider = YahooFinanceProvider()  # ✅ REAL-TIME DATA
        
        # Trading state
        self.is_trading_active = False
        self.is_emergency_stop = False
        self.current_balance_usdt = 30.0  # Starting balance
        
        # Market data cache
        self.market_data_cache: Dict[str, MarketData] = {}
        self.last_market_update = datetime.utcnow()
        
        # Active orders and positions
        self.active_orders: Dict[str, TradingOrder] = {}
        self.active_positions: Dict[str, Position] = {}
        
        # Performance tracking
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_volume_usdt': 0.0,
            'total_fees_usdt': 0.0,
            'gross_pnl_usdt': 0.0,
            'net_pnl_usdt': 0.0,
            'best_trade_usdt': 0.0,
            'worst_trade_usdt': 0.0,
            'average_trade_duration': timedelta(hours=0),
            'win_rate_percentage': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown_usdt': 0.0,
            'current_streak': 0,
            'max_winning_streak': 0,
            'max_losing_streak': 0
        }
        
        # Trading configuration
        self.trading_config = {
            'max_concurrent_positions': 3,
            'default_slippage_tolerance': 0.005,  # 0.5%
            'order_timeout_seconds': 300,  # 5 minutes
            'market_data_refresh_seconds': 30,
            'position_check_interval_seconds': 60,
            'emergency_stop_check_seconds': 10,
            'min_spread_threshold': 0.001,  # 0.1%
            'max_spread_threshold': 0.02,   # 2%
            'liquidity_threshold': 100000   # Minimum 24h volume USDT
        }
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.market_data_thread = None
        self.position_monitor_thread = None
        self.running = False
        
        # Initialize database
        self._init_database()
        
        # Event callbacks
        self.on_trade_executed: Optional[Callable] = None
        self.on_position_opened: Optional[Callable] = None
        self.on_position_closed: Optional[Callable] = None
        self.on_risk_alert: Optional[Callable] = None
        
        logger.info("TradingEngineUSDT initialized with USDT-native trading")
    
    def get_balance(self) -> Dict[str, float]:
        """
        Get current account balance
        
        Returns:
            Dict with balance information
        """
        try:
            if self.binance_adapter:
                # Get real balance from Binance
                balance = self.binance_adapter.get_balance()
                if balance:
                    return balance
            
            # Return current demo/local balance
            return {
                "USDT": self.current_balance_usdt,
                "total_value": self.current_balance_usdt,
                "available": self.current_balance_usdt,
                "locked": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {
                "USDT": self.current_balance_usdt,
                "total_value": self.current_balance_usdt,
                "available": self.current_balance_usdt,
                "locked": 0.0
            }
    
    def _init_database(self):
        """Initialize trading engine database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    amount_usdt REAL NOT NULL,
                    price REAL NOT NULL,
                    stop_loss_price REAL,
                    take_profit_price REAL,
                    status TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    filled_amount_usdt REAL DEFAULT 0,
                    average_fill_price REAL DEFAULT 0,
                    fees_usdt REAL DEFAULT 0,
                    strategy_id TEXT,
                    user_id INTEGER,
                    metadata TEXT
                )
            ''')
            
            # Trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    amount_usdt REAL NOT NULL,
                    execution_price REAL NOT NULL,
                    fees_usdt REAL NOT NULL,
                    net_amount_usdt REAL NOT NULL,
                    execution_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    slippage_percentage REAL,
                    strategy_id TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id)
                )
            ''')
            
            # Positions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    position_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    amount_usdt REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    unrealized_pnl_usdt REAL NOT NULL,
                    stop_loss_price REAL,
                    take_profit_price REAL,
                    opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    closed_at DATETIME,
                    realized_pnl_usdt REAL,
                    strategy_id TEXT,
                    user_id INTEGER
                )
            ''')
            
            # Market data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume_24h REAL NOT NULL,
                    price_change_24h REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Performance tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_daily (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    trades_count INTEGER DEFAULT 0,
                    volume_usdt REAL DEFAULT 0,
                    pnl_usdt REAL DEFAULT 0,
                    fees_usdt REAL DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    max_drawdown_usdt REAL DEFAULT 0,
                    user_id INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Trading engine database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing trading database: {str(e)}")
    
    def start_trading(self, user_id: int = 1) -> Dict:
        """
        Start automated trading system
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict: Startup result
        """
        try:
            if self.is_trading_active:
                return {
                    'success': False,
                    'error': 'Trading is already active'
                }
            
            # Check emergency conditions
            if self.is_emergency_stop:
                return {
                    'success': False,
                    'error': 'Emergency stop is active - cannot start trading'
                }
            
            # Validate initial conditions
            validation = self._validate_startup_conditions(user_id)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': f"Startup validation failed: {validation['errors']}"
                }
            
            # Start trading components
            self.is_trading_active = True
            self.running = True
            
            # Start background threads
            self._start_background_threads()
            
            # Log startup
            self._log_trading_event("TRADING_STARTED", f"Trading started for user {user_id}")
            
            startup_result = {
                'success': True,
                'message': 'Trading engine started successfully',
                'timestamp': datetime.utcnow().isoformat(),
                'initial_balance_usdt': self.current_balance_usdt,
                'strategy': 'Challenge Growth Strategy USDT',
                'risk_management': 'Active',
                'max_concurrent_positions': self.trading_config['max_concurrent_positions'],
                'trading_pairs': self.strategy.trading_pairs
            }
            
            logger.info(f"Trading started successfully for user {user_id}")
            return startup_result
            
        except Exception as e:
            logger.error(f"Error starting trading: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to start trading: {str(e)}"
            }
    
    def stop_trading(self, reason: str = "Manual stop", user_id: int = 1) -> Dict:
        """
        Stop automated trading system
        
        Args:
            reason: Reason for stopping
            user_id: User identifier
            
        Returns:
            Dict: Stop result
        """
        try:
            if not self.is_trading_active:
                return {
                    'success': False,
                    'error': 'Trading is not active'
                }
            
            # Stop trading
            self.is_trading_active = False
            self.running = False
            
            # Stop background threads
            self._stop_background_threads()
            
            # Cancel pending orders
            cancelled_orders = self._cancel_all_pending_orders()
            
            # Get final positions
            final_positions = list(self.active_positions.values())
            
            # Log stop event
            self._log_trading_event("TRADING_STOPPED", f"Trading stopped: {reason}")
            
            stop_result = {
                'success': True,
                'message': f'Trading stopped: {reason}',
                'timestamp': datetime.utcnow().isoformat(),
                'final_balance_usdt': self.current_balance_usdt,
                'cancelled_orders': len(cancelled_orders),
                'open_positions': len(final_positions),
                'performance_summary': self._get_session_performance()
            }
            
            logger.info(f"Trading stopped successfully: {reason}")
            return stop_result
            
        except Exception as e:
            logger.error(f"Error stopping trading: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to stop trading: {str(e)}"
            }
    
    def execute_trade(self, symbol: str, side: TradeDirection, amount_usdt: float, 
                     order_type: OrderType = OrderType.MARKET, price: Optional[float] = None,
                     stop_loss_price: Optional[float] = None, take_profit_price: Optional[float] = None,
                     user_id: int = 1) -> Dict:
        """
        Execute a trading order
        
        Args:
            symbol: Trading pair symbol
            side: Trade direction (BUY/SELL)
            amount_usdt: Amount in USDT
            order_type: Type of order
            price: Limit price (for limit orders)
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price
            user_id: User identifier
            
        Returns:
            Dict: Execution result
        """
        try:
            # Validate trade
            validation = self.risk_manager.validate_trade(
                symbol=symbol,
                side=side.value,
                amount_usdt=amount_usdt,
                current_balance_usdt=self.current_balance_usdt,
                user_id=user_id
            )
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': f"Trade validation failed: {validation['errors']}",
                    'risk_analysis': validation
                }
            
            # Get current market data
            market_data = self._get_market_data(symbol)
            if not market_data:
                return {
                    'success': False,
                    'error': f"Market data not available for {symbol}"
                }
            
            # Create order
            order = self._create_order(
                symbol=symbol,
                side=side,
                amount_usdt=amount_usdt,
                order_type=order_type,
                price=price or market_data.price,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                user_id=user_id
            )
            
            # Execute order
            execution_result = self._execute_order(order, market_data)
            
            if execution_result['success']:
                # Update balance
                if side == TradeDirection.BUY:
                    self.current_balance_usdt -= execution_result['net_amount_usdt']
                else:
                    self.current_balance_usdt += execution_result['net_amount_usdt']
                
                # Create position if buy order
                if side == TradeDirection.BUY:
                    position = self._create_position(order, execution_result, user_id)
                    self.active_positions[position.position_id] = position
                    
                    if self.on_position_opened:
                        self.on_position_opened(position)
                
                # Update performance metrics
                self._update_performance_metrics(execution_result)
                
                # Trigger callback
                if self.on_trade_executed:
                    self.on_trade_executed(execution_result)
                
                logger.info(f"Trade executed successfully: {symbol} {side.value} {amount_usdt} USDT")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return {
                'success': False,
                'error': f"Trade execution failed: {str(e)}"
            }
    
    def scan_market_opportunities(self, user_id: int = 1) -> List[Dict]:
        """
        Scan market for trading opportunities
        
        Args:
            user_id: User identifier
            
        Returns:
            List[Dict]: List of trading opportunities
        """
        try:
            opportunities = []
            
            # Update market data
            self._update_market_data()
            
            # Scan each trading pair
            for symbol in self.strategy.trading_pairs:
                market_data = self.market_data_cache.get(symbol)
                if not market_data:
                    continue
                
                # Analyze opportunity
                signal = self.strategy.analyze_market_opportunity(
                    symbol=symbol,
                    market_data={
                        'price': market_data.price,
                        'volume_24h': market_data.volume_24h,
                        'price_change_24h': market_data.price_change_percentage_24h
                    }
                )
                
                if signal and signal.confidence > 0.6:  # High confidence signals only
                    # Calculate position sizing
                    sizing = self.risk_manager.calculate_optimal_position_size(
                        symbol=symbol,
                        balance_usdt=self.current_balance_usdt,
                        confidence=signal.confidence,
                        volatility=market_data.spread_percentage
                    )
                    
                    if sizing['trade_viable']:
                        opportunity = {
                            'symbol': symbol,
                            'signal': signal.side,
                            'confidence': signal.confidence,
                            'current_price': market_data.price,
                            'recommended_amount_usdt': sizing['recommended_size_usdt'],
                            'estimated_risk_usdt': sizing['estimated_risk_usdt'],
                            'reason': signal.reason,
                            'market_data': {
                                'price_change_24h': market_data.price_change_percentage_24h,
                                'volume_24h': market_data.volume_24h,
                                'spread': market_data.spread_percentage
                            },
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        opportunities.append(opportunity)
            
            # Sort by confidence
            opportunities.sort(key=lambda x: x['confidence'], reverse=True)
            
            logger.info(f"Market scan completed: {len(opportunities)} opportunities found")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error scanning market opportunities: {str(e)}")
            return []
    
    def get_trading_status(self, user_id: int = 1) -> Dict:
        """
        Get comprehensive trading status
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict: Complete trading status
        """
        try:
            # Get strategy status
            strategy_status = self.strategy.get_strategy_status(self.current_balance_usdt)
            
            # Get risk summary
            risk_summary = self.risk_manager.get_risk_summary(user_id)
            
            # Get active positions summary
            positions_summary = self._get_positions_summary()
            
            # Get recent performance
            recent_performance = self._get_recent_performance()
            
            trading_status = {
                'timestamp': datetime.utcnow().isoformat(),
                'trading_active': self.is_trading_active,
                'emergency_stop': self.is_emergency_stop,
                'current_balance_usdt': self.current_balance_usdt,
                'strategy_status': strategy_status,
                'risk_summary': {
                    'overall_risk_score': risk_summary.get('daily_summary', {}).get('risk_score', 0.0),
                    'emergency_stop_active': risk_summary.get('emergency_stop_active', False),
                    'circuit_breaker_active': risk_summary.get('circuit_breaker_active', False),
                    'active_alerts': risk_summary.get('alerts_count', 0)
                },
                'positions': positions_summary,
                'performance': {
                    'session': self.performance_metrics.copy(),
                    'recent': recent_performance
                },
                'market_status': {
                    'last_update': self.last_market_update.isoformat(),
                    'tracked_pairs': len(self.market_data_cache),
                    'data_quality': self._assess_market_data_quality()
                },
                'system_health': {
                    'threads_running': self.running,
                    'orders_pending': len([o for o in self.active_orders.values() if o.status == OrderStatus.PENDING]),
                    'positions_open': len(self.active_positions),
                    'last_trade': self._get_last_trade_time()
                }
            }
            
            return trading_status
            
        except Exception as e:
            logger.error(f"Error getting trading status: {str(e)}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'trading_active': False
            }
    
    def emergency_stop(self, reason: str = "Emergency stop triggered", user_id: int = 1) -> Dict:
        """
        Emergency stop all trading activities
        
        Args:
            reason: Reason for emergency stop
            user_id: User identifier
            
        Returns:
            Dict: Emergency stop result
        """
        try:
            logger.warning(f"EMERGENCY STOP TRIGGERED: {reason}")
            
            # Set emergency state
            self.is_emergency_stop = True
            self.is_trading_active = False
            
            # Cancel all pending orders
            cancelled_orders = self._cancel_all_pending_orders()
            
            # Close all positions (in real implementation)
            # For now, just mark them for closure
            positions_to_close = list(self.active_positions.values())
            
            # Stop all background processes
            self.running = False
            self._stop_background_threads()
            
            # Log emergency event
            self._log_trading_event("EMERGENCY_STOP", reason)
            
            # Trigger risk alert callback
            if self.on_risk_alert:
                self.on_risk_alert({
                    'type': 'EMERGENCY_STOP',
                    'severity': 'CRITICAL',
                    'message': reason,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            emergency_result = {
                'success': True,
                'message': f'Emergency stop executed: {reason}',
                'timestamp': datetime.utcnow().isoformat(),
                'actions_taken': {
                    'cancelled_orders': len(cancelled_orders),
                    'positions_marked_for_closure': len(positions_to_close),
                    'trading_suspended': True,
                    'background_processes_stopped': True
                },
                'current_balance_usdt': self.current_balance_usdt,
                'recovery_instructions': [
                    "Review the cause of emergency stop",
                    "Verify system integrity",
                    "Reset emergency state manually",
                    "Restart trading when safe"
                ]
            }
            
            return emergency_result
            
        except Exception as e:
            logger.error(f"Error during emergency stop: {str(e)}")
            return {
                'success': False,
                'error': f"Emergency stop failed: {str(e)}"
            }
    
    # Private helper methods
    
    def _validate_startup_conditions(self, user_id: int) -> Dict:
        """Validate conditions for starting trading"""
        errors = []
        
        if self.current_balance_usdt < 1.0:
            errors.append("Insufficient balance for trading")
        
        if not self.strategy.trading_pairs:
            errors.append("No trading pairs configured")
        
        # Check market data availability
        if not self.market_data_cache:
            self._update_market_data()
            if not self.market_data_cache:
                errors.append("Market data not available")
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    def _start_background_threads(self):
        """Start background monitoring threads"""
        try:
            # Market data update thread
            self.market_data_thread = threading.Thread(
                target=self._market_data_loop,
                daemon=True
            )
            self.market_data_thread.start()
            
            # Position monitoring thread
            self.position_monitor_thread = threading.Thread(
                target=self._position_monitor_loop,
                daemon=True
            )
            self.position_monitor_thread.start()
            
            logger.info("Background threads started")
            
        except Exception as e:
            logger.error(f"Error starting background threads: {str(e)}")
    
    def _stop_background_threads(self):
        """Stop background monitoring threads"""
        try:
            self.running = False
            
            # Wait for threads to finish
            if self.market_data_thread and self.market_data_thread.is_alive():
                self.market_data_thread.join(timeout=5)
            
            if self.position_monitor_thread and self.position_monitor_thread.is_alive():
                self.position_monitor_thread.join(timeout=5)
            
            logger.info("Background threads stopped")
            
        except Exception as e:
            logger.error(f"Error stopping background threads: {str(e)}")
    
    def _market_data_loop(self):
        """Background loop for updating market data"""
        while self.running:
            try:
                self._update_market_data()
                time.sleep(self.trading_config['market_data_refresh_seconds'])
            except Exception as e:
                logger.error(f"Error in market data loop: {str(e)}")
                time.sleep(10)  # Wait before retrying
    
    def _position_monitor_loop(self):
        """Background loop for monitoring positions"""
        while self.running:
            try:
                self._monitor_positions()
                time.sleep(self.trading_config['position_check_interval_seconds'])
            except Exception as e:
                logger.error(f"Error in position monitor loop: {str(e)}")
                time.sleep(10)  # Wait before retrying
    
    def _update_market_data(self):
        """Update market data for all trading pairs using real-time data"""
        try:
            for symbol in self.strategy.trading_pairs:
                # Get real-time market data (no more simulation!)
                market_data = self._get_real_market_data(symbol)
                if market_data:
                    self.market_data_cache[symbol] = market_data
                else:
                    logger.error(f"❌ Failed to get market data for {symbol}")
            
            self.last_market_update = datetime.utcnow()
            logger.info(f"📊 Updated real-time data for {len(self.market_data_cache)} symbols")
            
        except Exception as e:
            logger.error(f"Error updating market data: {str(e)}")
    
    def _get_real_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get real-time market data using Yahoo Finance (REAL DATA)"""
        try:
            # Get real-time data from Yahoo Finance
            yahoo_data = self.yahoo_provider.get_real_time_price(symbol)
            
            if not yahoo_data:
                logger.warning(f"⚠️ Failed to get real-time data for {symbol}, using fallback")
                return self._get_fallback_market_data(symbol)
            
            # Convert Yahoo data to our MarketData format
            market_data = MarketData(
                symbol=symbol,
                price=yahoo_data.price,
                bid=yahoo_data.bid,
                ask=yahoo_data.ask,
                volume_24h=yahoo_data.volume_24h,
                price_change_24h=yahoo_data.change_24h,
                price_change_percentage_24h=yahoo_data.change_24h_percent,
                high_24h=yahoo_data.price * 1.02,  # Approximate high
                low_24h=yahoo_data.price * 0.98,   # Approximate low
                timestamp=yahoo_data.timestamp,
                spread_percentage=((yahoo_data.ask - yahoo_data.bid) / yahoo_data.price) * 100,
                liquidity_score=0.9 if yahoo_data.volume_24h > 1000000 else 0.7
            )
            
            logger.info(f"📊 Real-time data for {symbol}: ${market_data.price:.2f} ({market_data.price_change_percentage_24h:+.2f}%)")
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Error getting real-time data for {symbol}: {str(e)}")
            return self._get_fallback_market_data(symbol)
    
    def _get_fallback_market_data(self, symbol: str) -> MarketData:
        """Fallback market data if real-time fails (emergency only)"""
        logger.warning(f"⚠️ Using fallback data for {symbol}")
        
        # Conservative fallback prices (updated September 2025)
        fallback_prices = {
            'BTC/USDT': 113000,  # Updated realistic prices
            'ETH/USDT': 4400,
            'BNB/USDT': 890,
            'SOL/USDT': 220,
            'ADA/USDT': 0.65,
            'DOT/USDT': 8.5,
            'MATIC/USDT': 1.1,
            'AVAX/USDT': 45,
            'LINK/USDT': 18,
            'UNI/USDT': 12
        }
        
        base_price = fallback_prices.get(symbol, 100)
        bid = base_price * 0.999
        ask = base_price * 1.001
        
        return MarketData(
            symbol=symbol,
            price=base_price,
            bid=bid,
            ask=ask,
            volume_24h=5000000,  # Conservative volume
            price_change_24h=0.0,
            price_change_percentage_24h=0.0,
            high_24h=base_price * 1.01,
            low_24h=base_price * 0.99,
            timestamp=datetime.utcnow(),
            spread_percentage=0.1,
            liquidity_score=0.6
        )
    
    def _get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get market data for symbol"""
        return self.market_data_cache.get(symbol)
    
    def _create_order(self, symbol: str, side: TradeDirection, amount_usdt: float,
                     order_type: OrderType, price: float, stop_loss_price: Optional[float],
                     take_profit_price: Optional[float], user_id: int) -> TradingOrder:
        """Create a trading order"""
        order_id = f"ORDER_{uuid.uuid4().hex[:8].upper()}"
        
        order = TradingOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount_usdt=amount_usdt,
            price=price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            filled_amount_usdt=0.0,
            average_fill_price=0.0,
            fees_usdt=0.0,
            strategy_id="challenge_growth_usdt",
            user_id=user_id,
            metadata={}
        )
        
        self.active_orders[order_id] = order
        return order
    
    def _execute_order(self, order: TradingOrder, market_data: MarketData) -> Dict:
        """Execute a trading order using BinanceAdapter (REAL TRADING)"""
        try:
            # Check if BinanceAdapter is available
            if not self.binance_adapter:
                logger.warning("⚠️ BinanceAdapter not available - Using simulation mode")
                return self._execute_order_simulation(order, market_data)
            
            # Import OrderSide from BinanceAdapter
            from ..exchanges.binance_adapter import OrderSide
            
            # Convert TradeDirection to OrderSide
            binance_side = OrderSide.BUY if order.side == TradeDirection.BUY else OrderSide.SELL
            
            # Calculate quantity based on order type
            if order.order_type == OrderType.MARKET:
                # For market orders, calculate quantity from USDT amount
                if order.side == TradeDirection.BUY:
                    quantity = order.amount_usdt / market_data.price
                else:
                    # For sell orders, we need the asset quantity (not USDT)
                    # This should come from position size
                    quantity = order.amount_usdt / market_data.price
                
                # Execute market order on Binance
                logger.info(f"🚀 EXECUTING REAL TRADE: {binance_side.value} {quantity:.6f} {order.symbol}")
                result = self.binance_adapter.create_market_order(
                    symbol=order.symbol.replace('/', ''),  # Convert BTC/USDT to BTCUSDT
                    side=binance_side,
                    quantity=quantity
                )
                
            elif order.order_type == OrderType.LIMIT:
                # Calculate quantity for limit order
                quantity = order.amount_usdt / order.price
                
                # Execute limit order on Binance
                logger.info(f"🚀 EXECUTING REAL LIMIT ORDER: {binance_side.value} {quantity:.6f} {order.symbol} @ {order.price}")
                result = self.binance_adapter.create_limit_order(
                    symbol=order.symbol.replace('/', ''),
                    side=binance_side,
                    quantity=quantity,
                    price=order.price
                )
            
            else:
                return {
                    'success': False,
                    'error': f'Order type {order.order_type} not supported yet'
                }
            
            # Check if order was successful
            if not result.success:
                logger.error(f"❌ BINANCE ORDER FAILED: {result.error_message}")
                return {
                    'success': False,
                    'error': f'Binance order failed: {result.error_message}'
                }
            
            # Update order status with real data
            order.status = OrderStatus.FILLED if result.status == 'FILLED' else OrderStatus.SUBMITTED
            order.filled_amount_usdt = result.executed_qty * result.price if result.executed_qty else order.amount_usdt
            order.average_fill_price = result.price if result.price else market_data.price
            order.fees_usdt = result.commission if result.commission else order.amount_usdt * 0.001  # Default 0.1% fee
            order.updated_at = datetime.utcnow()
            
            # Create trade execution record
            trade_id = f"TRADE_{uuid.uuid4().hex[:8].upper()}"
            
            execution = TradeExecution(
                trade_id=trade_id,
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                amount_usdt=order.amount_usdt,
                execution_price=order.average_fill_price,
                fees_usdt=order.fees_usdt,
                net_amount_usdt=order.amount_usdt - order.fees_usdt,
                execution_time=datetime.utcnow(),
                slippage_percentage=0.0,  # Real slippage will be calculated from execution price
                success=True,
                error_message=None
            )
            
            # Save to database
            self._save_trade_execution(execution)
            
            logger.info(f"✅ REAL TRADE EXECUTED: {trade_id} - {order.side.value} {order.amount_usdt} USDT")
            
            return {
                'success': True,
                'trade_id': trade_id,
                'execution_price': order.average_fill_price,
                'fees_usdt': order.fees_usdt,
                'net_amount_usdt': order.amount_usdt - order.fees_usdt,
                'binance_order_id': result.order_id,
                'real_trading': True  # Flag to indicate this was a real trade
            }
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in real trade execution: {str(e)}")
            return {
                'success': False,
                'error': f'Real trade execution failed: {str(e)}'
            }
    
    def _execute_order_simulation(self, order: TradingOrder, market_data: MarketData) -> Dict:
        """Execute order in simulation mode (fallback when no BinanceAdapter)"""
        try:
            logger.info(f"📊 SIMULATION MODE: {order.side.value} {order.amount_usdt} USDT of {order.symbol}")
            
            # Simulate execution with realistic parameters
            execution_price = market_data.price
            fees_usdt = order.amount_usdt * 0.001  # 0.1% fee
            net_amount_usdt = order.amount_usdt - fees_usdt
            
            # Update order status
            order.status = OrderStatus.FILLED
            order.filled_amount_usdt = order.amount_usdt
            order.average_fill_price = execution_price
            order.fees_usdt = fees_usdt
            order.updated_at = datetime.utcnow()
            
            # Create trade execution record
            trade_id = f"SIM_{uuid.uuid4().hex[:8].upper()}"
            
            execution = TradeExecution(
                trade_id=trade_id,
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                amount_usdt=order.amount_usdt,
                execution_price=execution_price,
                fees_usdt=fees_usdt,
                net_amount_usdt=net_amount_usdt,
                execution_time=datetime.utcnow(),
                slippage_percentage=0.0,
                success=True,
                error_message=None
            )
            
            # Save to database
            self._save_trade_execution(execution)
            
            logger.info(f"✅ SIMULATION TRADE: {trade_id} - {order.side.value} {order.amount_usdt} USDT")
            
            return {
                'success': True,
                'trade_id': trade_id,
                'execution_price': execution_price,
                'fees_usdt': fees_usdt,
                'net_amount_usdt': net_amount_usdt,
                'real_trading': False  # Flag to indicate this was simulation
            }
            
        except Exception as e:
            logger.error(f"❌ ERROR in simulation trade execution: {str(e)}")
            return {
                'success': False,
                'error': f'Simulation trade execution failed: {str(e)}'
            }
    
    def _create_position(self, order: TradingOrder, execution_result: Dict, user_id: int) -> Position:
        """Create a position from executed order"""
        position_id = f"POS_{uuid.uuid4().hex[:8].upper()}"
        
        position = Position(
            position_id=position_id,
            symbol=order.symbol,
            side=order.side,
            amount_usdt=order.amount_usdt,
            entry_price=execution_result['execution_price'],
            current_price=execution_result['execution_price'],
            unrealized_pnl_usdt=0.0,
            stop_loss_price=order.stop_loss_price or 0.0,
            take_profit_price=order.take_profit_price or 0.0,
            opened_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            strategy_id=order.strategy_id,
            user_id=user_id
        )
        
        return position
    
    def _monitor_positions(self):
        """Monitor active positions for stop loss/take profit"""
        for position in list(self.active_positions.values()):
            try:
                # Get current market data
                market_data = self._get_market_data(position.symbol)
                if not market_data:
                    continue
                
                # Update position with current price
                position.current_price = market_data.price
                position.updated_at = datetime.utcnow()
                
                # Calculate unrealized P&L
                if position.side == TradeDirection.BUY:
                    quantity = position.amount_usdt / position.entry_price
                    current_value = quantity * position.current_price
                    position.unrealized_pnl_usdt = current_value - position.amount_usdt
                
                # Check stop loss
                if position.stop_loss_price > 0:
                    if ((position.side == TradeDirection.BUY and market_data.price <= position.stop_loss_price) or
                        (position.side == TradeDirection.SELL and market_data.price >= position.stop_loss_price)):
                        self._close_position(position, "Stop loss triggered")
                        continue
                
                # Check take profit
                if position.take_profit_price > 0:
                    if ((position.side == TradeDirection.BUY and market_data.price >= position.take_profit_price) or
                        (position.side == TradeDirection.SELL and market_data.price <= position.take_profit_price)):
                        self._close_position(position, "Take profit triggered")
                        continue
                
            except Exception as e:
                logger.error(f"Error monitoring position {position.position_id}: {str(e)}")
    
    def _close_position(self, position: Position, reason: str):
        """Close a position"""
        try:
            logger.info(f"Closing position {position.position_id}: {reason}")
            
            # Execute closing trade
            close_side = TradeDirection.SELL if position.side == TradeDirection.BUY else TradeDirection.BUY
            
            execution_result = self.execute_trade(
                symbol=position.symbol,
                side=close_side,
                amount_usdt=position.amount_usdt,
                user_id=position.user_id
            )
            
            if execution_result['success']:
                # Remove from active positions
                del self.active_positions[position.position_id]
                
                # Trigger callback
                if self.on_position_closed:
                    self.on_position_closed(position, reason)
                
                logger.info(f"Position {position.position_id} closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing position {position.position_id}: {str(e)}")
    
    def _cancel_all_pending_orders(self) -> List[str]:
        """Cancel all pending orders"""
        cancelled_orders = []
        
        for order_id, order in list(self.active_orders.items()):
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.utcnow()
                cancelled_orders.append(order_id)
        
        return cancelled_orders
    
    def _update_performance_metrics(self, execution_result: Dict):
        """Update performance tracking metrics"""
        self.performance_metrics['total_trades'] += 1
        self.performance_metrics['total_volume_usdt'] += execution_result.get('amount_usdt', 0)
        self.performance_metrics['total_fees_usdt'] += execution_result.get('fees_usdt', 0)
    
    def _get_positions_summary(self) -> Dict:
        """Get summary of active positions"""
        if not self.active_positions:
            return {
                'total_positions': 0,
                'total_invested_usdt': 0.0,
                'total_unrealized_pnl_usdt': 0.0
            }
        
        total_invested = sum(pos.amount_usdt for pos in self.active_positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl_usdt for pos in self.active_positions.values())
        
        return {
            'total_positions': len(self.active_positions),
            'total_invested_usdt': total_invested,
            'total_unrealized_pnl_usdt': total_unrealized_pnl,
            'positions': [
                {
                    'symbol': pos.symbol,
                    'amount_usdt': pos.amount_usdt,
                    'unrealized_pnl_usdt': pos.unrealized_pnl_usdt,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price
                }
                for pos in self.active_positions.values()
            ]
        }
    
    def _get_recent_performance(self) -> Dict:
        """Get recent performance metrics"""
        return {
            'today_trades': 0,
            'today_pnl_usdt': 0.0,
            'week_pnl_usdt': 0.0,
            'month_pnl_usdt': 0.0
        }
    
    def _assess_market_data_quality(self) -> str:
        """Assess quality of market data"""
        if not self.market_data_cache:
            return "NO_DATA"
        
        # Check data freshness
        time_since_update = datetime.utcnow() - self.last_market_update
        if time_since_update.total_seconds() > 300:  # 5 minutes
            return "STALE"
        
        return "GOOD"
    
    def _get_last_trade_time(self) -> Optional[str]:
        """Get timestamp of last trade"""
        # Would query database for last trade
        return None
    
    def _get_session_performance(self) -> Dict:
        """Get performance summary for current session"""
        return self.performance_metrics.copy()
    
    def _log_trading_event(self, event_type: str, description: str):
        """Log trading event"""
        logger.info(f"TRADING_EVENT: {event_type} - {description}")
    
    def _save_trade_execution(self, execution: TradeExecution):
        """Save trade execution to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (
                    trade_id, order_id, symbol, side, amount_usdt, execution_price,
                    fees_usdt, net_amount_usdt, execution_time, slippage_percentage,
                    strategy_id, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution.trade_id, execution.order_id, execution.symbol,
                execution.side.value, execution.amount_usdt, execution.execution_price,
                execution.fees_usdt, execution.net_amount_usdt, execution.execution_time,
                execution.slippage_percentage, "challenge_growth_usdt", 1
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving trade execution: {str(e)}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize trading engine
    engine = TradingEngineUSDT()
    
    print("=== AurumBotX Trading Engine USDT - Testing ===\n")
    
    # Test 1: Start trading
    print("1. Starting Trading Engine:")
    start_result = engine.start_trading()
    print(f"Success: {start_result['success']}")
    if start_result['success']:
        print(f"Initial Balance: {start_result['initial_balance_usdt']} USDT")
        print(f"Strategy: {start_result['strategy']}")
    
    # Test 2: Scan market opportunities
    print("\n2. Scanning Market Opportunities:")
    opportunities = engine.scan_market_opportunities()
    print(f"Found {len(opportunities)} opportunities")
    for i, opp in enumerate(opportunities[:3]):  # Show top 3
        print(f"  {i+1}. {opp['symbol']}: {opp['signal']} (confidence: {opp['confidence']:.2f})")
    
    # Test 3: Execute a trade
    if opportunities:
        print("\n3. Executing Test Trade:")
        best_opportunity = opportunities[0]
        
        trade_result = engine.execute_trade(
            symbol=best_opportunity['symbol'],
            side=TradeDirection.BUY if best_opportunity['signal'] == 'BUY' else TradeDirection.SELL,
            amount_usdt=best_opportunity['recommended_amount_usdt']
        )
        
        print(f"Trade Success: {trade_result['success']}")
        if trade_result['success']:
            print(f"Execution Price: {trade_result['execution_price']:.2f}")
            print(f"Fees: {trade_result['fees_usdt']:.4f} USDT")
            print(f"Slippage: {trade_result['slippage_percentage']:.3f}%")
    
    # Test 4: Get trading status
    print("\n4. Trading Status:")
    status = engine.get_trading_status()
    print(f"Trading Active: {status['trading_active']}")
    print(f"Current Balance: {status['current_balance_usdt']} USDT")
    print(f"Open Positions: {status['positions']['total_positions']}")
    print(f"Strategy Phase: {status['strategy_status']['current_phase']}")
    
    # Test 5: Stop trading
    print("\n5. Stopping Trading Engine:")
    stop_result = engine.stop_trading("Test completed")
    print(f"Success: {stop_result['success']}")
    print(f"Final Balance: {stop_result['final_balance_usdt']} USDT")
    
    print("\n=== Trading Engine USDT Testing Complete ===")

