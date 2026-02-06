import pytest

from utils.trade_executor_v2 import RobustTradeExecutor


class DummyExchange:
    async def create_market_buy_order(self, symbol, amount):
        return {"id": "1", "status": "FILLED", "symbol": symbol, "amount": amount}

    async def create_market_sell_order(self, symbol, amount):
        return {"id": "2", "status": "FILLED", "symbol": symbol, "amount": amount}


@pytest.mark.asyncio
async def test_trade_executor_executes_buy():
    executor = RobustTradeExecutor(DummyExchange())
    signal = {"action": "buy", "symbol": "BTCUSDT", "confidence": 0.9}
    result = await executor.execute_trade(signal)
    assert result["status"] == "FILLED"
