#!/bin/bash

# AurumBotX - Script Installazione Automatica
# Versione: 2.0
# Data: 29 Agosto 2025

set -e  # Exit on any error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
echo "  ╔═══════════════════════════════════════════════════════════╗"
echo "  ║                    🚀 AURUMBOTX 🚀                        ║"
echo "  ║              Installazione Automatica v2.0               ║"
echo "  ║                                                           ║"
echo "  ║  💰 Sistema Trading Automatico Avanzato                  ║"
echo "  ║  🤖 AI-Powered Trading Bot                               ║"
echo "  ║  📊 Dashboard Multiple Integrate                         ║"
echo "  ║  🛡️ Risk Management Avanzato                            ║"
echo "  ╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Funzioni utility
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verifica sistema operativo
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/debian_version ]; then
            DISTRO="debian"
        elif [ -f /etc/redhat-release ]; then
            DISTRO="redhat"
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        DISTRO="windows"
    else
        OS="unknown"
        DISTRO="unknown"
    fi
    
    log_info "Sistema operativo rilevato: $OS ($DISTRO)"
}

# Verifica prerequisiti
check_prerequisites() {
    log_info "Verifica prerequisiti..."
    
    # Verifica Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python3 trovato: $PYTHON_VERSION"
        
        # Verifica versione Python (minimo 3.8)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            log_success "Versione Python compatibile"
        else
            log_error "Python 3.8+ richiesto. Versione attuale: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python3 non trovato. Installazione necessaria."
        install_python
    fi
    
    # Verifica pip
    if command -v pip3 &> /dev/null; then
        log_success "pip3 trovato"
    else
        log_warning "pip3 non trovato. Installazione..."
        install_pip
    fi
    
    # Verifica git
    if command -v git &> /dev/null; then
        log_success "Git trovato"
    else
        log_warning "Git non trovato. Installazione..."
        install_git
    fi
    
    # Verifica curl/wget
    if command -v curl &> /dev/null; then
        DOWNLOADER="curl -fsSL"
        log_success "curl trovato"
    elif command -v wget &> /dev/null; then
        DOWNLOADER="wget -qO-"
        log_success "wget trovato"
    else
        log_error "curl o wget richiesto"
        exit 1
    fi
}

# Installazione Python (se necessario)
install_python() {
    log_info "Installazione Python3..."
    
    case $DISTRO in
        "debian")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        "redhat")
            sudo yum install -y python3 python3-pip
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install python3
            else
                log_error "Homebrew richiesto su macOS. Installa da: https://brew.sh"
                exit 1
            fi
            ;;
        *)
            log_error "Installazione automatica Python non supportata per questo OS"
            log_info "Installa manualmente Python 3.8+ e riprova"
            exit 1
            ;;
    esac
}

# Installazione pip (se necessario)
install_pip() {
    case $DISTRO in
        "debian")
            sudo apt install -y python3-pip
            ;;
        "redhat")
            sudo yum install -y python3-pip
            ;;
        "macos")
            python3 -m ensurepip --upgrade
            ;;
    esac
}

# Installazione git (se necessario)
install_git() {
    case $DISTRO in
        "debian")
            sudo apt install -y git
            ;;
        "redhat")
            sudo yum install -y git
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install git
            else
                log_error "Installa Git manualmente su macOS"
                exit 1
            fi
            ;;
    esac
}

# Download AurumBotX
download_aurumbotx() {
    log_info "Download AurumBotX..."
    
    # Determina directory installazione
    INSTALL_DIR="$HOME/AurumBotX"
    
    if [ -d "$INSTALL_DIR" ]; then
        log_warning "Directory $INSTALL_DIR già esistente"
        read -p "Sovrascrivere? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installazione annullata"
            exit 0
        fi
        rm -rf "$INSTALL_DIR"
    fi
    
    # Clone repository
    log_info "Cloning repository..."
    git clone https://github.com/Cryptomalo/AurumBotX.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    log_success "AurumBotX scaricato in: $INSTALL_DIR"
}

