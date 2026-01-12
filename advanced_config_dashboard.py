#!/usr/bin/env python3
"""
⚙️ DASHBOARD CONFIGURAZIONE AVANZATA AURUMBOTX
Controlli completi: Cifra Trading, Strategia, AI, Operatività
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import sys
import subprocess
import time
from datetime import datetime
import sqlite3

# Aggiungi path per import
sys.path.append('.')

# Import moduli per test
try:
    from utils.ai_trading import AITrading
    from utils.prediction_model import PredictionModel
    from utils.data_loader import CryptoDataLoader
    from utils.exchange_manager import ExchangeManager
except ImportError as e:
    st.error(f"Errore import moduli: {e}")

# Configurazione pagina
st.set_page_config(
    page_title="⚙️ AurumBotX - Configurazione Avanzata",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #6c5ce7, #a29bfe);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .config-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #6c5ce7;
        margin: 1rem 0;
    }
    .ai-status-active { 
        color: #28a745; 
        font-weight: bold;
        background: #d4edda;
        padding: 0.5rem;
        border-radius: 5px;
    }
    .ai-status-inactive { 
        color: #dc3545; 
        font-weight: bold;
        background: #f8d7da;
        padding: 0.5rem;
        border-radius: 5px;
    }
    .strategy-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .test-result {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header principale
st.markdown("""
<div class="main-header">
    <h1>⚙️ Configurazione Avanzata AurumBotX</h1>
    <p>Controllo Completo: Cifra, Strategia, AI, Operatività</p>
</div>
""", unsafe_allow_html=True)

# Funzioni di utilità
def load_current_config():
    """Carica configurazione corrente"""
    default_config = {
        'trading_amount_eur': 1000.0,
        'risk_per_trade_pct': 2.0,
        'min_confidence': 0.65,
        'strategy': 'swing_trading_6m',
        'profit_target_pct': 0.8,
        'stop_loss_pct': 0.5,
        'max_daily_trades': 50,
        'ai_enabled': True,
        'fallback_enabled': True
    }
    
    try:
        if os.path.exists('configs/advanced_config.json'):
            with open('configs/advanced_config.json', 'r') as f:
                config = json.load(f)
                # Merge con default per nuove chiavi
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
    except:
        pass
    
    return default_config

def save_config(config):
    """Salva configurazione"""
    try:
        os.makedirs('configs', exist_ok=True)
        with open('configs/advanced_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")
        return False

def test_ai_integration():
    """Test integrazione AI"""
    results = {
        'ai_trading': False,
        'prediction_model': False,
        'data_loader': False,
        'exchange_manager': False,
        'ai_prediction_test': False,
        'details': {}
    }
    
    try:
        # Test AI Trading
        ai_trading = AITrading()
        results['ai_trading'] = True
        results['details']['ai_trading'] = "✅ Inizializzato correttamente"
    except Exception as e:
        results['details']['ai_trading'] = f"❌ Errore: {str(e)[:100]}"
    
    try:
        # Test Prediction Model
        pred_model = PredictionModel()
        results['prediction_model'] = True
        results['details']['prediction_model'] = "✅ Modelli caricati"
    except Exception as e:
        results['details']['prediction_model'] = f"❌ Errore: {str(e)[:100]}"
    
    try:
        # Test Data Loader
        data_loader = CryptoDataLoader()
        results['data_loader'] = True
        results['details']['data_loader'] = "✅ Connessione dati OK"
    except Exception as e:
        results['details']['data_loader'] = f"❌ Errore: {str(e)[:100]}"
    
    try:
        # Test Exchange Manager
        exchange = ExchangeManager('binance', testnet=True)
        results['exchange_manager'] = True
        results['details']['exchange_manager'] = "✅ Exchange connesso"
    except Exception as e:
        results['details']['exchange_manager'] = f"❌ Errore: {str(e)[:100]}"
    
    return results

def get_bot_status():
    """Verifica status bot"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'test_trading_1000_euro' in result.stdout:
            return "🟢 TEST ATTIVO", "running"
        elif 'activate_24h_monitoring' in result.stdout:
            return "🟢 BOT ATTIVO", "running"
        else:
            return "🔴 INATTIVO", "stopped"
    except:
        return "⚠️ ERRORE", "error"

