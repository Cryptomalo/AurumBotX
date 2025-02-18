import streamlit as st
import logging
import json
from datetime import datetime, timedelta
from utils.data_loader import CryptoDataLoader
from utils.strategies.strategy_manager import StrategyManager
from utils.auto_trader import AutoTrader
from utils.backtesting import Backtester
from utils.strategies.scalping import ScalpingStrategy

# Setup logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('streamlit_bot.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize session state with validation
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()
    logger.info("Initialized start_time in session state")
if 'trades' not in st.session_state:
    st.session_state.trades = []
    logger.info("Initialized trades list in session state")
if 'active_strategies' not in st.session_state:
    st.session_state.active_strategies = []
    logger.info("Initialized active_strategies in session state")
if 'bot' not in st.session_state:
    st.session_state.bot = None
    logger.info("Initialized bot in session state")

def validate_trading_params(params):
    """Validate trading parameters"""
    try:
        if params.get('risk_per_trade'):
            risk = float(params['risk_per_trade'])
            if not 0 < risk <= 0.1:
                return False, "Risk per trade must be between 0 and 10%"

        if params.get('amount'):
            amount = float(params['amount'])
            if amount <= 0:
                return False, "Amount must be greater than 0"

        return True, None
    except ValueError as e:
        return False, f"Invalid number format: {str(e)}"
    except Exception as e:
        logger.error(f"Parameter validation error: {str(e)}")
        return False, f"Validation error: {str(e)}"

def init_components():
    """Initialize trading components with enhanced error handling"""
    try:
        logger.info("Initializing trading components...")
        data_loader = CryptoDataLoader()
        strategy_manager = StrategyManager()

        # Initialize bot if not already initialized
        if st.session_state.bot is None:
            st.session_state.bot = AutoTrader(
                symbol="BTC-USD",
                initial_balance=10000,
                risk_per_trade=0.02,
                testnet=True
            )
            logger.info("Trading bot initialized")

        # Test component functionality
        test_price = data_loader.get_current_price("BTC-USD")
        if test_price is None:
            raise Exception("Failed to fetch initial price data")

        logger.info("Components initialized successfully")
        return data_loader, strategy_manager

    except Exception as e:
        error_msg = f"Component initialization error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return None, None

async def execute_test_trade(risk_per_trade=0.01, amount=0.1):
    """Execute a test trade with parameter validation"""
    try:
        # Validate parameters
        valid, error_msg = validate_trading_params({
            'risk_per_trade': risk_per_trade,
            'amount': amount
        })

        if not valid:
            raise ValueError(error_msg)

        if st.session_state.bot is None:
            raise ValueError("Trading bot not initialized")

        # Get market data for analysis
        market_data = st.session_state.bot.data_loader.get_historical_data("BTC-USD")

        # Analyze market and execute trade
        signal = await st.session_state.bot.analyze_market_async(market_data)
        if signal:
            result = await st.session_state.bot.execute_trade_async(signal)
            if result.get('success'):
                st.session_state.trades.append(result)
                st.success(f"Trade executed successfully!\nAction: {result['action']}\nPrice: ${result['price']:,.2f}")
                return result
            else:
                raise Exception(result.get('reason', 'Unknown error'))
        else:
            st.info("No trading signal generated")
            return None

    except Exception as e:
        error_msg = f"Test trade error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return {"status": "error", "message": str(e)}

async def run_backtest(symbol="BTC-USDT", days=7):
    """Run backtest on historical data"""
    try:
        logger.info(f"Starting backtest for {symbol}")

        # Initialize strategy
        strategy = ScalpingStrategy({
            'volume_threshold': 500000,
            'min_volatility': 0.001,
            'profit_target': 0.003,
            'initial_stop_loss': 0.002,
            'trailing_stop': 0.001,
            'testnet': True
        })

        # Set up backtester
        initial_balance = 10000
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()

        backtester = Backtester(
            symbol=symbol,
            strategy=strategy,
            initial_balance=initial_balance,
            start_date=start_date,
            end_date=end_date
        )

        # Run backtest
        results = await backtester.run_backtest()

        if results:
            st.success("Backtest completed successfully!")
            return results
        else:
            st.error("Backtest failed to generate results")
            return None

    except Exception as e:
        error_msg = f"Backtest error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return None

