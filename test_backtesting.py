import logging
from datetime import datetime, timedelta
from utils.backtesting import Backtester
from utils.strategies.scalping import ScalpingStrategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize strategy with test configuration
    strategy = ScalpingStrategy({
        'volume_threshold': 1000000,
        'min_volatility': 0.002,
        'profit_target': 0.005,
        'initial_stop_loss': 0.003,
        'trailing_stop': 0.002,
        'testnet': True
    })
    
    # Set up backtester
    symbol = "BTC-USDT"
    initial_balance = 10000
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    backtester = Backtester(
        symbol=symbol,
        strategy=strategy,
        initial_balance=initial_balance,
        start_date=start_date,
        end_date=end_date
    )
    
    # Run backtest
    try:
        results = backtester.run_backtest()
        
        # Print results
        print("\nBacktest Results:")
        print(f"Strategy: {results.strategy_name}")
        print(f"Symbol: {results.symbol}")
        print(f"Period: {results.start_date} to {results.end_date}")
        print(f"Initial Balance: ${results.initial_balance:,.2f}")
        print(f"Final Balance: ${results.final_balance:,.2f}")
        print(f"Total Profit/Loss: ${results.profit_loss:,.2f}")
        print(f"Win Rate: {results.win_rate:.2%}")
        print(f"Total Trades: {results.total_trades}")
        print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {results.max_drawdown:.2%}")
        
    except Exception as e:
        logger.error(f"Backtesting error: {str(e)}")

if __name__ == "__main__":
    main()
