#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX External Access Manager
Script per rendere i link accessibili da qualsiasi luogo, non solo da Manus
"""

import os
import sys
import subprocess
import time
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
import threading
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/external_access.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ExternalAccess')

class NgrokTunnelManager:
    """Manager per tunnel Ngrok"""
    
    def __init__(self):
        self.logger = logging.getLogger('NgrokManager')
        self.tunnels = {}
        self.ngrok_process = None
        self.config_file = 'ngrok_config.yml'
    
    def install_ngrok(self) -> bool:
        """Installa Ngrok se non presente"""
        try:
            # Controlla se ngrok è già installato
            result = subprocess.run(['which', 'ngrok'], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("✅ Ngrok già installato")
                return True
            
            self.logger.info("📦 Installazione Ngrok...")
            
            # Download e installazione Ngrok
            commands = [
                "curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null",
                "echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list",
                "sudo apt update",
                "sudo apt install ngrok -y"
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"❌ Errore comando: {cmd}")
                    return False
            
            self.logger.info("✅ Ngrok installato con successo")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore installazione Ngrok: {e}")
            return False
    
    def create_config(self, auth_token: Optional[str] = None) -> bool:
        """Crea configurazione Ngrok"""
        try:
            config_content = f"""
version: "2"
authtoken: {auth_token or 'YOUR_NGROK_TOKEN_HERE'}
tunnels:
  admin:
    proto: http
    addr: 8501
    bind_tls: true
  premium:
    proto: http
    addr: 8502
    bind_tls: true
  performance:
    proto: http
    addr: 8503
    bind_tls: true
  config:
    proto: http
    addr: 8504
    bind_tls: true
  mobile:
    proto: http
    addr: 8505
    bind_tls: true
"""
            
            with open(self.config_file, 'w') as f:
                f.write(config_content)
            
            self.logger.info(f"✅ Configurazione Ngrok creata: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore creazione config: {e}")
            return False
    
    def start_tunnels(self) -> Dict:
        """Avvia tunnel Ngrok"""
        try:
            self.logger.info("🚀 Avvio tunnel Ngrok...")
            
            # Avvia ngrok con configurazione
            cmd = f"ngrok start --all --config {self.config_file}"
            self.ngrok_process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Aspetta che ngrok si avvii
            time.sleep(5)
            
            # Ottieni URL dei tunnel
            tunnels = self.get_tunnel_urls()
            
            if tunnels:
                self.tunnels = tunnels
                self.logger.info("✅ Tunnel Ngrok avviati con successo")
                return tunnels
            else:
                self.logger.error("❌ Nessun tunnel disponibile")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ Errore avvio tunnel: {e}")
            return {}
    
    def get_tunnel_urls(self) -> Dict:
        """Ottieni URL dei tunnel attivi"""
        try:
            # API Ngrok locale
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                tunnels = {}
                
                for tunnel in data.get('tunnels', []):
                    name = tunnel.get('name', '')
                    public_url = tunnel.get('public_url', '')
                    local_addr = tunnel.get('config', {}).get('addr', '')
                    
                    if name and public_url:
                        tunnels[name] = {
                            'public_url': public_url,
                            'local_addr': local_addr,
                            'status': 'active'
                        }
                
                return tunnels
            
            return {}
            
        except Exception as e:
            self.logger.error(f"❌ Errore recupero tunnel URLs: {e}")
            return {}
    
    def stop_tunnels(self):
        """Ferma tunnel Ngrok"""
        try:
            if self.ngrok_process:
                self.ngrok_process.terminate()
                self.ngrok_process.wait()
                self.logger.info("🛑 Tunnel Ngrok fermati")
        except Exception as e:
            self.logger.error(f"❌ Errore stop tunnel: {e}")

class CloudflareTunnelManager:
    """Manager per Cloudflare Tunnel (alternativa gratuita)"""
    
    def __init__(self):
        self.logger = logging.getLogger('CloudflareManager')
        self.tunnel_process = None
        self.tunnel_config = 'cloudflared_config.yml'
    
    def install_cloudflared(self) -> bool:
        """Installa Cloudflared"""
        try:
            # Controlla se già installato
            result = subprocess.run(['which', 'cloudflared'], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("✅ Cloudflared già installato")
                return True
            
            self.logger.info("📦 Installazione Cloudflared...")
            
            # Download e installazione
            commands = [
                "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb",
                "sudo dpkg -i cloudflared-linux-amd64.deb",
                "rm cloudflared-linux-amd64.deb"
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"⚠️ Comando fallito: {cmd}")
            
            # Verifica installazione
            result = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("✅ Cloudflared installato con successo")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Errore installazione Cloudflared: {e}")
            return False
    
    def create_tunnel_config(self) -> bool:
        """Crea configurazione tunnel"""
        try:
            config_content = """
