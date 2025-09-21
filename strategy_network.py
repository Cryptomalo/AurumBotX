#!/usr/bin/env python3
"""
AurumBotX - Strategy Network
Rete intelligente di possibilità strategiche che si adatta dinamicamente
al capitale e alle previsioni di mercato
"""

import json
import time
import math
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class MarketCondition(Enum):
    BULL_STRONG = "bull_strong"      # +5% o più
    BULL_MODERATE = "bull_moderate"  # +2% a +5%
    SIDEWAYS = "sideways"            # -2% a +2%
    BEAR_MODERATE = "bear_moderate"  # -5% a -2%
    BEAR_STRONG = "bear_strong"      # -5% o meno
    VOLATILE = "volatile"            # Alta volatilità

class CapitalTier(Enum):
    MICRO = "micro"          # €100-200
    SMALL = "small"          # €200-500
    MEDIUM = "medium"        # €500-1000
    LARGE = "large"          # €1000+

@dataclass
class StrategyOption:
    name: str
    description: str
    risk_level: float        # 0.0-1.0
    capital_efficiency: float # 0.0-1.0
    market_conditions: List[MarketCondition]
    capital_tiers: List[CapitalTier]
    min_confidence: float    # Confidence AI minima
    position_size_factor: float
    stop_loss: float
    take_profit: float
    max_positions: int
    holding_time: str        # "minutes", "hours", "days"
    success_rate: float      # Storico
    avg_return: float        # Return medio per trade

