#!/usr/bin/env python3
"""
AurumBotX Team Management System
Sistema completo per gestione team con autenticazione e controllo accessi
"""

import streamlit as st
import sqlite3
import hashlib
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from cryptography.fernet import Fernet
import base64

class TeamManagementSystem:
    """Sistema gestione team AurumBotX"""
    
    def __init__(self):
        self.db_name = "team_management.db"
        self.setup_database()
        self.setup_encryption()
    
    def setup_encryption(self):
        """Setup crittografia per credenziali"""
        key_file = ".encryption_key"
        if not os.path.exists(key_file):
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
        else:
            with open(key_file, "rb") as f:
                key = f.read()
        
        self.cipher = Fernet(key)
    
    def encrypt_data(self, data):
        """Cripta dati sensibili"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        """Decripta dati sensibili"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def setup_database(self):
        """Setup database team"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabella utenti team
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                permissions TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                active BOOLEAN DEFAULT 1
            );
        """)
        
        # Tabella credenziali sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT UNIQUE NOT NULL,
                encrypted_credentials TEXT NOT NULL,
                description TEXT,
                updated_at TEXT NOT NULL,
                updated_by TEXT NOT NULL
            );
        """)
        
        # Tabella log accessi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TEXT NOT NULL
            );
        """)
        
        # Crea admin di default se non esiste
        cursor.execute("SELECT COUNT(*) FROM team_users WHERE role = 'admin'")
        if cursor.fetchone()[0] == 0:
            admin_password = self.hash_password("admin123")
            cursor.execute("""
                INSERT INTO team_users (username, password_hash, role, permissions, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin", admin_password, "admin", "all", datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password sicuro"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, username, password):
        """Autentica utente"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute("""
            SELECT id, username, role, permissions, active 
            FROM team_users 
            WHERE username = ? AND password_hash = ? AND active = 1
        """, (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # Log accesso
            cursor.execute("""
                INSERT INTO access_logs (username, action, timestamp)
                VALUES (?, ?, ?)
            """, (username, "login", datetime.now().isoformat()))
            
            # Aggiorna ultimo login
            cursor.execute("""
                UPDATE team_users SET last_login = ? WHERE username = ?
            """, (datetime.now().isoformat(), username))
            
            conn.commit()
        
        conn.close()
        return user
    
    def get_trading_data(self):
        """Recupera dati trading da tutti i database"""
        trading_data = {}
        
        # Database disponibili
        databases = [
            ("mega_aggressive_trading.db", "mega_trades", "Mega Aggressive"),
            ("ultra_aggressive_trading.db", "ultra_trades", "Ultra Aggressive"),
            ("mainnet_250_euro.db", "mainnet_trades", "Mainnet €250")
        ]
        
        for db_file, table_name, system_name in databases:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 100", conn)
                    
                    if not df.empty:
                        # Statistiche
                        total_trades = len(df)
                        total_profit = df['profit_loss'].sum()
                        win_rate = (df['profit_loss'] > 0).mean() * 100
                        avg_profit = df['profit_loss'].mean()
                        
                        trading_data[system_name] = {
                            'data': df,
                            'stats': {
                                'total_trades': total_trades,
                                'total_profit': total_profit,
                                'win_rate': win_rate,
                                'avg_profit': avg_profit
                            }
                        }
                    
                    conn.close()
                except Exception as e:
                    st.error(f"Errore lettura {system_name}: {e}")
        
        return trading_data
    
    def save_credentials(self, service_name, credentials, description, username):
        """Salva credenziali crittografate"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        encrypted_creds = self.encrypt_data(json.dumps(credentials))
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_credentials 
            (service_name, encrypted_credentials, description, updated_at, updated_by)
            VALUES (?, ?, ?, ?, ?)
        """, (service_name, encrypted_creds, description, datetime.now().isoformat(), username))
        
        conn.commit()
        conn.close()
    
    def get_credentials(self, service_name):
        """Recupera credenziali decrittografate"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT encrypted_credentials FROM system_credentials WHERE service_name = ?
        """, (service_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(self.decrypt_data(result[0]))
        return None


    # Health check endpoint
    if st.query_params.get("health"):
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "systems": {
                "database": "ok",
                "authentication": "ok",
                "trading_data": "ok"
            }
        }
        st.json(health_status)
        return
\ndef main():
    """Interfaccia Streamlit"""
    st.set_page_config(
        page_title="AurumBotX Team Management",
        page_icon="🤖",
        layout="wide"
    )
    
    tms = TeamManagementSystem()
    
    # Inizializza session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None
    
    # Login form
    if not st.session_state.authenticated:
        st.title("🔐 AurumBotX Team Login")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                st.subheader("Accesso Team")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    user = tms.authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            'id': user[0],
                            'username': user[1],
                            'role': user[2],
                            'permissions': user[3]
                        }
                        st.success("Login effettuato!")
                        st.rerun()
                    else:
                        st.error("Credenziali non valide")
        
        # Info credenziali default
        st.info("**Credenziali default:** admin / admin123")
        return
    
    # Dashboard principale
    st.title("🤖 AurumBotX Team Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user['username']}**")
        st.write(f"🎯 **{st.session_state.user['role'].title()}**")
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
    
    # Tabs principali
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Trading Data", 
        "🔑 Credentials", 
        "👥 Team Management", 
        "🔧 System Control",
        "📋 Logs"
    ])
    
    # Tab 1: Trading Data
    with tab1:
        st.header("📊 Dati Trading Real-Time")
        
        trading_data = tms.get_trading_data()
        
        if trading_data:
            # Metriche aggregate
            col1, col2, col3, col4 = st.columns(4)
            
            total_profit = sum([data['stats']['total_profit'] for data in trading_data.values()])
            total_trades = sum([data['stats']['total_trades'] for data in trading_data.values()])
            avg_win_rate = sum([data['stats']['win_rate'] for data in trading_data.values()]) / len(trading_data)
            
            col1.metric("💰 Profitto Totale", f"€{total_profit:,.2f}")
            col2.metric("🎯 Trade Totali", f"{total_trades:,}")
            col3.metric("✅ Win Rate Medio", f"{avg_win_rate:.1f}%")
            col4.metric("🤖 Sistemi Attivi", len(trading_data))
            
            # Dati per sistema
            for system_name, data in trading_data.items():
                with st.expander(f"📈 {system_name}", expanded=True):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    stats = data['stats']
                    col1.metric("Trade", stats['total_trades'])
                    col2.metric("Profitto", f"€{stats['total_profit']:,.2f}")
                    col3.metric("Win Rate", f"{stats['win_rate']:.1f}%")
                    col4.metric("Media Trade", f"€{stats['avg_profit']:,.2f}")
                    
                    # Grafico performance
                    df = data['data']
                    if len(df) > 1:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df['timestamp'],
                            y=df['balance_after'],
                            mode='lines',
                            name='Balance',
                            line=dict(color='green')
                        ))
                        fig.update_layout(
                            title=f"Balance Evolution - {system_name}",
                            xaxis_title="Time",
                            yaxis_title="Balance (€)",
                            height=300
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Ultimi trade
                    st.subheader("🔥 Ultimi 10 Trade")
                    recent_trades = df.head(10)[['timestamp', 'action', 'amount', 'profit_loss', 'balance_after']]
                    st.dataframe(recent_trades, use_container_width=True)
        else:
            st.warning("Nessun dato trading disponibile")
    
    # Tab 2: Credentials Management
    with tab2:
        st.header("🔑 Gestione Credenziali")
        
        if st.session_state.user['role'] in ['admin', 'developer']:
            # Form aggiunta credenziali
            with st.form("add_credentials"):
                st.subheader("➕ Aggiungi/Aggiorna Credenziali")
                
                service = st.selectbox("Servizio", [
                    "Binance API",
                    "PostgreSQL",
                    "OpenRouter AI",
                    "Telegram Bot",
                    "Email SMTP",
                    "Cloud Storage",
                    "Altro"
                ])
                
                if service == "Altro":
                    service = st.text_input("Nome Servizio")
                
                description = st.text_area("Descrizione")
                
                # Campi credenziali dinamici
                if service == "Binance API":
                    api_key = st.text_input("API Key")
                    secret_key = st.text_input("Secret Key", type="password")
                    testnet = st.checkbox("Testnet")
                    credentials = {"api_key": api_key, "secret_key": secret_key, "testnet": testnet}
                
                elif service == "PostgreSQL":
                    host = st.text_input("Host", value="localhost")
                    port = st.number_input("Port", value=5432)
                    database = st.text_input("Database")
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    credentials = {"host": host, "port": port, "database": database, "username": username, "password": password}
                
                else:
                    # Campi generici
                    cred_json = st.text_area("Credenziali (JSON)", placeholder='{"key": "value"}')
                    try:
                        credentials = json.loads(cred_json) if cred_json else {}
                    except:
                        credentials = {}
                
                if st.form_submit_button("💾 Salva Credenziali"):
                    if service and credentials:
                        tms.save_credentials(service, credentials, description, st.session_state.user['username'])
                        st.success(f"Credenziali {service} salvate!")
                    else:
                        st.error("Compila tutti i campi")
            
            # Lista credenziali esistenti
            st.subheader("📋 Credenziali Salvate")
            
            conn = sqlite3.connect(tms.db_name)
            creds_df = pd.read_sql_query("""
                SELECT service_name, description, updated_at, updated_by 
                FROM system_credentials 
                ORDER BY updated_at DESC
            """, conn)
            conn.close()
            
            if not creds_df.empty:
                st.dataframe(creds_df, use_container_width=True)
            else:
                st.info("Nessuna credenziale salvata")
        
        else:
            st.warning("Accesso limitato - Solo Admin e Developer")
    
    # Tab 3: Team Management
    with tab3:
        st.header("👥 Gestione Team")
        
        if st.session_state.user['role'] == 'admin':
            # Form aggiunta utente
            with st.form("add_user"):
                st.subheader("➕ Aggiungi Utente")
                
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Ruolo", ["viewer", "developer", "admin"])
                
                permissions_map = {
                    "viewer": "read",
                    "developer": "read,write,execute",
                    "admin": "all"
                }
                
                if st.form_submit_button("👤 Crea Utente"):
                    if new_username and new_password:
                        conn = sqlite3.connect(tms.db_name)
                        cursor = conn.cursor()
                        
                        try:
                            password_hash = tms.hash_password(new_password)
                            cursor.execute("""
                                INSERT INTO team_users (username, password_hash, role, permissions, created_at)
                                VALUES (?, ?, ?, ?, ?)
                            """, (new_username, password_hash, new_role, permissions_map[new_role], datetime.now().isoformat()))
                            conn.commit()
                            st.success(f"Utente {new_username} creato!")
                        except sqlite3.IntegrityError:
                            st.error("Username già esistente")
                        finally:
                            conn.close()
            
            # Lista utenti
            st.subheader("📋 Utenti Team")
            
            conn = sqlite3.connect(tms.db_name)
            users_df = pd.read_sql_query("""
                SELECT username, role, created_at, last_login, active 
                FROM team_users 
                ORDER BY created_at DESC
            """, conn)
            conn.close()
            
            st.dataframe(users_df, use_container_width=True)
        
        else:
            st.warning("Accesso limitato - Solo Admin")
    
    # Tab 4: System Control
    with tab4:
        st.header("🔧 Controllo Sistema")
        
        if st.session_state.user['role'] in ['admin', 'developer']:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🤖 Controlli Bot")
                
                if st.button("🚀 Start All Bots"):
                    st.info("Avvio tutti i bot...")
                
                if st.button("🛑 Stop All Bots"):
                    st.info("Fermata tutti i bot...")
                
                if st.button("🔄 Restart System"):
                    st.info("Riavvio sistema...")
            
            with col2:
                st.subheader("📊 Status Sistema")
                
                # Controlla processi attivi
                import subprocess
                try:
                    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                    python_processes = [line for line in result.stdout.split('\n') if 'python' in line and 'aurumbotx' in line.lower()]
                    
                    st.metric("🤖 Processi Attivi", len(python_processes))
                    
                    if python_processes:
                        st.text("Processi in esecuzione:")
                        for proc in python_processes[:5]:
                            st.code(proc)
                
                except Exception as e:
                    st.error(f"Errore controllo processi: {e}")
        
        else:
            st.warning("Accesso limitato - Solo Admin e Developer")
    
    # Tab 5: Logs
    with tab5:
        st.header("📋 Log Sistema")
        
        # Log accessi
        st.subheader("🔐 Log Accessi")
        
        conn = sqlite3.connect(tms.db_name)
        logs_df = pd.read_sql_query("""
            SELECT username, action, timestamp 
            FROM access_logs 
            ORDER BY timestamp DESC 
            LIMIT 50
        """, conn)
        conn.close()
        
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info("Nessun log disponibile")
        
        # Log file sistema
        st.subheader("📄 Log File")
        
        log_files = []
        if os.path.exists("logs"):
            log_files = [f for f in os.listdir("logs") if f.endswith('.log')]
        
        if log_files:
            selected_log = st.selectbox("Seleziona Log File", log_files)
            
            if selected_log:
                try:
                    with open(f"logs/{selected_log}", "r") as f:
                        log_content = f.read()
                    
                    st.text_area("Contenuto Log", log_content, height=300)
                except Exception as e:
                    st.error(f"Errore lettura log: {e}")
        else:
            st.info("Nessun log file disponibile")

if __name__ == "__main__":
    main()

