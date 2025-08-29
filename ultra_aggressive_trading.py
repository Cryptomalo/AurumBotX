#!/usr/bin/env python3
"""
AurumBotX Ultra Aggressive Trading System
Sistema di trading ultra-aggressivo per massimizzare profitti
"""

import os
import sys
import asyncio
import logging
import json
import pandas as pd
import numpy as np
import sqlite3
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ultra_aggressive.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('UltraAggressive')

class UltraAggressiveConfig:
    """Configurazione ultra-aggressiva"""
    
    # PARAMETRI AGGRESSIVI
    INITIAL_BALANCE = 1000.0
    
    # POSITION SIZING (MOLTO PIÙ AGGRESSIVO)
    MIN_POSITION_SIZE_PERCENT = 5.0    # Era 3%, ora 5% minimo
    MAX_POSITION_SIZE_PERCENT = 12.0   # Era 5%, ora 12% massimo
    AGGRESSIVE_POSITION_SIZE_PERCENT = 8.0  # Standard aggressivo
    
    # CONFIDENCE THRESHOLDS (PIÙ BASSI = PIÙ TRADE)
    MIN_CONFIDENCE = 0.15              # Era 0.30, ora 0.15 (molto basso)
    AGGRESSIVE_CONFIDENCE = 0.25       # Era 0.60, ora 0.25
    HIGH_CONFIDENCE = 0.40             # Era 0.70, ora 0.40
    
    # PROFIT TARGETS (PIÙ ALTI)
    MIN_PROFIT_TARGET = 0.8            # Era 0.2%, ora 0.8%
    AGGRESSIVE_PROFIT_TARGET = 1.5     # Era 0.5%, ora 1.5%
    MAX_PROFIT_TARGET = 3.0            # Era 1.0%, ora 3.0%
    
    # RISK MANAGEMENT (PIÙ PERMISSIVO)
    MAX_LOSS_PER_TRADE = 2.0           # Era 1.0%, ora 2.0%
    MAX_DAILY_LOSS = 8.0               # Era 5.0%, ora 8.0%
    
    # FREQUENCY (PIÙ FREQUENTE)
    TRADE_INTERVAL_SECONDS = 90        # Era 120, ora 90 secondi
    FORCE_TRADE_AFTER_CYCLES = 2       # Era 3, ora 2 (più forzato)
    
    # VOLATILITY MULTIPLIERS (PIÙ AGGRESSIVI)
    HIGH_VOLATILITY_MULTIPLIER = 2.5   # Era 1.5, ora 2.5
    MEDIUM_VOLATILITY_MULTIPLIER = 1.8 # Era 1.2, ora 1.8
    LOW_VOLATILITY_MULTIPLIER = 1.3    # Era 1.0, ora 1.3
    
    # FEE STRUCTURE (PIÙ ALTA PER MAGGIORI PROFITTI)
    BASE_FEE_PERCENT = 0.08            # Era 0.075%, ora 0.08%
    AGGRESSIVE_FEE_PERCENT = 0.10      # Era 0.075%, ora 0.10%

