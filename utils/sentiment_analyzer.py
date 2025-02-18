import logging
from typing import Dict, List, Optional, Union, Any
import asyncio
import concurrent.futures
from datetime import datetime
import json
import os
import time
from openai import OpenAI, RateLimitError, APIError
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        """Initialize sentiment analyzer with improved error handling and rate limiting"""
        self.initialize_ai_clients()
        self.last_api_call = 0
        self.min_delay_between_calls = 1.0  # Minimum seconds between API calls
        self.max_retries = 3
        self.retry_delay = 2.0
        self.initialize_social_clients()
        self.fallback_enabled = True

    def initialize_ai_clients(self):
        """Initialize AI clients with proper error handling"""
        try:
            openai_key = os.environ.get("OPENAI_API_KEY")
            if not openai_key:
                logger.warning("OpenAI API key not found")
                self.openai_client = None
            else:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"OpenAI initialization failed: {e}")
            self.openai_client = None

        try:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
            if not anthropic_key:
                logger.warning("Anthropic API key not found")
                self.anthropic_client = None
            else:
                self.anthropic_client = Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized successfully")
        except Exception as e:
            logger.error(f"Anthropic initialization failed: {e}")
            self.anthropic_client = None

        if not self.openai_client and not self.anthropic_client:
            logger.warning("No AI clients available - will use technical analysis only")

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
        """Analyze sentiment with fallback mechanisms and rate limiting"""
        try:
            social_data = {
                "reddit": await self._get_reddit_data(symbol) if self.reddit else [],
                "twitter": [],  # Twitter temporarily disabled
                "telegram": [],  # Telegram temporarily disabled
                "timestamp": datetime.now().isoformat()
            }
            data = {"items": social_data}

            # Respect rate limits
            await self._wait_for_rate_limit()

            # Try OpenAI first
            if self.openai_client:
                try:
                    analysis = await self._analyze_with_openai(data)
                    if analysis:
                        return self._create_sentiment_response(data, analysis)
                except (RateLimitError, APIError) as e:
                    logger.warning(f"OpenAI analysis failed, trying Anthropic fallback: {e}")
                except Exception as e:
                    logger.error(f"Unexpected OpenAI error: {e}")

            # Fallback to Anthropic if available
            if self.anthropic_client:
                try:
                    analysis = await self._analyze_with_anthropic(data)
                    if analysis:
                        return self._create_sentiment_response(data, analysis)
                except Exception as e:
                    logger.error(f"Anthropic analysis failed: {e}")

            # If both AI services fail, use technical analysis
            logger.warning("All AI analysis attempts failed, using technical analysis")
            return await self._get_technical_analysis(data)

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self._get_neutral_sentiment()

    async def _wait_for_rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.min_delay_between_calls:
            await asyncio.sleep(self.min_delay_between_calls - time_since_last_call)
        self.last_api_call = time.time()

    async def _analyze_with_openai(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze with OpenAI with improved retry logic and longer delays"""
        prompt = self._create_analysis_prompt(data)

        for attempt in range(self.max_retries):
            try:
                # Increase delay between attempts significantly
                if attempt > 0:
                    delay = self.retry_delay * (4 ** attempt)  # Exponential backoff with higher base
                    logger.info(f"Waiting {delay} seconds before retry {attempt + 1}")
                    await asyncio.sleep(delay)

                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    completion = await loop.run_in_executor(
                        executor,
                        lambda: self.openai_client.chat.completions.create(
                            model="gpt-4",
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
                        logger.info(f"OpenAI analysis successful: {result}")
                        return result

            except RateLimitError:
                logger.warning(f"OpenAI rate limit hit on attempt {attempt + 1}, will retry in {delay} seconds")
            except Exception as e:
                logger.error(f"OpenAI analysis error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    continue
                break

        logger.info("Falling back to technical analysis after OpenAI attempts exhausted")
        return None

    async def _analyze_with_anthropic(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze with Anthropic as fallback"""
        if not self.anthropic_client:
            logger.warning("Anthropic client not initialized")
            return None

        prompt = self._create_analysis_prompt(data)

        for attempt in range(self.max_retries):
            try:
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    completion = await loop.run_in_executor(
                        executor,
                        lambda: self.anthropic_client.messages.create(
                            model="claude-3-5-sonnet-20241022",  # Latest Anthropic model
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

            except Exception as e:
                logger.error(f"Anthropic analysis error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        return None

    async def _get_technical_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced technical analysis fallback with improved metrics"""
        try:
            # Calculate more detailed metrics
            engagement_scores = [self._get_engagement_score(item) for item in data.get('items', [])]
            total_engagement = sum(engagement_scores)
            avg_engagement = total_engagement / len(engagement_scores) if engagement_scores else 0

            sentiment_score = self._calculate_base_sentiment(data)
            confidence = min(0.7, max(0.4, avg_engagement / 100 if avg_engagement > 0 else 0.4))

            analysis = {
                "sentiment": "positive" if sentiment_score > 0.6 else "negative" if sentiment_score < 0.4 else "neutral",
                "confidence": confidence,
                "score": sentiment_score,
                "source": "technical_analysis",
                "timestamp": datetime.now().isoformat(),
                "key_points": [
                    "Analysis based on technical indicators and social metrics",
                    f"Total engagement: {total_engagement}",
                    f"Average engagement: {avg_engagement:.2f}"
                ],
                "market_signals": [
                    "Strong social engagement" if avg_engagement > 50 else "Moderate social activity" if avg_engagement > 10 else "Limited social data",
                    "Positive sentiment trend" if sentiment_score > 0.6 else "Negative sentiment trend" if sentiment_score < 0.4 else "Neutral market sentiment"
                ],
                "risk_level": "low" if confidence > 0.6 else "medium" if confidence > 0.4 else "high"
            }

            logger.info(f"Technical analysis results: {analysis}")
            return analysis

        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            return self._get_neutral_sentiment()

    def _get_engagement_score(self, item: Dict[str, Any]) -> float:
        """Calculate engagement score for a single item"""
        try:
            score = 0.0
            if 'likes' in item:
                score += item['likes'] * 0.5
            if 'comments' in item:
                score += item['comments'] * 1.0
            if 'shares' in item:
                score += item['shares'] * 1.5
            return score
        except Exception:
            return 0.0

    def _calculate_base_sentiment(self, data: Dict[str, Any]) -> float:
        """Calculate base sentiment score from raw data"""
        try:
            total_items = len(data.get('items', []))
            if total_items == 0:
                return 0.5

            positive_count = sum(1 for item in data.get('items', [])
                               if self._is_positive_content(item))

            return positive_count / total_items
        except Exception:
            return 0.5

    def _is_positive_content(self, item: Dict[str, Any]) -> bool:
        """Determine if content is positive based on simple heuristics"""
        try:
            positive_keywords = {'bull', 'buy', 'up', 'moon', 'gain', 'profit', 'growth'}
            negative_keywords = {'bear', 'sell', 'down', 'crash', 'loss', 'drop', 'dump'}

            text = ' '.join(str(v).lower() for v in item.values() if isinstance(v, str))

            positive_matches = sum(1 for word in positive_keywords if word in text)
            negative_matches = sum(1 for word in negative_keywords if word in text)

            return positive_matches > negative_matches
        except Exception:
            return False

    def _get_neutral_sentiment(self) -> Dict[str, Any]:
        """Return neutral sentiment with low confidence"""
        return {
            "sentiment": "neutral",
            "confidence": 0.3,
            "score": 0.5,
            "source": "fallback",
            "timestamp": datetime.now().isoformat(),
            "key_points": ["Insufficient data for analysis"],
            "market_signals": ["No clear market direction"],
            "risk_level": "high"
        }

    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create analysis prompt with metrics"""
        return f"""
        Analyze the following market data for sentiment:

        Items: {len(data.get('items', []))}
        Average Engagement: {sum(self._get_engagement_score(item) for item in data.get('items', [])) / max(1, len(data.get('items', [])))}
        Timeframe: {data.get('timeframe', 'recent')}

        Provide analysis in JSON format:
        {{
            "sentiment": "positive/negative/neutral",
            "confidence": float between 0 and 1,
            "key_points": list of strings,
            "market_signals": list of strings,
            "risk_level": "low/medium/high"
        }}
        """

    def _validate_ai_response(self, response: Dict[str, Any]) -> bool:
        """Validate AI response format"""
        required_fields = ['sentiment', 'confidence', 'key_points', 'market_signals']
        return all(field in response for field in required_fields)

    def _create_sentiment_response(self, data: Dict[str, Any], 
                                 analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized sentiment response"""
        return {
            "sentiment": analysis.get('sentiment', 'neutral'),
            "confidence": analysis.get('confidence', 0.5),
            "score": self._calculate_sentiment_score(analysis),
            "key_points": analysis.get('key_points', []),
            "market_signals": analysis.get('market_signals', []),
            "risk_level": analysis.get('risk_level', 'medium'),
            "source": "ai_analysis",
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_sentiment_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate numerical sentiment score"""
        try:
            sentiment_map = {
                'positive': 0.75,
                'neutral': 0.5,
                'negative': 0.25
            }
            base_score = sentiment_map.get(analysis.get('sentiment', 'neutral'), 0.5)
            confidence = min(max(analysis.get('confidence', 0.5), 0.0), 1.0)

            return max(0.0, min(1.0, base_score * confidence + 0.5 * (1 - confidence)))
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.5

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
                                await asyncio.sleep(1 * (2**attempt))  # Exponential backoff

                        except Exception as e:
                            logger.warning(f"Reddit fetch attempt {attempt + 1} failed: {e}")
                            if attempt == 2:  # Last attempt
                                raise
                            await asyncio.sleep(1 * (2**attempt))  # Exponential backoff

                except Exception as sub_e:
                    logger.warning(f"Error fetching from subreddit {subreddit}: {sub_e}")
                    continue

            logger.info(f"Successfully retrieved {len(posts)} total posts from Reddit")
            return posts

        except Exception as e:
            logger.error(f"Error getting Reddit data: {e}")
            return []