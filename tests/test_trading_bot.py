import unittest
from utils.auto_trader import AutoTrader
from utils.data_loader import CryptoDataLoader

class TestTradingBot(unittest.TestCase):

    def setUp(self):
        self.trading_pair = "BTC/USDT"
        self.initial_balance = 1000.0
        self.risk_per_trade = 0.02
        self.testnet_mode = True
        self.bot = AutoTrader(
            symbol=self.trading_pair,
            initial_balance=self.initial_balance,
            risk_per_trade=self.risk_per_trade,
            testnet=self.testnet_mode
        )
        self.data_loader = CryptoDataLoader(testnet=self.testnet_mode)

    def test_initialization(self):
        self.assertIsNotNone(self.bot)
        self.assertEqual(self.bot.symbol, self.trading_pair)
        self.assertEqual(self.bot.initial_balance, self.initial_balance)
        self.assertEqual(self.bot.risk_per_trade, self.risk_per_trade / 100)

    def test_data_loader_initialization(self):
        self.assertIsNotNone(self.data_loader)

    def test_historical_data_loading(self):
        df = self.data_loader.get_historical_data(self.trading_pair, '1d')
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)

if __name__ == '__main__':
    unittest.main()
