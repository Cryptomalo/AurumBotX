
import logging
import time
from datetime import datetime, timedelta
from utils.auto_trader import AutoTrader
from utils.prediction_model import PredictionModel
from utils.data_loader import CryptoDataLoader

class AurumBotTester:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_loader = CryptoDataLoader()
        
    def test_stability(self, duration_minutes=30):
        """Test di stabilità del sistema"""
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            bot = AutoTrader("BTC-USD", initial_balance=10000)
            errors = []
            iterations = 0
            
            while datetime.now() < end_time:
                try:
                    signal = bot.analyze_market()
                    bot.execute_trade(signal)
                    iterations += 1
                    time.sleep(10)  # Intervallo tra le iterazioni
                except Exception as e:
                    errors.append(str(e))
                    self.logger.error(f"Errore durante il test: {str(e)}")
            
            return {
                "duration": duration_minutes,
                "iterations": iterations,
                "errors": len(errors),
                "error_rate": len(errors) / iterations if iterations > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Test di stabilità fallito: {str(e)}")
            return None

    def test_performance(self):
        """Test delle performance del sistema"""
        try:
            start_time = time.time()
            
            # Test velocità analisi mercato
            market_analysis_times = []
            for _ in range(10):
                t0 = time.time()
                bot = AutoTrader("BTC-USD")
                bot.analyze_market()
                market_analysis_times.append(time.time() - t0)
            
            # Test predizione
            prediction_times = []
            model = PredictionModel()
            data = self.data_loader.get_historical_data("BTC-USD", period='30d')
            for _ in range(5):
                t0 = time.time()
                model.predict(data)
                prediction_times.append(time.time() - t0)
            
            return {
                "avg_market_analysis_time": sum(market_analysis_times) / len(market_analysis_times),
                "avg_prediction_time": sum(prediction_times) / len(prediction_times),
                "total_test_time": time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Test performance fallito: {str(e)}")
            return None
