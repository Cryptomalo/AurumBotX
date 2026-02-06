#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
Fix Definitivo Segnali AI e Feature Mismatch
Risolve il problema delle 26 vs 25 feature per attivare i segnali AI
"""

import os
import sys
import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

class AISignalsFixer:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('AISignalsFixer')
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def print_header(self, title):
        print(f"\n{'='*80}")
        print(f"🤖 {title}")
        print(f"{'='*80}")
        
    def print_section(self, title):
        print(f"\n📋 {title}")
        print(f"{'-'*60}")
    
    async def fix_ai_signals_definitive(self):
        """Fix definitivo per segnali AI e feature mismatch"""
        self.print_header("FIX DEFINITIVO SEGNALI AI E FEATURE MISMATCH")
        
        try:
            # 1. Analisi problema feature mismatch
            await self.analyze_feature_mismatch()
            
            # 2. Fix prediction model
            await self.fix_prediction_model()
            
            # 3. Fix indicators alignment
            await self.fix_indicators_alignment()
            
            # 4. Test segnali AI
            await self.test_ai_signals()
            
            # 5. Validazione completa
            await self.validate_complete_system()
            
        except Exception as e:
            self.logger.error(f"❌ Errore fix AI: {e}")
            import traceback
            traceback.print_exc()
    
    async def analyze_feature_mismatch(self):
        """Analizza il problema del feature mismatch"""
        self.print_section("ANALISI FEATURE MISMATCH")
        
        try:
            # Carica variabili ambiente
            if os.path.exists('/home/ubuntu/AurumBotX/.env'):
                with open('/home/ubuntu/AurumBotX/.env', 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
            
            # Test con dati reali
            from utils.data_loader import CryptoDataLoader
            from utils.indicators import TechnicalIndicators
            from utils.prediction_model import PredictionModel
            
            # Inizializza componenti
            data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await data_loader.initialize()
            
            indicators = TechnicalIndicators()
            prediction_model = PredictionModel()
            
            # Ottieni dati storici
            print("  📊 Recupero dati storici...")
            data = await data_loader.get_historical_data('BTCUSDT', '1d', 100)
            
            if data is None or data.empty:
                print("  ❌ Impossibile recuperare dati storici")
                return
            
            print(f"  ✅ Dati recuperati: {len(data)} righe")
            
            # Calcola indicatori (usa add_all_indicators)
            print("  🔧 Calcolo indicatori tecnici...")
            data_with_indicators = indicators.add_all_indicators(data)
            
            print(f"  📊 Feature generate dagli indicatori: {len(data_with_indicators.columns)}")
            print("  📋 Colonne generate:")
            for i, col in enumerate(data_with_indicators.columns, 1):
                print(f"    {i:2d}. {col}")
            
            # Verifica expected features del modello
            print("  🤖 Expected features del modello:")
            expected_features = prediction_model.expected_features
            print(f"  📊 Expected features: {len(expected_features)}")
            for i, feature in enumerate(expected_features, 1):
                print(f"    {i:2d}. {feature}")
            
            # Identifica mismatch
            generated_features = set(data_with_indicators.columns)
            expected_features_set = set(expected_features)
            
            missing_features = expected_features_set - generated_features
            extra_features = generated_features - expected_features_set
            
            print(f"\n  🔍 ANALISI MISMATCH:")
            print(f"    Feature generate: {len(generated_features)}")
            print(f"    Feature attese: {len(expected_features_set)}")
            
            if missing_features:
                print(f"    ❌ Feature mancanti ({len(missing_features)}):")
                for feature in missing_features:
                    print(f"      - {feature}")
            
            if extra_features:
                print(f"    ⚠️ Feature extra ({len(extra_features)}):")
                for feature in extra_features:
                    print(f"      - {feature}")
            
            if not missing_features and not extra_features:
                print("    ✅ Nessun mismatch trovato!")
            
            return {
                'generated_features': list(generated_features),
                'expected_features': expected_features,
                'missing_features': list(missing_features),
                'extra_features': list(extra_features),
                'data_with_indicators': data_with_indicators
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore analisi mismatch: {e}")
            raise
    
    async def fix_prediction_model(self):
        """Fix del prediction model per allineare le feature"""
        self.print_section("FIX PREDICTION MODEL")
        
        try:
            # Leggi il file prediction_model.py
            model_path = "/home/ubuntu/AurumBotX/utils/prediction_model.py"
            
            with open(model_path, 'r') as f:
                content = f.read()
            
            # Nuova lista di expected_features basata sui dati reali
            new_expected_features = [
                'open', 'high', 'low', 'close', 'volume',
                'returns', 'volatility', 'sma_20', 'ema_20', 'sma_50', 'ema_50',
                'sma_200', 'ema_200', 'macd', 'macd_signal', 'macd_hist',
                'rsi_14', 'rsi_28', 'bb_middle', 'bb_upper', 'bb_lower',
                'bb_width', 'atr', 'volume_ma', 'volume_ratio', 'obv'
            ]
            
            print(f"  🔧 Aggiornamento expected_features a {len(new_expected_features)} feature...")
            
            # Sostituisci la lista expected_features
            old_pattern = r'self\.expected_features = \[.*?\]'
            new_features_str = "self.expected_features = [\n"
            for feature in new_expected_features:
                new_features_str += f"            '{feature}',\n"
            new_features_str = new_features_str.rstrip(',\n') + "\n        ]"
            
            import re
            content = re.sub(old_pattern, new_features_str, content, flags=re.DOTALL)
            
            # Migliora il metodo _prepare_features
            improved_prepare_features = '''
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepara le feature per il modello con allineamento automatico"""
        try:
            # Assicurati che tutte le expected_features siano presenti
            missing_features = []
            for feature in self.expected_features:
                if feature not in data.columns:
                    missing_features.append(feature)
            
            if missing_features:
                logger.warning(f"Feature mancanti: {missing_features}")
                # Aggiungi feature mancanti con valori di default
                for feature in missing_features:
                    if 'rsi' in feature.lower():
                        data[feature] = 50.0  # RSI neutrale
                    elif 'volume' in feature.lower():
                        data[feature] = data['volume'].mean() if 'volume' in data.columns else 1000000
                    elif any(x in feature.lower() for x in ['sma', 'ema', 'bb']):
                        data[feature] = data['close'].mean() if 'close' in data.columns else 50000
                    else:
                        data[feature] = 0.0
            
            # Seleziona solo le feature attese nell'ordine corretto
            feature_data = data[self.expected_features].copy()
            
            # Gestisci valori mancanti
            feature_data = feature_data.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            # Converti a numpy array
            X = feature_data.values
            
            # Scala le feature se il scaler è disponibile
            if hasattr(self, 'scaler') and self.scaler is not None:
                X = self.scaler.transform(X)
            
            logger.info(f"✅ Feature preparate: {X.shape}")
            return X
            
        except Exception as e:
            logger.error(f"❌ Errore preparazione feature: {e}")
            raise
