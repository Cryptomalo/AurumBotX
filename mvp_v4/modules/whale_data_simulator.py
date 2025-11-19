"""
Whale Data Simulator - For Development & Testing
Generates realistic whale transaction data when real API is unavailable
Based on historical patterns from Alpha Arena and real whale movements
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List
import json


class WhaleDataSimulator:
    """
    Simulates realistic whale transaction data
    for development and testing purposes
    """
    
    def __init__(self, seed: int = None):
        """
        Initialize simulator
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed:
            random.seed(seed)
        
        # Realistic parameters based on historical data
        self.avg_transactions_per_6h = {
            "bitcoin": 40,
            "ethereum": 35,
            "solana": 25
        }
        
        self.exchange_types = [
            "binance", "coinbase", "kraken", "okx", "bybit",
            "bitfinex", "huobi", "gemini"
        ]
    
    def generate_transaction(self, 
                           symbol: str = "bitcoin",
                           timestamp: int = None,
                           bias: str = "neutral") -> Dict:
        """
        Generate a single realistic whale transaction
        
        Args:
            symbol: Cryptocurrency symbol
            timestamp: Unix timestamp (default: random in last 6h)
            bias: "bullish", "bearish", or "neutral"
            
        Returns:
            Transaction dict matching Whale Alert format
        """
        if timestamp is None:
            # Random time in last 6 hours
            hours_ago = random.uniform(0, 6)
            timestamp = int((datetime.now() - timedelta(hours=hours_ago)).timestamp())
        
        # Generate transaction amount (realistic distribution)
        # Most transactions: $1-5M
        # Some transactions: $5-20M
        # Few transactions: $20-100M
        # Rare transactions: $100M+
        
        rand = random.random()
        if rand < 0.70:  # 70% small
            amount_usd = random.uniform(1_000_000, 5_000_000)
        elif rand < 0.90:  # 20% medium
            amount_usd = random.uniform(5_000_000, 20_000_000)
        elif rand < 0.98:  # 8% large
            amount_usd = random.uniform(20_000_000, 100_000_000)
        else:  # 2% mega
            amount_usd = random.uniform(100_000_000, 500_000_000)
        
        # Determine direction based on bias
        if bias == "bullish":
            # More outflows (accumulation)
            is_outflow = random.random() < 0.70
        elif bias == "bearish":
            # More inflows (distribution)
            is_outflow = random.random() < 0.30
        else:  # neutral
            is_outflow = random.random() < 0.50
        
        # Generate from/to
        exchange = random.choice(self.exchange_types)
        
        if is_outflow:
            # Exchange → Wallet (bullish)
            from_data = {
                "owner": exchange,
                "owner_type": "exchange"
            }
            to_data = {
                "owner": "unknown",
                "owner_type": "unknown"
            }
        else:
            # Wallet → Exchange (bearish)
            from_data = {
                "owner": "unknown",
                "owner_type": "unknown"
            }
            to_data = {
                "owner": exchange,
                "owner_type": "exchange"
            }
        
        return {
            "blockchain": symbol,
            "symbol": symbol.upper()[:3],
            "transaction_type": "transfer",
            "hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
            "from": from_data,
            "to": to_data,
            "timestamp": timestamp,
            "amount": amount_usd / 50000,  # Approximate coin amount
            "amount_usd": amount_usd,
            "transaction_count": 1
        }
    
    def generate_scenario(self, 
                         symbol: str = "bitcoin",
                         scenario: str = "bullish") -> List[Dict]:
        """
        Generate a complete scenario of whale transactions
        
        Args:
            symbol: Cryptocurrency symbol
            scenario: "strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"
            
        Returns:
            List of whale transactions
        """
        # Determine transaction count and bias
        base_count = self.avg_transactions_per_6h.get(symbol, 30)
        
        if scenario == "strong_bullish":
            count = int(base_count * 1.5)  # More activity
            bias = "bullish"
            # Add some mega transactions
            mega_count = random.randint(1, 3)
        elif scenario == "bullish":
            count = int(base_count * 1.2)
            bias = "bullish"
            mega_count = random.randint(0, 1)
        elif scenario == "neutral":
            count = base_count
            bias = "neutral"
            mega_count = 0
        elif scenario == "bearish":
            count = int(base_count * 1.2)
            bias = "bearish"
            mega_count = random.randint(0, 1)
        else:  # strong_bearish
            count = int(base_count * 1.5)
            bias = "bearish"
            mega_count = random.randint(1, 3)
        
        transactions = []
        
        # Generate regular transactions
        for _ in range(count):
            tx = self.generate_transaction(symbol, bias=bias)
            transactions.append(tx)
        
        # Add mega transactions if needed
        for _ in range(mega_count):
            tx = self.generate_transaction(symbol, bias=bias)
            # Force mega size
            tx['amount_usd'] = random.uniform(100_000_000, 500_000_000)
            transactions.append(tx)
        
        # Sort by timestamp
        transactions.sort(key=lambda x: x['timestamp'])
        
        return transactions
    
    def simulate_whale_alert_response(self, 
                                     symbol: str = "bitcoin",
                                     scenario: str = "neutral") -> Dict:
        """
        Simulate complete Whale Alert API response
        
        Args:
            symbol: Cryptocurrency symbol
            scenario: Market scenario
            
        Returns:
            Dict matching Whale Alert API response format
        """
        transactions = self.generate_scenario(symbol, scenario)
        
        return {
            "result": "success",
            "cursor": None,
            "count": len(transactions),
            "transactions": transactions
        }


