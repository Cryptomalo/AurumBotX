from binance.client import Client

class BinanceAdapter:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)

    def get_balance(self):
        account_info = self.client.get_account()
        balances = {}
        for balance in account_info['balances']:
            asset = balance['asset']
            balances[asset] = {
                'free': float(balance['free']),
                'locked': float(balance['locked'])
            }
        return balances

    def get_ticker(self, symbol):
        return self.client.get_ticker(symbol=symbol)

    def create_order(self, symbol, side, type, quantity):
        return self.client.create_order(
            symbol=symbol,
            side=side,
            type=type,
            quantity=quantity
        )

    def get_order(self, symbol, order_id):
        return self.client.get_order(symbol=symbol, orderId=order_id)

    def get_all_orders(self, symbol):
        return self.client.get_all_orders(symbol=symbol)

    def get_my_trades(self, symbol):
        return self.client.get_my_trades(symbol=symbol)

