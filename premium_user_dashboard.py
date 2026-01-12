#!/usr/bin/env python3
"""
🌟 AURUMBOTX PREMIUM USER DASHBOARD
Dashboard completa per utenti con login Telegram, pagamenti, wallet, rewards
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import hashlib
import time
import requests
from typing import Dict, Any
import sqlite3

# Configurazione pagina
st.set_page_config(
    page_title="🌟 AurumBotX Premium",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizzato per UI moderna
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    
    .login-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem auto;
        max-width: 500px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
    }
    
    .premium-header {
        background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb, #ff9ff3);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .feature-card {
        background: white;
        border: 1px solid #e1e8ed;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .wallet-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .strategy-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .strategy-card:hover {
        transform: scale(1.02);
    }
    
    .reward-card {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    .premium-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
    }
    
    .premium-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    .status-active { 
        color: #00b894; 
        font-weight: bold;
        background: #d4edda;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
    }
    
    .status-inactive { 
        color: #e17055; 
        font-weight: bold;
        background: #f8d7da;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
    }
    
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 4px solid #667eea;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2d3436;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: #636e72;
        font-weight: 500;
    }
    
    .chat-container {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 1rem;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .chat-message {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .progress-bar {
        background: #e9ecef;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, #667eea, #764ba2);
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    
    .sidebar .sidebar-content {
        background: white;
        border-radius: 15px;
        padding: 1rem;
    }
    
    .notification {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
    
    .warning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    
    .error {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Database setup per utenti
def init_user_database():
    """Inizializza database utenti"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Tabella utenti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            username TEXT,
            email TEXT,
            premium_status BOOLEAN DEFAULT FALSE,
            premium_expires TEXT,
            wallet_address TEXT,
            capital_amount REAL DEFAULT 1000.0,
            selected_strategy TEXT DEFAULT 'swing_trading_6m',
            created_at TEXT,
            last_login TEXT,
            total_profit REAL DEFAULT 0.0,
            total_trades INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0.0
        )
    ''')
    
    # Tabella pagamenti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            currency TEXT,
            payment_method TEXT,
            status TEXT,
            transaction_id TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabella rewards
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            milestone REAL,
            reward_type TEXT,
            claimed BOOLEAN DEFAULT FALSE,
            claimed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Inizializza database
init_user_database()

# Funzioni di utilità
def get_user_by_telegram_id(telegram_id: str) -> Dict[str, Any]:
    """Ottieni utente da Telegram ID"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        columns = ['id', 'telegram_id', 'username', 'email', 'premium_status', 
                  'premium_expires', 'wallet_address', 'capital_amount', 
                  'selected_strategy', 'created_at', 'last_login', 'total_profit', 
                  'total_trades', 'win_rate']
        return dict(zip(columns, user))
    return None

def create_user(telegram_id: str, username: str, email: str = None) -> bool:
    """Crea nuovo utente"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (telegram_id, username, email, created_at, last_login)
            VALUES (?, ?, ?, ?, ?)
        ''', (telegram_id, username, email, datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def update_premium_status(user_id: int, expires_at: str) -> bool:
    """Aggiorna status premium"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET premium_status = TRUE, premium_expires = ?
            WHERE id = ?
        ''', (expires_at, user_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_user_performance(user_id: int) -> Dict[str, Any]:
    """Ottieni performance utente"""
    # Simulato per demo
    return {
        'total_profit': 2847.50,
        'roi_percentage': 184.75,
        'total_trades': 156,
        'win_rate': 73.2,
        'best_trade': 245.80,
        'current_balance': 3847.50,
        'daily_profit': 127.30,
        'weekly_profit': 891.20
    }

def get_rewards_progress(user_id: int) -> Dict[str, Any]:
    """Ottieni progressi rewards"""
    performance = get_user_performance(user_id)
    current_balance = performance['current_balance']
    
    milestones = [10000, 25000, 50000, 100000]
    rewards = {
        10000: "🎁 Premium Features Unlock + 1 Mese Gratis",
        25000: "💎 VIP Status + Strategie Esclusive",
        50000: "🏆 Elite Membership + Personal Manager",
        100000: "👑 Diamond Status + Profit Sharing Bonus"
    }
    
    progress = []
    for milestone in milestones:
        percentage = min((current_balance / milestone) * 100, 100)
        progress.append({
            'milestone': milestone,
            'percentage': percentage,
            'reward': rewards[milestone],
            'achieved': current_balance >= milestone
        })
    
    return progress

# Sistema di autenticazione
def telegram_login_component():
    """Componente login Telegram"""
    st.markdown("""
    <div class="login-container">
        <h1>🌟 Benvenuto in AurumBotX Premium</h1>
        <p style="font-size: 1.2rem; margin: 2rem 0;">
            La piattaforma di trading automatico più avanzata al mondo
        </p>
        <div style="margin: 2rem 0;">
            <h3>🚀 Caratteristiche Premium:</h3>
            <ul style="text-align: left; display: inline-block;">
                <li>🤖 Trading AI avanzato</li>
                <li>💰 Gestione capitale intelligente</li>
                <li>🎯 6+ strategie professionali</li>
                <li>🏆 Sistema rewards esclusivo</li>
                <li>🛡️ Sicurezza massima</li>
                <li>📊 Analytics avanzate</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Accesso Telegram")
        
        # Simulazione login Telegram
        telegram_id = st.text_input("🆔 Telegram ID", placeholder="Inserisci il tuo Telegram ID")
        username = st.text_input("👤 Username", placeholder="Il tuo username Telegram")
        
        if st.button("🚀 Accedi con Telegram", key="telegram_login"):
            if telegram_id and username:
                # Simula autenticazione
                user = get_user_by_telegram_id(telegram_id)
                if not user:
                    if create_user(telegram_id, username):
                        st.success("✅ Account creato con successo!")
                        time.sleep(2)
                        st.session_state.user_id = telegram_id
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ Errore nella creazione dell'account")
                else:
                    st.success("✅ Login effettuato con successo!")
                    time.sleep(1)
                    st.session_state.user_id = telegram_id
                    st.session_state.authenticated = True
                    st.session_state.user_data = user
                    st.rerun()
            else:
                st.error("❌ Inserisci Telegram ID e Username")
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666;">
            <p>🔒 I tuoi dati sono protetti con crittografia end-to-end</p>
            <p>📱 Usa il tuo account Telegram per accedere in sicurezza</p>
        </div>
        """, unsafe_allow_html=True)

def premium_subscription_component():
    """Componente abbonamento premium"""
    st.markdown("""
    <div class="premium-header">
        <h1>💎 Sblocca AurumBotX Premium</h1>
        <p>Accedi a tutte le funzionalità avanzate di trading automatico</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📅 Mensile</h3>
            <div style="font-size: 2rem; font-weight: bold; color: #667eea;">€97</div>
            <p style="color: #666;">per mese</p>
            <ul style="text-align: left;">
                <li>🤖 Trading AI completo</li>
                <li>📊 Tutte le strategie</li>
                <li>💰 Capitale illimitato</li>
                <li>🏆 Sistema rewards</li>
                <li>🛡️ Supporto prioritario</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💳 Abbonati Mensile", key="monthly"):
            st.session_state.selected_plan = "monthly"
            st.session_state.show_payment = True
    
    with col2:
        st.markdown("""
        <div class="feature-card" style="border: 3px solid #667eea; transform: scale(1.05);">
            <div style="background: #667eea; color: white; padding: 0.5rem; border-radius: 10px; margin: -1rem -1rem 1rem -1rem;">
                <strong>🌟 PIÙ POPOLARE</strong>
            </div>
            <h3>📅 Annuale</h3>
            <div style="font-size: 2rem; font-weight: bold; color: #667eea;">€697</div>
            <p style="color: #666;">per anno</p>
            <p style="color: #00b894; font-weight: bold;">💰 Risparmi €467!</p>
            <ul style="text-align: left;">
                <li>🤖 Trading AI completo</li>
                <li>📊 Tutte le strategie</li>
                <li>💰 Capitale illimitato</li>
                <li>🏆 Sistema rewards</li>
                <li>🛡️ Supporto prioritario</li>
                <li>🎁 2 mesi GRATIS</li>
                <li>💎 Funzioni VIP</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💎 Abbonati Annuale", key="yearly"):
            st.session_state.selected_plan = "yearly"
            st.session_state.show_payment = True
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🚀 Lifetime</h3>
            <div style="font-size: 2rem; font-weight: bold; color: #667eea;">€1,997</div>
            <p style="color: #666;">una tantum</p>
            <p style="color: #00b894; font-weight: bold;">🔥 Offerta Limitata!</p>
            <ul style="text-align: left;">
                <li>🤖 Trading AI completo</li>
                <li>📊 Tutte le strategie</li>
                <li>💰 Capitale illimitato</li>
                <li>🏆 Sistema rewards</li>
                <li>🛡️ Supporto prioritario</li>
                <li>👑 Accesso a vita</li>
                <li>🎯 Strategie esclusive</li>
                <li>💼 Personal manager</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("👑 Lifetime Access", key="lifetime"):
            st.session_state.selected_plan = "lifetime"
            st.session_state.show_payment = True

def payment_component():
    """Componente pagamento"""
    if st.session_state.get('show_payment', False):
        plan = st.session_state.get('selected_plan', 'monthly')
        
        prices = {
            'monthly': 97,
            'yearly': 697,
            'lifetime': 1997
        }
        
        st.markdown(f"""
        <div class="premium-header">
            <h2>💳 Completa il Pagamento</h2>
            <p>Piano selezionato: <strong>{plan.title()}</strong> - €{prices[plan]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💳 Metodi di Pagamento")
            
            payment_method = st.selectbox(
                "Seleziona metodo",
                ["💳 Carta di Credito", "🏦 Bonifico Bancario", "₿ Bitcoin", "💎 Ethereum", "💰 PayPal"]
            )
            
            if "Carta" in payment_method:
                st.text_input("Numero Carta", placeholder="1234 5678 9012 3456")
                col_exp, col_cvv = st.columns(2)
                with col_exp:
                    st.text_input("Scadenza", placeholder="MM/AA")
                with col_cvv:
                    st.text_input("CVV", placeholder="123")
                st.text_input("Nome Titolare", placeholder="Mario Rossi")
            
            elif "Bitcoin" in payment_method or "Ethereum" in payment_method:
                st.info(f"📱 Invia €{prices[plan]} all'indirizzo:")
                st.code("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
                st.text_input("Transaction ID", placeholder="Inserisci l'ID della transazione")
            
            elif "PayPal" in payment_method:
                st.info("🔄 Verrai reindirizzato a PayPal per completare il pagamento")
            
            elif "Bonifico" in payment_method:
                st.info("🏦 Dati per bonifico:")
                st.code("""
IBAN: IT60 X054 2811 1010 0000 0123 456
BIC: BPMOIT22XXX
Causale: AurumBotX Premium - [TUO_TELEGRAM_ID]
                """)
        
        with col2:
            st.markdown("### 📋 Riepilogo Ordine")
            
            st.markdown(f"""
            <div class="feature-card">
                <h4>📦 Piano {plan.title()}</h4>
                <div style="display: flex; justify-content: space-between; margin: 1rem 0;">
                    <span>Prezzo:</span>
                    <strong>€{prices[plan]}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 1rem 0;">
                    <span>IVA (22%):</span>
                    <strong>€{prices[plan] * 0.22:.2f}</strong>
                </div>
                <hr>
                <div style="display: flex; justify-content: space-between; margin: 1rem 0; font-size: 1.2rem;">
                    <span><strong>Totale:</strong></span>
                    <strong style="color: #667eea;">€{prices[plan] * 1.22:.2f}</strong>
                </div>
                
                <div style="margin: 2rem 0;">
                    <h5>✅ Cosa Ottieni:</h5>
                    <ul style="text-align: left;">
                        <li>🤖 Accesso immediato</li>
                        <li>📊 Tutte le funzionalità</li>
                        <li>🛡️ Supporto 24/7</li>
                        <li>💰 Garanzia 30 giorni</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        col_back, col_pay = st.columns(2)
        
        with col_back:
            if st.button("⬅️ Torna ai Piani"):
                st.session_state.show_payment = False
                st.rerun()
        
        with col_pay:
            if st.button("💎 Completa Pagamento", key="complete_payment"):
                # Simula pagamento
                st.success("✅ Pagamento completato con successo!")
                st.balloons()
                
                # Attiva premium
                user_data = st.session_state.get('user_data', {})
                if user_data:
                    expires_at = datetime.now() + timedelta(days=365 if plan == 'yearly' else 30 if plan == 'monthly' else 36500)
                    update_premium_status(user_data['id'], expires_at.isoformat())
                
                st.session_state.premium_active = True
                st.session_state.show_payment = False
                time.sleep(2)
                st.rerun()

def wallet_management_component():
    """Componente gestione wallet"""
    st.markdown("""
    <div class="premium-header">
        <h2>💰 Gestione Wallet e Capitale</h2>
        <p>Collega il tuo wallet e configura il capitale per il trading</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔗 Collega Wallet")
        
        wallet_type = st.selectbox(
            "Tipo Wallet",
            ["🦊 MetaMask", "🛡️ Trust Wallet", "💎 Coinbase Wallet", "🔐 Hardware Wallet", "🏦 Exchange Wallet"]
        )
        
        if "MetaMask" in wallet_type:
            st.markdown("""
            <div class="wallet-card">
                <h4>🦊 MetaMask</h4>
                <p>Connetti il tuo wallet MetaMask per iniziare</p>
                <button class="premium-button" onclick="connectMetaMask()">
                    🔗 Connetti MetaMask
                </button>
            </div>
            """, unsafe_allow_html=True)
            
            # Simula connessione
            wallet_address = st.text_input("Indirizzo Wallet", value="0x742d35Cc6634C0532925a3b8D4C0532925a3b8D4")
            
        elif "Exchange" in wallet_type:
            st.markdown("#### 🏦 Configura Exchange")
            exchange = st.selectbox("Exchange", ["Binance", "Coinbase", "Kraken", "Bitfinex"])
            api_key = st.text_input("API Key", type="password")
            api_secret = st.text_input("API Secret", type="password")
            
        # Balance simulato
        if st.button("💰 Verifica Balance"):
            st.success("✅ Wallet connesso con successo!")
            
            # Simula balance
            balances = {
                "USDT": 15420.50,
                "BTC": 0.2847,
                "ETH": 4.125,
                "BNB": 12.8
            }
            
            st.markdown("#### 💰 Balance Disponibile:")
            for token, amount in balances.items():
                if token == "USDT":
                    st.metric(f"{token}", f"${amount:,.2f}")
                else:
                    st.metric(f"{token}", f"{amount:.4f}")
    
    with col2:
        st.markdown("### 🎯 Configurazione Capitale")
        
        # Capitale da investire
        capital_amount = st.number_input(
            "💰 Capitale da Investire (€)",
            min_value=100.0,
            max_value=100000.0,
            value=5000.0,
            step=100.0,
            help="Importo che vuoi destinare al trading automatico"
        )
        
        # Percentuale del wallet
        wallet_percentage = st.slider(
            "📊 Percentuale Wallet (%)",
            min_value=1,
            max_value=100,
            value=25,
            help="Quanto del tuo wallet vuoi usare per il trading"
        )
        
        # Risk management
        st.markdown("#### 🛡️ Risk Management")
        
        max_risk_per_trade = st.slider(
            "🎯 Risk Max per Trade (%)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.1
        )
        
        daily_loss_limit = st.slider(
            "🛑 Limite Perdite Giornaliere (%)",
            min_value=1.0,
            max_value=20.0,
            value=5.0,
            step=0.5
        )
        
        # Calcoli automatici
        st.markdown("#### 📊 Calcoli Automatici")
        
        max_trade_amount = capital_amount * (max_risk_per_trade / 100)
        daily_limit_amount = capital_amount * (daily_loss_limit / 100)
        
        st.info(f"""
        💡 **Riepilogo Configurazione:**
        - 💰 Capitale Trading: €{capital_amount:,.2f}
        - 🎯 Max per Trade: €{max_trade_amount:.2f}
        - 🛑 Limite Giornaliero: €{daily_limit_amount:.2f}
        - 📊 Percentuale Wallet: {wallet_percentage}%
        """)
        
        if st.button("💾 Salva Configurazione Capitale"):
            st.success("✅ Configurazione salvata con successo!")
            st.session_state.capital_configured = True

def strategy_selection_component():
    """Componente selezione strategia"""
    st.markdown("""
    <div class="premium-header">
        <h2>🎯 Selezione Strategia Trading</h2>
        <p>Scegli la strategia più adatta al tuo profilo di rischio</p>
    </div>
    """, unsafe_allow_html=True)
    
    strategies = {
        'swing_trading_6m': {
            'name': '📈 Swing Trading 6M',
            'description': 'Strategia conservativa ideale per principianti',
            'risk': 'Basso',
            'timeframe': '6 minuti',
            'trades_day': '5-15',
            'profit_target': '0.5-1.0%',
            'win_rate': '75%',
            'color': '#74b9ff'
        },
        'scalping_conservative': {
            'name': '⚡ Scalping Conservativo',
            'description': 'Trading rapido con rischio controllato',
            'risk': 'Medio-Basso',
            'timeframe': '3-6 minuti',
            'trades_day': '20-50',
            'profit_target': '0.3-0.5%',
            'win_rate': '68%',
            'color': '#00b894'
        },
        'scalping_aggressive': {
            'name': '🚀 Scalping Aggressivo',
            'description': 'Massimi profitti con rischio elevato',
            'risk': 'Alto',
            'timeframe': '1-3 minuti',
            'trades_day': '50-100',
            'profit_target': '0.8-1.5%',
            'win_rate': '62%',
            'color': '#e17055'
        },
        'ai_adaptive': {
            'name': '🤖 AI Adaptive',
            'description': 'Strategia che si adatta alle condizioni di mercato',
            'risk': 'Medio',
            'timeframe': 'Variabile',
            'trades_day': '10-30',
            'profit_target': '0.6-1.2%',
            'win_rate': '71%',
            'color': '#a29bfe'
        },
        'mixed_portfolio': {
            'name': '🎯 Portfolio Misto',
            'description': 'Combina multiple strategie per diversificare',
            'risk': 'Medio',
            'timeframe': 'Multi',
            'trades_day': '15-40',
            'profit_target': '0.7-1.1%',
            'win_rate': '69%',
            'color': '#fdcb6e'
        },
        'whale_following': {
            'name': '🐋 Whale Following',
            'description': 'Segue i movimenti delle balene crypto',
            'risk': 'Medio-Alto',
            'timeframe': '5-15 minuti',
            'trades_day': '8-25',
            'profit_target': '1.0-2.0%',
            'win_rate': '65%',
            'color': '#6c5ce7'
        }
    }
    
    # Grid di strategie
    cols = st.columns(2)
    
    for i, (key, strategy) in enumerate(strategies.items()):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="strategy-card" style="background: linear-gradient(135deg, {strategy['color']} 0%, {strategy['color']}aa 100%);">
                <h3>{strategy['name']}</h3>
                <p>{strategy['description']}</p>
                <div style="margin: 1rem 0;">
                    <strong>📊 Caratteristiche:</strong>
                    <ul style="text-align: left; margin: 0.5rem 0;">
                        <li>🎯 Risk Level: {strategy['risk']}</li>
                        <li>⏱️ Timeframe: {strategy['timeframe']}</li>
                        <li>📈 Trade/Giorno: {strategy['trades_day']}</li>
                        <li>💰 Profit Target: {strategy['profit_target']}</li>
                        <li>🏆 Win Rate: {strategy['win_rate']}</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🚀 Seleziona {strategy['name']}", key=f"select_{key}"):
                st.session_state.selected_strategy = key
                st.success(f"✅ Strategia {strategy['name']} selezionata!")
                st.session_state.strategy_configured = True
    
    # Configurazione avanzata strategia
    if st.session_state.get('selected_strategy'):
        selected = st.session_state.selected_strategy
        st.markdown(f"### ⚙️ Configurazione {strategies[selected]['name']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            profit_multiplier = st.slider(
                "🎯 Moltiplicatore Profit",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="Aumenta o diminuisci i target di profitto"
            )
            
            risk_multiplier = st.slider(
                "🛡️ Moltiplicatore Risk",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="Aumenta o diminuisci il rischio per trade"
            )
        
        with col2:
            trading_pairs = st.multiselect(
                "💱 Coppie Trading",
                ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'BNBUSDT'],
                default=['BTCUSDT', 'ETHUSDT']
            )
            
            active_hours = st.select_slider(
                "🕐 Ore Attive",
                options=['00-24', '06-22', '08-20', '09-18', '10-16'],
                value='00-24',
                help="Orari in cui il bot può operare"
            )
        
        if st.button("💾 Salva Configurazione Strategia"):
            st.success("✅ Configurazione strategia salvata!")

def rewards_system_component():
    """Componente sistema rewards"""
    st.markdown("""
    <div class="premium-header">
        <h2>🏆 Sistema Rewards</h2>
        <p>Raggiungi i traguardi e sblocca rewards esclusivi</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Ottieni progressi (simulati)
    user_id = 1  # Simulato
    rewards_progress = get_rewards_progress(user_id)
    performance = get_user_performance(user_id)
    
    # Progress generale
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">€{performance['current_balance']:,.2f}</div>
        <div class="metric-label">Balance Attuale</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Milestone rewards
    st.markdown("### 🎯 Milestone Rewards")
    
    for reward in rewards_progress:
        milestone = reward['milestone']
        percentage = reward['percentage']
        reward_text = reward['reward']
        achieved = reward['achieved']
        
        # Colore basato su achievement
        color = "#00b894" if achieved else "#667eea"
        status = "🏆 COMPLETATO" if achieved else f"{percentage:.1f}% completato"
        
        st.markdown(f"""
        <div class="reward-card" style="background: linear-gradient(135deg, {color} 0%, {color}aa 100%);">
            <h3>🎯 €{milestone:,} Milestone</h3>
            <p><strong>{reward_text}</strong></p>
            <div class="progress-bar" style="margin: 1rem 0;">
                <div class="progress-fill" style="width: {min(percentage, 100)}%;"></div>
            </div>
            <p><strong>{status}</strong></p>
            {f'<button class="premium-button">🎁 Riscatta Reward</button>' if achieved else ''}
        </div>
        """, unsafe_allow_html=True)
    
    # Rewards speciali
    st.markdown("### 🌟 Rewards Speciali")
    
    special_rewards = [
        {
            'title': '🔥 Streak Master',
            'description': '7 giorni consecutivi di profitto',
            'reward': 'Bonus 5% su tutti i profitti per 1 settimana',
            'progress': 85,
            'achieved': False
        },
        {
            'title': '💎 Diamond Hands',
            'description': 'Mantieni posizione durante alta volatilità',
            'reward': 'Accesso a strategie VIP esclusive',
            'progress': 100,
            'achieved': True
        },
        {
            'title': '🚀 Rocket Trader',
            'description': 'Raggiungi 90% win rate in 1 mese',
            'reward': 'Personal trading coach per 1 mese',
            'progress': 67,
            'achieved': False
        }
    ]
    
    cols = st.columns(3)
    
    for i, reward in enumerate(special_rewards):
        with cols[i]:
            color = "#00b894" if reward['achieved'] else "#667eea"
            
            st.markdown(f"""
            <div class="feature-card" style="border-left: 4px solid {color};">
                <h4>{reward['title']}</h4>
                <p>{reward['description']}</p>
                <div class="progress-bar" style="margin: 1rem 0;">
                    <div class="progress-fill" style="width: {reward['progress']}%; background: {color};"></div>
                </div>
                <p style="font-size: 0.9rem; color: #666;">{reward['reward']}</p>
                {'<span class="status-active">🏆 Completato</span>' if reward['achieved'] else f'<span class="status-inactive">{reward["progress"]}%</span>'}
            </div>
            """, unsafe_allow_html=True)

def ai_support_component():
    """Componente supporto AI"""
    st.markdown("""
    <div class="premium-header">
        <h2>🤖 Supporto AI</h2>
        <p>Il tuo assistente personale per trading e supporto tecnico</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat interface
    st.markdown("### 💬 Chat con AI Assistant")
    
    # Messaggi chat (simulati)
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {
                'role': 'assistant',
                'content': '👋 Ciao! Sono il tuo AI Assistant di AurumBotX. Come posso aiutarti oggi?',
                'timestamp': datetime.now() - timedelta(minutes=5)
            }
        ]
    
    # Mostra chat
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.chat_messages:
        role_icon = "🤖" if message['role'] == 'assistant' else "👤"
        time_str = message['timestamp'].strftime('%H:%M')
        
        st.markdown(f"""
        <div class="chat-message">
            <strong>{role_icon} {message['role'].title()}</strong> 
            <span style="color: #666; font-size: 0.8rem;">{time_str}</span>
            <p>{message['content']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input utente
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input("💬 Scrivi il tuo messaggio...", key="chat_input")
    
    with col2:
        if st.button("📤 Invia"):
            if user_input:
                # Aggiungi messaggio utente
                st.session_state.chat_messages.append({
                    'role': 'user',
                    'content': user_input,
                    'timestamp': datetime.now()
                })
                
                # Simula risposta AI
                ai_responses = [
                    "📊 Ho analizzato la tua strategia e sembra ottimale per le condizioni attuali di mercato.",
                    "💡 Ti consiglio di ridurre leggermente il risk per trade durante questa fase di alta volatilità.",
                    "🎯 La tua performance è eccellente! Hai superato il 73% di win rate questo mese.",
                    "🔧 Ho rilevato un'opportunità di ottimizzazione nella tua strategia. Vuoi che la implementi?",
                    "📈 Il mercato sta mostrando segnali rialzisti. La strategia Swing Trading potrebbe essere ideale.",
                    "🛡️ Ho attivato automaticamente le protezioni anti-perdita per il tuo portfolio."
                ]
                
                import random
                ai_response = random.choice(ai_responses)
                
                st.session_state.chat_messages.append({
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': datetime.now()
                })
                
                st.rerun()
    
    # Quick actions
    st.markdown("### ⚡ Azioni Rapide")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Analizza Performance"):
            st.session_state.chat_messages.append({
                'role': 'assistant',
                'content': '📊 Analisi completata! La tua performance è del +184.75% con un win rate del 73.2%. Ottimo lavoro!',
                'timestamp': datetime.now()
            })
            st.rerun()
    
    with col2:
        if st.button("🎯 Ottimizza Strategia"):
            st.session_state.chat_messages.append({
                'role': 'assistant',
                'content': '🎯 Ho ottimizzato i parametri della tua strategia. Profit target aumentato del 12% mantenendo lo stesso livello di rischio.',
                'timestamp': datetime.now()
            })
            st.rerun()
    
    with col3:
        if st.button("🚨 Check Rischi"):
            st.session_state.chat_messages.append({
                'role': 'assistant',
                'content': '🛡️ Tutti i sistemi di sicurezza sono attivi. Il tuo portfolio è protetto con stop-loss automatici.',
                'timestamp': datetime.now()
            })
            st.rerun()
    
    with col4:
        if st.button("💡 Suggerimenti"):
            st.session_state.chat_messages.append({
                'role': 'assistant',
                'content': '💡 Suggerimento: considera di diversificare su ETH e ADA per ridurre la correlazione con BTC.',
                'timestamp': datetime.now()
            })
            st.rerun()

def main_dashboard():
    """Dashboard principale per utenti premium"""
    st.markdown("""
    <div class="premium-header">
        <h1>🌟 AurumBotX Premium Dashboard</h1>
        <p>Benvenuto nella tua piattaforma di trading automatico</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metriche principali
    performance = get_user_performance(1)  # Simulato
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">€{performance['current_balance']:,.2f}</div>
            <div class="metric-label">Balance Totale</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #00b894;">+{performance['roi_percentage']:.1f}%</div>
            <div class="metric-label">ROI Totale</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{performance['total_trades']}</div>
            <div class="metric-label">Trade Totali</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #667eea;">{performance['win_rate']:.1f}%</div>
            <div class="metric-label">Win Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Grafici performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Evoluzione Balance")
        
        # Dati simulati
        dates = pd.date_range(start='2024-01-01', end='2024-08-18', freq='D')
        balance_data = []
        current_balance = 1000
        
        for date in dates:
            change = np.random.normal(0.02, 0.05)  # 2% crescita media con volatilità
            current_balance *= (1 + change)
            balance_data.append(current_balance)
        
        df = pd.DataFrame({
            'Date': dates,
            'Balance': balance_data
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Balance'],
            mode='lines',
            name='Balance',
            line=dict(color='#667eea', width=3),
            fill='tonexty'
        ))
        
        fig.update_layout(
            title="Evoluzione Balance",
            xaxis_title="Data",
            yaxis_title="Balance (€)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Distribuzione Trade")
        
        # Dati simulati
        trade_results = ['Win', 'Loss']
        trade_counts = [114, 42]  # 73.2% win rate
        
        fig = go.Figure(data=[go.Pie(
            labels=trade_results,
            values=trade_counts,
            hole=.3,
            marker_colors=['#00b894', '#e17055']
        )])
        
        fig.update_layout(
            title="Win/Loss Ratio",
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Status sistema
    st.markdown("### 🤖 Status Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 Trading Bot</h4>
            <span class="status-active">🟢 ATTIVO</span>
            <p>Ultima attività: 2 minuti fa</p>
            <p>Prossimo trade: In analisi...</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🎯 Strategia Attiva</h4>
            <span class="status-active">📈 Swing Trading 6M</span>
            <p>Performance oggi: +€127.30</p>
            <p>Trade oggi: 8 (7 win, 1 loss)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>🛡️ Risk Management</h4>
            <span class="status-active">🟢 SICURO</span>
            <p>Risk utilizzato: 45% del limite</p>
            <p>Drawdown max: -2.3%</p>
        </div>
        """, unsafe_allow_html=True)

# Main app logic
def main():
    """Funzione principale dell'app"""
    
    # Inizializza session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'premium_active' not in st.session_state:
        st.session_state.premium_active = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'
    
    # Controllo autenticazione
    if not st.session_state.authenticated:
        telegram_login_component()
        return
    
    # Controllo premium
    if not st.session_state.premium_active:
        # Simula check premium dal database
        user_data = st.session_state.get('user_data', {})
        if user_data and user_data.get('premium_status'):
            st.session_state.premium_active = True
        else:
            premium_subscription_component()
            payment_component()
            return
    
    # Sidebar navigation per utenti premium
    with st.sidebar:
        st.markdown("### 🌟 AurumBotX Premium")
        
        pages = {
            'dashboard': '📊 Dashboard',
            'wallet': '💰 Wallet & Capitale',
            'strategy': '🎯 Strategia',
            'rewards': '🏆 Rewards',
            'support': '🤖 Supporto AI',
            'settings': '⚙️ Impostazioni'
        }
        
        for key, label in pages.items():
            if st.button(label, key=f"nav_{key}"):
                st.session_state.current_page = key
                st.rerun()
        
        st.markdown("---")
        
        # User info
        user_data = st.session_state.get('user_data', {})
        if user_data:
            st.markdown(f"👤 **{user_data.get('username', 'User')}**")
            st.markdown("💎 **Premium Active**")
        
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Render della pagina corrente
    current_page = st.session_state.get('current_page', 'dashboard')
    
    if current_page == 'dashboard':
        main_dashboard()
    elif current_page == 'wallet':
        wallet_management_component()
    elif current_page == 'strategy':
        strategy_selection_component()
    elif current_page == 'rewards':
        rewards_system_component()
    elif current_page == 'support':
        ai_support_component()
    elif current_page == 'settings':
        st.markdown("### ⚙️ Impostazioni")
        st.info("🚧 Sezione in sviluppo...")

if __name__ == "__main__":
    # Import necessari per simulazioni
    import numpy as np
    
    main()

