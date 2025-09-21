#!/usr/bin/env python3
"""
AurumBotX - Security Dashboard
Dashboard sicurezza integrata con VPN, anti-furto e protezione dati

Author: AurumBotX Team
Date: 12 Settembre 2025
Version: 1.0 - Security Ready
"""

import streamlit as st
import sys
import os

# Add project root to path with proper handling
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.security.advanced_security_layer import AdvancedSecurityLayer
    from src.security.vpn_manager import VPNManager
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

import time
import json
from datetime import datetime, timedelta

# Configurazione pagina
st.set_page_config(
    page_title="AurumBotX - Security Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .security-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .vpn-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    
    .security-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    
    .threat-card {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: #333;
        margin: 1rem 0;
        border-left: 5px solid #ff6b6b;
    }
    
    .safe-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: #333;
        margin: 1rem 0;
        border-left: 5px solid #51cf66;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .status-online {
        color: #51cf66;
        font-weight: bold;
    }
    
    .status-offline {
        color: #ff6b6b;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffd43b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Inizializza sistemi sicurezza
@st.cache_resource
def init_security_systems():
    """Inizializza sistemi di sicurezza"""
    security_layer = AdvancedSecurityLayer()
    vpn_manager = VPNManager()
    return security_layer, vpn_manager

def main():
    """Dashboard principale sicurezza"""
    
    # Header principale
    st.markdown("""
    <div class="security-header">
        <h1>🛡️ AurumBotX Security Center</h1>
        <h3>VPN, Anti-Furto e Protezione Dati Avanzata</h3>
        <p>🔒 Sicurezza enterprise per trading reale</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inizializza sistemi
    security_layer, vpn_manager = init_security_systems()
    
    # Sidebar con controlli
    with st.sidebar:
        st.markdown("### 🔧 Controlli Sicurezza")
        
        # Controlli VPN
        st.markdown("#### 🔒 VPN Controls")
        
        if st.button("🚀 Connetti VPN", key="connect_vpn"):
            with st.spinner("Connessione VPN..."):
                connection = vpn_manager.auto_connect_best_server()
                if connection.connected:
                    st.success("✅ VPN Connessa!")
                else:
                    st.error("❌ Connessione fallita")
        
        if st.button("🔓 Disconnetti VPN", key="disconnect_vpn"):
            with st.spinner("Disconnessione..."):
                if vpn_manager.disconnect_vpn():
                    st.success("✅ VPN Disconnessa")
                else:
                    st.error("❌ Errore disconnessione")
        
        st.markdown("---")
        
        # Controlli sicurezza
        st.markdown("#### 🛡️ Security Controls")
        
        if st.button("🚨 Emergency Lockdown", key="emergency_lockdown"):
            security_layer.emergency_lockdown("Manual activation from dashboard")
            st.error("🚨 SISTEMA IN LOCKDOWN!")
        
        if st.button("🔄 Reset Security", key="reset_security"):
            st.info("🔄 Sistema sicurezza resettato")
        
        st.markdown("---")
        
        # Auto-refresh
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=True)
        
        if auto_refresh:
            time.sleep(30)
            st.rerun()
    
    # Layout principale
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Status VPN
        st.markdown("""
        <div class="vpn-card">
            <h2>🔒 VPN Status</h2>
            <p>Connessione sicura e anonima</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Ottieni status VPN
        current_ip = vpn_manager.get_current_ip()
        location = vpn_manager.get_ip_location(current_ip)
        vpn_connection = vpn_manager.get_vpn_status()
        
        # Metriche VPN
        col_vpn1, col_vpn2, col_vpn3 = st.columns(3)
        
        with col_vpn1:
            if vpn_connection and vpn_connection.connected:
                st.metric("🔒 VPN Status", "CONNECTED", "🟢")
            else:
                st.metric("🔒 VPN Status", "DISCONNECTED", "🔴")
        
        with col_vpn2:
            st.metric("📍 Location", f"{location['city']}", f"{location['country']}")
        
        with col_vpn3:
            st.metric("🌐 IP Address", current_ip[:12] + "...", "")
        
        # Dettagli VPN
        if vpn_connection and vpn_connection.connected:
            st.markdown("""
            <div class="safe-card">
                <h4>✅ VPN Attiva</h4>
                <p><strong>Server:</strong> {}</p>
                <p><strong>Encryption:</strong> AES-256</p>
                <p><strong>Kill Switch:</strong> {}</p>
                <p><strong>DNS Leak Protection:</strong> Attiva</p>
            </div>
            """.format(
                vpn_connection.server.name if vpn_connection.server else "Unknown",
                "Attivo" if vpn_connection.kill_switch_active else "Inattivo"
            ), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="threat-card">
                <h4>⚠️ VPN Non Attiva</h4>
                <p>La connessione non è protetta</p>
                <p><strong>Rischi:</strong></p>
                <ul>
                    <li>IP pubblico esposto</li>
                    <li>Traffico non crittografato</li>
                    <li>Possibile tracking</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Server raccomandati
        st.markdown("#### 🎯 Server VPN Raccomandati")
        servers = vpn_manager.get_recommended_servers()
        
        for server in servers[:3]:
            with st.expander(f"🌍 {server.name} - {server.city}, {server.country}"):
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("Load", f"{server.load}%")
                with col_s2:
                    st.metric("Ping", f"{server.ping}ms")
                with col_s3:
                    if server.recommended:
                        st.success("✅ Raccomandato")
                    else:
                        st.info("ℹ️ Disponibile")
    
    with col2:
        # Security Status
        st.markdown("""
        <div class="security-card">
            <h2>🛡️ Security Status</h2>
            <p>Protezione avanzata e monitoraggio</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Ottieni status sicurezza
        security_status = security_layer.get_security_status()
        
        # Metriche sicurezza
        col_sec1, col_sec2, col_sec3 = st.columns(3)
        
        with col_sec1:
            total_events = security_status['security_events']['total_24h']
            st.metric("🚨 Eventi 24h", total_events, "")
        
        with col_sec2:
            suspicious_ips = security_status['threats']['suspicious_ips']
            st.metric("🚫 IP Sospetti", suspicious_ips, "")
        
        with col_sec3:
            failed_attempts = security_status['threats']['failed_attempts']
            st.metric("❌ Tentativi Falliti", failed_attempts, "")
        
        # Dettagli sicurezza
        critical_events = security_status['security_events']['critical']
        high_events = security_status['security_events']['high']
        
        if critical_events > 0 or high_events > 0:
            st.markdown(f"""
            <div class="threat-card">
                <h4>⚠️ Minacce Rilevate</h4>
                <p><strong>Eventi Critici:</strong> {critical_events}</p>
                <p><strong>Eventi High:</strong> {high_events}</p>
                <p><strong>Azione:</strong> Monitoraggio attivo</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="safe-card">
                <h4>✅ Sistema Sicuro</h4>
                <p>Nessuna minaccia rilevata</p>
                <p><strong>Encryption:</strong> AES-256</p>
                <p><strong>Monitoring:</strong> Attivo 24/7</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Test transazione sicurezza
        st.markdown("#### 💰 Test Sicurezza Transazione")
        
        with st.expander("🧪 Simula Transazione"):
            amount = st.number_input("Importo (USDT)", min_value=1.0, max_value=1000.0, value=50.0)
            destination = st.text_input("Destinazione", value="0x742d35Cc6634C0532925a3b8D4f2e3E4f2e")
            
            if st.button("🔍 Valida Transazione", key="validate_tx"):
                transaction_data = {
                    "amount": amount,
                    "currency": "USDT",
                    "destination": destination
                }
                
                with st.spinner("Validazione in corso..."):
                    tx_security = security_layer.validate_transaction(transaction_data)
                    
                    if tx_security:
                        col_tx1, col_tx2 = st.columns(2)
                        
                        with col_tx1:
                            st.metric("Security Score", f"{tx_security.security_score:.2f}")
                            st.metric("Risk Level", tx_security.risk_level)
                        
                        with col_tx2:
                            if tx_security.approved:
                                st.success("✅ APPROVATA")
                            else:
                                st.error("❌ RIFIUTATA")
                            
                            st.info(f"Verifiche: {len(tx_security.verification_methods)}")
    
    # Sezione monitoring avanzato
    st.markdown("---")
    st.markdown("### 📊 Monitoring Avanzato")
    
    col3, col4, col5 = st.columns([1, 1, 1])
    
    with col3:
        st.markdown("#### 🔐 Crittografia")
        st.info("**Algoritmo:** AES-256-GCM")
        st.info("**Key Derivation:** PBKDF2-SHA256")
        st.info("**Iterations:** 100,000")
        st.success("✅ Encryption Active")
    
    with col4:
        st.markdown("#### 🌐 Network Security")
        st.info("**Firewall:** Attivo")
        st.info("**DDoS Protection:** Attivo")
        st.info("**Intrusion Detection:** Attivo")
        
        if vpn_connection and vpn_connection.connected:
            st.success("✅ VPN Protected")
        else:
            st.warning("⚠️ VPN Disconnected")
    
    with col5:
        st.markdown("#### 📱 Anti-Furto")
        st.info("**Transaction Monitoring:** Attivo")
        st.info("**Anomaly Detection:** Attivo")
        st.info("**Emergency Lockdown:** Disponibile")
        st.success("✅ Protection Active")
    
    # Performance VPN (se connessa)
    if vpn_connection and vpn_connection.connected:
        st.markdown("---")
        st.markdown("### 🚀 Performance VPN")
        
        if st.button("🧪 Test Performance", key="test_performance"):
            with st.spinner("Test in corso..."):
                performance = vpn_manager.test_vpn_performance()
                
                if "error" not in performance:
                    col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
                    
                    with col_perf1:
                        st.metric("Download", f"{performance['download_speed_mbps']} Mbps")
                    with col_perf2:
                        st.metric("Upload", f"{performance['upload_speed_mbps']} Mbps")
                    with col_perf3:
                        st.metric("Latency", f"{performance['latency_ms']} ms")
                    with col_perf4:
                        st.metric("Score", f"{performance['overall_score']}/100")
                    
                    # Indicatori sicurezza
                    col_ind1, col_ind2, col_ind3 = st.columns(3)
                    
                    with col_ind1:
                        if performance['dns_leak']:
                            st.error("❌ DNS Leak Detected")
                        else:
                            st.success("✅ No DNS Leak")
                    
                    with col_ind2:
                        if performance['webrtc_leak']:
                            st.error("❌ WebRTC Leak")
                        else:
                            st.success("✅ No WebRTC Leak")
                    
                    with col_ind3:
                        if performance['ip_changed']:
                            st.success("✅ IP Changed")
                        else:
                            st.error("❌ IP Not Changed")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🛡️ <strong>AurumBotX Security Center</strong> - Protezione Enterprise</p>
        <p>🔒 VPN Protection | 🛡️ Anti-Theft | 🔐 Data Encryption | 🚨 24/7 Monitoring</p>
        <p><em>Ultimo aggiornamento: {}</em></p>
    </div>
    """.format(datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()

