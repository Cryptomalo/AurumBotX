import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import pandas as pd

def create_cumulative_balance_chart(data: List[Dict[str, Any]], initial_capital: float) -> go.Figure:
    """
    Creates an interactive cumulative balance chart using Plotly.
    
    Args:
        data: List of dictionaries with 'close_time' and 'cumulative_balance'.
        initial_capital: The starting capital for the trading period.
        
    Returns:
        A Plotly Figure object.
    """
    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No trading data available to plot.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(title="Cumulative Balance Over Time", height=500)
        return fig

    df = pd.DataFrame(data)
    df['close_time'] = pd.to_datetime(df['close_time'])

    # Ensure the initial capital is included at the start time
    initial_row = pd.DataFrame({
        'close_time': [df['close_time'].min() - pd.Timedelta(seconds=1)],
        'cumulative_balance': [initial_capital]
    })
    df = pd.concat([initial_row, df], ignore_index=True)
    df.sort_values('close_time', inplace=True)
    
    fig = go.Figure()

    # Add the cumulative balance line
    fig.add_trace(go.Scatter(
        x=df['close_time'], 
        y=df['cumulative_balance'], 
        mode='lines+markers', 
        name='Cumulative Balance',
        line=dict(color='rgb(30, 144, 255)', width=3),
        marker=dict(size=5)
    ))

    # Add a line for the initial capital
    fig.add_hline(
        y=initial_capital, 
        line_dash="dash", 
        line_color="gray", 
        annotation_text="Initial Capital", 
        annotation_position="bottom right"
    )

    # Customize layout
    fig.update_layout(
        title={
            'text': "AurumBotX: Cumulative Balance Over Time",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Time",
        yaxis_title="Balance (USDT)",
        hovermode="x unified",
        template="plotly_dark", # Use a dark theme for a modern look
        height=600
    )
    
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(visible=True),
        type="date"
    )

    return fig

def create_win_loss_pie_chart(metrics: Dict[str, Any]) -> go.Figure:
    """
    Creates a pie chart showing the distribution of winning and losing trades.
    """
    labels = ['Winning Trades', 'Losing Trades']
    values = [metrics.get('winning_trades', 0), metrics.get('losing_trades', 0)]
    colors = ['#00CC96', '#EF553B'] # Green for win, Red for loss

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.3, 
        marker_colors=colors,
        textinfo='label+percent'
    )])

    fig.update_layout(
        title_text="Win/Loss Trade Distribution",
        template="plotly_dark"
    )
    return fig

if __name__ == "__main__":
    # Example usage (requires AdvancedAnalyticsEngine to run first)
    import sys
    from pathlib import Path

    # Add project root to sys.path for local execution
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

    from src.analytics.advanced_analytics_engine import AdvancedAnalyticsEngine
    
    analytics = AdvancedAnalyticsEngine("/home/ubuntu/AurumBotX/data/trading_engine.db")
    metrics = analytics.calculate_metrics(initial_capital=1000.0)
    balance_data = analytics.get_cumulative_balance_data()
    
    # 1. Cumulative Balance Chart
    fig_balance = create_cumulative_balance_chart(balance_data, metrics.get("initial_capital", 1000.0))
    fig_balance.write_image("/home/ubuntu/AurumBotX/reports/cumulative_balance_chart.png")
    
    # 2. Win/Loss Pie Chart
    fig_pie = create_win_loss_pie_chart(metrics)
    fig_pie.write_image("/home/ubuntu/AurumBotX/reports/win_loss_pie_chart.png")

    print("Charts generated and saved to /home/ubuntu/AurumBotX/reports/")

