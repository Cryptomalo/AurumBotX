import asyncio
import logging
from datetime import datetime
import os
import signal
import sys
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from utils.trading_bot import WebSocketHandler
from utils.strategies.strategy_manager import StrategyManager
from utils.sentiment_analyzer import SentimentAnalyzer

# Setup logging
log_filename = f'test_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ])
logger = logging.getLogger(__name__)

class TestBot:
    def __init__(self):
        logger.info("Initializing TestBot...")
        self.engine = None
        self.Session = None
        self.websocket_handler: Optional[WebSocketHandler] = None
        self.strategy_manager: Optional[StrategyManager] = None
        self.sentiment_analyzer: Optional[SentimentAnalyzer] = None
        self.should_run: bool = True
        self.setup_signal_handlers()
        logger.info("TestBot initialized successfully")

    def setup_signal_handlers(self) -> None:
        """Configure signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        logger.info("Signal handlers configured")

    def handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle graceful shutdown"""
        logger.info("Received shutdown signal...")
        self.should_run = False

    async def initialize_components(self) -> bool:
        """Initialize components with retry"""
        try:
            logger.info("Initializing components...")
            # Initialize database connection
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                logger.error("DATABASE_URL not set")
                raise ValueError("DATABASE_URL not set")

            logger.info("Initializing database connection...")
            # Remove SSL parameter from connection URL if present
            if 'sslmode=' in db_url:
                db_url = db_url.replace('?sslmode=require', '')

            self.engine = create_engine(db_url)
            self.Session = sessionmaker(bind=self.engine)

            if not await self.db_health_check():
                logger.error("Database health check failed")
                raise ValueError("Database health check failed")

            # Initialize components
            logger.info("Initializing WebSocket handler...")
            self.websocket_handler = WebSocketHandler(db_url)

            logger.info("Initializing Strategy manager...")
            self.strategy_manager = StrategyManager()

            logger.info("Initializing Sentiment analyzer...")
            self.sentiment_analyzer = SentimentAnalyzer()

            logger.info("All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            return False

    async def db_health_check(self) -> bool:
        """Verify database health with synchronous session"""
        if not self.Session:
            logger.error("Database session not initialized during health check")
            raise ValueError("Database session not initialized")

        max_attempts = 3
        retry_delay = 5

        for attempt in range(max_attempts):
            try:
                logger.info(f"Attempt {attempt + 1} of database health check")

                # Test simple query using synchronous session
                session = self.Session()
                try:
                    logger.debug("Executing test query...")
                    session.execute(text("SELECT 1"))
                    session.commit()
                    logger.info("Database health check passed")
                    return True
                except Exception as e:
                    logger.error(f"Test query failed: {str(e)}")
                    session.rollback()
                    raise
                finally:
                    session.close()

            except Exception as e:
                logger.error(
                    f"Database health check attempt {attempt + 1} failed: {str(e)}"
                )
                if attempt < max_attempts - 1:
                    logger.info(
                        f"Waiting {retry_delay}s before next attempt..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2

        logger.error("Database health check failed after all attempts")
        return False

    async def test_websocket(self) -> bool:
        """Test connessione WebSocket"""
        if not self.websocket_handler:
            logger.error("WebSocket handler not initialized")
            return False

        try:
            logger.info("Tentativo connessione WebSocket...")
            if not await self.websocket_handler.connect_websocket():
                logger.error("Test WebSocket fallito: impossibile connettersi")
                return False

            logger.info("Test WebSocket superato: connessione stabilita")
            return True

        except Exception as e:
            logger.error(f"Test WebSocket fallito con errore: {str(e)}")
            return False

    async def test_strategies(self) -> bool:
        """Test strategie di trading"""
        if not self.strategy_manager:
            logger.error("Strategy manager not initialized")
            return False

        try:
            logger.info("Inizializzazione test strategie...")
            # Test strategia DEX
            dex_config = {
                'rpc_url': 'https://bsc-dataseed.binance.org/',
                'min_liquidity': 5,
                'max_buy_tax': 10,
                'min_holders': 50
            }

            # Attiva e testa la strategia
            logger.info("Attivazione strategia DEX...")
            if await self.strategy_manager.activate_strategy(
                    'dex_sniping', dex_config):
                logger.info(
                    "Test strategia DEX superato: attivazione riuscita")
                return True

            logger.error(
                "Test strategia DEX fallito: attivazione non riuscita")
            return False

        except Exception as e:
            logger.error(f"Test strategie fallito con errore: {str(e)}")
            return False

    async def test_sentiment_analysis(self) -> bool:
        """Test analisi sentiment"""
        if not self.sentiment_analyzer:
            logger.error("Sentiment analyzer not initialized")
            return False

        try:
            logger.info("Esecuzione analisi sentiment per BTC...")
            sentiment_data = await self.sentiment_analyzer.analyze_social_sentiment(
                "BTC")
            if sentiment_data and 'score' in sentiment_data:
                logger.info(
                    f"Test sentiment analysis superato. Score: {sentiment_data['score']}"
                )
                return True

            logger.error("Test sentiment analysis fallito: dati non validi")
            return False

        except Exception as e:
            logger.error(
                f"Test sentiment analysis fallito con errore: {str(e)}")
            return False

    async def run_all_tests(self) -> bool:
        """Esegue tutti i test con gestione errori"""
        try:
            logger.info("Avvio suite di test...")
            if not await self.initialize_components():
                logger.error("Inizializzazione componenti fallita")
                return False

            test_results = {
                'websocket': await self.test_websocket(),
                'strategies': await self.test_strategies(),
                'sentiment': await self.test_sentiment_analysis()
            }

            # Verifica risultati
            all_passed = all(test_results.values())
            if all_passed:
                logger.info("Tutti i test completati con successo")
            else:
                failed_tests = [
                    name for name, passed in test_results.items() if not passed
                ]
                logger.error(f"Test falliti: {', '.join(failed_tests)}")

            return all_passed

        except Exception as e:
            logger.error(f"Errore durante l'esecuzione dei test: {str(e)}")
            return False
        finally:
            await self.cleanup()

    async def cleanup(self) -> None:
        """Pulizia risorse"""
        try:
            logger.info("Avvio procedura di cleanup...")
            if self.websocket_handler:
                await self.websocket_handler.cleanup()
            if self.strategy_manager:
                for strategy_name in list(
                        self.strategy_manager.active_strategies.keys()):
                    await self.strategy_manager.deactivate_strategy(
                        strategy_name)
            if self.engine:
                self.engine.dispose()
            logger.info("Pulizia risorse completata")
        except Exception as e:
            logger.error(f"Errore durante la pulizia: {str(e)}")


if __name__ == "__main__":
    logger.info("Avvio programma principale...")
    bot = TestBot()
    success = asyncio.run(bot.run_all_tests())
    sys.exit(0 if success else 1)