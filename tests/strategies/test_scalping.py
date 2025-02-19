```python
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from utils.strategies.scalping import ScalpingStrategy

@pytest.fixture
def mock_market_data():
    # Create mock market data for testing
    dates = pd.date_range(start='2025-01-01', periods=100, freq='1min')
    df = pd.DataFrame({
        'Open': np.random.normal(100, 1, 100),
        'High': np.random.normal(101, 1, 100),
        'Low': np.random.normal(99, 1, 100),
        'Close': np.random.normal(100, 1, 100),
        'Volume': np.random.normal(1000000, 100000, 100)
    }, index=dates)
    return df

@pytest.fixture
def mock_config():
    return {
        'volume_threshold': 1000000,
        'min_volatility': 0.002,
        'profit_target': 0.005,
        'initial_stop_loss': 0.003,
        'trailing_stop': 0.002,
        'max_position_size': 0.1,
        'risk_per_trade': 0.02
    }

@pytest.fixture
def strategy(mock_config):
    return ScalpingStrategy(mock_config)

@pytest.mark.asyncio
async def test_market_analysis(strategy, mock_market_data):
    # Test market analysis functionality
    analysis = await strategy.analyze_market(mock_market_data)
    
    assert isinstance(analysis, list), "Should return list of signals"
    if len(analysis) > 0:
        signal = analysis[0]
        assert all(key in signal for key in ['action', 'confidence', 'target_price', 'stop_loss'])

@pytest.mark.asyncio
async def test_signal_generation_performance(strategy, mock_market_data):
    # Test signal generation performance
    start_time = datetime.now()
    signals = await strategy.analyze_market(mock_market_data)
    execution_time = (datetime.now() - start_time).total_seconds()
    
    assert execution_time < 1.0, "Market analysis should complete within 1 second"

@pytest.mark.asyncio
async def test_validate_trade(strategy):
    signal = {
        'action': 'buy',
        'confidence': 0.8,
        'target_price': 101.0,
        'stop_loss': 99.0,
        'size_factor': 0.1
    }
    portfolio = {
        'available_capital': 1000,
        'total_capital': 10000,
        'current_spread': 0.0005
    }
    
    is_valid = await strategy.validate_trade(signal, portfolio)
    assert isinstance(is_valid, bool), "Trade validation should return boolean"

def test_position_sizing(strategy):
    # Test position sizing logic
    price = 100.0
    risk_score = 0.3
    position_size = strategy._calculate_position_size(price, risk_score)
    
    assert position_size > 0, "Position size should be positive"
    assert position_size <= strategy.max_position_size, "Position size should respect maximum limit"

@pytest.mark.asyncio
async def test_risk_management(strategy, mock_market_data):
    # Test risk management features
    signals = await strategy.analyze_market(mock_market_data)
    
    for signal in signals:
        assert 'stop_loss' in signal, "All signals should include stop loss"
        assert 'target_price' in signal, "All signals should include target price"
        
        # Verify risk-reward ratio
        if 'action' in signal and signal['action'] != 'hold':
            risk = abs(signal['stop_loss'] - mock_market_data['Close'].iloc[-1])
            reward = abs(signal['target_price'] - mock_market_data['Close'].iloc[-1])
            assert reward > risk, "Reward should be greater than risk"

@pytest.mark.asyncio
async def test_api_call_optimization(strategy, mock_market_data):
    # Test that strategy minimizes API calls
    start_time = datetime.now()
    
    # Simulate multiple market analyses
    for _ in range(10):
        await strategy.analyze_market(mock_market_data)
    
    execution_time = (datetime.now() - start_time).total_seconds()
    assert execution_time < 10.0, "Multiple analyses should be efficient"

def test_memory_usage(strategy, mock_market_data):
    # Test memory efficiency
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Run multiple analyses
    for _ in range(10):
        strategy.generate_signals(mock_market_data)
    
    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
    
    assert memory_increase < 50, "Memory usage should be efficient"
```