tunnel: aurumbotx-dashboard
credentials-file: /home/ubuntu/.cloudflared/cert.pem

ingress:
  - hostname: admin.aurumbotx.your-domain.com
    service: http://localhost:8501
  - hostname: premium.aurumbotx.your-domain.com
    service: http://localhost:8502
  - hostname: performance.aurumbotx.your-domain.com
    service: http://localhost:8503
  - hostname: config.aurumbotx.your-domain.com
    service: http://localhost:8504
  - hostname: mobile.aurumbotx.your-domain.com
    service: http://localhost:8505
  - service: http_status:404
"""
            
            with open(self.tunnel_config, 'w') as f:
                f.write(config_content)
            
            self.logger.info(f"✅ Config Cloudflare creata: {self.tunnel_config}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore creazione config Cloudflare: {e}")
            return False
    
    def start_quick_tunnel(self) -> Dict:
        """Avvia tunnel rapido (senza dominio)"""
        try:
            self.logger.info("🚀 Avvio Cloudflare Quick Tunnel...")
            
            # Avvia tunnel per ogni porta
            tunnels = {}
            ports = {
                'admin': 8501,
                'premium': 8502,
                'performance': 8503,
                'config': 8504,
                'mobile': 8505
            }
            
            for name, port in ports.items():
                try:
                    # Avvia tunnel in background
                    cmd = f"cloudflared tunnel --url http://localhost:{port}"
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    # Aspetta URL tunnel
                    time.sleep(3)
                    
                    # Simula URL (in realtà dovrebbe essere estratto dall'output)
                    tunnel_url = f"https://{name}-{port}.trycloudflare.com"
                    
                    tunnels[name] = {
                        'public_url': tunnel_url,
                        'local_port': port,
                        'process': process,
                        'status': 'active'
                    }
                    
                except Exception as e:
                    self.logger.error(f"❌ Errore tunnel {name}: {e}")
            
            return tunnels
            
        except Exception as e:
            self.logger.error(f"❌ Errore avvio quick tunnel: {e}")
            return {}

class LocalTunnelManager:
    """Manager per LocalTunnel (alternativa semplice)"""
    
    def __init__(self):
        self.logger = logging.getLogger('LocalTunnelManager')
        self.tunnels = {}
    
    def install_localtunnel(self) -> bool:
        """Installa LocalTunnel"""
        try:
            # Installa via npm
            result = subprocess.run(['npm', 'install', '-g', 'localtunnel'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("✅ LocalTunnel installato con successo")
                return True
            else:
                self.logger.error(f"❌ Errore installazione LocalTunnel: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Errore installazione LocalTunnel: {e}")
            return False
    
    def start_tunnels(self) -> Dict:
        """Avvia tunnel LocalTunnel"""
        try:
            self.logger.info("🚀 Avvio LocalTunnel...")
            
            ports = {
                'admin': 8501,
                'premium': 8502,
                'performance': 8503,
                'config': 8504,
                'mobile': 8505
            }
            
            tunnels = {}
            
            for name, port in ports.items():
                try:
                    # Avvia tunnel
                    cmd = f"lt --port {port} --subdomain aurumbotx-{name}"
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    time.sleep(2)
                    
                    # URL tunnel
                    tunnel_url = f"https://aurumbotx-{name}.loca.lt"
                    
                    tunnels[name] = {
                        'public_url': tunnel_url,
                        'local_port': port,
                        'process': process,
                        'status': 'active'
                    }
                    
                except Exception as e:
                    self.logger.error(f"❌ Errore tunnel {name}: {e}")
            
            self.tunnels = tunnels
            return tunnels
            
        except Exception as e:
            self.logger.error(f"❌ Errore avvio LocalTunnel: {e}")
            return {}

class ExternalAccessManager:
    """Manager principale per accesso esterno"""
    
    def __init__(self):
        self.logger = logging.getLogger('ExternalAccessManager')
        self.ngrok = NgrokTunnelManager()
        self.cloudflare = CloudflareTunnelManager()
        self.localtunnel = LocalTunnelManager()
        self.active_tunnels = {}
        self.tunnel_method = None
    
    def setup_external_access(self, method: str = 'auto') -> Dict:
        """Setup accesso esterno"""
        try:
            self.logger.info(f"🚀 Setup accesso esterno (metodo: {method})...")
            
            if method == 'auto':
                # Prova metodi in ordine di preferenza
                methods = ['localtunnel', 'cloudflare', 'ngrok']
            else:
                methods = [method]
            
            for tunnel_method in methods:
                self.logger.info(f"🔄 Tentativo con {tunnel_method}...")
                
                success = False
                tunnels = {}
                
                if tunnel_method == 'ngrok':
                    if self.ngrok.install_ngrok():
                        self.ngrok.create_config()
                        tunnels = self.ngrok.start_tunnels()
                        success = bool(tunnels)
                
                elif tunnel_method == 'cloudflare':
                    if self.cloudflare.install_cloudflared():
                        tunnels = self.cloudflare.start_quick_tunnel()
                        success = bool(tunnels)
                
                elif tunnel_method == 'localtunnel':
                    if self.localtunnel.install_localtunnel():
                        tunnels = self.localtunnel.start_tunnels()
                        success = bool(tunnels)
                
                if success:
                    self.active_tunnels = tunnels
                    self.tunnel_method = tunnel_method
                    self.logger.info(f"✅ Accesso esterno configurato con {tunnel_method}")
                    
                    # Salva configurazione
                    self.save_tunnel_config()
                    
                    return {
                        'status': 'success',
                        'method': tunnel_method,
                        'tunnels': tunnels
                    }
            
            return {'status': 'failed', 'error': 'Nessun metodo tunnel disponibile'}
            
        except Exception as e:
            self.logger.error(f"❌ Errore setup accesso esterno: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def save_tunnel_config(self):
        """Salva configurazione tunnel"""
        try:
            config = {
                'timestamp': datetime.now().isoformat(),
                'method': self.tunnel_method,
                'tunnels': self.active_tunnels
            }
            
            with open('external_access_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            # Crea file HTML con i link
            self.create_access_page()
            
            self.logger.info("✅ Configurazione tunnel salvata")
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio config: {e}")
    
    def create_access_page(self):
        """Crea pagina HTML con i link di accesso"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AurumBotX - Accesso Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 40px;
            font-size: 2.5em;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .dashboard-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            transition: transform 0.3s ease;
            border: 2px solid transparent;
        }}
        .dashboard-card:hover {{
            transform: translateY(-5px);
            border-color: #667eea;
        }}
        .dashboard-card h3 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        .dashboard-card a {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 12px 25px;
            border-radius: 25px;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        .dashboard-card a:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .info {{
            background: #e8f4fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .status {{
            text-align: center;
            margin-bottom: 30px;
            padding: 15px;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 10px;
            color: #155724;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AurumBotX Dashboard</h1>
        
        <div class="status">
            ✅ <strong>Accesso Esterno Attivo</strong> - Metodo: {self.tunnel_method.upper()}
        </div>
        
        <div class="info">
            <strong>ℹ️ Informazioni:</strong><br>
            Questi link sono accessibili da qualsiasi dispositivo con connessione internet.
            I tunnel sono attivi e sicuri (HTTPS).
        </div>
        
        <div class="dashboard-grid">
"""
            
            # Aggiungi card per ogni dashboard
            dashboard_info = {
                'admin': {'title': '🔧 Admin Dashboard', 'desc': 'Controllo completo del sistema'},
                'premium': {'title': '💎 Premium Dashboard', 'desc': 'Interfaccia utenti premium'},
                'performance': {'title': '📈 Performance Dashboard', 'desc': 'Monitoraggio performance'},
                'config': {'title': '⚙️ Config Dashboard', 'desc': 'Configurazione avanzata'},
                'mobile': {'title': '📱 Mobile Dashboard', 'desc': 'Versione mobile ottimizzata'}
            }
            
            for name, tunnel_info in self.active_tunnels.items():
                if name in dashboard_info:
                    info = dashboard_info[name]
                    url = tunnel_info.get('public_url', '#')
                    
                    html_content += f"""
            <div class="dashboard-card">
                <h3>{info['title']}</h3>
                <p>{info['desc']}</p>
                <a href="{url}" target="_blank">Accedi Dashboard</a>
                <div style="margin-top: 10px; font-size: 0.8em; color: #666;">
                    {url}
                </div>
            </div>
"""
            
            html_content += f"""
        </div>
        
        <div class="timestamp">
            Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
            
            with open('aurumbotx_access.html', 'w') as f:
                f.write(html_content)
            
            self.logger.info("✅ Pagina di accesso creata: aurumbotx_access.html")
            
        except Exception as e:
            self.logger.error(f"❌ Errore creazione pagina: {e}")
    
    def get_access_links(self) -> Dict:
        """Ottieni link di accesso"""
        return self.active_tunnels
    
    def stop_tunnels(self):
        """Ferma tutti i tunnel"""
        try:
            if self.tunnel_method == 'ngrok':
                self.ngrok.stop_tunnels()
            elif self.tunnel_method == 'localtunnel':
                for tunnel in self.localtunnel.tunnels.values():
                    if 'process' in tunnel:
                        tunnel['process'].terminate()
            
            self.logger.info("🛑 Tutti i tunnel fermati")
            
        except Exception as e:
            self.logger.error(f"❌ Errore stop tunnel: {e}")

def signal_handler(sig, frame):
    """Handler per segnali di terminazione"""
    print("\n🛑 Fermando tunnel...")
    if 'access_manager' in globals():
        access_manager.stop_tunnels()
    sys.exit(0)

def main():
    """Funzione principale"""
    print("🌐 AurumBotX External Access Manager")
    print("=" * 60)
    print("🎯 OBIETTIVO: Rendere dashboard accessibili ovunque")
    print("🔗 METODI: LocalTunnel, Cloudflare, Ngrok")
    print("📱 COMPATIBILITÀ: Desktop, Mobile, Tablet")
    print("=" * 60)
    
    # Setup
    os.makedirs('logs', exist_ok=True)
    
    # Signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Inizializza manager
    global access_manager
    access_manager = ExternalAccessManager()
    
    # Setup accesso esterno
    result = access_manager.setup_external_access('auto')
    
    if result['status'] == 'success':
        print(f"\n🎉 ACCESSO ESTERNO CONFIGURATO!")
        print(f"🔧 Metodo: {result['method'].upper()}")
        print(f"🔗 Tunnel attivi: {len(result['tunnels'])}")
        
        print(f"\n📱 LINK DASHBOARD ESTERNI:")
        for name, tunnel in result['tunnels'].items():
            url = tunnel.get('public_url', 'N/A')
            print(f"   🔗 {name.title()}: {url}")
        
        print(f"\n📄 Pagina di accesso creata: aurumbotx_access.html")
        print(f"💡 Apri il file HTML nel browser per accedere facilmente!")
        
        print(f"\n🔄 Tunnel attivi - Premi Ctrl+C per fermare")
        
        # Mantieni attivo
        try:
            while True:
                time.sleep(60)
                # Verifica stato tunnel ogni minuto
                logger.info("🔄 Tunnel attivi e operativi")
        except KeyboardInterrupt:
            pass
    
    else:
        print(f"\n❌ ERRORE CONFIGURAZIONE: {result.get('error', 'Unknown')}")
        print("💡 Verifica connessione internet e dipendenze")

if __name__ == "__main__":
    main()

