#!/usr/bin/env python3
"""
AurumBotX - Multi-Wallet API Server
API REST per la dashboard web multi-wallet
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__, static_folder='web_interface', static_url_path='')
CORS(app)

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
            data = json.load(f)
            data['wallet_id'] = wallet['id']
            data['wallet_name'] = wallet['name']
            return data
    except FileNotFoundError:
        return None

@app.route('/')
def index():
    """Serve la dashboard web"""
    return send_from_directory('web_interface', 'index.html')

@app.route('/api/status')
def api_status():
    """Status API"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "version": "2.3-multi-wallet"
    })

@app.route('/api/wallets')
def api_wallets():
    """Ritorna lista wallet"""
    wallets_data = []
    
    for wallet in WALLETS:
        state = load_wallet_state(wallet)
        if state:
            wallets_data.append({
                "id": wallet['id'],
                "name": wallet['name'],
                "capital": state.get('capital', 0),
                "initial_capital": state.get('initial_capital', 0),
                "total_pnl": state.get('total_pnl', 0),
                "total_trades": state.get('total_trades', 0),
                "winning_trades": state.get('winning_trades', 0),
                "losing_trades": state.get('losing_trades', 0),
                "win_rate": (state.get('winning_trades', 0) / state.get('total_trades', 1) * 100) if state.get('total_trades', 0) > 0 else 0,
                "roi": ((state.get('capital', 0) / state.get('initial_capital', 1) - 1) * 100) if state.get('initial_capital', 0) > 0 else 0,
                "status": "active"
            })
        else:
            wallets_data.append({
                "id": wallet['id'],
                "name": wallet['name'],
                "capital": 0,
                "initial_capital": 0,
                "total_pnl": 0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "roi": 0,
                "status": "inactive"
            })
    
    return jsonify(wallets_data)

@app.route('/api/summary')
def api_summary():
    """Ritorna riepilogo generale"""
    wallets_data = [load_wallet_state(w) for w in WALLETS]
    wallets_data = [w for w in wallets_data if w]  # Filtra None
    
    if not wallets_data:
        return jsonify({
            "total_capital": 0,
            "total_initial_capital": 0,
            "total_pnl": 0,
            "total_roi": 0,
            "total_trades": 0,
            "total_wins": 0,
            "avg_win_rate": 0,
            "active_wallets": 0
        })
    
    total_capital = sum(w.get('capital', 0) for w in wallets_data)
    total_initial = sum(w.get('initial_capital', 0) for w in wallets_data)
    total_pnl = sum(w.get('total_pnl', 0) for w in wallets_data)
    total_trades = sum(w.get('total_trades', 0) for w in wallets_data)
    total_wins = sum(w.get('winning_trades', 0) for w in wallets_data)
    
    return jsonify({
        "total_capital": total_capital,
        "total_initial_capital": total_initial,
        "total_pnl": total_pnl,
        "total_roi": ((total_capital / total_initial - 1) * 100) if total_initial > 0 else 0,
        "total_trades": total_trades,
        "total_wins": total_wins,
        "avg_win_rate": (total_wins / total_trades * 100) if total_trades > 0 else 0,
        "active_wallets": len(wallets_data)
    })

@app.route('/api/wallet/<wallet_id>')
def api_wallet_detail(wallet_id):
    """Ritorna dettagli di un wallet specifico"""
    wallet = next((w for w in WALLETS if w['id'] == wallet_id), None)
    
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404
    
    state = load_wallet_state(wallet)
    
    if not state:
        return jsonify({"error": "Wallet state not found"}), 404
    
    return jsonify(state)

@app.route('/api/trades')
def api_trades():
    """Ritorna tutti i trade di tutti i wallet"""
    all_trades = []
    
    for wallet in WALLETS:
        state = load_wallet_state(wallet)
        if state and 'trades_history' in state:
            for trade in state['trades_history']:
                trade['wallet_id'] = wallet['id']
                trade['wallet_name'] = wallet['name']
                all_trades.append(trade)
    
    # Ordina per timestamp (più recenti prima)
    all_trades.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return jsonify(all_trades[:100])  # Ultimi 100 trade

@app.route('/api/trades/<wallet_id>')
def api_wallet_trades(wallet_id):
    """Ritorna trade di un wallet specifico"""
    wallet = next((w for w in WALLETS if w['id'] == wallet_id), None)
    
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404
    
    state = load_wallet_state(wallet)
    
    if not state or 'trades_history' not in state:
        return jsonify([])
    
    return jsonify(state['trades_history'][-50:])  # Ultimi 50 trade

if __name__ == '__main__':
    print("="*80)
    print("AURUMBOTX - MULTI-WALLET API SERVER")
    print("="*80)
    print(f"Dashboard: http://localhost:8080")
    print(f"API Endpoints:")
    print(f"  - GET /api/status")
    print(f"  - GET /api/wallets")
    print(f"  - GET /api/summary")
    print(f"  - GET /api/wallet/<wallet_id>")
    print(f"  - GET /api/trades")
    print(f"  - GET /api/trades/<wallet_id>")
    print("="*80)
    
    app.run(host='0.0.0.0', port=8080, debug=False)

