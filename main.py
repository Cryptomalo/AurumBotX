import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from utils.data_loader import CryptoDataLoader
from utils.indicators import TechnicalIndicators
from utils.trading_bot import TradingBot
from utils.simulator import TradingSimulator
from utils.database import get_db, SimulationResult

# Page config
st.set_page_config(page_title="Crypto Trading AI Platform", layout="wide")

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

# Load and prepare data
df = data_loader.get_historical_data(selected_coin, timeframe)
if df is not None:
    # Add technical indicators
    df = indicators.add_sma(df)
    df = indicators.add_ema(df)
    df = indicators.add_rsi(df)
    df = indicators.add_macd(df)

    # Current price metrics
    col1, col2, col3 = st.columns(3)
    current_price = df['Close'].iloc[-1]
    price_change = (df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1)

    with col1:
        st.metric("Current Price", f"${current_price:.2f}", 
                 f"{price_change:.2%}")
    with col2:
        st.metric("24h Volume", f"${df['Volume'].iloc[-1]:,.0f}")
    with col3:
        st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")

    # Price chart
    st.subheader("Price Chart")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        high=df['High'],
        low=df['Low'],
        open=df['Open'],
        close=df['Close'],
        name='Price'
    ))
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA_20'],
        name='SMA 20',
        line=dict(color='orange')
    ))
    fig.update_layout(
        height=600,
        template='plotly_white',
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # Trading Simulator
    st.subheader("Trading Simulator")
    if st.button("Run Simulation"):
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

    # Historical Simulations
    st.subheader("Historical Simulations")
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

else:
    st.error("Error loading data. Please try again later.")

# Footer
st.markdown("---")
st.markdown("*Disclaimer: This is a simulation platform. Do not use for actual trading without proper risk management.*")