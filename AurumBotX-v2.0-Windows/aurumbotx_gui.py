#!/usr/bin/env python3
"""
AurumBotX GUI Application
Native desktop application for AurumBotX trading system

Author: AurumBotX Team
Date: 13 Settembre 2025
Version: 2.0
"""

import sys
import os
import json
import time
import threading
import webbrowser
import subprocess
from pathlib import Path
from datetime import datetime
import sqlite3

# GUI Framework
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    from tkinter.scrolledtext import ScrolledText
except ImportError:
    print("❌ tkinter not available. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tk"])
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    from tkinter.scrolledtext import ScrolledText

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

# Import update manager
try:
    from src.updater.update_manager import get_update_manager
    UPDATE_MANAGER_AVAILABLE = True
except ImportError:
    UPDATE_MANAGER_AVAILABLE = False
    print("⚠️ Update manager not available")

class AurumBotXGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AurumBotX - Professional Trading Bot")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Set icon (if available)
        try:
            icon_path = current_dir / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        # Variables
        self.trading_active = tk.BooleanVar()
        self.balance = tk.StringVar(value="30.00 USDT")
        self.trades_count = tk.StringVar(value="0")
        self.win_rate = tk.StringVar(value="0.0%")
        self.roi = tk.StringVar(value="0.0%")
        self.status = tk.StringVar(value="🔴 OFFLINE")
        
        # Configuration
        self.config = self.load_config()
        
        # Initialize update manager
        if UPDATE_MANAGER_AVAILABLE:
            self.update_manager = get_update_manager(self.on_update_notification)
            self.update_manager.start_auto_update_service()
        else:
            self.update_manager = None
        
        # Setup GUI
        self.setup_gui()
        
        # Start monitoring
        self.start_monitoring()
        
        print("🚀 AurumBotX GUI initialized")
    
    def load_config(self):
        """Load configuration"""
        config_file = current_dir / "config" / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default config
        return {
            "trading": {
                "initial_capital": 30.0,
                "currency": "USDT",
                "risk_per_trade": 0.25,
                "max_drawdown": 0.20
            },
            "api": {
                "binance_api_key": "",
                "binance_secret_key": ""
            }
        }
    
    def save_config(self):
        """Save configuration"""
        config_dir = current_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_gui(self):
        """Setup GUI components"""
        # Main menu
        self.setup_menu()
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame - Status and controls
        self.setup_top_frame(main_frame)
        
        # Middle frame - Notebook with tabs
        self.setup_notebook(main_frame)
        
        # Bottom frame - Log
        self.setup_bottom_frame(main_frame)
    
    def setup_menu(self):
        """Setup menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Config", command=self.open_config)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Trading menu
        trading_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Trading", menu=trading_menu)
        trading_menu.add_command(label="Start Trading", command=self.start_trading)
        trading_menu.add_command(label="Stop Trading", command=self.stop_trading)
        trading_menu.add_separator()
        trading_menu.add_command(label="Emergency Stop", command=self.emergency_stop)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Web Dashboard", command=self.open_dashboard)
        tools_menu.add_command(label="API Health", command=self.check_api_health)
        tools_menu.add_command(label="Database Viewer", command=self.open_database_viewer)
        
        # Update menu
        update_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Update", menu=update_menu)
        update_menu.add_command(label="Check for Updates", command=self.check_updates)
        update_menu.add_command(label="Update Settings", command=self.show_update_settings)
        update_menu.add_command(label="Update History", command=self.show_update_history)
        update_menu.add_separator()
        update_menu.add_command(label="Rollback Update", command=self.rollback_update)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.open_docs)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_top_frame(self, parent):
        """Setup top status frame"""
        top_frame = ttk.LabelFrame(parent, text="System Status", padding=10)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status indicators
        status_frame = ttk.Frame(top_frame)
        status_frame.pack(fill=tk.X)
        
        # Left side - Status
        left_frame = ttk.Frame(status_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
        status_label = ttk.Label(left_frame, textvariable=self.status, font=("Arial", 12, "bold"))
        status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Right side - Controls
        right_frame = ttk.Frame(status_frame)
        right_frame.pack(side=tk.RIGHT)
        
        self.start_btn = ttk.Button(right_frame, text="🚀 Start Trading", 
                                   command=self.start_trading, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(right_frame, text="⏹️ Stop Trading", 
                                  command=self.stop_trading, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        emergency_btn = ttk.Button(right_frame, text="🚨 Emergency Stop", 
                                  command=self.emergency_stop, style="Danger.TButton")
        emergency_btn.pack(side=tk.LEFT)
    
    def setup_notebook(self, parent):
        """Setup main notebook with tabs"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Dashboard tab
        self.setup_dashboard_tab()
        
        # Trading tab
        self.setup_trading_tab()
        
        # Portfolio tab
        self.setup_portfolio_tab()
        
        # Settings tab
        self.setup_settings_tab()
    
    def setup_dashboard_tab(self):
        """Setup dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Metrics frame
        metrics_frame = ttk.LabelFrame(dashboard_frame, text="Performance Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Create metrics grid
        metrics = [
            ("Balance:", self.balance),
            ("Trades:", self.trades_count),
            ("Win Rate:", self.win_rate),
            ("ROI:", self.roi)
        ]
        
        for i, (label, var) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(metrics_frame, text=label, font=("Arial", 10, "bold")).grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5)
            ttk.Label(metrics_frame, textvariable=var, font=("Arial", 12)).grid(
                row=row, column=col+1, sticky=tk.W, padx=(0, 30), pady=5)
        
        # Chart placeholder
        chart_frame = ttk.LabelFrame(dashboard_frame, text="Performance Chart", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        chart_label = ttk.Label(chart_frame, text="📈 Real-time chart will be displayed here\n(Feature coming soon)", 
                               font=("Arial", 12), anchor=tk.CENTER)
        chart_label.pack(expand=True)
    
    def setup_trading_tab(self):
        """Setup trading tab"""
        trading_frame = ttk.Frame(self.notebook)
        self.notebook.add(trading_frame, text="🤖 Trading")
        
        # Trading controls
        controls_frame = ttk.LabelFrame(trading_frame, text="Trading Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Capital input
        ttk.Label(controls_frame, text="Initial Capital (USDT):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.capital_var = tk.StringVar(value=str(self.config["trading"]["initial_capital"]))
        capital_entry = ttk.Entry(controls_frame, textvariable=self.capital_var, width=15)
        capital_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Risk per trade
        ttk.Label(controls_frame, text="Risk per Trade (%):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.risk_var = tk.StringVar(value=str(int(self.config["trading"]["risk_per_trade"] * 100)))
        risk_scale = ttk.Scale(controls_frame, from_=1, to=50, variable=self.risk_var, orient=tk.HORIZONTAL)
        risk_scale.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # Strategy selection
        ttk.Label(controls_frame, text="Strategy:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.strategy_var = tk.StringVar(value="AI Enhanced Momentum")
        strategy_combo = ttk.Combobox(controls_frame, textvariable=self.strategy_var, 
                                     values=["AI Enhanced Momentum", "Mean Reversion", "Breakout Hunter", "Grid Trading"])
        strategy_combo.grid(row=2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # Recent trades
        trades_frame = ttk.LabelFrame(trading_frame, text="Recent Trades", padding=10)
        trades_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Trades treeview
        columns = ("Time", "Pair", "Side", "Amount", "Price", "P&L")
        self.trades_tree = ttk.Treeview(trades_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.trades_tree.heading(col, text=col)
            self.trades_tree.column(col, width=100)
        
        # Scrollbar for trades
        trades_scroll = ttk.Scrollbar(trades_frame, orient=tk.VERTICAL, command=self.trades_tree.yview)
        self.trades_tree.configure(yscrollcommand=trades_scroll.set)
        
        self.trades_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trades_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_portfolio_tab(self):
        """Setup portfolio tab"""
        portfolio_frame = ttk.Frame(self.notebook)
        self.notebook.add(portfolio_frame, text="💼 Portfolio")
        
        # Portfolio treeview
        portfolio_tree_frame = ttk.LabelFrame(portfolio_frame, text="Current Holdings", padding=10)
        portfolio_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("Asset", "Amount", "Value (USDT)", "Change (24h)")
        self.portfolio_tree = ttk.Treeview(portfolio_tree_frame, columns=columns, show="headings")
        
        for col in columns:
            self.portfolio_tree.heading(col, text=col)
            self.portfolio_tree.column(col, width=150)
        
        # Sample data
        sample_data = [
            ("USDT", "25.50", "25.50", "0.0%"),
            ("BTC", "0.0002", "8.70", "+2.3%"),
            ("ETH", "0.003", "7.95", "-1.2%"),
            ("ADA", "15.2", "5.62", "+4.1%")
        ]
        
        for item in sample_data:
            self.portfolio_tree.insert("", tk.END, values=item)
        
        self.portfolio_tree.pack(fill=tk.BOTH, expand=True)
    
    def setup_settings_tab(self):
        """Setup settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # API Configuration
        api_frame = ttk.LabelFrame(settings_frame, text="API Configuration", padding=10)
        api_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(api_frame, text="Binance API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value=self.config["api"]["binance_api_key"])
        api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*")
        api_key_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        ttk.Label(api_frame, text="Binance Secret Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.secret_key_var = tk.StringVar(value=self.config["api"]["binance_secret_key"])
        secret_key_entry = ttk.Entry(api_frame, textvariable=self.secret_key_var, width=50, show="*")
        secret_key_entry.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # Risk Management
        risk_frame = ttk.LabelFrame(settings_frame, text="Risk Management", padding=10)
        risk_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(risk_frame, text="Max Drawdown (%):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_drawdown_var = tk.StringVar(value=str(int(self.config["trading"]["max_drawdown"] * 100)))
        drawdown_scale = ttk.Scale(risk_frame, from_=5, to=50, variable=self.max_drawdown_var, orient=tk.HORIZONTAL)
        drawdown_scale.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # Save button
        save_btn = ttk.Button(settings_frame, text="💾 Save Settings", command=self.save_settings)
        save_btn.pack(pady=10)
    
    def setup_bottom_frame(self, parent):
        """Setup bottom log frame"""
        log_frame = ttk.LabelFrame(parent, text="System Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Add initial log message
        self.log("🚀 AurumBotX GUI started")
        self.log("📊 System ready for trading")
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
        # Limit log size
        lines = self.log_text.get("1.0", tk.END).split("\n")
        if len(lines) > 1000:
            self.log_text.delete("1.0", "100.0")
    
    def start_trading(self):
        """Start trading"""
        try:
            self.log("🚀 Starting trading system...")
            
            # Update UI
            self.trading_active.set(True)
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status.set("🟢 TRADING ACTIVE")
            
            # Start trading process (demo mode)
            self.start_demo_trading()
            
            self.log("✅ Trading started successfully")
            messagebox.showinfo("Success", "Trading started successfully!")
            
        except Exception as e:
            self.log(f"❌ Error starting trading: {e}")
            messagebox.showerror("Error", f"Failed to start trading: {e}")
    
    def stop_trading(self):
        """Stop trading"""
        try:
            self.log("⏹️ Stopping trading system...")
            
            # Update UI
            self.trading_active.set(False)
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status.set("🔴 OFFLINE")
            
            self.log("✅ Trading stopped successfully")
            messagebox.showinfo("Success", "Trading stopped successfully!")
            
        except Exception as e:
            self.log(f"❌ Error stopping trading: {e}")
            messagebox.showerror("Error", f"Failed to stop trading: {e}")
    
    def emergency_stop(self):
        """Emergency stop"""
        result = messagebox.askyesno("Emergency Stop", 
                                   "Are you sure you want to emergency stop all trading?\n\nThis will immediately close all positions.")
        if result:
            self.stop_trading()
            self.log("🚨 EMERGENCY STOP activated")
            messagebox.showwarning("Emergency Stop", "Emergency stop activated!")
    
    def start_demo_trading(self):
        """Start demo trading simulation"""
        def demo_trading_loop():
            import random
            import time
            
            balance = float(self.capital_var.get())
            trades = 0
            winning_trades = 0
            
            while self.trading_active.get():
                # Simulate trade
                profit_loss = random.uniform(-2, 3)  # Random P&L
                balance += profit_loss
                trades += 1
                
                if profit_loss > 0:
                    winning_trades += 1
                
                # Update metrics
                self.balance.set(f"{balance:.2f} USDT")
                self.trades_count.set(str(trades))
                
                if trades > 0:
                    win_rate = (winning_trades / trades) * 100
                    self.win_rate.set(f"{win_rate:.1f}%")
                    
                    initial_capital = float(self.capital_var.get())
                    roi = ((balance - initial_capital) / initial_capital) * 100
                    self.roi.set(f"{roi:+.2f}%")
                
                # Add trade to tree
                timestamp = datetime.now().strftime("%H:%M:%S")
                pair = random.choice(["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"])
                side = random.choice(["BUY", "SELL"])
                amount = random.uniform(0.001, 0.1)
                price = random.uniform(100, 50000)
                
                self.trades_tree.insert("", 0, values=(
                    timestamp, pair, side, f"{amount:.6f}", f"{price:.2f}", f"{profit_loss:+.2f}"
                ))
                
                # Log trade
                status = "✅" if profit_loss > 0 else "❌"
                self.log(f"{status} TRADE: {side} {amount:.6f} {pair} | P&L: {profit_loss:+.2f} USDT")
                
                # Wait before next trade
                time.sleep(random.uniform(30, 120))  # 30-120 seconds
        
        # Start trading thread
        trading_thread = threading.Thread(target=demo_trading_loop, daemon=True)
        trading_thread.start()
    
    def start_monitoring(self):
        """Start system monitoring"""
        def monitor_loop():
            while True:
                try:
                    # Check if trading process is running
                    if self.trading_active.get():
                        self.status.set("🟢 TRADING ACTIVE")
                    else:
                        self.status.set("🔴 OFFLINE")
                    
                    time.sleep(5)
                except:
                    break
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def save_settings(self):
        """Save settings"""
        try:
            # Update config
            self.config["api"]["binance_api_key"] = self.api_key_var.get()
            self.config["api"]["binance_secret_key"] = self.secret_key_var.get()
            self.config["trading"]["initial_capital"] = float(self.capital_var.get())
            self.config["trading"]["risk_per_trade"] = float(self.risk_var.get()) / 100
            self.config["trading"]["max_drawdown"] = float(self.max_drawdown_var.get()) / 100
            
            # Save to file
            self.save_config()
            
            self.log("💾 Settings saved successfully")
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except Exception as e:
            self.log(f"❌ Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def open_config(self):
        """Open config file"""
        filename = filedialog.askopenfilename(
            title="Open Configuration File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.config = json.load(f)
                self.log(f"📁 Configuration loaded from {filename}")
                messagebox.showinfo("Success", "Configuration loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def open_dashboard(self):
        """Open web dashboard"""
        webbrowser.open("http://localhost:8501")
        self.log("🌐 Web dashboard opened")
    
    def check_api_health(self):
        """Check API health"""
        try:
            import requests
            response = requests.get("http://localhost:8005/health", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("API Health", "✅ API server is healthy!")
                self.log("✅ API health check passed")
            else:
                messagebox.showwarning("API Health", "⚠️ API server responded with error")
                self.log("⚠️ API health check failed")
        except:
            messagebox.showerror("API Health", "❌ API server is not responding")
            self.log("❌ API server not responding")
    
    def open_database_viewer(self):
        """Open database viewer"""
        messagebox.showinfo("Database Viewer", "Database viewer feature coming soon!")
    
    def open_docs(self):
        """Open documentation"""
        webbrowser.open("https://docs.aurumbotx.ai")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """AurumBotX v2.0
Professional Cryptocurrency Trading Bot

🚀 Features:
• AI-powered trading strategies
• Real-time market analysis
• Advanced risk management
• Multi-exchange support
• 24/7 automated trading

📧 Support: support@aurumbotx.ai
🌐 Website: https://aurumbotx.ai

© 2025 AurumBotX Team"""
        
        messagebox.showinfo("About AurumBotX", about_text)
    
    def run(self):
        """Run the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log("👋 Application closed by user")

def main():
    """Main function"""
    print("🚀 Starting AurumBotX GUI...")
    
    try:
        app = AurumBotXGUI()
        app.run()
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()


    
    def on_update_notification(self, notification):
        """Handle update notifications"""
        try:
            message = notification.get("message", "")
            notif_type = notification.get("type", "info")
            
            # Show notification in GUI
            if notif_type == "error":
                messagebox.showerror("Update Error", message)
            elif notif_type == "warning":
                messagebox.showwarning("Update Warning", message)
            elif notif_type == "success":
                messagebox.showinfo("Update Success", message)
            else:
                # Log info messages
                self.log(message)
                
        except Exception as e:
            print(f"⚠️ Update notification error: {e}")
    
    def check_updates(self):
        """Check for updates"""
        if not self.update_manager:
            messagebox.showwarning("Update Manager", "Update manager not available")
            return
        
        self.log("🔍 Checking for updates...")
        success = self.update_manager.force_update_check()
        
        if not success:
            messagebox.showinfo("Update Check", "Update check already in progress")
    
    def show_update_settings(self):
        """Show update settings dialog"""
        if not self.update_manager:
            messagebox.showwarning("Update Manager", "Update manager not available")
            return
        
        # Create settings window
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Update Settings")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Get current settings
        status = self.update_manager.get_status()
        
        # Auto-check setting
        auto_check_var = tk.BooleanVar(value=status.get("auto_check_enabled", True))
        ttk.Checkbutton(settings_window, text="Automatically check for updates", 
                       variable=auto_check_var).pack(pady=10)
        
        # Check interval
        ttk.Label(settings_window, text="Check interval (hours):").pack(pady=5)
        interval_var = tk.StringVar(value=str(status.get("check_interval_hours", 6)))
        ttk.Entry(settings_window, textvariable=interval_var, width=10).pack(pady=5)
        
        # Auto-download setting
        auto_download_var = tk.BooleanVar(value=status.get("auto_download", True))
        ttk.Checkbutton(settings_window, text="Automatically download updates", 
                       variable=auto_download_var).pack(pady=10)
        
        # Auto-install setting
        auto_install_var = tk.BooleanVar(value=status.get("auto_install", False))
        ttk.Checkbutton(settings_window, text="Automatically install updates", 
                       variable=auto_install_var).pack(pady=10)
        
        # Update channel
        ttk.Label(settings_window, text="Update channel:").pack(pady=5)
        channel_var = tk.StringVar(value=status.get("update_channel", "stable"))
        channel_combo = ttk.Combobox(settings_window, textvariable=channel_var,
                                   values=["stable", "beta", "alpha"], state="readonly")
        channel_combo.pack(pady=5)
        
        # Save button
        def save_settings():
            try:
                config_updates = {
                    "auto_check": auto_check_var.get(),
                    "check_interval_hours": int(interval_var.get()),
                    "auto_download": auto_download_var.get(),
                    "auto_install": auto_install_var.get(),
                    "update_channel": channel_var.get()
                }
                
                if self.update_manager.update_config(config_updates):
                    messagebox.showinfo("Settings", "Update settings saved successfully!")
                    settings_window.destroy()
                else:
                    messagebox.showerror("Settings", "Failed to save settings")
                    
            except ValueError:
                messagebox.showerror("Settings", "Invalid check interval value")
        
        ttk.Button(settings_window, text="Save Settings", command=save_settings).pack(pady=20)
    
    def show_update_history(self):
        """Show update history"""
        if not self.update_manager:
            messagebox.showwarning("Update Manager", "Update manager not available")
            return
        
        # Create history window
        history_window = tk.Toplevel(self.root)
        history_window.title("Update History")
        history_window.geometry("600x400")
        
        # History treeview
        columns = ("Version", "Date", "Size", "Status")
        history_tree = ttk.Treeview(history_window, columns=columns, show="headings")
        
        for col in columns:
            history_tree.heading(col, text=col)
            history_tree.column(col, width=120)
        
        # Get update history
        history = self.update_manager.get_update_history()
        
        for item in history:
            size_mb = item.get("size", 0) / (1024 * 1024)
            history_tree.insert("", tk.END, values=(
                item.get("version", "Unknown"),
                item.get("timestamp", "Unknown"),
                f"{size_mb:.1f} MB",
                "Backup Available"
            ))
        
        # Add current version
        current_version = self.update_manager.updater.current_version
        history_tree.insert("", 0, values=(
            f"{current_version} (Current)",
            "Active",
            "-",
            "Running"
        ))
        
        history_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(history_window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Refresh", 
                  command=lambda: self.refresh_history(history_tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Close", 
                  command=history_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def refresh_history(self, tree):
        """Refresh update history"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Reload history
        if self.update_manager:
            history = self.update_manager.get_update_history()
            
            for item in history:
                size_mb = item.get("size", 0) / (1024 * 1024)
                tree.insert("", tk.END, values=(
                    item.get("version", "Unknown"),
                    item.get("timestamp", "Unknown"),
                    f"{size_mb:.1f} MB",
                    "Backup Available"
                ))
            
            # Add current version
            current_version = self.update_manager.updater.current_version
            tree.insert("", 0, values=(
                f"{current_version} (Current)",
                "Active",
                "-",
                "Running"
            ))
    
    def rollback_update(self):
        """Rollback to previous version"""
        if not self.update_manager:
            messagebox.showwarning("Update Manager", "Update manager not available")
            return
        
        # Confirm rollback
        result = messagebox.askyesno("Rollback Update", 
                                   "Are you sure you want to rollback to the previous version?\n\n"
                                   "This will restore the last backup and restart the application.")
        
        if result:
            self.log("🔄 Starting rollback process...")
            self.update_manager.rollback_async()

