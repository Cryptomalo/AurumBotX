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
        
    async def update_trade_data(self, trade_result: Dict[str, Any]):
        """Update dashboard with new trade data"""
        try:
            self.trade_history.append({
                **trade_result,
                'timestamp': datetime.now().isoformat() if 'timestamp' not in trade_result else trade_result['timestamp']
            })
            
            # Update performance metrics
            self._calculate_performance_metrics()
            self.logger.info(f"Dashboard updated with trade: {trade_result}")
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {str(e)}")

    async def update_report(self, report_data: Dict[str, Any]):
        """Update dashboard with new report data"""
        try:
            self.performance_metrics.update(report_data)
            self.logger.info("Dashboard report updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating report: {str(e)}")

    def _calculate_performance_metrics(self):
        """Calculate performance metrics from trade history"""
        try:
            if not self.trade_history:
                return
            
            df = pd.DataFrame(self.trade_history)
            
            # Basic metrics
            total_trades = len(df)
            successful_trades = len(df[df['success'] == True])
            win_rate = successful_trades / total_trades if total_trades > 0 else 0
            
            # Calculate profit metrics if price data available
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
        """Render dashboard using Streamlit"""
        try:
            st.title("🤖 AurumBot Trading Dashboard")
            
            # Performance Metrics
            st.header("Performance Metrics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Trades", self.performance_metrics.get('total_trades', 0))
            with col2:
                st.metric("Win Rate", f"{self.performance_metrics.get('win_rate', 0):.2%}")
            with col3:
                st.metric("Total Profit", f"${self.performance_metrics.get('total_profit', 0):.2f}")
            
            # Trade History
            if self.trade_history:
                st.header("Recent Trades")
                df = pd.DataFrame(self.trade_history[-100:])  # Show last 100 trades
                st.dataframe(df)
                
                # Profit Chart
                if 'price' in df.columns and 'take_profit' in df.columns:
                    profits = df.apply(lambda x: x['take_profit'] - x['price'] if x['success'] else 0, axis=1)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(y=profits.cumsum(), mode='lines', name='Cumulative Profit'))
                    st.plotly_chart(fig)
            
        except Exception as e:
            self.logger.error(f"Error rendering dashboard: {str(e)}")
            st.error("Error rendering dashboard components")
