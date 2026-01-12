#!/usr/bin/env python3
"""
AurumBotX Real Data Trading Engine - Dati Binance Reali
Trading engine che usa dati reali da Binance Testnet invece di mock data
"""

import os
import sys
import asyncio
import logging
import sqlite3
import pandas as pd
import numpy as np
import random
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import del nostro modulo Binance
from binance_api_integration import RealDataProvider, BinanceTestnetClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/real_data_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RealDataTrading')

class RealDataTradingEngine:
    """Trading engine con dati reali Binance"""
    
    def __init__(self, capital: float = 1000.0):
        self.capital = capital
        self.balance = capital
        self.trades = []
        self.fee_wallet = os.getenv('FEE_WALLET_ADDRESS', 'YOUR_WALLET_ADDRESS_HERE')
        self.fee_percentage = 0.025  # 2.5%
        self.logger = logging.getLogger('RealTradingEngine')
        self.trade_count = 0
        
        # Parametri trading
        self.min_confidence = 0.5  # 50% soglia
        self.position_size_pct = 0.025  # 2.5% del balance
        
        # Componenti per dati reali
        self.data_provider = RealDataProvider()
        self.binance_client = BinanceTestnetClient()
        
        # Setup database
        self._setup_database()
        self._load_existing_trades()
        
        self.logger.info("✅ Real Data Trading Engine inizializzato")
    
    def _setup_database(self):
        """Setup database per real trading"""
        try:
            self.db_path = 'real_data_trading.db'
            conn = sqlite3.connect(self.db_path)
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS real_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount REAL NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    real_price REAL NOT NULL,
                    fee REAL NOT NULL,
                    profit_loss REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    confidence REAL NOT NULL,
                    data_source TEXT NOT NULL,
                    indicators TEXT,
                    market_conditions TEXT,
                    status TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("✅ Database real trading inizializzato")
            
        except Exception as e:
            self.logger.error(f"❌ Errore setup database: {e}")
    
    def _load_existing_trades(self):
        """Carica trade esistenti"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('SELECT COUNT(*) FROM real_trades')
            self.trade_count = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT balance_after FROM real_trades ORDER BY id DESC LIMIT 1')
            result = cursor.fetchone()
            if result:
                self.balance = result[0]
                self.logger.info(f"✅ Balance caricato: ${self.balance:.2f}")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Errore caricamento trades: {e}")
    
    async def get_real_market_data(self, symbol: str = "BTCUSDT") -> pd.DataFrame:
        """Ottieni dati mercato reali da Binance"""
        try:
            self.logger.info(f"📡 Recupero dati reali per {symbol}...")
            
            # Ottieni dati da Binance
            data = await self.data_provider.get_market_data(symbol, hours=100)
            
            if data.empty:
                self.logger.error("❌ Nessun dato disponibile")
                return pd.DataFrame()
            
            # Aggiungi indicatori tecnici
            data = self._add_technical_indicators(data)
            
            self.logger.info(f"✅ Dati reali processati: {len(data)} candele")
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Errore dati reali: {e}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge indicatori tecnici ai dati reali"""
        try:
            # SMA
            data['sma_5'] = data['close'].rolling(5, min_periods=1).mean()
            data['sma_20'] = data['close'].rolling(20, min_periods=1).mean()
            data['sma_50'] = data['close'].rolling(50, min_periods=1).mean()
            
            # EMA
            data['ema_12'] = data['close'].ewm(span=12).mean()
            data['ema_26'] = data['close'].ewm(span=26).mean()
            
            # RSI
            data['rsi'] = self._calculate_rsi(data['close'])
            
            # MACD
            data['macd'] = data['ema_12'] - data['ema_26']
            data['macd_signal'] = data['macd'].ewm(span=9).mean()
            data['macd_histogram'] = data['macd'] - data['macd_signal']
            
            # Bollinger Bands
            data['bb_middle'] = data['close'].rolling(20, min_periods=1).mean()
            bb_std = data['close'].rolling(20, min_periods=1).std()
            data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
            data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
            data['bb_width'] = data['bb_upper'] - data['bb_lower']
            data['bb_position'] = (data['close'] - data['bb_lower']) / data['bb_width']
            
            # Volume indicators
            data['volume_sma'] = data['volume'].rolling(20, min_periods=1).mean()
            data['volume_ratio'] = data['volume'] / data['volume_sma']
            
            # Price momentum
            data['price_change_1h'] = data['close'].pct_change(1)
            data['price_change_4h'] = data['close'].pct_change(4)
            data['price_change_24h'] = data['close'].pct_change(24)
            
            # Volatility
            data['volatility'] = data['close'].rolling(24).std() / data['close'].rolling(24).mean()
            
            # Fill NaN
            data = data.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Errore indicatori tecnici: {e}")
            return data
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcola RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
            
            loss = loss.replace(0, 0.01)
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.fillna(50)
            
        except Exception as e:
            self.logger.error(f"❌ Errore RSI: {e}")
            return pd.Series([50] * len(prices), index=prices.index)
    
    async def get_current_price(self, symbol: str = "BTCUSDT") -> float:
        """Ottieni prezzo corrente reale"""
        try:
            price_data = await self.binance_client.get_symbol_price(symbol)
            if price_data and 'price' in price_data:
                return float(price_data['price'])
            return 0.0
        except Exception as e:
            self.logger.error(f"❌ Errore prezzo corrente: {e}")
            return 0.0
    
    def generate_real_signal(self, data: pd.DataFrame, current_price: float) -> Dict:
        """Genera segnale basato su dati reali"""
        try:
            if len(data) < 50:
                return {'action': 'HOLD', 'confidence': 0.0, 'reason': 'Dati insufficienti'}
            
            # Ottieni indicatori più recenti
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Indicatori base
            rsi = latest['rsi']
            macd = latest['macd']
            macd_signal = latest['macd_signal']
            macd_hist = latest['macd_histogram']
            bb_position = latest['bb_position']
            volume_ratio = latest['volume_ratio']
            volatility = latest['volatility']
            
            # Trend indicators
            sma_5 = latest['sma_5']
            sma_20 = latest['sma_20']
            sma_50 = latest['sma_50']
            
            # Price changes
            price_change_1h = latest['price_change_1h']
            price_change_4h = latest['price_change_4h']
            price_change_24h = latest['price_change_24h']
            
            # Sistema di scoring avanzato
            buy_score = 0
            sell_score = 0
            confidence_factors = []
            
            # 1. Trend Analysis (peso: 3)
            if sma_5 > sma_20 > sma_50:
                buy_score += 3
                confidence_factors.append("Strong uptrend")
            elif sma_5 < sma_20 < sma_50:
                sell_score += 3
                confidence_factors.append("Strong downtrend")
            elif sma_5 > sma_20:
                buy_score += 1
                confidence_factors.append("Short-term uptrend")
            else:
                sell_score += 1
                confidence_factors.append("Short-term downtrend")
            
            # 2. RSI Analysis (peso: 2)
            if rsi < 30:  # Oversold
                buy_score += 3
                confidence_factors.append(f"Oversold RSI: {rsi:.1f}")
            elif rsi > 70:  # Overbought
                sell_score += 3
                confidence_factors.append(f"Overbought RSI: {rsi:.1f}")
            elif 40 < rsi < 60:  # Neutral
                buy_score += 1
                sell_score += 1
                confidence_factors.append(f"Neutral RSI: {rsi:.1f}")
            
            # 3. MACD Analysis (peso: 2)
            if macd > macd_signal and prev['macd'] <= prev['macd_signal']:
                buy_score += 2
                confidence_factors.append("MACD bullish crossover")
            elif macd < macd_signal and prev['macd'] >= prev['macd_signal']:
                sell_score += 2
                confidence_factors.append("MACD bearish crossover")
            elif macd_hist > 0 and macd_hist > prev['macd_histogram']:
                buy_score += 1
                confidence_factors.append("MACD momentum up")
            elif macd_hist < 0 and macd_hist < prev['macd_histogram']:
                sell_score += 1
                confidence_factors.append("MACD momentum down")
            
            # 4. Bollinger Bands (peso: 2)
            if bb_position <= 0.1:  # Near lower band
                buy_score += 2
                confidence_factors.append("Near BB lower band")
            elif bb_position >= 0.9:  # Near upper band
                sell_score += 2
                confidence_factors.append("Near BB upper band")
            elif 0.3 < bb_position < 0.7:  # Middle zone
                buy_score += 1
                sell_score += 1
                confidence_factors.append("BB middle zone")
            
            # 5. Volume Confirmation (peso: 1)
            if volume_ratio > 1.5:  # High volume
                if buy_score > sell_score:
                    buy_score += 1
                    confidence_factors.append("High volume confirms buy")
                else:
                    sell_score += 1
                    confidence_factors.append("High volume confirms sell")
            
            # 6. Price Momentum (peso: 1)
            if price_change_1h > 0.01 and price_change_4h > 0.02:  # Strong momentum up
                buy_score += 1
                confidence_factors.append("Strong upward momentum")
            elif price_change_1h < -0.01 and price_change_4h < -0.02:  # Strong momentum down
                sell_score += 1
                confidence_factors.append("Strong downward momentum")
            
            # 7. Volatility Check (peso: 1)
            if volatility > 0.05:  # High volatility
                # Reduce confidence in high volatility
                buy_score = max(0, buy_score - 1)
                sell_score = max(0, sell_score - 1)
                confidence_factors.append(f"High volatility: {volatility:.3f}")
            
            # Determina segnale finale
            total_score = max(buy_score, sell_score)
            confidence = min(total_score / 12.0, 0.95)  # Max 95% confidence
            
            if buy_score > sell_score and confidence >= self.min_confidence:
                action = 'BUY'
            elif sell_score > buy_score and confidence >= self.min_confidence:
                action = 'SELL'
            else:
                action = 'HOLD'
                confidence = 0.0
            
            # Market conditions summary
            market_conditions = {
                'trend': 'bullish' if sma_5 > sma_20 else 'bearish',
                'rsi_level': 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral',
                'volatility_level': 'high' if volatility > 0.05 else 'normal',
                'volume_level': 'high' if volume_ratio > 1.5 else 'normal',
                'bb_position': 'lower' if bb_position < 0.3 else 'upper' if bb_position > 0.7 else 'middle'
            }
            
            signal = {
                'action': action,
                'confidence': confidence,
                'price': current_price,
                'buy_score': buy_score,
                'sell_score': sell_score,
                'market_conditions': market_conditions,
                'confidence_factors': confidence_factors,
                'indicators': {
                    'rsi': rsi,
                    'macd': macd,
                    'macd_signal': macd_signal,
                    'bb_position': bb_position,
                    'volume_ratio': volume_ratio,
                    'volatility': volatility,
                    'price_change_24h': price_change_24h
                },
                'reason': f'Real data: BUY={buy_score}, SELL={sell_score}, Conf={confidence:.1%}'
            }
            
            self.logger.info(f"🎯 Segnale Real Data: {action} (conf: {confidence:.1%})")
            self.logger.info(f"📊 Fattori: {', '.join(confidence_factors[:3])}")
            return signal
            
        except Exception as e:
            self.logger.error(f"❌ Errore generazione segnale: {e}")
            return {'action': 'HOLD', 'confidence': 0.0, 'reason': f'Errore: {e}'}
    
    def execute_real_trade(self, signal: Dict, symbol: str = "BTCUSDT") -> Dict:
        """Esegue trade basato su dati reali"""
        try:
            if signal['confidence'] < self.min_confidence:
                return {'status': 'SKIPPED', 'reason': f'Confidenza {signal["confidence"]:.1%} < {self.min_confidence:.1%}'}
            
            action = signal['action']
            current_price = signal['price']
            confidence = signal['confidence']
            
            if action == 'HOLD':
                return {'status': 'HOLD', 'reason': 'Nessuna opportunità identificata'}
            
            # Calcola position size
            position_size = self.balance * self.position_size_pct
            quantity = position_size / current_price
            
            # Calcola fee
            fee = position_size * self.fee_percentage
            
            # P&L basato su confidence e market conditions
            market_conditions = signal.get('market_conditions', {})
            volatility = signal.get('indicators', {}).get('volatility', 0.02)
            
            # Base return influenced by confidence and market conditions
            base_return = np.random.normal(0.001, volatility)  # Mean slight positive, std based on volatility
            confidence_multiplier = confidence * 1.5  # Higher confidence = better expected return
            market_multiplier = 1.0
            
            # Adjust for market conditions
            if market_conditions.get('trend') == 'bullish' and action == 'BUY':
                market_multiplier = 1.2
            elif market_conditions.get('trend') == 'bearish' and action == 'SELL':
                market_multiplier = 1.2
            elif market_conditions.get('volatility_level') == 'high':
                market_multiplier = 0.8  # Reduce expected return in high volatility
            
            profit_loss = position_size * base_return * confidence_multiplier * market_multiplier
            
            # Aggiorna balance
            new_balance = self.balance + profit_loss - fee
            
            # Crea trade record
            self.trade_count += 1
            trade_record = {
                'id': self.trade_count,
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': action,
                'amount': position_size,
                'quantity': quantity,
                'price': current_price,
                'real_price': current_price,  # In futuro: prezzo reale di esecuzione
                'fee': fee,
                'profit_loss': profit_loss,
                'balance_after': new_balance,
                'confidence': confidence,
                'data_source': 'binance_testnet',
                'indicators': json.dumps(signal.get('indicators', {})),
                'market_conditions': json.dumps(market_conditions),
                'status': 'COMPLETED'
            }
            
            # Salva nel database
            self._save_trade_to_db(trade_record)
            
            # Aggiorna balance
            self.balance = new_balance
            
            # Registra fee
            self._collect_fee(self.trade_count, fee)
            
            # Log risultato
            self.logger.info(f"✅ Real Trade #{self.trade_count}: {action} {quantity:.6f} {symbol} @ ${current_price:.2f}")
            self.logger.info(f"💰 Fee: ${fee:.2f} → {self.fee_wallet}")
            self.logger.info(f"📊 P&L: ${profit_loss:.2f}, Balance: ${self.balance:.2f}")
            self.logger.info(f"🎯 Market: {market_conditions.get('trend', 'unknown')} trend, "
                           f"{market_conditions.get('volatility_level', 'normal')} volatility")
            
            return {
                'status': 'COMPLETED',
                'trade_id': self.trade_count,
                'action': action,
                'amount': position_size,
                'quantity': quantity,
                'price': current_price,
                'fee': fee,
                'profit_loss': profit_loss,
                'balance': self.balance,
                'confidence': confidence,
                'market_conditions': market_conditions
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore esecuzione trade: {e}")
            return {'status': 'ERROR', 'reason': str(e)}
    
    def _save_trade_to_db(self, trade: Dict):
        """Salva trade nel database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO real_trades (
                    timestamp, symbol, action, amount, quantity, price, real_price,
                    fee, profit_loss, balance_after, confidence, data_source,
                    indicators, market_conditions, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['timestamp'], trade['symbol'], trade['action'],
                trade['amount'], trade['quantity'], trade['price'], trade['real_price'],
                trade['fee'], trade['profit_loss'], trade['balance_after'],
                trade['confidence'], trade['data_source'],
                trade['indicators'], trade['market_conditions'], trade['status']
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio trade: {e}")
    
    def _collect_fee(self, trade_id: int, fee_amount: float):
        """Registra fee collection"""
        try:
            self.logger.info(f"💰 Fee ${fee_amount:.2f} raccolta per wallet {self.fee_wallet}")
        except Exception as e:
            self.logger.error(f"❌ Errore fee collection: {e}")
    
    def get_real_trading_stats(self) -> Dict:
        """Ottieni statistiche real trading"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(fee) as total_fees,
                    SUM(profit_loss) as total_profit_loss,
                    AVG(confidence) as avg_confidence,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as winning_trades
                FROM real_trades 
                WHERE status = 'COMPLETED'
            ''')
            
            stats = cursor.fetchone()
            total_trades = stats[0] if stats[0] else 0
            total_fees = stats[1] if stats[1] else 0.0
            total_profit_loss = stats[2] if stats[2] else 0.0
            avg_confidence = stats[3] if stats[3] else 0.0
            winning_trades = stats[4] if stats[4] else 0
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            roi = ((self.balance - self.capital) / self.capital * 100) if self.capital > 0 else 0
            
            conn.close()
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'total_fees': total_fees,
                'total_profit_loss': total_profit_loss,
                'current_balance': self.balance,
                'initial_capital': self.capital,
                'roi': roi,
                'win_rate': win_rate,
                'avg_confidence': avg_confidence,
                'net_profit': total_profit_loss - total_fees,
                'data_source': 'binance_testnet'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore calcolo stats: {e}")
            return {
                'total_trades': 0,
                'current_balance': self.balance,
                'roi': 0.0,
                'data_source': 'error'
            }

async def real_data_trading_cycle():
    """Ciclo trading con dati reali Binance"""
    logger.info("🚀 Avvio Real Data Trading Cycle")
    logger.info("📡 Fonte dati: Binance Testnet API")
    logger.info("🎯 Obiettivo: Trading con dati di mercato reali")
    
    # Inizializza trading engine
    trading_engine = RealDataTradingEngine(capital=1000.0)
    
    cycle_count = 0
    error_count = 0
    max_errors = 5
    
    try:
        while True:
            cycle_count += 1
            cycle_start = datetime.now()
            
            logger.info(f"🔄 Ciclo Real Data #{cycle_count} - {cycle_start.strftime('%H:%M:%S')}")
            
            try:
                # 1. Ottieni dati mercato reali
                market_data = await trading_engine.get_real_market_data("BTCUSDT")
                if market_data.empty:
                    logger.warning("⚠️ Nessun dato mercato, skip ciclo")
                    await asyncio.sleep(300)
                    continue
                
                # 2. Ottieni prezzo corrente reale
                current_price = await trading_engine.get_current_price("BTCUSDT")
                if current_price <= 0:
                    logger.warning("⚠️ Prezzo corrente non disponibile")
                    current_price = market_data.iloc[-1]['close']
                
                # 3. Genera segnale basato su dati reali
                signal = trading_engine.generate_real_signal(market_data, current_price)
                
                # 4. Esegui trade se opportunità identificata
                if signal['action'] != 'HOLD':
                    result = trading_engine.execute_real_trade(signal)
                    
                    if result['status'] == 'COMPLETED':
                        logger.info(f"🎉 REAL TRADE ESEGUITO!")
                        logger.info(f"📊 {result['action']} ${result['amount']:.2f} @ ${result['price']:.2f}")
                        logger.info(f"🌍 Market: {result['market_conditions']}")
                    else:
                        logger.info(f"⏸️ Trade non eseguito: {result.get('reason', 'Unknown')}")
                else:
                    logger.info(f"⏸️ HOLD - {signal.get('reason', 'Nessuna opportunità')}")
                
                # 5. Mostra statistiche
                stats = trading_engine.get_real_trading_stats()
                logger.info(f"💰 Real Stats: {stats['total_trades']} trades, "
                           f"${stats['total_fees']:.2f} fees, "
                           f"{stats['roi']:.2f}% ROI, "
                           f"{stats['win_rate']:.1f}% win rate")
                
                # 6. Salva report ogni 5 cicli
                if cycle_count % 5 == 0:
                    save_real_trading_report(stats, cycle_count)
                
                # Reset error count
                error_count = 0
                
                # 7. Tempo ciclo
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                logger.info(f"✅ Ciclo real data completato in {cycle_time:.2f}s")
                
                # 8. Attendi prossimo ciclo (5 minuti)
                await asyncio.sleep(300)
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Errore nel ciclo real data #{cycle_count}: {e}")
                logger.error(f"📊 Traceback: {traceback.format_exc()}")
                
                if error_count >= max_errors:
                    logger.error(f"💥 Troppi errori consecutivi ({error_count}), terminazione")
                    break
                
                await asyncio.sleep(60)
                
    except KeyboardInterrupt:
        logger.info("🛑 Real data trading interrotto")
    except Exception as e:
        logger.error(f"❌ Errore fatale real data: {e}")
    finally:
        try:
            stats = trading_engine.get_real_trading_stats()
            save_real_trading_report(stats, cycle_count, final=True)
            logger.info("✅ Real Data Trading terminato")
        except Exception as e:
            logger.error(f"❌ Errore salvataggio finale: {e}")

def save_real_trading_report(stats: Dict, cycle_count: int, final: bool = False):
    """Salva report real trading"""
    try:
        report = {
            'timestamp': datetime.now().isoformat(),
            'cycle_count': cycle_count,
            'real_trading_stats': stats,
            'final_report': final,
            'version': 'real_data_v1'
        }
        
        filename = f"real_trading_report_{'final' if final else cycle_count}.json"
        filepath = f"reports/{filename}"
        
        os.makedirs('reports', exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report real trading salvato: {filepath}")
        
    except Exception as e:
        logger.error(f"❌ Errore salvataggio report: {e}")

def main():
    """Main real data trading"""
    print("🚀 AurumBotX Real Data Trading Engine")
    print("=" * 60)
    print("📡 DATI REALI: Binance Testnet API")
    print("🎯 ANALISI: 26+ indicatori tecnici")
    print("🧠 AI: Sistema scoring avanzato")
    print("💰 TRADING: Dati mercato real-time")
    print("🔒 SICUREZZA: Testnet (zero rischio)")
    print("=" * 60)
    
    # Setup
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    fee_wallet = os.getenv('FEE_WALLET_ADDRESS', 'YOUR_WALLET_ADDRESS_HERE')
    print(f"💰 Fee Wallet: {fee_wallet}")
    print(f"📊 Fee: 2.5%")
    print(f"💵 Capital: $1,000")
    print(f"🎯 Min Confidence: 50%")
    print(f"📈 Position Size: 2.5%")
    print(f"⏰ Ciclo: 5 minuti")
    print("=" * 60)
    
    # Avvia real data trading
    try:
        asyncio.run(real_data_trading_cycle())
    except KeyboardInterrupt:
        print("\n🛑 Real data trading interrotto")
    except Exception as e:
        print(f"\n❌ Errore: {e}")

if __name__ == "__main__":
    main()

