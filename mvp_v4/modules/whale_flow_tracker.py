"""
Whale Flow Tracker MVP - AurumBotX v4.0
Tracks large cryptocurrency transactions and whale movements
Uses Whale Alert API to detect accumulation/distribution patterns
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class WhaleFlowTracker:
    """
    Tracks whale transactions and analyzes exchange flows
    to generate bullish/bearish signals
    """
    
    def __init__(self, api_key: str = "demo", min_value_usd: int = 1000000):
        """
        Initialize Whale Flow Tracker
        
        Args:
            api_key: Whale Alert API key (default: "demo" for free tier)
            min_value_usd: Minimum transaction value to track (default: $1M)
        """
        self.api_key = api_key
        self.min_value_usd = min_value_usd
        self.api_url = "https://api.whale-alert.io/v1/transactions"
        self.buffer_hours = 6  # Analysis window
        
        # Cache for API responses
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def fetch_whale_transactions(self, 
                                 symbol: str = "bitcoin",
                                 start_time: Optional[int] = None) -> List[Dict]:
        """
        Fetch whale transactions from Whale Alert API
        
        Args:
            symbol: Cryptocurrency symbol (e.g., "bitcoin", "ethereum")
            start_time: Unix timestamp for start time (default: 6h ago)
            
        Returns:
            List of whale transactions
        """
        # Calculate start time if not provided
        if start_time is None:
            start_time = int((datetime.now() - timedelta(hours=self.buffer_hours)).timestamp())
        
        # Check cache
        cache_key = f"{symbol}_{start_time}"
        if cache_key in self.cache:
            cache_data, cache_time = self.cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                print(f"✅ Using cached data for {symbol}")
                return cache_data
        
        # API parameters
        params = {
            "api_key": self.api_key,
            "start": start_time,
            "currency": symbol,
            "min_value": self.min_value_usd
        }
        
        try:
            print(f"🔍 Fetching whale transactions for {symbol}...")
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'transactions' not in data:
                print(f"⚠️  No transactions found in response")
                return []
            
            transactions = data['transactions']
            
            # Cache the result
            self.cache[cache_key] = (transactions, time.time())
            
            print(f"✅ Fetched {len(transactions)} whale transactions")
            return transactions
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching whale transactions: {e}")
            return []
    
    def classify_transaction(self, tx: Dict) -> Dict:
        """
        Classify a transaction as bullish/bearish based on direction
        
        Args:
            tx: Transaction dictionary from Whale Alert
            
        Returns:
            Classification dict with type, signal, and weight
        """
        from_type = tx.get('from', {}).get('owner_type', 'unknown')
        to_type = tx.get('to', {}).get('owner_type', 'unknown')
        amount_usd = tx.get('amount_usd', 0)
        
        # Determine transaction type
        if to_type == 'exchange':
            tx_type = 'exchange_inflow'
            signal = 'bearish'  # Whale sending to exchange = likely to sell
        elif from_type == 'exchange':
            tx_type = 'exchange_outflow'
            signal = 'bullish'  # Whale withdrawing from exchange = accumulation
        else:
            tx_type = 'wallet_transfer'
            signal = 'neutral'
        
        # Calculate weight based on size
        if amount_usd >= 100_000_000:  # $100M+
            weight = 30
            size_class = 'mega'
        elif amount_usd >= 20_000_000:  # $20M+
            weight = 10
            size_class = 'large'
        elif amount_usd >= 5_000_000:  # $5M+
            weight = 3
            size_class = 'medium'
        else:  # $1M-5M
            weight = 1
            size_class = 'small'
        
        return {
            'type': tx_type,
            'signal': signal,
            'weight': weight,
            'size_class': size_class,
            'amount_usd': amount_usd,
            'timestamp': tx.get('timestamp', 0)
        }
    
    def analyze_flows(self, transactions: List[Dict]) -> Dict:
        """
        Analyze whale flows and generate trading signal
        
        Args:
            transactions: List of whale transactions
            
        Returns:
            Analysis dict with flows, signal, and confidence
        """
        if not transactions:
            return {
                "inflows_usd": 0,
                "outflows_usd": 0,
                "net_flow_usd": 0,
                "signal": "neutral",
                "confidence": 0.0,
                "transactions_count": 0,
                "weighted_score": 0
            }
        
        # Initialize counters
        inflows = 0
        outflows = 0
        weighted_score = 0
        
        # Classify and aggregate transactions
        for tx in transactions:
            classification = self.classify_transaction(tx)
            
            if classification['type'] == 'exchange_inflow':
                inflows += classification['amount_usd']
                weighted_score -= classification['weight']  # Bearish
            elif classification['type'] == 'exchange_outflow':
                outflows += classification['amount_usd']
                weighted_score += classification['weight']  # Bullish
        
        # Calculate net flow
        net_flow = outflows - inflows
        
        # Generate signal based on net flow and weighted score
        if net_flow > 100_000_000 and weighted_score > 20:
            signal = "strong_bullish"
            confidence = 0.85
        elif net_flow > 50_000_000 and weighted_score > 10:
            signal = "bullish"
            confidence = 0.75
        elif net_flow < -100_000_000 and weighted_score < -20:
            signal = "strong_bearish"
            confidence = 0.85
        elif net_flow < -50_000_000 and weighted_score < -10:
            signal = "bearish"
            confidence = 0.75
        elif abs(net_flow) < 10_000_000:
            signal = "neutral"
            confidence = 0.50
        else:
            # Weak signal
            if net_flow > 0:
                signal = "weak_bullish"
                confidence = 0.60
            else:
                signal = "weak_bearish"
                confidence = 0.60
        
        return {
            "inflows_usd": inflows,
            "outflows_usd": outflows,
            "net_flow_usd": net_flow,
            "signal": signal,
            "confidence": confidence,
            "transactions_count": len(transactions),
            "weighted_score": weighted_score
        }
    
    def detect_patterns(self, transactions: List[Dict]) -> Dict:
        """
        Detect patterns in whale transactions (clustering, sustained activity)
        
        Args:
            transactions: List of whale transactions
            
        Returns:
            Pattern detection results
        """
        if len(transactions) < 2:
            return {
                "has_cluster": False,
                "has_sustained": False,
                "pattern_multiplier": 1.0
            }
        
        # Sort by timestamp
        sorted_txs = sorted(transactions, key=lambda x: x.get('timestamp', 0))
        
        # Detect clustering (multiple transactions within 1 hour)
        clusters = []
        current_cluster = [sorted_txs[0]]
        
        for i in range(1, len(sorted_txs)):
            time_diff = sorted_txs[i]['timestamp'] - sorted_txs[i-1]['timestamp']
            
            if time_diff <= 3600:  # Within 1 hour
                current_cluster.append(sorted_txs[i])
            else:
                if len(current_cluster) >= 3:
                    clusters.append(current_cluster)
                current_cluster = [sorted_txs[i]]
        
        # Check last cluster
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)
        
        has_cluster = len(clusters) > 0
        
        # Detect sustained activity (transactions spread over >6 hours)
        time_span = sorted_txs[-1]['timestamp'] - sorted_txs[0]['timestamp']
        has_sustained = time_span > 21600  # 6 hours
        
        # Calculate pattern multiplier
        multiplier = 1.0
        if has_cluster:
            multiplier *= 2.0
        if has_sustained:
            multiplier *= 1.5
        
        return {
            "has_cluster": has_cluster,
            "has_sustained": has_sustained,
            "pattern_multiplier": multiplier,
            "cluster_count": len(clusters),
            "time_span_hours": time_span / 3600
        }
    
    def get_whale_data(self, symbol: str = "bitcoin") -> Dict:
        """
        Main method: Get complete whale flow data and analysis
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Complete whale flow analysis
        """
        print(f"\n{'='*60}")
        print(f"🐋 WHALE FLOW ANALYSIS - {symbol.upper()}")
        print(f"{'='*60}")
        
        # Fetch transactions
        transactions = self.fetch_whale_transactions(symbol)
        
        # Analyze flows
        flow_analysis = self.analyze_flows(transactions)
        
        # Detect patterns
        pattern_analysis = self.detect_patterns(transactions)
        
        # Adjust confidence based on patterns
        adjusted_confidence = flow_analysis['confidence'] * pattern_analysis['pattern_multiplier']
        adjusted_confidence = min(adjusted_confidence, 0.95)  # Cap at 95%
        
        # Get top 5 largest transactions for context
        top_transactions = sorted(
            transactions,
            key=lambda x: x.get('amount_usd', 0),
            reverse=True
        )[:5]
        
        top_tx_summary = []
        for tx in top_transactions:
            classification = self.classify_transaction(tx)
            top_tx_summary.append({
                "amount_usd": classification['amount_usd'],
                "type": classification['type'],
                "signal": classification['signal'],
                "size_class": classification['size_class'],
                "timestamp": datetime.fromtimestamp(tx['timestamp']).isoformat()
            })
        
        # Compile final result
        result = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "analysis_window_hours": self.buffer_hours,
            "whale_activity": {
                **flow_analysis,
                "adjusted_confidence": adjusted_confidence,
                "pattern_detected": pattern_analysis['has_cluster'] or pattern_analysis['has_sustained'],
                "pattern_details": pattern_analysis
            },
            "top_transactions": top_tx_summary
        }
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    def _print_summary(self, data: Dict):
        """Print formatted summary of whale flow analysis"""
        activity = data['whale_activity']
        
        print(f"\n📊 FLOW SUMMARY")
        print(f"   Inflows:  ${activity['inflows_usd']:>15,.0f}")
        print(f"   Outflows: ${activity['outflows_usd']:>15,.0f}")
        print(f"   Net Flow: ${activity['net_flow_usd']:>15,.0f}")
        print(f"\n🎯 SIGNAL")
        print(f"   Direction: {activity['signal'].upper()}")
        print(f"   Confidence: {activity['adjusted_confidence']:.0%}")
        print(f"   Weighted Score: {activity['weighted_score']:+d}")
        print(f"\n📈 ACTIVITY")
        print(f"   Transactions: {activity['transactions_count']}")
        
        if activity['pattern_detected']:
            details = activity['pattern_details']
            print(f"   ⚠️  Pattern Detected:")
            if details['has_cluster']:
                print(f"      - Clustering ({details['cluster_count']} clusters)")
            if details['has_sustained']:
                print(f"      - Sustained activity ({details['time_span_hours']:.1f}h)")
        
        if data['top_transactions']:
            print(f"\n🔝 TOP TRANSACTIONS")
            for i, tx in enumerate(data['top_transactions'][:3], 1):
                print(f"   {i}. ${tx['amount_usd']:,.0f} - {tx['type']} ({tx['signal']})")
        
        print(f"\n{'='*60}\n")
    
    def save_to_file(self, data: Dict, filepath: str):
        """Save whale flow data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Data saved to: {filepath}")


# Test function
def test_whale_flow_tracker():
    """Test the Whale Flow Tracker"""
    print("🧪 Testing Whale Flow Tracker...\n")
    
    # Initialize tracker
    tracker = WhaleFlowTracker(api_key="demo")
    
    # Test with Bitcoin
    btc_data = tracker.get_whale_data("bitcoin")
    
    # Save to file
    tracker.save_to_file(btc_data, "/home/ubuntu/AurumBotX/mvp_v4/data/whale_flow_btc_test.json")
    
    # Test with Ethereum
    print("\n" + "="*60 + "\n")
    eth_data = tracker.get_whale_data("ethereum")
    
    tracker.save_to_file(eth_data, "/home/ubuntu/AurumBotX/mvp_v4/data/whale_flow_eth_test.json")
    
    return btc_data, eth_data


if __name__ == "__main__":
    test_whale_flow_tracker()
