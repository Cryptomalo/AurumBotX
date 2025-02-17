import os
from twilio.rest import Client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TradingNotifier:
    def __init__(self):
        self.client = None
        self.phone_number = None
        self.setup_complete = False

    def setup(self, to_phone_number: str) -> bool:
        """
        Configura il notificatore con le credenziali Twilio
        """
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')

            if not all([account_sid, auth_token, self.phone_number]):
                logger.error("Missing Twilio credentials")
                return False

            self.client = Client(account_sid, auth_token)
            self.to_phone_number = to_phone_number
            self.setup_complete = True
            logger.info("Twilio notifier setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error setting up Twilio: {str(e)}")
            return False

    def send_trade_notification(self, action: str, symbol: str, price: float, quantity: float, 
                              ml_confidence: float = None, profit_loss: float = None) -> bool:
        """
        Invia una notifica per un'operazione di trading con informazioni ML
        """
        if not self.setup_complete:
            logger.warning("Notifier not setup, skipping notification")
            return False

        try:
            message = f"Trading Bot Alert - {symbol}\n"
            message += f"Action: {action}\n"
            message += f"Price: ${price:.6f}\n"
            message += f"Quantity: {quantity:.6f}\n"

            if ml_confidence is not None:
                message += f"ML Confidence: {ml_confidence:.2%}\n"

            if profit_loss is not None:
                message += f"P/L: ${profit_loss:.2f}\n"

            message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=self.to_phone_number
            )

            logger.info(f"Trade notification sent successfully for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

    def send_error_notification(self, symbol: str, error_message: str) -> bool:
        """
        Invia una notifica in caso di errore
        """
        if not self.setup_complete:
            logger.warning("Notifier not setup, skipping error notification")
            return False

        try:
            message = f"Trading Bot Error - {symbol}\n"
            message += f"Error: {error_message}\n"
            message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=self.to_phone_number
            )

            logger.info(f"Error notification sent successfully for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

    def send_analysis_alert(self, symbol: str, analysis: dict) -> bool:
        """
        Invia un alert per analisi di mercato significative
        """
        if not self.setup_complete:
            logger.warning("Notifier not setup, skipping analysis alert")
            return False

        try:
            message = f"Market Analysis Alert - {symbol}\n"
            message += f"ML Confidence: {analysis.get('ml_confidence', 0):.2%}\n"
            message += f"Technical Score: {analysis.get('technical_score', 0):.2f}\n"
            message += f"Sentiment Score: {analysis.get('sentiment_score', 0):.2f}\n"
            message += f"Viral Coefficient: {analysis.get('viral_score', 0):.2f}\n"
            message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=self.to_phone_number
            )

            logger.info(f"Analysis alert sent successfully for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error sending analysis alert: {str(e)}")
            return False