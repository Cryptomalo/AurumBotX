#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX - AI Autonomous Always-On System
Sistema sempre attivo in background con auto-recovery
Capitale: 100 USD | AI Models: 327 | Mode: Demo Mainnet
"""

import json
import time
import random
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Configurazione
CONFIG_FILE = Path("/home/ubuntu/AurumBotX/config/demo_mainnet_100usd.json")
STATE_FILE = Path("/home/ubuntu/AurumBotX/demo_trading/always_on_state.json")
LOG_FILE = Path("/home/ubuntu/AurumBotX/logs/ai_autonomous_always_on.log")
RESULTS_DIR = Path("/home/ubuntu/AurumBotX/demo_trading/always_on_results")

# Crea directory se non esiste
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Sistema di logging
class Logger:
    def __init__(self, log_file):
        self.log_file = log_file
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")

logger = Logger(LOG_FILE)

# Gestione segnali per graceful shutdown
class GracefulKiller:
    kill_now = False
    
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    
    def exit_gracefully(self, signum, frame):
        logger.log("Ricevuto segnale di shutdown, salvando stato...", "WARNING")
        self.kill_now = True

killer = GracefulKiller()

# Carica configurazione
logger.log("="*100)
logger.log("AURUMBOTX - AI AUTONOMOUS ALWAYS-ON SYSTEM")
logger.log("="*100)

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

logger.log(f"Configurazione caricata: {CONFIG_FILE}")
logger.log(f"Capitale Iniziale: ${config['initial_capital']}")
logger.log(f"AI Models: {config['ai_configuration']['models_count']}")
logger.log(f"Mode: {config['mode']}")

# Stato del sistema
class TradingState:
    def __init__(self):
        self.capital = config['initial_capital']
        self.initial_capital = config['initial_capital']
        self.total_cycles = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.trades_history = []
        self.ai_decisions = []
        self.strategy_usage = {s: 0 for s in config['strategy_settings']['available_strategies']}
        self.start_time = datetime.now()
        self.last_save_time = datetime.now()
        self.last_daily_reset = datetime.now()
        
    def load_state(self):
        """Carica stato salvato se esiste"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                
                self.capital = data.get('capital', self.initial_capital)
                self.total_cycles = data.get('total_cycles', 0)
                self.total_trades = data.get('total_trades', 0)
                self.winning_trades = data.get('winning_trades', 0)
                self.losing_trades = data.get('losing_trades', 0)
                self.total_pnl = data.get('total_pnl', 0.0)
                self.daily_pnl = data.get('daily_pnl', 0.0)
                self.trades_history = data.get('trades_history', [])
                self.ai_decisions = data.get('ai_decisions', [])
                self.strategy_usage = data.get('strategy_usage', self.strategy_usage)
                self.start_time = datetime.fromisoformat(data.get('start_time', datetime.now().isoformat()))
                self.last_daily_reset = datetime.fromisoformat(data.get('last_daily_reset', datetime.now().isoformat()))
                
                logger.log(f"Stato caricato da: {STATE_FILE}", "INFO")
                logger.log(f"Capitale ripristinato: ${self.capital:.2f}", "INFO")
                logger.log(f"Cicli completati: {self.total_cycles}", "INFO")
                
            except Exception as e:
                logger.log(f"Errore caricamento stato: {e}", "ERROR")
                logger.log("Inizio con stato pulito", "WARNING")
    
    def save_state(self):
        """Salva stato corrente"""
        try:
            data = {
                'capital': self.capital,
                'initial_capital': self.initial_capital,
                'total_cycles': self.total_cycles,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'total_pnl': self.total_pnl,
                'daily_pnl': self.daily_pnl,
                'trades_history': self.trades_history[-100:],  # Ultimi 100 trade
                'ai_decisions': self.ai_decisions[-500:],  # Ultime 500 decisioni
                'strategy_usage': self.strategy_usage,
                'start_time': self.start_time.isoformat(),
                'last_save_time': datetime.now().isoformat(),
                'last_daily_reset': self.last_daily_reset.isoformat()
            }
            
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.last_save_time = datetime.now()
            logger.log(f"Stato salvato: {STATE_FILE}", "DEBUG")
            
        except Exception as e:
            logger.log(f"Errore salvataggio stato: {e}", "ERROR")
    
    def reset_daily_stats(self):
        """Reset statistiche giornaliere"""
        self.daily_pnl = 0.0
        self.last_daily_reset = datetime.now()
        logger.log("Statistiche giornaliere resettate", "INFO")

