
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

class TradingDashboard:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.trade_history = []
        self.performance_metrics = {}
        self.initialize_session_state()
        self.data_cache = None
        self.last_update = datetime.now() - timedelta(minutes=1)
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        session_vars = ['active_trades', 'daily_change', 'daily_profit']
        for var in session_vars:
            if var not in st.session_state:
                setattr(st.session_state, var, 0 if var != 'daily_change' else 0.0)
            
    async def update_trade_data(self, trade_result: Dict[str, Any]):
        """Update dashboard with new trade data"""
        try:
            trade_data = {
                **trade_result,
                'timestamp': datetime.now().isoformat()
            }
            self.trade_history.append(trade_data)
            await self._calculate_performance_metrics()
            self.logger.info(f"Trade data updated: {trade_data}")
            self.data_cache = None
        except Exception as e:
            self.logger.error(f"Error updating trade data: {str(e)}")

    async def _calculate_performance_metrics(self):
        """Calculate performance metrics from trade history"""
        try:
            if not self.trade_history:
                return
            
            df = pd.DataFrame(self.trade_history)
            total_trades = len(df)
            successful_trades = len(df[df['success'] == True])
            win_rate = successful_trades / total_trades if total_trades > 0 else 0
            
            if 'price' in df.columns and 'take_profit' in df.columns:
                profits = df.apply(lambda x: x['take_profit'] - x['price'] if x['success'] else 0, axis=1)
                total_profit = profits.sum()
                daily_profit = profits[df['timestamp'].dt.date == datetime.now().date()].sum()
                
                self.performance_metrics.update({
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'total_profit': total_profit,
                    'daily_profit': daily_profit,
                    'daily_change': (daily_profit / total_profit * 100) if total_profit else 0,
                    'active_positions': len(df[df['active'] == True]),
                    'last_updated': datetime.now().isoformat()
                })
                
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}")

    @st.cache_data
    def load_trade_history(self):
        """Load trade history with caching"""
        if self.data_cache is None or (datetime.now() - self.last_update).seconds > 60:
            self.data_cache = pd.DataFrame(self.trade_history)
            self.last_update = datetime.now()
        return self.data_cache

    def render_dashboard(self):
        """Render modern dashboard with enhanced metrics"""
        try:
            st.title("🌟 AurumBot Trading Dashboard")
            
            if (datetime.now() - self.last_update).seconds > 60:
                self.data_cache = None
                st.experimental_rerun()

            df = self.load_trade_history()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Portfolio Value",
                    f"${self.performance_metrics.get('total_profit', 0):,.2f}",
                    f"{self.performance_metrics.get('daily_change', 0):+.2f}%"
                )
                
            with col2:
                st.metric(
                    "Win Rate",
                    f"{self.performance_metrics.get('win_rate', 0):.1%}",
                    f"{self.performance_metrics.get('total_trades', 0)} trades"
                )
                
            with col3:
                st.metric(
                    "Daily P&L",
                    f"${self.performance_metrics.get('daily_profit', 0):,.2f}",
                    f"{self.performance_metrics.get('daily_change', 0):+.2f}%"
                )
                
            with col4:
                active_pos = self.performance_metrics.get('active_positions', 0)
                st.metric(
                    "Active Positions",
                    f"{active_pos}",
                    f"{active_pos - st.session_state.active_trades:+d}"
                )
                st.session_state.active_trades = active_pos

            st.sidebar.title("Filter Trades")
            timeframe = st.sidebar.selectbox("Select Timeframe", ["1h", "1d", "1w"], index=1)
            symbol_filter = st.sidebar.selectbox("Filter by Symbol", ['All'] + list(df['symbol'].unique() if not df.empty else []))
            success_filter = st.sidebar.selectbox("Filter by Success", ["All", "Success", "Failure"])

            filtered_df = self.filter_trades(df, symbol_filter, success_filter)
            fig = self._create_trading_chart(filtered_df, timeframe)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Recent Trades")
            if len(filtered_df) > 0:
                display_df = filtered_df[['timestamp', 'symbol', 'type', 'price', 'success']].tail(10)
                display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                st.dataframe(display_df, hide_index=True)
            
        except Exception as e:
            self.logger.error(f"Error rendering dashboard: {str(e)}")
            st.error("Error loading dashboard components")

    def filter_trades(self, df: pd.DataFrame, symbol: str, success: str) -> pd.DataFrame:
        """Filter trading data based on symbol and success"""
        if df.empty:
            return df
        if symbol and symbol != 'All':
            df = df[df['symbol'] == symbol]
        if success != "All":
            df = df[df['success'] == (success == "Success")]
        return df

    def _create_trading_chart(self, df: pd.DataFrame, timeframe: str) -> go.Figure:
        """Create interactive trading chart with timeframe selection"""
        try:
            fig = go.Figure()
            
            if len(df) > 0:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                
                if timeframe == "1h":
                    df = df.resample('1H').last()
                elif timeframe == "1d":
                    df = df.resample('1D').last()
                elif timeframe == "1w":
                    df = df.resample('1W').last()

                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['price'],
                        mode='lines+markers',
                        name='Price',
                        line=dict(color='#00C853', width=2)
                    )
                )
                
                fig.update_layout(
                    title='Trading Activity',
                    template='plotly_dark',
                    height=500,
                    margin=dict(l=0, r=0, t=30, b=0),
                    showlegend=True,
                    hovermode='x unified'
                )
                
            return fig
        except Exception as e:
            self.logger.error(f"Error creating chart: {str(e)}")
            return go.Figure()
