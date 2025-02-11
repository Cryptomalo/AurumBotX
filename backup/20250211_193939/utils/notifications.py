import os
from twilio.rest import Client
from datetime import datetime

class TradingNotifier:
    def __init__(self):
        # Inizializza il client Twilio
        self.client = None
        self.phone_number = None
        self.setup_complete = False
        
    def setup(self, to_phone_number):
        """
        Configura il notificatore con le credenziali Twilio
        """
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
            
            if not all([account_sid, auth_token, self.phone_number]):
                return False
                
            self.client = Client(account_sid, auth_token)
            self.to_phone_number = to_phone_number
            self.setup_complete = True
            return True
            
        except Exception as e:
            print(f"Error setting up Twilio: {str(e)}")
            return False
            
    def send_trade_notification(self, action, symbol, price, quantity, profit_loss=None):
        """
        Invia una notifica per un'operazione di trading
        """
        if not self.setup_complete:
            return
            
        try:
            message = f"Trading Bot Alert - {symbol}\n"
            message += f"Action: {action}\n"
            message += f"Price: ${price:.2f}\n"
            message += f"Quantity: {quantity:.6f}\n"
            
            if profit_loss is not None:
                message += f"P/L: ${profit_loss:.2f}\n"
                
            message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=self.to_phone_number
            )
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            
    def send_error_notification(self, symbol, error_message):
        """
        Invia una notifica in caso di errore
        """
        if not self.setup_complete:
            return
            
        try:
            message = f"Trading Bot Error - {symbol}\n"
            message += f"Error: {error_message}\n"
            message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=self.to_phone_number
            )
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            
    def send_price_alert(self, symbol, price, change_percent):
        """
        Invia un alert per variazioni significative di prezzo
        """
        if not self.setup_complete:
            return
            
        try:
            message = f"Price Alert - {symbol}\n"
            message += f"Current Price: ${price:.2f}\n"
            message += f"24h Change: {change_percent:.2%}\n"
            message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=self.to_phone_number
            )
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
