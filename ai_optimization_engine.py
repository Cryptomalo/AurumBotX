#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX AI Optimization Engine
Sistema avanzato di ottimizzazione AI per migliorare predizioni e performance
"""

import os
import sys
import asyncio
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import sqlite3
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIOptimization')

class AdvancedFeatureEngineer:
    """Ingegnere delle feature avanzato per AI"""
    
    def __init__(self):
        self.logger = logging.getLogger('FeatureEngineer')
        self.scalers = {}
        self.feature_importance = {}
    
    def create_advanced_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Crea feature avanzate per AI"""
        try:
            self.logger.info(f"🔧 Creazione feature avanzate da {len(data)} righe...")
            
            # Copia dati
            df = data.copy()
            
            # 1. Feature tecniche base
            df = self._add_technical_indicators(df)
            
            # 2. Feature di momentum
            df = self._add_momentum_features(df)
            
            # 3. Feature di volatilità
            df = self._add_volatility_features(df)
            
            # 4. Feature di volume
            df = self._add_volume_features(df)
            
            # 5. Feature di pattern
            df = self._add_pattern_features(df)
            
            # 6. Feature di sentiment (simulato)
            df = self._add_sentiment_features(df)
            
            # 7. Feature di time series
            df = self._add_time_features(df)
            
            # 8. Feature di cross-correlation
            df = self._add_correlation_features(df)
            
            # 9. Pulizia finale
            df = self._clean_features(df)
            
            self.logger.info(f"✅ Feature create: {len(df.columns)} colonne totali")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore creazione feature: {e}")
            return data
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge indicatori tecnici avanzati"""
        try:
            # SMA multiple
            for period in [5, 10, 20, 50, 100]:
                df[f'sma_{period}'] = df['close'].rolling(period, min_periods=1).mean()
            
            # EMA multiple
            for period in [5, 10, 20, 50]:
                df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            
            # RSI multiple
            for period in [7, 14, 21]:
                df[f'rsi_{period}'] = self._calculate_rsi(df['close'], period)
            
            # MACD variations
            df['macd_12_26'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd_12_26'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd_12_26'] - df['macd_signal']
            
            # Bollinger Bands multiple
            for period in [10, 20, 50]:
                bb_middle = df['close'].rolling(period, min_periods=1).mean()
                bb_std = df['close'].rolling(period, min_periods=1).std()
                df[f'bb_upper_{period}'] = bb_middle + (bb_std * 2)
                df[f'bb_lower_{period}'] = bb_middle - (bb_std * 2)
                df[f'bb_width_{period}'] = df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']
                df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / df[f'bb_width_{period}']
            
            # Stochastic Oscillator
            df['stoch_k'] = self._calculate_stochastic(df)
            df['stoch_d'] = df['stoch_k'].rolling(3, min_periods=1).mean()
            
            # Williams %R
            df['williams_r'] = self._calculate_williams_r(df)
            
            # CCI (Commodity Channel Index)
            df['cci'] = self._calculate_cci(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore indicatori tecnici: {e}")
            return df
    
    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge feature di momentum"""
        try:
            # Price changes multiple timeframes
            for period in [1, 3, 5, 10, 20]:
                df[f'price_change_{period}'] = df['close'].pct_change(period)
                df[f'price_change_abs_{period}'] = df[f'price_change_{period}'].abs()
            
            # Momentum indicators
            df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
            df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
            
            # Rate of Change
            for period in [5, 10, 20]:
                df[f'roc_{period}'] = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
            
            # Acceleration (second derivative)
            df['acceleration'] = df['price_change_1'].diff()
            
            # Velocity (smoothed momentum)
            df['velocity'] = df['price_change_1'].rolling(5, min_periods=1).mean()
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore feature momentum: {e}")
            return df
    
    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge feature di volatilità"""
        try:
            # True Range
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            
            # Average True Range
            for period in [7, 14, 21]:
                df[f'atr_{period}'] = df['tr'].rolling(period, min_periods=1).mean()
            
            # Volatility (rolling std)
            for period in [5, 10, 20, 50]:
                df[f'volatility_{period}'] = df['close'].rolling(period, min_periods=1).std()
                df[f'volatility_ratio_{period}'] = df[f'volatility_{period}'] / df['close']
            
            # Intraday volatility
            df['intraday_volatility'] = (df['high'] - df['low']) / df['close']
            
            # Gap analysis
            df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
            df['gap_abs'] = df['gap'].abs()
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore feature volatilità: {e}")
            return df
    
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge feature di volume"""
        try:
            # Volume moving averages
            for period in [5, 10, 20, 50]:
                df[f'volume_sma_{period}'] = df['volume'].rolling(period, min_periods=1).mean()
                df[f'volume_ratio_{period}'] = df['volume'] / df[f'volume_sma_{period}']
            
            # Volume-Price Trend
            df['vpt'] = (df['volume'] * df['price_change_1']).cumsum()
            
            # On-Balance Volume
            df['obv'] = (df['volume'] * np.sign(df['price_change_1'])).cumsum()
            
            # Volume Rate of Change
            for period in [5, 10]:
                df[f'volume_roc_{period}'] = df['volume'].pct_change(period)
            
            # Money Flow Index (simplified)
            df['money_flow'] = df['volume'] * ((df['high'] + df['low'] + df['close']) / 3)
            df['mfi'] = df['money_flow'].rolling(14, min_periods=1).mean()
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore feature volume: {e}")
            return df
    
    def _add_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge feature di pattern recognition"""
        try:
            # Candlestick patterns (simplified)
            df['body_size'] = abs(df['close'] - df['open']) / df['close']
            df['upper_shadow'] = (df['high'] - np.maximum(df['open'], df['close'])) / df['close']
            df['lower_shadow'] = (np.minimum(df['open'], df['close']) - df['low']) / df['close']
            
            # Doji pattern
            df['is_doji'] = (df['body_size'] < 0.001).astype(int)
            
            # Hammer pattern
            df['is_hammer'] = ((df['lower_shadow'] > 2 * df['body_size']) & 
                              (df['upper_shadow'] < df['body_size'])).astype(int)
            
            # Engulfing patterns
            df['bullish_engulfing'] = ((df['close'] > df['open']) & 
                                      (df['close'].shift(1) < df['open'].shift(1)) &
                                      (df['open'] < df['close'].shift(1)) &
                                      (df['close'] > df['open'].shift(1))).astype(int)
            
            # Support/Resistance levels (simplified)
            df['local_high'] = df['high'].rolling(5, center=True, min_periods=1).max() == df['high']
            df['local_low'] = df['low'].rolling(5, center=True, min_periods=1).min() == df['low']
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore feature pattern: {e}")
            return df
    
    def _add_sentiment_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge feature di sentiment (simulate)"""
        try:
            # Fear & Greed Index (simulated)
            df['fear_greed'] = 50 + 30 * np.sin(np.arange(len(df)) * 0.1) + np.random.normal(0, 10, len(df))
            df['fear_greed'] = np.clip(df['fear_greed'], 0, 100)
            
            # Market sentiment based on price action
            df['bullish_sentiment'] = (df['close'] > df['sma_20']).astype(int)
            df['bearish_sentiment'] = (df['close'] < df['sma_20']).astype(int)
            
            # Trend strength
            df['trend_strength'] = abs(df['close'] - df['sma_50']) / df['sma_50']
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore feature sentiment: {e}")
            return df
    
    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge feature temporali"""
        try:
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['hour'] = df['timestamp'].dt.hour
                df['day_of_week'] = df['timestamp'].dt.dayofweek
                df['day_of_month'] = df['timestamp'].dt.day
                df['month'] = df['timestamp'].dt.month
                
                # Cyclical encoding
                df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
                df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
                df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
                df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            
            # Sequence features
            df['sequence_id'] = np.arange(len(df))
            df['sequence_normalized'] = df['sequence_id'] / len(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore feature temporali: {e}")
            return df
    
    def _add_correlation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge feature di correlazione"""
        try:
            # Price-Volume correlation
            df['price_volume_corr'] = df['close'].rolling(20, min_periods=1).corr(df['volume'])
            
            # High-Low correlation with volume
            df['hl_volume_corr'] = (df['high'] - df['low']).rolling(20, min_periods=1).corr(df['volume'])
            
            # Cross-correlation between different timeframes
            df['sma_5_20_ratio'] = df['sma_5'] / df['sma_20']
            df['sma_20_50_ratio'] = df['sma_20'] / df['sma_50']
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore feature correlazione: {e}")
            return df
    
    def _clean_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pulisce e normalizza le feature"""
        try:
            # Rimuovi infiniti e NaN
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            # Clip outliers (3 sigma rule)
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if col not in ['timestamp', 'sequence_id']:
                    mean = df[col].mean()
                    std = df[col].std()
                    df[col] = np.clip(df[col], mean - 3*std, mean + 3*std)
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Errore pulizia feature: {e}")
            return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcola RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
            loss = loss.replace(0, 0.01)
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except:
            return pd.Series([50] * len(prices), index=prices.index)
    
    def _calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calcola Stochastic Oscillator"""
        try:
            low_min = df['low'].rolling(period, min_periods=1).min()
            high_max = df['high'].rolling(period, min_periods=1).max()
            return 100 * (df['close'] - low_min) / (high_max - low_min)
        except:
            return pd.Series([50] * len(df), index=df.index)
    
    def _calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calcola Williams %R"""
        try:
            high_max = df['high'].rolling(period, min_periods=1).max()
            low_min = df['low'].rolling(period, min_periods=1).min()
            return -100 * (high_max - df['close']) / (high_max - low_min)
        except:
            return pd.Series([-50] * len(df), index=df.index)
    
    def _calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calcola Commodity Channel Index"""
        try:
            tp = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = tp.rolling(period, min_periods=1).mean()
            mad = tp.rolling(period, min_periods=1).apply(lambda x: np.mean(np.abs(x - x.mean())))
            return (tp - sma_tp) / (0.015 * mad)
        except:
            return pd.Series([0] * len(df), index=df.index)

