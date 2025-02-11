import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from utils.database import SimulationResult, TradingStrategy, get_db

class AdvancedBacktester:
    def __init__(self, strategy, initial_balance=10000):
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.results = []
        
    def run_backtest(self, historical_data, start_date, end_date):
        """Esegue backtest con simulazione mercato realistica"""
        balance = self.initial_balance
        positions = {}
        trades = []
        
        for timestamp, row in historical_data.iterrows():
            if start_date <= timestamp <= end_date:
                signal = self.strategy.analyze_market(historical_data[:timestamp])
                if signal and signal['action'] != 'hold':
                    trade_result = self._simulate_trade(signal, row, balance)
                    trades.append(trade_result)
                    balance = trade_result['new_balance']
                    
        return {
            'final_balance': balance,
            'total_trades': len(trades),
            'profit_factor': self._calculate_profit_factor(trades),
            'sharpe_ratio': self._calculate_sharpe_ratio(trades),
            'max_drawdown': self._calculate_max_drawdown(trades),
            'trades': trades
        }
        
    def _simulate_trade(self, signal, price_data, balance):
        """Simula trade con slippage e commissioni realistiche"""
        slippage = 0.001  # 0.1% slippage
        commission = 0.002  # 0.2% commission
        
        entry_price = price_data['Close'] * (1 + slippage)
        position_size = balance * signal['size_factor']
        commission_cost = position_size * commission
        
        return {
            'timestamp': price_data.name,
            'action': signal['action'],
            'entry_price': entry_price,
            'position_size': position_size,
            'commission': commission_cost,
            'new_balance': balance - position_size - commission_cost
        }

class TradingSimulator:
    def __init__(self, initial_balance=10000):
        self.initial_balance = initial_balance

    def simulate_strategy(self, df, predictions, threshold=0.6):
        """Simulate trading strategy based on predictions"""
        portfolio = pd.DataFrame(index=df.index)
        portfolio['Price'] = df['Close']
        portfolio['Signal'] = (predictions > threshold).astype(int)

        # Calculate positions and holdings
        portfolio['Position'] = portfolio['Signal'].diff()
        portfolio['Holdings'] = self.initial_balance
        portfolio['Shares'] = 0
        total_trades = abs(portfolio['Position']).sum()

        current_shares = 0
        current_balance = self.initial_balance

        for i in range(1, len(portfolio)):
            if portfolio['Position'].iloc[i] == 1:  # Buy
                shares_to_buy = current_balance / portfolio['Price'].iloc[i]
                current_shares = shares_to_buy
                current_balance = 0
            elif portfolio['Position'].iloc[i] == -1:  # Sell
                current_balance = current_shares * portfolio['Price'].iloc[i]
                current_shares = 0

            portfolio['Shares'].iloc[i] = current_shares
            portfolio['Holdings'].iloc[i] = current_shares * portfolio['Price'].iloc[i] + current_balance

        return portfolio

    def calculate_metrics(self, portfolio):
        """Calculate performance metrics"""
        total_return = (portfolio['Holdings'].iloc[-1] - self.initial_balance) / self.initial_balance
        daily_returns = portfolio['Holdings'].pct_change().dropna()
        win_rate = (daily_returns > 0).mean()
        sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
        max_drawdown = (portfolio['Holdings'].max() - portfolio['Holdings'].min()) / portfolio['Holdings'].max()

        metrics = {
            'Total Return': total_return,
            'Sharpe Ratio': sharpe_ratio,
            'Max Drawdown': max_drawdown,
            'Win Rate': win_rate
        }

        return metrics

    def save_simulation_results(self, symbol, metrics, start_date, end_date, strategy_name="AI Trading Strategy"):
        """Save simulation results to database"""
        db = next(get_db())

        # Get or create strategy
        strategy = db.query(TradingStrategy).filter_by(name=strategy_name).first()
        if not strategy:
            strategy = TradingStrategy(
                name=strategy_name,
                description="AI-powered trading strategy using machine learning",
                parameters="{}"
            )
            db.add(strategy)
            db.commit()
            db.refresh(strategy)

        # Create simulation result
        simulation = SimulationResult(
            strategy_id=strategy.id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=float(self.initial_balance),
            final_balance=float(self.initial_balance * (1 + metrics['Total Return'])),
            total_trades=int(total_trades),
            win_rate=float(metrics['Win Rate']),
            sharpe_ratio=float(metrics['Sharpe Ratio']),
            max_drawdown=float(metrics['Max Drawdown']),
            created_at=datetime.now(pytz.UTC)
        )

        db.add(simulation)
        db.commit()

        return simulation