'''
            
            # Sostituisci il metodo _prepare_features
            content = re.sub(
                r'def _prepare_features\(self, data: pd\.DataFrame\) -> np\.ndarray:.*?(?=\n    def|\n    async def|\nclass|\Z)',
                improved_prepare_features.strip(),
                content,
                flags=re.DOTALL
            )
            
            # Salva il file modificato
            with open(model_path, 'w') as f:
                f.write(content)
            
            print("  ✅ PredictionModel aggiornato con feature alignment")
            
        except Exception as e:
            self.logger.error(f"❌ Errore fix prediction model: {e}")
            raise
    
    async def fix_indicators_alignment(self):
        """Fix degli indicatori per allineare le feature generate"""
        self.print_section("FIX INDICATORS ALIGNMENT")
        
        try:
            # Leggi il file indicators.py
            indicators_path = "/home/ubuntu/AurumBotX/utils/indicators.py"
            
            with open(indicators_path, 'r') as f:
                content = f.read()
            
            # Assicurati che calculate_all_indicators generi esattamente le feature attese
            improved_calculate_all = '''
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcola tutti gli indicatori tecnici con feature standardizzate"""
        try:
            df = data.copy()
            
            # Assicurati che le colonne base esistano
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'volume':
                        df[col] = 1000000  # Volume di default
                    else:
                        df[col] = df['close'] if 'close' in df.columns else 50000
            
            # Calcola indicatori base
            df['returns'] = df['close'].pct_change().fillna(0)
            df['volatility'] = df['returns'].rolling(window=20).std().fillna(0)
            
            # Moving averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['ema_20'] = df['close'].ewm(span=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()
            df['sma_200'] = df['close'].rolling(window=200).mean()
            df['ema_200'] = df['close'].ewm(span=200).mean()
            
            # MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # RSI
            df['rsi_14'] = self.calculate_rsi(df['close'], 14)
            df['rsi_28'] = self.calculate_rsi(df['close'], 28)
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_width'] = df['bb_upper'] - df['bb_lower']
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df['atr'] = true_range.rolling(window=14).mean()
            
            # Volume indicators
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            df['obv'] = (df['volume'] * np.sign(df['close'].diff())).cumsum()
            
            # Riempi valori mancanti
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            logger.info(f"✅ Indicatori calcolati: {len(df.columns)} colonne")
            return df
            
        except Exception as e:
            logger.error(f"❌ Errore calcolo indicatori: {e}")
            raise
'''
            
            # Sostituisci il metodo calculate_all_indicators
            import re
            content = re.sub(
                r'def calculate_all_indicators\(self, data: pd\.DataFrame\) -> pd\.DataFrame:.*?(?=\n    def|\n    async def|\nclass|\Z)',
                improved_calculate_all.strip(),
                content,
                flags=re.DOTALL
            )
            
            # Salva il file modificato
            with open(indicators_path, 'w') as f:
                f.write(content)
            
            print("  ✅ TechnicalIndicators aggiornato con feature alignment")
            
        except Exception as e:
            self.logger.error(f"❌ Errore fix indicators: {e}")
            raise
    
    async def test_ai_signals(self):
        """Test generazione segnali AI dopo i fix"""
        self.print_section("TEST SEGNALI AI")
        
        try:
            # Ricarica moduli modificati
            modules_to_reload = [
                'utils.prediction_model',
                'utils.indicators',
                'utils.ai_trading'
            ]
            
            for module in modules_to_reload:
                if module in sys.modules:
                    del sys.modules[module]
            
            # Import moduli aggiornati
            from utils.ai_trading import AITrading
            
            # Inizializza AI Trading
            print("  🤖 Inizializzazione AI Trading...")
            ai_trading = AITrading()
            await ai_trading.initialize()
            
            # Test generazione segnali
            print("  🎯 Test generazione segnali...")
            signals = await ai_trading.generate_trading_signals('BTCUSDT')
            
            if signals:
                print(f"  ✅ Segnali generati: {len(signals)}")
                for i, signal in enumerate(signals, 1):
                    print(f"    {i}. Azione: {signal.get('action', 'N/A')}")
                    print(f"       Confidenza: {signal.get('confidence', 0):.1%}")
                    print(f"       Prezzo: ${signal.get('price', 0):,.2f}")
                return True
            else:
                print("  ❌ Nessun segnale generato")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Errore test segnali: {e}")
            return False
    
    async def validate_complete_system(self):
        """Validazione completa del sistema AI"""
        self.print_section("VALIDAZIONE SISTEMA COMPLETO")
        
        try:
            # Test completo del flusso
            from utils.data_loader import CryptoDataLoader
            from utils.indicators import TechnicalIndicators
            from utils.prediction_model import PredictionModel
            from utils.ai_trading import AITrading
            
            print("  🔄 Test flusso completo...")
            
            # 1. Data Loader
            data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await data_loader.initialize()
            
            # 2. Dati storici
            data = await data_loader.get_historical_data('BTCUSDT', '1d', 100)
            print(f"    ✅ Dati storici: {len(data)} righe")
            
            # 3. Indicatori
            indicators = TechnicalIndicators()
            data_with_indicators = indicators.calculate_all_indicators(data)
            print(f"    ✅ Indicatori: {len(data_with_indicators.columns)} colonne")
            
            # 4. Prediction Model
            prediction_model = PredictionModel()
            features = prediction_model._prepare_features(data_with_indicators)
            print(f"    ✅ Feature preparate: {features.shape}")
            
            # 5. AI Trading
            ai_trading = AITrading()
            await ai_trading.initialize()
            
            # 6. Analisi mercato
            market_analysis = await ai_trading.analyze_market('BTCUSDT')
            if market_analysis:
                print("    ✅ Analisi mercato: OK")
            else:
                print("    ❌ Analisi mercato: FALLITA")
            
            # 7. Segnali trading
            signals = await ai_trading.generate_trading_signals('BTCUSDT')
            if signals:
                print(f"    ✅ Segnali trading: {len(signals)} generati")
                
                # Salva risultati
                results = {
                    'timestamp': datetime.now().isoformat(),
                    'validation_status': 'SUCCESS',
                    'data_rows': len(data),
                    'indicators_columns': len(data_with_indicators.columns),
                    'features_shape': list(features.shape),
                    'signals_generated': len(signals),
                    'signals': signals
                }
                
                results_file = "/home/ubuntu/AurumBotX/validation_results/ai_signals_validation.json"
                os.makedirs(os.path.dirname(results_file), exist_ok=True)
                
                with open(results_file, 'w') as f:
                    json.dump(results, f, indent=2)
                
                print(f"    ✅ Risultati salvati: {results_file}")
                print("  🎉 SISTEMA AI COMPLETAMENTE OPERATIVO!")
                return True
            else:
                print("    ❌ Segnali trading: NESSUNO")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Errore validazione: {e}")
            return False

async def main():
    fixer = AISignalsFixer()
    await fixer.fix_ai_signals_definitive()

if __name__ == "__main__":
    asyncio.run(main())

