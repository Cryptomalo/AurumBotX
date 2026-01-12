#!/usr/bin/env python3
"""
AurumBotX Mega Mainnet Strategy
Strategia mega-aggressiva adattata per mainnet con parametri moderati
"""

import sqlite3
import json
import time
import random
import numpy as np
from datetime import datetime, timedelta
import requests
import os

class MegaMainnetStrategy:
    """Strategia mega adattata per mainnet con parametri moderati"""
    
    def __init__(self, initial_balance=1000.0):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.db_name = 'mega_mainnet_strategy.db'
        self.log_file = 'logs/mega_mainnet.log'
        
        # Parametri adattati per mainnet
        self.config = {
            # Position Sizing (moderato vs testnet)
            'base_position_size': 0.08,      # 8% vs 12% testnet
            'max_position_size': 0.15,       # 15% vs 35% testnet
            'min_position_size': 0.03,       # 3% vs 5% testnet
            
            # Confidence Thresholds (più conservativi)
            'min_confidence': 0.35,          # 35% vs 15% testnet
            'aggressive_confidence': 0.55,   # 55% vs 25% testnet
            'high_confidence': 0.75,         # 75% vs 40% testnet
            
            # Profit Targets (realistici per mainnet)
            'min_profit_target': 0.004,      # 0.4% vs 0.8% testnet
            'standard_profit_target': 0.008, # 0.8% vs 1.5% testnet
            'max_profit_target': 0.015,      # 1.5% vs 3.0% testnet
            
            # Risk Management (più stringente)
            'max_loss_per_trade': 0.02,      # 2% max loss
            'daily_loss_limit': 0.05,        # 5% daily loss limit
            'consecutive_loss_limit': 3,     # Stop dopo 3 loss consecutivi
            
            # Timing (meno frequente)
            'cycle_interval': 180,            # 3 minuti vs 90 secondi
            'force_trade_cycles': 5,          # Ogni 5 cicli vs 2
            'cooldown_after_loss': 300,      # 5 minuti cooldown
            
            # Market Conditions (adattivo)
            'volatility_threshold': 0.02,    # 2% volatilità minima
            'spread_threshold': 0.001,       # 0.1% spread massimo
            'volume_threshold': 100,         # Volume minimo BTC
            
            # AI Enhancement (mantenuto)
            'ai_confidence_boost': 1.2,      # Boost confidence AI
            'ensemble_models': 3,            # 3 modelli ensemble
            'feature_importance': 0.8        # Peso feature importance
        }
        
        # Stato trading
        self.consecutive_losses = 0
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_trade_time = None
        self.cooldown_until = None
        
        # Setup database e logging
        self.setup_database()
        self.setup_logging()
        
        print(f"🎯 Mega Mainnet Strategy inizializzata")
        print(f"💰 Balance iniziale: ${self.balance:.2f}")
        print(f"🛡️ Parametri moderati per mainnet attivati")
    
    def setup_database(self):
        """Setup database per tracking trade"""
        os.makedirs('logs', exist_ok=True)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mega_mainnet_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                confidence REAL NOT NULL,
                profit_loss REAL NOT NULL,
                balance_after REAL NOT NULL,
                position_size_percent REAL NOT NULL,
                market_conditions TEXT,
                ai_signals TEXT,
                risk_metrics TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_logging(self):
        """Setup logging sistema"""
        os.makedirs('logs', exist_ok=True)
        
        with open(self.log_file, 'a') as f:
            f.write(f"\\n{'='*50}\\n")
            f.write(f"Mega Mainnet Strategy Started: {datetime.now()}\\n")
            f.write(f"Initial Balance: ${self.balance:.2f}\\n")
            f.write(f"{'='*50}\\n")
    
    def log_message(self, message):
        """Log messaggio con timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\\n")
    
    def get_market_data(self):
        """Ottieni dati mercato reali (simulati per testnet)"""
        try:
            # In mainnet, qui useresti API Binance reale
            # Per ora simulo dati realistici
            
            base_price = 65000  # BTC price base
            volatility = random.uniform(0.005, 0.03)  # 0.5-3% volatilità
            
            price_change = random.uniform(-volatility, volatility)
            current_price = base_price * (1 + price_change)
            
            # Simula condizioni mercato realistiche
            volume = random.uniform(50, 500)  # Volume BTC
            spread = random.uniform(0.0001, 0.002)  # Spread 0.01-0.2%
            
            market_data = {
                'price': round(current_price, 2),
                'volume': volume,
                'spread': spread,
                'volatility': volatility,
                'timestamp': datetime.now().isoformat()
            }
            
            return market_data
            
        except Exception as e:
            self.log_message(f"❌ Errore market data: {e}")
            return None
    
    def check_market_conditions(self, market_data):
        """Verifica condizioni mercato per trading"""
        if not market_data:
            return False, "Dati mercato non disponibili"
        
        conditions = []
        
        # Check volatilità
        if market_data['volatility'] < self.config['volatility_threshold']:
            return False, f"Volatilità troppo bassa: {market_data['volatility']:.3f}"
        
        # Check spread
        if market_data['spread'] > self.config['spread_threshold']:
            return False, f"Spread troppo alto: {market_data['spread']:.3f}"
        
        # Check volume
        if market_data['volume'] < self.config['volume_threshold']:
            return False, f"Volume troppo basso: {market_data['volume']:.1f}"
        
        return True, "Condizioni mercato favorevoli"
    
    def generate_ai_signals(self, market_data):
        """Genera segnali AI avanzati (simulati ma realistici)"""
        try:
            # Simula ensemble di modelli AI
            signals = []
            
            # Modello 1: Trend Analysis
            trend_signal = random.uniform(0.2, 0.9)
            trend_action = 'BUY' if random.random() > 0.5 else 'SELL'
            signals.append({
                'model': 'trend_analysis',
                'confidence': trend_signal,
                'action': trend_action
            })
            
            # Modello 2: Mean Reversion
            reversion_signal = random.uniform(0.3, 0.85)
            reversion_action = 'SELL' if trend_action == 'BUY' else 'BUY'  # Contrarian
            signals.append({
                'model': 'mean_reversion',
                'confidence': reversion_signal,
                'action': reversion_action
            })
            
            # Modello 3: Momentum
            momentum_signal = random.uniform(0.25, 0.8)
            momentum_action = trend_action  # Segue trend
            signals.append({
                'model': 'momentum',
                'confidence': momentum_signal,
                'action': momentum_action
            })
            
            # Ensemble decision
            buy_confidence = sum(s['confidence'] for s in signals if s['action'] == 'BUY')
            sell_confidence = sum(s['confidence'] for s in signals if s['action'] == 'SELL')
            
            if buy_confidence > sell_confidence:
                final_action = 'BUY'
                final_confidence = buy_confidence / len(signals)
            else:
                final_action = 'SELL'
                final_confidence = sell_confidence / len(signals)
            
            # Apply AI confidence boost
            final_confidence *= self.config['ai_confidence_boost']
            final_confidence = min(final_confidence, 0.95)  # Cap a 95%
            
            return {
                'action': final_action,
                'confidence': final_confidence,
                'individual_signals': signals,
                'ensemble_method': 'weighted_average'
            }
            
        except Exception as e:
            self.log_message(f"❌ Errore AI signals: {e}")
            return None
    
    def calculate_position_size(self, confidence, market_data):
        """Calcola position size basato su confidence e condizioni mercato"""
        
        # Base position size
        base_size = self.config['base_position_size']
        
        # Adjust per confidence
        confidence_multiplier = 1 + (confidence - 0.5) * 2  # 0.5 conf = 1x, 1.0 conf = 2x
        
        # Adjust per volatilità (più volatilità = size minore)
        volatility_adjustment = 1 - (market_data['volatility'] - 0.01) * 2
        volatility_adjustment = max(0.5, min(1.5, volatility_adjustment))
        
        # Adjust per consecutive losses
        loss_adjustment = 1 - (self.consecutive_losses * 0.1)  # -10% per loss
        loss_adjustment = max(0.3, loss_adjustment)
        
        # Calcola final size
        position_size = base_size * confidence_multiplier * volatility_adjustment * loss_adjustment
        
        # Apply limits
        position_size = max(self.config['min_position_size'], position_size)
        position_size = min(self.config['max_position_size'], position_size)
        
        return position_size
    
    def calculate_profit_target(self, confidence, volatility):
        """Calcola profit target dinamico"""
        
        # Base target
        base_target = self.config['standard_profit_target']
        
        # Adjust per confidence
        confidence_bonus = (confidence - 0.5) * 0.01  # +1% per 50% confidence extra
        
        # Adjust per volatilità
        volatility_bonus = volatility * 0.5  # Più volatilità = target più alto
        
        profit_target = base_target + confidence_bonus + volatility_bonus
        
        # Apply limits
        profit_target = max(self.config['min_profit_target'], profit_target)
        profit_target = min(self.config['max_profit_target'], profit_target)
        
        return profit_target
    
    def check_risk_limits(self):
        """Verifica limiti di rischio"""
        
        # Check daily loss limit
        if self.daily_pnl < -self.balance * self.config['daily_loss_limit']:
            return False, f"Daily loss limit raggiunto: ${self.daily_pnl:.2f}"
        
        # Check consecutive losses
        if self.consecutive_losses >= self.config['consecutive_loss_limit']:
            return False, f"Consecutive loss limit: {self.consecutive_losses}"
        
        # Check cooldown
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            remaining = (self.cooldown_until - datetime.now()).total_seconds()
            return False, f"Cooldown attivo: {remaining:.0f}s rimanenti"
        
        return True, "Risk limits OK"
    
    def execute_trade(self, action, amount, price, confidence, market_data, ai_signals):
        """Esegui trade con logica mainnet"""
        
        # Simula slippage realistico
        slippage = random.uniform(0.0001, 0.001)  # 0.01-0.1%
        if action == 'BUY':
            execution_price = price * (1 + slippage)
        else:
            execution_price = price * (1 - slippage)
        
        # Simula fee Binance
        fee_rate = 0.001  # 0.1% fee
        fee = amount * fee_rate
        
        # Calcola profit/loss simulato
        profit_target = self.calculate_profit_target(confidence, market_data['volatility'])
        
        # Simula risultato trade basato su confidence
        success_probability = confidence * 0.8  # 80% della confidence
        
        if random.random() < success_probability:
            # Trade vincente
            profit_percent = random.uniform(profit_target * 0.5, profit_target * 1.5)
            profit_loss = amount * profit_percent - fee
            self.consecutive_losses = 0
        else:
            # Trade perdente
            loss_percent = random.uniform(0.005, self.config['max_loss_per_trade'])
            profit_loss = -(amount * loss_percent + fee)
            self.consecutive_losses += 1
            
            # Attiva cooldown dopo loss
            self.cooldown_until = datetime.now() + timedelta(seconds=self.config['cooldown_after_loss'])
        
        # Aggiorna balance
        self.balance += profit_loss
        self.daily_pnl += profit_loss
        self.daily_trades += 1
        self.last_trade_time = datetime.now()
        
        # Calcola position size percent
        position_size_percent = (amount / (self.balance - profit_loss)) * 100
        
        # Salva trade nel database
        self.save_trade({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'amount': amount,
            'price': execution_price,
            'confidence': confidence,
            'profit_loss': profit_loss,
            'balance_after': self.balance,
            'position_size_percent': position_size_percent,
            'market_conditions': json.dumps(market_data),
            'ai_signals': json.dumps(ai_signals),
            'risk_metrics': json.dumps({
                'slippage': slippage,
                'fee': fee,
                'consecutive_losses': self.consecutive_losses,
                'daily_pnl': self.daily_pnl
            })
        })
        
        # Log trade
        status = "✅ WIN" if profit_loss > 0 else "❌ LOSS"
        self.log_message(f"{status} {action} ${amount:.2f} @ ${execution_price:.0f} → {profit_loss:+.2f} (conf: {confidence:.1%})")
        self.log_message(f"💰 Balance: ${self.balance:.2f} | Daily P&L: ${self.daily_pnl:.2f} | Consecutive losses: {self.consecutive_losses}")
        
        return profit_loss
    
    def save_trade(self, trade_data):
        """Salva trade nel database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO mega_mainnet_trades 
                (timestamp, action, amount, price, confidence, profit_loss, balance_after, 
                 position_size_percent, market_conditions, ai_signals, risk_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data['timestamp'],
                trade_data['action'],
                trade_data['amount'],
                trade_data['price'],
                trade_data['confidence'],
                trade_data['profit_loss'],
                trade_data['balance_after'],
                trade_data['position_size_percent'],
                trade_data['market_conditions'],
                trade_data['ai_signals'],
                trade_data['risk_metrics']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log_message(f"❌ Errore salvataggio trade: {e}")
    
    def should_force_trade(self, cycles_since_last_trade):
        """Determina se forzare un trade"""
        return cycles_since_last_trade >= self.config['force_trade_cycles']
    
    def run_trading_cycle(self):
        """Esegui un ciclo di trading"""
        
        # Check risk limits
        risk_ok, risk_message = self.check_risk_limits()
        if not risk_ok:
            self.log_message(f"🛡️ Risk limit: {risk_message}")
            return False
        
        # Ottieni dati mercato
        market_data = self.get_market_data()
        if not market_data:
            self.log_message("❌ Impossibile ottenere dati mercato")
            return False
        
        # Check condizioni mercato
        market_ok, market_message = self.check_market_conditions(market_data)
        if not market_ok:
            self.log_message(f"📊 Mercato: {market_message}")
            return False
        
        # Genera segnali AI
        ai_signals = self.generate_ai_signals(market_data)
        if not ai_signals:
            self.log_message("❌ Impossibile generare segnali AI")
            return False
        
        # Check confidence threshold
        confidence = ai_signals['confidence']
        if confidence < self.config['min_confidence']:
            self.log_message(f"🎯 Confidence troppo bassa: {confidence:.1%}")
            return False
        
        # Calcola position size
        position_size_percent = self.calculate_position_size(confidence, market_data)
        trade_amount = self.balance * position_size_percent
        
        # Verifica amount minimo
        if trade_amount < 10:  # $10 minimo
            self.log_message(f"💰 Amount troppo basso: ${trade_amount:.2f}")
            return False
        
        # Esegui trade
        action = ai_signals['action']
        price = market_data['price']
        
        self.log_message(f"🚀 Executing {action}: ${trade_amount:.2f} @ ${price:.0f} (conf: {confidence:.1%}, size: {position_size_percent:.1%})")
        
        profit_loss = self.execute_trade(
            action, trade_amount, price, confidence, market_data, ai_signals
        )
        
        return True
    
    def run_continuous_trading(self):
        """Esegui trading continuo"""
        
        self.log_message("🎯 Mega Mainnet Strategy avviata")
        self.log_message(f"⚙️ Configurazione: Position {self.config['base_position_size']:.1%}-{self.config['max_position_size']:.1%}, Confidence {self.config['min_confidence']:.1%}+")
        
        cycles_since_last_trade = 0
        
        try:
            while True:
                cycle_start = datetime.now()
                
                # Reset daily stats se nuovo giorno
                if self.last_trade_time and self.last_trade_time.date() != datetime.now().date():
                    self.daily_trades = 0
                    self.daily_pnl = 0.0
                    self.log_message("📅 Nuovo giorno - Reset statistiche daily")
                
                # Esegui ciclo trading
                trade_executed = self.run_trading_cycle()
                
                if trade_executed:
                    cycles_since_last_trade = 0
                else:
                    cycles_since_last_trade += 1
                
                # Force trade se necessario
                if self.should_force_trade(cycles_since_last_trade):
                    self.log_message(f"⚡ Force trade dopo {cycles_since_last_trade} cicli")
                    # Riduci temporaneamente confidence threshold
                    original_min_conf = self.config['min_confidence']
                    self.config['min_confidence'] *= 0.7  # Riduci del 30%
                    
                    force_executed = self.run_trading_cycle()
                    
                    # Ripristina threshold
                    self.config['min_confidence'] = original_min_conf
                    
                    if force_executed:
                        cycles_since_last_trade = 0
                
                # Statistiche ciclo
                roi = ((self.balance - self.initial_balance) / self.initial_balance) * 100
                
                if cycles_since_last_trade % 10 == 0:  # Log ogni 10 cicli
                    self.log_message(f"📊 Ciclo {cycles_since_last_trade} | Balance: ${self.balance:.2f} | ROI: {roi:+.1f}% | Daily: ${self.daily_pnl:+.2f}")
                
                # Attendi prossimo ciclo
                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                sleep_time = max(0, self.config['cycle_interval'] - cycle_duration)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.log_message("🛑 Trading fermato dall'utente")
        except Exception as e:
            self.log_message(f"❌ Errore trading: {e}")
        finally:
            final_roi = ((self.balance - self.initial_balance) / self.initial_balance) * 100
            self.log_message(f"🏁 Trading terminato | Balance finale: ${self.balance:.2f} | ROI: {final_roi:+.1f}%")

def main():
    """Funzione principale"""
    print("🎯 AurumBotX Mega Mainnet Strategy")
    print("=" * 50)
    
    # Inizializza strategia
    strategy = MegaMainnetStrategy(initial_balance=1000.0)
    
    print(f"\\n⚙️ CONFIGURAZIONE MAINNET:")
    print(f"💰 Position Size: {strategy.config['base_position_size']:.1%} - {strategy.config['max_position_size']:.1%}")
    print(f"🎯 Confidence Min: {strategy.config['min_confidence']:.1%}")
    print(f"📈 Profit Target: {strategy.config['min_profit_target']:.1%} - {strategy.config['max_profit_target']:.1%}")
    print(f"🛡️ Max Loss: {strategy.config['max_loss_per_trade']:.1%}")
    print(f"⏰ Ciclo: {strategy.config['cycle_interval']}s")
    
    print(f"\\n🚀 Avvio trading automatico...")
    
    # Avvia trading
    strategy.run_continuous_trading()

if __name__ == "__main__":
    main()

