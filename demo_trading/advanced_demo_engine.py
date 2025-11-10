#!/usr/bin/env python3
"""
AurumBotX Advanced Demo Trading Engine
Motore di trading demo avanzato con AI aggressiva e generazione di trade reali
Capital: 1000 USD
Genera trade reali basati su dati di mercato Binance
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
import random

# Configurazione
INITIAL_CAPITAL = 1000.0
DEMO_CONFIG = {
    "capital": INITIAL_CAPITAL,
    "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"],
    "timeframe": "1h",
    "max_positions": 5,
    "position_size": 0.12,  # 12% per posizione
    "stop_loss": 0.06,  # 6% stop loss
    "take_profit": 0.20,  # 20% take profit
    "min_confidence": 0.50,  # 50% confidence threshold (più basso = più trade)
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
            return []

class AdvancedAIAnalyzer:
    """AI avanzata per analisi di mercato e generazione di segnali"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calcola RSI"""
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
    def calculate_macd(prices: List[float]) -> Tuple[float, float, float]:
        """Calcola MACD"""
        if len(prices) < 26:
            return 0.0, 0.0, 0.0
        
        ema_12 = np.mean(prices[-12:])
        ema_26 = np.mean(prices[-26:])
        macd = ema_12 - ema_26
        signal = np.mean([ema_12, ema_26])
        histogram = macd - signal
        
        return macd, signal, histogram
    
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
    
    @staticmethod
    def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Calcola ATR (Average True Range)"""
        if len(highs) < period:
            return 0.0
        
        tr_list = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_list.append(tr)
        
        atr = np.mean(tr_list[-period:])
        return atr
    
    @staticmethod
    def analyze_market_advanced(symbol: str, klines: List[Dict]) -> Dict:
        """Analisi avanzata del mercato con AI"""
        if not klines or len(klines) < 26:
            return {"signal": "HOLD", "confidence": 0.0, "reason": "Dati insufficienti"}
        
        closes = [k["close"] for k in klines]
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]
        volumes = [k["volume"] for k in klines]
        
        # Calcola indicatori
        rsi = AdvancedAIAnalyzer.calculate_rsi(closes)
        macd, signal, histogram = AdvancedAIAnalyzer.calculate_macd(closes)
        upper, sma, lower = AdvancedAIAnalyzer.calculate_bollinger_bands(closes)
        atr = AdvancedAIAnalyzer.calculate_atr(highs, lows, closes)
        
        # Analisi di volume
        avg_volume = np.mean(volumes[-10:])
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Trend
        price_change_5 = (closes[-1] - closes[-5]) / closes[-5] * 100
        price_change_10 = (closes[-1] - closes[-10]) / closes[-10] * 100
        
        # Volatilità
        volatility = np.std(np.diff(closes)) / np.mean(closes) * 100
        
        # Momentum
        momentum = closes[-1] - closes[-5]
        
        # Logica decisionale AI avanzata
        signal = "HOLD"
        confidence = 0.0
        reason = ""
        
        # Contatore di segnali
        buy_signals = 0
        sell_signals = 0
        
        # RSI Signals
        if rsi < 30:
            buy_signals += 2
        elif rsi < 40:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 2
        elif rsi > 60:
            sell_signals += 1
        
        # MACD Signals
        if macd > signal and histogram > 0:
            buy_signals += 1
        elif macd < signal and histogram < 0:
            sell_signals += 1
        
        # Bollinger Bands Signals
        if closes[-1] < lower:
            buy_signals += 1
        elif closes[-1] > upper:
            sell_signals += 1
        
        # Volume Signals
        if volume_ratio > 1.5:
            if price_change_5 > 0:
                buy_signals += 1
            else:
                sell_signals += 1
        
        # Trend Signals
        if price_change_10 > 2:
            buy_signals += 1
        elif price_change_10 < -2:
            sell_signals += 1
        
        # Momentum Signals
        if momentum > 0 and rsi < 50:
            buy_signals += 1
        elif momentum < 0 and rsi > 50:
            sell_signals += 1
        
        # Determina segnale finale
        total_signals = buy_signals + sell_signals
        
        if buy_signals > sell_signals and buy_signals > 0:
            signal = "BUY"
            confidence = min(0.95, buy_signals / max(total_signals, 1) * 0.95)
            reason = f"AI Signals: {buy_signals} BUY vs {sell_signals} SELL | RSI: {rsi:.1f}, MACD: {'bullish' if macd > signal else 'bearish'}, Trend: {price_change_10:+.2f}%"
        
        elif sell_signals > buy_signals and sell_signals > 0:
            signal = "SELL"
            confidence = min(0.95, sell_signals / max(total_signals, 1) * 0.95)
            reason = f"AI Signals: {sell_signals} SELL vs {buy_signals} BUY | RSI: {rsi:.1f}, MACD: {'bearish' if macd < signal else 'bullish'}, Trend: {price_change_10:+.2f}%"
        
        else:
            confidence = 0.3
            reason = f"Mercato neutrale - RSI: {rsi:.1f}, Volatilità: {volatility:.2f}%, Trend: {price_change_10:+.2f}%"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "rsi": rsi,
            "macd": macd,
            "price": closes[-1],
            "volume_ratio": volume_ratio,
            "volatility": volatility,
            "trend": price_change_10,
            "atr": atr
        }

class AdvancedDemoTradingEngine:
    """Motore di trading demo avanzato"""
    
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
        self.ai_analyzer = AdvancedAIAnalyzer()
        
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
            
            # Analisi AI avanzata
            analysis = self.ai_analyzer.analyze_market_advanced(symbol, klines)
            
            # Gestisci posizioni aperte
            if symbol in self.open_positions:
                trade = self.open_positions[symbol]
                self._check_exit_conditions(trade, current_price, analysis)
            
            # Genera nuovi segnali di trading
            if analysis["signal"] == "BUY" and analysis["confidence"] > DEMO_CONFIG["min_confidence"]:
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
            "trade_id": trade.id,
            "status": "success"
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
            "duration_hours": (datetime.fromisoformat(trade.exit_time) - datetime.fromisoformat(trade.entry_time)).total_seconds() / 3600,
            "status": "success"
        }
    
    def _check_exit_conditions(self, trade: Trade, current_price: float, analysis: Dict):
        """Controlla le condizioni di uscita"""
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
                "sharpe_ratio": 0.0,
                "profit_factor": 0.0
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
        
        # Sharpe Ratio
        pnl_values = [t.pnl for t in self.closed_trades]
        if len(pnl_values) > 1:
            std_dev = np.std(pnl_values)
            sharpe_ratio = (np.mean(pnl_values) / std_dev) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0.0
        
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
            "total_pnl_percent": total_pnl_percent,
            "avg_pnl": avg_pnl,
            "max_drawdown_percent": max_drawdown_percent,
            "sharpe_ratio": sharpe_ratio,
            "profit_factor": profit_factor
        }
    
    def save_state(self, filename: str = "advanced_demo_state.json"):
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
    print("=" * 100)
    print("AurumBotX Advanced Demo Trading Engine - AI Adattiva")
    print("=" * 100)
    print(f"\nCapitale Iniziale: ${INITIAL_CAPITAL}")
    print(f"Simboli: {', '.join(DEMO_CONFIG['symbols'])}")
    print(f"Position Size: {DEMO_CONFIG['position_size']*100}%")
    print(f"Stop Loss: {DEMO_CONFIG['stop_loss']*100}%")
    print(f"Take Profit: {DEMO_CONFIG['take_profit']*100}%")
    print(f"Min Confidence: {DEMO_CONFIG['min_confidence']*100}%")
    print("\n" + "=" * 100)
    print("Avvio del motore di trading demo avanzato...")
    print("Fetch dati reali da Binance e generazione di trade...")
    print("=" * 100 + "\n")
    
    engine = AdvancedDemoTradingEngine(INITIAL_CAPITAL)
    
    # Esegui 10 cicli di trading
    for cycle in range(10):
        print(f"\n[CICLO {cycle + 1}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 100)
        
        results = engine.execute_trading_cycle()
        
        portfolio_value = results['portfolio_value']
        pnl = portfolio_value - INITIAL_CAPITAL
        pnl_percent = (pnl / INITIAL_CAPITAL) * 100
        
        print(f"Portafoglio: ${portfolio_value:.2f} | P&L: ${pnl:+.2f} ({pnl_percent:+.2f}%)")
        print(f"Posizioni Aperte: {results['open_positions']} | Trade Totali Chiusi: {results['total_trades']}")
        
        if results['actions']:
            for action in results['actions']:
                if action.get('status') == 'success':
                    if action.get('type') == 'BUY':
                        print(f"  ✓ BUY {action['symbol']} @ ${action['price']:.2f} | Qty: {action['quantity']:.4f} | Confidence: {action['confidence']*100:.1f}%")
                    elif action.get('type') == 'SELL':
                        print(f"  ✓ SELL {action['symbol']} @ ${action['price']:.2f} | P&L: ${action['pnl']:+.2f} ({action['pnl_percent']:+.2f}%) | Reason: {action.get('reason', 'N/A')}")
        else:
            print("  → Nessuna azione")
        
        time.sleep(0.5)
    
    # Salva lo stato finale
    print("\n" + "=" * 100)
    print("REPORT FINALE - PERFORMANCE METRICS")
    print("=" * 100)
    
    state = engine.save_state("/home/ubuntu/AurumBotX/demo_trading/advanced_demo_state.json")
    
    metrics = engine.get_performance_metrics()
    print(f"\nCapitale Finale: ${state['portfolio_value']:.2f}")
    print(f"Profitto/Perdita: ${metrics['total_pnl']:+.2f} ({metrics['total_pnl_percent']:+.2f}%)")
    print(f"\nTrade Totali: {metrics['total_trades']}")
    print(f"Trade Vincenti: {metrics['winning_trades']} ({metrics['win_rate']:.1f}%)")
    print(f"Trade Perdenti: {metrics['losing_trades']}")
    print(f"Profitto Medio: ${metrics['avg_pnl']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown_percent']:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}x")
    
    print("\n" + "=" * 100)
    print("Demo avanzata completata! Stato salvato in advanced_demo_state.json")
    print("=" * 100)

