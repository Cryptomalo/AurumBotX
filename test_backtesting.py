import logging
from datetime import datetime, timedelta
import asyncio
from utils.backtesting import Backtester
from utils.strategies.scalping import ScalpingStrategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Initialize strategy with test configuration
    strategy = ScalpingStrategy({
        'volume_threshold': 500000,  # Ridotto per avere più segnali
        'min_volatility': 0.001,    # Ridotto al 0.1%
        'profit_target': 0.003,     # Target profit al 0.3%
        'initial_stop_loss': 0.002, # Stop loss al 0.2%
        'trailing_stop': 0.001,     # Trailing stop al 0.1%
        'testnet': True
    })

    # Set up backtester with longer timeframe
    symbol = "BTC-USDT"
    initial_balance = 10000
    start_date = datetime.now() - timedelta(days=7)  # Ridotto a 7 giorni per test più precisi
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
        results = await backtester.run_backtest()

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

        # Additional performance metrics
        print("\nPerformance Metrics:")
        for metric, value in results.performance_metrics.items():
            print(f"{metric}: {value:.2f}")

    except Exception as e:
        logger.error(f"Backtesting error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())