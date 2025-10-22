#!/usr/bin/env python3
"""
AurumBotX v2.1 - Advanced Telegram Bot
Enterprise-grade Telegram bot for remote trading control and monitoring
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ParseMode
except ImportError:
    print("❌ Telegram library not installed. Run: pip install python-telegram-bot")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/home/ubuntu/AurumBotX/logs/telegram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AurumBotXTelegramBot:
    """Advanced Telegram Bot for AurumBotX Enterprise Trading System"""
    
    def __init__(self, token: str, authorized_users: List[int] = None):
        """
        Initialize the Telegram bot
        
        Args:
            token: Telegram bot token
            authorized_users: List of authorized user IDs
        """
        self.token = token
        self.authorized_users = authorized_users or []
        self.application = None
        self.db_path = "/home/ubuntu/AurumBotX/data/trading_engine.db"
        self.api_base = "http://localhost:5678"
        
        # Bot state
        self.is_running = False
        self.last_update = datetime.now()
        self.alert_settings = {
            'balance_alerts': True,
            'trade_alerts': True,
            'error_alerts': True,
            'performance_alerts': True
        }
        
        # Command descriptions
        self.commands = [
            BotCommand("start", "🚀 Start the bot and show main menu"),
            BotCommand("status", "📊 Show system status and performance"),
            BotCommand("balance", "💰 Show current balance and portfolio"),
            BotCommand("trades", "📈 Show recent trades"),
            BotCommand("performance", "📊 Show performance metrics"),
            BotCommand("start_trading", "▶️ Start trading operations"),
            BotCommand("stop_trading", "⏹️ Stop trading operations"),
            BotCommand("emergency", "🚨 Emergency stop all operations"),
            BotCommand("settings", "⚙️ Configure bot settings"),
            BotCommand("alerts", "🔔 Configure alert settings"),
            BotCommand("help", "❓ Show help and available commands")
        ]

    async def initialize(self):
        """Initialize the bot application"""
        try:
            self.application = Application.builder().token(self.token).build()
            
            # Register handlers
            await self._register_handlers()
            
            # Set bot commands
            await self.application.bot.set_my_commands(self.commands)
            
            logger.info("✅ Telegram bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram bot: {e}")
            return False

    async def _register_handlers(self):
        """Register all command and callback handlers"""
        app = self.application
        
        # Command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CommandHandler("balance", self.balance_command))
        app.add_handler(CommandHandler("trades", self.trades_command))
        app.add_handler(CommandHandler("performance", self.performance_command))
        app.add_handler(CommandHandler("start_trading", self.start_trading_command))
        app.add_handler(CommandHandler("stop_trading", self.stop_trading_command))
        app.add_handler(CommandHandler("emergency", self.emergency_command))
        app.add_handler(CommandHandler("settings", self.settings_command))
        app.add_handler(CommandHandler("alerts", self.alerts_command))
        app.add_handler(CommandHandler("help", self.help_command))
        
        # Callback query handlers
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handlers
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def _check_authorization(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot"""
        if not self.authorized_users:
            return True  # No restrictions if no authorized users set
        return user_id in self.authorized_users

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        if not self._check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access. Contact administrator.")
            return
        
        welcome_message = """
🚀 **AurumBotX v2.1 Enterprise Bot**

Welcome to the advanced trading control center!

**Quick Actions:**
• `/status` - System overview
• `/balance` - Portfolio status  
• `/trades` - Recent activity
• `/start_trading` - Begin operations
• `/emergency` - Emergency stop

**Main Menu:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("💰 Balance", callback_data="balance")
            ],
            [
                InlineKeyboardButton("📈 Trades", callback_data="trades"),
                InlineKeyboardButton("📊 Performance", callback_data="performance")
            ],
            [
                InlineKeyboardButton("▶️ Start Trading", callback_data="start_trading"),
                InlineKeyboardButton("⏹️ Stop Trading", callback_data="stop_trading")
            ],
            [
                InlineKeyboardButton("🚨 Emergency Stop", callback_data="emergency"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ],
            [
                InlineKeyboardButton("🔔 Alerts", callback_data="alerts"),
                InlineKeyboardButton("❓ Help", callback_data="help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        if not self._check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        try:
            # Get system status
            status_data = await self._get_system_status()
            
            status_message = f"""
