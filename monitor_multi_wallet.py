#!/usr/bin/env python3
"""
AurumBotX - Multi-Wallet Monitor
Dashboard unificato per monitorare tutte le sessioni wallet
"""

import json
import os
from datetime import datetime
from pathlib import Path

WALLETS = [
    {"id": "wallet_100", "name": "Wallet $100", "state_file": "demo_trading/always_on_state.json"},
    {"id": "wallet_500", "name": "Wallet $500", "state_file": "demo_trading/wallet_500/state.json"},
    {"id": "wallet_1000", "name": "Wallet $1000", "state_file": "demo_trading/wallet_1000/state.json"},
    {"id": "wallet_5000", "name": "Wallet $5000", "state_file": "demo_trading/wallet_5000/state.json"}
]

def load_wallet_state(wallet):
    """Carica lo stato di un wallet"""
    try:
        with open(wallet['state_file'], 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def print_header():
    """Stampa header dashboard"""
    print("\n" + "="*120)
    print(" " * 40 + "AURUMBOTX - MULTI-WALLET DASHBOARD")
    print("="*120)
    print(f"Aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120 + "\n")

def print_summary(wallets_data):
    """Stampa riepilogo generale"""
    total_capital = sum(w['capital'] for w in wallets_data if w)
    total_initial = sum(w['initial_capital'] for w in wallets_data if w)
    total_pnl = sum(w['total_pnl'] for w in wallets_data if w)
    total_trades = sum(w['total_trades'] for w in wallets_data if w)
    total_wins = sum(w['winning_trades'] for w in wallets_data if w)
    
    avg_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    total_roi = ((total_capital / total_initial - 1) * 100) if total_initial > 0 else 0
    
    print("### RIEPILOGO GENERALE ###\n")
    print(f"{'Capitale Totale Iniziale:':<30} ${total_initial:>12,.2f}")
    print(f"{'Capitale Totale Corrente:':<30} ${total_capital:>12,.2f}")
    print(f"{'P&L Totale:':<30} ${total_pnl:>12,.2f}")
    print(f"{'ROI Totale:':<30} {total_roi:>11,.2f}%")
    print(f"")
    print(f"{'Trade Totali:':<30} {total_trades:>13,}")
    print(f"{'Winning Trades:':<30} {total_wins:>13,}")
    print(f"{'Win Rate Medio:':<30} {avg_win_rate:>11,.1f}%")
    print()

def print_wallets_table(wallets_data):
    """Stampa tabella wallet"""
    print("### DETTAGLIO WALLET ###\n")
    
    header = f"{'Wallet':<15} {'Capitale':<15} {'P&L':<15} {'ROI':<10} {'Trade':<10} {'Win Rate':<10} {'Status':<10}"
    print(header)
    print("-" * 120)
    
    for i, (wallet, data) in enumerate(zip(WALLETS, wallets_data)):
        if data:
            capital = f"${data['capital']:,.2f}"
            pnl = f"${data['total_pnl']:+,.2f}"
            roi = f"{((data['capital']/data['initial_capital']-1)*100):+.2f}%"
            trades = f"{data['total_trades']}"
            wr = f"{(data['winning_trades']/data['total_trades']*100):.1f}%" if data['total_trades'] > 0 else "N/A"
            status = "✅ ATTIVO"
        else:
            capital = "N/A"
            pnl = "N/A"
            roi = "N/A"
            trades = "0"
            wr = "N/A"
            status = "❌ FERMO"
        
        print(f"{wallet['name']:<15} {capital:<15} {pnl:<15} {roi:<10} {trades:<10} {wr:<10} {status:<10}")
    
    print()

def print_best_performers(wallets_data):
    """Stampa i migliori performer"""
    print("### TOP PERFORMERS ###\n")
    
    # Filtra wallet attivi
    active_wallets = [(w, d) for w, d in zip(WALLETS, wallets_data) if d and d['total_trades'] > 0]
    
    if not active_wallets:
        print("Nessun wallet con trade eseguiti\n")
        return
    
    # Ordina per ROI
    sorted_by_roi = sorted(active_wallets, key=lambda x: (x[1]['capital']/x[1]['initial_capital']-1), reverse=True)
    
    print("🏆 Migliore ROI:")
    if sorted_by_roi:
        w, d = sorted_by_roi[0]
        roi = ((d['capital']/d['initial_capital']-1)*100)
        print(f"   {w['name']}: {roi:+.2f}% (${d['total_pnl']:+,.2f})")
    
    # Ordina per P&L assoluto
    sorted_by_pnl = sorted(active_wallets, key=lambda x: x[1]['total_pnl'], reverse=True)
    
    print("\n💰 Maggiore P&L:")
    if sorted_by_pnl:
        w, d = sorted_by_pnl[0]
        print(f"   {w['name']}: ${d['total_pnl']:+,.2f}")
    
    # Ordina per Win Rate
    sorted_by_wr = sorted(active_wallets, key=lambda x: x[1]['winning_trades']/x[1]['total_trades'] if x[1]['total_trades'] > 0 else 0, reverse=True)
    
    print("\n🎯 Migliore Win Rate:")
    if sorted_by_wr:
        w, d = sorted_by_wr[0]
        wr = (d['winning_trades']/d['total_trades']*100) if d['total_trades'] > 0 else 0
        print(f"   {w['name']}: {wr:.1f}% ({d['winning_trades']}/{d['total_trades']} trade)")
    
    print()

def print_recent_activity(wallets_data):
    """Stampa attività recente"""
    print("### ATTIVITÀ RECENTE (Ultimi 3 trade per wallet) ###\n")
    
    for wallet, data in zip(WALLETS, wallets_data):
        if data and data['trades_history']:
            print(f"{wallet['name']}:")
            
            recent_trades = data['trades_history'][-3:]
            for i, trade in enumerate(recent_trades, len(data['trades_history'])-2):
                result_icon = "✅" if trade['result'] == 'WIN' else "❌"
                print(f"  #{i}: {trade['pair']:<12} {trade['action']:<6} {result_icon} {trade['result']:<6} P&L: ${trade['pnl']:+.4f}")
            print()

def main():
    """Main dashboard"""
    print_header()
    
    # Carica dati wallet
    wallets_data = [load_wallet_state(w) for w in WALLETS]
    
    # Stampa sezioni
    print_summary(wallets_data)
    print_wallets_table(wallets_data)
    print_best_performers(wallets_data)
    print_recent_activity(wallets_data)
    
    print("="*120)
    print("Per aggiornare: python3 monitor_multi_wallet.py")
    print("="*120 + "\n")

if __name__ == '__main__':
    main()

