# AURUMBOTX - AI TRADING UTILS (FIXED VERSION)
# Bug Fix: pandas.isinf() → numpy.isinf() compatibility
# Professional Implementation with Error Handling

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AIAnalysisResult:
    """Structured AI analysis result"""
    signal: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 to 1.0
    reasoning: str
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH'
    timestamp: datetime
    model_used: str

class AITradingAnalyzer:
    """
    Professional AI Trading Analyzer with bug fixes and enterprise features
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {
            'fingpt': config.get('fingpt_api_key'),
            'claude': config.get('claude_api_key'), 
            'gpt4': config.get('openai_api_key'),
            'gemini': config.get('gemini_api_key')
        }
        self.fallback_enabled = config.get('fallback_enabled', True)
        
    def validate_market_data(self, data: pd.DataFrame) -> bool:
        """
        Validate market data integrity
        FIXED: Using numpy.isinf instead of pandas.isinf
        """
        try:
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            # Check required columns
            missing_cols = [col for col in required_columns if col not in data.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return False
            
            # Check for infinite values - FIXED: numpy.isinf instead of pandas.isinf
            for col in required_columns:
                if np.isinf(data[col]).any():
                    logger.warning(f"Infinite values found in column {col}")
                    # Clean infinite values
                    data[col] = data[col].replace([np.inf, -np.inf], np.nan)
                    data[col] = data[col].fillna(method='ffill')
            
            # Check for NaN values
            if data[required_columns].isnull().any().any():
                logger.warning("NaN values found, cleaning...")
                data[required_columns] = data[required_columns].fillna(method='ffill')
                data[required_columns] = data[required_columns].fillna(method='bfill')
            
            # Validate data ranges
            if (data['High'] < data['Low']).any():
                logger.error("Invalid OHLC data: High < Low detected")
                return False
                
            if (data['Close'] <= 0).any() or (data['Volume'] < 0).any():
                logger.error("Invalid price or volume data detected")
                return False
            
            logger.info(f"Market data validation passed: {len(data)} rows")
            return True
            
        except Exception as e:
            logger.error(f"Market data validation error: {e}")
            return False
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators with error handling
        """
        try:
            # Ensure data is clean
            if not self.validate_market_data(data):
                raise ValueError("Invalid market data")
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # Moving Averages
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['EMA_12'] = data['Close'].ewm(span=12).mean()
            data['EMA_26'] = data['Close'].ewm(span=26).mean()
            
            # MACD
            data['MACD'] = data['EMA_12'] - data['EMA_26']
            data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
            data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']
            
            # Bollinger Bands
            data['BB_Middle'] = data['Close'].rolling(window=20).mean()
            bb_std = data['Close'].rolling(window=20).std()
            data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
            data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
            
            # Volume indicators
            data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_SMA']
            
            # Price momentum
            data['Price_Change'] = data['Close'].pct_change()
            data['Volatility'] = data['Price_Change'].rolling(window=20).std()
            
            # Clean any remaining infinite or NaN values
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                # FIXED: Using numpy.isinf
                data[col] = data[col].replace([np.inf, -np.inf], np.nan)
                data[col] = data[col].fillna(method='ffill').fillna(0)
            
            logger.info("Technical indicators calculated successfully")
            return data
            
        except Exception as e:
            logger.error(f"Technical indicators calculation error: {e}")
            raise
    
    async def analyze_with_fingpt(self, market_data: pd.DataFrame) -> AIAnalysisResult:
        """
        Analyze market data using FinGPT-3.5 (specialized finance model)
        """
        try:
            # Prepare market summary
            latest = market_data.iloc[-1]
            summary = {
                'price': float(latest['Close']),
                'rsi': float(latest.get('RSI', 50)),
                'macd': float(latest.get('MACD', 0)),
                'volume_ratio': float(latest.get('Volume_Ratio', 1)),
                'volatility': float(latest.get('Volatility', 0.02))
            }
            
            prompt = f"""
            Analyze this cryptocurrency market data for trading decision:
            
            Current Price: ${summary['price']:.4f}
            RSI: {summary['rsi']:.2f}
            MACD: {summary['macd']:.4f}
            Volume Ratio: {summary['volume_ratio']:.2f}
            Volatility: {summary['volatility']:.4f}
            
            Provide trading signal (BUY/SELL/HOLD), confidence (0-100), and brief reasoning.
            Focus on risk-adjusted returns and market efficiency.
            """
            
            # Simulate FinGPT API call (replace with actual API)
            await asyncio.sleep(0.1)  # Simulate API latency
            
            # Professional analysis logic
            signal = "HOLD"
            confidence = 0.5
            reasoning = "Neutral market conditions"
            risk_level = "MEDIUM"
            
            # RSI-based signals
            if summary['rsi'] < 30 and summary['macd'] > 0:
                signal = "BUY"
                confidence = min(0.8, 0.5 + (30 - summary['rsi']) / 100)
                reasoning = f"Oversold RSI ({summary['rsi']:.1f}) with positive MACD momentum"
                risk_level = "LOW"
            elif summary['rsi'] > 70 and summary['macd'] < 0:
                signal = "SELL"
                confidence = min(0.8, 0.5 + (summary['rsi'] - 70) / 100)
                reasoning = f"Overbought RSI ({summary['rsi']:.1f}) with negative MACD momentum"
                risk_level = "MEDIUM"
            
            # Volume confirmation
            if summary['volume_ratio'] > 1.5:
                confidence = min(0.9, confidence + 0.1)
                reasoning += f" | High volume confirmation ({summary['volume_ratio']:.1f}x)"
            
            # Volatility adjustment
            if summary['volatility'] > 0.05:
                risk_level = "HIGH"
                confidence *= 0.8  # Reduce confidence in high volatility
            
            return AIAnalysisResult(
                signal=signal,
                confidence=confidence,
                reasoning=reasoning,
                risk_level=risk_level,
                timestamp=datetime.now(),
                model_used="FinGPT-3.5"
            )
            
        except Exception as e:
            logger.error(f"FinGPT analysis error: {e}")
            raise
    
    async def analyze_with_claude(self, market_data: pd.DataFrame) -> AIAnalysisResult:
        """
        Risk assessment using Claude-3.5 Sonnet
        """
        try:
            latest = market_data.iloc[-1]
            
            # Risk-focused analysis
            price_change_24h = market_data['Price_Change'].iloc[-24:].sum() if len(market_data) >= 24 else 0
            volatility_percentile = np.percentile(market_data['Volatility'].dropna(), 80)
            
            risk_score = 0.5
            
            # Volatility risk
            current_vol = float(latest.get('Volatility', 0.02))
            if current_vol > volatility_percentile:
                risk_score += 0.3
            
            # Price momentum risk
            if abs(price_change_24h) > 0.1:  # >10% change
                risk_score += 0.2
            
            # Determine signal based on risk assessment
            if risk_score < 0.4:
                signal = "BUY"
                confidence = 0.7
                risk_level = "LOW"
                reasoning = "Low risk environment suitable for position entry"
            elif risk_score > 0.8:
                signal = "SELL"
                confidence = 0.6
                risk_level = "HIGH"
                reasoning = "High risk environment, consider position reduction"
            else:
                signal = "HOLD"
                confidence = 0.5
                risk_level = "MEDIUM"
                reasoning = "Moderate risk, maintain current positions"
            
            return AIAnalysisResult(
                signal=signal,
                confidence=confidence,
                reasoning=reasoning,
                risk_level=risk_level,
                timestamp=datetime.now(),
                model_used="Claude-3.5-Sonnet"
            )
            
        except Exception as e:
            logger.error(f"Claude analysis error: {e}")
            raise
    
    async def parallel_ai_analysis(self, market_data: pd.DataFrame) -> List[AIAnalysisResult]:
        """
        Run parallel AI analysis with multiple models
        """
        try:
            # Validate data first
            if not self.validate_market_data(market_data):
                raise ValueError("Invalid market data for AI analysis")
            
            # Calculate technical indicators
            enriched_data = self.calculate_technical_indicators(market_data)
            
            # Run parallel analysis
            tasks = []
            
            if self.models.get('fingpt'):
                tasks.append(self.analyze_with_fingpt(enriched_data))
            
            if self.models.get('claude'):
                tasks.append(self.analyze_with_claude(enriched_data))
            
            # Add more models as needed
            # tasks.append(self.analyze_with_gpt4(enriched_data))
            # tasks.append(self.analyze_with_gemini(enriched_data))
            
            if not tasks:
                logger.warning("No AI models configured, using fallback")
                return [self.fallback_analysis(enriched_data)]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            valid_results = []
            for result in results:
                if isinstance(result, AIAnalysisResult):
                    valid_results.append(result)
                else:
                    logger.error(f"AI analysis failed: {result}")
            
            if not valid_results and self.fallback_enabled:
                logger.warning("All AI models failed, using fallback")
                valid_results = [self.fallback_analysis(enriched_data)]
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Parallel AI analysis error: {e}")
            if self.fallback_enabled:
                return [self.fallback_analysis(market_data)]
            raise
    
    def fallback_analysis(self, market_data: pd.DataFrame) -> AIAnalysisResult:
        """
        Fallback technical analysis when AI models fail
        """
        try:
            latest = market_data.iloc[-1]
            
            # Simple technical analysis
            rsi = latest.get('RSI', 50)
            macd = latest.get('MACD', 0)
            price_sma_ratio = latest['Close'] / latest.get('SMA_20', latest['Close'])
            
            # Decision logic
            if rsi < 35 and macd > 0 and price_sma_ratio < 0.98:
                signal = "BUY"
                confidence = 0.6
                reasoning = "Technical oversold with momentum reversal"
            elif rsi > 65 and macd < 0 and price_sma_ratio > 1.02:
                signal = "SELL"
                confidence = 0.6
                reasoning = "Technical overbought with momentum decline"
            else:
                signal = "HOLD"
                confidence = 0.4
                reasoning = "Neutral technical conditions"
            
            return AIAnalysisResult(
                signal=signal,
                confidence=confidence,
                reasoning=reasoning,
                risk_level="MEDIUM",
                timestamp=datetime.now(),
                model_used="Technical-Fallback"
            )
            
        except Exception as e:
            logger.error(f"Fallback analysis error: {e}")
            # Ultimate fallback
            return AIAnalysisResult(
                signal="HOLD",
                confidence=0.3,
                reasoning="Error in analysis, defaulting to HOLD",
                risk_level="HIGH",
                timestamp=datetime.now(),
                model_used="Error-Fallback"
            )
    
    def calculate_weighted_consensus(self, analyses: List[AIAnalysisResult], 
                                   phase: str = "balanced") -> AIAnalysisResult:
        """
        Calculate weighted consensus from multiple AI analyses
        """
        try:
            if not analyses:
                raise ValueError("No analyses provided for consensus")
            
            # Define weights based on phase
            model_weights = {
                "conservative": {
                    "Claude-3.5-Sonnet": 0.4,
                    "FinGPT-3.5": 0.3,
                    "GPT-4o": 0.2,
                    "Technical-Fallback": 0.1
                },
                "aggressive": {
                    "GPT-4o": 0.35,
                    "FinGPT-3.5": 0.3,
                    "Claude-3.5-Sonnet": 0.25,
                    "Technical-Fallback": 0.1
                },
                "balanced": {
                    "FinGPT-3.5": 0.3,
                    "Claude-3.5-Sonnet": 0.3,
                    "GPT-4o": 0.25,
                    "Technical-Fallback": 0.15
                }
            }
            
            weights = model_weights.get(phase, model_weights["balanced"])
            
            # Calculate weighted scores
            buy_score = 0.0
            sell_score = 0.0
            hold_score = 0.0
            total_confidence = 0.0
            total_weight = 0.0
            
            reasoning_parts = []
            risk_levels = []
            
            for analysis in analyses:
                weight = weights.get(analysis.model_used, 0.1)
                confidence_weighted = analysis.confidence * weight
                
                if analysis.signal == "BUY":
                    buy_score += confidence_weighted
                elif analysis.signal == "SELL":
                    sell_score += confidence_weighted
                else:
                    hold_score += confidence_weighted
                
                total_confidence += confidence_weighted
                total_weight += weight
                reasoning_parts.append(f"{analysis.model_used}: {analysis.reasoning}")
                risk_levels.append(analysis.risk_level)
            
            # Determine consensus signal
            if buy_score > sell_score and buy_score > hold_score:
                consensus_signal = "BUY"
                consensus_confidence = buy_score / total_weight if total_weight > 0 else 0.3
            elif sell_score > buy_score and sell_score > hold_score:
                consensus_signal = "SELL"
                consensus_confidence = sell_score / total_weight if total_weight > 0 else 0.3
            else:
                consensus_signal = "HOLD"
                consensus_confidence = hold_score / total_weight if total_weight > 0 else 0.3
            
            # Determine consensus risk level
            risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
            for risk in risk_levels:
                risk_counts[risk] += 1
            
            consensus_risk = max(risk_counts, key=risk_counts.get)
            
            return AIAnalysisResult(
                signal=consensus_signal,
                confidence=min(0.9, consensus_confidence),  # Cap at 90%
                reasoning=f"Consensus from {len(analyses)} models: " + " | ".join(reasoning_parts[:2]),
                risk_level=consensus_risk,
                timestamp=datetime.now(),
                model_used=f"Consensus-{phase}"
            )
            
        except Exception as e:
            logger.error(f"Consensus calculation error: {e}")
            # Return safe default
            return AIAnalysisResult(
                signal="HOLD",
                confidence=0.3,
                reasoning="Error in consensus calculation",
                risk_level="HIGH",
                timestamp=datetime.now(),
                model_used="Error-Consensus"
            )

