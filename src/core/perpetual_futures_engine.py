#!/usr/bin/env python3
"""
AurumBotX Perpetual Futures Engine
Motore specializzato per il trading di perpetual futures su Hyperliquid
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class PositionSide(Enum):
    """Lati della posizione"""
    LONG = "Long"
    SHORT = "Short"

class PositionStatus(Enum):
    """Stato della posizione"""
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"

@dataclass
class PerpetualPosition:
    """Struttura per una posizione perpetual futures"""
    position_id: str
    symbol: str
    side: str  # "Long" o "Short"
    entry_price: float
    current_price: float
    size: float
    leverage: float
    collateral: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    liquidation_price: float
    stop_loss_price: float
    take_profit_price: float
    status: str
    entry_time: datetime
    last_update: datetime
    funding_paid: float = 0.0
    trades_count: int = 0

@dataclass
class PerpetualTrade:
    """Struttura per un trade perpetual futures"""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    size: float
    leverage: float
    pnl: float
    pnl_percent: float
    fees: float
    funding_paid: float
    entry_time: datetime
    exit_time: datetime
    duration_minutes: int
    status: str

class PerpetualFuturesEngine:
    """Engine per il trading di perpetual futures"""
    
    def __init__(self, hyperliquid_adapter, leverage_manager):
        """
        Inizializza il Perpetual Futures Engine
        
        Args:
            hyperliquid_adapter: Adapter per Hyperliquid
            leverage_manager: Manager per il leverage
        """
        self.adapter = hyperliquid_adapter
        self.leverage_manager = leverage_manager
        
        self.positions: Dict[str, PerpetualPosition] = {}
        self.closed_trades: List[PerpetualTrade] = []
        self.position_counter = 0
        self.trade_counter = 0
        
        self.total_fees_paid = 0.0
        self.total_funding_paid = 0.0
        
        logger.info("PerpetualFuturesEngine inizializzato")
    
    def open_position(
        self,
        symbol: str,
        side: str,
        size: float,
        leverage: float,
        entry_price: float,
        stop_loss_percent: float = 2.0,
        take_profit_percent: float = 5.0,
        collateral: float = None
    ) -> Dict:
        """
        Apre una nuova posizione perpetual futures
        
        Args:
            symbol: Simbolo (es. "BTC")
            side: "Long" o "Short"
            size: Dimensione della posizione
            leverage: Leverage da applicare
            entry_price: Prezzo di entrata
            stop_loss_percent: Percentuale di stop loss
            take_profit_percent: Percentuale di take profit
            collateral: Collaterale (calcolato automaticamente se None)
        
        Returns:
            Dizionario con i dettagli della posizione aperta
        """
        
        # Valida il leverage
        if not self.leverage_manager.validate_leverage(leverage):
            return {"error": "Invalid leverage"}
        
        # Calcola il collaterale
        if collateral is None:
            collateral = (size * entry_price) / leverage
        
        # Calcola i prezzi di stop loss e take profit
        stop_loss_price = self.leverage_manager.calculate_stop_loss_price(
            entry_price, leverage, side, stop_loss_percent
        )
        take_profit_price = self.leverage_manager.calculate_take_profit_price(
            entry_price, leverage, side, take_profit_percent
        )
        
        # Calcola il prezzo di liquidazione
        liquidation_price = self.leverage_manager.calculate_liquidation_price(
            entry_price, leverage, side
        )
        
        # Crea la posizione
        self.position_counter += 1
        position_id = f"POS_{self.position_counter}"
        
        position = PerpetualPosition(
            position_id=position_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            current_price=entry_price,
            size=size,
            leverage=leverage,
            collateral=collateral,
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0,
            liquidation_price=liquidation_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            status=PositionStatus.OPEN.value,
            entry_time=datetime.now(),
            last_update=datetime.now()
        )
        
        self.positions[position_id] = position
        
        logger.info(
            f"Position Opened: {position_id} | {symbol} {side} {size} @ ${entry_price:.2f} "
            f"| Leverage: {leverage:.1f}x | SL: ${stop_loss_price:.2f} | TP: ${take_profit_price:.2f}"
        )
        
        return {
            "position_id": position_id,
            "symbol": symbol,
            "side": side,
            "size": size,
            "entry_price": entry_price,
            "leverage": leverage,
            "collateral": collateral,
            "liquidation_price": liquidation_price,
            "stop_loss_price": stop_loss_price,
            "take_profit_price": take_profit_price,
            "status": "opened"
        }
    
    def close_position(
        self,
        position_id: str,
        exit_price: float,
        reason: str = "Manual"
    ) -> Dict:
        """
        Chiude una posizione perpetual futures
        
        Args:
            position_id: ID della posizione da chiudere
            exit_price: Prezzo di uscita
            reason: Motivo della chiusura
        
        Returns:
            Dizionario con i dettagli del trade chiuso
        """
        
        if position_id not in self.positions:
            logger.error(f"Position not found: {position_id}")
            return {"error": "Position not found"}
        
        position = self.positions[position_id]
        
        # Calcola il P&L
        pnl, pnl_percent = self.leverage_manager.calculate_pnl_with_leverage(
            position.entry_price,
            exit_price,
            position.size,
            position.leverage,
            position.side
        )
        
        # Calcola le fee (0.05% taker fee)
        fees = (position.size * exit_price) * 0.0005
        self.total_fees_paid += fees
        
        # Calcola il funding pagato (simulato)
        funding_paid = (position.size * position.entry_price) * 0.0001
        self.total_funding_paid += funding_paid
        
        # Crea il trade chiuso
        self.trade_counter += 1
        trade_id = f"TRADE_{self.trade_counter}"
        
        entry_time = position.entry_time
        exit_time = datetime.now()
        duration_minutes = int((exit_time - entry_time).total_seconds() / 60)
        
        trade = PerpetualTrade(
            trade_id=trade_id,
            symbol=position.symbol,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            size=position.size,
            leverage=position.leverage,
            pnl=pnl - fees,  # P&L netto dopo fee
            pnl_percent=pnl_percent,
            fees=fees,
            funding_paid=funding_paid,
            entry_time=entry_time,
            exit_time=exit_time,
            duration_minutes=duration_minutes,
            status="closed"
        )
        
        self.closed_trades.append(trade)
        
        # Aggiorna lo stato della posizione
        position.status = PositionStatus.CLOSED.value
        position.current_price = exit_price
        position.last_update = datetime.now()
        
        logger.info(
            f"Position Closed: {position_id} | {position.symbol} {position.side} "
            f"| P&L: ${pnl:+.2f} ({pnl_percent:+.2f}%) | Reason: {reason}"
        )
        
        return {
            "trade_id": trade_id,
            "position_id": position_id,
            "symbol": position.symbol,
            "side": position.side,
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "size": position.size,
            "leverage": position.leverage,
            "pnl": pnl - fees,
            "pnl_percent": pnl_percent,
            "fees": fees,
            "funding_paid": funding_paid,
            "duration_minutes": duration_minutes,
            "reason": reason,
            "status": "closed"
        }
    
    def update_position_price(self, position_id: str, current_price: float):
        """
        Aggiorna il prezzo corrente di una posizione
        
        Args:
            position_id: ID della posizione
            current_price: Prezzo corrente
        """
        
        if position_id not in self.positions:
            logger.error(f"Position not found: {position_id}")
            return
        
        position = self.positions[position_id]
        position.current_price = current_price
        position.last_update = datetime.now()
        
        # Calcola il P&L non realizzato
        pnl, pnl_percent = self.leverage_manager.calculate_pnl_with_leverage(
            position.entry_price,
            current_price,
            position.size,
            position.leverage,
            position.side
        )
        
        position.unrealized_pnl = pnl
        position.unrealized_pnl_percent = pnl_percent
        
        # Controlla le condizioni di uscita
        self._check_exit_conditions(position_id)
    
    def _check_exit_conditions(self, position_id: str):
        """
        Controlla le condizioni di uscita (stop loss, take profit, liquidazione)
        
        Args:
            position_id: ID della posizione
        """
        
        if position_id not in self.positions:
            return
        
        position = self.positions[position_id]
        
        # Controlla liquidazione
        if position.side == "Long" and position.current_price <= position.liquidation_price:
            self.close_position(position_id, position.liquidation_price, "Liquidated")
            logger.warning(f"Position {position_id} LIQUIDATED!")
        
        elif position.side == "Short" and position.current_price >= position.liquidation_price:
            self.close_position(position_id, position.liquidation_price, "Liquidated")
            logger.warning(f"Position {position_id} LIQUIDATED!")
        
        # Controlla stop loss
        elif position.side == "Long" and position.current_price <= position.stop_loss_price:
            self.close_position(position_id, position.stop_loss_price, "Stop Loss")
        
        elif position.side == "Short" and position.current_price >= position.stop_loss_price:
            self.close_position(position_id, position.stop_loss_price, "Stop Loss")
        
        # Controlla take profit
        elif position.side == "Long" and position.current_price >= position.take_profit_price:
            self.close_position(position_id, position.take_profit_price, "Take Profit")
        
        elif position.side == "Short" and position.current_price <= position.take_profit_price:
            self.close_position(position_id, position.take_profit_price, "Take Profit")
    
    def get_open_positions(self) -> List[Dict]:
        """Ottiene tutte le posizioni aperte"""
        open_positions = []
        
        for pos_id, position in self.positions.items():
            if position.status == PositionStatus.OPEN.value:
                open_positions.append({
                    "position_id": pos_id,
                    "symbol": position.symbol,
                    "side": position.side,
                    "size": position.size,
                    "entry_price": position.entry_price,
                    "current_price": position.current_price,
                    "leverage": position.leverage,
                    "unrealized_pnl": position.unrealized_pnl,
                    "unrealized_pnl_percent": position.unrealized_pnl_percent,
                    "liquidation_price": position.liquidation_price,
                    "stop_loss_price": position.stop_loss_price,
                    "take_profit_price": position.take_profit_price
                })
        
        return open_positions
    
    def get_closed_trades(self) -> List[Dict]:
        """Ottiene tutti i trade chiusi"""
        return [asdict(trade) for trade in self.closed_trades]
    
    def get_performance_metrics(self) -> Dict:
        """Calcola le metriche di performance"""
        
        if not self.closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "total_fees": self.total_fees_paid,
                "total_funding": self.total_funding_paid,
                "sharpe_ratio": 0.0,
                "profit_factor": 0.0
            }
        
        total_trades = len(self.closed_trades)
        winning_trades = len([t for t in self.closed_trades if t.pnl > 0])
        losing_trades = total_trades - winning_trades
        
        total_pnl = sum(t.pnl for t in self.closed_trades)
        avg_pnl = total_pnl / total_trades
        
        # Sharpe Ratio
        pnl_values = [t.pnl for t in self.closed_trades]
        import numpy as np
        std_dev = np.std(pnl_values) if len(pnl_values) > 1 else 0
        sharpe_ratio = (np.mean(pnl_values) / std_dev) if std_dev > 0 else 0
        
        # Profit Factor
        gross_profit = sum(t.pnl for t in self.closed_trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.closed_trades if t.pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "total_fees": self.total_fees_paid,
            "total_funding": self.total_funding_paid,
            "sharpe_ratio": sharpe_ratio,
            "profit_factor": profit_factor
        }

def test_perpetual_futures_engine():
    """Test del Perpetual Futures Engine"""
    
    print("\n" + "="*100)
    print("PERPETUAL FUTURES ENGINE TEST")
    print("="*100)
    
    # Mock objects
    class MockAdapter:
        pass
    
    import sys
    sys.path.insert(0, '/home/ubuntu/AurumBotX')
    from src.core.leverage_manager import LeverageManager, LeverageConfig, RiskLevel
    
    # Crea il manager e l'engine
    config = LeverageConfig(risk_level=RiskLevel.MODERATE)
    leverage_manager = LeverageManager(config)
    adapter = MockAdapter()
    
    engine = PerpetualFuturesEngine(adapter, leverage_manager)
    
    # Test 1: Apri una posizione Long
    print("\n1. Opening Long Position:")
    result = engine.open_position(
        symbol="BTC",
        side="Long",
        size=0.1,
        leverage=2.0,
        entry_price=50000,
        stop_loss_percent=2.0,
        take_profit_percent=5.0
    )
    position_id = result.get("position_id")
    print(f"   Position ID: {position_id}")
    print(f"   Entry Price: ${result['entry_price']:.2f}")
    print(f"   Liquidation Price: ${result['liquidation_price']:.2f}")
    
    # Test 2: Aggiorna il prezzo
    print("\n2. Updating Position Price:")
    engine.update_position_price(position_id, 51000)
    position = engine.positions[position_id]
    print(f"   Current Price: ${position.current_price:.2f}")
    print(f"   Unrealized P&L: ${position.unrealized_pnl:+.2f} ({position.unrealized_pnl_percent:+.2f}%)")
    
    # Test 3: Chiudi la posizione
    print("\n3. Closing Position:")
    close_result = engine.close_position(position_id, 52000, "Take Profit")
    print(f"   Trade ID: {close_result['trade_id']}")
    print(f"   P&L: ${close_result['pnl']:+.2f} ({close_result['pnl_percent']:+.2f}%)")
    print(f"   Fees: ${close_result['fees']:.2f}")
    
    # Test 4: Performance Metrics
    print("\n4. Performance Metrics:")
    metrics = engine.get_performance_metrics()
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Winning Trades: {metrics['winning_trades']}")
    print(f"   Win Rate: {metrics['win_rate']:.1f}%")
    print(f"   Total P&L: ${metrics['total_pnl']:+.2f}")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    
    print("\n" + "="*100)
    print("PERPETUAL FUTURES ENGINE TEST COMPLETED")
    print("="*100 + "\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_perpetual_futures_engine()

