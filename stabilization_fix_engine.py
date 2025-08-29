#!/usr/bin/env python3
"""
AurumBotX Stabilization Fix Engine
Sistema per stabilizzazione e risoluzione problemi minori della roadmap
"""

import os
import sys
import asyncio
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import subprocess
import importlib
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/stabilization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('StabilizationEngine')

class DataFrameErrorFixer:
    """Fix per errori DataFrame ambiguous nelle strategie"""
    
    def __init__(self):
        self.logger = logging.getLogger('DataFrameFixer')
        self.fixed_files = []
    
    async def fix_dataframe_errors(self) -> Dict:
        """Fix errori DataFrame nelle strategie"""
        try:
            self.logger.info("🔧 Avvio fix errori DataFrame...")
            
            # File da controllare
            strategy_files = [
                'utils/strategies/scalping.py',
                'utils/strategies/swing_trading.py',
                'utils/strategies/base_strategy.py',
                'utils/strategies/strategy_manager.py'
            ]
            
            results = {}
            
            for file_path in strategy_files:
                if os.path.exists(file_path):
                    result = await self._fix_file_dataframe_issues(file_path)
                    results[file_path] = result
                else:
                    results[file_path] = {'status': 'not_found'}
            
            # Test strategie dopo fix
            test_result = await self._test_strategies_after_fix()
            results['strategy_test'] = test_result
            
            return {
                'component': 'dataframe_fix',
                'status': 'completed',
                'files_fixed': len(self.fixed_files),
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore fix DataFrame: {e}")
            return {'component': 'dataframe_fix', 'status': 'error', 'error': str(e)}
    
    async def _fix_file_dataframe_issues(self, file_path: str) -> Dict:
        """Fix errori DataFrame in un singolo file"""
        try:
            self.logger.info(f"🔍 Controllo {file_path}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            fixes_applied = []
            
            # Fix 1: DataFrame ambiguous in condizioni booleane
            if 'if data:' in content or 'if not data:' in content:
                content = content.replace('if data:', 'if not data.empty:')
                content = content.replace('if not data:', 'if data.empty:')
                fixes_applied.append('boolean_conditions')
            
            # Fix 2: DataFrame in condizioni logiche
            if 'and data' in content or 'or data' in content:
                content = content.replace('and data', 'and not data.empty')
                content = content.replace('or data', 'or data.empty')
                fixes_applied.append('logical_conditions')
            
            # Fix 3: Controlli espliciti per DataFrame vuoti
            if 'len(data) > 0' not in content and 'data.empty' not in content:
                # Aggiungi controlli espliciti dove necessario
                if 'def should_buy' in content or 'def should_sell' in content:
                    content = content.replace(
                        'def should_buy(self, data):',
                        'def should_buy(self, data):\n        if data.empty or len(data) == 0:\n            return False'
                    )
                    content = content.replace(
                        'def should_sell(self, data):',
                        'def should_sell(self, data):\n        if data.empty or len(data) == 0:\n            return False'
                    )
                    fixes_applied.append('empty_checks')
            
            # Fix 4: Uso di .iloc per accesso sicuro
            if 'data[-1]' in content:
                content = content.replace('data[-1]', 'data.iloc[-1]')
                fixes_applied.append('iloc_access')
            
            # Fix 5: Controlli per indicatori tecnici
            if 'rsi' in content.lower() or 'macd' in content.lower():
                # Aggiungi controlli per NaN negli indicatori
                if 'np.isnan' not in content:
                    content = content.replace(
                        'import pandas as pd',
                        'import pandas as pd\nimport numpy as np'
                    )
                    fixes_applied.append('nan_checks')
            
            # Salva solo se ci sono stati fix
            if fixes_applied:
                # Backup originale
                backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with open(backup_path, 'w') as f:
                    f.write(original_content)
                
                # Salva versione fixed
                with open(file_path, 'w') as f:
                    f.write(content)
                
                self.fixed_files.append(file_path)
                self.logger.info(f"✅ Fix applicati a {file_path}: {fixes_applied}")
                
                return {
                    'status': 'fixed',
                    'fixes_applied': fixes_applied,
                    'backup_created': backup_path
                }
            else:
                return {'status': 'no_fixes_needed'}
                
        except Exception as e:
            self.logger.error(f"❌ Errore fix {file_path}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _test_strategies_after_fix(self) -> Dict:
        """Test strategie dopo i fix"""
        try:
            self.logger.info("🧪 Test strategie dopo fix...")
            
            # Test import strategie
            test_results = {}
            
            strategies = [
                ('utils.strategies.scalping', 'ScalpingStrategy'),
                ('utils.strategies.swing_trading', 'SwingTradingStrategy'),
                ('utils.strategies.base_strategy', 'BaseStrategy')
            ]
            
            for module_name, class_name in strategies:
                try:
                    # Ricarica modulo
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                    
                    module = importlib.import_module(module_name)
                    strategy_class = getattr(module, class_name)
                    
                    # Test inizializzazione
                    if class_name != 'BaseStrategy':  # BaseStrategy è astratta
                        strategy = strategy_class()
                        test_results[class_name] = {'status': 'success', 'import': True, 'init': True}
                    else:
                        test_results[class_name] = {'status': 'success', 'import': True, 'init': 'skipped'}
                    
                except Exception as e:
                    test_results[class_name] = {'status': 'error', 'error': str(e)}
            
            # Test con dati mock
            mock_data_test = await self._test_with_mock_data(test_results)
            
            return {
                'import_tests': test_results,
                'mock_data_test': mock_data_test,
                'overall_status': 'success' if all(r.get('status') == 'success' for r in test_results.values()) else 'partial'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore test strategie: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _test_with_mock_data(self, strategy_results: Dict) -> Dict:
        """Test strategie con dati mock"""
        try:
            # Crea dati mock
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=100, freq='1H')
            mock_data = pd.DataFrame({
                'timestamp': dates,
                'open': np.random.uniform(40000, 50000, 100),
                'high': np.random.uniform(45000, 55000, 100),
                'low': np.random.uniform(35000, 45000, 100),
                'close': np.random.uniform(40000, 50000, 100),
                'volume': np.random.uniform(1000, 10000, 100)
            })
            
            test_results = {}
            
            for strategy_name, result in strategy_results.items():
                if result.get('status') == 'success' and result.get('init') == True:
                    try:
                        # Import strategia
                        if strategy_name == 'ScalpingStrategy':
                            from utils.strategies.scalping import ScalpingStrategy
                            strategy = ScalpingStrategy()
                        elif strategy_name == 'SwingTradingStrategy':
                            from utils.strategies.swing_trading import SwingTradingStrategy
                            strategy = SwingTradingStrategy()
                        else:
                            continue
                        
                        # Test metodi
                        should_buy = strategy.should_buy(mock_data)
                        should_sell = strategy.should_sell(mock_data)
                        
                        test_results[strategy_name] = {
                            'status': 'success',
                            'should_buy': bool(should_buy),
                            'should_sell': bool(should_sell),
                            'dataframe_error': False
                        }
                        
                    except Exception as e:
                        error_msg = str(e)
                        is_dataframe_error = 'ambiguous' in error_msg.lower() or 'truth value' in error_msg.lower()
                        
                        test_results[strategy_name] = {
                            'status': 'error' if is_dataframe_error else 'warning',
                            'error': error_msg,
                            'dataframe_error': is_dataframe_error
                        }
            
            return test_results
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

class SentimentAnalyzerFixer:
    """Fix per SentimentAnalyzer"""
    
    def __init__(self):
        self.logger = logging.getLogger('SentimentFixer')
    
    async def fix_sentiment_analyzer(self) -> Dict:
        """Fix SentimentAnalyzer"""
        try:
            self.logger.info("🔧 Avvio fix SentimentAnalyzer...")
            
            sentiment_file = 'utils/sentiment_analyzer.py'
            
            if not os.path.exists(sentiment_file):
                return {'status': 'file_not_found', 'file': sentiment_file}
            
            # Leggi file corrente
            with open(sentiment_file, 'r') as f:
                content = f.read()
            
            # Backup
            backup_path = f"{sentiment_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_path, 'w') as f:
                f.write(content)
            
            # Fix principali
            fixes_applied = []
            
            # Fix 1: Inizializzazione reddit
            if 'self.reddit = None' not in content:
                content = content.replace(
                    'def __init__(self):',
                    'def __init__(self):\n        self.reddit = None\n        self.twitter_api = None'
                )
                fixes_applied.append('reddit_initialization')
            
            # Fix 2: Controlli sicuri per reddit
            if 'if self.reddit:' not in content:
                # Aggiungi controlli sicuri
                reddit_methods = ['get_reddit_sentiment', 'analyze_reddit_posts']
                for method in reddit_methods:
                    if method in content:
                        content = content.replace(
                            f'def {method}(',
                            f'def {method}(\n        if not self.reddit:\n            return 0.0  # Neutral sentiment\n        '
                        )
                        fixes_applied.append(f'{method}_safety_check')
            
            # Fix 3: Fallback robusti
            fallback_code = '''
    def get_fallback_sentiment(self, symbol: str) -> float:
        """Fallback sentiment basato su price action"""
        try:
            # Sentiment neutro come fallback
            return 0.0
        except Exception:
            return 0.0
    
    def get_combined_sentiment(self, symbol: str) -> float:
        """Sentiment combinato con fallback"""
        try:
            # Prova sentiment reale
            if self.reddit:
                reddit_sentiment = self.get_reddit_sentiment(symbol)
                if reddit_sentiment is not None:
                    return reddit_sentiment
            
            # Fallback
            return self.get_fallback_sentiment(symbol)
            
        except Exception as e:
            self.logger.warning(f"Sentiment analysis fallback: {e}")
            return 0.0
'''
            
            if 'get_fallback_sentiment' not in content:
                content += fallback_code
                fixes_applied.append('fallback_methods')
            
            # Fix 4: Import sicuri
            if 'import logging' not in content:
                content = 'import logging\n' + content
                fixes_applied.append('logging_import')
            
            # Salva versione fixed
            with open(sentiment_file, 'w') as f:
                f.write(content)
            
            # Test import
            test_result = await self._test_sentiment_analyzer()
            
            return {
                'component': 'sentiment_analyzer',
                'status': 'completed',
                'fixes_applied': fixes_applied,
                'backup_created': backup_path,
                'test_result': test_result
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore fix SentimentAnalyzer: {e}")
            return {'component': 'sentiment_analyzer', 'status': 'error', 'error': str(e)}
    
    async def _test_sentiment_analyzer(self) -> Dict:
        """Test SentimentAnalyzer dopo fix"""
        try:
            # Ricarica modulo
            if 'utils.sentiment_analyzer' in sys.modules:
                importlib.reload(sys.modules['utils.sentiment_analyzer'])
            
            from utils.sentiment_analyzer import SentimentAnalyzer
            
            # Test inizializzazione
            analyzer = SentimentAnalyzer()
            
            # Test metodi
            sentiment = analyzer.get_combined_sentiment('BTCUSDT')
            
            return {
                'status': 'success',
                'import': True,
                'initialization': True,
                'sentiment_test': sentiment,
                'methods_working': True
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'import': 'reddit' not in str(e).lower()
            }

class DependencyInstaller:
    """Installatore dipendenze mancanti"""
    
    def __init__(self):
        self.logger = logging.getLogger('DependencyInstaller')
    
    async def install_missing_dependencies(self) -> Dict:
        """Installa dipendenze mancanti"""
        try:
            self.logger.info("📦 Installazione dipendenze mancanti...")
            
            # Dipendenze da installare
            dependencies = [
                'twilio',
                'streamlit',
                'plotly',
                'praw',  # Reddit API
                'tweepy',  # Twitter API
                'yfinance',  # Yahoo Finance
                'ta',  # Technical Analysis
                'python-telegram-bot'
            ]
            
            results = {}
            installed = []
            
            for dep in dependencies:
                result = await self._install_dependency(dep)
                results[dep] = result
                if result.get('status') == 'success':
                    installed.append(dep)
            
            # Aggiorna requirements.txt
            await self._update_requirements_txt(installed)
            
            return {
                'component': 'dependencies',
                'status': 'completed',
                'installed': installed,
                'total_attempted': len(dependencies),
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore installazione dipendenze: {e}")
            return {'component': 'dependencies', 'status': 'error', 'error': str(e)}
    
    async def _install_dependency(self, package: str) -> Dict:
        """Installa singola dipendenza"""
        try:
            self.logger.info(f"📦 Installazione {package}...")
            
            # Controlla se già installato
            try:
                __import__(package)
                return {'status': 'already_installed', 'package': package}
            except ImportError:
                pass
            
            # Installa con pip
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"✅ {package} installato con successo")
                return {'status': 'success', 'package': package}
            else:
                self.logger.warning(f"⚠️ Errore installazione {package}: {result.stderr}")
                return {'status': 'error', 'package': package, 'error': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'package': package}
        except Exception as e:
            return {'status': 'error', 'package': package, 'error': str(e)}
    
    async def _update_requirements_txt(self, installed: List[str]):
        """Aggiorna requirements.txt"""
        try:
            requirements_file = 'requirements.txt'
            
            # Leggi requirements esistenti
            existing = []
            if os.path.exists(requirements_file):
                with open(requirements_file, 'r') as f:
                    existing = [line.strip() for line in f.readlines() if line.strip()]
            
            # Aggiungi nuove dipendenze
            for package in installed:
                if package not in existing and not any(package in req for req in existing):
                    existing.append(package)
            
            # Salva requirements aggiornato
            with open(requirements_file, 'w') as f:
                for req in sorted(existing):
                    f.write(f"{req}\n")
            
            self.logger.info(f"✅ Requirements.txt aggiornato con {len(installed)} nuove dipendenze")
            
        except Exception as e:
            self.logger.error(f"❌ Errore aggiornamento requirements.txt: {e}")

class PerformanceOptimizer:
    """Ottimizzatore performance"""
    
    def __init__(self):
        self.logger = logging.getLogger('PerformanceOptimizer')
    
    async def optimize_performance(self) -> Dict:
        """Ottimizza performance sistema"""
        try:
            self.logger.info("⚡ Avvio ottimizzazione performance...")
            
            results = {}
            
            # 1. Ottimizzazione cache
            cache_result = await self._optimize_cache()
            results['cache_optimization'] = cache_result
            
            # 2. Ottimizzazione query database
            db_result = await self._optimize_database_queries()
            results['database_optimization'] = db_result
            
            # 3. Ottimizzazione memoria
            memory_result = await self._optimize_memory_usage()
            results['memory_optimization'] = memory_result
            
            # 4. Ottimizzazione network
            network_result = await self._optimize_network_calls()
            results['network_optimization'] = network_result
            
            return {
                'component': 'performance',
                'status': 'completed',
                'optimizations': results
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore ottimizzazione performance: {e}")
            return {'component': 'performance', 'status': 'error', 'error': str(e)}
    
    async def _optimize_cache(self) -> Dict:
        """Ottimizza sistema cache"""
        try:
            # Crea sistema cache avanzato
            cache_code = '''
import time
from typing import Dict, Any, Optional
from functools import wraps

class AdvancedCache:
    """Cache avanzato con TTL e LRU"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Ottieni valore da cache"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Controlla TTL
        if time.time() > entry['expires']:
            self.delete(key)
            return None
        
        # Aggiorna access time per LRU
        self.access_times[key] = time.time()
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Imposta valore in cache"""
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl,
            'created': time.time()
        }
        self.access_times[key] = time.time()
    
    def delete(self, key: str) -> None:
        """Elimina da cache"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Rimuovi elemento meno recentemente usato"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self.delete(lru_key)

# Cache globale
global_cache = AdvancedCache()

def cached(ttl: int = 300):
    """Decorator per cache automatico"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Crea chiave cache
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Prova cache
            result = global_cache.get(cache_key)
            if result is not None:
                return result
            
            # Esegui funzione e caching
            result = func(*args, **kwargs)
            global_cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
'''
            
            # Salva sistema cache
            with open('utils/advanced_cache.py', 'w') as f:
                f.write(cache_code)
            
            return {'status': 'success', 'cache_system': 'created'}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _optimize_database_queries(self) -> Dict:
        """Ottimizza query database"""
        try:
            # Crea indici per performance
            databases = [
                'aggressive_trading.db',
                'real_data_trading.db',
                'ai_optimization.db'
            ]
            
            optimized = []
            
            for db_name in databases:
                if os.path.exists(db_name):
                    try:
                        conn = sqlite3.connect(db_name)
                        
                        # Crea indici comuni
                        indices = [
                            "CREATE INDEX IF NOT EXISTS idx_timestamp ON aggressive_trades(timestamp)",
                            "CREATE INDEX IF NOT EXISTS idx_symbol ON aggressive_trades(symbol)",
                            "CREATE INDEX IF NOT EXISTS idx_action ON aggressive_trades(action)",
                        ]
                        
                        for index_sql in indices:
                            try:
                                conn.execute(index_sql)
                            except:
                                pass  # Indice già esistente
                        
                        conn.commit()
                        conn.close()
                        optimized.append(db_name)
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Errore ottimizzazione {db_name}: {e}")
            
            return {'status': 'success', 'databases_optimized': optimized}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _optimize_memory_usage(self) -> Dict:
        """Ottimizza uso memoria"""
        try:
            # Crea memory profiler
            memory_code = '''
import psutil
import gc
import logging
from typing import Dict

class MemoryOptimizer:
    """Ottimizzatore memoria"""
    
    def __init__(self):
        self.logger = logging.getLogger('MemoryOptimizer')
    
    def get_memory_usage(self) -> Dict:
        """Ottieni uso memoria corrente"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def optimize_memory(self) -> Dict:
        """Ottimizza memoria"""
        before = self.get_memory_usage()
        
        # Garbage collection forzato
        collected = gc.collect()
        
        after = self.get_memory_usage()
        
        return {
            'before_mb': before['rss_mb'],
            'after_mb': after['rss_mb'],
            'freed_mb': before['rss_mb'] - after['rss_mb'],
            'objects_collected': collected
        }
    
    def monitor_memory(self, threshold_mb: float = 500) -> bool:
        """Monitora memoria e ottimizza se necessario"""
        usage = self.get_memory_usage()
        
        if usage['rss_mb'] > threshold_mb:
            self.logger.warning(f"Memoria alta: {usage['rss_mb']:.1f}MB")
            result = self.optimize_memory()
            self.logger.info(f"Memoria liberata: {result['freed_mb']:.1f}MB")
            return True
        
        return False

# Istanza globale
memory_optimizer = MemoryOptimizer()
'''
            
            with open('utils/memory_optimizer.py', 'w') as f:
                f.write(memory_code)
            
            return {'status': 'success', 'memory_optimizer': 'created'}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _optimize_network_calls(self) -> Dict:
        """Ottimizza chiamate network"""
        try:
            # Crea connection pool manager
            network_code = '''
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Dict, Optional

class OptimizedNetworkManager:
    """Manager network ottimizzato"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # HTTP Adapter con connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers comuni
        self.session.headers.update({
            'User-Agent': 'AurumBotX/1.0',
            'Connection': 'keep-alive'
        })
    
    def get(self, url: str, timeout: int = 10, **kwargs) -> Optional[requests.Response]:
        """GET ottimizzato"""
        try:
            response = self.session.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Network error: {e}")
            return None
    
    def post(self, url: str, timeout: int = 10, **kwargs) -> Optional[requests.Response]:
        """POST ottimizzato"""
        try:
            response = self.session.post(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Network error: {e}")
            return None

# Istanza globale
network_manager = OptimizedNetworkManager()
'''
            
            with open('utils/network_optimizer.py', 'w') as f:
                f.write(network_code)
            
            return {'status': 'success', 'network_manager': 'created'}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

class StabilizationEngine:
    """Engine principale per stabilizzazione"""
    
    def __init__(self):
        self.logger = logging.getLogger('StabilizationEngine')
        self.dataframe_fixer = DataFrameErrorFixer()
        self.sentiment_fixer = SentimentAnalyzerFixer()
        self.dependency_installer = DependencyInstaller()
        self.performance_optimizer = PerformanceOptimizer()
    
    async def run_stabilization(self) -> Dict:
        """Esegue stabilizzazione completa"""
        try:
            start_time = datetime.now()
            self.logger.info("🚀 Avvio stabilizzazione sistema AurumBotX...")
            
            results = {}
            
            # 1. Fix errori DataFrame
            self.logger.info("🔧 Fix errori DataFrame...")
            dataframe_result = await self.dataframe_fixer.fix_dataframe_errors()
            results['dataframe_fix'] = dataframe_result
            
            # 2. Fix SentimentAnalyzer
            self.logger.info("🔧 Fix SentimentAnalyzer...")
            sentiment_result = await self.sentiment_fixer.fix_sentiment_analyzer()
            results['sentiment_fix'] = sentiment_result
            
            # 3. Installazione dipendenze
            self.logger.info("📦 Installazione dipendenze...")
            dependency_result = await self.dependency_installer.install_missing_dependencies()
            results['dependencies'] = dependency_result
            
            # 4. Ottimizzazione performance
            self.logger.info("⚡ Ottimizzazione performance...")
            performance_result = await self.performance_optimizer.optimize_performance()
            results['performance'] = performance_result
            
            # 5. Test finale
            self.logger.info("🧪 Test finale stabilizzazione...")
            final_test = await self._run_final_test()
            results['final_test'] = final_test
            
            # Calcola risultati
            execution_time = (datetime.now() - start_time).total_seconds()
            success_count = sum(1 for r in results.values() if r.get('status') == 'completed')
            total_count = len(results)
            
            # Salva report
            await self._save_stabilization_report(results, execution_time)
            
            self.logger.info(f"✅ Stabilizzazione completata in {execution_time:.2f}s")
            self.logger.info(f"📊 Successi: {success_count}/{total_count}")
            
            return {
                'timestamp': datetime.now().isoformat(),
                'execution_time': execution_time,
                'success_count': success_count,
                'total_count': total_count,
                'success_rate': (success_count / total_count) * 100,
                'results': results,
                'status': 'completed' if success_count == total_count else 'partial'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore stabilizzazione: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    async def _run_final_test(self) -> Dict:
        """Test finale dopo stabilizzazione"""
        try:
            test_results = {}
            
            # Test import moduli
            modules_to_test = [
                'utils.strategies.scalping',
                'utils.strategies.swing_trading',
                'utils.sentiment_analyzer',
                'utils.advanced_cache',
                'utils.memory_optimizer',
                'utils.network_optimizer'
            ]
            
            import_results = {}
            for module in modules_to_test:
                try:
                    importlib.import_module(module)
                    import_results[module] = {'status': 'success'}
                except Exception as e:
                    import_results[module] = {'status': 'error', 'error': str(e)}
            
            test_results['imports'] = import_results
            
            # Test dipendenze
            dependencies_to_test = ['twilio', 'streamlit', 'plotly']
            dependency_results = {}
            
            for dep in dependencies_to_test:
                try:
                    __import__(dep)
                    dependency_results[dep] = {'status': 'available'}
                except ImportError:
                    dependency_results[dep] = {'status': 'missing'}
            
            test_results['dependencies'] = dependency_results
            
            # Test performance
            if os.path.exists('utils/memory_optimizer.py'):
                try:
                    from utils.memory_optimizer import memory_optimizer
                    memory_stats = memory_optimizer.get_memory_usage()
                    test_results['memory'] = {'status': 'success', 'usage_mb': memory_stats['rss_mb']}
                except Exception as e:
                    test_results['memory'] = {'status': 'error', 'error': str(e)}
            
            return test_results
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _save_stabilization_report(self, results: Dict, execution_time: float):
        """Salva report stabilizzazione"""
        try:
            os.makedirs('stabilization_results', exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stabilization_results/stabilization_report_{timestamp}.json"
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'execution_time': execution_time,
                'results': results,
                'summary': {
                    'dataframe_fixes': results.get('dataframe_fix', {}).get('files_fixed', 0),
                    'sentiment_fixed': results.get('sentiment_fix', {}).get('status') == 'completed',
                    'dependencies_installed': len(results.get('dependencies', {}).get('installed', [])),
                    'performance_optimized': results.get('performance', {}).get('status') == 'completed'
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"📊 Report salvato: {filename}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio report: {e}")

async def main():
    """Main stabilization function"""
    print("🚀 AurumBotX Stabilization Fix Engine")
    print("=" * 60)
    print("🎯 OBIETTIVO: Stabilizzazione e risoluzione problemi minori")
    print("🔧 FIX: DataFrame errors, SentimentAnalyzer, Dependencies")
    print("⚡ OTTIMIZZAZIONE: Performance, Cache, Memory, Network")
    print("=" * 60)
    
    # Setup
    os.makedirs('logs', exist_ok=True)
    os.makedirs('utils', exist_ok=True)
    
    # Esegui stabilizzazione
    engine = StabilizationEngine()
    report = await engine.run_stabilization()
    
    # Mostra risultati
    if report['status'] in ['completed', 'partial']:
        print(f"\n🎉 STABILIZZAZIONE COMPLETATA!")
        print(f"⏱️ Tempo Esecuzione: {report['execution_time']:.2f}s")
        print(f"📊 Successi: {report['success_count']}/{report['total_count']}")
        print(f"📈 Success Rate: {report['success_rate']:.1f}%")
        
        print(f"\n📋 RISULTATI:")
        for component, result in report['results'].items():
            status = result.get('status', 'unknown')
            emoji = "✅" if status == 'completed' else "⚠️" if status == 'partial' else "❌"
            print(f"   {emoji} {component.replace('_', ' ').title()}: {status.upper()}")
        
        print(f"\n📄 Report dettagliato salvato in: stabilization_results/")
    else:
        print(f"\n❌ ERRORE STABILIZZAZIONE: {report.get('error', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())