# Setup ambiente virtuale
setup_virtual_environment() {
    log_info "Setup ambiente virtuale Python..."
    
    # Crea ambiente virtuale
    python3 -m venv aurumbotx_env
    
    # Attiva ambiente virtuale
    source aurumbotx_env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_success "Ambiente virtuale creato e attivato"
}

# Installazione dipendenze
install_dependencies() {
    log_info "Installazione dipendenze Python..."
    
    # Assicurati che l'ambiente virtuale sia attivo
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        source aurumbotx_env/bin/activate
    fi
    
    # Installa dipendenze base
    pip install -r requirements.txt
    
    # Installa dipendenze aggiuntive per dashboard
    pip install streamlit plotly pandas numpy sqlite3
    
    # Installa dipendenze per trading
    pip install python-binance ccxt requests aiohttp
    
    # Installa dipendenze per AI
    pip install scikit-learn tensorflow keras
    
    log_success "Dipendenze installate"
}

# Setup configurazione
setup_configuration() {
    log_info "Setup configurazione..."
    
    # Crea directory config se non esiste
    mkdir -p config
    mkdir -p logs
    mkdir -p data
    mkdir -p backups
    
    # Crea file configurazione base
    cat > config/config.json << EOF
{
  "trading": {
    "mode": "testnet",
    "exchange": "binance",
    "api_key": "",
    "api_secret": "",
    "initial_balance": 1000.0,
    "max_position_size": 0.20,
    "risk_per_trade": 0.02
  },
  "strategies": {
    "active_strategy": "mega_aggressive",
    "volatility_threshold": 0.02,
    "confidence_threshold": 0.30,
    "profit_target_range": [0.01, 0.04],
    "stop_loss_range": [0.005, 0.02]
  },
  "monitoring": {
    "enable_dashboard": true,
    "dashboard_port": 8501,
    "enable_logging": true,
    "log_level": "INFO",
    "enable_notifications": false
  },
  "security": {
    "enable_2fa": false,
    "max_daily_loss": 0.05,
    "emergency_stop": true,
    "whitelist_ips": []
  }
}
EOF
    
    log_success "Configurazione base creata"
}

