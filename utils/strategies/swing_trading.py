import pandas as pd
from typing import Dict, Any
import numpy as np
from utils.strategies.base_strategy import BaseStrategy
from openai import OpenAI
import os

class SwingTradingStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Swing Trading", config)
        self.trend_period = config.get('trend_period', 20)  # Periodo per analisi trend
        self.profit_target = config.get('profit_target', 0.15)  # 15% target di profitto
        self.stop_loss = config.get('stop_loss', 0.10)  # 10% stop loss
        self.min_trend_strength = config.get('min_trend_strength', 0.6)
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def analyze_market(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analizza il mercato per swing trading
        """
        # Calcola indicatori tecnici
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Calcola trend
        trend_direction = 1 if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1] else -1
        trend_strength = abs(df['SMA_20'].iloc[-1] - df['SMA_50'].iloc[-1]) / df['SMA_50'].iloc[-1]
        
        # Calcola volatilità
        volatility = df['Close'].pct_change().rolling(window=self.trend_period).std().iloc[-1]
        
        # Analisi del volume
        volume_trend = df['Volume'].rolling(window=self.trend_period).mean().iloc[-1]
        volume_ratio = df['Volume'].iloc[-1] / volume_trend
        
        # Analisi del sentiment
        sentiment_score = self._analyze_market_sentiment()
        
        analysis = {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'volatility': volatility,
            'volume_ratio': volume_ratio,
            'sentiment_score': sentiment_score,
            'current_price': df['Close'].iloc[-1],
            'sma_20': df['SMA_20'].iloc[-1],
            'sma_50': df['SMA_50'].iloc[-1]
        }
        
        return analysis

    def _analyze_market_sentiment(self) -> float:
        """
        Analizza il sentiment del mercato per lungo termine
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # Latest stable model
                messages=[{
                    "role": "system",
                    "content": "Analyze the current market sentiment for long-term crypto trading and provide a sentiment score between 0 and 1."
                }],
                response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            return float(result.get('sentiment_score', 0.5))
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return 0.5

    def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera segnali per swing trading
        """
        signal = {
            'action': 'hold',
            'confidence': 0.0,
            'target_price': None,
            'stop_loss': None,
            'size_factor': 0.0
        }
        
        # Verifica la forza del trend
        if analysis['trend_strength'] < self.min_trend_strength:
            return signal
            
        # Calcola score complessivo
        trend_score = min(1.0, analysis['trend_strength'])
        sentiment_score = analysis['sentiment_score']
        volume_score = min(1.0, analysis['volume_ratio'])
        
        total_score = (
            trend_score * 0.4 +
            sentiment_score * 0.3 +
            volume_score * 0.3
        )
        
        # Genera segnale se lo score è sufficiente
        if total_score > 0.7:
            current_price = analysis['current_price']
            
            if analysis['trend_direction'] > 0 and analysis['sentiment_score'] > 0.6:
                signal.update({
                    'action': 'buy',
                    'confidence': total_score,
                    'target_price': current_price * (1 + self.profit_target),
                    'stop_loss': current_price * (1 - self.stop_loss),
                    'size_factor': total_score
                })
            elif analysis['trend_direction'] < 0 and analysis['sentiment_score'] < 0.4:
                signal.update({
                    'action': 'sell',
                    'confidence': total_score,
                    'target_price': current_price * (1 - self.profit_target),
                    'stop_loss': current_price * (1 + self.stop_loss),
                    'size_factor': total_score
                })
                
        return signal

    def validate_trade(self, signal: Dict[str, Any], current_portfolio: Dict[str, Any]) -> bool:
        """
        Valida un potenziale trade di swing
        """
        if signal['action'] == 'hold':
            return False
            
        # Verifica capitale disponibile
        required_capital = current_portfolio.get('available_capital', 0) * signal['size_factor']
        min_trade_size = 500  # Dimensione minima per swing trading
        
        if required_capital < min_trade_size:
            return False
            
        # Verifica rischio
        risk_amount = abs(signal['target_price'] - signal['stop_loss']) * required_capital
        max_risk = current_portfolio.get('total_capital', 0) * 0.05  # 5% rischio massimo per trade
        
        # Verifica timing di mercato
        market_conditions_favorable = (
            signal['confidence'] > 0.8 and
            current_portfolio.get('market_trend', 0) * (
                1 if signal['action'] == 'buy' else -1
            ) > 0
        )
        
        return risk_amount <= max_risk and market_conditions_favorable
