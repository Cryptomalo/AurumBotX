#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
📱 AURUMBOTX MOBILE WEB APP
App web ottimizzata per smartphone con tutte le funzionalità
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import sqlite3
import hashlib
import time
from typing import Dict, Any
import numpy as np

# Configurazione mobile-first
st.set_page_config(
    page_title="📱 AurumBotX Mobile",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS ottimizzato per mobile
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Mobile-first design */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
        margin: 0;
    }
    
    /* Header mobile */
    .mobile-header {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 0 0 20px 20px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Card mobile */
    .mobile-card {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    /* Bottoni mobile */
    .mobile-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 20px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin: 0.5rem 0;
        font-size: 1rem;
    }
    
    .mobile-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    
    /* Metriche mobile */
    .mobile-metric {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .metric-value-mobile {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2d3436;
        margin-bottom: 0.25rem;
    }
    
    .metric-label-mobile {
        color: #636e72;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    /* Status indicators */
    .status-online {
        color: #00b894;
        font-weight: bold;
        background: #d4edda;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    
    .status-offline {
        color: #e17055;
        font-weight: bold;
        background: #f8d7da;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    
    /* Navigation mobile */
    .mobile-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 0.5rem;
        box-shadow: 0 -4px 15px rgba(0,0,0,0.1);
        border-radius: 20px 20px 0 0;
        z-index: 1000;
    }
    
    .nav-item {
        display: inline-block;
        text-align: center;
        padding: 0.5rem;
        margin: 0 0.25rem;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
        min-width: 60px;
    }
    
    .nav-item:hover {
        background: #f8f9fa;
    }
    
    .nav-item.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Chat mobile */
    .mobile-chat {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 1rem;
        max-height: 300px;
        overflow-y: auto;
        margin: 1rem 0;
    }
    
    .chat-message-mobile {
        background: white;
        border-radius: 10px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .chat-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 2rem;
    }
    
    .chat-ai {
        background: #e8f4fd;
        margin-right: 2rem;
    }
    
    /* Login mobile */
    .mobile-login {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 1rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    /* Premium mobile */
    .premium-card-mobile {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .stApp > div {
            padding: 0 !important;
        }
        
        .main .block-container {
            padding: 1rem !important;
            max-width: 100% !important;
        }
        
        .mobile-metric {
            margin: 0.25rem 0;
            padding: 0.75rem;
        }
        
        .metric-value-mobile {
            font-size: 1.25rem;
        }
        
        .mobile-card {
            margin: 0.25rem 0;
            padding: 0.75rem;
        }
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
</style>
""", unsafe_allow_html=True)

# Database functions (same as premium dashboard)
def init_mobile_database():
    """Inizializza database mobile"""
    conn = sqlite3.connect('mobile_users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mobile_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE,
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
            push_notifications BOOLEAN DEFAULT TRUE,
            biometric_enabled BOOLEAN DEFAULT FALSE
        )
    ''')
    
    conn.commit()
    conn.close()

init_mobile_database()

# Mobile-specific functions
def get_mobile_user_data(phone_number: str) -> Dict[str, Any]:
    """Ottieni dati utente mobile"""
    # Simula dati utente
    return {
        'id': 1,
        'phone_number': phone_number,
        'username': 'MobileUser',
        'premium_status': True,
        'capital_amount': 5000.0,
        'selected_strategy': 'swing_trading_6m',
        'total_profit': 2847.50,
        'push_notifications': True,
        'biometric_enabled': True
    }

def get_mobile_performance() -> Dict[str, Any]:
    """Ottieni performance mobile"""
    return {
        'current_balance': 7847.50,
        'total_profit': 2847.50,
        'roi_percentage': 57.52,
        'total_trades': 89,
        'win_rate': 74.2,
        'daily_profit': 127.30,
        'weekly_profit': 891.20,
        'best_trade': 245.80,
        'active_strategy': 'Swing Trading 6M',
        'bot_status': 'ATTIVO',
        'last_trade': '2 minuti fa'
    }

# Mobile login component
def mobile_login():
    """Login mobile ottimizzato"""
    st.markdown("""
    <div class="mobile-header">
        <h1>📱 AurumBotX Mobile</h1>
        <p>Trading automatico sempre con te</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="mobile-login">
        <h2>🔐 Accesso Rapido</h2>
        <p>Accedi al tuo account AurumBotX</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login options
    login_method = st.selectbox(
        "Metodo di accesso",
        ["📱 Numero di telefono", "📧 Email", "🔗 Telegram", "👆 Biometrico"]
    )
    
    if "telefono" in login_method:
        phone = st.text_input("📱 Numero di telefono", placeholder="+39 123 456 7890")
        if st.button("📲 Invia SMS", key="sms_login"):
            if phone:
                st.success("✅ SMS inviato! Inserisci il codice ricevuto")
                code = st.text_input("🔢 Codice SMS", placeholder="123456")
                if st.button("🚀 Accedi", key="verify_sms"):
                    if code:
                        st.session_state.authenticated = True
                        st.session_state.user_data = get_mobile_user_data(phone)
                        st.rerun()
    
    elif "Email" in login_method:
        email = st.text_input("📧 Email", placeholder="tuaemail@example.com")
        password = st.text_input("🔒 Password", type="password")
        if st.button("🚀 Accedi con Email", key="email_login"):
            if email and password:
                st.session_state.authenticated = True
                st.session_state.user_data = get_mobile_user_data(email)
                st.rerun()
    
    elif "Telegram" in login_method:
        st.markdown("""
        <div class="mobile-card">
            <h4>🔗 Login Telegram</h4>
            <p>Accedi usando il tuo account Telegram</p>
            <button class="mobile-button" onclick="window.open('https://t.me/AurumBotXBot', '_blank')">
                📱 Apri Telegram Bot
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        telegram_code = st.text_input("🔢 Codice Telegram", placeholder="ABC123")
        if st.button("✅ Verifica Codice", key="telegram_verify"):
            if telegram_code:
                st.session_state.authenticated = True
                st.session_state.user_data = get_mobile_user_data("telegram_user")
                st.rerun()
    
    elif "Biometrico" in login_method:
        st.markdown("""
        <div class="mobile-card">
            <h4>👆 Accesso Biometrico</h4>
            <p>Usa la tua impronta digitale o Face ID</p>
            <div style="text-align: center; margin: 2rem 0;">
                <div style="width: 80px; height: 80px; border: 3px solid #667eea; border-radius: 50%; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-size: 2rem;">
                    👆
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔓 Sblocca con Biometria", key="biometric_login"):
            # Simula autenticazione biometrica
            with st.spinner("🔍 Verifica biometrica in corso..."):
                time.sleep(2)
            st.success("✅ Autenticazione biometrica riuscita!")
            st.session_state.authenticated = True
            st.session_state.user_data = get_mobile_user_data("biometric_user")
            st.rerun()

# Mobile dashboard
def mobile_dashboard():
    """Dashboard principale mobile"""
    performance = get_mobile_performance()
    
    # Header mobile
    st.markdown(f"""
    <div class="mobile-header">
        <h2>📊 Dashboard</h2>
        <p>Ultimo aggiornamento: {datetime.now().strftime('%H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metriche principali - 2x2 grid
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="mobile-metric">
            <div class="metric-value-mobile">€{performance['current_balance']:,.0f}</div>
            <div class="metric-label-mobile">Balance Totale</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="mobile-metric">
            <div class="metric-value-mobile">{performance['total_trades']}</div>
            <div class="metric-label-mobile">Trade Totali</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="mobile-metric">
            <div class="metric-value-mobile" style="color: #00b894;">+{performance['roi_percentage']:.1f}%</div>
            <div class="metric-label-mobile">ROI</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="mobile-metric">
            <div class="metric-value-mobile" style="color: #667eea;">{performance['win_rate']:.1f}%</div>
            <div class="metric-label-mobile">Win Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Status bot
    st.markdown(f"""
    <div class="mobile-card">
        <h4>🤖 Status Bot</h4>
        <p><span class="status-online">🟢 {performance['bot_status']}</span></p>
        <p><strong>Strategia:</strong> {performance['active_strategy']}</p>
        <p><strong>Ultimo Trade:</strong> {performance['last_trade']}</p>
        <p><strong>Profitto Oggi:</strong> €{performance['daily_profit']:.2f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Grafico performance mobile
    st.markdown("### 📈 Performance Settimanale")
    
    # Dati simulati per grafico mobile
    days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    profits = [127.30, 89.50, 156.80, 203.40, 91.20, 178.60, 245.30]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days,
        y=profits,
        mode='lines+markers',
        name='Profitto Giornaliero',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8, color='#667eea'),
        fill='tonexty'
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Mobile wallet
def mobile_wallet():
    """Gestione wallet mobile"""
    st.markdown("""
    <div class="mobile-header">
        <h2>💰 Wallet</h2>
        <p>Gestisci il tuo capitale</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Balance cards
    balances = {
        'USDT': 15420.50,
        'BTC': 0.2847,
        'ETH': 4.125,
        'BNB': 12.8
    }
    
    for token, amount in balances.items():
        if token == 'USDT':
            value_display = f"${amount:,.2f}"
        else:
            value_display = f"{amount:.4f}"
        
        st.markdown(f"""
        <div class="mobile-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4>{token}</h4>
                    <p style="margin: 0; color: #666;">Balance</p>
                </div>
                <div style="text-align: right;">
                    <h3 style="margin: 0; color: #667eea;">{value_display}</h3>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("### ⚡ Azioni Rapide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💰 Deposita", key="mobile_deposit"):
            st.success("💰 Funzione deposito in sviluppo")
    
    with col2:
        if st.button("💸 Preleva", key="mobile_withdraw"):
            st.success("💸 Funzione prelievo in sviluppo")
    
    # Configurazione capitale
    st.markdown("### 🎯 Configurazione Trading")
    
    capital = st.slider("💰 Capitale Trading (€)", 100, 50000, 5000, 100)
    risk_per_trade = st.slider("🎯 Risk per Trade (%)", 0.5, 10.0, 2.0, 0.1)
    
    st.markdown(f"""
    <div class="mobile-card">
        <h4>📊 Riepilogo</h4>
        <p><strong>Capitale Trading:</strong> €{capital:,}</p>
        <p><strong>Risk per Trade:</strong> {risk_per_trade}%</p>
        <p><strong>Max per Trade:</strong> €{capital * risk_per_trade / 100:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

# Mobile strategy
def mobile_strategy():
    """Selezione strategia mobile"""
    st.markdown("""
    <div class="mobile-header">
        <h2>🎯 Strategia</h2>
        <p>Scegli la tua strategia</p>
    </div>
    """, unsafe_allow_html=True)
    
    strategies = [
        {
            'name': '📈 Swing Trading 6M',
            'risk': 'Basso',
            'trades': '5-15/giorno',
            'profit': '0.5-1.0%',
            'color': '#74b9ff'
        },
        {
            'name': '⚡ Scalping Conservativo',
            'risk': 'Medio-Basso',
            'trades': '20-50/giorno',
            'profit': '0.3-0.5%',
            'color': '#00b894'
        },
        {
            'name': '🚀 Scalping Aggressivo',
            'risk': 'Alto',
            'trades': '50-100/giorno',
            'profit': '0.8-1.5%',
            'color': '#e17055'
        },
        {
            'name': '🤖 AI Adaptive',
            'risk': 'Medio',
            'trades': '10-30/giorno',
            'profit': '0.6-1.2%',
            'color': '#a29bfe'
        }
    ]
    
    for i, strategy in enumerate(strategies):
        selected = st.session_state.get('selected_strategy') == i
        border_color = strategy['color'] if selected else '#e1e8ed'
        
        st.markdown(f"""
        <div class="mobile-card" style="border-left: 4px solid {border_color};">
            <h4>{strategy['name']}</h4>
            <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                <span>Risk:</span>
                <strong>{strategy['risk']}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                <span>Trade/Giorno:</span>
                <strong>{strategy['trades']}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                <span>Profit Target:</span>
                <strong>{strategy['profit']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🚀 Seleziona", key=f"strategy_{i}"):
            st.session_state.selected_strategy = i
            st.success(f"✅ Strategia {strategy['name']} selezionata!")
            st.rerun()

# Mobile rewards
def mobile_rewards():
    """Sistema rewards mobile"""
    st.markdown("""
    <div class="mobile-header">
        <h2>🏆 Rewards</h2>
        <p>I tuoi traguardi</p>
    </div>
    """, unsafe_allow_html=True)
    
    current_balance = 7847.50
    
    milestones = [
        {'target': 10000, 'reward': '🎁 Premium Features + 1 Mese Gratis'},
        {'target': 25000, 'reward': '💎 VIP Status + Strategie Esclusive'},
        {'target': 50000, 'reward': '🏆 Elite Membership + Personal Manager'},
        {'target': 100000, 'reward': '👑 Diamond Status + Profit Sharing'}
    ]
    
    for milestone in milestones:
        target = milestone['target']
        reward = milestone['reward']
        progress = min((current_balance / target) * 100, 100)
        achieved = current_balance >= target
        
        color = '#00b894' if achieved else '#667eea'
        status = '🏆 COMPLETATO' if achieved else f'{progress:.1f}%'
        
        st.markdown(f"""
        <div class="mobile-card">
            <h4>🎯 €{target:,} Milestone</h4>
            <p>{reward}</p>
            <div style="background: #e9ecef; border-radius: 10px; height: 10px; margin: 1rem 0;">
                <div style="background: {color}; height: 100%; border-radius: 10px; width: {min(progress, 100)}%; transition: width 0.3s ease;"></div>
            </div>
            <div style="text-align: right;">
                <strong style="color: {color};">{status}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Mobile support (AI Chat)
def mobile_support():
    """Supporto AI mobile"""
    st.markdown("""
    <div class="mobile-header">
        <h2>🤖 Supporto AI</h2>
        <p>Il tuo assistente personale</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat interface mobile
    if 'mobile_chat' not in st.session_state:
        st.session_state.mobile_chat = [
            {
                'role': 'ai',
                'message': '👋 Ciao! Sono il tuo AI Assistant. Come posso aiutarti?',
                'time': datetime.now() - timedelta(minutes=1)
            }
        ]
    
    # Display chat
    st.markdown('<div class="mobile-chat">', unsafe_allow_html=True)
    
    for chat in st.session_state.mobile_chat:
        role_class = 'chat-ai' if chat['role'] == 'ai' else 'chat-user'
        role_icon = '🤖' if chat['role'] == 'ai' else '👤'
        time_str = chat['time'].strftime('%H:%M')
        
        st.markdown(f"""
        <div class="chat-message-mobile {role_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong>{role_icon} {chat['role'].upper()}</strong>
                <span style="font-size: 0.8rem; opacity: 0.7;">{time_str}</span>
            </div>
            <p style="margin: 0;">{chat['message']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("### ⚡ Azioni Rapide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Analizza Performance", key="mobile_analyze"):
            st.session_state.mobile_chat.append({
                'role': 'ai',
                'message': '📊 Analisi completata! La tua performance è eccellente: ROI +57.5% con 74.2% win rate. Ottimo lavoro!',
                'time': datetime.now()
            })
            st.rerun()
        
        if st.button("🚨 Check Rischi", key="mobile_risk"):
            st.session_state.mobile_chat.append({
                'role': 'ai',
                'message': '🛡️ Tutti i sistemi di sicurezza sono attivi. Il tuo portfolio è protetto con stop-loss automatici.',
                'time': datetime.now()
            })
            st.rerun()
    
    with col2:
        if st.button("🎯 Ottimizza Strategia", key="mobile_optimize"):
            st.session_state.mobile_chat.append({
                'role': 'ai',
                'message': '🎯 Ho ottimizzato i parametri della tua strategia. Profit target aumentato del 8% mantenendo lo stesso rischio.',
                'time': datetime.now()
            })
            st.rerun()
        
        if st.button("💡 Suggerimenti", key="mobile_suggestions"):
            st.session_state.mobile_chat.append({
                'role': 'ai',
                'message': '💡 Suggerimento: considera di aumentare leggermente l\'esposizione su ETH per diversificare il portfolio.',
                'time': datetime.now()
            })
            st.rerun()
    
    # Text input
    user_input = st.text_input("💬 Scrivi un messaggio...", key="mobile_chat_input")
    
    if st.button("📤 Invia", key="mobile_send"):
        if user_input:
            # Add user message
            st.session_state.mobile_chat.append({
                'role': 'user',
                'message': user_input,
                'time': datetime.now()
            })
            
            # Simulate AI response
            ai_responses = [
                f"🤖 Ho analizzato la tua richiesta '{user_input}'. Ecco la mia risposta personalizzata!",
                f"💡 Ottima domanda! Basandomi sui tuoi dati, ti consiglio di...",
                f"📊 Ho controllato le tue performance. La situazione è ottimale per '{user_input}'.",
                f"🎯 La tua strategia attuale è perfetta per quello che mi hai chiesto!"
            ]
            
            import random
            ai_response = random.choice(ai_responses)
            
            st.session_state.mobile_chat.append({
                'role': 'ai',
                'message': ai_response,
                'time': datetime.now()
            })
            
            st.rerun()

# Mobile settings
def mobile_settings():
    """Impostazioni mobile"""
    st.markdown("""
    <div class="mobile-header">
        <h2>⚙️ Impostazioni</h2>
        <p>Personalizza la tua app</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Account settings
    st.markdown("### 👤 Account")
    
    st.markdown("""
    <div class="mobile-card">
        <h4>Informazioni Account</h4>
        <p><strong>Username:</strong> MobileUser</p>
        <p><strong>Status:</strong> <span class="status-online">Premium Attivo</span></p>
        <p><strong>Scadenza:</strong> 15 Marzo 2025</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Notification settings
    st.markdown("### 🔔 Notifiche")
    
    push_notifications = st.checkbox("📱 Notifiche Push", value=True)
    trade_alerts = st.checkbox("💹 Alert Trade", value=True)
    daily_reports = st.checkbox("📊 Report Giornalieri", value=True)
    milestone_alerts = st.checkbox("🏆 Alert Milestone", value=True)
    
    # Security settings
    st.markdown("### 🔒 Sicurezza")
    
    biometric_login = st.checkbox("👆 Login Biometrico", value=True)
    two_factor = st.checkbox("🔐 Autenticazione 2FA", value=False)
    auto_logout = st.selectbox("⏰ Logout Automatico", ["Mai", "15 minuti", "30 minuti", "1 ora"])
    
    # App settings
    st.markdown("### 📱 App")
    
    theme = st.selectbox("🎨 Tema", ["Automatico", "Chiaro", "Scuro"])
    language = st.selectbox("🌍 Lingua", ["Italiano", "English", "Español", "Français"])
    currency = st.selectbox("💰 Valuta", ["EUR (€)", "USD ($)", "GBP (£)"])
    
    # Save settings
    if st.button("💾 Salva Impostazioni", key="save_mobile_settings"):
        st.success("✅ Impostazioni salvate con successo!")

# Mobile navigation
def mobile_navigation():
    """Navigazione mobile bottom"""
    current_page = st.session_state.get('mobile_page', 'dashboard')
    
    pages = {
        'dashboard': '📊',
        'wallet': '💰',
        'strategy': '🎯',
        'rewards': '🏆',
        'support': '🤖',
        'settings': '⚙️'
    }
    
    # Create navigation
    cols = st.columns(len(pages))
    
    for i, (page_key, icon) in enumerate(pages.items()):
        with cols[i]:
            active_class = 'active' if current_page == page_key else ''
            
            if st.button(f"{icon}", key=f"nav_{page_key}"):
                st.session_state.mobile_page = page_key
                st.rerun()

# Main mobile app
def main_mobile_app():
    """App principale mobile"""
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'mobile_page' not in st.session_state:
        st.session_state.mobile_page = 'dashboard'
    
    # Check authentication
    if not st.session_state.authenticated:
        mobile_login()
        return
    
    # Get current page
    current_page = st.session_state.get('mobile_page', 'dashboard')
    
    # Render current page
    if current_page == 'dashboard':
        mobile_dashboard()
    elif current_page == 'wallet':
        mobile_wallet()
    elif current_page == 'strategy':
        mobile_strategy()
    elif current_page == 'rewards':
        mobile_rewards()
    elif current_page == 'support':
        mobile_support()
    elif current_page == 'settings':
        mobile_settings()
    
    # Bottom navigation
    st.markdown("<div style='margin-bottom: 100px;'></div>", unsafe_allow_html=True)
    
    # Fixed bottom navigation
    st.markdown("""
    <div class="mobile-nav">
        <div style="display: flex; justify-content: space-around;">
    """, unsafe_allow_html=True)
    
    mobile_navigation()
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button in sidebar (hidden by default)
    with st.sidebar:
        st.markdown("### 📱 AurumBotX Mobile")
        user_data = st.session_state.get('user_data', {})
        if user_data:
            st.markdown(f"👤 **{user_data.get('username', 'User')}**")
            st.markdown("💎 **Premium Active**")
        
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main_mobile_app()

