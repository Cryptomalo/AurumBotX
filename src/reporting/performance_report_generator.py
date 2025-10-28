import json
import os
from fpdf import FPDF
from datetime import datetime
from typing import Dict, Any

# Assuming AdvancedAnalyticsEngine is in the same project structure
import sys
from pathlib import Path

# Add project root to sys.path for local execution
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analytics.advanced_analytics_engine import AdvancedAnalyticsEngine 

class PDFReportGenerator(FPDF):
    """
    Custom FPDF class for generating professional performance reports.
    """
    def header(self):
        # Logo
        # self.image('logo.png', 10, 8, 33)
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, 'AurumBotX Performance Report', 0, 0, 'C')
        # Line break
        self.ln(20)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        # Arial 12
        self.set_font('Arial', 'B', 12)
        # Color of frame, background and text
        self.set_fill_color(200, 220, 255)
        self.set_text_color(0, 0, 0)
        # Title
        self.cell(0, 6, title, 0, 1, 'L', 1)
        # Line break
        self.ln(4)

    def add_metrics_table(self, metrics: Dict[str, Any]):
        """Adds the key performance metrics in a structured table."""
        self.chapter_title("Key Performance Metrics")
        
        # Table settings
        col_width = 90
        row_height = 8
        
        # Data structure for the table
        data = [
            ("Initial Capital", f"{metrics.get('initial_capital', 0):,.2f} USDT"),
            ("Final Balance", f"{metrics.get('final_balance', 0):,.2f} USDT"),
            ("Total Profit", f"{metrics.get('total_profit_usdt', 0):,.2f} USDT"),
            ("Total Trades", f"{metrics.get('total_trades', 0)}"),
            ("Winning Trades", f"{metrics.get('winning_trades', 0)}"),
            ("Losing Trades", f"{metrics.get('losing_trades', 0)}"),
            ("Win Rate", f"{metrics.get('win_rate', 0)}%"),
            ("Profit Factor", f"{metrics.get('profit_factor', 'N/A')}"),
            ("Max Drawdown", f"{metrics.get('max_drawdown_usdt', 0):,.2f} USDT ({metrics.get('max_drawdown_percent', 0)}%)"),
            ("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 'N/A')}"),
            ("Avg Profit/Trade", f"{metrics.get('average_profit_per_trade', 0):,.2f} USDT"),
            ("Avg Trade Duration", f"{metrics.get('average_trade_duration_minutes', 0):,.2f} min"),
        ]

        # Draw table header
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(230, 230, 230)
        self.cell(col_width, row_height, 'Metric', 1, 0, 'L', 1)
        self.cell(col_width, row_height, 'Value', 1, 1, 'L', 1)

        # Draw table rows
        self.set_font('Arial', '', 10)
        for metric, value in data:
            self.cell(col_width, row_height, metric, 1, 0, 'L')
            self.cell(col_width, row_height, value, 1, 1, 'L')
            
        self.ln(5)

    def add_summary(self, metrics: Dict[str, Any]):
        """Adds a textual summary of the performance."""
        self.chapter_title("Performance Summary")
        self.set_font('Arial', '', 10)
        
        summary = f"""
        This report summarizes the performance of AurumBotX from the historical trade data.
        
        The bot executed a total of {metrics.get('total_trades', 0)} trades, achieving a commendable Win Rate of {metrics.get('win_rate', 0)}%. 
        The total net profit generated is {metrics.get('total_profit_usdt', 0):,.2f} USDT, resulting in a Final Balance of {metrics.get('final_balance', 0):,.2f} USDT from an initial capital of {metrics.get('initial_capital', 0):,.2f} USDT.
        
        Key risk indicators show a Profit Factor of {metrics.get('profit_factor', 'N/A')} and a Maximum Drawdown of {metrics.get('max_drawdown_percent', 0)}%. 
        The Sharpe Ratio, a measure of risk-adjusted return, is calculated at {metrics.get('sharpe_ratio', 'N/A')}.
        
        The average winning trade was {metrics.get('average_win_usdt', 0):,.2f} USDT, and the average losing trade was {metrics.get('average_loss_usdt', 0):,.2f} USDT.
        """
        self.multi_cell(0, 5, summary)
        self.ln(5)

    def generate_report(self, metrics: Dict[str, Any], output_path: str):
        """Generates the full PDF report."""
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()

        # Report Metadata
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f"Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
        self.cell(0, 5, f"Data Range: {metrics.get('data_start_date', 'N/A')} - {metrics.get('data_end_date', 'N/A')}", 0, 1)
        self.ln(10)
        
        self.add_metrics_table(metrics)
        self.add_summary(metrics)
        
        # Add a placeholder for the cumulative balance chart (will be added later)
        self.chapter_title("Cumulative Balance Chart (Placeholder)")
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, "A chart showing the cumulative balance over time will be inserted here.", 0, 1)
        
        self.output(output_path, 'F')
        print(f"Report generated successfully at: {output_path}")

def generate_performance_report(initial_capital: float = 1000.0, output_dir: str = "reports"):
    """
    Main function to calculate metrics and generate the PDF report.
    """
    # 1. Calculate Metrics
    analytics = AdvancedAnalyticsEngine()
    metrics = analytics.calculate_metrics(initial_capital=initial_capital)
    
    if "error" in metrics:
        print(f"Error generating report: {metrics['error']}")
        return

    # Add date range to metrics for the report
    if not analytics.df_trades.empty:
        metrics["data_start_date"] = analytics.df_trades['open_time'].min().strftime('%Y-%m-%d')
        metrics["data_end_date"] = analytics.df_trades['close_time'].max().strftime('%Y-%m-%d')
    else:
        metrics["data_start_date"] = "N/A"
        metrics["data_end_date"] = "N/A"

    # 2. Generate PDF
    os.makedirs(output_dir, exist_ok=True)
    report_filename = f"AurumBotX_Performance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(output_dir, report_filename)
    
    pdf = PDFReportGenerator()
    pdf.generate_report(metrics, output_path)

    # 3. Print metrics for immediate console review
    print("\n--- Advanced Performance Metrics ---")
    print(json.dumps(metrics, indent=4))
    
    return output_path

if __name__ == "__main__":
    # Create reports directory if it doesn't exist
    os.makedirs("/home/ubuntu/AurumBotX/reports", exist_ok=True)
    
    # Generate the report
    generate_performance_report(initial_capital=1000.0, output_dir="/home/ubuntu/AurumBotX/reports")