class UltraAggressiveDataGenerator:
    """Generatore dati con volatilità aumentata"""
    
    def __init__(self):
        self.logger = logging.getLogger('UltraDataGen')
        self.last_price = 45000.0
        self.trend_direction = 1
        self.volatility_factor = 1.0
    
    def generate_ultra_volatile_data(self, symbol: str = "BTCUSDT", periods: int = 20) -> pd.DataFrame:
        """Genera dati con volatilità ultra-alta per più opportunità"""
        try:
            data = []
            current_price = self.last_price
            
            for i in range(periods):
                # Volatilità estrema (2-8% per candela)
                volatility = random.uniform(0.02, 0.08)  # Era 0.01-0.03, ora 0.02-0.08
                
                # Trend più pronunciati
                if random.random() < 0.3:  # 30% chance di cambio trend
                    self.trend_direction *= -1
                
                # Movimento prezzo più ampio
                price_change = current_price * volatility * self.trend_direction
                price_change += random.uniform(-current_price * 0.02, current_price * 0.02)  # Noise
                
                new_price = current_price + price_change
                new_price = max(new_price, 20000)  # Floor price
                new_price = min(new_price, 80000)  # Ceiling price
                
                # OHLC con spread più ampi
                high_spread = random.uniform(0.005, 0.025)  # Era 0.002-0.01, ora 0.005-0.025
                low_spread = random.uniform(0.005, 0.025)
                
                open_price = current_price
                close_price = new_price
                high_price = max(open_price, close_price) * (1 + high_spread)
                low_price = min(open_price, close_price) * (1 - low_spread)
                
                # Volume più alto per liquidità
                volume = random.uniform(5000, 25000)  # Era 1000-10000, ora 5000-25000
                
                timestamp = datetime.now() - timedelta(minutes=(periods-i)*5)
                
                data.append({
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
                
                current_price = new_price
            
            self.last_price = current_price
            df = pd.DataFrame(data)
            
            self.logger.info(f"✅ Dati ultra-volatili generati: {len(df)} candele per {symbol}")
            self.logger.info(f"📊 Range prezzo: ${df['low'].min():.0f} - ${df['high'].max():.0f}")
            self.logger.info(f"⚡ Volatilità media: {((df['high'] - df['low']) / df['close'] * 100).mean():.2f}%")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore generazione dati: {e}")
            return pd.DataFrame()

class UltraAggressiveAI:
    """AI ultra-aggressivo per segnali di trading"""
    
    def __init__(self):
        self.logger = logging.getLogger('UltraAI')
        self.config = UltraAggressiveConfig()
    
    def generate_ultra_aggressive_signal(self, data: pd.DataFrame) -> Dict:
        """Genera segnali ultra-aggressivi"""
        try:
            if data.empty or len(data) < 5:
                return {'action': 'HOLD', 'confidence': 0.0, 'reason': 'insufficient_data'}
            
            # Calcola indicatori con parametri aggressivi
            latest = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else latest
            
            # Price action aggressiva
            price_change = (latest['close'] - prev['close']) / prev['close']
            volatility = (latest['high'] - latest['low']) / latest['close']
            volume_ratio = latest['volume'] / data['volume'].mean() if len(data) > 1 else 1.0
            
            # Segnali ultra-aggressivi
            signals = []
            confidence_factors = []
            
            # 1. MOMENTUM AGGRESSIVO
            if abs(price_change) > 0.008:  # Era 0.005, ora 0.008 (movimento 0.8%+)
                action = 'BUY' if price_change > 0 else 'SELL'
                signals.append(action)
                confidence_factors.append(min(abs(price_change) * 50, 0.8))  # Max 80% da momentum
            
            # 2. VOLATILITY BREAKOUT
            if volatility > 0.015:  # Era 0.01, ora 0.015 (volatilità 1.5%+)
                # Alta volatilità = opportunità
                action = 'BUY' if price_change >= 0 else 'SELL'
                signals.append(action)
                confidence_factors.append(min(volatility * 30, 0.7))
            
            # 3. VOLUME SPIKE
            if volume_ratio > 1.8:  # Era 1.5, ora 1.8 (volume 80%+ sopra media)
                action = 'BUY' if price_change >= 0 else 'SELL'
                signals.append(action)
                confidence_factors.append(min((volume_ratio - 1) * 0.4, 0.6))
            
            # 4. TREND CONTINUATION (PIÙ AGGRESSIVO)
            if len(data) >= 3:
                trend_strength = 0
                for i in range(1, min(4, len(data))):
                    change = (data.iloc[-i]['close'] - data.iloc[-i-1]['close']) / data.iloc[-i-1]['close']
                    trend_strength += change
                
                if abs(trend_strength) > 0.015:  # Era 0.01, ora 0.015
                    action = 'BUY' if trend_strength > 0 else 'SELL'
                    signals.append(action)
                    confidence_factors.append(min(abs(trend_strength) * 25, 0.65))
            
            # 5. CONTRARIAN ULTRA-AGGRESSIVO (Nuova strategia)
            if abs(price_change) > 0.025:  # Movimento estremo 2.5%+
                # Contrarian: se scende molto, compra (e viceversa)
                action = 'BUY' if price_change < -0.025 else 'SELL'
                signals.append(action)
                confidence_factors.append(min(abs(price_change) * 20, 0.75))
            
            # 6. RANDOM AGGRESSIVE (Per aumentare frequenza)
            if random.random() < 0.4:  # 40% chance di segnale random
                action = random.choice(['BUY', 'SELL'])
                signals.append(action)
                confidence_factors.append(random.uniform(0.2, 0.45))
            
            # Determina azione finale
            if not signals:
                return {'action': 'HOLD', 'confidence': 0.0, 'reason': 'no_signals'}
            
            # Conta voti
            buy_votes = signals.count('BUY')
            sell_votes = signals.count('SELL')
            
            if buy_votes > sell_votes:
                final_action = 'BUY'
                confidence = np.mean([cf for i, cf in enumerate(confidence_factors) if signals[i] == 'BUY'])
            elif sell_votes > buy_votes:
                final_action = 'SELL'
                confidence = np.mean([cf for i, cf in enumerate(confidence_factors) if signals[i] == 'SELL'])
            else:
                # Pareggio - scegli quello con confidence più alta
                buy_conf = np.mean([cf for i, cf in enumerate(confidence_factors) if signals[i] == 'BUY']) if buy_votes > 0 else 0
                sell_conf = np.mean([cf for i, cf in enumerate(confidence_factors) if signals[i] == 'SELL']) if sell_votes > 0 else 0
                
                if buy_conf > sell_conf:
                    final_action = 'BUY'
                    confidence = buy_conf
                else:
                    final_action = 'SELL'
                    confidence = sell_conf
            
            # Boost confidence per trading più aggressivo
            confidence = min(confidence * 1.3, 0.95)  # Boost 30%, max 95%
            
            # Dettagli segnale
            signal_details = {
                'action': final_action,
                'confidence': confidence,
                'price': latest['close'],
                'volatility': volatility,
                'volume_ratio': volume_ratio,
                'price_change': price_change,
                'signals_count': len(signals),
                'buy_votes': buy_votes,
                'sell_votes': sell_votes,
                'reason': f"{len(signals)}_signals_{final_action.lower()}"
            }
            
            self.logger.info(f"🎯 Segnale ultra-aggressivo: {final_action} (conf: {confidence:.1%})")
            
            return signal_details
            
        except Exception as e:
            self.logger.error(f"❌ Errore generazione segnale: {e}")
            return {'action': 'HOLD', 'confidence': 0.0, 'reason': 'error'}

class UltraAggressiveEngine:
    """Engine di trading ultra-aggressivo"""
    
    def __init__(self):
        self.logger = logging.getLogger('UltraEngine')
        self.config = UltraAggressiveConfig()
        self.data_generator = UltraAggressiveDataGenerator()
        self.ai = UltraAggressiveAI()
        
        self.balance = self.config.INITIAL_BALANCE
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_fees = 0.0
        self.total_pnl = 0.0
        self.cycles_without_trade = 0
        
        # Database
        self.db_name = 'ultra_aggressive_trading.db'
        self.init_database()
    
    def init_database(self):
        """Inizializza database"""
        try:
            conn = sqlite3.connect(self.db_name)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ultra_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL NOT NULL,
                    confidence REAL NOT NULL,
                    profit_loss REAL NOT NULL,
                    fee REAL NOT NULL,
                    balance_before REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    position_size_percent REAL NOT NULL,
                    volatility REAL NOT NULL,
                    volume_ratio REAL NOT NULL,
                    signals_count INTEGER NOT NULL,
                    reason TEXT
                )
            ''')
            conn.commit()
            conn.close()
            
            self.logger.info("✅ Database ultra-aggressivo inizializzato")
            
        except Exception as e:
            self.logger.error(f"❌ Errore init database: {e}")
    
    def calculate_position_size(self, confidence: float, volatility: float) -> float:
        """Calcola size posizione ultra-aggressiva"""
        try:
            # Base size aggressiva
            base_size = self.config.AGGRESSIVE_POSITION_SIZE_PERCENT
            
            # Multiplier per confidence (più confidence = più size)
            confidence_multiplier = 1.0 + (confidence * 1.5)  # Era 1.0, ora fino a 2.5x
            
            # Multiplier per volatilità (più volatilità = più opportunità = più size)
            if volatility > 0.03:
                volatility_multiplier = self.config.HIGH_VOLATILITY_MULTIPLIER
            elif volatility > 0.015:
                volatility_multiplier = self.config.MEDIUM_VOLATILITY_MULTIPLIER
            else:
                volatility_multiplier = self.config.LOW_VOLATILITY_MULTIPLIER
            
            # Calcola size finale
            position_size = base_size * confidence_multiplier * volatility_multiplier
            
            # Limiti
            position_size = max(position_size, self.config.MIN_POSITION_SIZE_PERCENT)
            position_size = min(position_size, self.config.MAX_POSITION_SIZE_PERCENT)
            
            self.logger.info(f"💰 Position size: {position_size:.1f}% (conf: {confidence:.1%}, vol: {volatility:.1%})")
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"❌ Errore calcolo position size: {e}")
            return self.config.MIN_POSITION_SIZE_PERCENT
    
    def execute_ultra_aggressive_trade(self, signal: Dict) -> bool:
        """Esegue trade ultra-aggressivo"""
        try:
            action = signal['action']
            confidence = signal['confidence']
            price = signal['price']
            volatility = signal.get('volatility', 0.02)
            
            # Calcola position size
            position_size_percent = self.calculate_position_size(confidence, volatility)
            trade_amount = (self.balance * position_size_percent / 100)
            
            # Calcola fee aggressiva (più alta = più profitto per il sistema)
            fee_percent = self.config.AGGRESSIVE_FEE_PERCENT if confidence > 0.5 else self.config.BASE_FEE_PERCENT
            fee = trade_amount * fee_percent / 100
            
            # Simula profitto/perdita aggressivo
            profit_target = self.config.AGGRESSIVE_PROFIT_TARGET if confidence > 0.4 else self.config.MIN_PROFIT_TARGET
            
            # Profitto basato su confidence e volatilità
            base_profit_percent = profit_target * confidence * (1 + volatility * 10)
            
            # Randomness per realismo (ma biased verso profitto)
            random_factor = random.uniform(-0.8, 1.5)  # Bias positivo
            final_profit_percent = base_profit_percent * random_factor
            
            # Calcola P&L
            profit_loss = trade_amount * final_profit_percent / 100
            
            # Aggiorna balance
            balance_before = self.balance
            self.balance = self.balance + profit_loss - fee  # Fee sempre sottratta
            
            # Statistiche
            self.total_trades += 1
            self.total_fees += fee
            self.total_pnl += profit_loss
            
            if profit_loss > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Salva trade
            self.save_trade({
                'timestamp': datetime.now().isoformat(),
                'symbol': 'BTCUSDT',
                'action': action,
                'amount': trade_amount,
                'price': price,
                'confidence': confidence,
                'profit_loss': profit_loss,
                'fee': fee,
                'balance_before': balance_before,
                'balance_after': self.balance,
                'position_size_percent': position_size_percent,
                'volatility': volatility,
                'volume_ratio': signal.get('volume_ratio', 1.0),
                'signals_count': signal.get('signals_count', 1),
                'reason': signal.get('reason', 'ultra_aggressive')
            })
            
            # Log trade
            pnl_emoji = "💚" if profit_loss > 0 else "❤️"
            self.logger.info(f"💰 TRADE ULTRA-AGGRESSIVO ESEGUITO!")
            self.logger.info(f"📊 {action} ${trade_amount:.2f} @ ${price:.0f} (pos: {position_size_percent:.1f}%)")
            self.logger.info(f"{pnl_emoji} P&L: ${profit_loss:.2f}, Fee: ${fee:.2f}")
            self.logger.info(f"💰 Balance: ${balance_before:.2f} → ${self.balance:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore esecuzione trade: {e}")
            return False
    
    def save_trade(self, trade_data: Dict):
        """Salva trade nel database"""
        try:
            conn = sqlite3.connect(self.db_name)
            
            conn.execute('''
                INSERT INTO ultra_trades (
                    timestamp, symbol, action, amount, price, confidence,
                    profit_loss, fee, balance_before, balance_after,
                    position_size_percent, volatility, volume_ratio,
                    signals_count, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data['timestamp'],
                trade_data['symbol'],
                trade_data['action'],
                trade_data['amount'],
                trade_data['price'],
                trade_data['confidence'],
                trade_data['profit_loss'],
                trade_data['fee'],
                trade_data['balance_before'],
                trade_data['balance_after'],
                trade_data['position_size_percent'],
                trade_data['volatility'],
                trade_data['volume_ratio'],
                trade_data['signals_count'],
                trade_data['reason']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio trade: {e}")
    
    def should_force_trade(self) -> bool:
        """Determina se forzare un trade"""
        return self.cycles_without_trade >= self.config.FORCE_TRADE_AFTER_CYCLES
    
    def get_performance_stats(self) -> Dict:
        """Ottieni statistiche performance"""
        try:
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            avg_pnl = (self.total_pnl / self.total_trades) if self.total_trades > 0 else 0
            roi = ((self.balance - self.config.INITIAL_BALANCE) / self.config.INITIAL_BALANCE * 100)
            
            return {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': win_rate,
                'total_pnl': self.total_pnl,
                'avg_pnl': avg_pnl,
                'total_fees': self.total_fees,
                'current_balance': self.balance,
                'initial_balance': self.config.INITIAL_BALANCE,
                'roi': roi,
                'cycles_without_trade': self.cycles_without_trade
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore calcolo stats: {e}")
            return {}
    
    async def run_ultra_aggressive_cycle(self):
        """Esegue ciclo di trading ultra-aggressivo"""
        try:
            cycle_start = time.time()
            
            # Genera dati ultra-volatili
            data = self.data_generator.generate_ultra_volatile_data()
            
            if data.empty:
                self.logger.warning("⚠️ Nessun dato generato")
                return
            
            # Genera segnale ultra-aggressivo
            signal = self.ai.generate_ultra_aggressive_signal(data)
            
            # Determina se tradare
            should_trade = False
            
            if signal['action'] in ['BUY', 'SELL']:
                # Soglia confidence ultra-bassa
                if signal['confidence'] >= self.config.MIN_CONFIDENCE:
                    should_trade = True
                    self.cycles_without_trade = 0
                elif self.should_force_trade():
                    should_trade = True
                    self.cycles_without_trade = 0
                    signal['confidence'] = max(signal['confidence'], self.config.MIN_CONFIDENCE)
                    self.logger.info(f"🔥 TRADE FORZATO dopo {self.cycles_without_trade} cicli")
                else:
                    self.cycles_without_trade += 1
            else:
                self.cycles_without_trade += 1
            
            # Esegui trade se necessario
            if should_trade:
                success = self.execute_ultra_aggressive_trade(signal)
                if success:
                    # Stats aggiornate
                    stats = self.get_performance_stats()
                    self.logger.info(f"📊 Stats Ultra-Aggressive: {stats['total_trades']} trades, "
                                   f"{stats['win_rate']:.1f}% win rate, ${stats['total_fees']:.2f} fees, "
                                   f"{stats['roi']:.2f}% ROI")
            else:
                self.logger.info(f"⏸️ Nessun trade (conf: {signal['confidence']:.1%}, cicli senza trade: {self.cycles_without_trade})")
            
            # Timing
            cycle_time = time.time() - cycle_start
            self.logger.info(f"✅ Ciclo ultra-aggressivo completato in {cycle_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Errore ciclo ultra-aggressivo: {e}")

async def main():
    """Main ultra-aggressive trading"""
    print("🔥 AurumBotX Ultra Aggressive Trading System")
    print("=" * 60)
    print("💰 OBIETTIVO: Massimizzare profitti con trading aggressivo")
    print("⚡ PARAMETRI: Position 5-12%, Confidence 15%+, Profit 0.8-3%")
    print("🎯 FREQUENZA: Trade ogni 90s, Force ogni 2 cicli")
    print("=" * 60)
    
    # Setup
    os.makedirs('logs', exist_ok=True)
    
    # Inizializza engine
    engine = UltraAggressiveEngine()
    
    # Mostra configurazione
    print(f"\n🔧 CONFIGURAZIONE ULTRA-AGGRESSIVA:")
    print(f"   💰 Balance iniziale: ${engine.config.INITIAL_BALANCE}")
    print(f"   📊 Position size: {engine.config.MIN_POSITION_SIZE_PERCENT}%-{engine.config.MAX_POSITION_SIZE_PERCENT}%")
    print(f"   🎯 Confidence min: {engine.config.MIN_CONFIDENCE:.1%}")
    print(f"   💸 Profit target: {engine.config.MIN_PROFIT_TARGET}%-{engine.config.MAX_PROFIT_TARGET}%")
    print(f"   ⏰ Intervallo: {engine.config.TRADE_INTERVAL_SECONDS}s")
    
    print(f"\n🚀 Avvio trading ultra-aggressivo...")
    
    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            
            print(f"\n🔄 CICLO #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Esegui ciclo
            await engine.run_ultra_aggressive_cycle()
            
            # Stats ogni 10 cicli
            if cycle_count % 10 == 0:
                stats = engine.get_performance_stats()
                print(f"\n📊 STATS ULTRA-AGGRESSIVE (Ciclo {cycle_count}):")
                print(f"   💰 Balance: ${stats['current_balance']:.2f} (ROI: {stats['roi']:.2f}%)")
                print(f"   📈 Trade: {stats['total_trades']} ({stats['win_rate']:.1f}% win rate)")
                print(f"   💸 P&L: ${stats['total_pnl']:.2f} (avg: ${stats['avg_pnl']:.2f})")
                print(f"   💰 Fee: ${stats['total_fees']:.2f}")
            
            # Pausa
            await asyncio.sleep(engine.config.TRADE_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Trading ultra-aggressivo fermato dall'utente")
        
        # Stats finali
        stats = engine.get_performance_stats()
        print(f"\n📊 RISULTATI FINALI:")
        print(f"   💰 Balance finale: ${stats['current_balance']:.2f}")
        print(f"   📈 ROI: {stats['roi']:.2f}%")
        print(f"   🎯 Trade totali: {stats['total_trades']}")
        print(f"   ✅ Win rate: {stats['win_rate']:.1f}%")
        print(f"   💸 Profitto totale: ${stats['total_pnl']:.2f}")
        print(f"   💰 Fee raccolte: ${stats['total_fees']:.2f}")
        
    except Exception as e:
        print(f"\n❌ ERRORE SISTEMA: {e}")

if __name__ == "__main__":
    asyncio.run(main())