# Inizializza stato
state = TradingState()
state.load_state()

# Market data simulator (prezzi realistici)
class MarketDataProvider:
    def __init__(self):
        self.market_data = {
            'BTC/USDT': {'price': 50000, 'volatility': 0.04},
            'ETH/USDT': {'price': 3000, 'volatility': 0.05},
            'SOL/USDT': {'price': 150, 'volatility': 0.06},
            'BNB/USDT': {'price': 400, 'volatility': 0.04},
            'XRP/USDT': {'price': 0.50, 'volatility': 0.05}
        }
    
    def update_prices(self):
        """Aggiorna prezzi di mercato con movimento realistico"""
        for pair in self.market_data:
            data = self.market_data[pair]
            volatility = data['volatility']
            
            # Movimento prezzo realistico
            price_change = random.uniform(-volatility, volatility)
            new_price = data['price'] * (1 + price_change)
            
            # Aggiorna volatilità (varia nel tempo)
            volatility_change = random.uniform(-0.005, 0.005)
            new_volatility = max(0.02, min(0.10, volatility + volatility_change))
            
            self.market_data[pair]['price'] = new_price
            self.market_data[pair]['volatility'] = new_volatility
    
    def get_data(self, pair):
        return self.market_data.get(pair, {})

market = MarketDataProvider()

# AI Decision Engine
def ai_select_strategy(market_conditions, capital, ai_models):
    """AI seleziona strategia ottimale"""
    strategies = config['strategy_settings']['available_strategies']
    strategy_votes = {}
    
    avg_vol = sum(d['volatility'] for d in market_conditions.values()) / len(market_conditions)
    
    for strategy in strategies:
        if strategy == 'volatility_surfing':
            votes = int(ai_models * (0.15 + avg_vol * 2))
        elif strategy == 'liquidity_hunting':
            votes = int(ai_models * (0.25 - avg_vol))
        elif strategy == 'smart_position_sizing':
            votes = int(ai_models * random.uniform(0.15, 0.25))
        elif strategy == 'multi_timeframe_confluence':
            votes = int(ai_models * random.uniform(0.10, 0.20))
        elif strategy == 'adaptive_risk_management':
            capital_factor = 1.0 if capital < 150 else 0.8
            votes = int(ai_models * random.uniform(0.15, 0.25) * capital_factor)
        else:
            votes = int(ai_models * 0.15)
        
        strategy_votes[strategy] = votes
    
    selected = max(strategy_votes, key=strategy_votes.get)
    confidence = strategy_votes[selected] / ai_models
    
    return selected, confidence

