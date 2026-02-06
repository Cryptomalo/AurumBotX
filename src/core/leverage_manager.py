#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Leverage Manager
Gestione intelligente del leverage per perpetual futures trading su Hyperliquid
"""

import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Livelli di rischio"""
    CONSERVATIVE = 1.0
    MODERATE = 2.0
    AGGRESSIVE = 3.0
    VERY_AGGRESSIVE = 5.0

@dataclass
class LeverageConfig:
    """Configurazione del leverage"""
    min_leverage: float = 1.0
    max_leverage: float = 20.0
    default_leverage: float = 2.0
    risk_level: RiskLevel = RiskLevel.MODERATE
    max_position_size_percent: float = 15.0
    max_account_risk_percent: float = 5.0

class LeverageManager:
    """Gestione intelligente del leverage per perpetual futures"""
    
    def __init__(self, config: LeverageConfig = None):
        """
        Inizializza il Leverage Manager
        
        Args:
            config: Configurazione del leverage
        """
        self.config = config or LeverageConfig()
        self.leverage_history: Dict[str, list] = {}
        self.risk_metrics: Dict[str, float] = {}
        
        logger.info(f"LeverageManager inizializzato - Risk Level: {self.config.risk_level.name}")
    
    def calculate_optimal_leverage(
        self,
        account_value: float,
        position_size: float,
        volatility: float,
        win_rate: float,
        confidence: float
    ) -> float:
        """
        Calcola il leverage ottimale basato su molteplici fattori
        
        Args:
            account_value: Valore totale dell'account
            position_size: Dimensione della posizione
            volatility: Volatilità del mercato (0-1)
            win_rate: Tasso di vincita (0-1)
            confidence: Confidenza del segnale AI (0-1)
        
        Returns:
            Leverage ottimale
        """
        
        # Base leverage dal risk level
        base_leverage = self.config.risk_level.value
        
        # Aggiustamento per volatilità (volatilità alta = leverage basso)
        volatility_adjustment = 1.0 - (volatility * 0.5)
        
        # Aggiustamento per win rate (win rate alta = leverage più alto)
        win_rate_adjustment = 0.8 + (win_rate * 0.4)
        
        # Aggiustamento per confidenza AI
        confidence_adjustment = 0.7 + (confidence * 0.3)
        
        # Calcola il leverage
        optimal_leverage = base_leverage * volatility_adjustment * win_rate_adjustment * confidence_adjustment
        
        # Applica i limiti
        optimal_leverage = max(self.config.min_leverage, min(optimal_leverage, self.config.max_leverage))
        
        logger.info(
            f"Optimal Leverage: {optimal_leverage:.2f}x "
            f"(Base: {base_leverage:.1f}x, Vol: {volatility_adjustment:.2f}, WR: {win_rate_adjustment:.2f}, Conf: {confidence_adjustment:.2f})"
        )
        
        return optimal_leverage
    
    def calculate_position_size_with_leverage(
        self,
        account_value: float,
        leverage: float,
        position_size_percent: float = None
    ) -> float:
        """
        Calcola la dimensione della posizione con leverage
        
        Args:
            account_value: Valore totale dell'account
            leverage: Leverage da applicare
            position_size_percent: Percentuale della posizione (default: config)
        
        Returns:
            Dimensione della posizione
        """
        
        position_size_percent = position_size_percent or self.config.max_position_size_percent
        
        # Posizione base
        base_position = account_value * (position_size_percent / 100)
        
        # Con leverage
        leveraged_position = base_position * leverage
        
        logger.info(
            f"Position Size: ${leveraged_position:.2f} "
            f"(Account: ${account_value:.2f}, Leverage: {leverage:.1f}x, %: {position_size_percent}%)"
        )
        
        return leveraged_position
    
    def calculate_liquidation_price(
        self,
        entry_price: float,
        leverage: float,
        side: str,
        maintenance_margin: float = 0.05
    ) -> float:
        """
        Calcola il prezzo di liquidazione
        
        Args:
            entry_price: Prezzo di entrata
            leverage: Leverage utilizzato
            side: "Long" o "Short"
            maintenance_margin: Margine di mantenimento (default: 5%)
        
        Returns:
            Prezzo di liquidazione
        """
        
        # Margine iniziale
        initial_margin = 1.0 / leverage
        
        # Prezzo di liquidazione
        if side == "Long":
            liquidation_price = entry_price * (1 - (initial_margin - maintenance_margin))
        else:  # Short
            liquidation_price = entry_price * (1 + (initial_margin - maintenance_margin))
        
        logger.info(
            f"Liquidation Price: ${liquidation_price:.2f} "
            f"(Entry: ${entry_price:.2f}, Leverage: {leverage:.1f}x, Side: {side})"
        )
        
        return liquidation_price
    
    def calculate_stop_loss_price(
        self,
        entry_price: float,
        leverage: float,
        side: str,
        stop_loss_percent: float = 2.0
    ) -> float:
        """
        Calcola il prezzo di stop loss
        
        Args:
            entry_price: Prezzo di entrata
            leverage: Leverage utilizzato
            side: "Long" o "Short"
            stop_loss_percent: Percentuale di stop loss
        
        Returns:
            Prezzo di stop loss
        """
        
        if side == "Long":
            stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
        else:  # Short
            stop_loss_price = entry_price * (1 + stop_loss_percent / 100)
        
        logger.info(
            f"Stop Loss Price: ${stop_loss_price:.2f} "
            f"(Entry: ${entry_price:.2f}, SL%: {stop_loss_percent}%, Side: {side})"
        )
        
        return stop_loss_price
    
    def calculate_take_profit_price(
        self,
        entry_price: float,
        leverage: float,
        side: str,
        take_profit_percent: float = 5.0
    ) -> float:
        """
        Calcola il prezzo di take profit
        
        Args:
            entry_price: Prezzo di entrata
            leverage: Leverage utilizzato
            side: "Long" o "Short"
            take_profit_percent: Percentuale di take profit
        
        Returns:
            Prezzo di take profit
        """
        
        if side == "Long":
            take_profit_price = entry_price * (1 + take_profit_percent / 100)
        else:  # Short
            take_profit_price = entry_price * (1 - take_profit_percent / 100)
        
        logger.info(
            f"Take Profit Price: ${take_profit_price:.2f} "
            f"(Entry: ${entry_price:.2f}, TP%: {take_profit_percent}%, Side: {side})"
        )
        
        return take_profit_price
    
    def calculate_max_risk_per_trade(
        self,
        account_value: float,
        max_risk_percent: float = None
    ) -> float:
        """
        Calcola il rischio massimo per trade
        
        Args:
            account_value: Valore totale dell'account
            max_risk_percent: Percentuale di rischio massimo
        
        Returns:
            Rischio massimo in USDT
        """
        
        max_risk_percent = max_risk_percent or self.config.max_account_risk_percent
        max_risk = account_value * (max_risk_percent / 100)
        
        logger.info(f"Max Risk Per Trade: ${max_risk:.2f} ({max_risk_percent}% of ${account_value:.2f})")
        
        return max_risk
    
    def validate_leverage(self, leverage: float) -> bool:
        """
        Valida il leverage
        
        Args:
            leverage: Leverage da validare
        
        Returns:
            True se valido, False altrimenti
        """
        
        is_valid = self.config.min_leverage <= leverage <= self.config.max_leverage
        
        if not is_valid:
            logger.warning(
                f"Invalid leverage: {leverage}. Must be between {self.config.min_leverage} and {self.config.max_leverage}"
            )
        
        return is_valid
    
    def calculate_pnl_with_leverage(
        self,
        entry_price: float,
        exit_price: float,
        position_size: float,
        leverage: float,
        side: str
    ) -> Tuple[float, float]:
        """
        Calcola il P&L con leverage
        
        Args:
            entry_price: Prezzo di entrata
            exit_price: Prezzo di uscita
            position_size: Dimensione della posizione
            leverage: Leverage utilizzato
            side: "Long" o "Short"
        
        Returns:
            Tupla (pnl_assoluto, pnl_percentuale)
        """
        
        if side == "Long":
            price_diff = exit_price - entry_price
        else:  # Short
            price_diff = entry_price - exit_price
        
        pnl_percent = (price_diff / entry_price) * 100
        pnl_absolute = (pnl_percent / 100) * position_size * leverage
        
        logger.info(
            f"P&L Calculation: ${pnl_absolute:+.2f} ({pnl_percent:+.2f}%) "
            f"(Entry: ${entry_price:.2f}, Exit: ${exit_price:.2f}, Size: {position_size:.4f}, Leverage: {leverage:.1f}x)"
        )
        
        return pnl_absolute, pnl_percent
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Ottiene le metriche di rischio"""
        return {
            "min_leverage": self.config.min_leverage,
            "max_leverage": self.config.max_leverage,
            "default_leverage": self.config.default_leverage,
            "max_position_size_percent": self.config.max_position_size_percent,
            "max_account_risk_percent": self.config.max_account_risk_percent,
            "risk_level": self.config.risk_level.name
        }
    
    def adjust_leverage_for_volatility(
        self,
        current_leverage: float,
        volatility: float
    ) -> float:
        """
        Aggiusta il leverage in base alla volatilità del mercato
        
        Args:
            current_leverage: Leverage attuale
            volatility: Volatilità del mercato (0-1)
        
        Returns:
            Leverage aggiustato
        """
        
        # Volatilità alta = ridurre leverage
        adjustment_factor = 1.0 - (volatility * 0.3)
        adjusted_leverage = current_leverage * adjustment_factor
        
        # Applica i limiti
        adjusted_leverage = max(self.config.min_leverage, min(adjusted_leverage, self.config.max_leverage))
        
        logger.info(f"Leverage adjusted from {current_leverage:.2f}x to {adjusted_leverage:.2f}x (Volatility: {volatility:.2f})")
        
        return adjusted_leverage

def test_leverage_manager():
    """Test del Leverage Manager"""
    
    print("\n" + "="*100)
    print("LEVERAGE MANAGER TEST")
    print("="*100)
    
    # Crea il manager con configurazione moderata
    config = LeverageConfig(
        risk_level=RiskLevel.MODERATE,
        max_leverage=20.0,
        default_leverage=2.0
    )
    manager = LeverageManager(config)
    
    # Test 1: Calcolo leverage ottimale
    print("\n1. Optimal Leverage Calculation:")
    optimal_leverage = manager.calculate_optimal_leverage(
        account_value=10000,
        position_size=1500,
        volatility=0.3,
        win_rate=0.65,
        confidence=0.75
    )
    print(f"   Optimal Leverage: {optimal_leverage:.2f}x")
    
    # Test 2: Calcolo dimensione posizione con leverage
    print("\n2. Position Size with Leverage:")
    position_size = manager.calculate_position_size_with_leverage(
        account_value=10000,
        leverage=2.0,
        position_size_percent=15
    )
    print(f"   Position Size: ${position_size:.2f}")
    
    # Test 3: Prezzo di liquidazione
    print("\n3. Liquidation Price (Long):")
    liq_price = manager.calculate_liquidation_price(
        entry_price=50000,
        leverage=2.0,
        side="Long"
    )
    print(f"   Liquidation Price: ${liq_price:.2f}")
    
    # Test 4: Stop Loss
    print("\n4. Stop Loss Price (Long):")
    sl_price = manager.calculate_stop_loss_price(
        entry_price=50000,
        leverage=2.0,
        side="Long",
        stop_loss_percent=2.0
    )
    print(f"   Stop Loss Price: ${sl_price:.2f}")
    
    # Test 5: Take Profit
    print("\n5. Take Profit Price (Long):")
    tp_price = manager.calculate_take_profit_price(
        entry_price=50000,
        leverage=2.0,
        side="Long",
        take_profit_percent=5.0
    )
    print(f"   Take Profit Price: ${tp_price:.2f}")
    
    # Test 6: Max Risk Per Trade
    print("\n6. Max Risk Per Trade:")
    max_risk = manager.calculate_max_risk_per_trade(
        account_value=10000,
        max_risk_percent=5.0
    )
    print(f"   Max Risk: ${max_risk:.2f}")
    
    # Test 7: P&L with Leverage
    print("\n7. P&L Calculation (Long, Profitable):")
    pnl, pnl_percent = manager.calculate_pnl_with_leverage(
        entry_price=50000,
        exit_price=52000,
        position_size=1500,
        leverage=2.0,
        side="Long"
    )
    print(f"   P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)")
    
    # Test 8: Volatility Adjustment
    print("\n8. Leverage Adjustment for Volatility:")
    adjusted = manager.adjust_leverage_for_volatility(2.0, 0.5)
    print(f"   Adjusted Leverage: {adjusted:.2f}x")
    
    # Test 9: Risk Metrics
    print("\n9. Risk Metrics:")
    metrics = manager.get_risk_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*100)
    print("LEVERAGE MANAGER TEST COMPLETED")
    print("="*100 + "\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_leverage_manager()

