#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX - Wallet Runner
Script generico per avviare sessioni wallet specifiche
"""

import sys
import os
import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path

# Configurazione passata come argomento
if len(sys.argv) < 2:
    print("Usage: python3 wallet_runner.py <config_file>")
    sys.exit(1)

CONFIG_FILE = sys.argv[1]

# Carica configurazione
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

WALLET_ID = config['wallet_id']
INITIAL_CAPITAL = config['initial_capital']
STATE_FILE = f"demo_trading/{WALLET_ID}/state.json"
LOG_FILE = f"logs/{WALLET_ID}.log"

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def load_or_create_state():
    """Carica o crea lo stato del wallet"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    
    return {
        "wallet_id": WALLET_ID,
        "initial_capital": INITIAL_CAPITAL,
        "capital": INITIAL_CAPITAL,
        "total_cycles": 0,
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "total_pnl": 0.0,
        "daily_pnl": 0.0,
        "trades_history": [],
        "start_time": datetime.now().isoformat()
    }

def save_state(state):
    """Salva lo stato del wallet"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def ai_analyze_pair(pair, capital, config):
    """Simula analisi AI per una coppia"""
    confidence = random.uniform(35, 75)
    
    if confidence > config['ai_configuration']['confidence_threshold'] * 100:
        action = random.choice(['BUY', 'SELL']) if confidence > 60 else 'BUY'
    else:
        action = 'HOLD'
    
    return {
        'pair': pair,
        'action': action,
        'confidence': confidence
    }

def execute_trade(pair, action, capital, config):
    """Esegue un trade simulato"""
    position_size_pct = config['risk_management']['max_position_size_percentage'] / 100
    position_size = capital * position_size_pct
    
    # Simula risultato
    win_prob = 0.75  # 75% win rate target
    is_win = random.random() < win_prob
    
    if is_win:
        pnl_pct = random.uniform(0.5, 3.5)  # 0.5% - 3.5% profit
        pnl = position_size * (pnl_pct / 100)
        result = 'WIN'
    else:
        pnl_pct = random.uniform(-2.0, -0.3)  # -2.0% - -0.3% loss
        pnl = position_size * (pnl_pct / 100)
        result = 'LOSS'
    
    # Applica fee
    fee = position_size * (config['execution_parameters']['fee_percentage'] / 100)
    pnl -= fee
    
    return {
        'pair': pair,
        'action': action,
        'result': result,
        'pnl': pnl,
        'capital_after': capital + pnl
    }

def run_cycle(state, config):
    """Esegue un ciclo di trading"""
    state['total_cycles'] += 1
    cycle = state['total_cycles']
    
    logger.info("=" * 80)
    logger.info(f"CICLO {cycle} | Wallet: {WALLET_ID} | Capitale: ${state['capital']:.2f}")
    logger.info("=" * 80)
    
    # Analizza coppie
    for pair in config['trading_pairs']:
        analysis = ai_analyze_pair(pair, state['capital'], config)
        
        logger.info(f"  {pair}: {analysis['action']} (Conf: {analysis['confidence']:.1f}%)")
        
        if analysis['action'] in ['BUY', 'SELL']:
            trade = execute_trade(pair, analysis['action'], state['capital'], config)
            
            state['capital'] = trade['capital_after']
            state['total_trades'] += 1
            state['total_pnl'] += trade['pnl']
            state['daily_pnl'] += trade['pnl']
            
            if trade['result'] == 'WIN':
                state['winning_trades'] += 1
            else:
                state['losing_trades'] += 1
            
            state['trades_history'].append(trade)
            
            logger.info(f"    TRADE: {trade['result']} | P&L: ${trade['pnl']:+.4f} | Capitale: ${trade['capital_after']:.2f}")
    
    return state

def main():
    logger.info("=" * 80)
    logger.info(f"AURUMBOTX - WALLET RUNNER: {WALLET_ID}")
    logger.info("=" * 80)
    logger.info(f"Configurazione: {CONFIG_FILE}")
    logger.info(f"Capitale Iniziale: ${INITIAL_CAPITAL}")
    logger.info(f"Confidence Threshold: {config['ai_configuration']['confidence_threshold']*100}%")
    logger.info(f"Position Size: {config['risk_management']['max_position_size_percentage']}%")
    logger.info("=" * 80)
    
    state = load_or_create_state()
    
    if state['total_cycles'] > 0:
        logger.info(f"Stato ripristinato: Capitale ${state['capital']:.2f}, Cicli {state['total_cycles']}")
    
    logger.info(f"SISTEMA AVVIATO - {WALLET_ID}")
    logger.info("=" * 80)
    
    try:
        while True:
            state = run_cycle(state, config)
            save_state(state)
            
            # Pausa tra cicli (5 minuti)
            time.sleep(300)
            
    except KeyboardInterrupt:
        logger.warning("Ricevuto segnale di shutdown, salvando stato...")
        save_state(state)
        logger.info(f"Stato salvato. Capitale finale: ${state['capital']:.2f}")

if __name__ == '__main__':
    main()

