#!/usr/bin/env python3
"""
AurumBotX Multi-Bot Monitoring Dashboard
Dashboard per monitorare 8 bot simultanei

Author: AurumBotX Team
Date: 12 Settembre 2025
Version: 1.0
"""

import streamlit as st
import json
import psutil
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Page config
st.set_page_config(
    page_title="AurumBotX Multi-Bot Monitor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class MultiBotMonitor:
    def __init__(self):
        self.config_file = "config/multi_bot_config.json"
        self.config = self.load_config()
        
    def load_config(self):
        """Load multi-bot configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading config: {e}")
            return None
    
    def get_bot_processes(self):
        """Get all bot processes"""
        bot_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status', 'cpu_percent', 'memory_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'bot_' in cmdline and '.py' in cmdline:
                    # Extract bot ID from command line
                    for part in cmdline.split():
                        if 'bot_' in part and '.py' in part:
                            bot_id = part.split('bot_')[1].split('.')[0]
                            bot_processes.append({
                                'bot_id': int(bot_id),
                                'pid': proc.info['pid'],
                                'status': proc.info['status'],
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent']
                            })
                            break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return sorted(bot_processes, key=lambda x: x['bot_id'])
    
    def get_bot_logs(self, bot_id, lines=50):
        """Get recent log entries for a bot"""
        log_file = f"logs/bot_{bot_id}.log"
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    return f.readlines()[-lines:]
            else:
                return [f"Log file not found: {log_file}"]
        except Exception as e:
            return [f"Error reading log: {e}"]
    
    def create_status_overview(self):
        """Create status overview"""
        if not self.config:
            st.error("Configuration not loaded")
            return
        
        st.title("🤖 AurumBotX Multi-Bot System")
        st.markdown("---")
        
        # System overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bots", len(self.config['bots']))
        
        with col2:
            st.metric("Total Capital", f"{self.config['multi_bot_system']['total_capital']} USDT")
        
        with col3:
            bot_processes = self.get_bot_processes()
            active_bots = len(bot_processes)
            st.metric("Active Bots", active_bots, delta=active_bots - len(self.config['bots']))
        
        with col4:
            if active_bots > 0:
                avg_cpu = sum(p['cpu_percent'] for p in bot_processes) / len(bot_processes)
                st.metric("Avg CPU Usage", f"{avg_cpu:.1f}%")
            else:
                st.metric("Avg CPU Usage", "0%")
    
    def create_bot_status_table(self):
        """Create bot status table"""
        st.subheader("📊 Bot Status Overview")
        
        bot_processes = self.get_bot_processes()
        process_dict = {p['bot_id']: p for p in bot_processes}
        
        # Create status data
        status_data = []
        for bot in self.config['bots']:
            bot_id = bot['bot_id']
            process_info = process_dict.get(bot_id)
            
            if process_info:
                status = "🟢 RUNNING"
                pid = process_info['pid']
                cpu = f"{process_info['cpu_percent']:.1f}%"
                memory = f"{process_info['memory_percent']:.1f}%"
            else:
                status = "🔴 STOPPED"
                pid = "N/A"
                cpu = "0%"
                memory = "0%"
            
            status_data.append({
                'Bot ID': bot_id,
                'Name': bot['name'],
                'Strategy': bot['strategy'],
                'Capital': f"{bot['capital']} USDT",
                'Pairs': ', '.join(bot['pairs'][:2]) + ('...' if len(bot['pairs']) > 2 else ''),
                'Status': status,
                'PID': pid,
                'CPU': cpu,
                'Memory': memory
            })
        
        df = pd.DataFrame(status_data)
        st.dataframe(df, use_container_width=True)
    
    def create_performance_charts(self):
        """Create performance charts"""
        st.subheader("📈 Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU Usage Chart
            bot_processes = self.get_bot_processes()
            if bot_processes:
                cpu_data = pd.DataFrame(bot_processes)
                fig_cpu = px.bar(
                    cpu_data, 
                    x='bot_id', 
                    y='cpu_percent',
                    title='CPU Usage by Bot',
                    labels={'bot_id': 'Bot ID', 'cpu_percent': 'CPU %'}
                )
                st.plotly_chart(fig_cpu, use_container_width=True)
            else:
                st.info("No active bots to display CPU usage")
        
        with col2:
            # Memory Usage Chart
            if bot_processes:
                memory_data = pd.DataFrame(bot_processes)
                fig_memory = px.bar(
                    memory_data, 
                    x='bot_id', 
                    y='memory_percent',
                    title='Memory Usage by Bot',
                    labels={'bot_id': 'Bot ID', 'memory_percent': 'Memory %'}
                )
                st.plotly_chart(fig_memory, use_container_width=True)
            else:
                st.info("No active bots to display memory usage")
    
    def create_strategy_distribution(self):
        """Create strategy distribution chart"""
        st.subheader("🎯 Strategy Distribution")
        
        strategies = [bot['strategy'] for bot in self.config['bots']]
        strategy_counts = pd.Series(strategies).value_counts()
        
        fig = px.pie(
            values=strategy_counts.values,
            names=strategy_counts.index,
            title="Bot Strategy Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def create_log_viewer(self):
        """Create log viewer"""
        st.subheader("📋 Bot Logs")
        
        # Bot selection
        bot_options = [f"Bot {bot['bot_id']}: {bot['name']}" for bot in self.config['bots']]
        selected_bot = st.selectbox("Select Bot", bot_options)
        
        if selected_bot:
            bot_id = int(selected_bot.split(':')[0].split()[1])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                lines = st.slider("Number of lines", 10, 200, 50)
            with col2:
                if st.button("Refresh Logs"):
                    st.rerun()
            
            # Display logs
            logs = self.get_bot_logs(bot_id, lines)
            log_text = ''.join(logs)
            
            st.text_area(
                f"Recent logs for Bot {bot_id}:",
                log_text,
                height=400,
                key=f"logs_{bot_id}"
            )
    
    def create_control_panel(self):
        """Create control panel"""
        st.sidebar.title("🎛️ Control Panel")
        
        # System controls
        st.sidebar.subheader("System Controls")
        
        if st.sidebar.button("🔄 Refresh Status"):
            st.rerun()
        
        if st.sidebar.button("📊 Export Status"):
            # Create status export
            bot_processes = self.get_bot_processes()
            status_export = {
                'timestamp': datetime.now().isoformat(),
                'total_bots': len(self.config['bots']),
                'active_bots': len(bot_processes),
                'bot_status': bot_processes
            }
            
            st.sidebar.download_button(
                "Download Status JSON",
                json.dumps(status_export, indent=2),
                file_name=f"multibot_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        # Auto-refresh
        st.sidebar.subheader("Auto-Refresh")
        auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh")
        if auto_refresh:
            refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)
            time.sleep(refresh_interval)
            st.rerun()
        
        # System info
        st.sidebar.subheader("System Info")
        st.sidebar.info(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
        
        # Quick stats
        bot_processes = self.get_bot_processes()
        if bot_processes:
            total_cpu = sum(p['cpu_percent'] for p in bot_processes)
            total_memory = sum(p['memory_percent'] for p in bot_processes)
            st.sidebar.metric("Total CPU", f"{total_cpu:.1f}%")
            st.sidebar.metric("Total Memory", f"{total_memory:.1f}%")

def main():
    """Main dashboard function"""
    monitor = MultiBotMonitor()
    
    # Create control panel
    monitor.create_control_panel()
    
    # Main content
    monitor.create_status_overview()
    monitor.create_bot_status_table()
    
    # Charts and logs in tabs
    tab1, tab2, tab3 = st.tabs(["📈 Performance", "🎯 Strategy Analysis", "📋 Logs"])
    
    with tab1:
        monitor.create_performance_charts()
    
    with tab2:
        monitor.create_strategy_distribution()
    
    with tab3:
        monitor.create_log_viewer()
    
    # Footer
    st.markdown("---")
    st.markdown("🤖 **AurumBotX Multi-Bot System** | Real-time monitoring dashboard")

if __name__ == "__main__":
    main()