def ai_analyze_pair(pair, market_data, strategy, ai_models):
    """AI analizza coppia e genera decisione"""
    data = market_data.get_data(pair)
    if not data:
        return None
    
    price = data['price']
    volatility = data['volatility']
    
    # Simula voti AI
    buy_votes = 0
    sell_votes = 0
    hold_votes = 0
    
    if strategy == 'volatility_surfing':
        if volatility > 0.04:
            buy_votes = random.randint(120, 180)
            sell_votes = random.randint(40, 80)
            hold_votes = random.randint(60, 100)
        else:
            hold_votes = random.randint(150, 200)
            buy_votes = random.randint(60, 100)
            sell_votes = random.randint(20, 50)
    elif strategy == 'adaptive_risk_management':
        buy_votes = random.randint(80, 130)
        sell_votes = random.randint(30, 80)
        hold_votes = random.randint(120, 170)
    else:
        buy_votes = random.randint(100, 150)
        sell_votes = random.randint(50, 100)
        hold_votes = random.randint(80, 130)
    
    total_votes = buy_votes + sell_votes + (hold_votes if 'hold_votes' in locals() else 0)
    remaining = ai_models - total_votes
    if 'hold_votes' not in locals():
        hold_votes = remaining
    else:
        hold_votes += remaining
    
    votes = {'BUY': buy_votes, 'SELL': sell_votes, 'HOLD': hold_votes}
    action = max(votes, key=votes.get)
    confidence = votes[action] / ai_models
    
    # Position sizing
    if action in ['BUY', 'SELL']:
        base_size = 0.12
        position_size_pct = base_size * confidence * (1.0 - volatility / 0.10)
        position_size_pct = max(0.05, min(0.20, position_size_pct))
        
        stop_loss_pct = min(0.04, 0.015 + volatility * 0.5)
        take_profit_pct = min(0.08, 0.025 + volatility * 0.8 + confidence * 0.02)
    else:
        position_size_pct = 0.0
        stop_loss_pct = 0.0
        take_profit_pct = 0.0
    
    return {
        'pair': pair,
        'action': action,
        'confidence': confidence,
        'votes': votes,
        'price': price,
        'volatility': volatility,
        'position_size_pct': position_size_pct,
        'stop_loss_pct': stop_loss_pct,
        'take_profit_pct': take_profit_pct,
        'strategy_used': strategy
    }

def execute_trade(decision, capital):
    """Esegue trade con simulazione realistica"""
    pair = decision['pair']
    action = decision['action']
    entry_price = decision['price']
    position_size_pct = decision['position_size_pct']
    stop_loss_pct = decision['stop_loss_pct']
    take_profit_pct = decision['take_profit_pct']
    
    position_size = capital * position_size_pct
    
    # Slippage
    slippage_pct = random.uniform(0.0001, 0.001)
    entry_price *= (1 + slippage_pct) if action == 'BUY' else (1 - slippage_pct)
    
    # Movimento prezzo
    volatility = decision['volatility']
    price_change = random.uniform(-volatility, volatility * 1.5)
    
    # Determina exit
    if action == 'BUY':
        if price_change < -stop_loss_pct:
            exit_price = entry_price * (1 - stop_loss_pct)
            pnl_pct = -stop_loss_pct
        elif price_change > take_profit_pct:
            exit_price = entry_price * (1 + take_profit_pct)
            pnl_pct = take_profit_pct
        else:
            exit_price = entry_price * (1 + price_change)
            pnl_pct = price_change
    else:  # SELL
        if price_change > stop_loss_pct:
            exit_price = entry_price * (1 + stop_loss_pct)
            pnl_pct = -stop_loss_pct
        elif price_change < -take_profit_pct:
            exit_price = entry_price * (1 - take_profit_pct)
            pnl_pct = take_profit_pct
        else:
            exit_price = entry_price * (1 - price_change)
            pnl_pct = -price_change
    
    pnl = position_size * pnl_pct
    fee = position_size * 0.002
    pnl -= fee
    
    result = 'WIN' if pnl > 0 else 'LOSS'
    
    return {
        'pair': pair,
        'action': action,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'position_size': position_size,
        'pnl': pnl,
        'pnl_pct': pnl_pct * 100,
        'fee': fee,
        'result': result,
        'strategy': decision['strategy_used'],
        'timestamp': datetime.now().isoformat()
    }

# Main loop
logger.log("="*100)
logger.log("SISTEMA ALWAYS-ON AVVIATO")
logger.log("="*100)
logger.log(f"Capitale Iniziale: ${state.capital:.2f}")
logger.log(f"Cicli già completati: {state.total_cycles}")
logger.log(f"Trade già eseguiti: {state.total_trades}")
logger.log("Premi Ctrl+C per fermare gracefully")
logger.log("="*100)