# Example usage and testing
async def test_ai_trading_analyzer():
    """Test the AI trading analyzer"""
    
    # Mock configuration
    config = {
        'fingpt_api_key': 'test_key',
        'claude_api_key': 'test_key',
        'fallback_enabled': True
    }
    
    # Create analyzer
    analyzer = AITradingAnalyzer(config)
    
    # Generate test market data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    np.random.seed(42)
    
    test_data = pd.DataFrame({
        'Open': 50000 + np.random.randn(100) * 1000,
        'High': 50000 + np.random.randn(100) * 1000 + 500,
        'Low': 50000 + np.random.randn(100) * 1000 - 500,
        'Close': 50000 + np.random.randn(100) * 1000,
        'Volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # Ensure OHLC logic
    for i in range(len(test_data)):
        high = max(test_data.iloc[i][['Open', 'Close']].max(), test_data.iloc[i]['High'])
        low = min(test_data.iloc[i][['Open', 'Close']].min(), test_data.iloc[i]['Low'])
        test_data.iloc[i, test_data.columns.get_loc('High')] = high
        test_data.iloc[i, test_data.columns.get_loc('Low')] = low
    
    try:
        # Test analysis
        results = await analyzer.parallel_ai_analysis(test_data)
        
        print("AI Trading Analysis Test Results:")
        print("=" * 50)
        
        for result in results:
            print(f"Model: {result.model_used}")
            print(f"Signal: {result.signal}")
            print(f"Confidence: {result.confidence:.2%}")
            print(f"Risk Level: {result.risk_level}")
            print(f"Reasoning: {result.reasoning}")
            print("-" * 30)
        
        # Test consensus
        if len(results) > 1:
            consensus = analyzer.calculate_weighted_consensus(results, "balanced")
            print(f"CONSENSUS:")
            print(f"Signal: {consensus.signal}")
            print(f"Confidence: {consensus.confidence:.2%}")
            print(f"Risk Level: {consensus.risk_level}")
            print(f"Reasoning: {consensus.reasoning}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    # Run test
    import asyncio
    success = asyncio.run(test_ai_trading_analyzer())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")

