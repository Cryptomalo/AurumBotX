from typing import Dict, List, Optional, Union, Any
import logging
import asyncio
import concurrent.futures
from datetime import datetime
import json
import os
import numpy as np
import pandas as pd
from openai import OpenAI, RateLimitError, APIError
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        """Initialize sentiment analyzer with OpenAI and Anthropic assistants for fallback"""
        self.openai_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        self.anthropic_client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.initialize_social_clients()
        self.fallback_enabled = True

    def initialize_social_clients(self):
        """Initialize social media clients with improved error handling"""
        try:
            # Reddit setup with better error handling
            try:
                self.reddit = None
                if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
                    import praw
                    self.reddit = praw.Reddit(
                        client_id=os.getenv("REDDIT_CLIENT_ID"),
                        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                        user_agent="CryptoBot/1.0"
                    )
                    # Verify credentials silently
                    try:
                        self.reddit.user.me()
                        logger.info("Reddit client initialized successfully")
                    except Exception as auth_e:
                        logger.error(f"Reddit authentication failed: {auth_e}")
                        self.reddit = None
                else:
                    logger.warning("Reddit credentials not found")
            except Exception as reddit_e:
                logger.error(f"Reddit initialization failed: {reddit_e}")
                self.reddit = None

            # Twitter setup (temporarily disabled)
            self.twitter = None
            logger.warning("Twitter integration temporarily disabled")

            # Telegram setup (temporarily disabled) 
            self.telegram = None
            logger.info("Telegram integration temporarily disabled")

        except Exception as e:
            logger.error(f"Error initializing social clients: {e}")
            raise

    async def analyze_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze social media sentiment with comprehensive error handling and fallback"""
        try:
            social_data = {
                "reddit": await self._get_reddit_data(symbol) if self.reddit else [],
                "twitter": [],  # Twitter temporarily disabled
                "telegram": [],  # Telegram temporarily disabled
                "timestamp": datetime.now().isoformat()
            }

            if not any(len(data) > 0 for data in social_data.values() if isinstance(data, list)):
                logger.warning("No social media data available")
                return self._get_neutral_sentiment()

            # Try OpenAI first
            try:
                analysis = await self._analyze_with_openai(social_data)
                if analysis:
                    return self._create_sentiment_response(social_data, analysis)
            except (RateLimitError, APIError) as e:
                logger.warning(f"OpenAI analysis failed, trying Anthropic fallback: {e}")

            # Fallback to Anthropic if OpenAI fails
            if self.fallback_enabled:
                try:
                    analysis = await self._analyze_with_anthropic(social_data)
                    if analysis:
                        return self._create_sentiment_response(social_data, analysis)
                except Exception as e:
                    logger.error(f"Anthropic fallback failed: {e}")

            # Return neutral sentiment if both APIs fail
            logger.warning("All AI analysis attempts failed, using neutral sentiment")
            return self._get_neutral_sentiment()

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self._get_neutral_sentiment()

    def _get_neutral_sentiment(self) -> Dict[str, Any]:
        """Return neutral sentiment with low confidence"""
        return {
            "sentiment": "neutral",
            "score": 0.5,
            "confidence": 0.3,
            "error": "Analysis unavailable",
            "raw_data": {}
        }

    async def _analyze_with_openai(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze with OpenAI with improved error handling"""
        try:
            prompt = self._create_analysis_prompt(data)

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                completion = await loop.run_in_executor(
                    executor,
                    lambda: self.openai_client.chat.completions.create(
                        model="gpt-4o",  # Use the latest model
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert crypto market analyst."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.7
                    )
                )

            if completion and completion.choices:
                result = json.loads(completion.choices[0].message.content)
                if self._validate_ai_response(result):
                    return result

            logger.warning("Invalid OpenAI response format")
            return None

        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {e}")
            return None

    async def _analyze_with_anthropic(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze with Anthropic as fallback"""
        try:
            prompt = self._create_analysis_prompt(data)

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                completion = await loop.run_in_executor(
                    executor,
                    lambda: self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": f"{prompt}\nProvide analysis in JSON format only."
                        }]
                    )
                )

            if completion and completion.content:
                try:
                    result = json.loads(completion.content[0].text)
                    if self._validate_ai_response(result):
                        return result
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing Anthropic response: {e}")

            logger.warning("Invalid Anthropic response format")
            return None

        except Exception as e:
            logger.error(f"Error in Anthropic analysis: {e}")
            return None

    def _create_sentiment_response(self, social_data: Dict[str, Any], 
                                 analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized sentiment response"""
        score = self._calculate_sentiment_score(analysis)
        return {
            "raw_data": social_data,
            "analysis": analysis,
            "score": score,
            "confidence": analysis.get('confidence', 0.5),
            "timestamp": datetime.now().isoformat()
        }

    async def _get_reddit_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Get Reddit data with improved error handling and retry logic"""
        try:
            if not self.reddit:
                logger.info("Reddit client not initialized - skipping Reddit data collection")
                return []

            posts = []
            # Use more reliable subreddits and better symbol handling
            symbol_clean = symbol.split('/')[0] if '/' in symbol else symbol
            subreddits = ['CryptoCurrency', 'CryptoMarkets', symbol_clean.lower()]
            logger.info(f"Attempting to fetch Reddit data for symbol: {symbol_clean} from subreddits: {subreddits}")

            for subreddit in subreddits:
                try:
                    def fetch_subreddit_posts():
                        try:
                            # First try direct subreddit access
                            sub = self.reddit.subreddit(subreddit)
                            posts_query = list(sub.hot(limit=5))  # Get hot posts first
                            logger.debug(f"Retrieved {len(posts_query)} hot posts from r/{subreddit}")

                            # If no posts, try search
                            if not posts_query and subreddit in ['CryptoCurrency', 'CryptoMarkets']:
                                search_query = f"title:{symbol_clean} OR flair:{symbol_clean}"
                                logger.debug(f"Attempting search in r/{subreddit} with query: {search_query}")
                                posts_query = list(sub.search(search_query, limit=5, time_filter="week"))
                                logger.debug(f"Search retrieved {len(posts_query)} posts")

                            return posts_query
                        except Exception as e:
                            logger.debug(f"Reddit fetch error for {subreddit}: {e}")
                            return []

                    # Get posts with retry mechanism
                    for attempt in range(3):  # 3 retries
                        try:
                            logger.debug(f"Attempt {attempt + 1} to fetch from r/{subreddit}")
                            loop = asyncio.get_event_loop()
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                subreddit_posts = await loop.run_in_executor(None, fetch_subreddit_posts)

                            if subreddit_posts:  # If we got valid posts, process them
                                for post in subreddit_posts:
                                    if post and hasattr(post, 'title'):
                                        posts.append({
                                            "title": post.title[:500],  # Limit length
                                            "text": post.selftext[:1000] if hasattr(post, 'selftext') else "",
                                            "score": getattr(post, 'score', 0),
                                            "comments": getattr(post, 'num_comments', 0),
                                            "created_utc": getattr(post, 'created_utc', 0),
                                            "subreddit": subreddit,
                                            "url": getattr(post, 'url', '')
                                        })
                                        logger.debug(f"Retrieved post from r/{subreddit}: {post.title[:50]}...")
                                break  # Break retry loop if successful

                            if attempt < 2:  # Only sleep if we're going to retry
                                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff

                        except Exception as e:
                            logger.warning(f"Reddit fetch attempt {attempt + 1} failed: {e}")
                            if attempt == 2:  # Last attempt
                                raise
                            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff

                except Exception as sub_e:
                    logger.warning(f"Error fetching from subreddit {subreddit}: {sub_e}")
                    continue

            logger.info(f"Successfully retrieved {len(posts)} total posts from Reddit")
            return posts

        except Exception as e:
            logger.error(f"Error getting Reddit data: {e}")
            return []

    async def analyze_with_ai(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze social data with AI and improved error handling"""
        try:
            if not self.openai_client:
                logger.warning("OpenAI client not initialized")
                return self._get_fallback_analysis()

            prompt = self._create_analysis_prompt(data)

            try:
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    completion = await loop.run_in_executor(
                        executor,
                        lambda: self.openai_client.chat.completions.create(
                            model="gpt-3.5-turbo",  # Using available model
                            messages=[
                                {
                                    "role": "system",
                                    "content": """You are an expert crypto market analyst. 
                                    Analyze social media data and provide market insights."""
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.7
                        )
                    )

                if completion and completion.choices:
                    result = json.loads(completion.choices[0].message.content)
                    if self._validate_ai_response(result):
                        return result

                logger.warning("Invalid AI response format")
                return self._get_fallback_analysis()

            except RateLimitError as e:
                logger.warning(f"OpenAI rate limit exceeded: {e}")
                return self._get_fallback_analysis()
            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                return self._get_fallback_analysis()
            except Exception as e:
                logger.error(f"Error in AI analysis: {e}")
                return self._get_fallback_analysis()

        except Exception as e:
            logger.error(f"Error in analyze_with_ai: {e}")
            return self._get_fallback_analysis()

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Get fallback analysis when AI analysis fails"""
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "insights": ["Insufficient data for detailed analysis"],
            "market_signals": ["No clear market signals"],
            "momentum_score": 0.5
        }

    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create analysis prompt with metrics"""
        reddit_stats = {
            'posts': len(data['reddit']),
            'total_score': sum(post['score'] for post in data['reddit']),
            'total_comments': sum(post['comments'] for post in data['reddit'])
        }

        return f"""
        Analyze the following social media metrics:

        Reddit Activity:
        - Total Posts: {reddit_stats['posts']}
        - Total Score: {reddit_stats['total_score']}
        - Total Comments: {reddit_stats['total_comments']}

        Provide analysis including:
        1. Overall sentiment (positive/negative/neutral)
        2. Confidence score (0-1)
        3. Key insights
        4. Market signals

        Response format:
        {{
            "sentiment": "positive/negative/neutral",
            "confidence": float,
            "insights": string[],
            "market_signals": string[],
            "momentum_score": float
        }}
        """

    def _validate_ai_response(self, response: Dict[str, Any]) -> bool:
        """Validate AI response format"""
        required_fields = ['sentiment', 'confidence', 'insights', 'market_signals']
        return all(field in response for field in required_fields)

    def _calculate_sentiment_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate numerical sentiment score"""
        try:
            # Base sentiment score
            sentiment_map = {
                'positive': 0.75,
                'neutral': 0.5,
                'negative': 0.25
            }
            base_score = sentiment_map.get(analysis.get('sentiment', 'neutral'), 0.5)

            # Adjust by confidence
            confidence = min(max(analysis.get('confidence', 0.5), 0.0), 1.0)

            # Calculate final score with neutral bias
            final_score = (base_score * confidence + 0.5 * (1 - confidence))

            return max(0.0, min(1.0, final_score))

        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.5  # Neutral fallback