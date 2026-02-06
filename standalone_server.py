#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Standalone Server
Server completamente autonomo per accesso team
"""

import http.server
import socketserver
import json
import sqlite3
import os
import threading
import time
from datetime import datetime
import urllib.parse
import base64

class AurumBotXHandler(http.server.SimpleHTTPRequestHandler):
    """Handler per server AurumBotX"""
    
    def do_GET(self):
        """Gestisce richieste GET"""
        if self.path == '/' or self.path == '/dashboard':
            self.serve_dashboard()
        elif self.path == '/api/trading-data':
            self.serve_trading_data()
        elif self.path == '/api/system-status':
            self.serve_system_status()
        elif self.path == '/api/bot-control':
            self.serve_bot_control()
        else:
            super().do_GET()
    
    def do_POST(self):
        """Gestisce richieste POST"""
        if self.path == '/api/bot-action':
            self.handle_bot_action()
        elif self.path == '/api/login':
            self.handle_login()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve dashboard principale"""
        html_content = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 AurumBotX Team Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 3em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-value { font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }
        .stat-label { font-size: 1.1em; opacity: 0.8; }
        .controls { display: flex; gap: 15px; justify-content: center; margin-bottom: 30px; flex-wrap: wrap; }
        .btn { 
            padding: 12px 24px; 
            border: none; 
            border-radius: 25px; 
            font-size: 1.1em; 
            cursor: pointer; 
            transition: all 0.3s ease;
            font-weight: bold;
        }
        .btn-start { background: #4CAF50; color: white; }
        .btn-stop { background: #f44336; color: white; }
        .btn-restart { background: #ff9800; color: white; }
        .btn-data { background: #2196F3; color: white; }
        .btn:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .data-section { 
            background: rgba(255,255,255,0.1); 
            padding: 25px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .data-table th, .data-table td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid rgba(255,255,255,0.2); 
        }
        .data-table th { background: rgba(255,255,255,0.2); font-weight: bold; }
        .profit-positive { color: #4CAF50; font-weight: bold; }
        .profit-negative { color: #f44336; font-weight: bold; }
        .status-indicator { 
            display: inline-block; 
            width: 12px; 
            height: 12px; 
            border-radius: 50%; 
            margin-right: 8px; 
        }
        .status-active { background: #4CAF50; }
        .status-inactive { background: #f44336; }
        .login-form { 
            max-width: 400px; 
            margin: 100px auto; 
            background: rgba(255,255,255,0.1); 
            padding: 30px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
        }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input { 
            width: 100%; 
            padding: 12px; 
            border: none; 
            border-radius: 8px; 
            background: rgba(255,255,255,0.2); 
            color: white; 
            font-size: 1.1em;
        }
        .form-group input::placeholder { color: rgba(255,255,255,0.7); }
        .refresh-btn { 
            position: fixed; 
            bottom: 20px; 
            right: 20px; 
            background: #4CAF50; 
            color: white; 
            border: none; 
            border-radius: 50%; 
            width: 60px; 
            height: 60px; 
            font-size: 1.5em; 
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        @media (max-width: 768px) {
            .header h1 { font-size: 2em; }
            .stats-grid { grid-template-columns: 1fr; }
            .controls { flex-direction: column; align-items: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AurumBotX Team Dashboard</h1>
            <p>Sistema Trading Autonomo - Controllo Completo Team</p>
        </div>
        
        <div id="loginSection" class="login-form" style="display: none;">
            <h2 style="text-align: center; margin-bottom: 20px;">🔐 Team Login</h2>
            <div class="form-group">
                <label>Username:</label>
                <input type="text" id="username" placeholder="Inserisci username">
            </div>
            <div class="form-group">
                <label>Password:</label>
                <input type="password" id="password" placeholder="Inserisci password">
            </div>
            <button class="btn btn-start" style="width: 100%;" onclick="login()">🚀 Accedi</button>
            <p style="text-align: center; margin-top: 15px; opacity: 0.8;">
                Imposta AURUMBOTX_ADMIN_PASSWORD (o ADMIN_PASSWORD) nelle variabili ambiente
            </p>
        </div>
        
        <div id="dashboardSection">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="totalTrades">-</div>
                    <div class="stat-label">🎯 Trade Totali</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="totalProfit">-</div>
                    <div class="stat-label">💰 Profitto Totale</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="winRate">-</div>
                    <div class="stat-label">✅ Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="systemStatus">-</div>
                    <div class="stat-label">🤖 Status Sistema</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-start" onclick="startBot()">🚀 Start Bot</button>
                <button class="btn btn-stop" onclick="stopBot()">🛑 Stop Bot</button>
                <button class="btn btn-restart" onclick="restartBot()">🔄 Restart</button>
                <button class="btn btn-data" onclick="refreshData()">📊 Refresh Data</button>
            </div>
            
            <div class="data-section">
                <h3>📈 Performance Sistemi Trading</h3>
                <div id="systemsData">Caricamento dati...</div>
            </div>
            
            <div class="data-section">
                <h3>🔥 Ultimi Trade</h3>
                <div id="recentTrades">Caricamento trade...</div>
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()">🔄</button>
    
    <script>
        let authenticated = false;
        
        function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // Simulazione login (in produzione usare API reale)
            const expectedUsername = "__ADMIN_USERNAME__";
            const expectedPassword = "__ADMIN_PASSWORD__";
            if (username === expectedUsername && password === expectedPassword) {
                authenticated = true;
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('dashboardSection').style.display = 'block';
                refreshData();
            } else {
                alert('❌ Credenziali non valide');
            }
        }
        
        function startBot() {
            if (!authenticated) return;
            fetch('/api/bot-action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'start'})
            }).then(() => {
                alert('🚀 Bot avviato!');
                refreshData();
            });
        }
        
        function stopBot() {
            if (!authenticated) return;
            fetch('/api/bot-action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'stop'})
            }).then(() => {
                alert('🛑 Bot fermato!');
                refreshData();
            });
        }
        
        function restartBot() {
            if (!authenticated) return;
            fetch('/api/bot-action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'restart'})
            }).then(() => {
                alert('🔄 Bot riavviato!');
                refreshData();
            });
        }
        
        function refreshData() {
            if (!authenticated) return;
            
            // Carica dati trading
            fetch('/api/trading-data')
                .then(response => response.json())
                .then(data => {
                    updateStats(data);
                    updateSystemsData(data);
                    updateRecentTrades(data);
                })
                .catch(error => console.error('Errore caricamento dati:', error));
        }
        
        function updateStats(data) {
            document.getElementById('totalTrades').textContent = data.total_trades || '0';
            document.getElementById('totalProfit').textContent = '€' + (data.total_profit || '0');
            document.getElementById('winRate').textContent = (data.win_rate || '0') + '%';
            document.getElementById('systemStatus').innerHTML = 
                '<span class="status-indicator ' + (data.system_active ? 'status-active' : 'status-inactive') + '"></span>' +
                (data.system_active ? 'ATTIVO' : 'INATTIVO');
        }
        
        function updateSystemsData(data) {
            let html = '<table class="data-table"><tr><th>Sistema</th><th>Trade</th><th>Profitto</th><th>Win Rate</th><th>Status</th></tr>';
            
            if (data.systems) {
                data.systems.forEach(system => {
                    html += `<tr>
                        <td>${system.name}</td>
                        <td>${system.trades}</td>
                        <td class="${system.profit >= 0 ? 'profit-positive' : 'profit-negative'}">€${system.profit}</td>
                        <td>${system.win_rate}%</td>
                        <td><span class="status-indicator ${system.active ? 'status-active' : 'status-inactive'}"></span>${system.active ? 'ON' : 'OFF'}</td>
                    </tr>`;
                });
            }
            
            html += '</table>';
            document.getElementById('systemsData').innerHTML = html;
        }
        
        function updateRecentTrades(data) {
            let html = '<table class="data-table"><tr><th>Timestamp</th><th>Azione</th><th>Importo</th><th>P&L</th></tr>';
            
            if (data.recent_trades) {
                data.recent_trades.forEach(trade => {
                    html += `<tr>
                        <td>${new Date(trade.timestamp).toLocaleString()}</td>
                        <td>${trade.action}</td>
                        <td>€${trade.amount}</td>
                        <td class="${trade.profit_loss >= 0 ? 'profit-positive' : 'profit-negative'}">€${trade.profit_loss}</td>
                    </tr>`;
                });
            }
            
            html += '</table>';
            document.getElementById('recentTrades').innerHTML = html;
        }
        
        // Auto-refresh ogni 30 secondi
        setInterval(() => {
            if (authenticated) refreshData();
        }, 30000);
        
        // Caricamento iniziale
        window.onload = function() {
            // Per demo, mostra direttamente dashboard
            authenticated = true;
            refreshData();
        };
    </script>
</body>
</html>
        """

        admin_username = os.getenv("AURUMBOTX_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("AURUMBOTX_ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD") or ""
        html_content = (
            html_content.replace("__ADMIN_USERNAME__", admin_username)
            .replace("__ADMIN_PASSWORD__", admin_password)
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_trading_data(self):
        """Serve dati trading"""
        try:
            # Carica dati da database
            data = self.load_trading_data()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        
        except Exception as e:
            self.send_error(500, str(e))
    
    def load_trading_data(self):
        """Carica dati trading da database"""
        data = {
            'total_trades': 0,
            'total_profit': 0,
            'win_rate': 0,
            'system_active': False,
            'systems': [],
            'recent_trades': []
        }
        
        # Database disponibili
        databases = [
            ('mega_aggressive_trading.db', 'mega_trades', 'Mega Aggressive'),
            ('ultra_aggressive_trading.db', 'ultra_trades', 'Ultra Aggressive'),
            ('mainnet_250_euro.db', 'mainnet_trades', 'Mainnet €250')
        ]
        
        total_trades = 0
        total_profit = 0
        winning_trades = 0
        all_recent_trades = []
        
        for db_file, table_name, system_name in databases:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    # Stats sistema
                    cursor.execute(f"""
                        SELECT COUNT(*), SUM(profit_loss), 
                               COUNT(CASE WHEN profit_loss > 0 THEN 1 END)
                        FROM {table_name}
                    """)
                    
                    result = cursor.fetchone()
                    if result and result[0] > 0:
                        sys_trades = result[0]
                        sys_profit = result[1] or 0
                        sys_wins = result[2] or 0
                        sys_win_rate = (sys_wins / sys_trades * 100) if sys_trades > 0 else 0
                        
                        data['systems'].append({
                            'name': system_name,
                            'trades': sys_trades,
                            'profit': round(sys_profit, 2),
                            'win_rate': round(sys_win_rate, 1),
                            'active': False  # Aggiornare con status reale
                        })
                        
                        total_trades += sys_trades
                        total_profit += sys_profit
                        winning_trades += sys_wins
                    
                    # Recent trades
                    cursor.execute(f"""
                        SELECT timestamp, action, amount, profit_loss
                        FROM {table_name}
                        ORDER BY id DESC
                        LIMIT 5
                    """)
                    
                    for row in cursor.fetchall():
                        all_recent_trades.append({
                            'timestamp': row[0],
                            'action': row[1],
                            'amount': round(row[2], 2),
                            'profit_loss': round(row[3], 2)
                        })
                    
                    conn.close()
                
                except Exception as e:
                    print(f"Errore database {system_name}: {e}")
        
        # Aggiorna totali
        data['total_trades'] = total_trades
        data['total_profit'] = round(total_profit, 2)
        data['win_rate'] = round((winning_trades / total_trades * 100) if total_trades > 0 else 0, 1)
        data['recent_trades'] = sorted(all_recent_trades, key=lambda x: x['timestamp'], reverse=True)[:10]
        
        return data
    
    def handle_bot_action(self):
        """Gestisce azioni bot"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            action = data.get('action')
            
            if action == 'start':
                # Avvia bot (implementare logica reale)
                result = {'status': 'success', 'message': 'Bot avviato'}
            elif action == 'stop':
                # Ferma bot (implementare logica reale)
                result = {'status': 'success', 'message': 'Bot fermato'}
            elif action == 'restart':
                # Riavvia bot (implementare logica reale)
                result = {'status': 'success', 'message': 'Bot riavviato'}
            else:
                result = {'status': 'error', 'message': 'Azione non valida'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        
        except Exception as e:
            self.send_error(500, str(e))

def start_server(port=8080):
    """Avvia server standalone"""
    try:
        with socketserver.TCPServer(("", port), AurumBotXHandler) as httpd:
            print(f"🌐 AurumBotX Server avviato su porta {port}")
            print(f"📊 Dashboard: http://localhost:{port}")
            print("🔐 Login: admin (password impostata via AURUMBOTX_ADMIN_PASSWORD o ADMIN_PASSWORD)")
            print("🛑 Ctrl+C per fermare")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server fermato")
    except Exception as e:
        print(f"❌ Errore server: {e}")

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_server(port)
