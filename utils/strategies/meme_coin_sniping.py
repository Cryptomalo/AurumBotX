import pandas as pd
from typing import Dict, Any
import numpy as np
from utils.strategies.base_strategy import BaseStrategy
from openai import OpenAI
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.keypair import Keypair
from pyserum.market import Market
from pyserum.connection import conn
import os
import asyncio
import time

class MemeCoinSnipingStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Meme Coin Sniping", config)
        self.min_liquidity = config.get('min_liquidity', 100000)
        self.sentiment_threshold = config.get('sentiment_threshold', 0.7)
        self.profit_target = config.get('profit_target', 0.15)  # Increased to 15%
        self.max_loss = config.get('max_loss', 0.05)
        self.volume_threshold = config.get('volume_threshold', 50000)
        self.momentum_period = config.get('momentum_period', 12)

        # Solana setup
        self.solana_client = Client("https://api.mainnet-beta.solana.com")
        self.keypair = Keypair.from_secret_key(bytes(os.getenv('SOLANA_PRIVATE_KEY')))

        # Initialize OpenAI
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Trading parameters
        self.max_slippage = 0.02  # 2% max slippage
        self.min_volume_24h = 100000  # Minimum 24h volume in USD

    def _analyze_liquidity(self, market_data: Dict) -> float:
        """Analyze market liquidity"""
        return min(1.0, market_data['volume_24h'] / self.min_liquidity)

    def _analyze_momentum(self, df: pd.DataFrame) -> float:
        """Calculate price momentum"""
        returns = df['Close'].pct_change(self.momentum_period)
        return np.tanh(returns.mean() * 100)  # Normalize between -1 and 1

    def _get_market_data(self, token_address: str) -> Dict:
        """Get market data from Solana DEX"""
        try:
            market = Market.load(self.solana_client, token_address)
            orderbook = market.load_orderbook()

            return {
                'price': market.get_mid_price(),
                'volume_24h': market.get_volume_quote_token(24),
                'bid_depth': sum(order.quantity for order in orderbook.bids),
                'ask_depth': sum(order.quantity for order in orderbook.asks)
            }
        except Exception as e:
            print(f"Error getting market data: {e}")
            return None

    async def _execute_trade(self, market_address: str, size: float, is_buy: bool) -> bool:
        """Execute trade on Solana"""
        try:
            market = Market.load(self.solana_client, market_address)
            order_type = 'buy' if is_buy else 'sell'
            price = market.get_mid_price() * (1 + self.max_slippage if is_buy else 1 - self.max_slippage)

            transaction = Transaction()
            transaction.add(
                market.place_order(
                    payer=self.keypair.public_key,
                    owner=self.keypair,
                    side=order_type,
                    order_type='limit',
                    limit_price=price,
                    max_quantity=size
                )
            )

            result = await self.solana_client.send_transaction(
                transaction,
                self.keypair
            )
            return 'result' in result

        except Exception as e:
            print(f"Trade execution error: {e}")
            return False

    def _scan_reddit_trending(self) -> Dict:
        """Scan Reddit for trending tokens"""
        subreddits = ['CryptoMoonShots', 'CryptoCurrency', 'SatoshiStreetBets']
        # Implementa scanning Reddit
        return {'trending_score': 0.8, 'mention_count': 150}

    def _scan_telegram_groups(self) -> Dict:
        """Monitor Telegram groups for early signals"""
        # Implementa monitoring Telegram
        return {'signal_strength': 0.7, 'group_momentum': 0.85}

    def _analyze_twitter_sentiment(self) -> Dict:
        """Analyze Twitter/X sentiment"""
        # Implementa analisi Twitter
        return {'sentiment': 0.75, 'viral_potential': 0.9}

    def _scan_web_mentions(self) -> Dict:
        """Scan web for token mentions"""
        # Implementa web scanning
        return {'mention_frequency': 0.65, 'growth_rate': 0.8}

    def _analyze_social_signals(self) -> Dict[str, float]:
        """Advanced social signal analysis"""
        try:
            # Analisi Reddit
            reddit_data = self._scan_reddit_trending()

            # Analisi Telegram
            telegram_mentions = self._scan_telegram_groups()

            # Analisi Twitter/X
            twitter_sentiment = self._analyze_twitter_sentiment()

            # Analisi web generale
            web_mentions = self._scan_web_mentions()

            # Analizza con GPT-4 per sentiment complessivo
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{
                    "role": "system",
                    "content": f"""Analyze comprehensive market data:
                    Reddit Trends: {reddit_data}
                    Telegram Mentions: {telegram_mentions}
                    Twitter Sentiment: {twitter_sentiment}
                    Web Mentions: {web_mentions}

                    Provide detailed sentiment analysis with:
                    1. Overall sentiment score (0-1)
                    2. Trend strength (0-1)
                    3. Growth potential (0-1)
                    4. Risk factor (0-1)"""
                }],
                response_format={"type": "json_object"}
            )

            result = response.choices[0].message.content
            return {
                'sentiment': float(result.get('sentiment', 0.5)),
                'trend_strength': float(result.get('trend_strength', 0.5)),
                'growth_potential': float(result.get('growth_potential', 0.5)),
                'risk_factor': float(result.get('risk_factor', 0.5))
            }

        except Exception as e:
            print(f"Social analysis error: {e}")
            return {
                'sentiment': 0.5,
                'trend_strength': 0.5,
                'growth_potential': 0.5,
                'risk_factor': 0.5
            }

    def analyze_market(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced market analysis"""
        market_data = self._get_market_data(df['token_address'].iloc[-1])
        if not market_data:
            return {'action': 'hold', 'confidence': 0}

        analysis = {
            'volume_24h': market_data['volume_24h'],
            'price_change_24h': (df['Close'].iloc[-1] / df['Close'].iloc[-24] - 1),
            'volatility': df['Close'].rolling(window=24).std().iloc[-1],
            'liquidity_score': self._analyze_liquidity(market_data),
            'momentum_score': self._analyze_momentum(df),
            'current_price': market_data['price']
        }

        return analysis

    def generate_signals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered signal generation"""
        social_signals = self._analyze_social_signals()

        # Calcolo score avanzato con pesi dinamici
        score = (
            0.25 * analysis['liquidity_score'] +
            0.20 * social_signals['sentiment'] +
            0.15 * social_signals['trend_strength'] +
            0.15 * social_signals['growth_potential'] +
            0.15 * analysis['momentum_score'] +
            0.10 * (1 if analysis['volume_24h'] > self.volume_threshold else 0)
        )

        # Risk adjustment
        risk_adjusted_score = score * (1 - social_signals['risk_factor'])

        # Risk adjustment based on market conditions
        risk_factor = min(1.0, analysis['volume_24h'] / (self.volume_threshold * 2))
        adjusted_size = risk_factor * 0.8  # Max 80% of available position size

        signal = {
            'action': 'buy' if score > 0.7 else 'hold',
            'confidence': score,
            'target_price': analysis['current_price'] * (1 + self.profit_target),
            'stop_loss': analysis['current_price'] * (1 - self.max_loss),
            'size_factor': adjusted_size
        }

        return signal

    def validate_trade(self, signal: Dict[str, Any], current_portfolio: Dict[str, Any]) -> bool:
        """Enhanced trade validation"""
        if signal['action'] != 'buy':
            return False

        required_capital = current_portfolio.get('available_capital', 0) * signal['size_factor']
        min_required = 100  # Minimum capital required

        if required_capital < min_required:
            return False

        risk_amount = (signal['target_price'] - signal['stop_loss']) * required_capital
        max_risk_per_trade = current_portfolio.get('total_capital', 0) * 0.02

        return (
            risk_amount <= max_risk_per_trade and
            signal['confidence'] > 0.7 and
            current_portfolio.get('market_trend', 0) > 0
        )