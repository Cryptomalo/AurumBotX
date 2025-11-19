#!/usr/bin/env python3
"""
AurumBotX - Chameleon Strategy
Strategia adattiva per crescita esponenziale del capitale
"""

import json
import time
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

class ChameleonLevel(Enum):
    """Livelli strategia Chameleon"""
    TURTLE = 1    # Protezione capitale
    RABBIT = 2    # Crescita moderata
    EAGLE = 3     # Crescita aggressiva
    CHEETAH = 4   # Scalping veloce
    ROCKET = 5    # Esponenziale

@dataclass
class LevelConfig:
    """Configurazione per ogni livello"""
    name: str
    position_size_min: float  # Percentuale capitale
    position_size_max: float
    stop_loss: float
    take_profit: float
    confidence_threshold: float
    pairs_count: int
    timeframe: str
    description: str

class ChameleonStrategy:
    """
    Strategia Chameleon Adattiva
    Si adatta dinamicamente alle condizioni di mercato
    """
    
    # Configurazioni livelli (HIGH-PROFIT OPTIMIZED)
    LEVEL_CONFIGS = {
        ChameleonLevel.TURTLE: LevelConfig(
            name="TURTLE",
            position_size_min=0.03,  # 3% (optimized for profit)
            position_size_max=0.05,  # 5%
            stop_loss=0.02,          # 2% (allows volatility)
            take_profit=0.08,        # 8% (high profit target)
            confidence_threshold=0.65,  # 65% (balanced)
            pairs_count=5,           # More pairs
            timeframe="1h-4h",
            description="🐢 High-Profit Conservative"
        ),
        ChameleonLevel.RABBIT: LevelConfig(
            name="RABBIT",
            position_size_min=0.05,  # 5%
            position_size_max=0.08,  # 8%
            stop_loss=0.025,         # 2.5%
            take_profit=0.10,        # 10%
            confidence_threshold=0.60,  # 60%
            pairs_count=7,
            timeframe="2h-6h",
            description="🐇 High-Profit Moderate"
        ),
        ChameleonLevel.EAGLE: LevelConfig(
            name="EAGLE",
            position_size_min=0.08,  # 8%
            position_size_max=0.12,  # 12%
            stop_loss=0.03,          # 3%
            take_profit=0.12,        # 12%
            confidence_threshold=0.55,  # 55%
            pairs_count=10,
            timeframe="4h-12h",
            description="🦅 High-Profit Aggressive"
        ),
        ChameleonLevel.CHEETAH: LevelConfig(
            name="CHEETAH",
            position_size_min=0.12,  # 12%
            position_size_max=0.18,  # 18%
            stop_loss=0.04,          # 4%
            take_profit=0.15,        # 15%
            confidence_threshold=0.50,  # 50%
            pairs_count=12,
            timeframe="6h-24h",
            description="🐆 High-Profit Swing"
        ),
        ChameleonLevel.ROCKET: LevelConfig(
            name="ROCKET",
            position_size_min=0.18,  # 18%
            position_size_max=0.25,  # 25%
            stop_loss=0.05,          # 5%
            take_profit=0.20,        # 20%
            confidence_threshold=0.45,  # 45%
            pairs_count=15,
            timeframe="12h-48h",
            description="🚀 High-Profit Exponential"
        )
    }
    
    def __init__(self, initial_capital: float, initial_level: ChameleonLevel = ChameleonLevel.TURTLE):
        """
        Inizializza strategia Chameleon
        
        Args:
            initial_capital: Capitale iniziale
            initial_level: Livello iniziale
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.current_level = initial_level
        self.trades_history = []
        self.level_history = [(datetime.now(), initial_level)]
        
        # Statistiche
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.max_consecutive_wins = 0
        self.max_consecutive_losses = 0
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        # Setup logging
        self.logger = logging.getLogger("ChameleonStrategy")
        
        self.logger.info(f"🦎 Chameleon Strategy inizializzata")
        self.logger.info(f"   Capitale: ${initial_capital:.2f}")
        self.logger.info(f"   Livello: {self.get_current_config().description}")
    
    def get_current_config(self) -> LevelConfig:
        """Ottieni configurazione livello corrente"""
        return self.LEVEL_CONFIGS[self.current_level]
    
    def calculate_position_size(self, confidence: float, trend_strength: float = 1.0, expected_profit: float = 0.08) -> float:
        """
        Calcola position size dinamico
        
        Args:
            confidence: Confidence AI (0-1)
            trend_strength: Forza trend (0.8-1.3)
        
        Returns:
            Position size in USD
        """
        config = self.get_current_config()
        
        # Base position size (percentuale capitale)
        base_percentage = (config.position_size_min + config.position_size_max) / 2
        
        # Confidence multiplier (0.8-1.2)
        confidence_multiplier = 0.8 + (confidence * 0.4)
        
        # Trend multiplier (già fornito 0.8-1.3)
        trend_multiplier = max(0.8, min(1.3, trend_strength))
        
        # Fee-aware multiplier (NEW: High-Profit Optimization)
        fee_percentage = 0.001  # 0.10% round-trip
        profit_fee_ratio = expected_profit / fee_percentage
        
        if profit_fee_ratio > 100:  # Profit > 10%
            fee_multiplier = 1.3
        elif profit_fee_ratio > 80:  # Profit > 8%
            fee_multiplier = 1.2
        elif profit_fee_ratio > 50:  # Profit > 5%
            fee_multiplier = 1.1
        else:
            fee_multiplier = 1.0
        
        # Calcola position size (con fee multiplier)
        position_size = self.current_capital * base_percentage * confidence_multiplier * trend_multiplier * fee_multiplier
        
        # Limiti assoluti (HIGH-PROFIT: max 25%)
        max_position = self.current_capital * 0.25  # Max 25% capitale
        min_position = 1.00  # Min $1.00
        
        final_position = max(min_position, min(max_position, position_size))
        
        self.logger.debug(f"Position size: ${final_position:.2f} "
                         f"(base: {base_percentage:.1%}, conf: {confidence_multiplier:.2f}, "
                         f"trend: {trend_multiplier:.2f})")
        
        return final_position
    
    def calculate_stop_loss(self, entry_price: float, volatility: float = 0.02) -> float:
        """
        Calcola stop loss dinamico
        
        Args:
            entry_price: Prezzo entrata
            volatility: Volatilità corrente (default 2%)
        
        Returns:
            Prezzo stop loss
        """
        config = self.get_current_config()
        
        # Base stop loss
        base_sl = config.stop_loss
        
        # Aggiustamento volatilità (max +2%)
        volatility_adjustment = min(volatility * 0.5, 0.02)
        
        # Stop loss finale (min 0.5%, max 4%)
        final_sl_percentage = max(0.005, min(0.04, base_sl + volatility_adjustment))
        
        stop_loss_price = entry_price * (1 - final_sl_percentage)
        
        self.logger.debug(f"Stop loss: {final_sl_percentage:.2%} @ ${stop_loss_price:.4f}")
        
        return stop_loss_price
    
    def calculate_take_profit(self, entry_price: float) -> float:
        """
        Calcola take profit
        
        Args:
            entry_price: Prezzo entrata
        
        Returns:
            Prezzo take profit
        """
        config = self.get_current_config()
        take_profit_price = entry_price * (1 + config.take_profit)
        
        self.logger.debug(f"Take profit: {config.take_profit:.2%} @ ${take_profit_price:.4f}")
        
        return take_profit_price
    
    def should_trade(self, confidence: float, market_conditions: Dict, expected_profit: float = 0.08) -> Tuple[bool, str]:
        """
        Determina se eseguire trade
        
        Args:
            confidence: Confidence AI
            market_conditions: Condizioni mercato
        
        Returns:
            (should_trade, reason)
        """
        config = self.get_current_config()
        
        # Check 1: Confidence threshold
        if confidence < config.confidence_threshold:
            return False, f"Confidence {confidence:.1%} < threshold {config.confidence_threshold:.1%}"
        
        # Check 1.5: Profit/Fee ratio (NEW: High-Profit Filter)
        fee_percentage = 0.001  # 0.10%
        profit_fee_ratio = (expected_profit / fee_percentage) * confidence
        min_ratio = 50.0  # Min 50x fee
        
        if profit_fee_ratio < min_ratio:
            return False, f"Profit/fee ratio {profit_fee_ratio:.1f} < {min_ratio}"
        
        # Check 1.6: Minimum profit target
        min_profit = config.take_profit * 0.625  # 62.5% of take profit
        if expected_profit < min_profit:
            return False, f"Expected profit {expected_profit:.1%} < min {min_profit:.1%}"
        
        # Check 2: Daily loss limit
        if self.daily_pnl < -self.current_capital * 0.08:
            return False, f"Daily loss limit raggiunto: ${self.daily_pnl:.2f}"
        
        # Check 3: Consecutive losses
        if self.consecutive_losses >= 5:
            return False, f"Troppe perdite consecutive: {self.consecutive_losses}"
        
        # Check 4: Capital drawdown
        drawdown = (self.initial_capital - self.current_capital) / self.initial_capital
        if drawdown > 0.30:
            return False, f"Drawdown eccessivo: {drawdown:.1%}"
        
        # Check 5: Volume (se disponibile)
        if 'volume_ratio' in market_conditions:
            if market_conditions['volume_ratio'] < 1.0:
                return False, f"Volume troppo basso: {market_conditions['volume_ratio']:.2f}x"
        
        return True, "All checks passed"
    
    def record_trade(self, trade_result: Dict):
        """
        Registra risultato trade e aggiorna statistiche
        
        Args:
            trade_result: Dict con info trade
        """
        self.trades_history.append(trade_result)
        self.total_trades += 1
        self.daily_trades += 1
        
        pnl = trade_result.get('pnl', 0)
        self.current_capital += pnl
        self.daily_pnl += pnl
        
        # Aggiorna win/loss
        if pnl > 0:
            self.winning_trades += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            self.max_consecutive_wins = max(self.max_consecutive_wins, self.consecutive_wins)
            result_emoji = "✅"
        else:
            self.losing_trades += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            self.max_consecutive_losses = max(self.max_consecutive_losses, self.consecutive_losses)
            result_emoji = "❌"
        
        # Log trade
        self.logger.info(f"{result_emoji} Trade #{self.total_trades}: "
                        f"P&L ${pnl:+.2f} | Capitale: ${self.current_capital:.2f} | "
                        f"Win streak: {self.consecutive_wins} | Loss streak: {self.consecutive_losses}")
        
        # Check level adjustment
        self._check_level_adjustment()
        
        # Reset daily stats se nuovo giorno
        self._check_daily_reset()
    
    def _check_level_adjustment(self):
        """Verifica se cambiare livello"""
        # Calcola metriche recenti
        recent_trades = self.trades_history[-20:] if len(self.trades_history) >= 20 else self.trades_history
        
        if len(recent_trades) < 10:
            return  # Troppo pochi trade per valutare
        
        recent_wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
        win_rate = recent_wins / len(recent_trades)
        
        # Calcola crescita capitale ultimi 7 giorni
        seven_days_ago = datetime.now() - timedelta(days=7)
        trades_7d = [t for t in self.trades_history if datetime.fromisoformat(t.get('timestamp', '2000-01-01')) > seven_days_ago]
        
        if trades_7d:
            capital_7d_ago = self.current_capital - sum(t.get('pnl', 0) for t in trades_7d)
            growth_7d = (self.current_capital - capital_7d_ago) / capital_7d_ago if capital_7d_ago > 0 else 0
        else:
            growth_7d = 0
        
        # Trigger UPGRADE
        if (win_rate > 0.70 and 
            growth_7d > 0.15 and 
            self.consecutive_wins >= 5 and
            self.current_level.value < ChameleonLevel.ROCKET.value):
            
            new_level = ChameleonLevel(self.current_level.value + 1)
            self._upgrade_level(new_level, win_rate, growth_7d)
        
        # Trigger DOWNGRADE
        elif (win_rate < 0.55 or 
              self.consecutive_losses >= 3 or
              self.daily_pnl < -self.current_capital * 0.05):
            
            if self.current_level.value > ChameleonLevel.TURTLE.value:
                new_level = ChameleonLevel(self.current_level.value - 1)
                self._downgrade_level(new_level, win_rate)
    
    def _upgrade_level(self, new_level: ChameleonLevel, win_rate: float, growth: float):
        """Upgrade a livello superiore"""
        old_config = self.get_current_config()
        self.current_level = new_level
        new_config = self.get_current_config()
        
        self.level_history.append((datetime.now(), new_level))
        
        self.logger.warning(f"⬆️  LEVEL UP! {old_config.description} → {new_config.description}")
        self.logger.warning(f"   Win Rate: {win_rate:.1%} | Growth 7d: {growth:+.1%}")
        self.logger.warning(f"   New Position Size: {new_config.position_size_min:.1%}-{new_config.position_size_max:.1%}")
    
    def _downgrade_level(self, new_level: ChameleonLevel, win_rate: float):
        """Downgrade a livello inferiore"""
        old_config = self.get_current_config()
        self.current_level = new_level
        new_config = self.get_current_config()
        
        self.level_history.append((datetime.now(), new_level))
        
        self.logger.warning(f"⬇️  LEVEL DOWN! {old_config.description} → {new_config.description}")
        self.logger.warning(f"   Win Rate: {win_rate:.1%} | Consecutive Losses: {self.consecutive_losses}")
        self.logger.warning(f"   New Position Size: {new_config.position_size_min:.1%}-{new_config.position_size_max:.1%}")
    
    def _check_daily_reset(self):
        """Reset statistiche giornaliere"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.logger.info(f"📊 Daily Summary: Trades: {self.daily_trades} | P&L: ${self.daily_pnl:+.2f}")
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = today
    
    def get_statistics(self) -> Dict:
        """Ottieni statistiche complete"""
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        total_profit = sum(t.get('pnl', 0) for t in self.trades_history if t.get('pnl', 0) > 0)
        total_loss = abs(sum(t.get('pnl', 0) for t in self.trades_history if t.get('pnl', 0) < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        roi = (self.current_capital - self.initial_capital) / self.initial_capital if self.initial_capital > 0 else 0
        
        return {
            'current_capital': self.current_capital,
            'initial_capital': self.initial_capital,
            'total_pnl': self.current_capital - self.initial_capital,
            'roi_percentage': roi * 100,
            'current_level': self.get_current_config().description,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate * 100,
            'profit_factor': profit_factor,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
            'max_consecutive_wins': self.max_consecutive_wins,
            'max_consecutive_losses': self.max_consecutive_losses,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'level_changes': len(self.level_history) - 1
        }
    
    def get_trading_pairs(self) -> List[str]:
        """Ottieni coppie trading per livello corrente"""
        config = self.get_current_config()
        
        # Pool completo coppie (ordinato per liquidità/stabilità)
        all_pairs = [
            'BTC/USDT', 'ETH/USDT', 'USDC/USDT',  # Core stablecoin
            'SOL/USDT', 'BNB/USDT', 'XRP/USDT',    # Large cap
            'ADA/USDT', 'AVAX/USDT', 'DOT/USDT',   # Mid cap
            'MATIC/USDT', 'LINK/USDT', 'UNI/USDT', # DeFi
            'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT'  # Meme (alta volatilità)
        ]
        
        # Ritorna numero coppie basato su livello
        return all_pairs[:config.pairs_count]
    
    def save_state(self, filepath: str):
        """Salva stato strategia"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'current_level': self.current_level.name,
            'statistics': self.get_statistics(),
            'trades_history': self.trades_history[-100:],  # Ultimi 100 trade
            'level_history': [(ts.isoformat(), level.name) for ts, level in self.level_history]
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.logger.info(f"💾 Stato salvato: {filepath}")
    
    @classmethod
    def load_state(cls, filepath: str) -> 'ChameleonStrategy':
        """Carica stato strategia"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Ricrea istanza
        initial_level = ChameleonLevel[state['current_level']]
        strategy = cls(state['initial_capital'], initial_level)
        
        # Ripristina stato
        strategy.current_capital = state['current_capital']
        strategy.trades_history = state['trades_history']
        
        # Ripristina statistiche
        stats = state['statistics']
        strategy.total_trades = stats['total_trades']
        strategy.winning_trades = stats['winning_trades']
        strategy.losing_trades = stats['losing_trades']
        strategy.consecutive_wins = stats['consecutive_wins']
        strategy.consecutive_losses = stats['consecutive_losses']
        strategy.max_consecutive_wins = stats['max_consecutive_wins']
        strategy.max_consecutive_losses = stats['max_consecutive_losses']
        strategy.daily_pnl = stats['daily_pnl']
        strategy.daily_trades = stats['daily_trades']
        
        return strategy


# Test rapido
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=" * 80)
    print("TEST CHAMELEON STRATEGY")
    print("=" * 80)
    print()
    
    # Crea strategia
    strategy = ChameleonStrategy(initial_capital=50.0)
    
    # Simula alcuni trade
    print("Simulazione trade...")
    print()
    
    # 5 trade vincenti
    for i in range(5):
        position_size = strategy.calculate_position_size(confidence=0.75, trend_strength=1.1)
        profit = position_size * 0.03  # 3% profit
        strategy.record_trade({
            'timestamp': datetime.now().isoformat(),
            'pair': 'BTC/USDT',
            'side': 'buy',
            'pnl': profit
        })
        time.sleep(0.1)
    
    # 2 trade perdenti
    for i in range(2):
        position_size = strategy.calculate_position_size(confidence=0.65, trend_strength=0.9)
        loss = -position_size * 0.015  # -1.5% loss
        strategy.record_trade({
            'timestamp': datetime.now().isoformat(),
            'pair': 'ETH/USDT',
            'side': 'sell',
            'pnl': loss
        })
        time.sleep(0.1)
    
    # Statistiche finali
    print()
    print("=" * 80)
    print("STATISTICHE FINALI")
    print("=" * 80)
    stats = strategy.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    
    print()
    print(f"Trading Pairs ({len(strategy.get_trading_pairs())}): {', '.join(strategy.get_trading_pairs())}")
    print()
    print("=" * 80)
    print("✅ Test completato!")
    print("=" * 80)
