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
        self.last_api_call = 0
        self.min_delay_between_calls = 1.0  # Minimum seconds between API calls
        self.max_retries = 3
        self.retry_delay = 2.0
        self.fallback_enabled = True
        
        # Inizializza attributi per evitare errori
        self.reddit = None
        self.twitter = None
        self.telegram = None
        self.openrouter_client = None

    async def initialize(self):
        """Initialize AI and social clients asynchronously"""
        self.initialize_ai_clients()
        self.initialize_social_clients()

    def initialize_ai_clients(self):
        """Initialize AI clients with proper error handling"""
        try:
            openrouter_key = os.environ.get("OPENROUTER_API_KEY")
            if not openrouter_key:
                logger.warning("OpenRouter API key not found")
                self.openrouter_client = None
            else:
                self.openrouter_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=openrouter_key
                )
                logger.info("OpenRouter client initialized successfully")
        except Exception as e:
            logger.error(f"OpenRouter initialization failed: {e}")
            self.openrouter_client = None

        if not self.openrouter_client:
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
        """Analyze sentiment with improved fallback mechanisms and rate limiting"""
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

            # Try OpenRouter
            if self.openrouter_client:
                try:
                    analysis = await self._analyze_with_openrouter(data)
                    if analysis:
                        logger.info("Successfully analyzed sentiment with OpenRouter")
                        return self._create_sentiment_response(data, analysis)
                except Exception as e:
                    logger.error(f"OpenRouter analysis failed: {e}")

            # If AI service fails, use technical analysis
            logger.warning("AI analysis failed, using technical analysis")
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

    async def _analyze_with_openrouter(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze with OpenRouter with improved retry logic and error handling"""
        if not self.openrouter_client:
            logger.warning("OpenRouter client not initialized")
            return None

        prompt = self._create_analysis_prompt(data)
        current_model = "openai/gpt-3.5-turbo"  # Use a working model for OpenRouter

        for attempt in range(self.max_retries):
            try:
                delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                if attempt > 0:
                    logger.info(f"Waiting {delay} seconds before retry {attempt + 1}")
                    await asyncio.sleep(delay)

                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    completion = await loop.run_in_executor(
                        executor,
                        lambda: self.openrouter_client.chat.completions.create(
                            model=current_model,
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
                        logger.info(f"OpenRouter analysis successful with model {current_model}")
                        return result

            except RateLimitError:
                logger.warning(f"OpenRouter rate limit hit on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    continue
            except APIError as e:
                logger.error(f"OpenRouter API error on attempt {attempt + 1}: {e}")
                if "model_not_found" in str(e) and current_model == "openai/gpt-4o":
                    current_model = "openai/gpt-3.5-turbo"
                    logger.info(f"Falling back to {current_model}")
                    continue
                break
            except Exception as e:
                logger.error(f"Unexpected OpenRouter error: {e}")
                break

        return None

    def _validate_ai_response(self, response: Dict[str, Any]) -> bool:
        """Validate AI response format"""
        try:
            required_fields = ["sentiment", "confidence", "key_points", "market_signals"]
            if not all(field in response for field in required_fields):
                return False

            # Validate sentiment values
            if response["sentiment"] not in ["positive", "negative", "neutral"]:
                return False

            # Validate confidence is float between 0-1
            if not isinstance(response["confidence"], (int, float)):
                return False
            if not 0 <= response["confidence"] <= 1:
                return False

            # Validate arrays
            if not isinstance(response["key_points"], list):
                return False
            if not isinstance(response["market_signals"], list):
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating AI response: {e}")
            return False

    async def _get_technical_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced technical analysis fallback with improved metrics"""
        try:
            # Calculate more detailed metrics
            engagement_scores = [self._get_engagement_score(item) for item in data.get("items", [])]
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
            if "likes" in item:
                score += item["likes"] * 0.5
            if "comments" in item:
                score += item["comments"] * 1.0
            if "shares" in item:
                score += item["shares"] * 1.5
            return score
        except Exception:
            return 0.0

    def _calculate_base_sentiment(self, data: Dict[str, Any]) -> float:
        """Calculate base sentiment score from raw data"""
        try:
            total_items = len(data.get("items", []))
            if total_items == 0:
                return 0.5

            positive_count = sum(1 for item in data.get("items", [])
                               if self._is_positive_content(item))

            return positive_count / total_items
        except Exception:
            return 0.5

    def _is_positive_content(self, item: Dict[str, Any]) -> bool:
        """Determine if content is positive based on simple heuristics"""
        try:
            positive_keywords = {"bull", "buy", "up", "moon", "gain", "profit", "growth"}
            negative_keywords = {"bear", "sell", "down", "crash", "loss", "drop", "dump"}

            text = " ".join(str(v).lower() for v in item.values() if isinstance(v, str))

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

        Items: {len(data.get("items", []))}
        Average Engagement: {sum(self._get_engagement_score(item) for item in data.get("items", [])) / max(1, len(data.get("items", [])))}
        Timeframe: {data.get("timeframe", "recent")}

        Provide analysis in JSON format:
        {{
            "sentiment": "positive/negative/neutral",
            "confidence": float between 0 and 1,
            "key_points": ["point1", "point2"],
            "market_signals": ["signal1", "signal2"],
            "risk_level": "low/medium/high"
        }}
        """

    def _create_sentiment_response(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a standardized sentiment response"""
        return {
            "sentiment": analysis.get("sentiment", "neutral"),
            "confidence": analysis.get("confidence", 0.5),
            "score": self._calculate_base_sentiment(data),
            "source": "openrouter",
            "timestamp": datetime.now().isoformat(),
            "key_points": analysis.get("key_points", []),
            "market_signals": analysis.get("market_signals", []),
            "risk_level": analysis.get("risk_level", "medium")
        }

    async def _get_reddit_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch data from Reddit"""
        if not self.reddit:
            return []

        try:
            subreddit = self.reddit.subreddit("cryptocurrency")
            posts = []
            for submission in subreddit.search(symbol, limit=10):
                posts.append({
                    "title": submission.title,
                    "score": submission.score,
                    "comments": submission.num_comments,
                    "url": submission.url
                })
            return posts
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
            return []





    def get_fallback_sentiment(self, symbol: str) -> float:
        """Fallback sentiment basato su price action"""
        try:
            # Sentiment neutro come fallback
            return 0.0
        except Exception:
            return 0.0
    
    def get_combined_sentiment(self, symbol: str) -> float:
        """Sentiment combinato con fallback"""
        try:
            # Prova sentiment reale
            if self.reddit:
                reddit_sentiment = self.get_reddit_sentiment(symbol)
                if reddit_sentiment is not None:
                    return reddit_sentiment
            
            # Fallback
            return self.get_fallback_sentiment(symbol)
            
        except Exception as e:
            self.logger.warning(f"Sentiment analysis fallback: {e}")
            return 0.0
