import pandas as pd
from typing import Dict, Any
import numpy as np
from utils.strategies.base_strategy import BaseStrategy
from openai import OpenAI
import os

class MemeCoinSnipingStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Meme Coin Sniping", config)
        self.min_liquidity = config.get('min_liquidity', 100000)  # Liquidità minima in USD
        self.sentiment_threshold = config.get('sentiment_threshold', 0.7)
        self.profit_target = config.get('profit_target', 0.1)  # 10% target di profitto
        self.max_loss = config.get('max_loss', 0.05)  # 5% stop loss
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def analyze_market(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analizza il mercato per la strategia meme coin
        """
        analysis = {
            'volume_24h': df['Volume'].iloc[-1],
            'price_change_24h': (df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1),
            'volatility': df['Close'].rolling(window=24).std().iloc[-1],
            'liquidity_sufficient': df['Volume'].iloc[-1] > self.min_liquidity,
            'sentiment_score': self._analyze_sentiment(),
            'current_price': df['Close'].iloc[-1]
        }
        
        return analysis

    def _analyze_sentiment(self) -> float:
        """
        Analizza il sentiment utilizzando OpenAI
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # Latest stable model
                messages=[{
                    "role": "system",
                    "content": "Analyze the current market sentiment for meme coins and provide a sentiment score between 0 and 1."
                }],
                response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            return float(result.get('sentiment_score', 0.5))
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return 0.5  # Neutral sentiment in case of error

    def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera segnali di trading basati sull'analisi
        """
        # Calcola il punteggio complessivo
        score = 0
        
        # Controlla la liquidità
        if analysis['liquidity_sufficient']:
            score += 0.3
            
        # Valuta il sentiment
        if analysis['sentiment_score'] > self.sentiment_threshold:
            score += 0.4
            
        # Considera la volatilità
        if analysis['volatility'] > 0:
            vol_score = min(0.3, analysis['volatility'])
            score += vol_score
            
        # Genera il segnale
        signal = {
            'action': 'buy' if score > 0.6 else 'hold',
            'confidence': score,
            'target_price': analysis['current_price'] * (1 + self.profit_target),
            'stop_loss': analysis['current_price'] * (1 - self.max_loss),
            'size_factor': min(1.0, score)  # Dimensione posizione basata sul punteggio
        }
        
        return signal

    def validate_trade(self, signal: Dict[str, Any], current_portfolio: Dict[str, Any]) -> bool:
        """
        Valida un potenziale trade
        """
        if signal['action'] != 'buy':
            return False
            
        # Verifica se abbiamo abbastanza capitale
        required_capital = current_portfolio.get('available_capital', 0) * signal['size_factor']
        min_required = 100  # Capitale minimo per trade
        
        if required_capital < min_required:
            return False
            
        # Verifica se il rischio è accettabile
        risk_amount = (signal['target_price'] - signal['stop_loss']) * required_capital
        max_risk_per_trade = current_portfolio.get('total_capital', 0) * 0.02  # 2% max rischio
        
        return risk_amount <= max_risk_per_trade