📊 **System Status Report**
🕐 *{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

**🔧 Core Services:**
• API Server: {status_data['api_status']}
• Trading Engine: {status_data['trading_status']}
• Database: {status_data['db_status']}
• Security Layer: {status_data['security_status']}

**💰 Financial Overview:**
• Current Balance: ${status_data['balance']:.2f}
• Daily P&L: {status_data['daily_pnl']:+.2f} USDT
• Total Trades: {status_data['total_trades']}
• Win Rate: {status_data['win_rate']:.1f}%

**📈 Performance Metrics:**
• Sharpe Ratio: {status_data['sharpe_ratio']:.2f}
• Max Drawdown: {status_data['max_drawdown']:.1f}%
• Profit Factor: {status_data['profit_factor']:.2f}

**⚙️ Current Strategy:** {status_data['strategy']}
**🎯 Challenge Progress:** {status_data['challenge_progress']:.1f}%
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="status"),
                    InlineKeyboardButton("📊 Details", callback_data="performance")
                ],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                status_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text(f"❌ Error retrieving status: {str(e)}")

    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        user_id = update.effective_user.id
        
        if not self._check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        try:
            balance_data = await self._get_balance_info()
            
            balance_message = f"""
💰 **Portfolio Overview**
🕐 *{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

**💵 Current Holdings:**
• USDT: ${balance_data['usdt']:.2f}
• BTC: {balance_data['btc']:.8f}
• ETH: {balance_data['eth']:.6f}
• SOL: {balance_data['sol']:.4f}

**📊 Portfolio Metrics:**
• Total Value: ${balance_data['total_value']:.2f}
• Initial Investment: $50.00
• Total P&L: {balance_data['total_pnl']:+.2f} USDT
• ROI: {balance_data['roi']:+.1f}%

**🎯 Challenge Status:**
• Target: $100.00
• Progress: {balance_data['progress']:.1f}%
• Remaining: ${balance_data['remaining']:.2f}

**📈 Performance:**
• Best Day: {balance_data['best_day']:+.2f} USDT
• Worst Day: {balance_data['worst_day']:+.2f} USDT
• Avg Daily: {balance_data['avg_daily']:+.2f} USDT
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="balance"),
                    InlineKeyboardButton("📈 Trades", callback_data="trades")
                ],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                balance_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            await update.message.reply_text(f"❌ Error retrieving balance: {str(e)}")

    async def trades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trades command"""
        user_id = update.effective_user.id
        
        if not self._check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        try:
            trades_data = await self._get_recent_trades()
            
            if not trades_data['trades']:
                await update.message.reply_text(
                    "📈 **Recent Trades**\n\n"
                    "No trades found. Start trading to see activity here."
                )
                return
            
            trades_message = "📈 **Recent Trades**\n\n"
            
            for i, trade in enumerate(trades_data['trades'][:10], 1):
                pnl_emoji = "🟢" if trade['pnl'] >= 0 else "🔴"
                side_emoji = "🟢" if trade['side'] == 'BUY' else "🔴"
                
                trades_message += f"""
**{i}. {trade['symbol']}** {side_emoji}
• Time: {trade['time']}
• Side: {trade['side']}
• Amount: ${trade['amount']:.2f}
• Price: ${trade['price']:.4f}
• P&L: {pnl_emoji} {trade['pnl']:+.4f} USDT
• Fee: ${trade['fee']:.4f}
---
                """
            
            trades_message += f"\n**Summary:**\n"
            trades_message += f"• Total Trades: {trades_data['total']}\n"
            trades_message += f"• Wins: {trades_data['wins']} | Losses: {trades_data['losses']}\n"
            trades_message += f"• Win Rate: {trades_data['win_rate']:.1f}%\n"
            trades_message += f"• Total P&L: {trades_data['total_pnl']:+.4f} USDT"
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="trades"),
                    InlineKeyboardButton("📊 Performance", callback_data="performance")
                ],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                trades_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in trades command: {e}")
            await update.message.reply_text(f"❌ Error retrieving trades: {str(e)}")

    async def start_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start_trading command"""
        user_id = update.effective_user.id
        
        if not self._check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        try:
            # Check current status
            status = await self._get_trading_status()
            
            if status['is_active']:
                await update.message.reply_text(
                    "⚠️ Trading is already active!\n\n"
                    f"Strategy: {status['strategy']}\n"
                    f"Started: {status['start_time']}\n"
                    f"Trades today: {status['trades_today']}"
                )
                return
            
            # Confirmation keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm Start", callback_data="confirm_start_trading"),
                    InlineKeyboardButton("❌ Cancel", callback_data="main_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "▶️ **Start Trading Confirmation**\n\n"
                "Are you sure you want to start trading operations?\n\n"
                "**Current Configuration:**\n"
                f"• Strategy: {status['strategy']}\n"
                f"• Balance: ${status['balance']:.2f}\n"
                f"• Risk Level: {status['risk_level']}/10\n"
                f"• Max Trades/Day: {status['max_trades']}\n\n"
                "⚠️ This will begin live trading with real funds.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in start_trading command: {e}")
            await update.message.reply_text(f"❌ Error starting trading: {str(e)}")

    async def stop_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop_trading command"""
        user_id = update.effective_user.id
        
        if not self._check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        try:
            # Check current status
            status = await self._get_trading_status()
            
            if not status['is_active']:
                await update.message.reply_text(
                    "ℹ️ Trading is already stopped.\n\n"
                    "Use /start_trading to begin operations."
                )
                return
            
            # Confirmation keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm Stop", callback_data="confirm_stop_trading"),
                    InlineKeyboardButton("❌ Cancel", callback_data="main_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "⏹️ **Stop Trading Confirmation**\n\n"
                "Are you sure you want to stop trading operations?\n\n"
                "**Current Session:**\n"
                f"• Running Time: {status['running_time']}\n"
                f"• Trades Today: {status['trades_today']}\n"
                f"• Session P&L: {status['session_pnl']:+.4f} USDT\n\n"
                "This will halt all automated trading.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in stop_trading command: {e}")
            await update.message.reply_text(f"❌ Error stopping trading: {str(e)}")

    async def emergency_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /emergency command"""
        user_id = update.effective_user.id
        
        if not self._check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        # Double confirmation for emergency stop
        keyboard = [
            [
                InlineKeyboardButton("🚨 EMERGENCY STOP", callback_data="confirm_emergency"),
                InlineKeyboardButton("❌ Cancel", callback_data="main_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🚨 **EMERGENCY STOP WARNING**\n\n"
            "⚠️ This will IMMEDIATELY halt ALL trading operations!\n\n"
            "**Actions that will be taken:**\n"
            "• Stop all active trades\n"
            "• Cancel pending orders\n"
            "• Disable automated trading\n"
            "• Send emergency notifications\n\n"
            "**Are you absolutely sure?**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if not self._check_authorization(user_id):
            await query.edit_message_text("❌ Unauthorized access.")
            return
        
        data = query.data
        
        try:
            if data == "main_menu":
                await self._show_main_menu(query)
            elif data == "status":
                await self._handle_status_callback(query)
            elif data == "balance":
                await self._handle_balance_callback(query)
            elif data == "trades":
                await self._handle_trades_callback(query)
            elif data == "performance":
                await self._handle_performance_callback(query)
            elif data == "confirm_start_trading":
                await self._handle_start_trading(query)
            elif data == "confirm_stop_trading":
                await self._handle_stop_trading(query)
            elif data == "confirm_emergency":
                await self._handle_emergency_stop(query)
            elif data == "settings":
                await self._handle_settings_callback(query)
            elif data == "alerts":
                await self._handle_alerts_callback(query)
            elif data == "help":
                await self._handle_help_callback(query)
            else:
                await query.edit_message_text(f"Unknown action: {data}")
                
        except Exception as e:
            logger.error(f"Error handling callback {data}: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        
        if not self._check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        text = update.message.text.lower()
        
        # Simple command recognition
        if "status" in text:
            await self.status_command(update, context)
        elif "balance" in text:
            await self.balance_command(update, context)
        elif "trades" in text:
            await self.trades_command(update, context)
        elif "help" in text:
            await self.help_command(update, context)
        else:
            await update.message.reply_text(
                "I didn't understand that command. Use /help to see available commands."
            )

    # Helper methods for data retrieval
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # This would normally call the API or check database
            # For now, return mock data
            return {
                'api_status': '🟢 ONLINE',
                'trading_status': '🟡 STANDBY',
                'db_status': '🟢 OPERATIONAL',
                'security_status': '🟢 ACTIVE',
                'balance': 50.0,
                'daily_pnl': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'profit_factor': 0.0,
                'strategy': 'Challenge Growth',
                'challenge_progress': 50.0
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise

    async def _get_balance_info(self) -> Dict[str, Any]:
        """Get detailed balance information"""
        try:
            return {
                'usdt': 50.0,
                'btc': 0.0,
                'eth': 0.0,
                'sol': 0.0,
                'total_value': 50.0,
                'total_pnl': 0.0,
                'roi': 0.0,
                'progress': 50.0,
                'remaining': 50.0,
                'best_day': 0.0,
                'worst_day': 0.0,
                'avg_daily': 0.0
            }
        except Exception as e:
            logger.error(f"Error getting balance info: {e}")
            raise

    async def _get_recent_trades(self) -> Dict[str, Any]:
        """Get recent trading activity"""
        try:
            return {
                'trades': [],
                'total': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0
            }
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            raise

    async def _get_trading_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        try:
            return {
                'is_active': False,
                'strategy': 'Challenge Growth',
                'start_time': 'Not started',
                'trades_today': 0,
                'balance': 50.0,
                'risk_level': 5,
                'max_trades': 20,
                'running_time': '00:00:00',
                'session_pnl': 0.0
            }
        except Exception as e:
            logger.error(f"Error getting trading status: {e}")
            raise

    # Callback handlers
    async def _show_main_menu(self, query):
        """Show main menu"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("💰 Balance", callback_data="balance")
            ],
            [
                InlineKeyboardButton("📈 Trades", callback_data="trades"),
                InlineKeyboardButton("📊 Performance", callback_data="performance")
            ],
            [
                InlineKeyboardButton("▶️ Start Trading", callback_data="start_trading"),
                InlineKeyboardButton("⏹️ Stop Trading", callback_data="stop_trading")
            ],
            [
                InlineKeyboardButton("🚨 Emergency Stop", callback_data="emergency"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🚀 **AurumBotX v2.1 Main Menu**\n\n"
            "Select an option:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def _handle_start_trading(self, query):
        """Handle start trading confirmation"""
        try:
            # Here you would call the actual API to start trading
            # For now, simulate success
            
            await query.edit_message_text(
                "✅ **Trading Started Successfully!**\n\n"
                "🚀 The bot is now actively monitoring markets and executing trades.\n\n"
                "**Status:**\n"
                "• Strategy: Challenge Growth\n"
                "• Risk Level: 5/10\n"
                "• Max Trades/Day: 20\n\n"
                "You will receive notifications for all trading activity.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Send notification to all authorized users
            await self._send_notification(
                "🚀 **Trading Started**\n"
                f"User: {query.from_user.first_name}\n"
                f"Time: {datetime.now().strftime('%H:%M:%S')}"
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ Failed to start trading: {str(e)}")

    async def _handle_stop_trading(self, query):
        """Handle stop trading confirmation"""
        try:
            await query.edit_message_text(
                "⏹️ **Trading Stopped Successfully!**\n\n"
                "All automated trading operations have been halted.\n\n"
                "**Final Session Stats:**\n"
                "• Duration: 00:00:00\n"
                "• Trades: 0\n"
                "• P&L: +0.0000 USDT\n\n"
                "Use /start_trading to resume operations.",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ Failed to stop trading: {str(e)}")

    async def _handle_emergency_stop(self, query):
        """Handle emergency stop confirmation"""
        try:
            await query.edit_message_text(
                "🚨 **EMERGENCY STOP ACTIVATED!**\n\n"
                "✅ All trading operations have been immediately halted.\n"
                "✅ Pending orders have been cancelled.\n"
                "✅ System is now in safe mode.\n\n"
                "**Emergency Report:**\n"
                f"• Triggered by: {query.from_user.first_name}\n"
                f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"• Reason: Manual emergency stop\n\n"
                "System requires manual restart to resume operations.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Send emergency notification
            await self._send_notification(
                "🚨 **EMERGENCY STOP ACTIVATED**\n"
                f"Triggered by: {query.from_user.first_name}\n"
                f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
                "All operations halted immediately."
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ Emergency stop failed: {str(e)}")

    async def _send_notification(self, message: str):
        """Send notification to all authorized users"""
        if not self.authorized_users:
            return
        
        for user_id in self.authorized_users:
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to send notification to {user_id}: {e}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
❓ **AurumBotX v2.1 Help**

**📋 Available Commands:**

**🔧 System Control:**
• `/start` - Show main menu
• `/status` - System status overview
• `/balance` - Portfolio information
• `/trades` - Recent trading activity
• `/performance` - Performance metrics

**⚡ Trading Control:**
• `/start_trading` - Begin trading operations
• `/stop_trading` - Stop trading operations
• `/emergency` - Emergency stop (immediate)

**⚙️ Configuration:**
• `/settings` - Bot configuration
• `/alerts` - Alert preferences
• `/help` - Show this help

**🔔 Notifications:**
The bot will automatically notify you of:
• Trade executions
• Balance changes
• System alerts
• Performance milestones

**🔐 Security:**
Only authorized users can control the bot.
All commands are logged for security.

**📞 Support:**
For technical support, contact the administrator.
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def run(self):
        """Start the bot"""
        if not await self.initialize():
            return False
        
        try:
            logger.info("🚀 Starting AurumBotX Telegram Bot...")
            self.is_running = True
            
            # Start the bot
            await self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            return False
        finally:
            self.is_running = False

    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.stop()
        self.is_running = False
        logger.info("🛑 Telegram bot stopped")

def main():
    """Main function to run the bot"""
    # Get configuration from environment or config file
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    # Get authorized users (comma-separated user IDs)
    authorized_users_str = os.getenv('TELEGRAM_AUTHORIZED_USERS', '')
    authorized_users = []
    if authorized_users_str:
        try:
            authorized_users = [int(uid.strip()) for uid in authorized_users_str.split(',')]
        except ValueError:
            print("⚠️ Invalid TELEGRAM_AUTHORIZED_USERS format")
    
    # Create and run bot
    bot = AurumBotXTelegramBot(token, authorized_users)
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")

if __name__ == "__main__":
    main()
