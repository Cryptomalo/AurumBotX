import os
from twilio.rest import Client
from datetime import datetime
import logging
from typing import Optional

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

    def _validate_and_format_phone_number(self, phone_number: str) -> Optional[str]:
        """Validate and format phone number to E.164 format"""
        try:
            # Remove any non-digit characters
            cleaned = ''.join(filter(str.isdigit, phone_number))

            # Add country code if missing
            if len(cleaned) == 10:  # US number without country code
                cleaned = '1' + cleaned

            if not cleaned.startswith('+'):
                cleaned = '+' + cleaned

            if len(cleaned) < 10 or len(cleaned) > 15:
                logger.error(f"Invalid phone number length: {cleaned}")
                return None

            return cleaned

        except Exception as e:
            logger.error(f"Error formatting phone number: {str(e)}")
            return None

    def send_trade_notification(self, action: str, symbol: str, price: float, quantity: float, 
                            ml_confidence: Optional[float] = None, profit_loss: Optional[float] = None) -> bool:
        """
        Invia una notifica per un'operazione di trading con informazioni ML
        """
        if not self.setup_complete:
            logger.warning("Notifier not setup, skipping notification")
            return False

        try:
            message = f"🤖 Trading Bot Alert - {symbol}\n"
            message += f"📊 Action: {action}\n"
            message += f"💰 Price: ${price:.8f}\n"
            message += f"📈 Quantity: {quantity:.6f}\n"

            if ml_confidence is not None:
                message += f"🎯 ML Confidence: {ml_confidence:.2%}\n"

            if profit_loss is not None:
                message += f"💸 P/L: ${profit_loss:.2f}\n"

            message += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Validate phone number before sending
            formatted_number = self._validate_and_format_phone_number(self.to_phone_number)
            if not formatted_number:
                logger.error("Invalid phone number format")
                return False

            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=formatted_number
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
            message = f"❌ Trading Bot Error - {symbol}\n"
            message += f"⚠️ Error: {error_message}\n"
            message += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            formatted_number = self._validate_and_format_phone_number(self.to_phone_number)
            if not formatted_number:
                logger.error("Invalid phone number format")
                return False

            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=formatted_number
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
            message = f"📊 Market Analysis Alert - {symbol}\n"
            message += f"🎯 ML Confidence: {analysis.get('ml_confidence', 0):.2%}\n"
            message += f"📈 Technical Score: {analysis.get('technical_score', 0):.2f}\n"
            message += f"🌐 Sentiment Score: {analysis.get('sentiment_score', 0):.2f}\n"
            message += f"🚀 Viral Coefficient: {analysis.get('viral_score', 0):.2f}\n"
            message += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            formatted_number = self._validate_and_format_phone_number(self.to_phone_number)
            if not formatted_number:
                logger.error("Invalid phone number format")
                return False

            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=formatted_number
            )

            logger.info(f"Analysis alert sent successfully for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error sending analysis alert: {str(e)}")
            return False

    def send_portfolio_update(self, portfolio_value: float, daily_pnl: float, 
                          active_positions: int) -> bool:
        """
        Invia un aggiornamento giornaliero del portfolio
        """
        if not self.setup_complete:
            logger.warning("Notifier not setup, skipping portfolio update")
            return False

        try:
            message = "📊 Daily Portfolio Update\n"
            message += f"💰 Total Value: ${portfolio_value:,.2f}\n"
            message += f"📈 Daily P/L: ${daily_pnl:,.2f} "
            message += f"({(daily_pnl/portfolio_value)*100:.2f}%)\n"
            message += f"🔄 Active Positions: {active_positions}\n"
            message += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            formatted_number = self._validate_and_format_phone_number(self.to_phone_number)
            if not formatted_number:
                logger.error("Invalid phone number format")
                return False

            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=formatted_number
            )

            logger.info("Portfolio update sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending portfolio update: {str(e)}")
            return False