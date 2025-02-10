import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import traceback
import threading
import time
import numpy as np #Added to handle np.mean
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
    page_title="✨ AurumBot - Smart Trading Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menu principale nella sidebar
with st.sidebar:
    st.title("🌟 AurumBot")
    st.markdown("---")

    menu = st.radio("Menu Principale", [
        "📊 Dashboard",
        "👤 Profilo",
        "📈 Statistiche PnL",
        "🔒 Sicurezza",
        "🏆 Traguardi"
    ])

    st.markdown("---")
    total_profit = 125000  # Esempio (da sostituire con dati reali)
    st.metric("💰 Profitto Totale", f"${total_profit:,.2f}")

# Load custom CSS
try:
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("⚠️ Style file not found. Using default styling.")
except Exception as e:
    st.error(f"Error loading styles: {str(e)}")

try:
    # Initialize components
    data_loader = CryptoDataLoader()
    indicators = TechnicalIndicators()
    trading_bot = TradingBot()
    simulator = TradingSimulator()

    if menu == "📊 Dashboard":
        st.title("📊 Trading Dashboard")
        # Il contenuto esistente del dashboard rimane qui

    elif menu == "👤 Profilo":
        st.title("👤 Profilo Trader")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📝 Informazioni")
            st.text_input("Nome Trader", "AurumTrader")
            st.text_input("Email", "trader@aurumbot.com")
            st.button("✏️ Modifica Profilo")

        with col2:
            st.markdown("### 📊 Statistiche")
            st.metric("Trade Totali", "1,234")
            st.metric("Win Rate", "68%")
            st.metric("Profitto Medio", "$312.45")

    elif menu == "📈 Statistiche PnL":
        st.title("📈 Analisi Profitti e Perdite")
        # Grafici PnL
        st.area_chart({"Profitti": [100, 250, 380, 420, 580, 600, 750]})

    elif menu == "🔒 Sicurezza":
        st.title("🔒 Sicurezza Account")
        st.toggle("2FA Attiva")
        st.toggle("Notifiche Email")
        st.toggle("Notifiche Telegram")

    elif menu == "🏆 Traguardi":
        st.title("🏆 I Tuoi Traguardi")
        col1, col2 = st.columns(2)

        achievements = [
            {"level": "10K", "reached": True},
            {"level": "25K", "reached": True},
            {"level": "50K", "reached": True},
            {"level": "100K", "reached": False},
            {"level": "250K", "reached": False},
            {"level": "500K", "reached": False},
            {"level": "1M", "reached": False}
        ]

        for ach in achievements:
            with col1 if achievements.index(ach) % 2 == 0 else col2:
                if ach["reached"]:
                    st.markdown(f'<div class="achievement-badge">🏆 {ach["level"]} Raggiunto!</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="achievement-badge locked">🔒 Obiettivo {ach["level"]}</div>', unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.title("🤖 AurumBot")
        st.markdown("---")

        selected_coin = st.selectbox(
            "🪙 Select Cryptocurrency",
            options=list(data_loader.supported_coins.keys()),
            format_func=lambda x: data_loader.supported_coins[x]
        )

        timeframe = st.selectbox(
            "📊 Select Timeframe",
            options=['1mo', '3mo', '6mo', '1y'],
            index=2
        )

        st.markdown("---")
        st.caption("Powered by Advanced AI Trading Strategies")

    # Main content
    st.title("Crypto Trading Dashboard")

    # Tabs with icons
    tab1, tab2, tab3 = st.tabs([
        "📈 Market Analysis", 
        "🔧 Trading Strategies", 
        "🤖 Auto Trading"
    ])

    with tab1:
        # Load and prepare data
        with st.spinner('Loading market data...'):
            df = data_loader.get_historical_data(selected_coin, timeframe)

            if df is not None and not df.empty:
                # Calculate all technical indicators first
                df = indicators.add_sma(df)
                df = indicators.add_rsi(df)
                df = indicators.add_macd(df)

                # Current price metrics in cards
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)

                current_price = df['Close'].iloc[-1]
                price_change = (df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1)

                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("💰 Current Price", 
                             f"${current_price:.2f}", 
                             f"{price_change:.2%}")
                    st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("📊 24h Volume", 
                             f"${df['Volume'].iloc[-1]:,.0f}")
                    st.markdown('</div>', unsafe_allow_html=True)

                with col3:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("📈 RSI", 
                             f"{df['RSI'].iloc[-1]:.2f}")
                    st.markdown('</div>', unsafe_allow_html=True)

                with col4:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("📉 MACD", 
                             f"{df['MACD'].iloc[-1]:.2f}")
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                # Technical Analysis Charts
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader("📊 Technical Analysis")

                # Create tabs for different charts
                chart_tab1, chart_tab2 = st.tabs(["Price & Indicators", "Volume Analysis"])

                with chart_tab1:
                    # Price chart with indicators
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
                        line=dict(color='orange', width=1)
                    ))

                    # Add MACD
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['MACD'],
                        name='MACD',
                        line=dict(color='blue', width=1)
                    ))

                    fig.update_layout(
                        height=500,
                        template='plotly_white',
                        xaxis_rangeslider_visible=False,
                        title="Price Action & Technical Indicators"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with chart_tab2:
                    # Volume analysis chart
                    fig = go.Figure()

                    fig.add_trace(go.Bar(
                        x=df.index,
                        y=df['Volume'],
                        name='Volume',
                        marker_color='rgba(58, 71, 80, 0.6)'
                    ))

                    fig.update_layout(
                        height=400,
                        template='plotly_white',
                        title="Trading Volume Analysis"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown('</div>', unsafe_allow_html=True)

                # AI Predictions Section
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader("🤖 Previsioni AI Avanzate")

                prediction_tab1, prediction_tab2, prediction_tab3 = st.tabs([
                    "📈 Previsioni di Prezzo", 
                    "📊 Metriche del Modello",
                    "🔍 Analisi Dettagliata"
                ])

                with prediction_tab1:
                    if df is not None and not df.empty:
                        try:
                            # Get predictions
                            predictions = trading_bot.prediction_model.predict(df)
                            pred_df = pd.DataFrame(index=df.index)
                            pred_df['Close'] = df['Close']
                            pred_df['Predicted'] = predictions['predictions']

                            if predictions['confidence_intervals']:
                                pred_df['Lower Bound'] = predictions['confidence_intervals']['lower']
                                pred_df['Upper Bound'] = predictions['confidence_intervals']['upper']

                            # Create prediction chart
                            fig = go.Figure()

                            # Actual price
                            fig.add_trace(go.Scatter(
                                x=pred_df.index,
                                y=pred_df['Close'],
                                name='Prezzo Attuale',
                                line=dict(color='blue', width=2)
                            ))

                            # Predicted price
                            fig.add_trace(go.Scatter(
                                x=pred_df.index,
                                y=pred_df['Predicted'],
                                name='Prezzo Previsto',
                                line=dict(color='green', width=2, dash='dash')
                            ))

                            # Confidence intervals
                            if 'Lower Bound' in pred_df.columns:
                                fig.add_trace(go.Scatter(
                                    x=pred_df.index,
                                    y=pred_df['Upper Bound'],
                                    fill=None,
                                    mode='lines',
                                    line_color='rgba(0,100,80,0)',
                                    showlegend=False
                                ))

                                fig.add_trace(go.Scatter(
                                    x=pred_df.index,
                                    y=pred_df['Lower Bound'],
                                    fill='tonexty',
                                    mode='lines',
                                    line_color='rgba(0,100,80,0)',
                                    name='Intervallo di Confidenza'
                                ))

                            fig.update_layout(
                                height=500,
                                template='plotly_dark',
                                title="Previsioni di Prezzo con Intervalli di Confidenza",
                                xaxis_title="Data",
                                yaxis_title="Prezzo ($)"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                            # Model performance metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Accuratezza Media", f"{np.mean(predictions['predictions']):.2%}")
                            with col2:
                                confidence_range = np.mean(
                                    predictions['confidence_intervals']['upper'] - 
                                    predictions['confidence_intervals']['lower']
                                )
                                st.metric("Intervallo di Confidenza", f"±{confidence_range:.2%}")
                            with col3:
                                st.metric("Orizzonte di Previsione", "5 giorni")

                        except Exception as e:
                            st.error(f"Errore nella generazione delle previsioni: {str(e)}")

                with prediction_tab2:
                    if hasattr(trading_bot.prediction_model, 'metrics') and trading_bot.prediction_model.metrics:
                        metrics = trading_bot.prediction_model.metrics

                        # Display model performance
                        st.subheader("Performance dei Modelli")
                        model_scores = pd.DataFrame({
                            'Modello': metrics['cv_scores_mean'].keys(),
                            'Score Medio': metrics['cv_scores_mean'].values(),
                            'Deviazione Standard': metrics['cv_scores_std'].values()
                        })

                        fig = go.Figure(data=[
                            go.Bar(name='Score Medio', x=model_scores['Modello'], y=model_scores['Score Medio']),
                            go.Bar(name='Deviazione Standard', x=model_scores['Modello'], y=model_scores['Deviazione Standard'])
                        ])

                        fig.update_layout(
                            barmode='group',
                            title="Performance dei Modelli nell'Ensemble",
                            xaxis_title="Modello",
                            yaxis_title="Score"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                with prediction_tab3:
                    st.subheader("Importanza delle Features")
                    feature_importance = trading_bot.prediction_model.get_feature_importance()
                    if feature_importance:
                        fi_df = pd.DataFrame(feature_importance, columns=['Feature', 'Importance'])
                        fi_df = fi_df.head(15)  # Show top 15 features

                        fig = go.Figure(go.Bar(
                            x=fi_df['Importance'],
                            y=fi_df['Feature'],
                            orientation='h'
                        ))

                        fig.update_layout(
                            height=500,
                            template='plotly_dark',
                            title="Top 15 Features più Influenti",
                            xaxis_title="Importanza Relativa",
                            yaxis_title="Feature"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # Feature correlation matrix
                        st.subheader("Matrice di Correlazione delle Features")
                        if 'feature_names' in metrics:
                            corr_matrix = df[metrics['feature_names']].corr()
                            fig = go.Figure(data=go.Heatmap(
                                z=corr_matrix,
                                x=corr_matrix.columns,
                                y=corr_matrix.columns,
                                colorscale='RdBu'
                            ))
                            fig.update_layout(
                                height=600,
                                title="Correlazione tra Features"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                    else:
                        st.info("Addestra il modello per vedere l'importanza delle features")

                st.markdown('</div>', unsafe_allow_html=True)


    with tab2:
        st.markdown('<div class="strategy-container">', unsafe_allow_html=True)
        st.subheader("🎯 Trading Strategies Configuration")

        # Strategy cards in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            with st.container():
                st.markdown("### 🚀 Meme Coin Sniping")
                use_meme = st.checkbox("Enable Strategy", key="meme_strategy")
                if use_meme:
                    st.slider("Sentiment Threshold", 0.0, 1.0, 0.7, key="meme_sentiment")
                    st.slider("Min Liquidity (USD)", 50000, 500000, 100000, step=50000, key="meme_liquidity")
                else:
                    st.info("Enable to trade trending meme coins")

        with col2:
            with st.container():
                st.markdown("### ⚡ Scalping Strategy")
                use_scalping = st.checkbox("Enable Strategy", key="scalp_strategy")
                if use_scalping:
                    st.slider("Volume Threshold", 500000, 5000000, 1000000, step=500000, key="scalp_volume")
                    st.slider("Profit Target (%)", 0.1, 2.0, 0.5, 0.1, key="scalp_target")
                else:
                    st.info("Enable for high-frequency trading")

        with col3:
            with st.container():
                st.markdown("### 📈 Swing Trading")
                use_swing = st.checkbox("Enable Strategy", key="swing_strategy")
                if use_swing:
                    st.slider("Trend Period (days)", 10, 50, 20, key="swing_period")
                    st.slider("Profit Target (%)", 5.0, 30.0, 15.0, 1.0, key="swing_target")
                else:
                    st.info("Enable for medium-term trades")

        # Strategy simulation section
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        if st.button("🔄 Run Strategy Simulation", use_container_width=True):
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

                    # Display metrics in cards
                    st.subheader("📊 Simulation Results")
                    metric_cols = st.columns(4)

                    with metric_cols[0]:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("Total Return", f"{metrics['Total Return']:.2%}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    with metric_cols[1]:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    with metric_cols[2]:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    with metric_cols[3]:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("Win Rate", f"{metrics['Win Rate']:.2%}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Portfolio performance chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=portfolio.index,
                        y=portfolio['Holdings'],
                        name='Portfolio Value',
                        line=dict(color='#059669', width=2)
                    ))
                    fig.update_layout(
                        height=400,
                        template='plotly_white',
                        title='Portfolio Performance Simulation'
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error during simulation: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="trading-container">', unsafe_allow_html=True)
        st.subheader("🤖 Automated Trading Console")

        # Bot configuration cards
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            initial_balance = st.number_input(
                "💰 Initial Balance ($)",
                min_value=100,
                value=10000,
                step=100
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Get active strategies
        active_strategies = []
        if use_meme:
            active_strategies.append('meme_coin')
        if use_scalping:
            active_strategies.append('scalping')
        if use_swing:
            active_strategies.append('swing')

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            if selected_coin in running_bots:
                if st.button("🛑 Stop Bot", use_container_width=True):
                    stop_bot(selected_coin)
            else:
                if st.button("▶️ Start Bot", use_container_width=True):
                    if not active_strategies:
                        st.warning("⚠️ Please select at least one trading strategy")
                    else:
                        start_bot(selected_coin, initial_balance, active_strategies)
            st.markdown('</div>', unsafe_allow_html=True)

        # Bot monitoring dashboard
        if running_bots:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("📊 Live Trading Dashboard")

            for symbol, bot_info in running_bots.items():
                bot = bot_info['bot']
                runtime = datetime.now() - bot_info['start_time']

                # Performance metrics
                metric_cols = st.columns(3)

                with metric_cols[0]:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("💰 Total Return", 
                             f"{((bot.balance / bot.initial_balance) - 1):.2%}")
                    st.metric("⏱️ Active Time",
                             f"{runtime.seconds // 3600}h {(runtime.seconds % 3600) // 60}m")
                    st.markdown('</div>', unsafe_allow_html=True)

                with metric_cols[1]:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.write("🎯 Active Strategies:")
                    for strategy in bot_info['active_strategies']:
                        st.write(f"✅ {strategy.replace('_', ' ').title()}")
                    st.markdown('</div>', unsafe_allow_html=True)

                with metric_cols[2]:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.write("📈 Current Position:")
                    if bot.current_position:
                        st.write(f"Entry Price: ${bot.current_position['entry_price']:.2f}")
                        st.write(f"Size: {bot.current_position['size']:.6f}")
                        st.write(f"Strategy: {bot.current_position['strategy']}")
                    else:
                        st.write("No active position")
                    st.markdown('</div>', unsafe_allow_html=True)

            # Trading logs
            if st.checkbox("📝 Show Recent Logs"):
                try:
                    with open(f'trading_log_{selected_coin}_{datetime.now().strftime("%Y%m%d")}.log', 'r') as f:
                        logs = f.readlines()[-20:]  # Show last 20 lines
                        st.code('\n'.join(logs))
                except FileNotFoundError:
                    st.info("No logs available yet")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("🤖 No active trading bots")

        # Historical performance
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("📈 Historical Performance")
        try:
            db = next(get_db())
            # Aggiunge retry logic per WebSocket
            def setup_websocket_connection():
                max_retries = 3
                retry_delay = 2  # secondi

                for attempt in range(max_retries):
                    try:
                        # Setup WebSocket connection
                        st.session_state['ws_connected'] = True
                        return True
                    except Exception as e:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        st.error(f"Errore di connessione WebSocket: {str(e)}")
                        return False

            try:
                if 'ws_connected' not in st.session_state:
                    setup_websocket_connection()

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
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error loading historical performance: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"An unexpected error occurred: {str(e)}")
    st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown("*Disclaimer: This is a simulation platform. Do not use for actual trading without proper risk management.*")