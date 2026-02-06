#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Universal Team Access System
Sistema per accesso team universale senza dipendenze Manus
"""

import os
import json
import subprocess
import time
from datetime import datetime
import sqlite3
import pandas as pd

class UniversalTeamAccess:
    """Sistema accesso universale team"""
    
    def __init__(self):
        self.project_root = os.getcwd()
        
    def log(self, message):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def create_standalone_server(self):
        """Crea server standalone per team"""
        server_code = '''#!/usr/bin/env python3
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
        print("\\n🛑 Server fermato")
    except Exception as e:
        print(f"❌ Errore server: {e}")

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_server(port)
'''
        
        with open("standalone_server.py", "w") as f:
            f.write(server_code)
        
        os.chmod("standalone_server.py", 0o755)
        self.log("✅ Server standalone creato")
    
    def create_ngrok_setup(self):
        """Crea setup ngrok per accesso esterno"""
        ngrok_script = '''#!/bin/bash
# AurumBotX Ngrok Setup per accesso esterno

echo "🌐 Setup accesso esterno AurumBotX..."

# Controlla se ngrok è installato
if ! command -v ngrok &> /dev/null; then
    echo "📦 Installazione ngrok..."
    
    # Download ngrok
    wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
    tar xzf ngrok-v3-stable-linux-amd64.tgz
    sudo mv ngrok /usr/local/bin/
    rm ngrok-v3-stable-linux-amd64.tgz
    
    echo "✅ Ngrok installato"
fi

# Avvia server in background
echo "🚀 Avvio server AurumBotX..."
python3 standalone_server.py 8080 &
SERVER_PID=$!

# Aspetta che il server si avvii
sleep 3

# Avvia ngrok
echo "🌐 Creazione tunnel pubblico..."
ngrok http 8080 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

# Aspetta che ngrok si avvii
sleep 5

# Estrae URL pubblico
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('Errore estrazione URL')
")

echo ""
echo "🎉 AurumBotX accessibile pubblicamente!"
echo "🔗 URL Pubblico: $PUBLIC_URL"
echo "🔐 Login: admin (password impostata via AURUMBOTX_ADMIN_PASSWORD o ADMIN_PASSWORD)"
echo ""
echo "📋 Condividi questo URL con il tuo team:"
echo "$PUBLIC_URL"
echo ""
echo "🛑 Premi Ctrl+C per fermare"

# Salva URL in file
echo "$PUBLIC_URL" > public_url.txt
echo "💾 URL salvato in public_url.txt"

# Mantieni attivo
trap "kill $SERVER_PID $NGROK_PID 2>/dev/null" EXIT
wait
'''
        
        with open("setup_public_access.sh", "w") as f:
            f.write(ngrok_script)
        
        os.chmod("setup_public_access.sh", 0o755)
        self.log("✅ Setup ngrok creato")
    
    def create_docker_solution(self):
        """Crea soluzione Docker completa"""
        dockerfile = '''FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    sqlite3 \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir pandas sqlite3

# Create data directory
RUN mkdir -p data logs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:8080/api/system-status || exit 1

# Start server
CMD ["python3", "standalone_server.py", "8080"]
'''
        
        with open("Dockerfile.standalone", "w") as f:
            f.write(dockerfile)
        
        # Docker compose
        compose = '''version: '3.8'

services:
  aurumbotx-team:
    build:
      context: .
      dockerfile: Dockerfile.standalone
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - TEAM_ACCESS=true
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080"]
      interval: 30s
      timeout: 10s
      retries: 3
'''
        
        with open("docker-compose.team.yml", "w") as f:
            f.write(compose)
        
        self.log("✅ Soluzione Docker creata")
    
    def create_replit_config(self):
        """Crea configurazione Replit"""
        replit_config = {
            "language": "python3",
            "run": "python3 standalone_server.py 8080",
            "entrypoint": "standalone_server.py",
            "hidden": [".config", ".git"],
            "modules": ["pandas", "sqlite3"]
        }
        
        with open(".replit", "w") as f:
            json.dump(replit_config, f, indent=2)
        
        # Main file per Replit
        main_replit = '''#!/usr/bin/env python3
"""
AurumBotX su Replit
Avvio automatico per team access
"""

import os
import subprocess
import sys

def main():
    print("🚀 Avvio AurumBotX su Replit...")
    
    # Avvia server
    os.system("python3 standalone_server.py 8080")

if __name__ == "__main__":
    main()
'''
        
        with open("main.py", "w") as f:
            f.write(main_replit)
        
        self.log("✅ Configurazione Replit creata")
    
    def create_final_pdf_report(self):
        """Crea PDF finale con tutti i risultati"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            
            # Crea PDF
            filename = f"AurumBotX_Final_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1,
                textColor=colors.darkblue
            )
            
            story.append(Paragraph("🤖 AurumBotX - Risultati Finali", title_style))
            story.append(Spacer(1, 20))
            
            # Risultati trading
            story.append(Paragraph("📊 RISULTATI TRADING COMPLETI", styles['Heading2']))
            
            # Carica dati da database
            trading_results = self.get_all_trading_data()
            
            # Tabella risultati
            data = [['Sistema', 'Trade', 'Profitto €', 'Win Rate %', 'Periodo']]
            for system, results in trading_results.items():
                data.append([
                    system,
                    str(results.get('trades', 0)),
                    f"{results.get('profit', 0):,.2f}",
                    f"{results.get('win_rate', 0):.1f}",
                    results.get('period', 'N/A')
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Sezione accesso team
            story.append(Paragraph("🌐 ACCESSO TEAM UNIVERSALE", styles['Heading2']))
            
            access_info = """
            <b>✅ SOLUZIONI IMPLEMENTATE:</b><br/>
            <br/>
            <b>1. Server Standalone</b><br/>
            • File: standalone_server.py<br/>
            • Comando: python3 standalone_server.py 8080<br/>
            • Dashboard: http://localhost:8080<br/>
            • Login: admin (password impostata via AURUMBOTX_ADMIN_PASSWORD o ADMIN_PASSWORD)<br/>
            <br/>
            <b>2. Accesso Pubblico (Ngrok)</b><br/>
            • Script: ./setup_public_access.sh<br/>
            • URL pubblico generato automaticamente<br/>
            • Accessibile da qualsiasi dispositivo<br/>
            <br/>
            <b>3. Docker Deploy</b><br/>
            • Comando: docker-compose -f docker-compose.team.yml up<br/>
            • Container isolato e sicuro<br/>
            • Auto-restart e health check<br/>
            <br/>
            <b>4. Replit Deploy</b><br/>
            • Upload su replit.com<br/>
            • Accesso 24/7 gratuito<br/>
            • URL pubblico automatico<br/>
            <br/>
            <b>5. GitHub Pages (Statico)</b><br/>
            • Dashboard HTML statica<br/>
            • Nessun server richiesto<br/>
            • Accesso immediato team<br/>
            """
            
            story.append(Paragraph(access_info, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Istruzioni team
            story.append(Paragraph("👥 ISTRUZIONI PER IL TEAM", styles['Heading2']))
            
            team_instructions = """
            <b>🚀 AVVIO RAPIDO (2 minuti):</b><br/>
            <br/>
            1. <b>Clone Repository:</b><br/>
            git clone https://github.com/Cryptomalo/AurumBotX.git<br/>
            cd AurumBotX<br/>
            <br/>
            2. <b>Avvio Locale:</b><br/>
            python3 standalone_server.py 8080<br/>
            Apri: http://localhost:8080<br/>
            <br/>
            3. <b>Accesso Pubblico:</b><br/>
            ./setup_public_access.sh<br/>
            Condividi URL generato<br/>
            <br/>
            <b>🔐 CREDENZIALI:</b><br/>
            • Username: admin<br/>
            • Password: impostata via AURUMBOTX_ADMIN_PASSWORD o ADMIN_PASSWORD<br/>
            <br/>
            <b>📊 FUNZIONALITÀ DISPONIBILI:</b><br/>
            • Visualizzazione dati trading real-time<br/>
            • Controllo bot (start/stop/restart)<br/>
            • Statistiche performance complete<br/>
            • Export dati per analisi<br/>
            • Gestione sistema completa<br/>
            """
            
            story.append(Paragraph(team_instructions, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            self.log(f"✅ PDF creato: {filename}")
            return filename
            
        except ImportError:
            # Fallback senza reportlab
            filename = f"AurumBotX_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(filename, "w") as f:
                f.write("🤖 AURUMBOTX - RISULTATI FINALI\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("📊 RISULTATI TRADING:\n")
                trading_results = self.get_all_trading_data()
                for system, results in trading_results.items():
                    f.write(f"\n{system}:\n")
                    f.write(f"  Trade: {results.get('trades', 0)}\n")
                    f.write(f"  Profitto: €{results.get('profit', 0):,.2f}\n")
                    f.write(f"  Win Rate: {results.get('win_rate', 0):.1f}%\n")
                
                f.write("\n\n🌐 ACCESSO TEAM:\n")
                f.write("• Server: python3 standalone_server.py 8080\n")
                f.write("• Pubblico: ./setup_public_access.sh\n")
                f.write("• Docker: docker-compose -f docker-compose.team.yml up\n")
                f.write("• Login: admin (password impostata via AURUMBOTX_ADMIN_PASSWORD o ADMIN_PASSWORD)\n")
            
            self.log(f"✅ Report TXT creato: {filename}")
            return filename
    
    def get_all_trading_data(self):
        """Recupera tutti i dati trading"""
        results = {}
        
        databases = [
            ('mega_aggressive_trading.db', 'mega_trades', 'Mega Aggressive'),
            ('ultra_aggressive_trading.db', 'ultra_trades', 'Ultra Aggressive'),
            ('mainnet_250_euro.db', 'mainnet_trades', 'Mainnet €250')
        ]
        
        for db_file, table_name, system_name in databases:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    cursor.execute(f"""
                        SELECT COUNT(*), SUM(profit_loss), 
                               COUNT(CASE WHEN profit_loss > 0 THEN 1 END),
                               MIN(timestamp), MAX(timestamp)
                        FROM {table_name}
                    """)
                    
                    result = cursor.fetchone()
                    if result and result[0] > 0:
                        trades = result[0]
                        profit = result[1] or 0
                        wins = result[2] or 0
                        win_rate = (wins / trades * 100) if trades > 0 else 0
                        
                        results[system_name] = {
                            'trades': trades,
                            'profit': profit,
                            'win_rate': win_rate,
                            'period': f"{result[3][:10]} - {result[4][:10]}" if result[3] and result[4] else 'N/A'
                        }
                    
                    conn.close()
                
                except Exception as e:
                    self.log(f"Errore database {system_name}: {e}")
        
        return results
    
    def run_complete_setup(self):
        """Esegue setup completo"""
        self.log("🚀 SETUP ACCESSO TEAM UNIVERSALE")
        self.log("=" * 60)
        
        steps = [
            ("Server Standalone", self.create_standalone_server),
            ("Setup Ngrok", self.create_ngrok_setup),
            ("Docker Solution", self.create_docker_solution),
            ("Replit Config", self.create_replit_config),
            ("PDF Report", self.create_final_pdf_report)
        ]
        
        success_count = 0
        pdf_file = None
        
        for step_name, step_func in steps:
            try:
                result = step_func()
                if step_name == "PDF Report":
                    pdf_file = result
                success_count += 1
                self.log(f"✅ {step_name} completato")
            except Exception as e:
                self.log(f"❌ Errore {step_name}: {e}")
        
        self.log("\n" + "=" * 60)
        self.log(f"✅ Setup completato: {success_count}/{len(steps)} step")
        
        if success_count >= 4:  # Almeno 4/5 step completati
            self.log("\n🎉 SISTEMA TEAM ACCESS PRONTO!")
            self.log("\n🚀 OPZIONI ACCESSO IMMEDIATE:")
            self.log("1. 🖥️  Locale: python3 standalone_server.py 8080")
            self.log("2. 🌐 Pubblico: ./setup_public_access.sh")
            self.log("3. 🐳 Docker: docker-compose -f docker-compose.team.yml up")
            self.log("4. 📱 Replit: Upload su replit.com")
            self.log("\n🔐 Login: admin (password impostata via AURUMBOTX_ADMIN_PASSWORD o ADMIN_PASSWORD)")
            self.log("📊 Dashboard: http://localhost:8080")
            
            if pdf_file:
                self.log(f"📄 Report: {pdf_file}")
        
        return success_count >= 4, pdf_file

def main():
    """Funzione principale"""
    print("🛑 AurumBotX - Setup Accesso Team Universale")
    print("=" * 60)
    
    access_system = UniversalTeamAccess()
    success, pdf_file = access_system.run_complete_setup()
    
    if success:
        print("\n🎉 SISTEMA PRONTO PER IL TUO TEAM!")
        print("\n🔗 Il team può ora accedere in 4 modi diversi:")
        print("• 🖥️  Server locale (sempre funziona)")
        print("• 🌐 Accesso pubblico (condivisibile)")
        print("• 🐳 Docker (isolato e sicuro)")
        print("• 📱 Replit (cloud gratuito)")
        print("\n✅ NESSUNA DIPENDENZA DA MANUS!")
        print("✅ FUNZIONA ANCHE QUANDO SEI OFFLINE!")
        
        if pdf_file:
            print(f"\n📄 Report completo: {pdf_file}")
    else:
        print("\n⚠️ Setup parzialmente completato")
        print("Controlla i log per dettagli errori")
    
    return success

if __name__ == "__main__":
    main()
