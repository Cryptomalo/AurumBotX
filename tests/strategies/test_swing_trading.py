import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.strategies.swing_trading import SwingTradingStrategy

@pytest.fixture
def mock_market_data():
    # Create realistic market data for swing trading testing
    dates = pd.date_range(start='2025-01-01', periods=100, freq='1h')
    df = pd.DataFrame({
        'Open': np.random.normal(100, 2, 100),
        'High': np.random.normal(102, 2, 100),
        'Low': np.random.normal(98, 2, 100),
        'Close': np.random.normal(100, 2, 100),
        'Volume': np.random.normal(1000000, 200000, 100)
    }, index=dates)
    return df

@pytest.fixture
def mock_config():
    return {
        'trend_period': 20,
        'profit_target': 0.15,
        'stop_loss': 0.10,
        'min_trend_strength': 0.6,
        'max_position_size': 0.2,
        'risk_per_trade': 0.02,
        'rsi_period': 14,
        'volume_ma_period': 20,
        'atr_period': 14
    }

@pytest.fixture
def strategy(mock_config):
    return SwingTradingStrategy(mock_config)

@pytest.mark.asyncio
async def test_technical_analysis(strategy, mock_market_data):
    # Test technical analysis components
    analysis = await strategy.analyze_market(mock_market_data)

    assert isinstance(analysis, dict), "Should return analysis dictionary"
    required_metrics = [
        'trend_direction',
        'trend_strength',
        'volume_ratio',
        'rsi',
        'atr',
        'macd',
        'macd_signal'
    ]
    for metric in required_metrics:
        assert metric in analysis, f"Analysis should include {metric}"

def test_sentiment_analysis(strategy):
    # Test sentiment analysis with mock data
    sentiment_score = strategy._technical_sentiment(pd.DataFrame({
        'Close': np.random.normal(100, 2, 50),
        'Volume': np.random.normal(1000000, 200000, 50)
    }))

    assert isinstance(sentiment_score, float), "Should return float sentiment score"
    assert 0 <= sentiment_score <= 1, "Sentiment score should be normalized"

@pytest.mark.asyncio
async def test_signal_generation(strategy, mock_market_data):
    # Test signal generation
    analysis = await strategy.analyze_market(mock_market_data)
    signals = strategy.generate_signals(analysis)

    assert isinstance(signals, dict), "Should return signals dictionary"
    assert 'action' in signals, "Should include action"
    assert 'confidence' in signals, "Should include confidence score"

def test_position_sizing_optimization(strategy):
    # Test position sizing with different market conditions
    test_cases = [
        {'price': 100, 'stop_loss_pct': 0.05, 'confidence': 0.1},  # Low risk
        {'price': 100, 'stop_loss_pct': 0.05, 'confidence': 0.5},  # Medium risk
        {'price': 100, 'stop_loss_pct': 0.05, 'confidence': 0.9}   # High risk
    ]

    for case in test_cases:
        size = strategy._calculate_position_size(
            case['price'], 
            case['stop_loss_pct'],
            case['confidence']
        )
        assert 0 < size <= strategy.max_position_size, "Position size should be within limits"
        # Higher confidence should allow larger position sizes
        assert size <= (case['confidence'] * strategy.max_position_size), "Position size should scale with confidence"

@pytest.mark.asyncio
async def test_risk_management(strategy, mock_market_data):
    # Test risk management functionality
    analysis = await strategy.analyze_market(mock_market_data)
    signals = strategy.generate_signals(analysis)

    if signals['action'] != 'hold':
        assert 'stop_loss' in signals, "Active signals should include stop loss"
        assert 'target_price' in signals, "Active signals should include target price"

        # Verify risk-reward ratio
        current_price = mock_market_data['Close'].iloc[-1]
        risk = abs(signals['stop_loss'] - current_price)
        reward = abs(signals['target_price'] - current_price)
        assert reward >= risk * 1.5, "Risk-reward ratio should be at least 1:1.5"

@pytest.mark.asyncio
async def test_trade_validation(strategy):
    # Test trade validation with different scenarios
    portfolio = {
        'available_capital': 10000,
        'total_capital': 20000,
        'current_spread': 0.001
    }

    valid_signal = {
        'action': 'buy',
        'confidence': 0.8,
        'target_price': 105,
        'stop_loss': 95,
        'size_factor': 0.1
    }

    invalid_signal = {
        'action': 'buy',
        'confidence': 0.4,  # Too low
        'target_price': 101,
        'stop_loss': 99,
        'size_factor': 0.5  # Too large
    }

    assert await strategy.validate_trade(valid_signal, portfolio), "Should accept valid trade"
    assert not await strategy.validate_trade(invalid_signal, portfolio), "Should reject invalid trade"

def test_cost_efficiency(strategy, mock_market_data):
    # Test API and computation efficiency
    import time

    # Measure API call efficiency
    start_time = time.time()
    analysis = await strategy.analyze_market(mock_market_data)
    execution_time = time.time() - start_time

    assert execution_time < 1.0, "Analysis should be efficient"

    # Verify caching mechanism
    cached_analysis = await strategy.analyze_market(mock_market_data)
    assert analysis['trend_direction'] == cached_analysis['trend_direction'], "Should use cached calculations where possible"

@pytest.mark.asyncio
async def test_market_condition_adaptation(strategy, mock_market_data):
    # Test strategy adaptation to different market conditions
    # Bullish market
    mock_market_data['Close'] = mock_market_data['Close'] * 1.1
    bullish_analysis = await strategy.analyze_market(mock_market_data)

    # Bearish market
    mock_market_data['Close'] = mock_market_data['Close'] * 0.9
    bearish_analysis = await strategy.analyze_market(mock_market_data)

    assert bullish_analysis['trend_direction'] != bearish_analysis['trend_direction'], "Should adapt to market conditions"