# Carica configurazione corrente
current_config = load_current_config()

# Sidebar controlli
st.sidebar.markdown("## 🎛️ Controlli Sistema")

# Status sistema
bot_status, bot_state = get_bot_status()
st.sidebar.markdown(f"**Status Bot:** {bot_status}")

if st.sidebar.button("🔄 Ricarica Config"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("🧪 Test AI Integration"):
    st.session_state.run_ai_test = True

# Tab principali
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 Cifra & Risk", "🎯 Strategia", "🤖 AI & Logica", "⚙️ Operatività", "🧪 Test Sistema"])

with tab1:
    st.markdown("## 💰 Configurazione Cifra e Risk Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💵 Capitale Trading")
        
        # Cifra trading principale
        trading_amount = st.number_input(
            "💰 Capitale Totale (€)",
            min_value=100.0,
            max_value=100000.0,
            value=current_config['trading_amount_eur'],
            step=100.0,
            help="Capitale totale disponibile per il trading"
        )
        
        # Risk per trade
        risk_per_trade = st.slider(
            "🛡️ Risk per Trade (%)",
            min_value=0.5,
            max_value=10.0,
            value=current_config['risk_per_trade_pct'],
            step=0.1,
            help="Percentuale massima del capitale da rischiare per singolo trade"
        )
        
        # Calcolo importo per trade
        max_amount_per_trade = trading_amount * (risk_per_trade / 100)
        st.info(f"💡 **Importo massimo per trade:** €{max_amount_per_trade:.2f}")
        
        # Profit target e stop loss
        profit_target = st.slider(
            "🎯 Profit Target (%)",
            min_value=0.1,
            max_value=5.0,
            value=current_config['profit_target_pct'],
            step=0.1
        )
        
        stop_loss = st.slider(
            "🛑 Stop Loss (%)",
            min_value=0.1,
            max_value=3.0,
            value=current_config['stop_loss_pct'],
            step=0.1
        )
    
    with col2:
        st.markdown("### 📊 Risk Management Avanzato")
        
        # Max trade giornalieri
        max_daily_trades = st.number_input(
            "📈 Max Trade Giornalieri",
            min_value=1,
            max_value=200,
            value=current_config['max_daily_trades'],
            help="Numero massimo di trade eseguibili in un giorno"
        )
        
        # Confidenza minima
        min_confidence = st.slider(
            "🎯 Confidenza Minima AI (%)",
            min_value=50,
            max_value=90,
            value=int(current_config['min_confidence'] * 100),
            help="Confidenza minima richiesta per eseguire un trade"
        ) / 100
        
        # Risk/Reward ratio
        risk_reward_ratio = profit_target / stop_loss
        st.metric("⚖️ Risk/Reward Ratio", f"1:{risk_reward_ratio:.2f}")
        
        # Calcoli risk management
        st.markdown("#### 📊 Calcoli Risk Management")
        st.write(f"💰 **Capitale:** €{trading_amount:,.2f}")
        st.write(f"🛡️ **Risk per Trade:** €{max_amount_per_trade:.2f} ({risk_per_trade}%)")
        st.write(f"🎯 **Profit Target:** €{max_amount_per_trade * profit_target/100:.2f}")
        st.write(f"🛑 **Stop Loss:** €{max_amount_per_trade * stop_loss/100:.2f}")
        
        # Salva configurazione cifra
        if st.button("💾 Salva Configurazione Cifra", key="save_money"):
            config_update = current_config.copy()
            config_update.update({
                'trading_amount_eur': trading_amount,
                'risk_per_trade_pct': risk_per_trade,
                'profit_target_pct': profit_target,
                'stop_loss_pct': stop_loss,
                'max_daily_trades': max_daily_trades,
                'min_confidence': min_confidence
            })
            
            if save_config(config_update):
                st.success("✅ Configurazione cifra salvata!")
                st.balloons()
                time.sleep(2)
                st.rerun()

with tab2:
    st.markdown("## 🎯 Selezione e Configurazione Strategia")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Strategia Trading")
        
        # Selezione strategia
        strategy_options = {
            'swing_trading_6m': '📈 Swing Trading 6M (Conservativo)',
            'scalping_6m_conservative': '⚡ Scalping 6M Conservativo',
            'scalping_6m_moderate': '⚡ Scalping 6M Moderato',
            'scalping_6m_aggressive': '⚡ Scalping 6M Aggressivo',
            'swing_trading_1h': '📈 Swing Trading 1H',
            'mixed_strategy': '🎯 Strategia Mista'
        }
        
        selected_strategy = st.selectbox(
            "🎯 Seleziona Strategia",
            options=list(strategy_options.keys()),
            index=list(strategy_options.keys()).index(current_config['strategy']) if current_config['strategy'] in strategy_options else 0,
            format_func=lambda x: strategy_options[x]
        )
        
        # Descrizione strategia
        strategy_descriptions = {
            'swing_trading_6m': {
                'desc': 'Strategia conservativa con timeframe 6 minuti. Ideale per principianti.',
                'timeframe': '6 minuti',
                'risk': 'Basso',
                'trades_day': '5-15',
                'profit_target': '0.5-1.0%',
                'stop_loss': '0.3-0.7%'
            },
            'scalping_6m_conservative': {
                'desc': 'Scalping rapido ma conservativo. Molti trade piccoli.',
                'timeframe': '6 minuti',
                'risk': 'Medio-Basso',
                'trades_day': '20-50',
                'profit_target': '0.3-0.5%',
                'stop_loss': '0.2-0.3%'
            },
            'scalping_6m_moderate': {
                'desc': 'Scalping moderato con buon bilanciamento risk/reward.',
                'timeframe': '6 minuti',
                'risk': 'Medio',
                'trades_day': '15-35',
                'profit_target': '0.5-0.8%',
                'stop_loss': '0.3-0.5%'
            }
        }
        
        if selected_strategy in strategy_descriptions:
            strategy_info = strategy_descriptions[selected_strategy]
            st.markdown(f"""
            <div class="strategy-card">
                <h4>📋 {strategy_options[selected_strategy]}</h4>
                <p>{strategy_info['desc']}</p>
                <ul>
                    <li><strong>Timeframe:</strong> {strategy_info['timeframe']}</li>
                    <li><strong>Risk Level:</strong> {strategy_info['risk']}</li>
                    <li><strong>Trade/Giorno:</strong> {strategy_info['trades_day']}</li>
                    <li><strong>Profit Target:</strong> {strategy_info['profit_target']}</li>
                    <li><strong>Stop Loss:</strong> {strategy_info['stop_loss']}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ⚙️ Parametri Strategia")
        
        # Parametri specifici strategia
        if 'scalping' in selected_strategy:
            st.markdown("#### ⚡ Parametri Scalping")
            
            scalp_profit = st.slider("🎯 Profit Target Scalping (%)", 0.1, 1.0, 0.3, 0.05)
            scalp_stop = st.slider("🛑 Stop Loss Scalping (%)", 0.1, 0.8, 0.2, 0.05)
            scalp_trades = st.number_input("📈 Max Trade/Ora", 1, 20, 10)
            
        elif 'swing' in selected_strategy:
            st.markdown("#### 📈 Parametri Swing Trading")
            
            swing_profit = st.slider("🎯 Profit Target Swing (%)", 0.3, 2.0, 0.8, 0.1)
            swing_stop = st.slider("🛑 Stop Loss Swing (%)", 0.2, 1.5, 0.5, 0.1)
            swing_hold_time = st.selectbox("⏱️ Tempo Holding", ["15min", "30min", "1h", "2h"])
        
        # Timeframe
        timeframe_options = ['1m', '3m', '5m', '6m', '15m', '30m', '1h']
        selected_timeframe = st.selectbox(
            "⏱️ Timeframe",
            timeframe_options,
            index=timeframe_options.index('6m')
        )
        
        # Pairs trading
        trading_pairs = st.multiselect(
            "💱 Coppie Trading",
            ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT'],
            default=['BTCUSDT']
        )
        
        # Salva strategia
        if st.button("💾 Salva Strategia", key="save_strategy"):
            config_update = current_config.copy()
            config_update.update({
                'strategy': selected_strategy,
                'timeframe': selected_timeframe,
                'trading_pairs': trading_pairs
            })
            
            if save_config(config_update):
                st.success("✅ Strategia salvata!")
                st.balloons()

with tab3:
    st.markdown("## 🤖 AI e Logica Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🧠 Configurazione AI")
        
        # AI Enable/Disable
        ai_enabled = st.checkbox(
            "🤖 Abilita AI Trading",
            value=current_config['ai_enabled'],
            help="Attiva/disattiva l'uso dell'AI per la generazione dei segnali"
        )
        
        # Fallback enable
        fallback_enabled = st.checkbox(
            "🔄 Abilita Fallback Tecnico",
            value=current_config['fallback_enabled'],
            help="Usa analisi tecnica quando AI non disponibile"
        )
        
        # Modelli AI
        st.markdown("#### 🎯 Modelli AI Disponibili")
        
        ai_models = st.multiselect(
            "Seleziona Modelli",
            ['RandomForest', 'GradientBoosting', 'XGBoost', 'LSTM', 'Transformer'],
            default=['RandomForest', 'GradientBoosting']
        )
        
        # Confidence threshold
        ai_confidence_threshold = st.slider(
            "🎯 Soglia Confidenza AI",
            0.5, 0.9, 0.7, 0.05,
            help="Confidenza minima per accettare segnali AI"
        )
        
        # Feature engineering
        st.markdown("#### 🔧 Feature Engineering")
        
        features_enabled = st.multiselect(
            "Features Abilitate",
            ['Technical Indicators', 'Sentiment Analysis', 'Volume Analysis', 'Price Action', 'Market Structure'],
            default=['Technical Indicators', 'Volume Analysis', 'Price Action']
        )
    
    with col2:
        st.markdown("### 📊 Status AI e Test")
        
        # Test AI Integration
        if st.button("🧪 Test Integrazione AI") or st.session_state.get('run_ai_test', False):
            if 'run_ai_test' in st.session_state:
                del st.session_state.run_ai_test
            
            with st.spinner("🔄 Testing AI Integration..."):
                ai_test_results = test_ai_integration()
            
            st.markdown("#### 🧪 Risultati Test AI")
            
            for component, status in ai_test_results.items():
                if component != 'details':
                    status_class = "ai-status-active" if status else "ai-status-inactive"
                    status_text = "✅ ATTIVO" if status else "❌ INATTIVO"
                    
                    st.markdown(f"""
                    <div class="{status_class}">
                        <strong>{component.replace('_', ' ').title()}:</strong> {status_text}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if component in ai_test_results['details']:
                        st.write(f"📋 {ai_test_results['details'][component]}")
            
            # Overall AI Status
            ai_components_active = sum([ai_test_results['ai_trading'], ai_test_results['prediction_model']])
            overall_status = "🟢 AI OPERATIVO" if ai_components_active >= 1 else "🔴 AI NON OPERATIVO"
            
            st.markdown(f"""
            <div class="test-result">
                <h4>🎯 Status Generale AI</h4>
                <p><strong>{overall_status}</strong></p>
                <p>Componenti attivi: {ai_components_active}/2</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Salva configurazione AI
        if st.button("💾 Salva Config AI", key="save_ai"):
            config_update = current_config.copy()
            config_update.update({
                'ai_enabled': ai_enabled,
                'fallback_enabled': fallback_enabled,
                'ai_models': ai_models,
                'ai_confidence_threshold': ai_confidence_threshold,
                'features_enabled': features_enabled
            })
            
            if save_config(config_update):
                st.success("✅ Configurazione AI salvata!")

with tab4:
    st.markdown("## ⚙️ Configurazione Operatività")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 Parametri Operativi")
        
        # Frequenza analisi
        analysis_frequency = st.selectbox(
            "⏱️ Frequenza Analisi",
            ['1 minuto', '3 minuti', '5 minuti', '10 minuti'],
            index=2
        )
        
        # Auto trading
        auto_trading = st.checkbox("🤖 Trading Automatico", value=True)
        
        # Paper trading
        paper_trading = st.checkbox("📄 Paper Trading (Simulazione)", value=True)
        
        # Notifications
        notifications = st.checkbox("🔔 Notifiche Trade", value=True)
        
        # Logging level
        log_level = st.selectbox(
            "📋 Livello Log",
            ['INFO', 'DEBUG', 'WARNING', 'ERROR'],
            index=0
        )
    
    with col2:
        st.markdown("### 🌐 Connessioni")
        
        # Exchange
        exchange = st.selectbox(
            "💱 Exchange",
            ['Binance Testnet', 'Binance Mainnet'],
            index=0
        )
        
        # Database
        database_enabled = st.checkbox("💾 Database Persistence", value=True)
        
        # API Rate Limits
        api_rate_limit = st.slider("🚦 API Rate Limit (req/min)", 100, 1200, 600)
        
        # Backup
        backup_enabled = st.checkbox("💾 Backup Automatico", value=True)
        backup_frequency = st.selectbox("⏱️ Frequenza Backup", ["1h", "6h", "12h", "24h"], index=1)

with tab5:
    st.markdown("## 🧪 Test Sistema Completo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 Test Componenti")
        
        if st.button("🧪 Test Completo Sistema"):
            with st.spinner("🔄 Esecuzione test completo..."):
                # Test AI
                ai_results = test_ai_integration()
                
                # Test configurazione
                config_valid = os.path.exists('configs/advanced_config.json')
                
                # Test database
                db_exists = os.path.exists('test_trading_1000_euro.db')
                
                # Test bot status
                bot_status, bot_state = get_bot_status()
                bot_running = bot_state == "running"
                
                # Risultati
                st.markdown("#### 📊 Risultati Test Completo")
                
                tests = [
                    ("🤖 AI Trading", ai_results['ai_trading']),
                    ("🧠 Prediction Model", ai_results['prediction_model']),
                    ("📊 Data Loader", ai_results['data_loader']),
                    ("💱 Exchange Manager", ai_results['exchange_manager']),
                    ("⚙️ Configurazione", config_valid),
                    ("💾 Database", db_exists),
                    ("🤖 Bot Running", bot_running)
                ]
                
                passed_tests = 0
                for test_name, test_result in tests:
                    status = "✅ PASS" if test_result else "❌ FAIL"
                    color = "green" if test_result else "red"
                    st.markdown(f"**{test_name}:** <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
                    if test_result:
                        passed_tests += 1
                
                # Score finale
                score = (passed_tests / len(tests)) * 100
                st.metric("🎯 Score Sistema", f"{score:.1f}%")
                
                if score >= 80:
                    st.success("🎉 Sistema pronto per il trading!")
                elif score >= 60:
                    st.warning("⚠️ Sistema parzialmente operativo")
                else:
                    st.error("❌ Sistema necessita correzioni")
    
    with col2:
        st.markdown("### 📊 Configurazione Attuale")
        
        # Mostra config corrente
        st.json(current_config)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #666;">
    <h4>⚙️ Configurazione Avanzata AurumBotX</h4>
    <p>Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>🎯 Controllo Completo Sistema | 💰 Cifra Configurabile | 🤖 AI Integrata</p>
</div>
""", unsafe_allow_html=True)

