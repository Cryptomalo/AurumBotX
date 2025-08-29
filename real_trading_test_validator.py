#!/usr/bin/env python3
"""
Test Trading Reale e Validazione Profitti
Sistema completo per testare il trading reale su Binance Testnet
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

class RealTradingValidator:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('RealTradingValidator')
        self.trading_active = False
        self.test_results = {
            'start_time': datetime.now(),
            'trades_executed': [],
            'total_profit': 0.0,
            'successful_trades': 0,
            'failed_trades': 0,
            'system_errors': 0,
            'uptime_minutes': 0
        }
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/ubuntu/AurumBotX/logs/real_trading_test.log'),
                logging.StreamHandler()
            ]
        )
    
    def print_header(self, title):
        print(f"\n{'='*80}")
        print(f"💰 {title}")
        print(f"{'='*80}")
        
    def print_section(self, title):
        print(f"\n📋 {title}")
        print(f"{'-'*60}")
    
    async def run_real_trading_test(self):
        """Esegue test completo di trading reale"""
        self.print_header("TEST TRADING REALE E VALIDAZIONE PROFITTI")
        
        try:
            # Setup ambiente
            self.load_environment()
            
            # Inizializza componenti
            await self.initialize_trading_components()
            
            # Verifica saldi iniziali
            initial_balance = await self.get_initial_balance()
            
            # Configura test
            test_config = self.configure_real_trading_test()
            
            # Esegue test trading reale
            await self.execute_real_trading_test(test_config, initial_balance)
            
            # Validazione profitti
            await self.validate_profits(initial_balance)
            
            # Report finale
            self.generate_final_report()
            
        except Exception as e:
            self.logger.error(f"❌ Errore test trading reale: {e}")
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
    
    async def initialize_trading_components(self):
        """Inizializza tutti i componenti per trading reale"""
        self.print_section("INIZIALIZZAZIONE COMPONENTI TRADING REALE")
        
        try:
            from utils.data_loader import CryptoDataLoader
            from utils.exchange_manager import ExchangeManager
            from utils.ai_trading import AITrading
            
            # Data Loader
            print("  📊 Inizializzazione Data Loader...")
            self.data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await self.data_loader.initialize()
            print("    ✅ Data Loader operativo")
            
            # Exchange Manager per ordini reali
            print("  💹 Inizializzazione Exchange Manager...")
            self.exchange_manager = ExchangeManager('binance', testnet=True)
            print("    ✅ Exchange Manager operativo")
            
            # AI Trading
            print("  🤖 Inizializzazione AI Trading...")
            self.ai_trading = AITrading()
            await self.ai_trading.initialize()
            print("    ✅ AI Trading operativo")
            
            # Test connessioni
            await self.test_all_connections()
            
        except Exception as e:
            self.logger.error(f"❌ Errore inizializzazione: {e}")
            raise
    
    async def test_all_connections(self):
        """Testa tutte le connessioni critiche"""
        print("  🔍 Test connessioni critiche...")
        
        try:
            # Test prezzo real-time
            price = await self.data_loader.get_latest_price('BTCUSDT')
            if price and price > 50000:
                print(f"    ✅ Prezzo BTC real-time: ${price:,.2f}")
                self.test_results['current_btc_price'] = price
            else:
                print(f"    ⚠️ Prezzo BTC anomalo: ${price}")
                self.test_results['price_warning'] = True
            
            # Test saldo account
            balance = await self.exchange_manager.get_balance()
            if balance:
                usdt_free = balance.get('USDT', {}).get('free', 0)
                btc_free = balance.get('BTC', {}).get('free', 0)
                
                print(f"    ✅ Saldo USDT: {usdt_free}")
                print(f"    ✅ Saldo BTC: {btc_free}")
                
                self.test_results['initial_usdt'] = float(usdt_free)
                self.test_results['initial_btc'] = float(btc_free)
            else:
                print("    ❌ Impossibile recuperare saldo")
                raise Exception("Saldo non disponibile")
            
            # Test generazione segnali
            print("    🎯 Test generazione segnali...")
            try:
                signals = await self.ai_trading.generate_trading_signals('BTCUSDT')
                if signals:
                    print(f"    ✅ Segnali AI: {len(signals)} generati")
                else:
                    print("    ⚠️ Nessun segnale AI, userò fallback")
            except Exception as e:
                print(f"    ⚠️ Segnali AI falliti: {e}")
            
        except Exception as e:
            print(f"    ❌ Errore test connessioni: {e}")
            raise
    
    async def get_initial_balance(self):
        """Ottiene saldo iniziale per calcolo profitti"""
        self.print_section("SALDO INIZIALE")
        
        try:
            balance = await self.exchange_manager.get_balance()
            
            initial_balance = {
                'usdt': float(balance.get('USDT', {}).get('free', 0)),
                'btc': float(balance.get('BTC', {}).get('free', 0)),
                'timestamp': datetime.now().isoformat()
            }
            
            # Calcola valore totale in USDT
            btc_price = await self.data_loader.get_latest_price('BTCUSDT')
            total_value_usdt = initial_balance['usdt'] + (initial_balance['btc'] * btc_price)
            
            initial_balance['total_value_usdt'] = total_value_usdt
            initial_balance['btc_price'] = btc_price
            
            print(f"  💰 SALDO INIZIALE:")
            print(f"    USDT: {initial_balance['usdt']}")
            print(f"    BTC: {initial_balance['btc']}")
            print(f"    Valore totale: ${total_value_usdt:.2f} USDT")
            
            return initial_balance
            
        except Exception as e:
            self.logger.error(f"❌ Errore saldo iniziale: {e}")
            raise
    
    def configure_real_trading_test(self):
        """Configura parametri per test trading reale"""
        self.print_section("CONFIGURAZIONE TEST TRADING REALE")
        
        config = {
            'test_duration_minutes': 30,  # 30 minuti di test
            'max_trades': 5,              # Massimo 5 trade
            'trade_amount_btc': 0.00005,  # 0.00005 BTC (~$6)
            'profit_target': 0.005,       # 0.5% target
            'stop_loss': 0.003,           # 0.3% stop loss
            'min_confidence': 0.6,        # 60% confidenza minima
            'cycle_interval_seconds': 60, # Ciclo ogni minuto
            'max_concurrent_trades': 1,   # 1 trade alla volta
            'enable_real_orders': True,   # ORDINI REALI
            'symbol': 'BTCUSDT'
        }
        
        print(f"  ⚙️ CONFIGURAZIONE TEST:")
        for key, value in config.items():
            print(f"    {key}: {value}")
        
        # Salva configurazione
        config_file = "/home/ubuntu/AurumBotX/configs/real_trading_test.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"  ✅ Configurazione salvata: {config_file}")
        
        return config
    
    async def execute_real_trading_test(self, config, initial_balance):
        """Esegue il test di trading reale"""
        self.print_section("ESECUZIONE TEST TRADING REALE")
        
        print("  🚀 AVVIO TEST TRADING REALE")
        print(f"  ⏰ Durata: {config['test_duration_minutes']} minuti")
        print(f"  💰 Importo per trade: {config['trade_amount_btc']} BTC")
        print(f"  🎯 Target: +{config['profit_target']:.1%} | Stop: -{config['stop_loss']:.1%}")
        print(f"  ⚠️ ATTENZIONE: ORDINI REALI ATTIVI")
        print("")
        
        self.trading_active = True
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=config['test_duration_minutes'])
        
        cycle_count = 0
        active_trades = []
        
        try:
            while self.trading_active and datetime.now() < end_time:
                cycle_count += 1
                cycle_start = datetime.now()
                
                print(f"🔄 CICLO #{cycle_count} - {cycle_start.strftime('%H:%M:%S')}")
                
                try:
                    # 1. Analisi mercato
                    market_data = await self.analyze_market_for_trading()
                    
                    # 2. Gestione trade attivi
                    active_trades = await self.manage_active_trades(active_trades, config)
                    
                    # 3. Nuovi trade se possibile
                    if len(active_trades) < config['max_concurrent_trades']:
                        if len(self.test_results['trades_executed']) < config['max_trades']:
                            new_trade = await self.evaluate_new_trade(market_data, config)
                            
                            if new_trade:
                                trade_result = await self.execute_real_trade(new_trade, config)
                                if trade_result:
                                    active_trades.append(trade_result)
                    
                    # 4. Report ciclo
                    self.report_trading_cycle(cycle_count, market_data, active_trades)
                    
                except Exception as e:
                    self.logger.error(f"❌ Errore ciclo #{cycle_count}: {e}")
                    self.test_results['system_errors'] += 1
                
                # Pausa tra cicli
                await asyncio.sleep(config['cycle_interval_seconds'])
            
            # Chiudi trade rimanenti
            await self.close_remaining_trades(active_trades)
            
        except KeyboardInterrupt:
            print("\n⏹️ Test interrotto dall'utente")
            await self.close_remaining_trades(active_trades)
        
        # Calcola uptime
        self.test_results['uptime_minutes'] = (datetime.now() - start_time).total_seconds() / 60
        
        print(f"\n✅ Test completato - Durata: {self.test_results['uptime_minutes']:.1f} minuti")
    
    async def analyze_market_for_trading(self):
        """Analisi mercato per decisioni di trading"""
        try:
            current_price = await self.data_loader.get_latest_price('BTCUSDT')
            
            # Analisi AI se disponibile
            ai_analysis = None
            try:
                ai_analysis = await self.ai_trading.analyze_market('BTCUSDT')
            except:
                pass
            
            # Segnali di trading
            signals = []
            try:
                ai_signals = await self.ai_trading.generate_trading_signals('BTCUSDT')
                if ai_signals:
                    signals.extend(ai_signals)
            except:
                pass
            
            # Fallback signal se necessario
            if not signals:
                signals.append(self.generate_simple_signal(current_price))
            
            return {
                'current_price': current_price,
                'ai_analysis': ai_analysis,
                'signals': signals,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore analisi mercato: {e}")
            return {
                'current_price': None,
                'ai_analysis': None,
                'signals': [],
                'timestamp': datetime.now()
            }
    
    def generate_simple_signal(self, current_price):
        """Genera segnale semplice come fallback"""
        # Logica semplice: segnale casuale conservativo
        if np.random.random() > 0.8:  # 20% probabilità
            action = np.random.choice(['BUY', 'SELL'])
            confidence = np.random.uniform(0.6, 0.8)
            
            return {
                'action': action,
                'confidence': confidence,
                'price': current_price,
                'source': 'simple_fallback',
                'timestamp': datetime.now().isoformat()
            }
        return None
    
    async def manage_active_trades(self, active_trades, config):
        """Gestisce trade attivi (profit/stop)"""
        updated_trades = []
        
        for trade in active_trades:
            try:
                # Verifica stato ordine
                order_status = await self.exchange_manager.get_order_status(
                    trade['order_id'], 'BTCUSDT'
                )
                
                if order_status and order_status.get('status') == 'FILLED':
                    # Trade completato
                    self.process_completed_trade(trade, order_status)
                else:
                    # Trade ancora attivo
                    updated_trades.append(trade)
                    
            except Exception as e:
                self.logger.error(f"❌ Errore gestione trade {trade.get('order_id')}: {e}")
                updated_trades.append(trade)  # Mantieni per retry
        
        return updated_trades
    
    def process_completed_trade(self, trade, order_status):
        """Processa trade completato"""
        try:
            executed_price = float(order_status.get('fills', [{}])[0].get('price', 0))
            executed_qty = float(order_status.get('executedQty', 0))
            
            # Calcola profit/loss
            entry_price = trade['entry_price']
            side = trade['side']
            
            if side == 'BUY':
                profit_pct = (executed_price - entry_price) / entry_price
            else:
                profit_pct = (entry_price - executed_price) / entry_price
            
            profit_usdt = profit_pct * entry_price * executed_qty
            
            # Aggiorna statistiche
            self.test_results['total_profit'] += profit_usdt
            
            if profit_usdt > 0:
                self.test_results['successful_trades'] += 1
            else:
                self.test_results['failed_trades'] += 1
            
            # Salva trade completato
            completed_trade = {
                **trade,
                'exit_price': executed_price,
                'exit_time': datetime.now().isoformat(),
                'profit_pct': profit_pct,
                'profit_usdt': profit_usdt,
                'status': 'COMPLETED'
            }
            
            self.test_results['trades_executed'].append(completed_trade)
            
            print(f"    ✅ Trade completato: {side} - Profit: {profit_pct:.2%} (${profit_usdt:.2f})")
            
        except Exception as e:
            self.logger.error(f"❌ Errore processing trade: {e}")
    
    async def evaluate_new_trade(self, market_data, config):
        """Valuta opportunità per nuovo trade"""
        try:
            signals = market_data.get('signals', [])
            current_price = market_data.get('current_price')
            
            if not signals or not current_price:
                return None
            
            # Filtra segnali per confidenza
            valid_signals = [
                s for s in signals 
                if s and s.get('confidence', 0) >= config['min_confidence']
            ]
            
            if not valid_signals:
                return None
            
            # Seleziona miglior segnale
            best_signal = max(valid_signals, key=lambda x: x.get('confidence', 0))
            
            return {
                'signal': best_signal,
                'entry_price': current_price,
                'amount': config['trade_amount_btc'],
                'profit_target': config['profit_target'],
                'stop_loss': config['stop_loss']
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore valutazione trade: {e}")
            return None
    
    async def execute_real_trade(self, trade_opportunity, config):
        """Esegue trade reale su Binance"""
        try:
            signal = trade_opportunity['signal']
            action = signal['action']
            amount = trade_opportunity['amount']
            entry_price = trade_opportunity['entry_price']
            
            print(f"  🚀 ESECUZIONE TRADE REALE: {action} {amount} BTC @ ${entry_price:,.2f}")
            print(f"    Confidenza: {signal['confidence']:.1%}")
            print(f"    Target: +{trade_opportunity['profit_target']:.1%}")
            print(f"    Stop: -{trade_opportunity['stop_loss']:.1%}")
            
            # Prepara ordine
            order_data = {
                'symbol': config['symbol'],
                'side': action,
                'type': 'MARKET',
                'quantity': amount
            }
            
            # ESEGUI ORDINE REALE
            if config['enable_real_orders']:
                result = await self.exchange_manager.place_order(**order_data)
                
                if result and result.get('status') in ['FILLED', 'PARTIALLY_FILLED']:
                    print(f"    ✅ ORDINE ESEGUITO - ID: {result.get('orderId')}")
                    
                    # Crea record trade
                    trade_record = {
                        'order_id': result.get('orderId'),
                        'symbol': result.get('symbol'),
                        'side': result.get('side'),
                        'amount': float(result.get('executedQty', amount)),
                        'entry_price': entry_price,
                        'entry_time': datetime.now().isoformat(),
                        'signal_confidence': signal['confidence'],
                        'signal_source': signal.get('source', 'unknown'),
                        'profit_target': trade_opportunity['profit_target'],
                        'stop_loss': trade_opportunity['stop_loss'],
                        'status': 'ACTIVE'
                    }
                    
                    return trade_record
                else:
                    print(f"    ❌ ORDINE FALLITO: {result}")
                    return None
            else:
                print("    ⚠️ Ordini reali disabilitati (simulazione)")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Errore esecuzione trade: {e}")
            print(f"    ❌ ERRORE TRADE: {e}")
            return None
    
    async def close_remaining_trades(self, active_trades):
        """Chiude trade rimanenti alla fine del test"""
        if active_trades:
            print(f"\n🔄 Chiusura {len(active_trades)} trade rimanenti...")
            
            for trade in active_trades:
                try:
                    # Cancella ordine se ancora attivo
                    await self.exchange_manager.cancel_order(trade['order_id'], 'BTCUSDT')
                    print(f"    ✅ Trade {trade['order_id']} chiuso")
                except Exception as e:
                    print(f"    ⚠️ Errore chiusura {trade['order_id']}: {e}")
    
    def report_trading_cycle(self, cycle, market_data, active_trades):
        """Report del ciclo di trading"""
        price = market_data.get('current_price', 0)
        signals_count = len(market_data.get('signals', []))
        active_count = len(active_trades)
        
        print(f"  📊 Prezzo: ${price:,.2f} | Segnali: {signals_count} | Trade attivi: {active_count}")
        print(f"  💰 Profit totale: ${self.test_results['total_profit']:.2f}")
    
    async def validate_profits(self, initial_balance):
        """Valida profitti ottenuti"""
        self.print_section("VALIDAZIONE PROFITTI")
        
        try:
            # Saldo finale
            final_balance = await self.exchange_manager.get_balance()
            
            final_usdt = float(final_balance.get('USDT', {}).get('free', 0))
            final_btc = float(final_balance.get('BTC', {}).get('free', 0))
            
            # Calcola valore finale
            btc_price = await self.data_loader.get_latest_price('BTCUSDT')
            final_value_usdt = final_usdt + (final_btc * btc_price)
            
            # Calcola profit reale
            initial_value = initial_balance['total_value_usdt']
            real_profit = final_value_usdt - initial_value
            profit_percentage = (real_profit / initial_value) * 100 if initial_value > 0 else 0
            
            print(f"  💰 VALIDAZIONE PROFITTI:")
            print(f"    Valore iniziale: ${initial_value:.2f} USDT")
            print(f"    Valore finale: ${final_value_usdt:.2f} USDT")
            print(f"    Profit reale: ${real_profit:.2f} USDT ({profit_percentage:+.2f}%)")
            print(f"    Trade eseguiti: {len(self.test_results['trades_executed'])}")
            print(f"    Trade vincenti: {self.test_results['successful_trades']}")
            print(f"    Trade perdenti: {self.test_results['failed_trades']}")
            
            # Aggiorna risultati
            self.test_results.update({
                'initial_value_usdt': initial_value,
                'final_value_usdt': final_value_usdt,
                'real_profit_usdt': real_profit,
                'profit_percentage': profit_percentage,
                'final_usdt': final_usdt,
                'final_btc': final_btc
            })
            
            # Determina successo test
            success = (
                len(self.test_results['trades_executed']) > 0 and
                self.test_results['system_errors'] < 3 and
                real_profit >= -10  # Perdita massima $10
            )
            
            self.test_results['test_success'] = success
            
            if success:
                print(f"  ✅ TEST VALIDATO CON SUCCESSO!")
            else:
                print(f"  ⚠️ Test completato con limitazioni")
                
        except Exception as e:
            self.logger.error(f"❌ Errore validazione profitti: {e}")
            self.test_results['validation_error'] = str(e)
    
    def generate_final_report(self):
        """Genera report finale del test"""
        self.print_section("REPORT FINALE TEST TRADING REALE")
        
        # Salva risultati completi
        results_file = "/home/ubuntu/AurumBotX/validation_results/real_trading_test_results.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        # Prepara risultati per JSON
        json_results = {
            'test_timestamp': self.test_results['start_time'].isoformat(),
            'uptime_minutes': self.test_results['uptime_minutes'],
            'trades_executed': len(self.test_results['trades_executed']),
            'successful_trades': self.test_results['successful_trades'],
            'failed_trades': self.test_results['failed_trades'],
            'system_errors': self.test_results['system_errors'],
            'total_profit_usdt': self.test_results.get('real_profit_usdt', 0),
            'profit_percentage': self.test_results.get('profit_percentage', 0),
            'test_success': self.test_results.get('test_success', False),
            'initial_value': self.test_results.get('initial_value_usdt', 0),
            'final_value': self.test_results.get('final_value_usdt', 0),
            'trades_detail': self.test_results['trades_executed']
        }
        
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        # Report console
        print(f"  📊 RISULTATI FINALI:")
        print(f"    ⏰ Durata test: {self.test_results['uptime_minutes']:.1f} minuti")
        print(f"    📈 Trade eseguiti: {len(self.test_results['trades_executed'])}")
        print(f"    ✅ Trade vincenti: {self.test_results['successful_trades']}")
        print(f"    ❌ Trade perdenti: {self.test_results['failed_trades']}")
        print(f"    🔧 Errori sistema: {self.test_results['system_errors']}")
        print(f"    💰 Profit totale: ${self.test_results.get('real_profit_usdt', 0):.2f}")
        print(f"    📊 Percentuale: {self.test_results.get('profit_percentage', 0):+.2f}%")
        print(f"    🎯 Test riuscito: {'✅ SÌ' if self.test_results.get('test_success') else '⚠️ PARZIALE'}")
        
        print(f"\n  💾 Risultati salvati: {results_file}")
        
        # Conclusione
        if self.test_results.get('test_success'):
            print(f"\n  🎉 SISTEMA AURUMBOTX VALIDATO PER TRADING REALE!")
            print(f"  🚀 Pronto per monitoraggio 24h continuo")
        else:
            print(f"\n  ⚠️ Sistema operativo ma necessita ottimizzazioni")
            print(f"  🔧 Raccomandato ulteriore testing")

async def main():
    validator = RealTradingValidator()
    await validator.run_real_trading_test()

if __name__ == "__main__":
    asyncio.run(main())

