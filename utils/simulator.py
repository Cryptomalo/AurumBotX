import pandas as pd
import numpy as np

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
        
        metrics = {
            'Total Return': f"{total_return:.2%}",
            'Sharpe Ratio': f"{np.sqrt(252) * daily_returns.mean() / daily_returns.std():.2f}",
            'Max Drawdown': f"{(portfolio['Holdings'].max() - portfolio['Holdings'].min()) / portfolio['Holdings'].max():.2%}",
            'Win Rate': f"{(daily_returns > 0).mean():.2%}"
        }
        
        return metrics
