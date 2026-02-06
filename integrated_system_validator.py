#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Integrated System Validator
Validazione completa di tutti i componenti del sistema trading
"""

import os
import sys
import asyncio
import logging
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import time
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SystemValidator')

class ComponentValidator:
    """Validatore per singoli componenti"""
    
    def __init__(self):
        self.logger = logging.getLogger('ComponentValidator')
        self.validation_results = {}
    
    async def validate_trading_engines(self) -> Dict:
        """Valida tutti i trading engine"""
        try:
            self.logger.info("🔍 Validazione Trading Engines...")
            
            results = {
                'enhanced_bootstrap': await self._check_enhanced_bootstrap(),
                'aggressive_trading': await self._check_aggressive_trading(),
                'real_data_trading': await self._check_real_data_trading(),
                'ai_optimization': await self._check_ai_optimization()
            }
            
            # Calcola score complessivo
            active_engines = sum(1 for r in results.values() if r.get('status') == 'active')
            total_engines = len(results)
            
            return {
                'component': 'trading_engines',
                'status': 'healthy' if active_engines >= 2 else 'degraded' if active_engines >= 1 else 'critical',
                'active_engines': active_engines,
                'total_engines': total_engines,
                'engines': results,
                'score': (active_engines / total_engines) * 100
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore validazione trading engines: {e}")
            return {'component': 'trading_engines', 'status': 'error', 'error': str(e)}
    
    async def _check_enhanced_bootstrap(self) -> Dict:
        """Controlla enhanced bootstrap"""
        try:
            # Controlla processo
            result = subprocess.run(['pgrep', '-f', 'enhanced_bootstrap_v2.py'], 
                                  capture_output=True, text=True)
            process_active = bool(result.stdout.strip())
            
            # Controlla database
            db_exists = os.path.exists('enhanced_trading_v2.db')
            
            # Controlla log recenti
            log_recent = False
            if os.path.exists('logs/enhanced_bootstrap_v2.log'):
                mod_time = os.path.getmtime('logs/enhanced_bootstrap_v2.log')
                log_recent = (time.time() - mod_time) < 3600  # Ultimo aggiornamento < 1h
            
            status = 'active' if process_active and db_exists else 'inactive'
            
            return {
                'name': 'Enhanced Bootstrap v2',
                'status': status,
                'process_active': process_active,
                'database_exists': db_exists,
                'log_recent': log_recent,
                'score': 100 if status == 'active' else 0
            }
            
        except Exception as e:
            return {'name': 'Enhanced Bootstrap v2', 'status': 'error', 'error': str(e)}
    
    async def _check_aggressive_trading(self) -> Dict:
        """Controlla aggressive trading"""
        try:
            # Controlla processo
            result = subprocess.run(['pgrep', '-f', 'aggressive_trading_fix.py'], 
                                  capture_output=True, text=True)
            process_active = bool(result.stdout.strip())
            
            # Controlla database e trade
            trades_count = 0
            if os.path.exists('aggressive_trading.db'):
                conn = sqlite3.connect('aggressive_trading.db')
                cursor = conn.execute('SELECT COUNT(*) FROM aggressive_trades')
                trades_count = cursor.fetchone()[0]
                conn.close()
            
            status = 'active' if process_active and trades_count > 0 else 'inactive'
            
            return {
                'name': 'Aggressive Trading',
                'status': status,
                'process_active': process_active,
                'trades_executed': trades_count,
                'score': 100 if status == 'active' else 50 if trades_count > 0 else 0
            }
            
        except Exception as e:
            return {'name': 'Aggressive Trading', 'status': 'error', 'error': str(e)}
    
    async def _check_real_data_trading(self) -> Dict:
        """Controlla real data trading"""
        try:
            # Controlla processo
            result = subprocess.run(['pgrep', '-f', 'real_data_trading_engine.py'], 
                                  capture_output=True, text=True)
            process_active = bool(result.stdout.strip())
            
            # Controlla connessione Binance
            binance_connected = False
            try:
                response = requests.get('https://testnet.binance.vision/api/v3/time', timeout=5)
                binance_connected = response.status_code == 200
            except:
                pass
            
            # Controlla database
            db_exists = os.path.exists('real_data_trading.db')
            
            status = 'active' if process_active and binance_connected else 'inactive'
            
            return {
                'name': 'Real Data Trading',
                'status': status,
                'process_active': process_active,
                'binance_connected': binance_connected,
                'database_exists': db_exists,
                'score': 100 if status == 'active' else 70 if binance_connected else 0
            }
            
        except Exception as e:
            return {'name': 'Real Data Trading', 'status': 'error', 'error': str(e)}
    
    async def _check_ai_optimization(self) -> Dict:
        """Controlla AI optimization"""
        try:
            # Controlla database AI
            ai_trained = False
            training_sessions = 0
            
            if os.path.exists('ai_optimization.db'):
                conn = sqlite3.connect('ai_optimization.db')
                cursor = conn.execute('SELECT COUNT(*) FROM ai_training_sessions WHERE status="completed"')
                training_sessions = cursor.fetchone()[0]
                ai_trained = training_sessions > 0
                conn.close()
            
            status = 'active' if ai_trained else 'inactive'
            
            return {
                'name': 'AI Optimization',
                'status': status,
                'ai_trained': ai_trained,
                'training_sessions': training_sessions,
                'score': 100 if ai_trained else 0
            }
            
        except Exception as e:
            return {'name': 'AI Optimization', 'status': 'error', 'error': str(e)}
    
    async def validate_dashboards(self) -> Dict:
        """Valida dashboard Streamlit"""
        try:
            self.logger.info("🔍 Validazione Dashboard...")
            
            dashboards = {
                'admin': {'port': 8501, 'name': 'Admin Dashboard'},
                'premium': {'port': 8502, 'name': 'Premium Dashboard'},
                'performance': {'port': 8503, 'name': 'Performance Dashboard'},
                'config': {'port': 8504, 'name': 'Config Dashboard'},
                'mobile': {'port': 8505, 'name': 'Mobile Dashboard'}
            }
            
            results = {}
            active_dashboards = 0
            
            for dash_id, info in dashboards.items():
                try:
                    # Controlla processo Streamlit
                    result = subprocess.run(['pgrep', '-f', f'--server.port {info["port"]}'], 
                                          capture_output=True, text=True)
                    process_active = bool(result.stdout.strip())
                    
                    # Test connessione HTTP
                    http_responsive = False
                    try:
                        response = requests.get(f'http://localhost:{info["port"]}', timeout=3)
                        http_responsive = response.status_code == 200
                    except:
                        pass
                    
                    status = 'active' if process_active and http_responsive else 'inactive'
                    if status == 'active':
                        active_dashboards += 1
                    
                    results[dash_id] = {
                        'name': info['name'],
                        'port': info['port'],
                        'status': status,
                        'process_active': process_active,
                        'http_responsive': http_responsive,
                        'score': 100 if status == 'active' else 0
                    }
                    
                except Exception as e:
                    results[dash_id] = {
                        'name': info['name'],
                        'status': 'error',
                        'error': str(e)
                    }
            
            return {
                'component': 'dashboards',
                'status': 'healthy' if active_dashboards >= 3 else 'degraded' if active_dashboards >= 1 else 'critical',
                'active_dashboards': active_dashboards,
                'total_dashboards': len(dashboards),
                'dashboards': results,
                'score': (active_dashboards / len(dashboards)) * 100
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore validazione dashboard: {e}")
            return {'component': 'dashboards', 'status': 'error', 'error': str(e)}
    
    async def validate_data_sources(self) -> Dict:
        """Valida sorgenti dati"""
        try:
            self.logger.info("🔍 Validazione Data Sources...")
            
            results = {}
            
            # Test Binance Testnet
            binance_status = await self._test_binance_connection()
            results['binance_testnet'] = binance_status
            
            # Test database locali
            db_status = await self._test_local_databases()
            results['local_databases'] = db_status
            
            # Test storage locale
            storage_status = await self._test_local_storage()
            results['local_storage'] = storage_status
            
            # Calcola score complessivo
            total_score = sum(r.get('score', 0) for r in results.values())
            avg_score = total_score / len(results) if results else 0
            
            return {
                'component': 'data_sources',
                'status': 'healthy' if avg_score >= 80 else 'degraded' if avg_score >= 50 else 'critical',
                'sources': results,
                'score': avg_score
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore validazione data sources: {e}")
            return {'component': 'data_sources', 'status': 'error', 'error': str(e)}
    
    async def _test_binance_connection(self) -> Dict:
        """Test connessione Binance"""
        try:
            # Test server time
            response = requests.get('https://testnet.binance.vision/api/v3/time', timeout=5)
            server_time_ok = response.status_code == 200
            
            # Test exchange info
            response = requests.get('https://testnet.binance.vision/api/v3/exchangeInfo', timeout=5)
            exchange_info_ok = response.status_code == 200
            
            # Test price ticker
            response = requests.get('https://testnet.binance.vision/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
            price_ok = response.status_code == 200
            
            all_ok = server_time_ok and exchange_info_ok and price_ok
            
            return {
                'name': 'Binance Testnet',
                'status': 'active' if all_ok else 'degraded',
                'server_time': server_time_ok,
                'exchange_info': exchange_info_ok,
                'price_data': price_ok,
                'score': 100 if all_ok else 70 if any([server_time_ok, exchange_info_ok, price_ok]) else 0
            }
            
        except Exception as e:
            return {
                'name': 'Binance Testnet',
                'status': 'error',
                'error': str(e),
                'score': 0
            }
    
    async def _test_local_databases(self) -> Dict:
        """Test database locali"""
        try:
            databases = [
                'aggressive_trading.db',
                'real_data_trading.db',
                'ai_optimization.db',
                'enhanced_trading_v2.db',
                'local_storage/aurumbotx.db'
            ]
            
            results = {}
            working_dbs = 0
            
            for db_name in databases:
                try:
                    if os.path.exists(db_name):
                        conn = sqlite3.connect(db_name)
                        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        conn.close()
                        
                        results[db_name] = {
                            'exists': True,
                            'tables_count': len(tables),
                            'status': 'active'
                        }
                        working_dbs += 1
                    else:
                        results[db_name] = {
                            'exists': False,
                            'status': 'missing'
                        }
                        
                except Exception as e:
                    results[db_name] = {
                        'exists': True,
                        'status': 'error',
                        'error': str(e)
                    }
            
            return {
                'name': 'Local Databases',
                'status': 'active' if working_dbs >= 3 else 'degraded' if working_dbs >= 1 else 'critical',
                'working_databases': working_dbs,
                'total_databases': len(databases),
                'databases': results,
                'score': (working_dbs / len(databases)) * 100
            }
            
        except Exception as e:
            return {
                'name': 'Local Databases',
                'status': 'error',
                'error': str(e),
                'score': 0
            }
    
    async def _test_local_storage(self) -> Dict:
        """Test storage locale"""
        try:
            # Test directory principali
            directories = ['logs', 'reports', 'local_storage', 'local_storage/data', 'local_storage/backups']
            
            existing_dirs = 0
            for directory in directories:
                if os.path.exists(directory):
                    existing_dirs += 1
            
            # Test scrittura/lettura
            test_file = 'local_storage/data/validation_test.json'
            write_ok = False
            read_ok = False
            
            try:
                os.makedirs(os.path.dirname(test_file), exist_ok=True)
                test_data = {'test': 'validation', 'timestamp': datetime.now().isoformat()}
                
                with open(test_file, 'w') as f:
                    json.dump(test_data, f)
                write_ok = True
                
                with open(test_file, 'r') as f:
                    loaded_data = json.load(f)
                read_ok = loaded_data.get('test') == 'validation'
                
                # Cleanup
                os.remove(test_file)
                
            except Exception as e:
                pass
            
            all_ok = existing_dirs >= 4 and write_ok and read_ok
            
            return {
                'name': 'Local Storage',
                'status': 'active' if all_ok else 'degraded',
                'directories_exist': existing_dirs,
                'total_directories': len(directories),
                'write_test': write_ok,
                'read_test': read_ok,
                'score': 100 if all_ok else 70 if write_ok and read_ok else 30 if existing_dirs >= 2 else 0
            }
            
        except Exception as e:
            return {
                'name': 'Local Storage',
                'status': 'error',
                'error': str(e),
                'score': 0
            }

class IntegratedSystemValidator:
    """Validatore sistema integrato completo"""
    
    def __init__(self):
        self.logger = logging.getLogger('IntegratedValidator')
        self.component_validator = ComponentValidator()
        self.validation_report = {}
    
    async def run_full_validation(self) -> Dict:
        """Esegue validazione completa del sistema"""
        try:
            start_time = datetime.now()
            self.logger.info("🚀 Avvio validazione completa sistema AurumBotX...")
            
            # 1. Validazione componenti core
            self.logger.info("🔧 Validazione Trading Engines...")
            trading_validation = await self.component_validator.validate_trading_engines()
            
            # 2. Validazione dashboard
            self.logger.info("📊 Validazione Dashboard...")
            dashboard_validation = await self.component_validator.validate_dashboards()
            
            # 3. Validazione data sources
            self.logger.info("📡 Validazione Data Sources...")
            data_validation = await self.component_validator.validate_data_sources()
            
            # 4. Test integrazione end-to-end
            self.logger.info("🔄 Test Integrazione End-to-End...")
            integration_test = await self._run_integration_test()
            
            # 5. Performance assessment
            self.logger.info("📈 Assessment Performance...")
            performance_assessment = await self._assess_performance()
            
            # 6. Calcola score complessivo
            validation_time = (datetime.now() - start_time).total_seconds()
            overall_score = self._calculate_overall_score([
                trading_validation,
                dashboard_validation,
                data_validation,
                integration_test,
                performance_assessment
            ])
            
            # 7. Determina stato sistema
            system_status = self._determine_system_status(overall_score)
            
            # 8. Crea report finale
            self.validation_report = {
                'timestamp': datetime.now().isoformat(),
                'validation_time': validation_time,
                'overall_score': overall_score,
                'system_status': system_status,
                'components': {
                    'trading_engines': trading_validation,
                    'dashboards': dashboard_validation,
                    'data_sources': data_validation,
                    'integration': integration_test,
                    'performance': performance_assessment
                },
                'recommendations': self._generate_recommendations(),
                'next_steps': self._generate_next_steps()
            }
            
            # 9. Salva report
            await self._save_validation_report()
            
            self.logger.info(f"✅ Validazione completata in {validation_time:.2f}s")
            self.logger.info(f"📊 Score complessivo: {overall_score:.1f}/100")
            self.logger.info(f"🎯 Stato sistema: {system_status.upper()}")
            
            return self.validation_report
            
        except Exception as e:
            self.logger.error(f"❌ Errore validazione sistema: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    async def _run_integration_test(self) -> Dict:
        """Test integrazione end-to-end"""
        try:
            results = {}
            
            # Test 1: Data flow (Binance -> Processing -> AI -> Trading)
            data_flow_ok = await self._test_data_flow()
            results['data_flow'] = data_flow_ok
            
            # Test 2: Dashboard connectivity
            dashboard_connectivity = await self._test_dashboard_connectivity()
            results['dashboard_connectivity'] = dashboard_connectivity
            
            # Test 3: Database consistency
            db_consistency = await self._test_database_consistency()
            results['database_consistency'] = db_consistency
            
            # Test 4: Error handling
            error_handling = await self._test_error_handling()
            results['error_handling'] = error_handling
            
            # Calcola score
            total_score = sum(r.get('score', 0) for r in results.values())
            avg_score = total_score / len(results) if results else 0
            
            return {
                'component': 'integration',
                'status': 'healthy' if avg_score >= 80 else 'degraded' if avg_score >= 60 else 'critical',
                'tests': results,
                'score': avg_score
            }
            
        except Exception as e:
            return {
                'component': 'integration',
                'status': 'error',
                'error': str(e),
                'score': 0
            }
    
    async def _test_data_flow(self) -> Dict:
        """Test flusso dati completo"""
        try:
            # Simula flusso: Binance -> AI -> Trading Decision
            
            # 1. Test connessione Binance
            try:
                response = requests.get('https://testnet.binance.vision/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
                binance_ok = response.status_code == 200
                current_price = float(response.json()['price']) if binance_ok else 0
            except:
                binance_ok = False
                current_price = 0
            
            # 2. Test AI prediction (se disponibile)
            ai_prediction_ok = False
            if os.path.exists('ai_optimization.db'):
                try:
                    conn = sqlite3.connect('ai_optimization.db')
                    cursor = conn.execute('SELECT COUNT(*) FROM ai_predictions')
                    predictions_count = cursor.fetchone()[0]
                    ai_prediction_ok = predictions_count > 0
                    conn.close()
                except:
                    pass
            
            # 3. Test trading decision
            trading_decision_ok = False
            if os.path.exists('aggressive_trading.db'):
                try:
                    conn = sqlite3.connect('aggressive_trading.db')
                    cursor = conn.execute('SELECT COUNT(*) FROM aggressive_trades WHERE timestamp > datetime("now", "-1 hour")')
                    recent_trades = cursor.fetchone()[0]
                    trading_decision_ok = recent_trades > 0
                    conn.close()
                except:
                    pass
            
            all_ok = binance_ok and (ai_prediction_ok or trading_decision_ok)
            
            return {
                'name': 'Data Flow Test',
                'status': 'active' if all_ok else 'degraded',
                'binance_connection': binance_ok,
                'current_price': current_price,
                'ai_predictions': ai_prediction_ok,
                'trading_decisions': trading_decision_ok,
                'score': 100 if all_ok else 70 if binance_ok else 30
            }
            
        except Exception as e:
            return {
                'name': 'Data Flow Test',
                'status': 'error',
                'error': str(e),
                'score': 0
            }
    
    async def _test_dashboard_connectivity(self) -> Dict:
        """Test connettività dashboard"""
        try:
            ports = [8501, 8502, 8503, 8504, 8505]
            responsive_dashboards = 0
            
            for port in ports:
                try:
                    response = requests.get(f'http://localhost:{port}', timeout=2)
                    if response.status_code == 200:
                        responsive_dashboards += 1
                except:
                    pass
            
            return {
                'name': 'Dashboard Connectivity',
                'status': 'active' if responsive_dashboards >= 3 else 'degraded',
                'responsive_dashboards': responsive_dashboards,
                'total_dashboards': len(ports),
                'score': (responsive_dashboards / len(ports)) * 100
            }
            
        except Exception as e:
            return {
                'name': 'Dashboard Connectivity',
                'status': 'error',
                'error': str(e),
                'score': 0
            }
    
    async def _test_database_consistency(self) -> Dict:
        """Test consistenza database"""
        try:
            databases = ['aggressive_trading.db', 'real_data_trading.db', 'ai_optimization.db']
            consistent_dbs = 0
            
            for db_name in databases:
                if os.path.exists(db_name):
                    try:
                        conn = sqlite3.connect(db_name)
                        # Test query semplice
                        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        if tables:  # Ha tabelle
                            consistent_dbs += 1
                        conn.close()
                    except:
                        pass
            
            return {
                'name': 'Database Consistency',
                'status': 'active' if consistent_dbs >= 2 else 'degraded',
                'consistent_databases': consistent_dbs,
                'total_databases': len(databases),
                'score': (consistent_dbs / len(databases)) * 100
            }
            
        except Exception as e:
            return {
                'name': 'Database Consistency',
                'status': 'error',
                'error': str(e),
                'score': 0
            }
    
    async def _test_error_handling(self) -> Dict:
        """Test gestione errori"""
        try:
            # Test log files per errori recenti
            log_files = ['logs/aggressive_trading.log', 'logs/real_data_trading.log', 'logs/ai_optimization.log']
            
            error_free_logs = 0
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # Controlla ultimi 100 righe per errori critici
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            recent_lines = lines[-100:] if len(lines) > 100 else lines
                            
                        # Conta errori critici
                        critical_errors = sum(1 for line in recent_lines if 'CRITICAL' in line or 'FATAL' in line)
                        
                        if critical_errors == 0:
                            error_free_logs += 1
                            
                    except:
                        pass
            
            return {
                'name': 'Error Handling',
                'status': 'active' if error_free_logs >= 2 else 'degraded',
                'error_free_logs': error_free_logs,
                'total_logs': len(log_files),
                'score': (error_free_logs / len(log_files)) * 100 if log_files else 50
            }
            
        except Exception as e:
            return {
                'name': 'Error Handling',
                'status': 'error',
                'error': str(e),
                'score': 0
            }
    
    async def _assess_performance(self) -> Dict:
        """Assessment performance sistema"""
        try:
            # Metriche performance
            metrics = {}
            
            # 1. Trading performance
            trading_perf = await self._get_trading_performance()
            metrics['trading'] = trading_perf
            
            # 2. AI performance
            ai_perf = await self._get_ai_performance()
            metrics['ai'] = ai_perf
            
            # 3. System performance
            system_perf = await self._get_system_performance()
            metrics['system'] = system_perf
            
            # Calcola score complessivo
            total_score = sum(m.get('score', 0) for m in metrics.values())
            avg_score = total_score / len(metrics) if metrics else 0
            
            return {
                'component': 'performance',
                'status': 'healthy' if avg_score >= 70 else 'degraded' if avg_score >= 50 else 'critical',
                'metrics': metrics,
                'score': avg_score
            }
            
        except Exception as e:
            return {
                'component': 'performance',
                'status': 'error',
                'error': str(e),
                'score': 0
            }
    
    async def _get_trading_performance(self) -> Dict:
        """Performance trading"""
        try:
            total_trades = 0
            total_profit = 0
            win_rate = 0
            
            # Aggressive trading stats
            if os.path.exists('aggressive_trading.db'):
                conn = sqlite3.connect('aggressive_trading.db')
                cursor = conn.execute('SELECT COUNT(*), SUM(profit_loss), AVG(CASE WHEN profit_loss > 0 THEN 1.0 ELSE 0.0 END) FROM aggressive_trades')
                result = cursor.fetchone()
                if result[0]:
                    total_trades += result[0]
                    total_profit += result[1] or 0
                    win_rate = result[2] or 0
                conn.close()
            
            return {
                'name': 'Trading Performance',
                'total_trades': total_trades,
                'total_profit': total_profit,
                'win_rate': win_rate * 100,
                'score': min(100, max(0, 50 + (total_profit * 10) + (win_rate * 30)))
            }
            
        except Exception as e:
            return {'name': 'Trading Performance', 'error': str(e), 'score': 0}
    
    async def _get_ai_performance(self) -> Dict:
        """Performance AI"""
        try:
            training_sessions = 0
            best_score = 0
            avg_confidence = 0
            
            if os.path.exists('ai_optimization.db'):
                conn = sqlite3.connect('ai_optimization.db')
                
                # Training sessions
                cursor = conn.execute('SELECT COUNT(*), MAX(best_score) FROM ai_training_sessions WHERE status="completed"')
                result = cursor.fetchone()
                training_sessions = result[0] or 0
                best_score = result[1] or 0
                
                # Predictions confidence
                cursor = conn.execute('SELECT AVG(confidence) FROM ai_predictions')
                result = cursor.fetchone()
                avg_confidence = result[0] or 0
                
                conn.close()
            
            return {
                'name': 'AI Performance',
                'training_sessions': training_sessions,
                'best_model_score': best_score,
                'avg_confidence': avg_confidence * 100,
                'score': min(100, (training_sessions * 20) + (best_score * 50) + (avg_confidence * 30))
            }
            
        except Exception as e:
            return {'name': 'AI Performance', 'error': str(e), 'score': 0}
    
    async def _get_system_performance(self) -> Dict:
        """Performance sistema"""
        try:
            # Uptime processi
            processes = ['enhanced_bootstrap_v2.py', 'aggressive_trading_fix.py', 'real_data_trading_engine.py']
            active_processes = 0
            
            for process in processes:
                result = subprocess.run(['pgrep', '-f', process], capture_output=True, text=True)
                if result.stdout.strip():
                    active_processes += 1
            
            # Dashboard attive
            dashboard_ports = [8501, 8502, 8503, 8504, 8505]
            active_dashboards = 0
            
            for port in dashboard_ports:
                result = subprocess.run(['pgrep', '-f', f'--server.port {port}'], capture_output=True, text=True)
                if result.stdout.strip():
                    active_dashboards += 1
            
            return {
                'name': 'System Performance',
                'active_processes': active_processes,
                'total_processes': len(processes),
                'active_dashboards': active_dashboards,
                'total_dashboards': len(dashboard_ports),
                'score': ((active_processes / len(processes)) * 50) + ((active_dashboards / len(dashboard_ports)) * 50)
            }
            
        except Exception as e:
            return {'name': 'System Performance', 'error': str(e), 'score': 0}
    
    def _calculate_overall_score(self, validations: List[Dict]) -> float:
        """Calcola score complessivo"""
        try:
            scores = [v.get('score', 0) for v in validations if 'score' in v]
            return sum(scores) / len(scores) if scores else 0
        except:
            return 0
    
    def _determine_system_status(self, score: float) -> str:
        """Determina stato sistema basato su score"""
        if score >= 85:
            return 'excellent'
        elif score >= 70:
            return 'healthy'
        elif score >= 50:
            return 'degraded'
        elif score >= 30:
            return 'critical'
        else:
            return 'failed'
    
    def _generate_recommendations(self) -> List[str]:
        """Genera raccomandazioni basate su validazione"""
        recommendations = []
        
        try:
            components = self.validation_report.get('components', {})
            
            # Trading engines
            trading = components.get('trading_engines', {})
            if trading.get('score', 0) < 80:
                recommendations.append("Riavviare trading engines inattivi per massimizzare performance")
            
            # Dashboard
            dashboards = components.get('dashboards', {})
            if dashboards.get('score', 0) < 80:
                recommendations.append("Verificare e riavviare dashboard Streamlit non responsive")
            
            # Data sources
            data = components.get('data_sources', {})
            if data.get('score', 0) < 80:
                recommendations.append("Controllare connessioni dati e stabilità API Binance")
            
            # Performance
            performance = components.get('performance', {})
            if performance.get('score', 0) < 70:
                recommendations.append("Ottimizzare parametri trading per migliorare performance")
            
            # AI
            ai_score = performance.get('metrics', {}).get('ai', {}).get('score', 0)
            if ai_score < 70:
                recommendations.append("Eseguire nuovo training AI con dati più recenti")
            
            if not recommendations:
                recommendations.append("Sistema operativo ottimale - continuare monitoraggio")
                
        except Exception as e:
            recommendations.append(f"Errore generazione raccomandazioni: {e}")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Genera prossimi step"""
        next_steps = []
        
        try:
            overall_score = self.validation_report.get('overall_score', 0)
            
            if overall_score >= 85:
                next_steps = [
                    "Monitorare performance per 24-48h",
                    "Considerare deploy in produzione",
                    "Implementare alerting avanzato",
                    "Pianificare scaling orizzontale"
                ]
            elif overall_score >= 70:
                next_steps = [
                    "Risolvere problemi identificati",
                    "Ottimizzare componenti degraded",
                    "Eseguire test stress",
                    "Validare nuovamente tra 24h"
                ]
            elif overall_score >= 50:
                next_steps = [
                    "Riparare componenti critici",
                    "Riavviare servizi inattivi",
                    "Verificare configurazioni",
                    "Eseguire validazione completa"
                ]
            else:
                next_steps = [
                    "Diagnosi approfondita errori",
                    "Ricostruzione componenti falliti",
                    "Backup e recovery dati",
                    "Restart completo sistema"
                ]
                
        except Exception as e:
            next_steps = [f"Errore generazione next steps: {e}"]
        
        return next_steps
    
    async def _save_validation_report(self):
        """Salva report validazione"""
        try:
            os.makedirs('validation_results', exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_results/system_validation_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.validation_report, f, indent=2, default=str)
            
            self.logger.info(f"📊 Report salvato: {filename}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio report: {e}")