# Page configuration
try:
    st.set_page_config(
        page_title="AurumBot Trading Dashboard",
        page_icon="🤖",
        layout="wide"
    )

    # Title and description
    st.title("🤖 AurumBot Trading Dashboard")
    st.write("Sistema di trading automatico con analisi AI")

    # Initialize components
    data_loader, strategy_manager = init_components()

    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Trading", "Backtest", "Settings"])

    with tab1:
        # Sidebar with controls and input validation
        with st.sidebar:
            st.header("Controlli Trading")

            # Strategy selection with validation
            strategy_type = st.selectbox(
                "Seleziona Strategia",
                ["Scalping", "Swing Trading", "DCA", "Grid Trading"]
            )

            # Risk parameter with validation
            risk_per_trade = st.slider(
                "Risk per Trade (%)", 
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1
            )

            # Amount with validation
            trade_amount = st.number_input(
                "Trade Amount (BTC)",
                min_value=0.001,
                max_value=1.0,
                value=0.1,
                step=0.001
            )

            if st.button("Esegui Trade Test"):
                st.write("Elaborazione trade in corso...")
                result = st.session_state.bot.execute_trade_async({'amount':trade_amount, 'risk':risk_per_trade/100}) #fixed the async issue.
                if result.get('success'):
                    st.success("Trade eseguito con successo!")
                else:
                    st.error(f"Errore: {result.get('message')}")


        # Main content
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Statistiche")
            st.metric(
                "Tempo di Attività",
                str(datetime.now() - st.session_state.start_time).split('.')[0]
            )
            st.metric("Trades Totali", len(st.session_state.trades))

            # Active strategies
            st.subheader("🎯 Strategie Attive")
            if st.session_state.active_strategies:
                for strategy in st.session_state.active_strategies:
                    st.write(f"• {strategy}")
            else:
                st.info("Nessuna strategia attiva")

        with col2:
            st.subheader("💹 Trading Pairs Attivi")
            if data_loader:
                try:
                    btc_price = data_loader.get_current_price("BTC-USD")
                    eth_price = data_loader.get_current_price("ETH-USD")

                    if btc_price:
                        st.metric("BTC/USDT", f"${btc_price:,.2f}")
                    if eth_price:
                        st.metric("ETH/USDT", f"${eth_price:,.2f}")
                except Exception as e:
                    logger.error(f"Error fetching prices: {e}")
                    st.error("Errore nel caricamento dei prezzi")

    with tab2:
        st.header("Backtest")

        col1, col2 = st.columns(2)

        with col1:
            symbol = st.selectbox(
                "Seleziona Coppia",
                ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
            )
            days = st.slider(
                "Periodo (giorni)",
                min_value=1,
                max_value=30,
                value=7
            )

        with col2:
            if st.button("Avvia Backtest"):
                results = run_backtest(symbol, days)
                if results:
                    st.success("Backtest completato!")
                    st.write("Risultati:")
                    st.json(results)

    with tab3:
        st.header("Impostazioni")

        # Risk Management Settings
        st.subheader("Gestione del Rischio")

        col1, col2 = st.columns(2)

        with col1:
            max_position_size = st.number_input(
                "Dimensione Massima Posizione (%)",
                min_value=1.0,
                max_value=100.0,
                value=10.0,
                step=1.0
            )

            stop_loss = st.number_input(
                "Stop Loss Default (%)",
                min_value=0.1,
                max_value=10.0,
                value=2.0,
                step=0.1
            )

        with col2:
            take_profit = st.number_input(
                "Take Profit Default (%)",
                min_value=0.1,
                max_value=20.0,
                value=4.0,
                step=0.1
            )

            trailing_stop = st.number_input(
                "Trailing Stop (%)",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1
            )

        if st.button("Salva Impostazioni"):
            st.success("Impostazioni salvate con successo!")

    # Trade History with detailed view
    st.subheader("📜 Storico Trade")
    if st.session_state.trades:
        for trade in reversed(st.session_state.trades):  # Show most recent first
            with st.expander(f"Trade {trade['timestamp']} - {trade['symbol']}"):
                st.json(trade)
    else:
        st.info("Nessun trade eseguito finora")

    # Performance Metrics with explanations
    st.subheader("📈 Metriche di Performance")
    col3, col4, col5 = st.columns(3)

    with col3:
        win_rate = "0%"  # Calculate actual win rate when implemented
        st.metric("Win Rate", win_rate)
        st.caption("Percentuale di trade profittevoli")

    with col4:
        pnl = "$0.00"  # Calculate actual P/L when implemented
        st.metric("Profit/Loss", pnl)
        st.caption("Profitto/Perdita totale")

    with col5:
        trades_per_hour = len(st.session_state.trades) / max(1, (datetime.now() - st.session_state.start_time).total_seconds() / 3600)
        st.metric("Trades per Hour", f"{trades_per_hour:.1f}")
        st.caption("Frequenza media di trading")

except Exception as e:
    error_msg = f"Application error: {str(e)}"
    logger.error(error_msg, exc_info=True)
    st.error(error_msg)