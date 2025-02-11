import logging
from typing import Dict, List, Optional, Union, Any
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import openai
from telethon import TelegramClient
import tweepy
import praw
import os
from utils.database import get_db

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        """Initialize sentiment analyzer with OpenAI assistant"""
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
        self.openai_client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        self.assistant_id = "asst_E21NUMje1wAB3TjAOBX9V6iY"
        self.initialize_social_clients()
        self._setup_assistant()

    def _setup_assistant(self):
        """Initialize OpenAI assistant for specialized trading analysis"""
        try:
            self.assistant = self.openai_client.beta.assistants.retrieve(
                assistant_id=self.assistant_id
            )
            logger.info("OpenAI assistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI assistant: {e}")
            self.assistant = None

    def initialize_social_clients(self):
        """Initialize social media clients with improved error handling"""
        try:
            # Reddit setup with better error handling
            try:
                self.reddit = praw.Reddit(
                    client_id=os.getenv("REDDIT_CLIENT_ID"),
                    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                    user_agent="AurumBot/1.0 Crypto Market Analyzer"
                )
                # Verify credentials
                self.reddit.user.me()
                logger.info("Reddit client initialized successfully")
            except Exception as reddit_e:
                logger.error(f"Reddit initialization failed: {reddit_e}")
                self.reddit = None

            # Twitter setup
            try:
                self.twitter = tweepy.Client(
                    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
                    wait_on_rate_limit=True
                )
                logger.info("Twitter client initialized successfully")
            except Exception as twitter_e:
                logger.error(f"Twitter initialization failed: {twitter_e}")
                self.twitter = None

            # Telegram setup - temporarily disabled
            self.telegram = None
            logger.info("Telegram integration temporarily disabled")

        except Exception as e:
            logger.error(f"Error initializing social clients: {e}")
            raise

    async def analyze_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze social media sentiment with comprehensive error handling"""
        try:
            reddit_data = await self.get_reddit_sentiment(symbol) if self.reddit else []
            twitter_data = await self.get_twitter_sentiment(symbol) if self.twitter else []
            telegram_data = []

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

            # Get both general sentiment and specialized trading analysis
            analysis = await self.analyze_with_ai(combined_data)
            trading_analysis = await self.analyze_with_assistant(combined_data, symbol)

            if analysis is None:
                return {
                    "error": "Failed to analyze sentiment",
                    "raw_data": combined_data,
                    "score": 0.0
                }

            # Combine both analyses
            combined_analysis = self._combine_analyses(analysis, trading_analysis)

            return {
                "raw_data": combined_data,
                "analysis": combined_analysis,
                "score": self.calculate_sentiment_score(combined_analysis)
            }

        except Exception as e:
            logger.error(f"Error in social sentiment analysis: {e}")
            return {
                "error": str(e),
                "raw_data": {},
                "score": 0.0
            }

    async def analyze_with_assistant(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Analyze data using the specialized trading assistant"""
        try:
            if not self.assistant:
                logger.warning("Assistant not initialized, skipping specialized analysis")
                return None

            # Create a thread for this analysis
            thread = self.openai_client.beta.threads.create()

            # Add market data message
            market_data_msg = f"""
            Analyzing {symbol} market sentiment:

            Social Media Activity:
            - Reddit posts: {len(data['reddit'])}
            - Twitter mentions: {len(data['twitter'])}

            Key Metrics:
            - Reddit engagement: {sum(post['score'] for post in data['reddit'])}
            - Twitter engagement: {sum(tweet['metrics'].get('like_count', 0) for tweet in data['twitter'])}

            Please analyze the trading implications and potential market signals.
            """

            self.openai_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=market_data_msg
            )

            # Run the assistant
            run = self.openai_client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )

            # Wait for completion
            while True:
                run_status = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    logger.error(f"Assistant analysis failed with status: {run_status.status}")
                    return None
                await asyncio.sleep(1)

            # Get the assistant's response
            messages = self.openai_client.beta.threads.messages.list(
                thread_id=thread.id
            )

            # Parse the last assistant message
            for message in messages.data:
                if message.role == "assistant":
                    return self._parse_assistant_response(message.content[0].text.value)

            return None

        except Exception as e:
            logger.error(f"Error in assistant analysis: {e}")
            return None

    def _parse_assistant_response(self, response: str) -> Dict[str, Any]:
        """Parse the assistant's response into structured data"""
        try:
            # Extract key trading signals and insights
            lines = response.split('\n')
            signals = []
            confidence = 0.5
            sentiment = "neutral"

            for line in lines:
                if "confidence:" in line.lower():
                    try:
                        confidence = float(line.split(':')[1].strip().rstrip('%')) / 100
                    except:
                        pass
                elif "sentiment:" in line.lower():
                    sentiment = line.split(':')[1].strip().lower()
                elif line.strip():
                    signals.append(line.strip())

            return {
                "trading_signals": signals,
                "trading_confidence": confidence,
                "market_sentiment": sentiment,
                "raw_analysis": response
            }

        except Exception as e:
            logger.error(f"Error parsing assistant response: {e}")
            return None

    def _combine_analyses(self, general_analysis: Dict[str, Any], trading_analysis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine general sentiment analysis with specialized trading analysis"""
        if not trading_analysis:
            return general_analysis

        combined = {
            "sentiment": general_analysis.get("sentiment", "neutral"),
            "confidence": general_analysis.get("confidence", 0.5),
            "key_points": general_analysis.get("key_points", []),
            "trading_signals": trading_analysis.get("trading_signals", []),
            "trading_confidence": trading_analysis.get("trading_confidence", 0.5),
            "market_sentiment": trading_analysis.get("market_sentiment", "neutral"),
            "raw_analysis": f"General Analysis:\n{general_analysis.get('raw_analysis', '')}\n\nTrading Analysis:\n{trading_analysis.get('raw_analysis', '')}"
        }

        # Adjust overall confidence based on both analyses
        combined["confidence"] = (combined["confidence"] + combined["trading_confidence"]) / 2

        return combined

    async def analyze_with_ai(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analizza i dati social con AI"""
        try:
            prompt = self._create_analysis_prompt(data)
            response = await self.openai_client.chat.completions.create(
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

            result = self._parse_ai_response(response.choices[0].message.content)
            if result is None:
                return {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "key_points": [],
                    "raw_analysis": "Analysis failed"
                }

            return result

        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "key_points": [],
                "raw_analysis": f"Error: {str(e)}"
            }

    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Crea il prompt per l'analisi AI"""
        return f"""
        Analyze the following social media data for crypto sentiment:

        Reddit Posts: {len(data['reddit'])} posts
        Twitter Mentions: {len(data['twitter'])} tweets

        Key metrics:
        - Reddit engagement: {sum(post['score'] for post in data['reddit'])}
        - Twitter engagement: {sum(tweet['metrics'].get('like_count', 0) for tweet in data['twitter'])}

        Please analyze the overall sentiment, identify key trends, and potential market signals.
        Provide your response with clear confidence levels and actionable insights.
        """

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parsa la risposta AI in un formato strutturato"""
        try:
            # Simple parsing logic based on content
            sentiment = "positive" if "positive" in response.lower() else "negative"
            confidence = 0.8  # Default confidence
            key_points = [point.strip() for point in response.split("\n") if point.strip()]

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "key_points": key_points,
                "raw_analysis": response
            }
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return None

    def calculate_sentiment_score(self, analysis: Dict[str, Any]) -> float:
        """Calcola uno score numerico del sentiment combinando analisi generale e trading"""
        try:
            if not analysis:
                return 0.0

            # Base score from general sentiment
            base_score = 1.0 if analysis.get("sentiment") == "positive" else -1.0

            # Adjust based on market sentiment if available
            if analysis.get("market_sentiment"):
                market_score = 1.0 if analysis.get("market_sentiment") == "positive" else -1.0
                base_score = (base_score + market_score) / 2

            # Use combined confidence
            confidence_modifier = analysis.get("confidence", 0.5)

            # Apply trading signals weight if available
            if analysis.get("trading_signals"):
                trading_confidence = analysis.get("trading_confidence", 0.5)
                confidence_modifier = (confidence_modifier + trading_confidence) / 2

            return base_score * confidence_modifier

        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.0

    async def get_reddit_sentiment(self, symbol: str) -> List[Dict[str, Any]]:
        """Ottiene post e commenti da Reddit con retry logic"""
        try:
            if not self.reddit:
                raise ValueError("Reddit client not initialized")

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
                            "created_utc": post.created_utc,
                            "subreddit": subreddit
                        })
                        logger.debug(f"Retrieved post from r/{subreddit}: {post.title[:50]}...")
                except Exception as sub_e:
                    logger.warning(f"Error fetching from subreddit {subreddit}: {sub_e}")
                    continue

            return posts

        except Exception as e:
            logger.error(f"Error getting Reddit sentiment: {e}")
            return []

    async def get_twitter_sentiment(self, symbol: str) -> List[Dict[str, Any]]:
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