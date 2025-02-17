import logging
import asyncio
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        """Initialize sentiment analyzer with OpenAI assistant"""
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
        self.openai_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        self.initialize_social_clients()

    async def analyze_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Alias for analyze_social_sentiment to maintain interface compatibility"""
        return await self.analyze_social_sentiment(symbol)

    async def analyze_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze social media sentiment with comprehensive error handling"""
        try:
            # Ottieni dati social in modo asincrono
            reddit_data = await self.get_reddit_sentiment(symbol) if self.reddit else []
            twitter_data = await self.get_twitter_sentiment(symbol) if self.twitter else []
            telegram_data = []  # Temporaneamente disabilitato

            combined_data = {
                "reddit": reddit_data,
                "twitter": twitter_data,
                "telegram": telegram_data,
                "timestamp": datetime.now().isoformat()
            }

            if not any([reddit_data, twitter_data]):
                logger.warning("No social media data available for analysis")
                return {
                    "error": "Insufficient social media data",
                    "raw_data": combined_data,
                    "score": 0.0
                }

            try:
                # Analisi asincrona con GPT-4o
                analysis = await self.analyze_with_ai(combined_data)

                if analysis:
                    score = self.calculate_sentiment_score(analysis)
                    return {
                        "raw_data": combined_data,
                        "analysis": analysis,
                        "score": score
                    }
                else:
                    logger.warning("AI analysis failed, using fallback")
                    return {
                        "error": "AI analysis failed",
                        "raw_data": combined_data,
                        "score": 0.5  # Neutral fallback
                    }

            except Exception as e:
                logger.error(f"Error in AI analysis: {e}")
                return {
                    "error": str(e),
                    "raw_data": combined_data,
                    "score": 0.5  # Neutral fallback
                }

        except Exception as e:
            logger.error(f"Error in social sentiment analysis: {e}")
            return {
                "error": str(e),
                "raw_data": {},
                "score": 0.0
            }

    async def analyze_with_ai(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analizza i dati social con AI avanzata"""
        try:
            prompt = self._create_analysis_prompt(data)

            # Utilizzo asincrono di GPT-4o con formato JSON
            try:
                completion = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-4o",
                    messages=[{
                        "role": "system",
                        "content": """Sei un esperto analista di mercato crypto specializzato in:
                        1. Analisi del sentiment sui social media
                        2. Identificazione di pattern di mercato
                        3. Valutazione del momentum e della forza del trend

                        Analizza i dati forniti e produci insights dettagliati."""
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )

                if completion and completion.choices:
                    try:
                        result = json.loads(completion.choices[0].message.content)
                        # Valida la struttura della risposta
                        required_fields = ["sentiment", "confidence", "key_points", "market_signals"]
                        if all(field in result for field in required_fields):
                            return result
                    except json.JSONDecodeError:
                        logger.error("Failed to decode AI response as JSON")
                        return None

                return None

            except Exception as e:
                logger.error(f"Error in OpenAI API call: {e}")
                return None

        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return None

    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Crea il prompt avanzato per l'analisi AI"""
        return f"""
        Analizza i seguenti dati di mercato e social media:

        Metriche Social:
        - Reddit Posts: {len(data['reddit'])} posts
        - Twitter Mentions: {len(data['twitter'])} tweets
        - Engagement Reddit: {sum(post['score'] for post in data['reddit'])}
        - Engagement Twitter: {sum(tweet['metrics'].get('like_count', 0) for tweet in data['twitter'])}

        Fornisci un'analisi dettagliata includendo:
        1. Sentiment generale (positivo/negativo/neutro)
        2. Livello di confidenza (0-1)
        3. Punti chiave identificati
        4. Segnali di trading potenziali
        5. Metriche di momentum sociale
        6. Correlazione con il prezzo di mercato

        Rispondi in formato JSON con la seguente struttura:
        {{
            "sentiment": string,
            "confidence": float,
            "key_points": string[],
            "market_signals": string[],
            "momentum_score": float,
            "price_correlation": float
        }}
        """

    def calculate_sentiment_score(self, analysis: Dict[str, Any]) -> float:
        """Calcola uno score numerico del sentiment"""
        try:
            if not analysis:
                return 0.5

            # Score base dal sentiment
            sentiment_map = {
                "positive": 1.0,
                "neutral": 0.5,
                "negative": 0.0
            }
            base_score = sentiment_map.get(analysis.get("sentiment", "neutral"), 0.5)

            # Usa la confidenza dell'analisi
            confidence = analysis.get("confidence", 0.5)

            # Incorpora il momentum score se disponibile
            momentum_score = analysis.get("momentum_score", 0.5)

            # Calcola lo score finale
            final_score = (base_score * 0.4 +
                           confidence * 0.3 +
                           momentum_score * 0.3)

            return max(0.0, min(1.0, final_score))

        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.5

    async def get_reddit_sentiment(self, symbol: str) -> List[Dict[str, Any]]:
        """Ottiene post e commenti da Reddit in modo asincrono"""
        try:
            if not self.reddit:
                return []

            posts = []
            subreddits = ['cryptocurrency', 'CryptoMarkets', symbol.lower()]

            for subreddit in subreddits:
                try:
                    # Esegui le operazioni Reddit in modo asincrono
                    posts_data = await asyncio.to_thread(
                        self._fetch_reddit_data,
                        subreddit
                    )
                    posts.extend(posts_data)
                except Exception as sub_e:
                    logger.warning(f"Error fetching from subreddit {subreddit}: {sub_e}")
                    continue

            return posts

        except Exception as e:
            logger.error(f"Error getting Reddit sentiment: {e}")
            return []

    def _fetch_reddit_data(self, subreddit: str) -> List[Dict[str, Any]]:
        """Helper function for Reddit data fetching"""
        posts = []
        try:
            import praw
            for post in self.reddit.subreddit(subreddit).hot(limit=10):
                posts.append({
                    "title": post.title,
                    "text": post.selftext,
                    "score": post.score,
                    "comments": post.num_comments,
                    "created_utc": post.created_utc,
                    "subreddit": subreddit
                })
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
        return posts


    async def get_twitter_sentiment(self, symbol: str) -> List[Dict[str, Any]]:
        """Ottiene tweet rilevanti in modo asincrono"""
        try:
            if not self.twitter:
                return []

            query = f"#{symbol} OR {symbol} crypto -is:retweet"

            # Esegui la ricerca Twitter in modo asincrono
            tweets = await asyncio.to_thread(
                self.twitter.search_recent_tweets,
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

    def initialize_social_clients(self):
        """Initialize social media clients with improved error handling"""
        try:
            # Reddit setup with better error handling
            try:
                self.reddit = None  # Initialize as None first
                if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
                    import praw
                    self.reddit = praw.Reddit(
                        client_id=os.getenv("REDDIT_CLIENT_ID"),
                        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                        user_agent="AurumBot/1.0 Crypto Market Analyzer"
                    )
                    # Verify credentials
                    self.reddit.user.me()
                    logger.info("Reddit client initialized successfully")
                else:
                    logger.warning("Reddit credentials not found, Reddit integration disabled")
            except Exception as reddit_e:
                logger.error(f"Reddit initialization failed: {reddit_e}")
                self.reddit = None

            # Twitter setup
            try:
                self.twitter = None  # Initialize as None first
                if os.getenv("TWITTER_BEARER_TOKEN"):
                    import tweepy
                    self.twitter = tweepy.Client(
                        bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
                        wait_on_rate_limit=True
                    )
                    logger.info("Twitter client initialized successfully")
                else:
                    logger.warning("Twitter credentials not found, Twitter integration disabled")
            except Exception as twitter_e:
                logger.error(f"Twitter initialization failed: {twitter_e}")
                self.twitter = None

            # Telegram setup - temporarily disabled
            self.telegram = None
            logger.info("Telegram integration temporarily disabled")

        except Exception as e:
            logger.error(f"Error initializing social clients: {e}")
            raise