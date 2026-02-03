#!/usr/bin/env python3  
"""  
Data Preprocessor Enterprise - Elimina completamente errori NaN  
"""  
import pandas as pd  
import numpy as np  
from sklearn.impute import SimpleImputer  
from sklearn.preprocessing import RobustScaler  
from sklearn.ensemble import IsolationForest  
  
class EnterpriseDataPreprocessor:  
    def __init__(self):  
        self.imputer = SimpleImputer(strategy='median')  
        self.scaler = RobustScaler()  
        self.outlier_detector = IsolationForest(contamination=0.1, random_state=42)  
          
    def clean_data(self, data):  
        """Pulizia completa dei dati con eliminazione NaN garantita"""  
        if data is None or (hasattr(data, 'empty') and data.empty):  
            return None  
              
        df = data.copy()  
          
        # 1. Rimuovi colonne con >50% NaN  
        threshold = len(df) * 0.5  
        df = df.dropna(thresh=threshold, axis=1)  
          
        # 2. Rimuovi righe con NaN  
        df = df.dropna()  
          
        # 3. Sostituisci infiniti con NaN e poi rimuovi  
        df = df.replace([np.inf, -np.inf], np.nan)  
        df = df.dropna()  
          
        # 4. Rimuovi outliers estremi  
        numeric_cols = df.select_dtypes(include=[np.number]).columns  
        if len(numeric_cols) > 0 and len(df) > 10:  
            try:  
                outlier_mask = self.outlier_detector.fit_predict(df[numeric_cols])  
                df = df[outlier_mask == 1]  
            except:  
                pass  
          
        # 5. Validazione finale  
        assert not df.isnull().any().any(), "NaN ancora presenti!"  
        assert not np.isinf(df.select_dtypes(include=[np.number]).values).any(), "Infiniti ancora presenti!"  
          
        return df
PIANO_LAVORO_FIX_TRADING.md:62-76

2. Trade Executor Robusto (Zero Trade Execution) 
Il sistema non esegue trade perché la logica non triggera PIANO_LAVORO_FIX_TRADING.md:22-28 . Crea utils/trade_executor_v2.py:

#!/usr/bin/env python3  
"""  
Trade Executor con retry logic e validazione completa  
"""  
import asyncio  
import logging  
from typing import Dict, Optional  
from datetime import datetime  
  
class RobustTradeExecutor:  
    def __init__(self, exchange_manager):  
        self.exchange = exchange_manager  
        self.logger = logging.getLogger('TradeExecutor')  
        self.max_retries = 3  
        self.retry_delay = 2  
          
    async def execute_trade(self, signal: Dict) -> Optional[Dict]:  
        """Esegue trade con retry automatico"""  
          
        # 1. Validazione segnale  
        if not self._validate_signal(signal):  
            self.logger.warning(f"Segnale non valido: {signal}")  
            return None  
          
        # 2. Verifica limiti di rischio  
        if not self._check_risk_limits(signal):  
            self.logger.warning("Limiti di rischio superati")  
            return None  
          
        # 3. Esecuzione con retry  
        for attempt in range(self.max_retries):  
            try:  
                order = await self._place_order(signal)  
                if order and order.get('status') == 'FILLED':  
                    self.logger.info(f"✅ Trade eseguito: {order['id']}")  
                    return order  
                      
            except Exception as e:  
                self.logger.error(f"Tentativo {attempt+1} fallito: {e}")  
                if attempt < self.max_retries - 1:  
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  
                      
        return None  
      
    def _validate_signal(self, signal: Dict) -> bool:  
        """Valida il segnale di trading"""  
        required_keys = ['action', 'symbol', 'confidence']  
          
        if not all(key in signal for key in required_keys):  
            return False  
              
        if signal['action'] not in ['buy', 'sell']:  
            return False  
              
        if not (0 <= signal['confidence'] <= 1):  
            return False  
              
        return True  
      
    def _check_risk_limits(self, signal: Dict) -> bool:  
        """Verifica limiti di rischio"""  
        # Implementa logica risk management  
        min_confidence = 0.65  
        return signal['confidence'] >= min_confidence  
      
    async def _place_order(self, signal: Dict) -> Optional[Dict]:  
        """Piazza ordine sull'exchange"""  
        try:  
            if signal['action'] == 'buy':  
                order = await self.exchange.create_market_buy_order(  
                    symbol=signal['symbol'],  
                    amount=signal.get('amount', 0.0001)  
                )  
            else:  
                order = await self.exchange.create_market_sell_order(  
                    symbol=signal['symbol'],  
                    amount=signal.get('amount', 0.0001)  
                )  
            return order  
        except Exception as e:  
            self.logger.error(f"Errore piazzamento ordine: {e}")  
            raise