class StrategyNetwork:
    def __init__(self):
        self.strategies = self._initialize_strategies()
        self.current_capital = 100.0
        self.market_history = []
        self.performance_history = {}
        
    def _initialize_strategies(self) -> Dict[str, StrategyOption]:
        """Inizializza tutte le strategie disponibili"""
        
        strategies = {
            # STRATEGIE CONSERVATIVE (Basso Rischio)
            "conservative_accumulation": StrategyOption(
                name="Conservative Accumulation",
                description="Accumulo graduale con rischio minimo",
                risk_level=0.15,
                capital_efficiency=0.6,
                market_conditions=[MarketCondition.SIDEWAYS, MarketCondition.BULL_MODERATE],
                capital_tiers=[CapitalTier.MICRO, CapitalTier.SMALL],
                min_confidence=0.75,
                position_size_factor=0.08,  # 8% del capitale
                stop_loss=0.03,             # 3% stop loss
                take_profit=0.06,           # 6% take profit
                max_positions=1,
                holding_time="hours",
                success_rate=0.82,
                avg_return=0.045
            ),
            
            "dca_strategy": StrategyOption(
                name="Dollar Cost Averaging",
                description="Acquisti regolari indipendenti dal prezzo",
                risk_level=0.20,
                capital_efficiency=0.7,
                market_conditions=[MarketCondition.BEAR_MODERATE, MarketCondition.SIDEWAYS],
                capital_tiers=[CapitalTier.MICRO, CapitalTier.SMALL, CapitalTier.MEDIUM],
                min_confidence=0.60,
                position_size_factor=0.12,
                stop_loss=0.08,
                take_profit=0.15,
                max_positions=2,
                holding_time="days",
                success_rate=0.75,
                avg_return=0.08
            ),
            
            # STRATEGIE MODERATE (Rischio Medio)
            "momentum_riding": StrategyOption(
                name="Momentum Riding",
                description="Cavalca i trend di mercato con timing preciso",
                risk_level=0.35,
                capital_efficiency=0.8,
                market_conditions=[MarketCondition.BULL_STRONG, MarketCondition.BULL_MODERATE],
                capital_tiers=[CapitalTier.SMALL, CapitalTier.MEDIUM, CapitalTier.LARGE],
                min_confidence=0.70,
                position_size_factor=0.25,
                stop_loss=0.06,
                take_profit=0.18,
                max_positions=2,
                holding_time="hours",
                success_rate=0.68,
                avg_return=0.12
            ),
            
            "breakout_capture": StrategyOption(
                name="Breakout Capture",
                description="Cattura breakout da livelli di resistenza",
                risk_level=0.40,
                capital_efficiency=0.85,
                market_conditions=[MarketCondition.BULL_STRONG, MarketCondition.VOLATILE],
                capital_tiers=[CapitalTier.SMALL, CapitalTier.MEDIUM],
                min_confidence=0.72,
                position_size_factor=0.30,
                stop_loss=0.08,
                take_profit=0.25,
                max_positions=2,
                holding_time="hours",
                success_rate=0.65,
                avg_return=0.16
            ),
            
            "mean_reversion": StrategyOption(
                name="Mean Reversion Enhanced",
                description="Sfrutta i rimbalzi dai livelli di supporto",
                risk_level=0.30,
                capital_efficiency=0.75,
                market_conditions=[MarketCondition.SIDEWAYS, MarketCondition.BEAR_MODERATE],
                capital_tiers=[CapitalTier.MICRO, CapitalTier.SMALL, CapitalTier.MEDIUM],
                min_confidence=0.68,
                position_size_factor=0.20,
                stop_loss=0.05,
                take_profit=0.12,
                max_positions=3,
                holding_time="hours",
                success_rate=0.72,
                avg_return=0.09
            ),
            
            # STRATEGIE AGGRESSIVE (Alto Rischio)
            "scalping_ai": StrategyOption(
                name="AI-Enhanced Scalping",
                description="Scalping rapido con AI per timing perfetto",
                risk_level=0.60,
                capital_efficiency=0.95,
                market_conditions=[MarketCondition.VOLATILE, MarketCondition.BULL_STRONG],
                capital_tiers=[CapitalTier.MEDIUM, CapitalTier.LARGE],
                min_confidence=0.80,
                position_size_factor=0.45,
                stop_loss=0.02,
                take_profit=0.04,
                max_positions=1,
                holding_time="minutes",
                success_rate=0.58,
                avg_return=0.025
            ),
            
            "swing_aggressive": StrategyOption(
                name="Aggressive Swing",
                description="Swing trading aggressivo su movimenti forti",
                risk_level=0.55,
                capital_efficiency=0.90,
                market_conditions=[MarketCondition.BULL_STRONG, MarketCondition.BEAR_STRONG],
                capital_tiers=[CapitalTier.SMALL, CapitalTier.MEDIUM, CapitalTier.LARGE],
                min_confidence=0.75,
                position_size_factor=0.40,
                stop_loss=0.10,
                take_profit=0.30,
                max_positions=2,
                holding_time="days",
                success_rate=0.62,
                avg_return=0.18
            ),
            
            # STRATEGIE SPECIALI
            "arbitrage_hunter": StrategyOption(
                name="Arbitrage Hunter",
                description="Caccia opportunità di arbitraggio tra exchange",
                risk_level=0.10,
                capital_efficiency=0.95,
                market_conditions=[MarketCondition.VOLATILE, MarketCondition.SIDEWAYS],
                capital_tiers=[CapitalTier.MEDIUM, CapitalTier.LARGE],
                min_confidence=0.85,
                position_size_factor=0.50,
                stop_loss=0.01,
                take_profit=0.02,
                max_positions=3,
                holding_time="minutes",
                success_rate=0.88,
                avg_return=0.015
            ),
            
            "news_reaction": StrategyOption(
                name="News Reaction Trading",
                description="Trading basato su reazioni immediate alle news",
                risk_level=0.70,
                capital_efficiency=0.85,
                market_conditions=[MarketCondition.VOLATILE, MarketCondition.BULL_STRONG, MarketCondition.BEAR_STRONG],
                capital_tiers=[CapitalTier.SMALL, CapitalTier.MEDIUM, CapitalTier.LARGE],
                min_confidence=0.78,
                position_size_factor=0.35,
                stop_loss=0.12,
                take_profit=0.40,
                max_positions=1,
                holding_time="hours",
                success_rate=0.55,
                avg_return=0.22
            ),
            
            "correlation_play": StrategyOption(
                name="Correlation Play",
                description="Sfrutta correlazioni tra asset diversi",
                risk_level=0.25,
                capital_efficiency=0.80,
                market_conditions=[MarketCondition.SIDEWAYS, MarketCondition.BULL_MODERATE, MarketCondition.BEAR_MODERATE],
                capital_tiers=[CapitalTier.MEDIUM, CapitalTier.LARGE],
                min_confidence=0.70,
                position_size_factor=0.22,
                stop_loss=0.06,
                take_profit=0.14,
                max_positions=4,
                holding_time="hours",
                success_rate=0.70,
                avg_return=0.10
            ),
            
            # STRATEGIE ADAPTIVE
            "ai_consensus": StrategyOption(
                name="AI Consensus Strategy",
                description="Decisioni basate su consensus di 327 modelli AI",
                risk_level=0.45,
                capital_efficiency=0.92,
                market_conditions=[MarketCondition.BULL_STRONG, MarketCondition.BULL_MODERATE, MarketCondition.VOLATILE],
                capital_tiers=[CapitalTier.SMALL, CapitalTier.MEDIUM, CapitalTier.LARGE],
                min_confidence=0.82,
                position_size_factor=0.35,
                stop_loss=0.07,
                take_profit=0.20,
                max_positions=3,
                holding_time="hours",
                success_rate=0.78,
                avg_return=0.14
            ),
            
            "dynamic_hedging": StrategyOption(
                name="Dynamic Hedging",
                description="Hedging dinamico per proteggere i profitti",
                risk_level=0.20,
                capital_efficiency=0.65,
                market_conditions=[MarketCondition.VOLATILE, MarketCondition.BEAR_MODERATE, MarketCondition.BEAR_STRONG],
                capital_tiers=[CapitalTier.MEDIUM, CapitalTier.LARGE],
                min_confidence=0.65,
                position_size_factor=0.15,
                stop_loss=0.04,
                take_profit=0.08,
                max_positions=5,
                holding_time="hours",
                success_rate=0.80,
                avg_return=0.06
            )
        }
        
        return strategies
    
    def get_available_strategies(self) -> List[str]:
        """
        Get list of available strategy names
        
        Returns:
            List of strategy names
        """
        return list(self.strategies.keys())
    
    def get_capital_tier(self, capital: float) -> CapitalTier:
        """Determina il tier di capitale"""
        if capital < 200:
            return CapitalTier.MICRO
        elif capital < 500:
            return CapitalTier.SMALL
        elif capital < 1000:
            return CapitalTier.MEDIUM
        else:
            return CapitalTier.LARGE
    
    def analyze_market_condition(self, market_data: Dict) -> MarketCondition:
        """Analizza le condizioni di mercato attuali"""
        try:
            # Calcola variazione media del mercato
            total_change = 0
            volatility_sum = 0
            asset_count = 0
            
            for asset, data in market_data.items():
                if 'change_24h' in data:
                    change = data['change_24h']
                    total_change += change
                    volatility_sum += abs(change)
                    asset_count += 1
            
            if asset_count == 0:
                return MarketCondition.SIDEWAYS
            
            avg_change = total_change / asset_count
            avg_volatility = volatility_sum / asset_count
            
            # Determina condizione basata su change e volatilità
            if avg_volatility > 0.08:  # >8% volatilità
                return MarketCondition.VOLATILE
            elif avg_change >= 0.05:   # +5% o più
                return MarketCondition.BULL_STRONG
            elif avg_change >= 0.02:   # +2% a +5%
                return MarketCondition.BULL_MODERATE
            elif avg_change <= -0.05:  # -5% o meno
                return MarketCondition.BEAR_STRONG
            elif avg_change <= -0.02:  # -5% a -2%
                return MarketCondition.BEAR_MODERATE
            else:                      # -2% a +2%
                return MarketCondition.SIDEWAYS
                
        except Exception as e:
            print(f"⚠️ Errore analisi mercato: {e}")
            return MarketCondition.SIDEWAYS
    
    def calculate_strategy_score(self, strategy: StrategyOption, 
                               market_condition: MarketCondition,
                               capital_tier: CapitalTier,
                               ai_confidence: float,
                               current_positions: int) -> float:
        """Calcola score per una strategia specifica"""
        
        score = 0.0
        
        # 1. Market Condition Match (30%)
        if market_condition in strategy.market_conditions:
            score += 0.30
        else:
            score += 0.05  # Penalty per mismatch
        
        # 2. Capital Tier Match (20%)
        if capital_tier in strategy.capital_tiers:
            score += 0.20
        else:
            score += 0.05  # Penalty per mismatch
        
        # 3. AI Confidence (25%)
        if ai_confidence >= strategy.min_confidence:
            confidence_bonus = (ai_confidence - strategy.min_confidence) / (1.0 - strategy.min_confidence)
            score += 0.25 * (1.0 + confidence_bonus)
        else:
            score += 0.05  # Penalty per confidence bassa
        
        # 4. Capital Efficiency (15%)
        score += 0.15 * strategy.capital_efficiency
        
        # 5. Historical Performance (10%)
        performance_score = (strategy.success_rate * 0.6) + (strategy.avg_return * 4.0)
        score += 0.10 * min(performance_score, 1.0)
        
        # Bonus/Penalty aggiuntivi
        
        # Bonus per basso rischio con capitale piccolo
        if capital_tier == CapitalTier.MICRO and strategy.risk_level < 0.3:
            score += 0.05
        
        # Bonus per alta efficienza con capitale grande
        if capital_tier == CapitalTier.LARGE and strategy.capital_efficiency > 0.85:
            score += 0.05
        
        # Penalty per troppe posizioni aperte
        if current_positions >= strategy.max_positions:
            score *= 0.3  # Forte penalty
        
        # Bonus per strategie AI-enhanced
        if "ai" in strategy.name.lower() or "consensus" in strategy.name.lower():
            score += 0.03
        
        return min(score, 1.0)  # Cap a 1.0
    
    def select_optimal_strategy(self, market_data: Dict, 
                              current_capital: float,
                              ai_confidence: float,
                              current_positions: int = 0) -> Tuple[StrategyOption, float]:
        """Seleziona la strategia ottimale basata su condizioni attuali"""
        
        # Analizza condizioni
        market_condition = self.analyze_market_condition(market_data)
        capital_tier = self.get_capital_tier(current_capital)
        
        print(f"🔍 ANALISI CONDIZIONI:")
        print(f"   Market: {market_condition.value}")
        print(f"   Capital Tier: {capital_tier.value}")
        print(f"   AI Confidence: {ai_confidence:.1%}")
        print(f"   Current Positions: {current_positions}")
        
        # Calcola score per ogni strategia
        strategy_scores = {}
        for name, strategy in self.strategies.items():
            score = self.calculate_strategy_score(
                strategy, market_condition, capital_tier, 
                ai_confidence, current_positions
            )
            strategy_scores[name] = score
        
        # Trova strategia con score più alto
        best_strategy_name = max(strategy_scores.keys(), 
                               key=lambda x: strategy_scores[x])
        best_strategy = self.strategies[best_strategy_name]
        best_score = strategy_scores[best_strategy_name]
        
        # Mostra top 3 strategie
        sorted_strategies = sorted(strategy_scores.items(), 
                                 key=lambda x: x[1], reverse=True)
        
        print(f"\\n🏆 TOP 3 STRATEGIE:")
        for i, (name, score) in enumerate(sorted_strategies[:3]):
            emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            print(f"   {emoji} {name}: {score:.3f}")
        
        return best_strategy, best_score
    
    def calculate_position_size(self, strategy: StrategyOption, 
                              current_capital: float,
                              ai_confidence: float) -> float:
        """Calcola dimensione posizione ottimale"""
        
        # Base position size dalla strategia
        base_size = current_capital * strategy.position_size_factor
        
        # Aggiustamenti dinamici
        
        # 1. Confidence adjustment
        confidence_multiplier = 0.5 + (ai_confidence * 1.5)  # 0.5x a 2.0x
        
        # 2. Capital tier adjustment
        capital_tier = self.get_capital_tier(current_capital)
        if capital_tier == CapitalTier.MICRO:
            capital_multiplier = 0.8  # Più conservativo
        elif capital_tier == CapitalTier.SMALL:
            capital_multiplier = 0.9
        elif capital_tier == CapitalTier.MEDIUM:
            capital_multiplier = 1.0
        else:  # LARGE
            capital_multiplier = 1.1  # Più aggressivo
        
        # 3. Risk adjustment
        risk_multiplier = 1.0 - (strategy.risk_level * 0.3)  # Riduce per alto rischio
        
        # Calcola size finale
        final_size = base_size * confidence_multiplier * capital_multiplier * risk_multiplier
        
        # Limiti di sicurezza
        min_size = current_capital * 0.02  # Minimo 2%
        max_size = current_capital * 0.50  # Massimo 50%
        
        final_size = max(min_size, min(final_size, max_size))
        
        return final_size
    
    def get_strategy_parameters(self, strategy: StrategyOption,
                              current_capital: float,
                              ai_confidence: float) -> Dict:
        """Ottieni parametri completi per la strategia selezionata"""
        
        position_size = self.calculate_position_size(strategy, current_capital, ai_confidence)
        
        # Aggiustamenti dinamici per stop loss e take profit
        confidence_factor = ai_confidence  # 0.6-1.0
        
        # Stop loss più stretto con alta confidence
        dynamic_stop_loss = strategy.stop_loss * (1.5 - confidence_factor)
        
        # Take profit più ambizioso con alta confidence  
        dynamic_take_profit = strategy.take_profit * (0.8 + confidence_factor * 0.4)
        
        parameters = {
            "strategy_name": strategy.name,
            "description": strategy.description,
            "position_size": position_size,
            "position_size_percent": (position_size / current_capital) * 100,
            "stop_loss": dynamic_stop_loss,
            "take_profit": dynamic_take_profit,
            "max_positions": strategy.max_positions,
            "holding_time": strategy.holding_time,
            "risk_level": strategy.risk_level,
            "expected_success_rate": strategy.success_rate,
            "expected_return": strategy.avg_return,
            "ai_confidence_used": ai_confidence,
            "capital_efficiency": strategy.capital_efficiency
        }
        
        return parameters
    
    def update_performance(self, strategy_name: str, 
                         trade_result: Dict):
        """Aggiorna performance storica delle strategie"""
        
        if strategy_name not in self.performance_history:
            self.performance_history[strategy_name] = {
                "trades": 0,
                "wins": 0,
                "total_return": 0.0,
                "avg_return": 0.0,
                "win_rate": 0.0
            }
        
        perf = self.performance_history[strategy_name]
        perf["trades"] += 1
        
        if trade_result.get("profit", 0) > 0:
            perf["wins"] += 1
        
        trade_return = trade_result.get("return_percent", 0)
        perf["total_return"] += trade_return
        perf["avg_return"] = perf["total_return"] / perf["trades"]
        perf["win_rate"] = perf["wins"] / perf["trades"]
        
        # Aggiorna strategia con nuove performance
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            # Media mobile delle performance
            alpha = 0.1  # Peso per nuovi dati
            strategy.success_rate = (1 - alpha) * strategy.success_rate + alpha * perf["win_rate"]
            strategy.avg_return = (1 - alpha) * strategy.avg_return + alpha * abs(perf["avg_return"])
    
    def get_strategy_network_status(self) -> Dict:
        """Ottieni status completo della rete strategica"""
        
        status = {
            "total_strategies": len(self.strategies),
            "strategies_by_risk": {
                "low": len([s for s in self.strategies.values() if s.risk_level < 0.3]),
                "medium": len([s for s in self.strategies.values() if 0.3 <= s.risk_level < 0.6]),
                "high": len([s for s in self.strategies.values() if s.risk_level >= 0.6])
            },
            "strategies_by_capital": {
                "micro": len([s for s in self.strategies.values() if CapitalTier.MICRO in s.capital_tiers]),
                "small": len([s for s in self.strategies.values() if CapitalTier.SMALL in s.capital_tiers]),
                "medium": len([s for s in self.strategies.values() if CapitalTier.MEDIUM in s.capital_tiers]),
                "large": len([s for s in self.strategies.values() if CapitalTier.LARGE in s.capital_tiers])
            },
            "avg_success_rate": sum(s.success_rate for s in self.strategies.values()) / len(self.strategies),
            "avg_return": sum(s.avg_return for s in self.strategies.values()) / len(self.strategies),
            "performance_history": self.performance_history
        }
        
        return status

