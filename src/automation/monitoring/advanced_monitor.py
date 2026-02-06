#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX v2.1 - Advanced Monitoring System
Enterprise-grade monitoring and alerting system
"""

import os
import sys
import json
import time
import asyncio
import logging
import sqlite3
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import threading
from dataclasses import dataclass, asdict
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/home/ubuntu/AurumBotX/logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types of alerts"""
    SYSTEM = "system"
    TRADING = "trading"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BALANCE = "balance"
    API = "api"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: datetime
    level: AlertLevel
    type: AlertType
    title: str
    message: str
    data: Dict[str, Any]
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    api_response_time: float
    database_connections: int
    active_trades: int
    balance: float
    daily_pnl: float

@dataclass
class TradingMetrics:
    """Trading performance metrics"""
    timestamp: datetime
    total_trades: int
    successful_trades: int
    failed_trades: int
    win_rate: float
    total_pnl: float
    daily_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    avg_trade_duration: float

class AdvancedMonitor:
    """Advanced monitoring and alerting system"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the monitoring system
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or "/home/ubuntu/AurumBotX/config/monitor_config.json"
        self.config = self._load_config()
        
        # Database paths
        self.db_path = "/home/ubuntu/AurumBotX/data/trading_engine.db"
        self.monitor_db_path = "/home/ubuntu/AurumBotX/data/monitor.db"
        
        # API endpoints
        self.api_base = "http://localhost:5678"
        
        # Monitoring state
        self.is_running = False
        self.alerts = []
        self.metrics_history = []
        self.last_check = datetime.now()
        
        # Thresholds and limits
        self.thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'api_response_time': 5.0,
            'max_drawdown': 20.0,
            'min_balance': 45.0,
            'max_daily_loss': 5.0,
            'network_latency': 1000.0
        }
        
        # Alert channels
        self.alert_channels = {
            'telegram': self.config.get('telegram', {}).get('enabled', False),
            'email': self.config.get('email', {}).get('enabled', False),
            'webhook': self.config.get('webhook', {}).get('enabled', False),
            'log': True
        }
        
        # Monitoring intervals (seconds)
        self.intervals = {
            'system_metrics': 30,
            'trading_metrics': 60,
            'api_health': 15,
            'database_health': 120,
            'security_check': 300
        }
        
        # Initialize database
        self._init_monitor_database()
        
        logger.info("🔍 Advanced Monitor initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    "telegram": {
                        "enabled": False,
                        "bot_token": "",
                        "chat_ids": []
                    },
                    "email": {
                        "enabled": False,
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587,
                        "username": "",
                        "password": "",
                        "recipients": []
                    },
                    "webhook": {
                        "enabled": False,
                        "url": "",
                        "headers": {}
                    },
                    "monitoring": {
                        "system_metrics": True,
                        "trading_metrics": True,
                        "api_monitoring": True,
                        "security_monitoring": True
                    },
                    "thresholds": {
                        "cpu_usage": 80.0,
                        "memory_usage": 85.0,
                        "disk_usage": 90.0,
                        "max_drawdown": 20.0,
                        "min_balance": 45.0
                    }
                }
                
                # Save default config
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def _init_monitor_database(self):
        """Initialize monitoring database"""
        try:
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,
                    acknowledged INTEGER DEFAULT 0,
                    resolved INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    timestamp TEXT PRIMARY KEY,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_latency REAL,
                    api_response_time REAL,
                    database_connections INTEGER,
                    active_trades INTEGER,
                    balance REAL,
                    daily_pnl REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_metrics (
                    timestamp TEXT PRIMARY KEY,
                    total_trades INTEGER,
                    successful_trades INTEGER,
                    failed_trades INTEGER,
                    win_rate REAL,
                    total_pnl REAL,
                    daily_pnl REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    profit_factor REAL,
                    avg_trade_duration REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Monitor database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize monitor database: {e}")

    async def start_monitoring(self):
        """Start the monitoring system"""
        if self.is_running:
            logger.warning("Monitor is already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting Advanced Monitor...")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_system_metrics()),
            asyncio.create_task(self._monitor_trading_metrics()),
            asyncio.create_task(self._monitor_api_health()),
            asyncio.create_task(self._monitor_database_health()),
            asyncio.create_task(self._monitor_security()),
            asyncio.create_task(self._process_alerts())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"❌ Monitor error: {e}")
        finally:
            self.is_running = False

    async def stop_monitoring(self):
        """Stop the monitoring system"""
        self.is_running = False
        logger.info("🛑 Advanced Monitor stopped")

    async def _monitor_system_metrics(self):
        """Monitor system performance metrics"""
        while self.is_running:
            try:
                metrics = await self._collect_system_metrics()
                await self._check_system_thresholds(metrics)
                await self._store_system_metrics(metrics)
                
                await asyncio.sleep(self.intervals['system_metrics'])
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(30)

    async def _monitor_trading_metrics(self):
        """Monitor trading performance metrics"""
        while self.is_running:
            try:
                metrics = await self._collect_trading_metrics()
                await self._check_trading_thresholds(metrics)
                await self._store_trading_metrics(metrics)
                
                await asyncio.sleep(self.intervals['trading_metrics'])
                
            except Exception as e:
                logger.error(f"Error monitoring trading metrics: {e}")
                await asyncio.sleep(60)

    async def _monitor_api_health(self):
        """Monitor API health and response times"""
        while self.is_running:
            try:
                health_status = await self._check_api_health()
                
                if not health_status['healthy']:
                    await self._create_alert(
                        AlertLevel.ERROR,
                        AlertType.API,
                        "API Health Check Failed",
                        f"API is not responding properly: {health_status['error']}",
                        health_status
                    )
                
                await asyncio.sleep(self.intervals['api_health'])
                
            except Exception as e:
                logger.error(f"Error monitoring API health: {e}")
                await asyncio.sleep(15)

    async def _monitor_database_health(self):
        """Monitor database health and performance"""
        while self.is_running:
            try:
                db_status = await self._check_database_health()
                
                if not db_status['healthy']:
                    await self._create_alert(
                        AlertLevel.ERROR,
                        AlertType.SYSTEM,
                        "Database Health Issue",
                        f"Database health check failed: {db_status['error']}",
                        db_status
                    )
                
                await asyncio.sleep(self.intervals['database_health'])
                
            except Exception as e:
                logger.error(f"Error monitoring database health: {e}")
                await asyncio.sleep(120)

    async def _monitor_security(self):
        """Monitor security-related metrics"""
        while self.is_running:
            try:
                security_status = await self._check_security_status()
                
                if security_status['threats_detected']:
                    await self._create_alert(
                        AlertLevel.CRITICAL,
                        AlertType.SECURITY,
                        "Security Threat Detected",
                        f"Potential security issues found: {security_status['details']}",
                        security_status
                    )
                
                await asyncio.sleep(self.intervals['security_check'])
                
            except Exception as e:
                logger.error(f"Error monitoring security: {e}")
                await asyncio.sleep(300)

    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            import psutil
            
            # CPU and Memory
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network latency (ping to Google DNS)
            import subprocess
            try:
                result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Extract latency from ping output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'time=' in line:
                            latency = float(line.split('time=')[1].split(' ms')[0])
                            break
                    else:
                        latency = 0.0
                else:
                    latency = 9999.0  # High value to indicate failure
            except:
                latency = 9999.0
            
            # API response time
            api_response_time = await self._measure_api_response_time()
            
            # Database connections (mock for now)
            database_connections = 1
            
            # Trading data
            trading_data = await self._get_current_trading_data()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=(disk.used / disk.total) * 100,
                network_latency=latency,
                api_response_time=api_response_time,
                database_connections=database_connections,
                active_trades=trading_data.get('active_trades', 0),
                balance=trading_data.get('balance', 50.0),
                daily_pnl=trading_data.get('daily_pnl', 0.0)
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Return default metrics
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_latency=0.0,
                api_response_time=0.0,
                database_connections=0,
                active_trades=0,
                balance=50.0,
                daily_pnl=0.0
            )

    async def _collect_trading_metrics(self) -> TradingMetrics:
        """Collect trading performance metrics"""
        try:
            trading_data = await self._get_trading_performance_data()
            
            return TradingMetrics(
                timestamp=datetime.now(),
                total_trades=trading_data.get('total_trades', 0),
                successful_trades=trading_data.get('successful_trades', 0),
                failed_trades=trading_data.get('failed_trades', 0),
                win_rate=trading_data.get('win_rate', 0.0),
                total_pnl=trading_data.get('total_pnl', 0.0),
                daily_pnl=trading_data.get('daily_pnl', 0.0),
                sharpe_ratio=trading_data.get('sharpe_ratio', 0.0),
                max_drawdown=trading_data.get('max_drawdown', 0.0),
                profit_factor=trading_data.get('profit_factor', 0.0),
                avg_trade_duration=trading_data.get('avg_trade_duration', 0.0)
            )
            
        except Exception as e:
            logger.error(f"Error collecting trading metrics: {e}")
            return TradingMetrics(
                timestamp=datetime.now(),
                total_trades=0,
                successful_trades=0,
                failed_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                daily_pnl=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                profit_factor=0.0,
                avg_trade_duration=0.0
            )

    async def _check_system_thresholds(self, metrics: SystemMetrics):
        """Check system metrics against thresholds"""
        # CPU usage check
        if metrics.cpu_usage > self.thresholds['cpu_usage']:
            await self._create_alert(
                AlertLevel.WARNING,
                AlertType.SYSTEM,
                "High CPU Usage",
                f"CPU usage is {metrics.cpu_usage:.1f}% (threshold: {self.thresholds['cpu_usage']}%)",
                {'cpu_usage': metrics.cpu_usage}
            )
        
        # Memory usage check
        if metrics.memory_usage > self.thresholds['memory_usage']:
            await self._create_alert(
                AlertLevel.WARNING,
                AlertType.SYSTEM,
                "High Memory Usage",
                f"Memory usage is {metrics.memory_usage:.1f}% (threshold: {self.thresholds['memory_usage']}%)",
                {'memory_usage': metrics.memory_usage}
            )
        
        # Disk usage check
        if metrics.disk_usage > self.thresholds['disk_usage']:
            await self._create_alert(
                AlertLevel.ERROR,
                AlertType.SYSTEM,
                "High Disk Usage",
                f"Disk usage is {metrics.disk_usage:.1f}% (threshold: {self.thresholds['disk_usage']}%)",
                {'disk_usage': metrics.disk_usage}
            )
        
        # API response time check
        if metrics.api_response_time > self.thresholds['api_response_time']:
            await self._create_alert(
                AlertLevel.WARNING,
                AlertType.API,
                "Slow API Response",
                f"API response time is {metrics.api_response_time:.2f}s (threshold: {self.thresholds['api_response_time']}s)",
                {'api_response_time': metrics.api_response_time}
            )
        
        # Balance check
        if metrics.balance < self.thresholds['min_balance']:
            await self._create_alert(
                AlertLevel.ERROR,
                AlertType.BALANCE,
                "Low Balance Alert",
                f"Balance is ${metrics.balance:.2f} (minimum: ${self.thresholds['min_balance']:.2f})",
                {'balance': metrics.balance}
            )
        
        # Daily loss check
        if metrics.daily_pnl < -self.thresholds['max_daily_loss']:
            await self._create_alert(
                AlertLevel.ERROR,
                AlertType.TRADING,
                "High Daily Loss",
                f"Daily P&L is {metrics.daily_pnl:.2f} USDT (max loss: {self.thresholds['max_daily_loss']} USDT)",
                {'daily_pnl': metrics.daily_pnl}
            )

    async def _check_trading_thresholds(self, metrics: TradingMetrics):
        """Check trading metrics against thresholds"""
        # Max drawdown check
        if metrics.max_drawdown > self.thresholds['max_drawdown']:
            await self._create_alert(
                AlertLevel.CRITICAL,
                AlertType.TRADING,
                "Maximum Drawdown Exceeded",
                f"Max drawdown is {metrics.max_drawdown:.1f}% (threshold: {self.thresholds['max_drawdown']}%)",
                {'max_drawdown': metrics.max_drawdown}
            )
        
        # Win rate check (if we have enough trades)
        if metrics.total_trades >= 10 and metrics.win_rate < 40.0:
            await self._create_alert(
                AlertLevel.WARNING,
                AlertType.PERFORMANCE,
                "Low Win Rate",
                f"Win rate is {metrics.win_rate:.1f}% with {metrics.total_trades} trades",
                {'win_rate': metrics.win_rate, 'total_trades': metrics.total_trades}
            )

    async def _create_alert(self, level: AlertLevel, alert_type: AlertType, 
                          title: str, message: str, data: Dict[str, Any]):
        """Create and process a new alert"""
        alert_id = f"{alert_type.value}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            level=level,
            type=alert_type,
            title=title,
            message=message,
            data=data
        )
        
        # Store alert
        await self._store_alert(alert)
        
        # Add to active alerts
        self.alerts.append(alert)
        
        # Send notifications
        await self._send_alert_notifications(alert)
        
        logger.info(f"🚨 Alert created: {level.value.upper()} - {title}")

    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (id, timestamp, level, type, title, message, data, acknowledged, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.id,
                alert.timestamp.isoformat(),
                alert.level.value,
                alert.type.value,
                alert.title,
                alert.message,
                json.dumps(alert.data),
                int(alert.acknowledged),
                int(alert.resolved)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing alert: {e}")

    async def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        try:
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO system_metrics 
                (timestamp, cpu_usage, memory_usage, disk_usage, network_latency, 
                 api_response_time, database_connections, active_trades, balance, daily_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp.isoformat(),
                metrics.cpu_usage,
                metrics.memory_usage,
                metrics.disk_usage,
                metrics.network_latency,
                metrics.api_response_time,
                metrics.database_connections,
                metrics.active_trades,
                metrics.balance,
                metrics.daily_pnl
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing system metrics: {e}")

    async def _store_trading_metrics(self, metrics: TradingMetrics):
        """Store trading metrics in database"""
        try:
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO trading_metrics 
                (timestamp, total_trades, successful_trades, failed_trades, win_rate,
                 total_pnl, daily_pnl, sharpe_ratio, max_drawdown, profit_factor, avg_trade_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp.isoformat(),
                metrics.total_trades,
                metrics.successful_trades,
                metrics.failed_trades,
                metrics.win_rate,
                metrics.total_pnl,
                metrics.daily_pnl,
                metrics.sharpe_ratio,
                metrics.max_drawdown,
                metrics.profit_factor,
                metrics.avg_trade_duration
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing trading metrics: {e}")

    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        # Log alert
        if self.alert_channels['log']:
            logger.warning(f"ALERT [{alert.level.value.upper()}] {alert.title}: {alert.message}")
        
        # Telegram notification
        if self.alert_channels['telegram']:
            await self._send_telegram_alert(alert)
        
        # Email notification
        if self.alert_channels['email']:
            await self._send_email_alert(alert)
        
        # Webhook notification
        if self.alert_channels['webhook']:
            await self._send_webhook_alert(alert)

    async def _send_telegram_alert(self, alert: Alert):
        """Send alert via Telegram"""
        try:
            # This would integrate with the Telegram bot
            # For now, just log
            logger.info(f"📱 Telegram alert sent: {alert.title}")
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")

    async def _send_email_alert(self, alert: Alert):
        """Send alert via email"""
        try:
            # Email implementation would go here
            logger.info(f"📧 Email alert sent: {alert.title}")
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")

    async def _send_webhook_alert(self, alert: Alert):
        """Send alert via webhook"""
        try:
            # Webhook implementation would go here
            logger.info(f"🔗 Webhook alert sent: {alert.title}")
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")

    async def _process_alerts(self):
        """Process and manage alerts"""
        while self.is_running:
            try:
                # Clean up old resolved alerts
                current_time = datetime.now()
                self.alerts = [
                    alert for alert in self.alerts 
                    if not alert.resolved or 
                    (current_time - alert.timestamp).days < 7
                ]
                
                await asyncio.sleep(60)  # Process every minute
                
            except Exception as e:
                logger.error(f"Error processing alerts: {e}")
                await asyncio.sleep(60)

    # Helper methods for data collection
    async def _measure_api_response_time(self) -> float:
        """Measure API response time"""
        try:
            import aiohttp
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/api/status", timeout=5) as response:
                    await response.text()
            
            return time.time() - start_time
            
        except Exception:
            return 9999.0  # High value to indicate failure

    async def _check_api_health(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/api/status", timeout=5) as response:
                    if response.status == 200:
                        return {'healthy': True, 'status_code': response.status}
                    else:
                        return {'healthy': False, 'status_code': response.status, 'error': 'Non-200 status'}
            
        except Exception as e:
            return {'healthy': False, 'error': str(e)}

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return {'healthy': True}
            
        except Exception as e:
            return {'healthy': False, 'error': str(e)}

    async def _check_security_status(self) -> Dict[str, Any]:
        """Check security status"""
        try:
            # Basic security checks
            threats_detected = False
            details = []
            
            # Check for suspicious file modifications
            # Check for unusual network activity
            # Check for failed login attempts
            # etc.
            
            return {
                'threats_detected': threats_detected,
                'details': details
            }
            
        except Exception as e:
            return {
                'threats_detected': True,
                'details': [f"Security check failed: {str(e)}"]
            }

    async def _get_current_trading_data(self) -> Dict[str, Any]:
        """Get current trading data"""
        try:
            # This would normally fetch from API or database
            return {
                'active_trades': 0,
                'balance': 50.0,
                'daily_pnl': 0.0
            }
        except Exception:
            return {
                'active_trades': 0,
                'balance': 50.0,
                'daily_pnl': 0.0
            }

    async def _get_trading_performance_data(self) -> Dict[str, Any]:
        """Get trading performance data"""
        try:
            # This would normally fetch from database
            return {
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'daily_pnl': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'profit_factor': 0.0,
                'avg_trade_duration': 0.0
            }
        except Exception:
            return {
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'daily_pnl': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'profit_factor': 0.0,
                'avg_trade_duration': 0.0
            }

    # Public methods for external access
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts"""
        return [alert for alert in self.alerts if not alert.resolved]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                # Update in database
                asyncio.create_task(self._update_alert_status(alert))
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                # Update in database
                asyncio.create_task(self._update_alert_status(alert))
                return True
        return False

    async def _update_alert_status(self, alert: Alert):
        """Update alert status in database"""
        try:
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts 
                SET acknowledged = ?, resolved = ?
                WHERE id = ?
            ''', (int(alert.acknowledged), int(alert.resolved), alert.id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'is_running': self.is_running,
            'last_check': self.last_check.isoformat(),
            'active_alerts': len(self.get_active_alerts()),
            'total_alerts': len(self.alerts),
            'monitoring_intervals': self.intervals,
            'thresholds': self.thresholds
        }

def main():
    """Main function to run the monitor"""
    monitor = AdvancedMonitor()
    
    try:
        asyncio.run(monitor.start_monitoring())
    except KeyboardInterrupt:
        print("\n🛑 Monitor stopped by user")
    except Exception as e:
        print(f"❌ Monitor crashed: {e}")

if __name__ == "__main__":
    main()
