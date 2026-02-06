# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

from flask import Flask, jsonify, request
import sys
sys.path.append('/home/ubuntu/AurumBotX')
from src.core.trading_engine_usdt_sqlalchemy import TradingEngineUSDT

app = Flask(__name__)

# Inizializza il trading engine (in un'applicazione reale, lo faresti in modo più strutturato)
engine = TradingEngineUSDT()

@app.route('/api/status')
def status():
    return jsonify({'status': 'online'})

@app.route("/api/balance")
def get_balance():
    balance = engine.get_balance()
    return jsonify(balance)

@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    reason = request.json.get('reason', 'Manual stop from API')
    result = engine.emergency_stop(reason=reason)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5678)

