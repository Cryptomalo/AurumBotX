
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

logger = logging.getLogger(__name__)

class TradingDashboard:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.trade_history = []
        self.performance_metrics = {}
        
    def update_trade_data(self, trade_result: Dict[str, Any]):
        """Update dashboard with new trade data"""
        try:
            self.trade_history.append({
                **trade_result,
                'timestamp': datetime.now().isoformat()
            })
            self._calculate_performance_metrics()
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {str(e)}")

    def _calculate_performance_metrics(self):
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
                avg_profit = profits.mean()
            else:
                total_profit = 0
                avg_profit = 0
                
            self.performance_metrics.update({
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'average_profit': avg_profit,
                'last_updated': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}")

    def render_dashboard(self):
        """Render modern dashboard with enhanced metrics"""
        try:
            st.title("🌟 AurumBot Trading Dashboard")
            
            # Quick Metrics Section
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
                    f"{len(self.trade_history)} trades"
                )
                
            with col3:
                st.metric(
                    "Daily P&L",
                    f"${self.performance_metrics.get('daily_profit', 0):,.2f}",
                    f"{self.performance_metrics.get('daily_roi', 0):+.2f}%"
                )
                
            with col4:
                st.metric(
                    "Active Positions",
                    f"{self.performance_metrics.get('active_positions', 0)}",
                    f"{self.performance_metrics.get('position_change', 0):+d} today"
                )
            
            # Main Chart
            if self.trade_history:
                df = pd.DataFrame(self.trade_history[-100:])
                fig = self._create_trading_chart(df)
                st.plotly_chart(fig, use_container_width=True)
                
                # Recent Trades Table
                st.subheader("Recent Trades")
                st.dataframe(
                    df[['timestamp', 'symbol', 'type', 'price', 'success']].tail(10),
                    hide_index=True
                )
            
        except Exception as e:
            self.logger.error(f"Error rendering dashboard: {str(e)}")
            st.error("Error loading dashboard components")

    def _create_trading_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create interactive trading chart"""
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['price'],
                mode='lines',
                name='Price'
            )
        )
        
        fig.update_layout(
            title='Trading Activity',
            template='plotly_dark',
            height=500,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig
