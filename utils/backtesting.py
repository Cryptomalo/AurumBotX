import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

@dataclass
class BacktestResult:
    """Data class to store backtest results"""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_loss: float
    max_drawdown: float
    sharpe_ratio: float
    trades_history: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]

class Backtester:
    def __init__(self, 
                 symbol: str,
                 strategy: BaseStrategy,
                 initial_balance: float = 10000,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None):
        """Initialize backtester with trading parameters"""
        self.symbol = symbol
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.start_date = start_date or (datetime.now() - timedelta(days=30))
        self.end_date = end_date or datetime.now()

        self.data_loader = CryptoDataLoader()
        self.indicators = TechnicalIndicators()

        # Performance tracking
        self.balance = initial_balance
        self.trades_history = []
        self.current_position = None

    async def run_backtest(self) -> BacktestResult:
        """Execute backtest and return results"""
        try:
            # Load historical data
            df = self.data_loader.get_historical_data(
                self.symbol,
                period='1d',
                interval='1m'
            )

            if df is None or df.empty:
                raise ValueError("No historical data available")

            # Add technical indicators
            df = self.indicators.add_all_indicators(df)

            # Prepare market data for analysis
            df['high_volume'] = df['Volume'] > df['Volume'].rolling(window=24).mean()

            # Main backtesting loop
            position_open = False
            entry_price = 0.0
            position_size = 0.0

            for timestamp, row in df.iterrows():
                # Skip data outside our date range
                if timestamp < self.start_date or timestamp > self.end_date:
                    continue

                current_price = row['Close']

                # Prepare market data for analysis
                market_data = df.loc[:timestamp].copy()

                # Generate trading signals
                analysis = await self.strategy.analyze_market(market_data)
                if analysis and isinstance(analysis, list):
                    analysis = analysis[0]  # Take first analysis result

                if analysis:
                    signal = self.strategy.generate_signals(analysis)
                else:
                    signal = None

                if signal and not position_open and signal['action'].lower() == 'buy':
                    position_size = self.balance * 0.1  # Use 10% of balance per trade
                    entry_price = current_price
                    position_open = True

                    self.trades_history.append({
                        'timestamp': timestamp,
                        'action': 'BUY',
                        'price': current_price,
                        'size': position_size,
                        'balance': self.balance
                    })

                elif position_open:
                    should_sell = False
                    if signal:
                        should_sell = signal['action'].lower() == 'sell'

                    # Add take profit and stop loss checks
                    take_profit_hit = current_price >= entry_price * 1.02  # 2% profit target
                    stop_loss_hit = current_price <= entry_price * 0.99   # 1% stop loss

                    if should_sell or take_profit_hit or stop_loss_hit:
                        profit_loss = (current_price - entry_price) * position_size
                        self.balance += profit_loss
                        position_open = False

                        self.trades_history.append({
                            'timestamp': timestamp,
                            'action': 'SELL',
                            'price': current_price,
                            'size': position_size,
                            'profit_loss': profit_loss,
                            'balance': self.balance
                        })

            # Calculate performance metrics
            return self._calculate_results()

        except Exception as e:
            logger.error(f"Backtesting error: {str(e)}")
            raise

    def _calculate_results(self) -> BacktestResult:
        """Calculate performance metrics from trade history"""
        if not self.trades_history:
            raise ValueError("No trades executed during backtest")

        winning_trades = sum(1 for trade in self.trades_history 
                           if trade.get('profit_loss', 0) > 0)
        total_trades = len([t for t in self.trades_history if t['action'] == 'SELL'])

        # Calculate daily returns for Sharpe ratio
        daily_returns = []
        current_day = None
        day_start_balance = self.initial_balance

        for trade in self.trades_history:
            trade_day = trade['timestamp'].date()
            if current_day != trade_day:
                if current_day is not None:
                    daily_return = (trade['balance'] - day_start_balance) / day_start_balance
                    daily_returns.append(daily_return)
                current_day = trade_day
                day_start_balance = trade['balance']

        # Calculate metrics
        sharpe_ratio = 0
        if daily_returns:
            returns_mean = np.mean(daily_returns)
            returns_std = np.std(daily_returns)
            if returns_std > 0:
                sharpe_ratio = (returns_mean / returns_std) * np.sqrt(252)

        # Calculate maximum drawdown
        peak_balance = self.initial_balance
        max_drawdown = 0

        for trade in self.trades_history:
            balance = trade['balance']
            if balance > peak_balance:
                peak_balance = balance
            drawdown = (peak_balance - balance) / peak_balance
            max_drawdown = max(max_drawdown, drawdown)

        return BacktestResult(
            strategy_name=self.strategy.__class__.__name__,
            symbol=self.symbol,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_balance=self.initial_balance,
            final_balance=self.balance,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=total_trades - winning_trades,
            win_rate=winning_trades / total_trades if total_trades > 0 else 0,
            profit_loss=self.balance - self.initial_balance,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades_history=self.trades_history,
            performance_metrics={
                'profit_factor': self._calculate_profit_factor(),
                'average_trade': self._calculate_average_trade(),
                'max_consecutive_losses': self._calculate_max_consecutive_losses()
            }
        )

    def _calculate_profit_factor(self) -> float:
        """Calculate the profit factor (gross profit / gross loss)"""
        gross_profit = sum(t.get('profit_loss', 0) for t in self.trades_history 
                         if t.get('profit_loss', 0) > 0)
        gross_loss = abs(sum(t.get('profit_loss', 0) for t in self.trades_history 
                           if t.get('profit_loss', 0) < 0))
        return gross_profit / gross_loss if gross_loss > 0 else 0

    def _calculate_average_trade(self) -> float:
        """Calculate the average profit/loss per trade"""
        profits = [t.get('profit_loss', 0) for t in self.trades_history 
                  if 'profit_loss' in t]
        return np.mean(profits) if profits else 0

    def _calculate_max_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losing trades"""
        current_streak = 0
        max_streak = 0

        for trade in self.trades_history:
            if trade.get('profit_loss', 0) < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak