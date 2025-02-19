```python
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from utils.strategies.dex_sniping import DexSnipingStrategy

@pytest.fixture
def mock_config():
    return {
        'min_liquidity': 5,
        'max_buy_tax': 10,
        'min_holders': 50,
        'risk_per_trade': 0.02,
        'max_position_size': 0.1,
        'rpc_url': 'https://api.mainnet-beta.solana.com'
    }

@pytest.fixture
def strategy(mock_config):
    return DexSnipingStrategy(mock_config)

@pytest.mark.asyncio
async def test_analyze_market_with_insufficient_liquidity(strategy):
    # Test that strategy rejects pairs with insufficient liquidity
    market_data = {
        'liquidity': {'usd': 1000},  # Below minimum
        'pairAddress': '0x123',
        'tokenAddress': '0x456'
    }
    
    signals = await strategy.analyze_market(market_data)
    assert len(signals) == 0, "Should reject low liquidity pairs"

@pytest.mark.asyncio
async def test_analyze_market_with_valid_pair(strategy):
    # Test analysis of valid trading pair
    market_data = {
        'liquidity': {'usd': 10000},
        'pairAddress': '0x123',
        'tokenAddress': '0x456',
        'price': 1.0
    }
    
    signals = await strategy.analyze_market(market_data)
    assert len(signals) > 0, "Should generate signals for valid pairs"
    
    signal = signals[0]
    assert 'action' in signal
    assert 'confidence' in signal
    assert signal['confidence'] >= 0.0 and signal['confidence'] <= 1.0

@pytest.mark.asyncio
async def test_validate_trade_with_insufficient_balance(strategy):
    # Test trade validation with insufficient balance
    signal = {
        'action': 'SNIPE',
        'confidence': 0.8,
        'position_size': 1.0,
        'token_address': '0x123'
    }
    portfolio = {
        'balance': 0.5,  # Less than position size
        'min_trade_size': 0.1
    }
    
    is_valid = await strategy.validate_trade(signal, portfolio)
    assert not is_valid, "Should reject trades with insufficient balance"

@pytest.mark.asyncio
async def test_validate_trade_with_valid_conditions(strategy):
    # Test trade validation with valid conditions
    signal = {
        'action': 'SNIPE',
        'confidence': 0.9,
        'position_size': 0.1,
        'token_address': '0x123'
    }
    portfolio = {
        'balance': 1.0,
        'min_trade_size': 0.01
    }
    
    is_valid = await strategy.validate_trade(signal, portfolio)
    assert is_valid, "Should accept valid trades"

@pytest.mark.asyncio
async def test_position_size_calculation(strategy):
    # Test position size calculation
    price = 100.0
    risk_score = 0.3
    
    position_size = strategy._calculate_position_size(price, risk_score)
    assert position_size > 0, "Position size should be positive"
    assert position_size <= strategy.max_position_size, "Position size should respect maximum limit"

@pytest.mark.asyncio
async def test_pair_safety_checks(strategy):
    # Test pair safety verification
    pair = {
        'token': '0x123',
        'pair': '0x456',
        'liquidity': 10000
    }
    
    is_safe = await strategy._is_pair_safe(pair)
    assert isinstance(is_safe, bool), "Safety check should return boolean"

def test_cost_optimization(strategy):
    # Test that strategy implements cost optimization
    # Check caching
    assert hasattr(strategy, 'scanned_pairs'), "Should implement pair caching"
    
    # Check batch processing
    assert hasattr(strategy, '_filter_opportunities'), "Should implement batch processing"
```