# Integration with WhaleFlowTracker
class WhaleFlowTrackerWithSimulator:
    """
    Extended WhaleFlowTracker that can use simulated data
    """
    
    def __init__(self, use_simulator: bool = False, scenario: str = "neutral"):
        """
        Initialize tracker with optional simulator
        
        Args:
            use_simulator: If True, use simulated data instead of real API
            scenario: Scenario for simulator
        """
        from whale_flow_tracker import WhaleFlowTracker
        
        self.tracker = WhaleFlowTracker()
        self.use_simulator = use_simulator
        self.scenario = scenario
        
        if use_simulator:
            self.simulator = WhaleDataSimulator()
            print(f"⚠️  Using SIMULATED whale data (scenario: {scenario})")
    
    def get_whale_data(self, symbol: str = "bitcoin") -> Dict:
        """Get whale data (real or simulated)"""
        
        if self.use_simulator:
            # Generate simulated transactions
            response = self.simulator.simulate_whale_alert_response(symbol, self.scenario)
            transactions = response['transactions']
            
            # Use tracker's analysis methods
            flow_analysis = self.tracker.analyze_flows(transactions)
            pattern_analysis = self.tracker.detect_patterns(transactions)
            
            adjusted_confidence = flow_analysis['confidence'] * pattern_analysis['pattern_multiplier']
            adjusted_confidence = min(adjusted_confidence, 0.95)
            
            top_transactions = sorted(
                transactions,
                key=lambda x: x.get('amount_usd', 0),
                reverse=True
            )[:5]
            
            top_tx_summary = []
            for tx in top_transactions:
                classification = self.tracker.classify_transaction(tx)
                top_tx_summary.append({
                    "amount_usd": classification['amount_usd'],
                    "type": classification['type'],
                    "signal": classification['signal'],
                    "size_class": classification['size_class'],
                    "timestamp": datetime.fromtimestamp(tx['timestamp']).isoformat()
                })
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "analysis_window_hours": self.tracker.buffer_hours,
                "data_source": f"SIMULATED ({self.scenario})",
                "whale_activity": {
                    **flow_analysis,
                    "adjusted_confidence": adjusted_confidence,
                    "pattern_detected": pattern_analysis['has_cluster'] or pattern_analysis['has_sustained'],
                    "pattern_details": pattern_analysis
                },
                "top_transactions": top_tx_summary
            }
            
            self.tracker._print_summary(result)
            return result
        else:
            # Use real API
            return self.tracker.get_whale_data(symbol)


def test_simulator():
    """Test whale data simulator with different scenarios"""
    
    scenarios = ["strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"]
    
    for scenario in scenarios:
        print(f"\n{'='*70}")
        print(f"TESTING SCENARIO: {scenario.upper()}")
        print(f"{'='*70}\n")
        
        tracker = WhaleFlowTrackerWithSimulator(use_simulator=True, scenario=scenario)
        data = tracker.get_whale_data("bitcoin")
        
        # Save to file
        filename = f"/home/ubuntu/AurumBotX/mvp_v4/data/whale_sim_{scenario}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved to: {filename}\n")


if __name__ == "__main__":
    test_simulator()