SAVE_INTERVAL = 1800  # 30 minuti
CYCLE_INTERVAL = 300  # 5 minuti tra cicli

try:
    while not killer.kill_now:
        state.total_cycles += 1
        cycle_start = datetime.now()
        
        logger.log(f"\n{'#'*100}")
        logger.log(f"CICLO {state.total_cycles} | Capitale: ${state.capital:.2f}")
        logger.log(f"{'#'*100}")
        
        # Aggiorna prezzi
        market.update_prices()
        
        # AI seleziona strategia
        strategy, strategy_conf = ai_select_strategy(market.market_data, state.capital, 327)
        state.strategy_usage[strategy] += 1
        
        logger.log(f"AI Strategy: {strategy} (Conf: {strategy_conf*100:.1f}%)")
        
        # Analizza coppie
        for pair in config['trading_pairs']:
            decision = ai_analyze_pair(pair, market, strategy, 327)
            
            if decision:
                state.ai_decisions.append({
                    'cycle': state.total_cycles,
                    'timestamp': datetime.now().isoformat(),
                    **decision
                })
                
                logger.log(f"  {pair}: {decision['action']} (Conf: {decision['confidence']*100:.1f}%)")
                
                # Esegui trade se sopra threshold
                if decision['confidence'] >= config['ai_configuration']['confidence_threshold'] and decision['action'] in ['BUY', 'SELL']:
                    trade = execute_trade(decision, state.capital)
                    
                    state.capital += trade['pnl']
                    state.total_pnl += trade['pnl']
                    state.daily_pnl += trade['pnl']
                    state.total_trades += 1
                    
                    if trade['result'] == 'WIN':
                        state.winning_trades += 1
                    else:
                        state.losing_trades += 1
                    
                    state.trades_history.append({
                        'cycle': state.total_cycles,
                        **trade,
                        'capital_after': state.capital
                    })
                    
                    logger.log(f"    TRADE: {trade['result']} | P&L: ${trade['pnl']:+.2f} | Capitale: ${state.capital:.2f}")
        
        # Check daily reset
        if (datetime.now() - state.last_daily_reset).days >= 1:
            state.reset_daily_stats()
        
        # Check circuit breaker
        daily_loss_pct = (state.daily_pnl / state.initial_capital) * 100
        if daily_loss_pct < -config['risk_management']['daily_loss_limit_percentage']:
            logger.log(f"CIRCUIT BREAKER: Daily loss {daily_loss_pct:.2f}%", "WARNING")
            logger.log("Trading sospeso fino a domani", "WARNING")
            time.sleep(3600)  # Pausa 1 ora
            continue
        
        # Salva stato periodicamente
        if (datetime.now() - state.last_save_time).seconds >= SAVE_INTERVAL:
            state.save_state()
            logger.log(f"Stato salvato (ogni {SAVE_INTERVAL/60:.0f} min)", "INFO")
        
        # Pausa tra cicli
        time.sleep(CYCLE_INTERVAL)
        
except KeyboardInterrupt:
    logger.log("\nInterruzione manuale ricevuta", "WARNING")
except Exception as e:
    logger.log(f"ERRORE: {e}", "ERROR")
finally:
    # Salva stato finale
    logger.log("\n" + "="*100)
    logger.log("SHUTDOWN SISTEMA")
    logger.log("="*100)
    
    state.save_state()
    
    # Statistiche finali
    roi = ((state.capital - state.initial_capital) / state.initial_capital) * 100
    win_rate = (state.winning_trades / state.total_trades * 100) if state.total_trades > 0 else 0
    
    logger.log(f"Cicli Totali: {state.total_cycles}")
    logger.log(f"Trade Totali: {state.total_trades}")
    logger.log(f"Capitale Finale: ${state.capital:.2f}")
    logger.log(f"ROI: {roi:+.2f}%")
    logger.log(f"Win Rate: {win_rate:.1f}%")
    logger.log(f"Stato salvato in: {STATE_FILE}")
    logger.log("="*100)

