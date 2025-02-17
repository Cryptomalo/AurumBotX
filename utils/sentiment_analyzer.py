import logging
import asyncio
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json
import os
from openai import OpenAI, RateLimitError, APIError

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        """Initialize sentiment analyzer with OpenAI assistant"""
        self.openai_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        self.initialize_social_clients()

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
        """Analyze social media sentiment with comprehensive error handling"""
        try:
            # Get social data asynchronously
            social_data = {
                "reddit": await self._get_reddit_data(symbol) if self.reddit else [],
                "twitter": [],  # Twitter temporarily disabled
                "telegram": [],  # Telegram temporarily disabled
                "timestamp": datetime.now().isoformat()
            }

            if not any(social_data.values()):
                logger.warning("No social media data available")
                return {
                    "error": "Insufficient data",
                    "raw_data": social_data,
                    "score": 0.5,  # Neutral fallback
                    "confidence": 0.0
                }

            try:
                # Analyze with GPT-4 if available
                analysis = await self._analyze_with_ai(social_data) if self.openai_client else None

                if analysis:
                    score = self._calculate_sentiment_score(analysis)
                    return {
                        "raw_data": social_data,
                        "analysis": analysis,
                        "score": score,
                        "confidence": analysis.get('confidence', 0.5)
                    }
                else:
                    logger.warning("AI analysis failed, using fallback scoring")
                    return {
                        "raw_data": social_data,
                        "score": 0.5,
                        "confidence": 0.3,
                        "error": "AI analysis unavailable"
                    }

            except Exception as e:
                logger.error(f"Error in AI analysis: {e}")
                return {
                    "error": str(e),
                    "raw_data": social_data,
                    "score": 0.5,
                    "confidence": 0.2
                }

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {
                "error": str(e),
                "raw_data": {},
                "score": 0.5,
                "confidence": 0.0
            }

    async def _get_reddit_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Get Reddit data with improved error handling"""
        try:
            if not self.reddit:
                return []

            posts = []
            subreddits = ['CryptoCurrency', 'CryptoMarkets', symbol.lower()]

            for subreddit in subreddits:
                try:
                    async def fetch_subreddit_posts():
                        try:
                            # Use a more specific subreddit search format
                            sub = self.reddit.subreddit(subreddit)
                            posts_query = sub.search(f"{symbol} OR {symbol.upper()}", limit=5, time_filter="day")
                            return list(posts_query)
                        except Exception as e:
                            if "received 400 HTTP response" in str(e):
                                # Try alternative search method
                                return list(sub.hot(limit=5))
                            raise

                    # Get posts with retry mechanism
                    for attempt in range(3):  # 3 retries
                        try:
                            subreddit_posts = await asyncio.to_thread(fetch_subreddit_posts)
                            for post in subreddit_posts:
                                if post and hasattr(post, 'title'):  # Verify post object is valid
                                    posts.append({
                                        "title": post.title,
                                        "text": post.selftext[:500],  # Limit text length
                                        "score": getattr(post, 'score', 0),
                                        "comments": getattr(post, 'num_comments', 0),
                                        "created_utc": getattr(post, 'created_utc', 0),
                                        "subreddit": subreddit
                                    })
                            if posts:  # If we got valid posts, break retry loop
                                break
                            await asyncio.sleep(1)  # Brief pause between attempts
                        except Exception as e:
                            logger.warning(f"Reddit fetch attempt {attempt + 1} failed: {e}")
                            if attempt == 2:  # Last attempt
                                raise
                            await asyncio.sleep(1 * (attempt + 1))  # Increasing backoff

                except Exception as sub_e:
                    logger.warning(f"Error fetching from subreddit {subreddit}: {sub_e}")
                    continue

            return posts

        except Exception as e:
            logger.error(f"Error getting Reddit data: {e}")
            return []

    async def _analyze_with_ai(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze social data with AI"""
        try:
            if not self.openai_client:
                return None

            prompt = self._create_analysis_prompt(data)

            try:
                completion = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-4",
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
                    response_format={"type": "json_object"}
                )

                if completion and completion.choices:
                    result = json.loads(completion.choices[0].message.content)
                    if self._validate_ai_response(result):
                        return result

            except (RateLimitError, APIError) as e:
                logger.warning(f"OpenAI API error: {e}")
                return None
            except Exception as e:
                logger.error(f"Error in OpenAI analysis: {e}")
                return None

            return None

        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return None

    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create analysis prompt with metrics"""
        reddit_stats = {
            'posts': len(data['reddit']),
            'total_score': sum(post['score'] for post in data['reddit']),
            'total_comments': sum(post['comments'] for post in data['reddit'])
        }

        return f"""
        Analyze the following social media data metrics:

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
            confidence = analysis.get('confidence', 0.5)

            # Calculate final score
            final_score = (base_score * confidence + 0.5 * (1 - confidence))

            return max(0.0, min(1.0, final_score))

        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.5  # Neutral fallback