import logging
import praw
import tweepy
from telethon import TelegramClient
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List
import openai
from utils.database import get_db

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.openai_client = openai.OpenAI()
        self.initialize_social_clients()
        
    def initialize_social_clients(self):
        """Inizializza i client per i social media"""
        try:
            # Reddit setup
            self.reddit = praw.Reddit(
                client_id="YOUR_CLIENT_ID",
                client_secret="YOUR_CLIENT_SECRET",
                user_agent="AurumBot Crypto Analyzer"
            )
            
            # Twitter setup
            self.twitter = tweepy.Client(
                bearer_token="YOUR_BEARER_TOKEN",
                wait_on_rate_limit=True
            )
            
            # Telegram setup (using environment variables)
            self.telegram = TelegramClient(
                'aurum_bot',
                api_id="YOUR_API_ID",
                api_hash="YOUR_API_HASH"
            )
            
        except Exception as e:
            logger.error(f"Error initializing social clients: {e}")
            
    async def analyze_social_sentiment(self, symbol: str) -> Dict:
        """Analizza il sentiment dai social media"""
        try:
            reddit_data = self.get_reddit_sentiment(symbol)
            twitter_data = self.get_twitter_sentiment(symbol)
            telegram_data = await self.get_telegram_sentiment(symbol)
            
            combined_data = {
                "reddit": reddit_data,
                "twitter": twitter_data,
                "telegram": telegram_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Analisi AI del sentiment combinato
            analysis = self.analyze_with_ai(combined_data)
            
            return {
                "raw_data": combined_data,
                "analysis": analysis,
                "score": self.calculate_sentiment_score(analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in social sentiment analysis: {e}")
            return None
            
    def get_reddit_sentiment(self, symbol: str) -> List[Dict]:
        """Ottiene post e commenti da Reddit"""
        try:
            subreddits = ['cryptocurrency', 'CryptoMarkets', symbol.lower()]
            posts = []
            
            for subreddit in subreddits:
                try:
                    for post in self.reddit.subreddit(subreddit).hot(limit=10):
                        posts.append({
                            "title": post.title,
                            "text": post.selftext,
                            "score": post.score,
                            "comments": post.num_comments,
                            "created_utc": post.created_utc
                        })
                except Exception as sub_e:
                    logger.warning(f"Error fetching from subreddit {subreddit}: {sub_e}")
                    
            return posts
        except Exception as e:
            logger.error(f"Error getting Reddit sentiment: {e}")
            return []
            
    def get_twitter_sentiment(self, symbol: str) -> List[Dict]:
        """Ottiene tweet rilevanti"""
        try:
            query = f"#{symbol} OR {symbol} crypto -is:retweet"
            tweets = self.twitter.search_recent_tweets(
                query=query,
                max_results=100,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            return [{
                "text": tweet.text,
                "metrics": tweet.public_metrics,
                "created_at": tweet.created_at
            } for tweet in tweets.data] if tweets.data else []
            
        except Exception as e:
            logger.error(f"Error getting Twitter sentiment: {e}")
            return []
            
    async def get_telegram_sentiment(self, symbol: str) -> List[Dict]:
        """Ottiene messaggi da canali Telegram"""
        try:
            channels = ['cryptosignals', 'binancenews']  # Add relevant channels
            messages = []
            
            async with self.telegram:
                for channel in channels:
                    try:
                        async for message in self.telegram.iter_messages(channel, limit=50):
                            if symbol.lower() in message.text.lower():
                                messages.append({
                                    "text": message.text,
                                    "date": message.date.isoformat(),
                                    "views": message.views
                                })
                    except Exception as chan_e:
                        logger.warning(f"Error fetching from channel {channel}: {chan_e}")
                        
            return messages
            
        except Exception as e:
            logger.error(f"Error getting Telegram sentiment: {e}")
            return []
            
    def analyze_with_ai(self, data: Dict) -> Dict:
        """Analizza i dati social con AI"""
        try:
            prompt = self._create_analysis_prompt(data)
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "system",
                    "content": "You are a crypto market sentiment analyzer. Analyze the social media data and provide insights."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7
            )
            
            return self._parse_ai_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return None
            
    def _create_analysis_prompt(self, data: Dict) -> str:
        """Crea il prompt per l'analisi AI"""
        return f"""
        Analyze the following social media data for crypto sentiment:
        
        Reddit Posts: {len(data['reddit'])} posts
        Twitter Mentions: {len(data['twitter'])} tweets
        Telegram Messages: {len(data['telegram'])} messages
        
        Key metrics:
        - Reddit engagement: {sum(post['score'] for post in data['reddit'])}
        - Twitter engagement: {sum(tweet['metrics']['like_count'] for tweet in data['twitter'])}
        - Telegram views: {sum(msg['views'] for msg in data['telegram'])}
        
        Please analyze the overall sentiment, identify key trends, and potential market signals.
        """
        
    def _parse_ai_response(self, response: str) -> Dict:
        """Parsa la risposta AI in un formato strutturato"""
        try:
            # Implement parsing logic based on your needs
            return {
                "sentiment": "positive" if "positive" in response.lower() else "negative",
                "confidence": 0.8,  # Implement proper confidence calculation
                "key_points": response.split("\n"),
                "raw_analysis": response
            }
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return None
            
    def calculate_sentiment_score(self, analysis: Dict) -> float:
        """Calcola uno score numerico del sentiment"""
        try:
            if not analysis:
                return 0.0
                
            # Implementa la logica di scoring basata sull'analisi
            base_score = 1.0 if analysis["sentiment"] == "positive" else -1.0
            confidence_modifier = analysis["confidence"]
            
            return base_score * confidence_modifier
            
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.0
