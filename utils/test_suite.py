import logging
import time
import json
from datetime import datetime, timedelta
import asyncio
from utils.auto_trader import AutoTrader
from utils.prediction_model import PredictionModel
from utils.data_loader import CryptoDataLoader
from utils.sentiment_analyzer import SentimentAnalyzer

class AurumBotTester:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_loader = CryptoDataLoader()
        self.sentiment_analyzer = SentimentAnalyzer()

    async def test_stability(self, duration_minutes=30):
        """Test di stabilità del sistema"""
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes)

            bot = AutoTrader("BTC-USD", initial_balance=10000)
            errors = []
            iterations = 0

            while datetime.now() < end_time:
                try:
                    # Use sync methods since analyze_market is not async
                    signal = bot.analyze_market()
                    if signal:
                        bot.execute_trade(signal)
                    iterations += 1
                    await asyncio.sleep(10)  # Use asyncio.sleep instead of time.sleep
                except Exception as e:
                    errors.append(str(e))
                    self.logger.error(f"Errore durante il test: {str(e)}")

            results = {
                "duration": duration_minutes,
                "iterations": iterations,
                "errors": len(errors),
                "error_rate": len(errors) / iterations if iterations > 0 else 0,
                "success_rate": 1 - (len(errors) / iterations if iterations > 0 else 0),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.logger.info(f"Test Results: {json.dumps(results, indent=2)}")
            return results
        except Exception as e:
            self.logger.error(f"Test di stabilità fallito: {str(e)}")
            return None

    async def test_sentiment_analysis(self, symbol: str = "BTC/USD") -> dict:
        """Test the enhanced sentiment analysis with assistant"""
        try:
            # Test basic sentiment analysis
            standard_analysis = await self.sentiment_analyzer.analyze_with_ai({
                "reddit": [],
                "twitter": [],
                "telegram": [],
                "timestamp": datetime.now().isoformat()
            })

            # Test combined analysis with assistant
            combined_analysis = await self.sentiment_analyzer.analyze_social_sentiment(symbol)

            return {
                "standard_analysis": {
                    "sentiment": standard_analysis.get("sentiment"),
                    "confidence": standard_analysis.get("confidence"),
                    "score": self.sentiment_analyzer.calculate_sentiment_score(standard_analysis)
                },
                "enhanced_analysis": {
                    "sentiment": combined_analysis.get("analysis", {}).get("sentiment"),
                    "confidence": combined_analysis.get("analysis", {}).get("confidence"),
                    "trading_signals": combined_analysis.get("analysis", {}).get("trading_signals", []),
                    "score": combined_analysis.get("score", 0.0)
                },
                "comparison": {
                    "has_trading_signals": bool(combined_analysis.get("analysis", {}).get("trading_signals")),
                    "confidence_improvement": (
                        combined_analysis.get("analysis", {}).get("confidence", 0) -
                        standard_analysis.get("confidence", 0)
                    )
                }
            }
        except Exception as e:
            self.logger.error(f"Sentiment analysis test failed: {str(e)}")
            return None

    async def test_performance(self):
        """Test delle performance del sistema"""
        try:
            start_time = time.time()

            # Test velocità analisi mercato
            market_analysis_times = []
            for _ in range(10):
                t0 = time.time()
                bot = AutoTrader("BTC-USD")
                # Use sync methods since analyze_market is not async
                signal = bot.analyze_market()
                if signal:
                    market_analysis_times.append(time.time() - t0)

            # Test predizione
            prediction_times = []
            model = PredictionModel()
            # Use sync method for historical data
            data = self.data_loader.get_historical_data("BTC-USD", period='30d')
            for _ in range(5):
                t0 = time.time()
                await model.predict(data)  # Assuming predict is async
                prediction_times.append(time.time() - t0)

            return {
                "avg_market_analysis_time": sum(market_analysis_times) / len(market_analysis_times) if market_analysis_times else 0,
                "avg_prediction_time": sum(prediction_times) / len(prediction_times) if prediction_times else 0,
                "total_test_time": time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Test performance fallito: {str(e)}")
            return None

    async def run_all_tests(self):
        """Run all tests sequentially"""
        try:
            self.logger.info("Starting all tests...")

            # Run stability test
            stability_results = await self.test_stability(duration_minutes=15)
            if stability_results:
                self.logger.info("Stability test completed successfully")
            else:
                self.logger.error("Stability test failed")

            # Run sentiment analysis test
            sentiment_results = await self.test_sentiment_analysis()
            if sentiment_results:
                self.logger.info("Sentiment analysis test completed successfully")
            else:
                self.logger.error("Sentiment analysis test failed")

            # Run performance test
            performance_results = await self.test_performance()
            if performance_results:
                self.logger.info("Performance test completed successfully")
            else:
                self.logger.error("Performance test failed")

            return {
                "stability": stability_results,
                "sentiment": sentiment_results,
                "performance": performance_results
            }
        except Exception as e:
            self.logger.error(f"Error running all tests: {str(e)}")
            return None