import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import traceback
import threading
import time
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.trading_bot import TradingBot
from utils.simulator import TradingSimulator
from utils.auto_trader import AutoTrader
from utils.database import get_db, SimulationResult
from utils.notifications import TradingNotifier

# Dictionary to store running bots
running_bots = {}

def start_bot(symbol, initial_balance, strategies=None):
    """Start a trading bot in a separate thread"""
    if symbol in running_bots:
        st.error(f"Bot already running for {symbol}")
        return

    bot = AutoTrader(symbol, initial_balance)

    # Activate selected strategies
    if strategies:
        for strategy_name in strategies:
            if strategy_name in bot.strategies:
                bot.strategies[strategy_name].activate()

    thread = threading.Thread(target=bot.run)
    thread.daemon = True
    thread.start()

    running_bots[symbol] = {
        'bot': bot,
        'thread': thread,
        'start_time': datetime.now(),
        'active_strategies': strategies
    }

def stop_bot(symbol):
    """Stop a running trading bot"""
    if symbol in running_bots:
        del running_bots[symbol]
        st.success(f"Bot stopped for {symbol}")

# Page config
st.set_page_config(
    page_title="Crypto Trading AI Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    # Load custom CSS
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    # Initialize components
    data_loader = CryptoDataLoader()
    indicators = TechnicalIndicators()
    trading_bot = TradingBot()
    simulator = TradingSimulator()

    # Sidebar
    st.sidebar.title("Configuration")
    selected_coin = st.sidebar.selectbox(
        "Select Cryptocurrency",
        options=list(data_loader.supported_coins.keys()),
        format_func=lambda x: data_loader.supported_coins[x]
    )

    timeframe = st.sidebar.selectbox(
        "Select Timeframe",
        options=['1mo', '3mo', '6mo', '1y'],
        index=2
    )

    # Main content
    st.title("Crypto Trading AI Platform")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Market Analysis", "Trading Strategies", "Auto Trading"])

    with tab1:
        # Load and prepare data
        with st.spinner('Loading data...'):
            df = data_loader.get_historical_data(selected_coin, timeframe)

        if df is not None and not df.empty:
            # Add technical indicators
            df = indicators.add_sma(df)
            df = indicators.add_rsi(df)
            df = indicators.add_macd(df)

            # Current price metrics
            col1, col2, col3, col4 = st.columns(4)
            current_price = df['Close'].iloc[-1]
            price_change = (df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1)

            with col1:
                st.metric("Current Price", f"${current_price:.2f}", f"{price_change:.2%}")
            with col2:
                st.metric("24h Volume", f"${df['Volume'].iloc[-1]:,.0f}")
            with col3:
                st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
            with col4:
                st.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")

            # Price chart
            st.subheader("Price Chart with Indicators")
            fig = go.Figure()

            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price'
            ))

            # Add SMA
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['SMA_20'],
                name='SMA 20',
                line=dict(color='orange')
            ))

            # Add MACD
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MACD'],
                name='MACD',
                line=dict(color='blue')
            ))

            fig.update_layout(
                height=600,
                template='plotly_white',
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Trading Strategies Configuration")

        # Strategy selection
        st.write("Select strategies to activate:")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("### Meme Coin Sniping")
            use_meme = st.checkbox("Enable Meme Coin Strategy")
            if use_meme:
                st.slider("Sentiment Threshold", 0.0, 1.0, 0.7, key="meme_sentiment")
                st.slider("Min Liquidity (USD)", 50000, 500000, 100000, step=50000, key="meme_liquidity")

        with col2:
            st.write("### Scalping Strategy")
            use_scalping = st.checkbox("Enable Scalping Strategy")
            if use_scalping:
                st.slider("Volume Threshold", 500000, 5000000, 1000000, step=500000, key="scalp_volume")
                st.slider("Profit Target (%)", 0.1, 2.0, 0.5, 0.1, key="scalp_target")

        with col3:
            st.write("### Swing Trading")
            use_swing = st.checkbox("Enable Swing Trading")
            if use_swing:
                st.slider("Trend Period (days)", 10, 50, 20, key="swing_period")
                st.slider("Profit Target (%)", 5.0, 30.0, 15.0, 1.0, key="swing_target")

        # Strategy simulation
        if st.button("Run Strategy Simulation"):
            try:
                with st.spinner("Running trading simulation..."):
                    # Train bot and get predictions
                    trading_bot.train(df)
                    predictions = trading_bot.predict(df)

                    # Run simulation
                    portfolio = simulator.simulate_strategy(df, predictions)
                    metrics = simulator.calculate_metrics(portfolio)

                    # Save simulation results
                    simulator.save_simulation_results(
                        symbol=selected_coin,
                        metrics=metrics,
                        start_date=df.index[0],
                        end_date=df.index[-1]
                    )

                    # Display metrics
                    st.subheader("Simulation Results")
                    cols = st.columns(4)
                    cols[0].metric("Total Return", f"{metrics['Total Return']:.2%}")
                    cols[1].metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
                    cols[2].metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
                    cols[3].metric("Win Rate", f"{metrics['Win Rate']:.2%}")

                    # Portfolio performance chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=portfolio.index,
                        y=portfolio['Holdings'],
                        name='Portfolio Value',
                        line=dict(color='green')
                    ))
                    fig.update_layout(
                        height=400,
                        template='plotly_white',
                        title='Portfolio Performance'
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error during simulation: {str(e)}")
                st.code(traceback.format_exc())

    with tab3:
        st.subheader("Automated Trading Bot")

        # Bot configuration
        col1, col2 = st.columns(2)
        with col1:
            initial_balance = st.number_input(
                "Initial Balance ($)",
                min_value=100,
                value=10000,
                step=100
            )

        # Get active strategies
        active_strategies = []
        if use_meme:
            active_strategies.append('meme_coin')
        if use_scalping:
            active_strategies.append('scalping')
        if use_swing:
            active_strategies.append('swing')

        with col2:
            if selected_coin in running_bots:
                if st.button("Stop Bot"):
                    stop_bot(selected_coin)
            else:
                if st.button("Start Bot"):
                    if not active_strategies:
                        st.warning("Please select at least one trading strategy")
                    else:
                        start_bot(selected_coin, initial_balance, active_strategies)

        # Bot status and monitoring
        st.subheader("Active Bots")
        if running_bots:
            # Create monitoring dashboard
            monitor_cols = st.columns(3)

            for symbol, bot_info in running_bots.items():
                bot = bot_info['bot']
                runtime = datetime.now() - bot_info['start_time']

                # Performance metrics
                with monitor_cols[0]:
                    st.metric("Total Return", f"{((bot.balance / bot.initial_balance) - 1):.2%}")
                    st.metric("Active Time", f"{runtime.seconds // 3600}h {(runtime.seconds % 3600) // 60}m")

                # Strategy status
                with monitor_cols[1]:
                    st.write("Active Strategies:")
                    for strategy in bot_info['active_strategies']:
                        st.write(f"- {strategy.replace('_', ' ').title()}")

                # Current positions
                with monitor_cols[2]:
                    st.write("Current Position:")
                    if bot.current_position:
                        st.write(f"Entry Price: ${bot.current_position['entry_price']:.2f}")
                        st.write(f"Size: {bot.current_position['size']:.6f}")
                        st.write(f"Strategy: {bot.current_position['strategy']}")
                    else:
                        st.write("No active position")

            # Show recent logs
            if st.checkbox("Show Recent Logs"):
                try:
                    with open(f'trading_log_{selected_coin}_{datetime.now().strftime("%Y%m%d")}.log', 'r') as f:
                        logs = f.readlines()[-20:]  # Show last 20 lines
                        st.code('\n'.join(logs))
                except FileNotFoundError:
                    st.info("No logs available yet")
        else:
            st.info("No active trading bots")

        # Historical performance
        st.subheader("Historical Performance")
        try:
            db = next(get_db())
            historical_sims = (
                db.query(SimulationResult)
                .filter_by(symbol=selected_coin)
                .order_by(SimulationResult.created_at.desc())
                .limit(5)
                .all()
            )

            if historical_sims:
                hist_data = []
                for sim in historical_sims:
                    hist_data.append({
                        'Date': sim.created_at.strftime('%Y-%m-%d %H:%M'),
                        'Total Return': f"{((sim.final_balance / sim.initial_balance) - 1):.2%}",
                        'Sharpe Ratio': f"{sim.sharpe_ratio:.2f}",
                        'Win Rate': f"{sim.win_rate:.2%}"
                    })
                st.dataframe(pd.DataFrame(hist_data))
            else:
                st.info("No historical simulations found for this cryptocurrency")

        except Exception as e:
            st.error(f"Error loading historical performance: {str(e)}")

except Exception as e:
    st.error(f"An unexpected error occurred: {str(e)}")
    st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown("*Disclaimer: This is a simulation platform. Do not use for actual trading without proper risk management.*")