def demo_strategy_network():
    """Demo della rete strategica"""
    
    print("🧠 AURUMBOTX STRATEGY NETWORK - DEMO")
    print("=" * 60)
    
    # Inizializza rete
    network = StrategyNetwork()
    
    # Simula dati di mercato
    market_scenarios = [
        {
            "name": "Bull Market Strong",
            "data": {
                "BTC": {"change_24h": 0.08},
                "ETH": {"change_24h": 0.12},
                "SOL": {"change_24h": 0.15}
            }
        },
        {
            "name": "Bear Market",
            "data": {
                "BTC": {"change_24h": -0.06},
                "ETH": {"change_24h": -0.08},
                "SOL": {"change_24h": -0.04}
            }
        },
        {
            "name": "Sideways Market",
            "data": {
                "BTC": {"change_24h": 0.01},
                "ETH": {"change_24h": -0.005},
                "SOL": {"change_24h": 0.015}
            }
        },
        {
            "name": "Volatile Market",
            "data": {
                "BTC": {"change_24h": 0.12},
                "ETH": {"change_24h": -0.09},
                "SOL": {"change_24h": 0.18}
            }
        }
    ]
    
    # Test con diversi capitali
    capital_scenarios = [150, 350, 750, 1500]
    ai_confidence = 0.78
    
    for capital in capital_scenarios:
        print(f"\\n💰 CAPITALE: €{capital}")
        print("-" * 40)
        
        for scenario in market_scenarios:
            print(f"\\n📊 SCENARIO: {scenario['name']}")
            
            strategy, score = network.select_optimal_strategy(
                scenario['data'], capital, ai_confidence
            )
            
            parameters = network.get_strategy_parameters(
                strategy, capital, ai_confidence
            )
            
            print(f"🎯 STRATEGIA SELEZIONATA: {strategy.name}")
            print(f"   Score: {score:.3f}")
            print(f"   Position Size: €{parameters['position_size']:.2f} ({parameters['position_size_percent']:.1f}%)")
            print(f"   Stop Loss: {parameters['stop_loss']:.1%}")
            print(f"   Take Profit: {parameters['take_profit']:.1%}")
            print(f"   Risk Level: {strategy.risk_level:.1%}")
            print(f"   Expected Win Rate: {strategy.success_rate:.1%}")
    
    # Status finale
    print(f"\\n📊 NETWORK STATUS:")
    status = network.get_strategy_network_status()
    print(f"   Total Strategies: {status['total_strategies']}")
    print(f"   Low Risk: {status['strategies_by_risk']['low']}")
    print(f"   Medium Risk: {status['strategies_by_risk']['medium']}")
    print(f"   High Risk: {status['strategies_by_risk']['high']}")
    print(f"   Avg Success Rate: {status['avg_success_rate']:.1%}")
    print(f"   Avg Return: {status['avg_return']:.1%}")

if __name__ == "__main__":
    demo_strategy_network()

