#!/usr/bin/env python3
"""
AurumBotX Demo Trading Engine
Motore di trading demo con dati reali di Binance
Capital: 1000 USD
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import requests
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

# Configurazione
INITIAL_CAPITAL = 1000.0
DEMO_CONFIG = {
    "capital": INITIAL_CAPITAL,
    "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"],
    "timeframe": "1h",
    "max_positions": 3,
    "position_size": 0.15,  # 15% per posizione
    "stop_loss": 0.08,  # 8% stop loss
    "take_profit": 0.25,  # 25% take profit
}

class TradeStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"

@dataclass
class Trade:
    id: str
    symbol: str
    entry_price: float
    entry_time: str
    quantity: float
    status: str
    pnl: float = 0.0
    pnl_percent: float = 0.0
    exit_price: float = 0.0
    exit_time: str = ""
    reason: str = ""

class BinanceDataFetcher:
    """Fetcher per dati reali da Binance"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    @staticmethod
    def get_current_price(symbol: str) -> float:
        """Ottiene il prezzo corrente da Binance"""
        try:
            url = f"{BinanceDataFetcher.BASE_URL}/ticker/price"
            params = {"symbol": symbol}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return float(response.json()["price"])
            return None
        except Exception as e:
            print(f"Errore nel fetch del prezzo {symbol}: {e}")
            return None
    
    @staticmethod
    def get_klines(symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict]:
        """Ottiene i dati OHLCV da Binance"""
        try:
            url = f"{BinanceDataFetcher.BASE_URL}/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                klines = response.json()
                return [
                    {
                        "time": datetime.fromtimestamp(k[0] / 1000),
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[7])
                    }
                    for k in klines
                ]
            return []
        except Exception as e:
            print(f"Errore nel fetch dei klines {symbol}: {e}")
            return []

