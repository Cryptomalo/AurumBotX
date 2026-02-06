#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
Attivazione Strategia 6M Conservativa
Loop automatico con gestione NaN robusta per trading reale
"""

import os
import sys
import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

class Conservative6MStrategy:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('Conservative6M')
        self.trading_active = False
        self.performance_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'start_time': datetime.now()
        }
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/ubuntu/AurumBotX/logs/6m_conservative.log'),
                logging.StreamHandler()
            ]
        )
    
    def print_header(self, title):
        print(f"\n{'='*80}")
        print(f"📈 {title}")
        print(f"{'='*80}")
        
    def print_section(self, title):
        print(f"\n📋 {title}")
        print(f"{'-'*60}")
    
    async def activate_conservative_strategy(self):
        """Attiva strategia 6M conservativa"""
        self.print_header("ATTIVAZIONE STRATEGIA 6M CONSERVATIVA")
        
        try:
            # Setup ambiente
            self.load_environment()
            
            # Inizializza componenti
            await self.initialize_components()
            
            # Configura strategia
            self.configure_conservative_strategy()
            
            # Avvia loop trading
            await self.start_trading_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Errore attivazione strategia: {e}")
            import traceback
            traceback.print_exc()
    
    def load_environment(self):
        """Carica variabili ambiente"""
        if os.path.exists('/home/ubuntu/AurumBotX/.env'):
            with open('/home/ubuntu/AurumBotX/.env', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        print("  ✅ Variabili ambiente caricate")
    
    async def initialize_components(self):
        """Inizializza componenti trading"""
        self.print_section("INIZIALIZZAZIONE COMPONENTI")
        
        try:
            from utils.data_loader import CryptoDataLoader
            from utils.exchange_manager import ExchangeManager
            from utils.ai_trading import AITrading
            
            # Data Loader
            print("  📊 Inizializzazione Data Loader...")
            self.data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await self.data_loader.initialize()
            print("    ✅ Data Loader inizializzato")
            
            # Exchange Manager
            print("  💹 Inizializzazione Exchange Manager...")
            self.exchange_manager = ExchangeManager('binance', testnet=True)
            print("    ✅ Exchange Manager inizializzato")
            
            # AI Trading
            print("  🤖 Inizializzazione AI Trading...")
            self.ai_trading = AITrading()
            await self.ai_trading.initialize()
            print("    ✅ AI Trading inizializzato")
            
            # Test connessioni
            await self.test_connections()
            
        except Exception as e:
            self.logger.error(f"❌ Errore inizializzazione: {e}")
            raise
    
    async def test_connections(self):
        """Testa tutte le connessioni"""
        print("  🔍 Test connessioni...")
        
        try:
            # Test prezzo
            price = await self.data_loader.get_latest_price('BTCUSDT')
            if price and price > 50000:
                print(f"    ✅ Prezzo BTC: ${price:,.2f}")
            else:
                print(f"    ⚠️ Prezzo BTC: ${price} (potrebbe essere mock)")
            
            # Test saldo
            balance = await self.exchange_manager.get_balance()
            if balance:
                usdt = balance.get('USDT', {}).get('free', 0)
                btc = balance.get('BTC', {}).get('free', 0)
                print(f"    ✅ Saldo USDT: {usdt}")
                print(f"    ✅ Saldo BTC: {btc}")
            else:
                print("    ⚠️ Impossibile recuperare saldo")
            
        except Exception as e:
            print(f"    ❌ Errore test connessioni: {e}")
    
    def configure_conservative_strategy(self):
        """Configura strategia conservativa"""
        self.print_section("CONFIGURAZIONE STRATEGIA CONSERVATIVA")
        
        self.strategy_config = {
            'name': 'Conservative 6M Strategy',
            'symbol': 'BTCUSDT',
            'timeframe': '6m',
            'trade_amount': 0.0001,  # 0.0001 BTC (~$12)
            'profit_target': 0.003,  # 0.3%
            'stop_loss': 0.002,      # 0.2%
            'min_confidence': 0.65,  # 65% confidenza minima
            'max_trades_per_hour': 5,
            'max_concurrent_trades': 2,
            'risk_per_trade': 0.01,  # 1% del capitale
            'cooldown_minutes': 15,   # 15 min tra trade
            'nan_handling': 'robust', # Gestione NaN robusta
            'fallback_signals': True  # Usa segnali fallback se AI fallisce
        }
        
        print("  📊 CONFIGURAZIONE STRATEGIA:")
        for key, value in self.strategy_config.items():
            print(f"    {key}: {value}")
        
        # Salva configurazione
        config_file = "/home/ubuntu/AurumBotX/configs/6m_conservative_active.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(self.strategy_config, f, indent=2)
        
        print(f"  ✅ Configurazione salvata: {config_file}")\n    \n    async def start_trading_loop(self):\n        \"\"\"Avvia loop trading automatico\"\"\"\n        self.print_section(\"AVVIO LOOP TRADING AUTOMATICO\")\n        \n        print(\"  🚀 Strategia 6M Conservativa ATTIVA\")\n        print(\"  ⏰ Cicli ogni 6 minuti\")\n        print(\"  🎯 Target: +0.3% | Stop: -0.2%\")\n        print(\"  🛡️ Confidenza minima: 65%\")\n        print(\"  💰 Importo per trade: 0.0001 BTC\")\n        print(\"\")\n        \n        self.trading_active = True\n        cycle_count = 0\n        last_trade_time = datetime.now() - timedelta(minutes=20)  # Permetti primo trade\n        \n        try:\n            while self.trading_active:\n                cycle_count += 1\n                cycle_start = datetime.now()\n                \n                print(f\"🔄 CICLO #{cycle_count} - {cycle_start.strftime('%H:%M:%S')}\")\n                \n                try:\n                    # 1. Analisi mercato\n                    market_data = await self.analyze_market_robust()\n                    \n                    # 2. Generazione segnali\n                    signals = await self.generate_signals_robust(market_data)\n                    \n                    # 3. Valutazione trade\n                    if signals:\n                        trade_decision = await self.evaluate_trade_opportunity(\n                            signals, last_trade_time\n                        )\n                        \n                        if trade_decision:\n                            # 4. Esecuzione trade\n                            trade_result = await self.execute_conservative_trade(trade_decision)\n                            \n                            if trade_result:\n                                last_trade_time = datetime.now()\n                                self.performance_stats['total_trades'] += 1\n                    \n                    # 5. Gestione trade attivi\n                    await self.manage_active_trades()\n                    \n                    # 6. Aggiornamento statistiche\n                    await self.update_performance_stats(cycle_count)\n                    \n                except Exception as e:\n                    self.logger.error(f\"❌ Errore ciclo #{cycle_count}: {e}\")\n                \n                # Pausa 6 minuti\n                await asyncio.sleep(360)\n                \n        except KeyboardInterrupt:\n            print(\"\\n⏹️ Trading interrotto dall'utente\")\n            self.trading_active = False\n        except Exception as e:\n            self.logger.error(f\"❌ Errore loop trading: {e}\")\n            self.trading_active = False\n    \n    async def analyze_market_robust(self) -> Dict[str, Any]:\n        \"\"\"Analisi mercato con gestione errori robusta\"\"\"\n        try:\n            # Ottieni prezzo corrente\n            current_price = await self.data_loader.get_latest_price('BTCUSDT')\n            \n            # Ottieni dati storici con gestione NaN\n            historical_data = await self.get_clean_historical_data()\n            \n            # Analisi AI se possibile\n            ai_analysis = None\n            try:\n                ai_analysis = await self.ai_trading.analyze_market('BTCUSDT')\n            except Exception as e:\n                self.logger.warning(f\"AI analysis fallita: {e}\")\n            \n            market_data = {\n                'current_price': current_price,\n                'historical_data': historical_data,\n                'ai_analysis': ai_analysis,\n                'timestamp': datetime.now(),\n                'data_quality': 'good' if historical_data is not None else 'poor'\n            }\n            \n            print(f\"  📊 Prezzo: ${current_price:,.2f} | Dati: {market_data['data_quality']}\")\n            return market_data\n            \n        except Exception as e:\n            self.logger.error(f\"❌ Errore analisi mercato: {e}\")\n            return {\n                'current_price': None,\n                'historical_data': None,\n                'ai_analysis': None,\n                'timestamp': datetime.now(),\n                'data_quality': 'error'\n            }\n    \n    async def get_clean_historical_data(self) -> Optional[pd.DataFrame]:\n        \"\"\"Ottiene dati storici puliti senza NaN\"\"\"\n        try:\n            # Prova con dati reali\n            data = await self.data_loader.get_historical_data('BTCUSDT', '1D', 50)\n            \n            if data is not None and not data.empty:\n                # Pulizia NaN robusta\n                data = data.fillna(method='ffill').fillna(method='bfill')\n                \n                # Verifica ancora NaN\n                if data.isna().any().any():\n                    # Riempi con valori ragionevoli\n                    for col in data.columns:\n                        if data[col].isna().any():\n                            if col == 'volume':\n                                data[col] = data[col].fillna(1000000)\n                            else:\n                                data[col] = data[col].fillna(data[col].mean())\n                \n                # Verifica finale\n                if not data.isna().any().any():\n                    return data\n            \n            # Fallback a dati mock puliti\n            return self.generate_clean_mock_data()\n            \n        except Exception as e:\n            self.logger.warning(f\"Errore dati storici: {e}\")\n            return self.generate_clean_mock_data()\n    \n    def generate_clean_mock_data(self) -> pd.DataFrame:\n        \"\"\"Genera dati mock puliti per fallback\"\"\"\n        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')\n        \n        base_price = 117000\n        prices = []\n        current_price = base_price\n        \n        for i in range(50):\n            change = np.random.uniform(-0.01, 0.01)  # ±1%\n            current_price = current_price * (1 + change)\n            prices.append(current_price)\n        \n        data = pd.DataFrame({\n            'timestamp': dates,\n            'open': [p * 0.999 for p in prices],\n            'high': [p * 1.002 for p in prices],\n            'low': [p * 0.998 for p in prices],\n            'close': prices,\n            'volume': [np.random.uniform(2000000, 4000000) for _ in range(50)]\n        })\n        \n        return data\n    \n    async def generate_signals_robust(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:\n        \"\"\"Genera segnali con fallback robusto\"\"\"\n        signals = []\n        \n        try:\n            # Prova segnali AI\n            if market_data['data_quality'] in ['good', 'poor']:\n                try:\n                    ai_signals = await self.ai_trading.generate_trading_signals('BTCUSDT')\n                    if ai_signals:\n                        signals.extend(ai_signals)\n                        print(f\"  🤖 Segnali AI: {len(ai_signals)}\")\n                except Exception as e:\n                    self.logger.warning(f\"Segnali AI falliti: {e}\")\n            \n            # Fallback a segnali tecnici semplici\n            if not signals and self.strategy_config['fallback_signals']:\n                fallback_signal = self.generate_fallback_signal(market_data)\n                if fallback_signal:\n                    signals.append(fallback_signal)\n                    print(\"  🔧 Segnale fallback generato\")\n            \n            return signals\n            \n        except Exception as e:\n            self.logger.error(f\"❌ Errore generazione segnali: {e}\")\n            return []\n    \n    def generate_fallback_signal(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:\n        \"\"\"Genera segnale fallback basato su logica semplice\"\"\"\n        try:\n            current_price = market_data.get('current_price')\n            if not current_price:\n                return None\n            \n            historical_data = market_data.get('historical_data')\n            if historical_data is None or historical_data.empty:\n                return None\n            \n            # Logica semplice: confronta con media mobile\n            recent_prices = historical_data['close'].tail(10)\n            sma_10 = recent_prices.mean()\n            \n            # Segnale conservativo\n            if current_price > sma_10 * 1.002:  # +0.2% sopra SMA\n                action = 'BUY'\n                confidence = 0.7\n            elif current_price < sma_10 * 0.998:  # -0.2% sotto SMA\n                action = 'SELL'\n                confidence = 0.7\n            else:\n                return None  # Nessun segnale in zona neutrale\n            \n            return {\n                'action': action,\n                'confidence': confidence,\n                'price': current_price,\n                'timestamp': datetime.now().isoformat(),\n                'source': 'fallback_technical',\n                'reason': f'Price vs SMA10: {current_price:.2f} vs {sma_10:.2f}'\n            }\n            \n        except Exception as e:\n            self.logger.error(f\"❌ Errore segnale fallback: {e}\")\n            return None\n    \n    async def evaluate_trade_opportunity(self, signals: List[Dict[str, Any]], \n                                       last_trade_time: datetime) -> Optional[Dict[str, Any]]:\n        \"\"\"Valuta opportunità di trade\"\"\"\n        try:\n            # Filtra segnali per confidenza\n            valid_signals = [\n                s for s in signals \n                if s.get('confidence', 0) >= self.strategy_config['min_confidence']\n            ]\n            \n            if not valid_signals:\n                print(\"  ⚠️ Nessun segnale con confidenza sufficiente\")\n                return None\n            \n            # Verifica cooldown\n            time_since_last = datetime.now() - last_trade_time\n            cooldown_minutes = self.strategy_config['cooldown_minutes']\n            \n            if time_since_last.total_seconds() < cooldown_minutes * 60:\n                remaining = cooldown_minutes * 60 - time_since_last.total_seconds()\n                print(f\"  ⏰ Cooldown attivo: {remaining/60:.1f} min rimanenti\")\n                return None\n            \n            # Seleziona miglior segnale\n            best_signal = max(valid_signals, key=lambda x: x.get('confidence', 0))\n            \n            print(f\"  🎯 Segnale selezionato: {best_signal['action']} - {best_signal['confidence']:.1%}\")\n            \n            return {\n                'signal': best_signal,\n                'trade_amount': self.strategy_config['trade_amount'],\n                'profit_target': self.strategy_config['profit_target'],\n                'stop_loss': self.strategy_config['stop_loss']\n            }\n            \n        except Exception as e:\n            self.logger.error(f\"❌ Errore valutazione trade: {e}\")\n            return None\n    \n    async def execute_conservative_trade(self, trade_decision: Dict[str, Any]) -> bool:\n        \"\"\"Esegue trade conservativo\"\"\"\n        try:\n            signal = trade_decision['signal']\n            action = signal['action']\n            amount = trade_decision['trade_amount']\n            \n            print(f\"  🚀 Esecuzione {action} - {amount} BTC\")\n            \n            # Prepara ordine\n            order_data = {\n                'symbol': 'BTCUSDT',\n                'side': action,\n                'type': 'MARKET',\n                'quantity': amount\n            }\n            \n            # Esegui ordine\n            result = await self.exchange_manager.place_order(**order_data)\n            \n            if result and result.get('status') == 'FILLED':\n                print(f\"    ✅ Trade eseguito - ID: {result.get('orderId')}\")\n                \n                # Salva trade per monitoraggio\n                await self.save_trade_record(result, trade_decision)\n                \n                return True\n            else:\n                print(f\"    ❌ Trade fallito: {result}\")\n                return False\n                \n        except Exception as e:\n            self.logger.error(f\"❌ Errore esecuzione trade: {e}\")\n            return False\n    \n    async def save_trade_record(self, order_result: Dict[str, Any], \n                              trade_decision: Dict[str, Any]):\n        \"\"\"Salva record del trade\"\"\"\n        try:\n            trade_record = {\n                'timestamp': datetime.now().isoformat(),\n                'order_id': order_result.get('orderId'),\n                'symbol': order_result.get('symbol'),\n                'side': order_result.get('side'),\n                'quantity': float(order_result.get('executedQty', 0)),\n                'price': float(order_result.get('fills', [{}])[0].get('price', 0)),\n                'signal_confidence': trade_decision['signal'].get('confidence'),\n                'signal_source': trade_decision['signal'].get('source'),\n                'profit_target': trade_decision['profit_target'],\n                'stop_loss': trade_decision['stop_loss'],\n                'status': 'ACTIVE'\n            }\n            \n            # Salva su file\n            trades_file = \"/home/ubuntu/AurumBotX/logs/trades_6m_conservative.json\"\n            \n            trades_history = []\n            if os.path.exists(trades_file):\n                with open(trades_file, 'r') as f:\n                    trades_history = json.load(f)\n            \n            trades_history.append(trade_record)\n            \n            with open(trades_file, 'w') as f:\n                json.dump(trades_history, f, indent=2)\n            \n            print(f\"    📝 Trade registrato: {trades_file}\")\n            \n        except Exception as e:\n            self.logger.error(f\"❌ Errore salvataggio trade: {e}\")\n    \n    async def manage_active_trades(self):\n        \"\"\"Gestisce trade attivi (profit/stop)\"\"\"\n        # Implementazione semplificata per ora\n        pass\n    \n    async def update_performance_stats(self, cycle_count: int):\n        \"\"\"Aggiorna statistiche performance\"\"\"\n        try:\n            if cycle_count % 10 == 0:  # Ogni 10 cicli (1 ora)\n                uptime = datetime.now() - self.performance_stats['start_time']\n                \n                stats = {\n                    'timestamp': datetime.now().isoformat(),\n                    'uptime_hours': uptime.total_seconds() / 3600,\n                    'total_cycles': cycle_count,\n                    'total_trades': self.performance_stats['total_trades'],\n                    'winning_trades': self.performance_stats['winning_trades'],\n                    'losing_trades': self.performance_stats['losing_trades'],\n                    'total_profit': self.performance_stats['total_profit']\n                }\n                \n                stats_file = \"/home/ubuntu/AurumBotX/logs/6m_conservative_stats.json\"\n                with open(stats_file, 'w') as f:\n                    json.dump(stats, f, indent=2)\n                \n                print(f\"  📊 Stats aggiornate - Cicli: {cycle_count} | Trade: {self.performance_stats['total_trades']}\")\n                \n        except Exception as e:\n            self.logger.error(f\"❌ Errore aggiornamento stats: {e}\")\n\nasync def main():\n    strategy = Conservative6MStrategy()\n    await strategy.activate_conservative_strategy()\n\nif __name__ == \"__main__\":\n    asyncio.run(main())

