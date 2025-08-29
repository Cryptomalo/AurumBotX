#!/usr/bin/env python3
"""
AurumBotX Bootstrap Fix - Core Trading Engine
Fix immediato per rendere operativo il sistema con budget zero
"""

import os
import sys
import asyncio
import logging
import sqlite3
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bootstrap_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BootstrapDataPreprocessor:
    """Preprocessore dati semplificato per fix immediato"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Pulizia dati con gestione NaN robusta"""
        try:
            # Rimuovi righe con troppi NaN
            data = data.dropna(thresh=len(data.columns) * 0.7)
            
            # Fill NaN con metodi semplici
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if data[col].isna().any():
                    # Forward fill poi backward fill
                    data[col] = data[col].fillna(method='ffill').fillna(method='bfill')
                    # Se ancora NaN, usa la media
                    if data[col].isna().any():
                        data[col] = data[col].fillna(data[col].mean())
                    # Se ancora NaN, usa 0
                    if data[col].isna().any():
                        data[col] = data[col].fillna(0)
            
            # Verifica finale
            if data.isna().any().any():
                self.logger.warning("Ancora NaN presenti, rimozione forzata")
                data = data.fillna(0)
            
            self.logger.info(f"✅ Dati puliti: {len(data)} righe, {len(data.columns)} colonne")
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Errore pulizia dati: {e}")
            # Fallback: crea dati mock puliti
            return self._create_clean_mock_data()
    
    def _create_clean_mock_data(self) -> pd.DataFrame:
        """Crea dati mock puliti per fallback"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(40000, 50000, 100),
            'high': np.random.uniform(40000, 50000, 100),
            'low': np.random.uniform(40000, 50000, 100),
            'close': np.random.uniform(40000, 50000, 100),
            'volume': np.random.uniform(1000, 10000, 100)
        })
        
        # Assicura che high >= low
        data['high'] = np.maximum(data['high'], data['low'])
        data['open'] = np.clip(data['open'], data['low'], data['high'])
        data['close'] = np.clip(data['close'], data['low'], data['high'])
        
        return data

class BootstrapTradingEngine:
    """Engine trading semplificato per bootstrap"""
    
    def __init__(self, capital: float = 1000.0):
        self.capital = capital
        self.balance = capital
        self.positions = {}
        self.trades = []
        self.fee_wallet = os.getenv('FEE_WALLET_ADDRESS', 'YOUR_WALLET_ADDRESS_HERE')
        self.fee_percentage = 0.025  # 2.5% fee
        self.logger = logging.getLogger(__name__)
        
        # Setup database
        self._setup_database()
    
    def _setup_database(self):
        """Setup database per tracking"""
        try:
            self.db_path = 'bootstrap_trading.db'
            conn = sqlite3.connect(self.db_path)
            
            # Tabella trades
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    action TEXT,
                    amount REAL,
                    price REAL,
                    fee REAL,
                    profit_loss REAL,
                    balance_after REAL,
                    status TEXT
                )
            ''')
            
            # Tabella fees
            conn.execute('''
                CREATE TABLE IF NOT EXISTS fees_collected (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    trade_id INTEGER,
                    fee_amount REAL,
                    wallet_address TEXT,
                    status TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("✅ Database bootstrap inizializzato")
            
        except Exception as e:
            self.logger.error(f"❌ Errore setup database: {e}")
    
    def generate_simple_signal(self, data: pd.DataFrame) -> Dict:
        """Genera segnale trading semplice ma efficace"""
        try:
            if len(data) < 20:
                return {'action': 'HOLD', 'confidence': 0.0, 'reason': 'Dati insufficienti'}
            
            # Calcola indicatori semplici
            data['sma_5'] = data['close'].rolling(5).mean()
            data['sma_20'] = data['close'].rolling(20).mean()
            data['rsi'] = self._calculate_rsi(data['close'], 14)
            
            current_price = data['close'].iloc[-1]
            sma_5 = data['sma_5'].iloc[-1]
            sma_20 = data['sma_20'].iloc[-1]
            rsi = data['rsi'].iloc[-1]
            
            # Logica trading semplice
            signal = {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
            
            # Segnale BUY
            if (sma_5 > sma_20 and rsi < 70 and rsi > 30):
                signal = {
                    'action': 'BUY',
                    'confidence': 0.7,
                    'price': current_price,
                    'reason': f'SMA crossover bullish, RSI: {rsi:.1f}'
                }
            
            # Segnale SELL
            elif (sma_5 < sma_20 and rsi > 30):
                signal = {
                    'action': 'SELL',
                    'confidence': 0.6,
                    'price': current_price,
                    'reason': f'SMA crossover bearish, RSI: {rsi:.1f}'
                }
            
            self.logger.info(f"🎯 Segnale generato: {signal['action']} (conf: {signal['confidence']:.1%})")
            return signal
            
        except Exception as e:
            self.logger.error(f"❌ Errore generazione segnale: {e}")
            return {'action': 'HOLD', 'confidence': 0.0, 'reason': f'Errore: {e}'}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcola RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.fillna(50)  # Fill NaN con valore neutro
        except:
            return pd.Series([50] * len(prices), index=prices.index)
    
    def execute_trade(self, signal: Dict, symbol: str = 'BTCUSDT') -> Dict:
        """Esegue trade con fee collection automatica"""
        try:
            if signal['confidence'] < 0.6:
                return {'status': 'SKIPPED', 'reason': 'Confidenza troppo bassa'}
            
            action = signal['action']
            price = signal['price']
            
            if action == 'HOLD':
                return {'status': 'HOLD', 'reason': 'Nessuna azione richiesta'}
            
            # Calcola amount (2% del balance per trade)
            trade_amount = self.balance * 0.02
            quantity = trade_amount / price
            
            # Calcola fee
            fee = trade_amount * self.fee_percentage
            
            # Simula esecuzione trade
            trade_id = len(self.trades) + 1
            timestamp = datetime.now().isoformat()
            
            # Simula P&L (random per demo)
            import random
            profit_loss = random.uniform(-0.01, 0.02) * trade_amount  # -1% a +2%
            
            # Aggiorna balance
            self.balance += profit_loss - fee
            
            # Registra trade
            trade_record = {
                'id': trade_id,
                'timestamp': timestamp,
                'symbol': symbol,
                'action': action,
                'amount': trade_amount,
                'quantity': quantity,
                'price': price,
                'fee': fee,
                'profit_loss': profit_loss,
                'balance_after': self.balance,
                'status': 'COMPLETED'
            }
            
            self.trades.append(trade_record)
            
            # Salva nel database
            self._save_trade_to_db(trade_record)
            
            # Registra fee collection
            self._collect_fee(trade_id, fee)
            
            self.logger.info(f"✅ Trade eseguito: {action} {quantity:.6f} {symbol} @ ${price:.2f}")
            self.logger.info(f"💰 Fee raccolta: ${fee:.2f} → {self.fee_wallet}")
            self.logger.info(f"📊 P&L: ${profit_loss:.2f}, Balance: ${self.balance:.2f}")
            
            return {
                'status': 'COMPLETED',
                'trade_id': trade_id,
                'action': action,
                'amount': trade_amount,
                'fee': fee,
                'profit_loss': profit_loss,
                'balance': self.balance
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore esecuzione trade: {e}")
            return {'status': 'ERROR', 'reason': str(e)}
    
    def _save_trade_to_db(self, trade: Dict):
        """Salva trade nel database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO trades (timestamp, symbol, action, amount, price, fee, profit_loss, balance_after, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['timestamp'], trade['symbol'], trade['action'],
                trade['amount'], trade['price'], trade['fee'],
                trade['profit_loss'], trade['balance_after'], trade['status']
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio trade: {e}")
    
    def _collect_fee(self, trade_id: int, fee_amount: float):
        """Registra fee collection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO fees_collected (timestamp, trade_id, fee_amount, wallet_address, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(), trade_id, fee_amount, 
                self.fee_wallet, 'COLLECTED'
            ))
            conn.commit()
            conn.close()
            
            self.logger.info(f"💰 Fee ${fee_amount:.2f} registrata per wallet {self.fee_wallet}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore registrazione fee: {e}")
    
    def get_performance_stats(self) -> Dict:
        """Ottieni statistiche performance"""
        try:
            if not self.trades:
                return {
                    'total_trades': 0,
                    'total_fees': 0.0,
                    'total_profit': 0.0,
                    'roi': 0.0,
                    'balance': self.balance
                }
            
            total_fees = sum(trade.get('fee', 0) for trade in self.trades)
            total_profit = sum(trade.get('profit_loss', 0) for trade in self.trades)
            roi = ((self.balance - self.capital) / self.capital) * 100
            
            return {
                'total_trades': len(self.trades),
                'total_fees': total_fees,
                'total_profit': total_profit,
                'roi': roi,
                'balance': self.balance,
                'capital': self.capital
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore calcolo stats: {e}")
            return {'error': str(e)}

class BootstrapDataLoader:
    """Data loader semplificato per bootstrap"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_market_data(self, symbol: str = 'BTCUSDT') -> pd.DataFrame:
        """Ottieni dati di mercato (mock per bootstrap)"""
        try:
            # Per ora usa dati mock realistici
            # TODO: Implementare connessione Binance reale
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=100)
            
            # Genera dati mock realistici
            dates = pd.date_range(start=start_time, end=end_time, freq='1H')
            base_price = 45000  # BTC price base
            
            data = []
            current_price = base_price
            
            for date in dates:
                # Simula movimento prezzo realistico
                change = np.random.normal(0, 0.02)  # 2% volatilità
                current_price *= (1 + change)
                
                # Assicura range realistico
                current_price = max(30000, min(70000, current_price))
                
                # Genera OHLCV
                high = current_price * (1 + abs(np.random.normal(0, 0.01)))
                low = current_price * (1 - abs(np.random.normal(0, 0.01)))
                open_price = np.random.uniform(low, high)
                close_price = current_price
                volume = np.random.uniform(1000, 10000)
                
                data.append({
                    'timestamp': date,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close_price,
                    'volume': volume
                })
            
            df = pd.DataFrame(data)
            self.logger.info(f"✅ Dati mercato generati: {len(df)} candele per {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore caricamento dati: {e}")
            return pd.DataFrame()