async def main():
    """Main validation function"""
    print("🚀 AurumBotX Integrated System Validator")
    print("=" * 60)
    print("🔍 VALIDAZIONE COMPLETA: Tutti i componenti")
    print("📊 METRICHE: Performance, Stabilità, Integrazione")
    print("🎯 OBIETTIVO: Certificazione sistema operativo")
    print("=" * 60)
    
    # Setup
    os.makedirs('logs', exist_ok=True)
    os.makedirs('validation_results', exist_ok=True)
    
    # Esegui validazione
    validator = IntegratedSystemValidator()
    report = await validator.run_full_validation()
    
    # Mostra risultati
    if 'error' not in report:
        print(f"\n🎉 VALIDAZIONE COMPLETATA!")
        print(f"📊 Score Complessivo: {report['overall_score']:.1f}/100")
        print(f"🎯 Stato Sistema: {report['system_status'].upper()}")
        print(f"⏱️ Tempo Validazione: {report['validation_time']:.2f}s")
        
        print(f"\n📋 COMPONENTI:")
        for comp_name, comp_data in report['components'].items():
            status = comp_data.get('status', 'unknown')
            score = comp_data.get('score', 0)
            emoji = "✅" if status == 'healthy' else "⚠️" if status == 'degraded' else "❌"
            print(f"   {emoji} {comp_name.title()}: {status.upper()} ({score:.1f}/100)")
        
        print(f"\n💡 RACCOMANDAZIONI:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n🎯 PROSSIMI STEP:")
        for i, step in enumerate(report['next_steps'], 1):
            print(f"   {i}. {step}")
        
        print(f"\n📄 Report completo salvato in: validation_results/")
    else:
        print(f"\n❌ ERRORE VALIDAZIONE: {report.get('error', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())