class EnsembleAIPredictor:
    """Predittore AI ensemble con modelli multipli"""
    
    def __init__(self):
        self.logger = logging.getLogger('EnsembleAI')
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_weights = {}
        self.is_trained = False
        
        # Inizializza modelli
        self._initialize_models()
    
    def _initialize_models(self):
        """Inizializza ensemble di modelli"""
        try:
            self.models = {
                'random_forest': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                ),
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                ),
                'neural_network': MLPRegressor(
                    hidden_layer_sizes=(100, 50),
                    max_iter=500,
                    random_state=42,
                    early_stopping=True
                ),
                'svr': SVR(
                    kernel='rbf',
                    C=1.0,
                    gamma='scale'
                ),
                'linear': Ridge(
                    alpha=1.0,
                    random_state=42
                )
            }
            
            # Inizializza scalers
            for model_name in self.models.keys():
                self.scalers[model_name] = RobustScaler()
            
            self.logger.info(f"✅ Ensemble inizializzato: {len(self.models)} modelli")
            
        except Exception as e:
            self.logger.error(f"❌ Errore inizializzazione modelli: {e}")
    
    def train_ensemble(self, features: pd.DataFrame, target: pd.Series) -> Dict:
        """Addestra ensemble di modelli"""
        try:
            self.logger.info(f"🎓 Addestramento ensemble su {len(features)} campioni...")
            
            # Prepara dati
            X = features.select_dtypes(include=[np.number]).fillna(0)
            y = target.fillna(target.mean())
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            results = {}
            
            # Addestra ogni modello
            for model_name, model in self.models.items():
                try:
                    self.logger.info(f"   🔄 Addestramento {model_name}...")
                    
                    # Scala features
                    X_train_scaled = self.scalers[model_name].fit_transform(X_train)
                    X_test_scaled = self.scalers[model_name].transform(X_test)
                    
                    # Addestra modello
                    model.fit(X_train_scaled, y_train)
                    
                    # Predizioni
                    y_pred_train = model.predict(X_train_scaled)
                    y_pred_test = model.predict(X_test_scaled)
                    
                    # Metriche
                    train_score = r2_score(y_train, y_pred_train)
                    test_score = r2_score(y_test, y_pred_test)
                    mse = mean_squared_error(y_test, y_pred_test)
                    mae = mean_absolute_error(y_test, y_pred_test)
                    
                    # Cross-validation
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
                    
                    results[model_name] = {
                        'train_r2': train_score,
                        'test_r2': test_score,
                        'mse': mse,
                        'mae': mae,
                        'cv_mean': cv_scores.mean(),
                        'cv_std': cv_scores.std()
                    }
                    
                    # Feature importance (se disponibile)
                    if hasattr(model, 'feature_importances_'):
                        self.feature_importance[model_name] = dict(
                            zip(X.columns, model.feature_importances_)
                        )
                    
                    self.logger.info(f"   ✅ {model_name}: R² = {test_score:.3f}, MAE = {mae:.4f}")
                    
                except Exception as e:
                    self.logger.error(f"   ❌ Errore {model_name}: {e}")
                    results[model_name] = {'error': str(e)}
            
            # Calcola pesi ensemble basati su performance
            self._calculate_ensemble_weights(results)
            
            self.is_trained = True
            self.logger.info("✅ Ensemble addestrato con successo")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Errore addestramento ensemble: {e}")
            return {}
    
    def _calculate_ensemble_weights(self, results: Dict):
        """Calcola pesi per ensemble basati su performance"""
        try:
            # Usa R² test come metrica per i pesi
            scores = {}
            for model_name, metrics in results.items():
                if 'test_r2' in metrics and metrics['test_r2'] > 0:
                    scores[model_name] = metrics['test_r2']
            
            if scores:
                # Normalizza pesi
                total_score = sum(scores.values())
                self.model_weights = {
                    name: score / total_score 
                    for name, score in scores.items()
                }
            else:
                # Pesi uniformi se nessun modello ha performance positive
                self.model_weights = {
                    name: 1.0 / len(self.models) 
                    for name in self.models.keys()
                }
            
            self.logger.info(f"📊 Pesi ensemble: {self.model_weights}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore calcolo pesi: {e}")
            self.model_weights = {name: 1.0 / len(self.models) for name in self.models.keys()}
    
    def predict_ensemble(self, features: pd.DataFrame) -> Dict:
        """Predizione ensemble"""
        try:
            if not self.is_trained:
                return {'error': 'Modelli non addestrati'}
            
            X = features.select_dtypes(include=[np.number]).fillna(0)
            
            predictions = {}
            valid_predictions = []
            valid_weights = []
            
            # Predizioni da ogni modello
            for model_name, model in self.models.items():
                try:
                    if model_name in self.model_weights:
                        X_scaled = self.scalers[model_name].transform(X)
                        pred = model.predict(X_scaled)
                        predictions[model_name] = pred[-1]  # Ultima predizione
                        
                        valid_predictions.append(pred[-1])
                        valid_weights.append(self.model_weights[model_name])
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Errore predizione {model_name}: {e}")
            
            if valid_predictions:
                # Predizione ensemble pesata
                ensemble_pred = np.average(valid_predictions, weights=valid_weights)
                
                # Confidence basata su accordo tra modelli
                pred_std = np.std(valid_predictions)
                confidence = max(0.1, 1.0 - (pred_std / abs(ensemble_pred)) if ensemble_pred != 0 else 0.5)
                confidence = min(confidence, 0.95)
                
                return {
                    'ensemble_prediction': ensemble_pred,
                    'individual_predictions': predictions,
                    'confidence': confidence,
                    'model_agreement': 1.0 - pred_std / (abs(ensemble_pred) + 1e-6),
                    'active_models': len(valid_predictions)
                }
            else:
                return {'error': 'Nessuna predizione valida'}
                
        except Exception as e:
            self.logger.error(f"❌ Errore predizione ensemble: {e}")
            return {'error': str(e)}
    
    def get_feature_importance(self) -> Dict:
        """Ottieni importanza feature aggregate"""
        try:
            if not self.feature_importance:
                return {}
            
            # Aggrega importanza da tutti i modelli
            all_features = set()
            for model_importance in self.feature_importance.values():
                all_features.update(model_importance.keys())
            
            aggregated_importance = {}
            for feature in all_features:
                importances = []
                weights = []
                
                for model_name, model_importance in self.feature_importance.items():
                    if feature in model_importance and model_name in self.model_weights:
                        importances.append(model_importance[feature])
                        weights.append(self.model_weights[model_name])
                
                if importances:
                    aggregated_importance[feature] = np.average(importances, weights=weights)
            
            # Ordina per importanza
            return dict(sorted(aggregated_importance.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            self.logger.error(f"❌ Errore feature importance: {e}")
            return {}

class AIOptimizationEngine:
    """Engine principale di ottimizzazione AI"""
    
    def __init__(self):
        self.logger = logging.getLogger('AIOptimizationEngine')
        self.feature_engineer = AdvancedFeatureEngineer()
        self.ai_predictor = EnsembleAIPredictor()
        self.optimization_history = []
        
        # Setup database
        self._setup_database()
    
    def _setup_database(self):
        """Setup database per ottimizzazione AI"""
        try:
            self.db_path = 'ai_optimization.db'
            conn = sqlite3.connect(self.db_path)
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_training_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    data_points INTEGER,
                    features_count INTEGER,
                    model_results TEXT,
                    best_model TEXT,
                    best_score REAL,
                    feature_importance TEXT,
                    training_time REAL,
                    status TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ensemble_prediction REAL,
                    confidence REAL,
                    model_agreement REAL,
                    active_models INTEGER,
                    individual_predictions TEXT,
                    actual_price REAL,
                    prediction_error REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("✅ Database AI optimization inizializzato")
            
        except Exception as e:
            self.logger.error(f"❌ Errore setup database AI: {e}")
    
    async def optimize_ai_models(self, market_data: pd.DataFrame) -> Dict:
        """Ottimizza modelli AI con nuovi dati"""
        try:
            start_time = datetime.now()
            self.logger.info(f"🚀 Avvio ottimizzazione AI con {len(market_data)} dati...")
            
            # 1. Feature engineering avanzato
            self.logger.info("🔧 Feature engineering...")
            enhanced_data = self.feature_engineer.create_advanced_features(market_data)
            
            # 2. Prepara target (prezzo futuro)
            target = enhanced_data['close'].shift(-1)  # Predici prezzo prossimo periodo
            target = target.fillna(target.mean())
            
            # 3. Rimuovi ultima riga (senza target)
            features = enhanced_data.iloc[:-1]
            target = target.iloc[:-1]
            
            # 4. Addestra ensemble
            self.logger.info("🎓 Addestramento ensemble AI...")
            training_results = self.ai_predictor.train_ensemble(features, target)
            
            # 5. Valuta performance
            best_model = self._find_best_model(training_results)
            best_score = training_results.get(best_model, {}).get('test_r2', 0.0)
            
            # 6. Feature importance
            feature_importance = self.ai_predictor.get_feature_importance()
            top_features = list(feature_importance.keys())[:20]
            
            # 7. Salva risultati
            training_time = (datetime.now() - start_time).total_seconds()
            
            optimization_result = {
                'timestamp': datetime.now().isoformat(),
                'data_points': len(features),
                'features_count': len(features.columns),
                'training_results': training_results,
                'best_model': best_model,
                'best_score': best_score,
                'top_features': top_features,
                'training_time': training_time,
                'status': 'completed'
            }
            
            # Salva nel database
            self._save_training_session(optimization_result)
            
            self.logger.info(f"✅ Ottimizzazione completata in {training_time:.2f}s")
            self.logger.info(f"🏆 Miglior modello: {best_model} (R² = {best_score:.3f})")
            self.logger.info(f"🔝 Top 5 feature: {top_features[:5]}")
            
            return optimization_result
            
        except Exception as e:
            self.logger.error(f"❌ Errore ottimizzazione AI: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _find_best_model(self, results: Dict) -> str:
        """Trova il miglior modello basato su metriche"""
        try:
            best_model = None
            best_score = -float('inf')
            
            for model_name, metrics in results.items():
                if 'test_r2' in metrics:
                    score = metrics['test_r2']
                    if score > best_score:
                        best_score = score
                        best_model = model_name
            
            return best_model or 'random_forest'
            
        except Exception as e:
            self.logger.error(f"❌ Errore ricerca miglior modello: {e}")
            return 'random_forest'
    
    def _save_training_session(self, result: Dict):
        """Salva sessione di training nel database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO ai_training_sessions (
                    data_points, features_count, model_results, best_model, 
                    best_score, feature_importance, training_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['data_points'],
                result['features_count'],
                json.dumps(result['training_results']),
                result['best_model'],
                result['best_score'],
                json.dumps(result['top_features']),
                result['training_time'],
                result['status']
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio training: {e}")
    
    async def generate_ai_prediction(self, current_data: pd.DataFrame) -> Dict:
        """Genera predizione AI ottimizzata"""
        try:
            self.logger.info("🔮 Generazione predizione AI...")
            
            # Feature engineering
            enhanced_data = self.feature_engineer.create_advanced_features(current_data)
            
            # Predizione ensemble
            prediction_result = self.ai_predictor.predict_ensemble(enhanced_data)
            
            if 'error' not in prediction_result:
                # Salva predizione
                self._save_prediction(prediction_result)
                
                self.logger.info(f"✅ Predizione AI: {prediction_result['ensemble_prediction']:.2f}")
                self.logger.info(f"🎯 Confidence: {prediction_result['confidence']:.1%}")
                self.logger.info(f"🤝 Model agreement: {prediction_result['model_agreement']:.1%}")
            
            return prediction_result
            
        except Exception as e:
            self.logger.error(f"❌ Errore predizione AI: {e}")
            return {'error': str(e)}
    
    def _save_prediction(self, prediction: Dict):
        """Salva predizione nel database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO ai_predictions (
                    ensemble_prediction, confidence, model_agreement, 
                    active_models, individual_predictions
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                prediction['ensemble_prediction'],
                prediction['confidence'],
                prediction['model_agreement'],
                prediction['active_models'],
                json.dumps(prediction['individual_predictions'])
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Errore salvataggio predizione: {e}")
    
    def get_optimization_stats(self) -> Dict:
        """Ottieni statistiche ottimizzazione"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Training sessions
            cursor = conn.execute('''
                SELECT COUNT(*) as total_sessions,
                       AVG(best_score) as avg_score,
                       MAX(best_score) as max_score,
                       AVG(training_time) as avg_training_time
                FROM ai_training_sessions 
                WHERE status = 'completed'
            ''')
            training_stats = cursor.fetchone()
            
            # Predictions
            cursor = conn.execute('''
                SELECT COUNT(*) as total_predictions,
                       AVG(confidence) as avg_confidence,
                       AVG(model_agreement) as avg_agreement
                FROM ai_predictions
            ''')
            prediction_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                'training_sessions': training_stats[0] if training_stats[0] else 0,
                'average_score': training_stats[1] if training_stats[1] else 0.0,
                'best_score': training_stats[2] if training_stats[2] else 0.0,
                'avg_training_time': training_stats[3] if training_stats[3] else 0.0,
                'total_predictions': prediction_stats[0] if prediction_stats[0] else 0,
                'avg_confidence': prediction_stats[1] if prediction_stats[1] else 0.0,
                'avg_model_agreement': prediction_stats[2] if prediction_stats[2] else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore stats ottimizzazione: {e}")
            return {}

async def main():
    """Test AI optimization engine"""
    print("🚀 AurumBotX AI Optimization Engine")
    print("=" * 60)
    print("🧠 ENSEMBLE AI: 5 modelli avanzati")
    print("🔧 FEATURE ENGINEERING: 100+ feature")
    print("📊 METRICHE: R², MAE, Cross-validation")
    print("🎯 PREDIZIONI: Ensemble pesato")
    print("=" * 60)
    
    # Setup
    os.makedirs('logs', exist_ok=True)
    
    # Inizializza engine
    ai_engine = AIOptimizationEngine()
    
    # Genera dati di test
    print("\n📊 Generazione dati di test...")
    dates = pd.date_range(start=datetime.now() - timedelta(days=100), periods=1000, freq='1H')
    
    # Simula dati realistici
    np.random.seed(42)
    base_price = 40000
    prices = [base_price]
    
    for i in range(1, 1000):
        change = np.random.normal(0, 0.02)  # 2% volatilità
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    test_data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        'close': prices,
        'volume': np.random.uniform(1000, 100000, 1000)
    })
    
    print(f"✅ Dati generati: {len(test_data)} candele")
    
    # Test ottimizzazione
    print("\n🚀 Test ottimizzazione AI...")
    optimization_result = await ai_engine.optimize_ai_models(test_data)
    
    if optimization_result['status'] == 'completed':
        print(f"✅ Ottimizzazione completata!")
        print(f"   🏆 Miglior modello: {optimization_result['best_model']}")
        print(f"   📊 Score: {optimization_result['best_score']:.3f}")
        print(f"   ⏱️ Tempo: {optimization_result['training_time']:.2f}s")
        print(f"   🔧 Feature: {optimization_result['features_count']}")
        
        # Test predizione
        print("\n🔮 Test predizione AI...")
        prediction = await ai_engine.generate_ai_prediction(test_data.tail(50))
        
        if 'error' not in prediction:
            print(f"✅ Predizione generata!")
            print(f"   💰 Prezzo predetto: ${prediction['ensemble_prediction']:.2f}")
            print(f"   🎯 Confidence: {prediction['confidence']:.1%}")
            print(f"   🤝 Agreement: {prediction['model_agreement']:.1%}")
            print(f"   🔢 Modelli attivi: {prediction['active_models']}")
        
        # Statistiche
        print("\n📊 Statistiche AI:")
        stats = ai_engine.get_optimization_stats()
        print(f"   🎓 Training sessions: {stats['training_sessions']}")
        print(f"   📈 Score medio: {stats['average_score']:.3f}")
        print(f"   🏆 Miglior score: {stats['best_score']:.3f}")
        print(f"   🔮 Predizioni: {stats['total_predictions']}")
        print(f"   🎯 Confidence media: {stats['avg_confidence']:.1%}")
    
    print(f"\n🎉 AI OPTIMIZATION ENGINE OPERATIVO!")

if __name__ == "__main__":
    asyncio.run(main())

