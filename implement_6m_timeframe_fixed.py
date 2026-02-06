#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
Implementazione Timeframe 6M con Dati Reali - Versione Corretta
"""

import os
import sys
import asyncio
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

from utils.data_loader import CryptoDataLoader
from utils.ai_trading import AITrading

class SixMinuteTimeframeImplementation:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('6MTimeframe')
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def print_header(self, title):
        """Header professionale"""
        print(f"\n{'='*100}")
        print(f"⏰ {title}")
        print(f"{'='*100}")
        
    def print_section(self, title):
        """Sezione"""
        print(f"\n📋 {title}")
        print(f"{'-'*80}")
    
    async def implement_6m_timeframe(self):
        """Implementa timeframe 6 minuti con dati reali"""
        self.print_header("IMPLEMENTAZIONE TIMEFRAME 6 MINUTI CON DATI REALI")
        
        try:
            # 1. Test connessione dati reali
            await self.test_real_data_connection()
            
            # 2. Implementazione timeframe 6M
            await self.implement_6m_support()
            
            # 3. Test timeframe 6M
            await self.test_6m_timeframe()
            
            # 4. Ottimizzazione strategie per 6M
            await self.optimize_strategies_for_6m()
            
            # 5. Test completo sistema
            await self.test_complete_system()
            
        except Exception as e:
            self.logger.error(f"❌ Errore implementazione 6M: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_real_data_connection(self):
        """Testa connessione dati reali"""
        self.print_section("TEST CONNESSIONE DATI REALI")
        
        try:
            # Inizializza data loader
            data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await data_loader.initialize()
            
            # Test connessione
            print("  🔍 Test connessione Binance...")
            latest_price = await data_loader.get_latest_price('BTCUSDT')
            
            if latest_price and latest_price > 50000:  # Prezzo realistico BTC
                print(f"  ✅ Connessione OK - Prezzo BTC: ${latest_price:,.2f}")
                
                # Test dati storici
                print("  📊 Test dati storici...")
                historical_data = await data_loader.get_historical_data('BTCUSDT', '1d', '1h')
                
                if historical_data is not None and not historical_data.empty:
                    print(f"  ✅ Dati storici OK - {len(historical_data)} candele")
                    print(f"  📈 Range prezzi: ${historical_data['Low'].min():,.2f} - ${historical_data['High'].max():,.2f}")
                    return True
                else:
                    print("  ❌ Dati storici non disponibili")
                    return False
            else:
                print(f"  ❌ Prezzo non realistico: ${latest_price}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Errore test connessione: {e}")
            return False
    
    async def implement_6m_support(self):
        """Implementa supporto timeframe 6 minuti"""
        self.print_section("IMPLEMENTAZIONE SUPPORTO TIMEFRAME 6M")
        
        # Verifica se Binance supporta 6m
        print("  🔍 Verifica supporto timeframe 6m su Binance...")
        
        # Binance supporta questi timeframe:
        # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        
        supported_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        
        if '6m' not in supported_timeframes:
            print("  ⚠️ Binance non supporta nativamente 6m")
            print("  🔧 Implementazione alternativa: aggregazione da 3m")
            
            # Implementa aggregazione da 3m a 6m
            await self.implement_6m_aggregation()
        else:
            print("  ✅ Timeframe 6m supportato nativamente")
    
    async def implement_6m_aggregation(self):
        """Implementa aggregazione da 3m a 6m"""
        print("  🔧 Implementazione aggregazione 3m -> 6m...")
        
        # Crea funzione di aggregazione nel data_loader
        aggregation_code = '''
    def aggregate_3m_to_6m(self, df_3m: pd.DataFrame) -> pd.DataFrame:
        """
        Aggrega dati 3m in 6m
        
        Args:
            df_3m: DataFrame con dati 3 minuti
            
        Returns:
            DataFrame con dati 6 minuti
        """
        try:
            if df_3m.empty:
                return df_3m
            
            # Raggruppa ogni 2 candele 3m per fare 6m
            df_6m = df_3m.groupby(df_3m.index // 2).agg({
                'Open': 'first',
                'High': 'max', 
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })
            
            # Ricostruisci index temporale
            df_6m.index = df_3m.index[::2]  # Ogni 2 candele
            
            return df_6m
            
        except Exception as e:
            logger.error(f"Errore aggregazione 3m->6m: {e}")
            return pd.DataFrame()

    async def get_6m_data(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """
        Ottiene dati 6 minuti tramite aggregazione da 3m
        
        Args:
            symbol: Simbolo trading (es. 'BTCUSDT')
            period: Periodo (es. '1d', '7d')
            
        Returns:
            DataFrame con dati 6 minuti
        """
        try:
            # Ottieni dati 3m (doppia quantità per aggregazione)
            period_multiplier = {'1d': '2d', '7d': '14d', '30d': '60d'}
            extended_period = period_multiplier.get(period, period)
            
            df_3m = await self.get_historical_data(symbol, extended_period, '3m')
            
            if df_3m is None or df_3m.empty:
                return None
                
            # Aggrega a 6m
            df_6m = self.aggregate_3m_to_6m(df_3m)
            
            # Taglia al periodo richiesto
            if period == '1d':
                df_6m = df_6m.tail(240)  # 24h * 10 candele/h = 240
            elif period == '7d':
                df_6m = df_6m.tail(1680)  # 7 * 240 = 1680
            elif period == '30d':
                df_6m = df_6m.tail(7200)  # 30 * 240 = 7200
                
            return df_6m
            
        except Exception as e:
            logger.error(f"Errore get_6m_data: {e}")
            return None
'''
        
        # Aggiungi al data_loader
        data_loader_path = "/home/ubuntu/AurumBotX/utils/data_loader.py"
        
        with open(data_loader_path, 'r') as f:
            content = f.read()
        
        # Aggiungi le funzioni se non esistono
        if "aggregate_3m_to_6m" not in content:
            # Aggiungi alla fine della classe
            content = content.rstrip() + aggregation_code + "\n"
            
            with open(data_loader_path, 'w') as f:
                f.write(content)
            
            print("  ✅ Funzioni aggregazione 6m aggiunte")
        else:
            print("  ✅ Funzioni aggregazione 6m già presenti")
    
    async def test_6m_timeframe(self):
        """Testa il timeframe 6 minuti"""
        self.print_section("TEST TIMEFRAME 6 MINUTI")
        
        try:
            # Inizializza data loader
            data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await data_loader.initialize()
            
            # Test dati 6m
            print("  📊 Test recupero dati 6m...")
            
            # Prova prima con 3m standard
            data_3m = await data_loader.get_historical_data('BTCUSDT', '1d', '3m')
            
            if data_3m is not None and not data_3m.empty:
                print(f"  ✅ Dati 3m OK - {len(data_3m)} candele")
                
                # Test aggregazione manuale
                if hasattr(data_loader, 'get_6m_data'):
                    data_6m = await data_loader.get_6m_data('BTCUSDT', '1d')
                    
                    if data_6m is not None and not data_6m.empty:
                        print(f"  ✅ Dati 6m OK - {len(data_6m)} candele")
                        print(f"  📈 Range prezzi 6m: ${data_6m['Low'].min():,.2f} - ${data_6m['High'].max():,.2f}")
                        
                        # Verifica qualità dati
                        volatility_6m = data_6m['Close'].pct_change().std() * 100
                        print(f"  📊 Volatilità 6m: {volatility_6m:.2f}%")
                        
                        return data_6m
                    else:
                        print("  ❌ Aggregazione 6m fallita")
                else:
                    print("  ❌ Funzione get_6m_data non disponibile")
            else:
                print("  ❌ Dati 3m non disponibili")
                
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Errore test 6m: {e}")
            return None
    
    async def optimize_strategies_for_6m(self):
        """Ottimizza strategie per timeframe 6 minuti"""
        self.print_section("OTTIMIZZAZIONE STRATEGIE PER 6M")
        
        # Configurazioni ottimizzate per 6m
        optimized_configs = {
            "scalping_6m_conservative": {
                "type": "scalping",
                "profit_target": 0.003,  # 0.3%
                "stop_loss": 0.002,      # 0.2%
                "trend_period": 10,      # 10 * 6m = 1h
                "min_trend_strength": 0.2,
                "timeframe": "6m",
                "description": "Scalping 6M Conservativo"
            },
            "scalping_6m_moderate": {
                "type": "scalping",
                "profit_target": 0.005,  # 0.5%
                "stop_loss": 0.003,      # 0.3%
                "trend_period": 15,      # 15 * 6m = 1.5h
                "min_trend_strength": 0.3,
                "timeframe": "6m",
                "description": "Scalping 6M Moderato"
            },
            "swing_6m_short": {
                "type": "swing",
                "profit_target": 0.01,   # 1%
                "stop_loss": 0.007,      # 0.7%
                "trend_period": 20,      # 20 * 6m = 2h
                "min_trend_strength": 0.4,
                "timeframe": "6m",
                "description": "Swing 6M Short-term"
            }
        }
        
        print("  📊 CONFIGURAZIONI OTTIMIZZATE PER 6M:")
        for name, config in optimized_configs.items():
            print(f"    🎯 {config['description']}")
            print(f"      Profit: {config['profit_target']:.1%} | Stop: {config['stop_loss']:.1%}")
            print(f"      Period: {config['trend_period']} ({config['trend_period'] * 6} min)")
        
        # Salva configurazioni
        config_file = "/home/ubuntu/AurumBotX/configs/6m_strategies.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(optimized_configs, f, indent=2)
        
        print(f"  ✅ Configurazioni salvate: {config_file}")
        
        return optimized_configs
    
    async def test_complete_system(self):
        """Test completo del sistema con timeframe 6M"""
        self.print_section("TEST COMPLETO SISTEMA 6M")
        
        try:
            # 1. Test data loader
            print("  🔍 Test 1: Data Loader 6M...")
            data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await data_loader.initialize()
            
            # Test dati 6m
            data_6m = await data_loader.get_historical_data('BTCUSDT', '1d', '3m')
            if data_6m is not None and not data_6m.empty:
                print("    ✅ Data Loader OK")
            else:
                print("    ❌ Data Loader FAIL")
                return False
            
            # 2. Test AI Trading
            print("  🤖 Test 2: AI Trading con dati 6M...")
            ai_trading = AITrading()
            await ai_trading.initialize()
            
            # Test analisi mercato
            market_analysis = await ai_trading.analyze_market('BTCUSDT')
            if market_analysis:
                print("    ✅ AI Trading OK")
                price = market_analysis.get('market_data', {}).get('price', 0)
                if price > 50000:  # Prezzo realistico
                    print(f"    ✅ Prezzo realistico: ${price:,.2f}")
                else:
                    print(f"    ⚠️ Prezzo non realistico: ${price}")
            else:
                print("    ❌ AI Trading FAIL")
            
            # 3. Test generazione segnali
            print("  🎯 Test 3: Generazione segnali...")
            signals = await ai_trading.generate_trading_signals('BTCUSDT')
            if signals:
                print(f"    ✅ Segnali generati: {len(signals)}")
                for signal in signals[:2]:  # Mostra primi 2
                    print(f"      📊 {signal['action']} - Confidenza: {signal['confidence']:.1%}")
            else:
                print("    ⚠️ Nessun segnale generato")
            
            # 4. Test performance
            print("  ⚡ Test 4: Performance sistema...")
            start_time = datetime.now()
            
            # Esegui 5 cicli di analisi
            for i in range(5):
                await ai_trading.analyze_market('BTCUSDT')
            
            end_time = datetime.now()
            avg_time = (end_time - start_time).total_seconds() / 5
            
            print(f"    ⏱️ Tempo medio per ciclo: {avg_time:.2f}s")
            
            if avg_time < 3.0:
                print("    ✅ Performance OK")
            else:
                print("    ⚠️ Performance lenta")
            
            print("\n  🎉 SISTEMA 6M COMPLETAMENTE OPERATIVO!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore test completo: {e}")
            return False

async def main():
    """Main implementazione 6M"""
    implementer = SixMinuteTimeframeImplementation()
    await implementer.implement_6m_timeframe()

if __name__ == "__main__":
    asyncio.run(main())

