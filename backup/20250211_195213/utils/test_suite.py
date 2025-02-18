import logging
import time
import json
from datetime import datetime, timedelta
from utils.auto_trader import AutoTrader
from utils.prediction_model import PredictionModel
from utils.data_loader import CryptoDataLoader

class AurumBotTester:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_loader = CryptoDataLoader()

    async def test_stability(self, duration_minutes=30):
        """Test system stability"""
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes)

            bot = AutoTrader("BTC-USD", initial_balance=10000)
            errors = []
            iterations = 0

            while datetime.now() < end_time:
                try:
                    signal = await bot.analyze_market_async(self.data_loader.get_historical_data("BTC-USD"))
                    if signal:
                        result = await bot.execute_trade_async(signal)
                        iterations += 1
                        time.sleep(10)  # Interval between iterations
                except Exception as e:
                    errors.append(str(e))
                    self.logger.error(f"Error during test: {str(e)}")

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
            self.logger.error(f"Stability test failed: {str(e)}")
            return None

    async def test_performance(self):
        """Test system performance"""
        try:
            start_time = time.time()

            # Test market analysis speed
            market_analysis_times = []
            for _ in range(10):
                t0 = time.time()
                bot = AutoTrader("BTC-USD")
                await bot.analyze_market_async(self.data_loader.get_historical_data("BTC-USD"))
                market_analysis_times.append(time.time() - t0)

            # Test prediction
            prediction_times = []
            model = PredictionModel()
            data = self.data_loader.get_historical_data("BTC-USD", period='30d')
            for _ in range(5):
                t0 = time.time()
                await model.predict_async(data)
                prediction_times.append(time.time() - t0)

            return {
                "avg_market_analysis_time": sum(market_analysis_times) / len(market_analysis_times),
                "avg_prediction_time": sum(prediction_times) / len(prediction_times),
                "total_test_time": time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Performance test failed: {str(e)}")
            return None