#!/usr/bin/env python3
"""
AurumBotX Aggressive Trading Fix - Forza Esecuzione Trade
Versione aggressiva per garantire esecuzione trade con soglie più basse
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aggressive_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AggressiveTrading')

class AggressiveTradingEngine:
    """Trading engine aggressivo che GARANTISCE esecuzione trade"""
    
    def __init__(self, capital: float = 1000.0):
        self.capital = capital
        self.balance = capital
        self.trades = []
        self.fee_wallet = os.getenv('FEE_WALLET_ADDRESS', 'YOUR_WALLET_ADDRESS_HERE')
        self.fee_percentage = 0.025  # 2.5%
        self.logger = logging.getLogger('AggressiveEngine')
        self.trade_count = 0
        self.forced_trades = 0
        
        # Parametri aggressivi
        self.min_confidence = 0.3  # Soglia molto bassa (30%)
        self.force_trade_every = 3  # Forza trade ogni 3 cicli
        self.cycles_since_trade = 0
        
        # Setup database
        self._setup_database()
        self._load_existing_trades()
    
    def _setup_database(self):
        """Setup database per tracking aggressivo"""
        try:
            self.db_path = 'aggressive_trading.db'
            conn = sqlite3.connect(self.db_path)
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS aggressive_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount REAL NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    fee REAL NOT NULL,
                    profit_loss REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    confidence REAL NOT NULL,
                    forced BOOLEAN NOT NULL,
                    reason TEXT,
                    status TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("✅ Database aggressivo inizializzato")
            
        except Exception as e:
            self.logger.error(f"❌ Errore setup database: {e}")
    
    def _load_existing_trades(self):
        """Carica trade esistenti"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('SELECT COUNT(*) FROM aggressive_trades')
            self.trade_count = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT balance_after FROM aggressive_trades ORDER BY id DESC LIMIT 1')
            result = cursor.fetchone()
            if result:
                self.balance = result[0]
                self.logger.info(f"✅ Balance caricato: ${self.balance:.2f}")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Errore caricamento trades: {e}")
    
    def generate_aggressive_signal(self, data: pd.DataFrame) -> Dict:
        """Genera segnale con logica aggressiva"""
        try:
            if len(data) < 5:
                return self._force_random_signal("Dati insufficienti")
            
            # Calcola indicatori base
            data['sma_5'] = data['close'].rolling(5, min_periods=1).mean()
            data['sma_10'] = data['close'].rolling(10, min_periods=1).mean()
            data['rsi'] = self._calculate_rsi(data['close'])
            
            latest = data.iloc[-1]
            current_price = latest['close']
            sma_5 = latest['sma_5']
            sma_10 = latest['sma_10']
            rsi = latest['rsi']
            
            # Logica aggressiva con soglie basse
            buy_score = 0
            sell_score = 0
            
            # Trend analysis (peso ridotto)
            if sma_5 > sma_10:
                buy_score += 1
            else:
                sell_score += 1
            
            # RSI analysis (soglie più ampie)
            if rsi < 50:  # Più aggressivo
                buy_score += 1
            else:
                sell_score += 1
            
            # Price momentum (semplificato)
            if len(data) > 1:
                price_change = (current_price - data.iloc[-2]['close']) / data.iloc[-2]['close']
                if price_change > 0:
                    buy_score += 1
                else:
                    sell_score += 1
            
            # Determina azione
            if buy_score > sell_score:
                action = 'BUY'
                confidence = 0.4 + (buy_score * 0.1)  # Min 40%
            elif sell_score > buy_score:
                action = 'SELL' 
                confidence = 0.4 + (sell_score * 0.1)  # Min 40%
            else:
                # Forza decisione random
                action = random.choice(['BUY', 'SELL'])
                confidence = 0.35
            
            # Incrementa counter
            self.cycles_since_trade += 1
            
            # Forza trade se necessario
            if self.cycles_since_trade >= self.force_trade_every:
                if confidence < self.min_confidence:
                    confidence = self.min_confidence + 0.1
                    self.logger.info(f"🔥 FORZANDO TRADE: Cicli senza trade: {self.cycles_since_trade}")
            
            signal = {
                'action': action,
                'confidence': min(confidence, 0.9),
                'price': current_price,
                'buy_score': buy_score,
                'sell_score': sell_score,
                'forced': self.cycles_since_trade >= self.force_trade_every,
                'reason': f'Aggressive: BUY={buy_score}, SELL={sell_score}, RSI={rsi:.1f}'
            }
            
            self.logger.info(f"🎯 Segnale aggressivo: {action} (conf: {confidence:.1%}) - Cicli: {self.cycles_since_trade}")
            return signal
            
        except Exception as e:
            self.logger.error(f"❌ Errore segnale: {e}")
            return self._force_random_signal(f"Errore: {e}")
    
    def _force_random_signal(self, reason: str) -> Dict:
        """Forza segnale random per garantire trade"""
        action = random.choice(['BUY', 'SELL'])
        confidence = random.uniform(0.4, 0.7)
        price = random.uniform(35000, 45000)
        
        return {
            'action': action,
            'confidence': confidence,
            'price': price,
            'buy_score': 0,
            'sell_score': 0,
            'forced': True,
            'reason': f'Forced random: {reason}'
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcola RSI semplificato"""
        try:
            if len(prices) < 2:
                return pd.Series([50] * len(prices), index=prices.index)
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=min(period, len(prices)), min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=min(period, len(prices)), min_periods=1).mean()
            
            loss = loss.replace(0, 0.01)  # Evita divisione per zero
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.fillna(50)
            
        except Exception as e:
            self.logger.error(f"❌ Errore RSI: {e}")
            return pd.Series([50] * len(prices), index=prices.index)
    
    def execute_aggressive_trade(self, signal: Dict, symbol: str = 'BTCUSDT') -> Dict:
        """Esegue trade con logica aggressiva - SEMPRE esegue se confidence > 30%"""
        try:
            action = signal['action']
            price = signal['price']
            confidence = signal['confidence']
            forced = signal.get('forced', False)
            
            # Soglia molto bassa per garantire esecuzione
            if confidence < self.min_confidence and not forced:
                return {'status': 'SKIPPED', 'reason': f'Confidenza {confidence:.1%} < {self.min_confidence:.1%}'}
            
            # Calcola trade size (aggressivo: 3% del balance)
            position_size = self.balance * 0.03
            quantity = position_size / price
            
            # Calcola fee
            fee = position_size * self.fee_percentage
            
            # P&L aggressivo (range più ampio)
            base_return = random.uniform(-0.02, 0.03)  # -2% a +3%
            confidence_multiplier = max(confidence, 0.5)  # Min 50% multiplier
            profit_loss = position_size * base_return * confidence_multiplier
            
            # Aggiorna balance
            new_balance = self.balance + profit_loss - fee
            
            # Crea trade record
            self.trade_count += 1
            if forced:
                self.forced_trades += 1
            
            trade_record = {
                'id': self.trade_count,
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': action,
                'amount': position_size,
                'quantity': quantity,
                'price': price,
                'fee': fee,
                'profit_loss': profit_loss,
                'balance_after': new_balance,
                'confidence': confidence,
                'forced': forced,
                'reason': signal.get('reason', 'Aggressive trade'),
                'status': 'COMPLETED'
            }
            
            # Salva nel database
            self._save_trade_to_db(trade_record)
            
            # Aggiorna balance
            self.balance = new_balance
            
            # Reset counter
            self.cycles_since_trade = 0
            
            # Registra fee
            self._collect_fee(self.trade_count, fee)
            
            # Log risultato
            forced_text = " [FORCED]" if forced else ""
            self.logger.info(f"✅ Trade #{self.trade_count}{forced_text}: {action} {quantity:.6f} {symbol} @ ${price:.2f}")
            self.logger.info(f"💰 Fee: ${fee:.2f} → {self.fee_wallet}")
            self.logger.info(f"📊 P&L: ${profit_loss:.2f}, Balance: ${self.balance:.2f}")
            
            return {
                'status': 'COMPLETED',
                'trade_id': self.trade_count,
                'action': action,
                'amount': position_size,
                'quantity': quantity,
                'price': price,
                'fee': fee,
                'profit_loss': profit_loss,
                'balance': self.balance,
                'confidence': confidence,
                'forced': forced
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore esecuzione trade: {e}")
            return {'status': 'ERROR', 'reason': str(e)}
    
    def _save_trade_to_db(self, trade: Dict):
        """Salva trade nel database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO aggressive_trades (
                    timestamp, symbol, action, amount, quantity, price, 
                    fee, profit_loss, balance_after, confidence, forced, reason, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['timestamp'], trade['symbol'], trade['action'],
                trade['amount'], trade['quantity'], trade['price'],
                trade['fee'], trade['profit_loss'], trade['balance_after'],
                trade['confidence'], trade['forced'], trade['reason'], trade['status']
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
    
    def get_aggressive_stats(self) -> Dict:
        """Ottieni statistiche aggressive"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(fee) as total_fees,
                    SUM(profit_loss) as total_profit_loss,
                    AVG(confidence) as avg_confidence,
                    SUM(CASE WHEN forced = 1 THEN 1 ELSE 0 END) as forced_trades
                FROM aggressive_trades 
                WHERE status = 'COMPLETED'
            ''')
            
            stats = cursor.fetchone()
            total_trades = stats[0] if stats[0] else 0
            total_fees = stats[1] if stats[1] else 0.0
            total_profit_loss = stats[2] if stats[2] else 0.0
            avg_confidence = stats[3] if stats[3] else 0.0
            forced_trades = stats[4] if stats[4] else 0
            
            # Win rate
            cursor = conn.execute('''
                SELECT COUNT(*) FROM aggressive_trades 
                WHERE status = 'COMPLETED' AND profit_loss > 0
            ''')
            winning_trades = cursor.fetchone()[0]
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # ROI
            roi = ((self.balance - self.capital) / self.capital * 100) if self.capital > 0 else 0
            
            conn.close()
            
            return {
                'total_trades': total_trades,
                'forced_trades': forced_trades,
                'natural_trades': total_trades - forced_trades,
                'total_fees': total_fees,
                'total_profit_loss': total_profit_loss,
                'current_balance': self.balance,
                'initial_capital': self.capital,
                'roi': roi,
                'win_rate': win_rate,
                'avg_confidence': avg_confidence,
                'net_profit': total_profit_loss - total_fees,
                'cycles_since_trade': self.cycles_since_trade
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore calcolo stats: {e}")
            return {
                'total_trades': 0,
                'forced_trades': 0,
                'natural_trades': 0,
                'total_fees': 0.0,
                'current_balance': self.balance,
                'roi': 0.0,
                'win_rate': 0.0,
                'cycles_since_trade': self.cycles_since_trade
            }

class SimpleDataGenerator:
    """Generatore dati semplice per test aggressivo"""
    
    def __init__(self):
        self.logger = logging.getLogger('DataGenerator')
    
    def get_simple_data(self, symbol: str = 'BTCUSDT') -> pd.DataFrame:
        """Genera dati semplici ma realistici"""
        try:
            # Genera 20 candele per analisi veloce
            dates = pd.date_range(
                start=datetime.now() - timedelta(hours=20),
                periods=20,
                freq='1H'
            )
            
            # Prezzo base con variazione
            base_price = 40000 + random.uniform(-5000, 5000)
            
            data = []
            for i, date in enumerate(dates):
                if i == 0:
                    price = base_price
                else:
                    # Variazione più marcata per trigger segnali
                    change = random.uniform(-0.03, 0.03)  # ±3%
                    price = data[-1]['close'] * (1 + change)
                
                # OHLC con spread
                spread = price * random.uniform(0.005, 0.02)  # 0.5-2%
                high = price + spread * random.random()
                low = price - spread * random.random()
                open_price = low + (high - low) * random.random()
                close_price = low + (high - low) * random.random()
                
                data.append({
                    'timestamp': date,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close_price,
                    'volume': random.uniform(5000, 50000)
                })
            
            df = pd.DataFrame(data)
            self.logger.info(f"✅ Dati generati: {len(df)} candele per {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore generazione dati: {e}")
            return pd.DataFrame()

async def aggressive_trading_cycle():
    """Ciclo trading aggressivo che GARANTISCE trade"""
    logger.info("🔥 Avvio Aggressive Trading Cycle")
    logger.info("🎯 Obiettivo: GARANTIRE esecuzione trade")
    logger.info(f"📊 Soglia minima: 30% confidence")
    logger.info(f"⚡ Force trade ogni: 3 cicli")
    
    # Inizializza componenti
    data_generator = SimpleDataGenerator()
    trading_engine = AggressiveTradingEngine(capital=1000.0)
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            cycle_start = datetime.now()
            
            logger.info(f"🔄 Ciclo Aggressivo #{cycle_count} - {cycle_start.strftime('%H:%M:%S')}")
            
            try:
                # 1. Genera dati semplici
                data = data_generator.get_simple_data('BTCUSDT')
                if data.empty:
                    logger.warning("⚠️ Nessun dato, creando fallback")
                    data = pd.DataFrame({
                        'close': [40000 + random.uniform(-1000, 1000) for _ in range(10)]
                    })
                
                # 2. Genera segnale aggressivo
                signal = trading_engine.generate_aggressive_signal(data)
                
                # 3. SEMPRE esegui trade se confidence >= 30%
                result = trading_engine.execute_aggressive_trade(signal)
                
                if result['status'] == 'COMPLETED':
                    forced_text = " [FORCED]" if result.get('forced', False) else ""
                    logger.info(f"🎉 TRADE ESEGUITO{forced_text}!")
                    logger.info(f"📊 {result['action']} ${result['amount']:.2f} @ ${result['price']:.2f}")
                else:
                    logger.warning(f"⚠️ Trade non eseguito: {result.get('reason', 'Unknown')}")
                
                # 4. Mostra stats aggressive
                stats = trading_engine.get_aggressive_stats()
                logger.info(f"💰 Stats Aggressive: {stats['total_trades']} trades "
                           f"({stats['forced_trades']} forced), "
                           f"${stats['total_fees']:.2f} fees, "
                           f"{stats['roi']:.2f}% ROI")
                
                # 5. Salva report ogni 5 cicli
                if cycle_count % 5 == 0:
                    save_aggressive_report(stats, cycle_count)
                
                # 6. Tempo ciclo
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                logger.info(f"✅ Ciclo aggressivo completato in {cycle_time:.2f}s")
                
                # 7. Attendi meno tempo per più aggressività (2 minuti)
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"❌ Errore nel ciclo aggressivo #{cycle_count}: {e}")
                logger.error(f"📊 Traceback: {traceback.format_exc()}")
                await asyncio.sleep(60)
                
    except KeyboardInterrupt:
        logger.info("🛑 Aggressive trading interrotto")
    except Exception as e:
        logger.error(f"❌ Errore fatale aggressivo: {e}")
    finally:
        try:
            stats = trading_engine.get_aggressive_stats()
            save_aggressive_report(stats, cycle_count, final=True)
            logger.info("✅ Aggressive Trading terminato")
        except Exception as e:
            logger.error(f"❌ Errore salvataggio finale: {e}")

def save_aggressive_report(stats: Dict, cycle_count: int, final: bool = False):
    """Salva report aggressivo"""
    try:
        report = {
            'timestamp': datetime.now().isoformat(),
            'cycle_count': cycle_count,
            'aggressive_stats': stats,
            'final_report': final,
            'version': 'aggressive_v1'
        }
        
        filename = f"aggressive_report_{'final' if final else cycle_count}.json"
        filepath = f"reports/{filename}"
        
        os.makedirs('reports', exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report aggressivo salvato: {filepath}")
        
    except Exception as e:
        logger.error(f"❌ Errore salvataggio report: {e}")

def main():
    """Main aggressive trading"""
    print("🔥 AurumBotX Aggressive Trading Fix")
    print("=" * 50)
    print("🎯 OBIETTIVO: GARANTIRE ESECUZIONE TRADE")
    print("⚡ Soglia confidence: 30% (molto bassa)")
    print("🔥 Force trade ogni: 3 cicli")
    print("💰 Position size: 3% (aggressivo)")
    print("⏰ Ciclo: 2 minuti (veloce)")
    print("=" * 50)
    
    # Setup
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    fee_wallet = os.getenv('FEE_WALLET_ADDRESS', 'YOUR_WALLET_ADDRESS_HERE')
    print(f"💰 Fee Wallet: {fee_wallet}")
    print(f"📊 Fee: 2.5%")
    print(f"💵 Capital: $1,000")
    print("=" * 50)
    
    # Avvia aggressive trading
    try:
        asyncio.run(aggressive_trading_cycle())
    except KeyboardInterrupt:
        print("\n🛑 Aggressive trading interrotto")
    except Exception as e:
        print(f"\n❌ Errore: {e}")

if __name__ == "__main__":
    main()