# Setup database
setup_database() {
    log_info "Inizializzazione database..."
    
    # Assicurati che l'ambiente virtuale sia attivo
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        source aurumbotx_env/bin/activate
    fi
    
    # Crea script setup database se non esiste
    cat > setup_database.py << 'EOF'
#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

def setup_databases():
    """Setup tutti i database necessari"""
    
    databases = [
        'mega_aggressive_trading.db',
        'ultra_aggressive_trading.db', 
        'mainnet_optimization.db',
        'system_monitoring.db'
    ]
    
    for db_name in databases:
        print(f"Inizializzazione {db_name}...")
        
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Tabella trade generica
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                strategy TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                profit_loss REAL NOT NULL,
                fee REAL NOT NULL,
                balance_after REAL NOT NULL,
                confidence REAL NOT NULL,
                volatility REAL NOT NULL
            )
        ''')
        
        # Tabella configurazioni
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Inserisci configurazione iniziale
        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', ('initialized', 'true', datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ {db_name} inizializzato")
    
    print("🎉 Tutti i database inizializzati con successo!")

if __name__ == "__main__":
    setup_databases()
EOF
    
    # Esegui setup database
    python3 setup_database.py
    
    log_success "Database inizializzati"
}

# Crea script di avvio
create_launch_scripts() {
    log_info "Creazione script di avvio..."
    
    # Script avvio principale
    cat > start_aurumbotx.sh << 'EOF'
#!/bin/bash

# AurumBotX - Script Avvio Principale

echo "🚀 Avvio AurumBotX..."

# Attiva ambiente virtuale
source aurumbotx_env/bin/activate

# Verifica configurazione
if [ ! -f "config/config.json" ]; then
    echo "❌ File configurazione non trovato!"
    echo "💡 Modifica config/config.json con le tue API keys"
    exit 1
fi

# Avvia componenti in background
echo "📊 Avvio dashboard..."
nohup streamlit run admin_dashboard.py --server.port=8501 > logs/admin_dashboard.log 2>&1 &
nohup streamlit run visual_performance_dashboard.py --server.port=8503 > logs/performance_dashboard.log 2>&1 &
nohup streamlit run mobile_web_app.py --server.port=8505 > logs/mobile_dashboard.log 2>&1 &

sleep 5

echo "🤖 Avvio trading engine..."
nohup python3 mega_aggressive_trading.py > logs/trading_engine.log 2>&1 &

echo "📈 Avvio sistema ottimizzazione..."
nohup python3 mainnet_optimization_strategies.py > logs/optimization.log 2>&1 &

echo ""
echo "✅ AurumBotX avviato con successo!"
echo ""
echo "📊 Dashboard disponibili:"
echo "   🔧 Admin: http://localhost:8501"
echo "   📈 Performance: http://localhost:8503"
echo "   📱 Mobile: http://localhost:8505"
echo ""
echo "📋 Comandi utili:"
echo "   ./stop_aurumbotx.sh    - Ferma tutto"
echo "   ./status_aurumbotx.sh  - Controlla status"
echo "   tail -f logs/*.log     - Visualizza logs"
echo ""
EOF
    
    # Script stop
    cat > stop_aurumbotx.sh << 'EOF'
#!/bin/bash

echo "🛑 Fermando AurumBotX..."

# Ferma processi Python
pkill -f "mega_aggressive_trading.py"
pkill -f "mainnet_optimization_strategies.py"
pkill -f "streamlit"

echo "✅ AurumBotX fermato"
EOF
    
    # Script status
    cat > status_aurumbotx.sh << 'EOF'
#!/bin/bash

echo "📊 Status AurumBotX"
echo "=================="

echo ""
echo "🤖 Trading Engines:"
if pgrep -f "mega_aggressive_trading.py" > /dev/null; then
    echo "   ✅ Mega Aggressive Trading: ATTIVO"
else
    echo "   ❌ Mega Aggressive Trading: INATTIVO"
fi

if pgrep -f "mainnet_optimization_strategies.py" > /dev/null; then
    echo "   ✅ Mainnet Optimization: ATTIVO"
else
    echo "   ❌ Mainnet Optimization: INATTIVO"
fi

echo ""
echo "📊 Dashboard:"
if pgrep -f "streamlit.*8501" > /dev/null; then
    echo "   ✅ Admin Dashboard (8501): ATTIVO"
else
    echo "   ❌ Admin Dashboard (8501): INATTIVO"
fi

if pgrep -f "streamlit.*8503" > /dev/null; then
    echo "   ✅ Performance Dashboard (8503): ATTIVO"
else
    echo "   ❌ Performance Dashboard (8503): INATTIVO"
fi

if pgrep -f "streamlit.*8505" > /dev/null; then
    echo "   ✅ Mobile Dashboard (8505): ATTIVO"
else
    echo "   ❌ Mobile Dashboard (8505): INATTIVO"
fi

echo ""
echo "💾 Database:"
for db in *.db; do
    if [ -f "$db" ]; then
        size=$(du -h "$db" | cut -f1)
        echo "   📁 $db: $size"
    fi
done

echo ""
echo "📋 Logs recenti:"
if [ -d "logs" ]; then
    ls -la logs/*.log 2>/dev/null | tail -5
fi
EOF
    
    # Rendi eseguibili
    chmod +x start_aurumbotx.sh
    chmod +x stop_aurumbotx.sh
    chmod +x status_aurumbotx.sh
    
    log_success "Script di avvio creati"
}

# Test installazione
test_installation() {
    log_info "Test installazione..."
    
    # Attiva ambiente virtuale
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        source aurumbotx_env/bin/activate
    fi
    
    # Crea script test
    cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
import sys
import sqlite3
import json
import os

def test_python_version():
    """Test versione Python"""
    if sys.version_info >= (3, 8):
        print("✅ Python version OK:", sys.version)
        return True
    else:
        print("❌ Python version troppo vecchia:", sys.version)
        return False

def test_dependencies():
    """Test dipendenze"""
    required_modules = [
        'sqlite3', 'json', 'datetime', 'logging',
        'pandas', 'numpy', 'streamlit'
    ]
    
    failed = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed.append(module)
    
    return len(failed) == 0

def test_configuration():
    """Test configurazione"""
    if os.path.exists('config/config.json'):
        try:
            with open('config/config.json', 'r') as f:
                config = json.load(f)
            print("✅ Configurazione caricata")
            return True
        except Exception as e:
            print(f"❌ Errore configurazione: {e}")
            return False
    else:
        print("❌ File configurazione non trovato")
        return False

def test_databases():
    """Test database"""
    db_files = ['mega_aggressive_trading.db', 'mainnet_optimization.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                print(f"✅ {db_file}: {len(tables)} tabelle")
            except Exception as e:
                print(f"❌ {db_file}: {e}")
                return False
        else:
            print(f"⚠️ {db_file}: Non trovato (verrà creato al primo avvio)")
    
    return True

def main():
    print("🧪 Test Installazione AurumBotX")
    print("=" * 40)
    
    tests = [
        ("Versione Python", test_python_version),
        ("Dipendenze", test_dependencies),
        ("Configurazione", test_configuration),
        ("Database", test_databases)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ Test fallito: {test_name}")
    
    print(f"\n📊 Risultati: {passed}/{total} test superati")
    
    if passed == total:
        print("🎉 Installazione completata con successo!")
        print("\n🚀 Prossimi step:")
        print("1. Modifica config/config.json con le tue API keys")
        print("2. Esegui: ./start_aurumbotx.sh")
        print("3. Apri: http://localhost:8501")
        return True
    else:
        print("❌ Installazione incompleta. Controlla gli errori sopra.")
        return False

if __name__ == "__main__":
    main()
EOF
    
    # Esegui test
    python3 test_installation.py
    
    log_success "Test installazione completato"
}

# Funzione principale
main() {
    echo -e "${CYAN}Inizio installazione AurumBotX...${NC}"
    echo ""
    
    # Step installazione
    detect_os
    check_prerequisites
    download_aurumbotx
    setup_virtual_environment
    install_dependencies
    setup_configuration
    setup_database
    create_launch_scripts
    test_installation
    
    echo ""
    echo -e "${GREEN}🎉 INSTALLAZIONE COMPLETATA CON SUCCESSO! 🎉${NC}"
    echo ""
    echo -e "${YELLOW}📋 PROSSIMI STEP:${NC}"
    echo "1. 🔑 Configura API Binance Testnet:"
    echo "   - Vai su: https://testnet.binance.vision/"
    echo "   - Crea account e genera API keys"
    echo "   - Modifica: config/config.json"
    echo ""
    echo "2. 🚀 Avvia AurumBotX:"
    echo "   ./start_aurumbotx.sh"
    echo ""
    echo "3. 📊 Accedi alle dashboard:"
    echo "   🔧 Admin: http://localhost:8501"
    echo "   📈 Performance: http://localhost:8503"
    echo "   📱 Mobile: http://localhost:8505"
    echo ""
    echo "4. 📋 Comandi utili:"
    echo "   ./status_aurumbotx.sh  - Controlla status"
    echo "   ./stop_aurumbotx.sh    - Ferma sistema"
    echo "   tail -f logs/*.log     - Visualizza logs"
    echo ""
    echo -e "${PURPLE}💎 AurumBotX è pronto per il trading automatico! 💎${NC}"
}

# Esegui installazione
main "$@"

