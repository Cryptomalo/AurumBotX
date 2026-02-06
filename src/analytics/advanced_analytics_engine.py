# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List

class AdvancedAnalyticsEngine:
    """
    Engine for calculating advanced trading analytics and performance metrics 
    from the historical trade data stored in the SQLite database.
    """

    def __init__(self, db_path: str = "data/trading_engine.db"):
        self.db_path = db_path
        self.conn = None
        self.df_trades = None
        self.df_metrics = None

    def _connect_db(self):
        """Establishes a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.conn = None

    def _load_data(self):
        """Loads trade data from the database into a pandas DataFrame."""
        if not self.conn:
            self._connect_db()
        
        if self.conn:
            try:
                self.df_trades = pd.read_sql_query("SELECT * FROM trades WHERE status = 'CLOSED'", self.conn)
                self.df_trades['close_time'] = pd.to_datetime(self.df_trades['close_time'])
                self.df_trades['profit_usdt'] = self.df_trades['profit_usdt'].astype(float)
                self.df_trades['duration_minutes'] = (self.df_trades['close_time'] - pd.to_datetime(self.df_trades['open_time'])).dt.total_seconds() / 60
            except Exception as e:
                print(f"Error loading data: {e}")
                self.df_trades = pd.DataFrame()
        else:
            self.df_trades = pd.DataFrame()

    def calculate_metrics(self, initial_capital: float = 1000.0) -> Dict[str, Any]:
        """Calculates a comprehensive set of performance metrics."""
        self._load_data()

        if self.df_trades.empty:
            return {"error": "No closed trades found or data loading failed."}

        # 1. Basic Metrics
        total_trades = len(self.df_trades)
        winning_trades = len(self.df_trades[self.df_trades['profit_usdt'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_profit = self.df_trades['profit_usdt'].sum()
        
        # 2. Profitability Metrics
        gross_profit = self.df_trades[self.df_trades['profit_usdt'] > 0]['profit_usdt'].sum()
        gross_loss = self.df_trades[self.df_trades['profit_usdt'] <= 0]['profit_usdt'].sum()
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else np.inf
        
        avg_profit_per_trade = total_profit / total_trades if total_trades > 0 else 0
        avg_win = self.df_trades[self.df_trades['profit_usdt'] > 0]['profit_usdt'].mean()
        avg_loss = self.df_trades[self.df_trades['profit_usdt'] <= 0]['profit_usdt'].mean()
        
        # 3. Drawdown and Risk Metrics
        self.df_trades['cumulative_profit'] = self.df_trades['profit_usdt'].cumsum()
        self.df_trades['cumulative_balance'] = initial_capital + self.df_trades['cumulative_profit']
        self.df_trades['peak'] = self.df_trades['cumulative_balance'].cummax()
        self.df_trades['drawdown'] = self.df_trades['cumulative_balance'] - self.df_trades['peak']
        
        max_drawdown = self.df_trades['drawdown'].min()
        max_drawdown_percent = abs(max_drawdown / initial_capital) * 100
        
        # 4. Time-based Metrics (for Sharpe Ratio)
        # Assuming daily returns for simplicity, need to resample the data
        if total_trades > 0:
            returns = self.df_trades.set_index('close_time')['profit_usdt'] / initial_capital
            daily_returns = returns.resample('D').sum().fillna(0)
            
            # Annualized Sharpe Ratio (assuming 252 trading days)
            risk_free_rate = 0.02 # 2% annual risk-free rate
            daily_risk_free_rate = (1 + risk_free_rate)**(1/252) - 1
            
            excess_returns = daily_returns - daily_risk_free_rate
            
            if excess_returns.std() != 0:
                sharpe_ratio = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
            else:
                sharpe_ratio = np.inf
        else:
            sharpe_ratio = 0
            
        # 5. Other Metrics
        avg_duration = self.df_trades['duration_minutes'].mean()
        
        metrics = {
            "initial_capital": initial_capital,
            "final_balance": self.df_trades['cumulative_balance'].iloc[-1] if not self.df_trades.empty else initial_capital,
            "total_profit_usdt": round(total_profit, 2),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate * 100, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != np.inf else "Inf",
            "sharpe_ratio": round(sharpe_ratio, 2) if sharpe_ratio != np.inf else "Inf",
            "max_drawdown_usdt": round(max_drawdown, 2),
            "max_drawdown_percent": round(max_drawdown_percent, 2),
            "average_profit_per_trade": round(avg_profit_per_trade, 2),
            "average_win_usdt": round(avg_win, 2) if not pd.isna(avg_win) else 0,
            "average_loss_usdt": round(avg_loss, 2) if not pd.isna(avg_loss) else 0,
            "average_trade_duration_minutes": round(avg_duration, 2) if not pd.isna(avg_duration) else 0,
        }
        
        return metrics

    def get_cumulative_balance_data(self) -> List[Dict[str, Any]]:
        """Returns cumulative balance data for plotting."""
        if self.df_trades is None or self.df_trades.empty:
            self._load_data()
        
        if self.df_trades.empty:
            return []

        # Ensure cumulative balance is calculated
        if 'cumulative_balance' not in self.df_trades.columns:
            self.calculate_metrics()

        plot_data = self.df_trades[['close_time', 'cumulative_balance']].copy()
        plot_data['close_time'] = plot_data['close_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return plot_data.to_dict('records')

if __name__ == "__main__":
    # Example Usage (requires a trading_engine.db with a 'trades' table)
    # The database file is in /home/ubuntu/AurumBotX/data/trading_engine.db
    
    # Create a dummy database for testing if it doesn't exist
    db_path = "/home/ubuntu/AurumBotX/data/trading_engine.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create dummy data if the database is empty or doesn't exist
    if not os.path.exists(db_path) or os.path.getsize(db_path) < 100:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                open_time TEXT,
                close_time TEXT,
                profit_usdt REAL,
                status TEXT
            )
        """)
        
        # Insert some dummy trades (5 wins, 5 losses)
        start_time = datetime.now() - timedelta(days=10)
        trades_data = []
        for i in range(10):
            open_time = start_time + timedelta(hours=i*2)
            close_time = open_time + timedelta(minutes=30)
            profit = 50.0 if i % 2 == 0 else -25.0 # Alternating win/loss
            trades_data.append((
                f"BTCUSDT_{i}",
                open_time.isoformat(),
                close_time.isoformat(),
                profit,
                "CLOSED"
            ))
            
        cursor.executemany("INSERT INTO trades (symbol, open_time, close_time, profit_usdt, status) VALUES (?, ?, ?, ?, ?)", trades_data)
        conn.commit()
        conn.close()

    analytics = AdvancedAnalyticsEngine(db_path)
    metrics = analytics.calculate_metrics(initial_capital=1000.0)
    
    print("--- Advanced Performance Metrics ---")
    print(json.dumps(metrics, indent=4))
    
    # Example of plotting data structure
    # balance_data = analytics.get_cumulative_balance_data()
    # print("\n--- Cumulative Balance Data Sample ---")
    # print(json.dumps(balance_data[:5], indent=4))

