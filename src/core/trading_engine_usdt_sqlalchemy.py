#!/usr/bin/env python3
"""
AurumBotX Trading Engine - USDT Native
Sistema completo di trading automatico per USDT pairs

Author: AurumBotX Team
Date: 11 Settembre 2025
Version: 2.1 - USDT Native with SQLAlchemy
"""

import logging
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
import os
import numpy as np

# Import SQLAlchemy for database connection pooling
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

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
    - SQLAlchemy connection pooling
    """
    
    def __init__(self, db_path: str = "data/trading_engine.db", 
                 binance_api_key: str = None, binance_api_secret: str = None):
        """Initialize USDT Trading Engine"""
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(project_root, db_path)
        self.base_currency = 'USDT'

        # Initialize SQLAlchemy Engine and Session
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            connect_args={'check_same_thread': False}
        )
        self.Session = sessionmaker(bind=self.engine)
        
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
        
        logger.info("TradingEngineUSDT initialized with USDT-native trading and SQLAlchemy connection pooling")
    
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
            with self.engine.connect() as connection:
                # Orders table
                connection.execute(text('''
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
                '''))
                
                # Trades table
                connection.execute(text('''
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
                        spread_percentage REAL,
                        strategy_id TEXT,
                        user_id INTEGER,
                        FOREIGN KEY (order_id) REFERENCES orders (order_id)
                    )
                '''))
                
                # Positions table
                connection.execute(text('''
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
                '''))
                
                # Market data table
                connection.execute(text('''
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        price REAL NOT NULL,
                        volume_24h REAL NOT NULL,
                        price_change_24h REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                '''))
                
                # Performance tracking table
                connection.execute(text('''
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
                '''))
            
            logger.info("Trading engine database initialized with SQLAlchemy")
            
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
            symbol: Trading pair (e.g., 'BTC-USDT')
            side: BUY or SELL
            amount_usdt: Amount in USDT
            order_type: MARKET, LIMIT, etc.
            price: Limit price (for LIMIT orders)
            stop_loss_price: Stop-loss price
            take_profit_price: Take-profit price
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

    def _cancel_all_pending_orders(self) -> List:
        """Cancel all pending orders."""
        # In a real implementation, this would interact with the exchange API
        # to cancel all open orders.
        cancelled_orders = []
        for order_id, order in list(self.active_orders.items()):
            if order.status == OrderStatus.PENDING or order.status == OrderStatus.SUBMITTED:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.utcnow()
                cancelled_orders.append(order)
                # In a real implementation, you would also remove the order from the exchange.
        return cancelled_orders

    def _log_trading_event(self, event_type: str, message: str):
        """Log a trading event to the database or a log file."""
        logger.info(f"[{event_type}] {message}")
        # In a real implementation, you might want to save this to a database table.

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
    
    def _get_fallback_market_data(self, symbol: str) -> Optional[MarketData]:
        """Fallback to get market data if real-time fails"""
        try:
            # Use Binance for fallback data
            if self.binance_adapter:
                ticker = self.binance_adapter.get_ticker(symbol)
                if ticker:
                    return MarketData(
                        symbol=symbol,
                        price=ticker['lastPrice'],
                        bid=ticker['bidPrice'],
                        ask=ticker['askPrice'],
                        volume_24h=ticker['volume'],
                        price_change_24h=ticker['priceChange'],
                        price_change_percentage_24h=ticker['priceChangePercent'],
                        high_24h=ticker['highPrice'],
                        low_24h=ticker['lowPrice'],
                        timestamp=datetime.fromtimestamp(ticker['closeTime'] / 1000),
                        spread_percentage=((ticker['askPrice'] - ticker['bidPrice']) / ticker['lastPrice']) * 100,
                        liquidity_score=0.8
                    )
            return None
        except Exception as e:
            logger.error(f"Error in fallback market data for {symbol}: {e}")
            return None

    def _log_trading_event(self, event_type: str, message: str):
        """Log a trading event to the database."""
        with self.Session() as session:
            # In a real application, you would have a dedicated events table
            logger.info(f"EVENT: {event_type} - {message}")
            # For now, we just log to the main logger

    def _get_session_performance(self) -> Dict:
        """Get performance summary for the current session."""
        return self.performance_metrics

    def _get_last_trade_time(self) -> Optional[str]:
        """Get the timestamp of the last trade."""
        with self.Session() as session:
            last_trade_time = session.execute(text("SELECT MAX(execution_time) FROM trades")).scalar()
            return last_trade_time.isoformat() if last_trade_time else None

    def _get_recent_performance(self) -> Dict:
        """Get performance metrics for the last 24 hours."""
        with self.Session() as session:
            # This is a simplified example. A real implementation would involve more complex queries.
            return {
                'trades_24h': 0,
                'pnl_24h': 0.0
            }

    def _assess_market_data_quality(self) -> str:
        """Assess the quality of the market data."""
        # Simple assessment based on last update time
        if (datetime.utcnow() - self.last_market_update).total_seconds() > 300:
            return "STALE"
        return "GOOD"

    def _get_positions_summary(self) -> List[Dict]:
        """Get a summary of all active positions."""
        summary = []
        for pos in self.active_positions.values():
            summary.append(asdict(pos))
        return summary

    def _cancel_all_pending_orders(self) -> List[Dict]:
        """Cancel all pending orders."""
        # This is a mock implementation. In a real scenario, you would interact with the exchange.
        cancelled_orders = []
        for order_id, order in list(self.active_orders.items()):
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.utcnow()
                cancelled_orders.append(asdict(order))
                # In a real implementation, you would also update the database
        return cancelled_orders

    def _create_order(self, symbol: str, side: TradeDirection, amount_usdt: float, order_type: OrderType, price: float, stop_loss_price: Optional[float], take_profit_price: Optional[float], user_id: int) -> TradingOrder:
        """Create a new trading order."""
        order = TradingOrder(
            order_id=str(uuid.uuid4()),
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
            strategy_id="default", # Or get from strategy
            user_id=user_id,
            metadata={}
        )
        self.active_orders[order.order_id] = order
        # In a real implementation, you would also save the order to the database here
        return order

    def _execute_order(self, order: TradingOrder, market_data: MarketData) -> Dict:
        """Execute a trading order."""
        try:
            if self.binance_adapter:
                # Real execution with Binance
                executed_order = self.binance_adapter.create_order(
                    symbol=order.symbol,
                    side=order.side.name,
                    type=order.order_type.name,
                    quantity=order.amount_usdt / market_data.price  # Approximate quantity
                )
                execution_price = float(executed_order['fills'][0]['price'])
                fees_usdt = float(executed_order['fills'][0]['commission'])
                net_amount_usdt = order.amount_usdt - fees_usdt
                slippage = (execution_price - market_data.price) / market_data.price
            else:
                # Mock execution
                slippage = self.trading_config['default_slippage_tolerance'] * (1 if order.side == TradeDirection.BUY else -1)
                execution_price = market_data.price * (1 + slippage)
                fees = 0.001 # 0.1% fee
                fees_usdt = order.amount_usdt * fees
                net_amount_usdt = order.amount_usdt - fees_usdt

            execution = TradeExecution(
                trade_id=str(uuid.uuid4()),
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                amount_usdt=order.amount_usdt,
                execution_price=execution_price,
                fees_usdt=fees_usdt,
                net_amount_usdt=net_amount_usdt,
                execution_time=datetime.utcnow(),
                slippage_percentage=slippage * 100,
                success=True,
                error_message=None
            )

            # Update order status
            order.status = OrderStatus.FILLED
            order.filled_amount_usdt = order.amount_usdt
            order.average_fill_price = execution_price
            order.fees_usdt = fees_usdt
            order.updated_at = datetime.utcnow()

            # Save trade to database
            with self.Session() as session:
                session.execute(
                    text("INSERT INTO trades (trade_id, order_id, symbol, side, amount_usdt, execution_price, fees_usdt, net_amount_usdt, execution_time, slippage_percentage, strategy_id, user_id) VALUES (:trade_id, :order_id, :symbol, :side, :amount_usdt, :execution_price, :fees_usdt, :net_amount_usdt, :execution_time, :slippage_percentage, :strategy_id, :user_id)"),
                    {"trade_id": execution.trade_id, "order_id": execution.order_id, "symbol": execution.symbol, "side": execution.side.value, "amount_usdt": execution.amount_usdt, "execution_price": execution.execution_price, "fees_usdt": execution.fees_usdt, "net_amount_usdt": execution.net_amount_usdt, "execution_time": execution.execution_time, "slippage_percentage": execution.slippage_percentage, "strategy_id": order.strategy_id, "user_id": order.user_id}
                )
                session.commit()

            return asdict(execution)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _create_position(self, order: TradingOrder, execution: Dict, user_id: int) -> Position:
        """Create a new position."""
        position = Position(
            position_id=str(uuid.uuid4()),
            symbol=order.symbol,
            side=order.side,
            amount_usdt=order.amount_usdt,
            entry_price=execution['execution_price'],
            current_price=execution['execution_price'],
            unrealized_pnl_usdt=0.0,
            stop_loss_price=order.stop_loss_price,
            take_profit_price=order.take_profit_price,
            opened_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            strategy_id=order.strategy_id,
            user_id=user_id
        )
        # Save position to database
        with self.Session() as session:
            session.execute(
                text("INSERT INTO positions (position_id, symbol, side, amount_usdt, entry_price, current_price, unrealized_pnl_usdt, stop_loss_price, take_profit_price, opened_at, updated_at, strategy_id, user_id) VALUES (:position_id, :symbol, :side, :amount_usdt, :entry_price, :current_price, :unrealized_pnl_usdt, :stop_loss_price, :take_profit_price, :opened_at, :updated_at, :strategy_id, :user_id)"),
                {"position_id": position.position_id, "symbol": position.symbol, "side": position.side.value, "amount_usdt": position.amount_usdt, "entry_price": position.entry_price, "current_price": position.current_price, "unrealized_pnl_usdt": position.unrealized_pnl_usdt, "stop_loss_price": position.stop_loss_price, "take_profit_price": position.take_profit_price, "opened_at": position.opened_at, "updated_at": position.updated_at, "strategy_id": position.strategy_id, "user_id": position.user_id}
            )
            session.commit()
        return position

    def _update_performance_metrics(self, pnl: float, trade_duration: timedelta):
        """Update performance metrics after a trade is closed."""
        self.performance_metrics['total_trades'] += 1
        
        if pnl > 0:
            self.performance_metrics['winning_trades'] += 1
            self.performance_metrics['gross_pnl_usdt'] += pnl
            if pnl > self.performance_metrics['best_trade_usdt']:
                self.performance_metrics['best_trade_usdt'] = pnl
            self.performance_metrics['current_streak'] = max(1, self.performance_metrics['current_streak'] + 1)
            self.performance_metrics['max_winning_streak'] = max(self.performance_metrics['max_winning_streak'], self.performance_metrics['current_streak'])
        else:
            self.performance_metrics['losing_trades'] += 1
            self.performance_metrics['gross_pnl_usdt'] += pnl # pnl is negative
            if pnl < self.performance_metrics['worst_trade_usdt']:
                self.performance_metrics['worst_trade_usdt'] = pnl
            self.performance_metrics['current_streak'] = min(-1, self.performance_metrics['current_streak'] - 1)
            self.performance_metrics['max_losing_streak'] = min(self.performance_metrics['max_losing_streak'], self.performance_metrics['current_streak'])

        self.performance_metrics['net_pnl_usdt'] = self.performance_metrics['gross_pnl_usdt'] - self.performance_metrics['total_fees_usdt']

        if self.performance_metrics['total_trades'] > 0:
            self.performance_metrics['win_rate_percentage'] = (self.performance_metrics['winning_trades'] / self.performance_metrics['total_trades']) * 100

        total_losses = self.performance_metrics['gross_pnl_usdt'] if self.performance_metrics['gross_pnl_usdt'] < 0 else 0
        if total_losses < 0:
            self.performance_metrics['profit_factor'] = abs(self.performance_metrics['gross_pnl_usdt'] / total_losses)
        else:
            self.performance_metrics['profit_factor'] = float('inf') # Infinite profit factor if no losses

        # Simplified Sharpe Ratio, assuming risk-free rate is 0
        returns = [pnl] # In a real scenario, you would have a list of returns
        if len(returns) > 1 and np.std(returns) > 0:
            self.performance_metrics['sharpe_ratio'] = np.mean(returns) / np.std(returns) * np.sqrt(252) # Annualized

        # Update average trade duration
        total_seconds = self.performance_metrics['average_trade_duration'].total_seconds() * (self.performance_metrics['total_trades'] - 1)
        new_total_seconds = total_seconds + trade_duration.total_seconds()
        self.performance_metrics['average_trade_duration'] = timedelta(seconds=new_total_seconds / self.performance_metrics['total_trades'])

    def _monitor_positions(self):
        """Monitor active positions for stop-loss and take-profit."""
        for position_id, position in list(self.active_positions.items()):
            market_data = self._get_market_data(position.symbol)
            if not market_data:
                continue

            position.current_price = market_data.price
            position.unrealized_pnl_usdt = (position.current_price - position.entry_price) * (position.amount_usdt / position.entry_price)
            position.updated_at = datetime.utcnow()

            # Check for stop-loss or take-profit
            if position.unrealized_pnl_usdt >= (position.take_profit_price - position.entry_price) * (position.amount_usdt / position.entry_price) or \
               position.unrealized_pnl_usdt <= (position.stop_loss_price - position.entry_price) * (position.amount_usdt / position.entry_price):
                # Close position (mock implementation)
                logger.info(f"Closing position {position_id} for {position.symbol}")
                del self.active_positions[position_id]
                if self.on_position_closed:
                    self.on_position_closed(position)

                # In a real implementation, you would execute a closing trade
                # and update the database

if __name__ == '__main__':
    # Example usage
    engine = TradingEngineUSDT()
    engine.start_trading()
    opportunities = engine.scan_market_opportunities()
    print(opportunities)
    engine.stop_trading()

