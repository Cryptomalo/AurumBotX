#!/usr/bin/env python3
"""
AurumBotX Professional Setup
Setup con cura maniacale per un sistema di trading production-ready
"""

import os
import sys
import asyncio
import logging
import json
import time
import psutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import traceback

class ProfessionalSetup:
    def __init__(self):
        self.setup_time = datetime.now()
        self.setup_logging()
        self.logger = logging.getLogger('ProfessionalSetup')
        self.checks_passed = 0
        self.checks_total = 0
        self.critical_issues = []
        self.warnings = []
        self.optimizations = []
        
    def setup_logging(self):
        """Setup logging professionale"""
        Path('logs').mkdir(exist_ok=True)
        
        # Logger principale con rotazione
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/professional_setup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
    
    def print_header(self, title):
        """Stampa header professionale"""
        print(f"\n{'='*60}")
        print(f"🎯 {title}")
        print(f"{'='*60}")
    
    def print_section(self, title):
        """Stampa sezione"""
        print(f"\n📋 {title}")
        print(f"{'-'*50}")
    
    def check_item(self, description, check_func, critical=True):
        """Esegue un controllo con logging dettagliato"""
        self.checks_total += 1
        try:
            result = check_func()
            if result:
                print(f"  ✅ {description}")
                self.checks_passed += 1
                return True
            else:
                print(f"  ❌ {description}")
                if critical:
                    self.critical_issues.append(description)
                else:
                    self.warnings.append(description)
                return False
        except Exception as e:
            print(f"  💥 {description} - Errore: {str(e)}")
            if critical:
                self.critical_issues.append(f"{description}: {str(e)}")
            else:
                self.warnings.append(f"{description}: {str(e)}")
            return False
    
    def system_health_check(self):
        """Controllo salute sistema completo"""
        self.print_section("CONTROLLO SALUTE SISTEMA")
        
        # CPU e Memoria
        self.check_item(
            f"CPU Usage < 80% (attuale: {psutil.cpu_percent():.1f}%)",
            lambda: psutil.cpu_percent() < 80,
            critical=False
        )
        
        memory = psutil.virtual_memory()
        self.check_item(
            f"Memoria disponibile > 1GB (attuale: {memory.available/1024/1024/1024:.1f}GB)",
            lambda: memory.available > 1024*1024*1024,
            critical=True
        )
        
        # Spazio disco
        disk = psutil.disk_usage('/')
        free_gb = disk.free / 1024 / 1024 / 1024
        self.check_item(
            f"Spazio disco > 5GB (attuale: {free_gb:.1f}GB)",
            lambda: free_gb > 5,
            critical=True
        )
        
        # Connessione internet
        self.check_item(
            "Connessione internet attiva",
            lambda: self.test_internet_connection(),
            critical=True
        )
    
    def test_internet_connection(self):
        """Test connessione internet"""
        try:
            import requests
            response = requests.get('https://api.binance.com/api/v3/ping', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def python_environment_check(self):
        """Controllo ambiente Python"""
        self.print_section("CONTROLLO AMBIENTE PYTHON")
        
        # Versione Python
        python_version = sys.version_info
        self.check_item(
            f"Python >= 3.8 (attuale: {python_version.major}.{python_version.minor})",
            lambda: python_version >= (3, 8),
            critical=True
        )
        
        # Dipendenze critiche
        critical_packages = [
            'pandas', 'numpy', 'asyncio', 'logging', 'ccxt', 
            'psycopg2', 'sqlalchemy', 'scikit-learn', 'requests'
        ]
        
        for package in critical_packages:
            self.check_item(
                f"Pacchetto {package} installato",
                lambda p=package: self.check_package(p),
                critical=True
            )
    
    def check_package(self, package_name):
        """Verifica se un pacchetto è installato"""
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
    
    def aurumbotx_modules_check(self):
        """Controllo moduli AurumBotX"""
        self.print_section("CONTROLLO MODULI AURUMBOTX")
        
        sys.path.append('.')
        
        core_modules = [
            ('utils.ai_trading', 'AITrading'),
            ('utils.data_loader', 'CryptoDataLoader'),
            ('utils.exchange_manager', 'ExchangeManager'),
            ('utils.prediction_model', 'PredictionModel'),
            ('utils.database_manager', 'DatabaseManager'),
            ('utils.sentiment_analyzer', 'SentimentAnalyzer'),
            ('utils.indicators', 'calculate_rsi'),
            ('utils.strategies.swing_trading', 'SwingTradingStrategy'),
            ('utils.strategies.scalping', 'ScalpingStrategy')
        ]
        
        for module_name, class_name in core_modules:
            self.check_item(
                f"Modulo {module_name}.{class_name}",
                lambda m=module_name, c=class_name: self.check_module_class(m, c),
                critical=True
            )
    
    def check_module_class(self, module_name, class_name):
        """Verifica modulo e classe"""
        try:
            module = __import__(module_name, fromlist=[class_name])
            return hasattr(module, class_name)
        except Exception as e:
            self.logger.error(f"Errore import {module_name}.{class_name}: {e}")
            return False
    
    def configuration_check(self):
        """Controllo configurazione"""
        self.print_section("CONTROLLO CONFIGURAZIONE")
        
        # Variabili d'ambiente
        env_vars = [
            'BINANCE_API_KEY',
            'BINANCE_SECRET_KEY', 
            'OPENROUTER_API_KEY',
            'DATABASE_URL'
        ]
        
        for var in env_vars:
            self.check_item(
                f"Variabile ambiente {var}",
                lambda v=var: os.getenv(v) is not None,
                critical=True
            )
        
        # File di configurazione
        config_files = [
            'requirements.txt',
            'README.md',
            'ROADMAP.md',
            'monitor_24_7.py',
            'start_monitor_24_7.sh'
        ]
        
        for file in config_files:
            self.check_item(
                f"File {file}",
                lambda f=file: os.path.exists(f),
                critical=True
            )
    
    def database_connectivity_check(self):
        """Test connettività database"""
        self.print_section("CONTROLLO DATABASE")
        
        try:
            from utils.database_manager import DatabaseManager
            
            # Test connessione
            self.check_item(
                "Connessione database PostgreSQL",
                lambda: self.test_database_connection(),
                critical=True
            )
            
        except Exception as e:
            self.check_item(
                f"Inizializzazione DatabaseManager: {str(e)}",
                lambda: False,
                critical=True
            )
    
    def test_database_connection(self):
        """Test connessione database"""
        try:
            import psycopg2
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                return False
            
            # Parse URL per test connessione
            if db_url.startswith('postgresql://'):
                # Test connessione rapida
                conn = psycopg2.connect(db_url)
                conn.close()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Test database fallito: {e}")
            return False
    
    def binance_api_check(self):
        """Test API Binance"""
        self.print_section("CONTROLLO API BINANCE")
        
        self.check_item(
            "Connessione Binance Testnet",
            lambda: self.test_binance_connection(),
            critical=True
        )
    
    def test_binance_connection(self):
        """Test connessione Binance"""
        try:
            import ccxt
            
            api_key = os.getenv('BINANCE_API_KEY')
            secret_key = os.getenv('BINANCE_SECRET_KEY')
            
            if not api_key or not secret_key:
                return False
            
            exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret_key,
                'sandbox': True,  # Testnet
                'enableRateLimit': True,
            })
            
            # Test semplice
            balance = exchange.fetch_balance()
            return 'USDT' in balance
            
        except Exception as e:
            self.logger.error(f"Test Binance fallito: {e}")
            return False
    
    def performance_optimization(self):
        """Ottimizzazioni performance"""
        self.print_section("OTTIMIZZAZIONI PERFORMANCE")
        
        # Ottimizzazione memoria Python
        try:
            import gc
            gc.collect()
            self.optimizations.append("Garbage collection eseguita")
            print("  ✅ Garbage collection ottimizzata")
        except:
            print("  ⚠️ Garbage collection non ottimizzabile")
        
        # Verifica cache directory
        cache_dirs = ['logs', '__pycache__']
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                self.optimizations.append(f"Directory {cache_dir} presente")
                print(f"  ✅ Directory cache {cache_dir} configurata")
        
        # Ottimizzazione file system
        try:
            # Verifica permessi
            test_file = 'logs/permission_test.tmp'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            self.optimizations.append("Permessi file system verificati")
            print("  ✅ Permessi file system ottimali")
        except:
            print("  ⚠️ Problemi permessi file system")
    
    def create_monitoring_config(self):
        """Crea configurazione monitoraggio avanzata"""
        self.print_section("CONFIGURAZIONE MONITORAGGIO AVANZATO")
        
        config = {
            'monitoring': {
                'cycle_interval': 60,
                'health_check_interval': 300,
                'log_stats_interval': 900,
                'auto_restart_on_error': True,
                'max_consecutive_errors': 5,
                'enable_trading': False,
                'trading_pairs': ['BTCUSDT'],
                'strategies': ['swing_trading']
            },
            'alerts': {
                'cpu_threshold': 80,
                'memory_threshold': 90,
                'error_threshold': 10,
                'confidence_threshold': 0.7
            },
            'performance': {
                'max_latency_ms': 1000,
                'min_uptime_percent': 99.5,
                'target_accuracy_percent': 70
            },
            'setup_info': {
                'setup_time': self.setup_time.isoformat(),
                'checks_passed': self.checks_passed,
                'checks_total': self.checks_total,
                'critical_issues': self.critical_issues,
                'warnings': self.warnings,
                'optimizations': self.optimizations
            }
        }
        
        config_file = 'logs/monitor_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"  ✅ Configurazione salvata in {config_file}")
        return config
    
    def generate_professional_report(self):
        """Genera report professionale"""
        self.print_header("REPORT SETUP PROFESSIONALE")
        
        success_rate = (self.checks_passed / self.checks_total * 100) if self.checks_total > 0 else 0
        
        print(f"📊 STATISTICHE SETUP")
        print(f"   Controlli superati: {self.checks_passed}/{self.checks_total} ({success_rate:.1f}%)")
        print(f"   Problemi critici: {len(self.critical_issues)}")
        print(f"   Warning: {len(self.warnings)}")
        print(f"   Ottimizzazioni: {len(self.optimizations)}")
        
        if self.critical_issues:
            print(f"\n🚨 PROBLEMI CRITICI DA RISOLVERE:")
            for issue in self.critical_issues:
                print(f"   ❌ {issue}")
        
        if self.warnings:
            print(f"\n⚠️ WARNING:")
            for warning in self.warnings:
                print(f"   ⚠️ {warning}")
        
        if self.optimizations:
            print(f"\n🚀 OTTIMIZZAZIONI APPLICATE:")
            for opt in self.optimizations:
                print(f"   ✅ {opt}")
        
        # Raccomandazioni
        print(f"\n💡 RACCOMANDAZIONI:")
        if success_rate >= 90:
            print("   🎉 Sistema pronto per produzione!")
            print("   🚀 Avvio monitoraggio 24/7 raccomandato")
        elif success_rate >= 70:
            print("   ⚠️ Sistema funzionale ma con miglioramenti necessari")
            print("   🔧 Risolvere warning prima del deploy produzione")
        else:
            print("   🚨 Sistema non pronto per produzione")
            print("   🛠️ Risolvere problemi critici prima di procedere")
        
        return success_rate >= 70
    
    async def run_professional_setup(self):
        """Esegue setup professionale completo"""
        self.print_header("AURUMBOTX PROFESSIONAL SETUP")
        print(f"🕐 Avvio: {self.setup_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👨‍💻 Modalità: Cura maniacale professionale")
        
        # Controlli sequenziali
        self.system_health_check()
        self.python_environment_check()
        self.aurumbotx_modules_check()
        self.configuration_check()
        self.database_connectivity_check()
        self.binance_api_check()
        self.performance_optimization()
        
        # Configurazione avanzata
        config = self.create_monitoring_config()
        
        # Report finale
        is_ready = self.generate_professional_report()
        
        return is_ready, config

def main():
    """Main setup professionale"""
    setup = ProfessionalSetup()
    
    try:
        is_ready, config = asyncio.run(setup.run_professional_setup())
        
        if is_ready:
            print(f"\n🎯 SETUP COMPLETATO CON SUCCESSO!")
            print(f"✅ Sistema pronto per monitoraggio 24/7")
            print(f"🚀 Prossimo step: ./start_monitor_24_7.sh background")
        else:
            print(f"\n⚠️ SETUP COMPLETATO CON PROBLEMI")
            print(f"🔧 Risolvere problemi critici prima di procedere")
        
        return 0 if is_ready else 1
        
    except Exception as e:
        print(f"\n💥 ERRORE CRITICO DURANTE SETUP: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