async def bootstrap_trading_cycle():
    """Ciclo trading bootstrap"""
    logger.info("🚀 Avvio Bootstrap Trading Cycle")
    
    # Inizializza componenti
    data_loader = BootstrapDataLoader()
    preprocessor = BootstrapDataPreprocessor()
    trading_engine = BootstrapTradingEngine(capital=1000.0)
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            logger.info(f"🔄 Ciclo #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            
            # 1. Carica dati mercato
            raw_data = data_loader.get_market_data('BTCUSDT')
            if raw_data.empty:
                logger.warning("⚠️ Nessun dato disponibile, skip ciclo")
                await asyncio.sleep(300)  # 5 minuti
                continue
            
            # 2. Preprocessa dati
            clean_data = preprocessor.clean_data(raw_data)
            
            # 3. Genera segnale
            signal = trading_engine.generate_simple_signal(clean_data)
            
            # 4. Esegui trade se necessario
            if signal['action'] != 'HOLD':
                result = trading_engine.execute_trade(signal)
                logger.info(f"📊 Risultato trade: {result}")
            
            # 5. Mostra stats
            stats = trading_engine.get_performance_stats()
            logger.info(f"💰 Stats: {stats['total_trades']} trades, "
                       f"${stats['total_fees']:.2f} fees, "
                       f"{stats['roi']:.2f}% ROI")
            
            # 6. Salva report
            if cycle_count % 10 == 0:  # Ogni 10 cicli
                save_bootstrap_report(stats, cycle_count)
            
            # 7. Attendi prossimo ciclo
            await asyncio.sleep(300)  # 5 minuti
            
    except KeyboardInterrupt:
        logger.info("🛑 Bootstrap interrotto dall'utente")
    except Exception as e:
        logger.error(f"❌ Errore nel ciclo bootstrap: {e}")
    finally:
        # Salva report finale
        stats = trading_engine.get_performance_stats()
        save_bootstrap_report(stats, cycle_count, final=True)
        logger.info("✅ Bootstrap terminato")

def save_bootstrap_report(stats: Dict, cycle_count: int, final: bool = False):
    """Salva report bootstrap"""
    try:
        report = {
            'timestamp': datetime.now().isoformat(),
            'cycle_count': cycle_count,
            'stats': stats,
            'final_report': final
        }
        
        filename = f"bootstrap_report_{'final' if final else cycle_count}.json"
        filepath = f"reports/{filename}"
        
        os.makedirs('reports', exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report salvato: {filepath}")
        
    except Exception as e:
        logger.error(f"❌ Errore salvataggio report: {e}")

def main():
    """Main bootstrap function"""
    print("🚀 AurumBotX Bootstrap Fix - Core Trading Engine")
    print("=" * 50)
    
    # Setup directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # Verifica configurazione
    fee_wallet = os.getenv('FEE_WALLET_ADDRESS')
    if not fee_wallet or fee_wallet == 'YOUR_WALLET_ADDRESS_HERE':
        print("⚠️  ATTENZIONE: Configura FEE_WALLET_ADDRESS nel file .env")
        print("   Esempio: FEE_WALLET_ADDRESS=0x1234567890abcdef...")
    
    print(f"💰 Fee Wallet: {fee_wallet}")
    print(f"📊 Fee Percentage: 2.5%")
    print(f"💵 Capital Iniziale: $1,000")
    print("=" * 50)
    
    # Avvia ciclo trading
    try:
        asyncio.run(bootstrap_trading_cycle())
    except KeyboardInterrupt:
        print("\n🛑 Bootstrap interrotto")
    except Exception as e:
        print(f"\n❌ Errore: {e}")

if __name__ == "__main__":
    main()

