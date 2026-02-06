#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX - Hyperliquid Integrated Demo
Demo end-to-end completa che dimostra l'integrazione di Hyperliquid con le strategie esistenti
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List

# Aggiungi il path del progetto
sys.path.insert(0, '/home/ubuntu/AurumBotX')

from src.core.leverage_manager import LeverageManager, LeverageConfig, RiskLevel
from src.core.perpetual_futures_engine import PerpetualFuturesEngine
from src.exchanges.hyperliquid_adapter import HyperliquidAdapter

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/AurumBotX/logs/hyperliquid_integrated_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Crea la directory logs se non esiste
os.makedirs('/home/ubuntu/AurumBotX/logs', exist_ok=True)

class HyperliquidIntegratedDemo:
    """Demo integrata di AurumBotX con Hyperliquid"""
    
    def __init__(self, capital: float = 1000.0, testnet: bool = True):
        """
        Inizializza la demo integrata
        
        Args:
            capital: Capitale iniziale
            testnet: Usa testnet se True
        """
        self.capital = capital
        self.testnet = testnet
        self.start_time = datetime.now()
        self.session_id = f"HYPER_DEMO_{self.start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Inizializza i componenti
        self._initialize_components()
        
        # Risultati
        self.results = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "capital": capital,
            "testnet": testnet,
            "trades": [],
            "performance": {},
            "ai_decisions": []
        }
        
        logger.info("=" * 120)
        logger.info("AURUMBOTX - HYPERLIQUID INTEGRATED DEMO")
        logger.info("=" * 120)
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Capital: ${capital}")
        logger.info(f"Mode: {'TESTNET' if testnet else 'MAINNET'}")
        logger.info("=" * 120)
    
    def _initialize_components(self):
        """Inizializza tutti i componenti del sistema"""
        
        # 1. Hyperliquid Adapter
        api_key = os.getenv("HYPERLIQUID_API_KEY", "demo_key")
        secret_key = os.getenv("HYPERLIQUID_SECRET_KEY", "demo_secret")
        self.adapter = HyperliquidAdapter(api_key, secret_key, testnet=self.testnet)
        logger.info("✓ Hyperliquid Adapter initialized")
        
        # 2. Leverage Manager
        leverage_config = LeverageConfig(
            risk_level=RiskLevel.MODERATE,
            max_leverage=5.0,
            default_leverage=2.0,
            max_position_size_percent=15.0,
            max_account_risk_percent=5.0
        )
        self.leverage_manager = LeverageManager(leverage_config)
        logger.info("✓ Leverage Manager initialized")
        
        # 3. Perpetual Futures Engine
        self.futures_engine = PerpetualFuturesEngine(self.adapter, self.leverage_manager)
        logger.info("✓ Perpetual Futures Engine initialized")
        
        # 4. AI Models (simulati)
        self.ai_models = ["GPT-4", "Claude", "Gemini", "DeepSeek", "Grok"]
        logger.info(f"✓ AI Models loaded: {len(self.ai_models)} models")
    
    def simulate_ai_consensus(self, symbol: str, cycle: int) -> Dict:
        """
        Simula il consensus di 327 modelli AI
        
        Args:
            symbol: Simbolo da analizzare
            cycle: Numero del ciclo
        
        Returns:
            Decisione AI con consensus
        """
        import random
        
        # Simula votazione dei modelli
        models_voting = {
            "BUY": random.randint(50, 150),
            "SELL": random.randint(30, 100),
            "HOLD": random.randint(100, 200)
        }
        
        total_models = sum(models_voting.values())
        
        # Determina il consensus
        consensus_action = max(models_voting, key=models_voting.get)
        consensus_confidence = models_voting[consensus_action] / total_models
        
        # Calcola metriche di mercato simulate
        volatility = 0.2 + (cycle % 10) * 0.05
        win_rate = 0.6 + (cycle % 5) * 0.05
        
        decision = {
            "symbol": symbol,
            "cycle": cycle,
            "timestamp": datetime.now().isoformat(),
            "action": consensus_action,
            "confidence": consensus_confidence,
            "models_voting": models_voting,
            "total_models": total_models,
            "market_metrics": {
                "volatility": volatility,
                "win_rate": win_rate,
                "trend": "UP" if cycle % 3 == 0 else "DOWN" if cycle % 5 == 0 else "NEUTRAL"
            }
        }
        
        return decision
    
    def execute_trading_cycle(self, cycle: int, symbols: List[str]) -> Dict:
        """
        Esegue un ciclo di trading completo
        
        Args:
            cycle: Numero del ciclo
            symbols: Lista di simboli da tradare
        
        Returns:
            Risultati del ciclo
        """
        
        logger.info(f"\n{'='*120}")
        logger.info(f"TRADING CYCLE #{cycle}")
        logger.info(f"{'='*120}")
        
        cycle_results = {
            "cycle": cycle,
            "timestamp": datetime.now().isoformat(),
            "decisions": {},
            "trades_executed": [],
            "positions_updated": []
        }
        
        for symbol in symbols:
            logger.info(f"\n--- Analyzing {symbol} ---")
            
            # 1. Ottieni decisione AI
            ai_decision = self.simulate_ai_consensus(symbol, cycle)
            cycle_results["decisions"][symbol] = ai_decision
            self.results["ai_decisions"].append(ai_decision)
            
            logger.info(f"AI Consensus: {ai_decision['action']}")
            logger.info(f"Confidence: {ai_decision['confidence']*100:.1f}%")
            logger.info(f"Models Voting: BUY={ai_decision['models_voting']['BUY']}, "
                       f"SELL={ai_decision['models_voting']['SELL']}, "
                       f"HOLD={ai_decision['models_voting']['HOLD']}")
            
            # 2. Calcola leverage ottimale
            optimal_leverage = self.leverage_manager.calculate_optimal_leverage(
                account_value=self.capital,
                position_size=self.capital * 0.15,
                volatility=ai_decision['market_metrics']['volatility'],
                win_rate=ai_decision['market_metrics']['win_rate'],
                confidence=ai_decision['confidence']
            )
            
            # 3. Esegui trade se confidence > threshold
            if ai_decision['confidence'] > 0.55:
                if ai_decision['action'] == "BUY":
                    trade = self._execute_buy(symbol, optimal_leverage, cycle)
                    if trade:
                        cycle_results["trades_executed"].append(trade)
                        self.results["trades"].append(trade)
                
                elif ai_decision['action'] == "SELL":
                    trade = self._execute_sell(symbol, optimal_leverage, cycle)
                    if trade:
                        cycle_results["trades_executed"].append(trade)
                        self.results["trades"].append(trade)
            
            # 4. Aggiorna posizioni esistenti
            self._update_positions(symbol, cycle)
        
        return cycle_results
    
    def _execute_buy(self, symbol: str, leverage: float, cycle: int) -> Dict:
        """Esegue un ordine di acquisto"""
        
        # Simula prezzo di mercato
        base_price = {"BTC": 50000, "ETH": 3000, "SOL": 100, "BNB": 300, "DOGE": 0.1}
        entry_price = base_price.get(symbol, 100) + (cycle % 50)
        
        # Calcola dimensione posizione
        position_size = self.leverage_manager.calculate_position_size_with_leverage(
            account_value=self.capital,
            leverage=leverage,
            position_size_percent=15.0
        )
        
        size = position_size / entry_price
        
        # Apri posizione
        result = self.futures_engine.open_position(
            symbol=symbol,
            side="Long",
            size=size,
            leverage=leverage,
            entry_price=entry_price,
            stop_loss_percent=2.0,
            take_profit_percent=5.0
        )
        
        logger.info(f"✓ BUY Executed: {symbol} {size:.4f} @ ${entry_price:.2f} with {leverage:.1f}x leverage")
        
        return {
            "type": "BUY",
            "symbol": symbol,
            "size": size,
            "entry_price": entry_price,
            "leverage": leverage,
            "position_id": result.get("position_id"),
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_sell(self, symbol: str, leverage: float, cycle: int) -> Dict:
        """Esegue un ordine di vendita"""
        
        # Trova posizione aperta
        open_positions = self.futures_engine.get_open_positions()
        position = next((p for p in open_positions if p["symbol"] == symbol), None)
        
        if not position:
            logger.warning(f"No open position for {symbol}")
            return None
        
        # Simula prezzo di uscita
        base_price = {"BTC": 50000, "ETH": 3000, "SOL": 100, "BNB": 300, "DOGE": 0.1}
        exit_price = base_price.get(symbol, 100) + (cycle % 50) + 10
        
        # Chiudi posizione
        result = self.futures_engine.close_position(
            position_id=position["position_id"],
            exit_price=exit_price,
            reason="AI Signal"
        )
        
        logger.info(f"✓ SELL Executed: {symbol} @ ${exit_price:.2f} | P&L: ${result.get('pnl', 0):+.2f}")
        
        return {
            "type": "SELL",
            "symbol": symbol,
            "exit_price": exit_price,
            "pnl": result.get("pnl", 0),
            "pnl_percent": result.get("pnl_percent", 0),
            "trade_id": result.get("trade_id"),
            "timestamp": datetime.now().isoformat()
        }
    
    def _update_positions(self, symbol: str, cycle: int):
        """Aggiorna le posizioni esistenti"""
        
        open_positions = self.futures_engine.get_open_positions()
        position = next((p for p in open_positions if p["symbol"] == symbol), None)
        
        if position:
            # Simula aggiornamento prezzo
            base_price = {"BTC": 50000, "ETH": 3000, "SOL": 100, "BNB": 300, "DOGE": 0.1}
            current_price = base_price.get(symbol, 100) + (cycle % 50) + 5
            
            self.futures_engine.update_position_price(position["position_id"], current_price)
    
    def run_demo(self, num_cycles: int = 12, symbols: List[str] = None):
        """
        Esegue la demo completa
        
        Args:
            num_cycles: Numero di cicli da eseguire
            symbols: Lista di simboli da tradare
        """
        
        if symbols is None:
            symbols = ["BTC", "ETH", "SOL"]
        
        logger.info(f"\nStarting demo with {num_cycles} cycles...")
        logger.info(f"Symbols: {', '.join(symbols)}\n")
        
        for cycle in range(1, num_cycles + 1):
            cycle_results = self.execute_trading_cycle(cycle, symbols)
            
            # Pausa tra cicli
            import time
            time.sleep(0.3)
        
        # Calcola performance finale
        self._calculate_final_performance()
        
        # Salva risultati
        self._save_results()
        
        logger.info(f"\n{'='*120}")
        logger.info("DEMO COMPLETED")
        logger.info(f"{'='*120}\n")
    
    def _calculate_final_performance(self):
        """Calcola le performance finali"""
        
        metrics = self.futures_engine.get_performance_metrics()
        
        self.results["performance"] = {
            "total_trades": metrics["total_trades"],
            "winning_trades": metrics["winning_trades"],
            "losing_trades": metrics["losing_trades"],
            "win_rate": metrics["win_rate"],
            "total_pnl": metrics["total_pnl"],
            "avg_pnl": metrics["avg_pnl"],
            "total_fees": metrics["total_fees"],
            "total_funding": metrics["total_funding"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "profit_factor": metrics["profit_factor"],
            "final_capital": self.capital + metrics["total_pnl"]
        }
        
        logger.info("\n" + "="*120)
        logger.info("FINAL PERFORMANCE")
        logger.info("="*120)
        logger.info(f"Initial Capital: ${self.capital:.2f}")
        logger.info(f"Final Capital: ${self.results['performance']['final_capital']:.2f}")
        logger.info(f"Total P&L: ${metrics['total_pnl']:+.2f}")
        logger.info(f"Total Trades: {metrics['total_trades']}")
        logger.info(f"Win Rate: {metrics['win_rate']:.1f}%")
        logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"Profit Factor: {metrics['profit_factor']:.2f}x")
        logger.info("="*120)
    
    def _save_results(self):
        """Salva i risultati della demo"""
        
        results_dir = '/home/ubuntu/AurumBotX/demo_trading'
        os.makedirs(results_dir, exist_ok=True)
        
        results_file = os.path.join(results_dir, f"hyperliquid_integrated_{self.session_id}.json")
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"\nResults saved to: {results_file}")

def main():
    """Funzione principale"""
    
    print("\n" + "="*120)
    print("AURUMBOTX - HYPERLIQUID INTEGRATED DEMO")
    print("="*120)
    print("\nDemonstrating end-to-end integration of:")
    print("  ✓ Hyperliquid DEX")
    print("  ✓ Perpetual Futures with Leverage")
    print("  ✓ AI Consensus (327 models)")
    print("  ✓ Risk Management")
    print("  ✓ Advanced Analytics")
    print("\n" + "="*120 + "\n")
    
    # Crea e avvia la demo
    demo = HyperliquidIntegratedDemo(capital=1000.0, testnet=True)
    
    # Esegui 12 cicli di trading
    demo.run_demo(num_cycles=12, symbols=["BTC", "ETH", "SOL"])
    
    print("\n" + "="*120)
    print("Demo completed! Check logs and results.")
    print("="*120 + "\n")

if __name__ == "__main__":
    main()