class TechnicalAnalysis:
    """Analisi tecnica per generare segnali di trading"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calcola RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 0
        rsi = 100.0 - 100.0 / (1.0 + rs)
        return rsi
    
    @staticmethod
    def calculate_macd(prices: List[float]) -> Tuple[float, float]:
        """Calcola MACD (Moving Average Convergence Divergence)"""
        if len(prices) < 26:
            return 0.0, 0.0
        
        ema_12 = np.mean(prices[-12:])
        ema_26 = np.mean(prices[-26:])
        macd = ema_12 - ema_26
        signal = np.mean([ema_12, ema_26])
        
        return macd, signal
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20) -> Tuple[float, float, float]:
        """Calcola Bollinger Bands"""
        if len(prices) < period:
            return prices[-1], prices[-1], prices[-1]
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        
        return upper, sma, lower

class AIStrategyAdapter:
    """AI per adattare la strategia in base ai dati di mercato"""
    
    @staticmethod
    def analyze_market(symbol: str, klines: List[Dict]) -> Dict:
        """Analizza il mercato e genera segnale di trading"""
        if not klines or len(klines) < 26:
            return {"signal": "HOLD", "confidence": 0.0, "reason": "Dati insufficienti"}
        
        closes = [k["close"] for k in klines]
        volumes = [k["volume"] for k in klines]
        
        # Calcola indicatori
        rsi = TechnicalAnalysis.calculate_rsi(closes)
        macd, signal = TechnicalAnalysis.calculate_macd(closes)
        upper, sma, lower = TechnicalAnalysis.calculate_bollinger_bands(closes)
        
        # Analisi di volume
        avg_volume = np.mean(volumes[-10:])
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Trend
        price_change = (closes[-1] - closes[-5]) / closes[-5] * 100
        
        # Logica decisionale
        signal = "HOLD"
        confidence = 0.0
        reason = ""
        
        # Segnale BUY
        if rsi < 30 and closes[-1] < lower and volume_ratio > 1.2:
            signal = "BUY"
            confidence = min(0.85, (30 - rsi) / 30 * 0.85)
            reason = f"RSI oversold ({rsi:.2f}), prezzo sotto Bollinger, volume alto"
        elif rsi < 35 and macd > signal and price_change > 0:
            signal = "BUY"
            confidence = 0.70
            reason = f"MACD bullish, RSI in recovery, trend positivo (+{price_change:.2f}%)"
        
        # Segnale SELL
        elif rsi > 70 and closes[-1] > upper and volume_ratio > 1.5:
            signal = "SELL"
            confidence = min(0.85, (rsi - 70) / 30 * 0.85)
            reason = f"RSI overbought ({rsi:.2f}), prezzo sopra Bollinger, volume alto"
        elif rsi > 65 and macd < signal and price_change < -1:
            signal = "SELL"
            confidence = 0.70
            reason = f"MACD bearish, RSI in calo, trend negativo ({price_change:.2f}%)"
        
        else:
            confidence = 0.5
            reason = f"Mercato neutrale - RSI: {rsi:.2f}, Trend: {price_change:+.2f}%"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "rsi": rsi,
            "macd": macd,
            "price": closes[-1],
            "volume_ratio": volume_ratio
        }

class DemoTradingEngine:
    """Motore di trading demo"""
    
    def __init__(self, capital: float = INITIAL_CAPITAL):
        self.capital = capital
        self.available_balance = capital
        self.trades: List[Trade] = []
        self.open_positions: Dict[str, Trade] = {}
        self.closed_trades: List[Trade] = []
        self.trade_history: List[Dict] = []
        self.start_time = datetime.now()
        self.trade_counter = 0
        self.fetcher = BinanceDataFetcher()
        self.ai_adapter = AIStrategyAdapter()
        
    def execute_trading_cycle(self) -> Dict:
        """Esegue un ciclo di trading completo"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "actions": [],
            "portfolio_value": self.calculate_portfolio_value(),
            "open_positions": len(self.open_positions),
            "total_trades": len(self.closed_trades)
        }
        
        # Analizza ogni simbolo
        for symbol in DEMO_CONFIG["symbols"]:
            # Fetch dati reali
            klines = self.fetcher.get_klines(symbol, limit=50)
            if not klines:
                continue
            
            current_price = klines[-1]["close"]
            
            # Analisi AI
            analysis = self.ai_adapter.analyze_market(symbol, klines)
            
            # Gestisci posizioni aperte
            if symbol in self.open_positions:
                trade = self.open_positions[symbol]
                self._check_exit_conditions(trade, current_price, analysis)
            
            # Genera nuovi segnali di trading
            if analysis["signal"] == "BUY" and analysis["confidence"] > 0.65:
                if symbol not in self.open_positions and len(self.open_positions) < DEMO_CONFIG["max_positions"]:
                    action = self._execute_buy(symbol, current_price, analysis)
                    results["actions"].append(action)
            
            elif analysis["signal"] == "SELL" and symbol in self.open_positions:
                action = self._execute_sell(symbol, current_price, analysis)
                results["actions"].append(action)
        
        return results
    
    def _execute_buy(self, symbol: str, price: float, analysis: Dict) -> Dict:
        """Esegue un ordine di acquisto"""
        position_value = self.available_balance * DEMO_CONFIG["position_size"]
        quantity = position_value / price
        
        # Simula fee Binance (0.1%)
        fee = position_value * 0.001
        total_cost = position_value + fee
        
        if total_cost > self.available_balance:
            return {"status": "failed", "reason": "Saldo insufficiente"}
        
        self.trade_counter += 1
        trade = Trade(
            id=f"TRADE_{self.trade_counter}",
            symbol=symbol,
            entry_price=price,
            entry_time=datetime.now().isoformat(),
            quantity=quantity,
            status=TradeStatus.OPEN.value
        )
        
        self.open_positions[symbol] = trade
        self.available_balance -= total_cost
        
        return {
            "type": "BUY",
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
            "cost": total_cost,
            "confidence": analysis["confidence"],
            "reason": analysis["reason"],
            "trade_id": trade.id
        }
    
    def _execute_sell(self, symbol: str, price: float, analysis: Dict) -> Dict:
        """Esegue un ordine di vendita"""
        if symbol not in self.open_positions:
            return {"status": "failed", "reason": "Nessuna posizione aperta"}
        
        trade = self.open_positions[symbol]
        revenue = trade.quantity * price
        fee = revenue * 0.001
        net_revenue = revenue - fee
        
        pnl = net_revenue - (trade.entry_price * trade.quantity)
        pnl_percent = (pnl / (trade.entry_price * trade.quantity)) * 100
        
        trade.status = TradeStatus.CLOSED.value
        trade.exit_price = price
        trade.exit_time = datetime.now().isoformat()
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        trade.reason = analysis["reason"]
        
        self.closed_trades.append(trade)
        del self.open_positions[symbol]
        self.available_balance += net_revenue
        
        return {
            "type": "SELL",
            "symbol": symbol,
            "price": price,
            "quantity": trade.quantity,
            "revenue": net_revenue,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "trade_id": trade.id,
            "duration": (datetime.fromisoformat(trade.exit_time) - datetime.fromisoformat(trade.entry_time)).total_seconds() / 3600
        }
    
    def _check_exit_conditions(self, trade: Trade, current_price: float, analysis: Dict):
        """Controlla le condizioni di uscita (stop loss, take profit)"""
        entry_value = trade.entry_price * trade.quantity
        current_value = current_price * trade.quantity
        pnl_percent = ((current_value - entry_value) / entry_value) * 100
        
        # Stop Loss
        if pnl_percent <= -DEMO_CONFIG["stop_loss"] * 100:
            self._execute_sell(trade.symbol, current_price, {"reason": "Stop Loss", "confidence": 1.0})
        
        # Take Profit
        elif pnl_percent >= DEMO_CONFIG["take_profit"] * 100:
            self._execute_sell(trade.symbol, current_price, {"reason": "Take Profit", "confidence": 1.0})
    
    def calculate_portfolio_value(self) -> float:
        """Calcola il valore totale del portafoglio"""
        open_positions_value = 0.0
        
        for symbol, trade in self.open_positions.items():
            price = self.fetcher.get_current_price(symbol)
            if price:
                open_positions_value += trade.quantity * price
        
        return self.available_balance + open_positions_value
    
    def get_performance_metrics(self) -> Dict:
        """Calcola le metriche di performance"""
        if not self.closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "total_pnl_percent": 0.0,
                "avg_pnl": 0.0,
                "max_drawdown_percent": 0.0,
                "sharpe_ratio": 0.0
            }
        
        total_trades = len(self.closed_trades)
        winning_trades = len([t for t in self.closed_trades if t.pnl > 0])
        losing_trades = total_trades - winning_trades
        
        total_pnl = sum(t.pnl for t in self.closed_trades)
        total_pnl_percent = (total_pnl / self.capital) * 100
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        # Max Drawdown
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        for trade in self.closed_trades:
            cumulative_pnl += trade.pnl
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_percent = (max_drawdown / self.capital) * 100 if self.capital > 0 else 0
        
        # Sharpe Ratio (semplificato)
        pnl_values = [t.pnl for t in self.closed_trades]
        if len(pnl_values) > 1:
            std_dev = np.std(pnl_values)
            sharpe_ratio = (np.mean(pnl_values) / std_dev) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0.0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "avg_pnl": avg_pnl,
            "max_drawdown_percent": max_drawdown_percent,
            "sharpe_ratio": sharpe_ratio
        }
    
    def save_state(self, filename: str = "demo_state.json"):
        """Salva lo stato della demo"""
        state = {
            "capital": self.capital,
            "available_balance": self.available_balance,
            "portfolio_value": self.calculate_portfolio_value(),
            "open_positions": [asdict(t) for t in self.open_positions.values()],
            "closed_trades": [asdict(t) for t in self.closed_trades],
            "performance": self.get_performance_metrics(),
            "start_time": self.start_time.isoformat(),
            "last_update": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        return state

if __name__ == "__main__":
    print("=" * 80)
    print("AurumBotX Demo Trading Engine")
    print("=" * 80)
    print(f"\nCapitale Iniziale: ${INITIAL_CAPITAL}")
    print(f"Simboli: {', '.join(DEMO_CONFIG['symbols'])}")
    print(f"Position Size: {DEMO_CONFIG['position_size']*100}%")
    print(f"Stop Loss: {DEMO_CONFIG['stop_loss']*100}%")
    print(f"Take Profit: {DEMO_CONFIG['take_profit']*100}%")
    print("\n" + "=" * 80)
    print("Avvio del motore di trading demo...")
    print("=" * 80 + "\n")
    
    engine = DemoTradingEngine(INITIAL_CAPITAL)
    
    # Esegui 5 cicli di trading
    for cycle in range(5):
        print(f"\n[CICLO {cycle + 1}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
        
        results = engine.execute_trading_cycle()
        
        print(f"Portafoglio: ${results['portfolio_value']:.2f}")
        print(f"Posizioni Aperte: {results['open_positions']}")
        print(f"Trade Totali: {results['total_trades']}")
        
        if results['actions']:
            for action in results['actions']:
                if action.get('type') == 'BUY':
                    print(f"  ✓ BUY {action['symbol']} @ ${action['price']:.2f} ({action['confidence']*100:.1f}% confidence)")
                elif action.get('type') == 'SELL':
                    print(f"  ✓ SELL {action['symbol']} @ ${action['price']:.2f} | PnL: ${action['pnl']:.2f} ({action['pnl_percent']:+.2f}%)")
        else:
            print("  → Nessuna azione")
        
        time.sleep(1)
    
    # Salva lo stato finale
    print("\n" + "=" * 80)
    print("REPORT FINALE")
    print("=" * 80)
    
    state = engine.save_state("/home/ubuntu/AurumBotX/demo_trading/demo_state.json")
    
    metrics = engine.get_performance_metrics()
    print(f"\nCapitale Finale: ${state['portfolio_value']:.2f}")
    print(f"Profitto/Perdita: ${metrics['total_pnl']:.2f} ({metrics['total_pnl_percent']:+.2f}%)")
    print(f"\nTrade Totali: {metrics['total_trades']}")
    print(f"Trade Vincenti: {metrics['winning_trades']} ({metrics['win_rate']:.1f}%)")
    print(f"Trade Perdenti: {metrics['losing_trades']}")
    print(f"Profitto Medio: ${metrics['avg_pnl']:.2f}")
    print(f"Max Drawdown: {metrics.get('max_drawdown_percent', 0):.2f}%")
    print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    
    print("\n" + "=" * 80)
    print("Demo completata! Stato salvato in demo_state.json")
    print("=" * 80)

