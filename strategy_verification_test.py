#!/usr/bin/env python3
"""
Test di verifica logica strategia BTC
Analizza la strategia attualmente implementata e verifica la correttezza della logica
"""

import os
import sys
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Aggiungi path del progetto
sys.path.append('/home/ubuntu/AurumBotX')

from utils.ai_trading import AITrading
from utils.data_loader import CryptoDataLoader
from utils.strategies.swing_trading import SwingTradingStrategy
from utils.strategies.scalping import ScalpingStrategy

class StrategyVerificationTest:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('StrategyVerification')
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def print_header(self, title):
        """Header professionale"""
        print(f"\n{'='*80}")
        print(f"🔍 {title}")
        print(f"{'='*80}")
        
    def print_section(self, title):
        """Sezione"""
        print(f"\n📋 {title}")
        print(f"{'-'*70}")
    
    async def test_current_strategy_logic(self):
        """Testa la logica della strategia attualmente implementata"""
        self.print_header("VERIFICA LOGICA STRATEGIA BTC ATTUALE")
        
        try:
            # 1. Inizializza componenti
            self.logger.info("🔧 Inizializzazione componenti...")
            
            data_loader = CryptoDataLoader(use_live_data=True, testnet=True)
            await data_loader.initialize()
            
            ai_trading = AITrading()
            await ai_trading.initialize()
            
            # 2. Configurazione strategia attuale (dal monitor)
            strategy_config = {
                'profit_target': 0.05,  # 5%
                'stop_loss': 0.03,      # 3%
                'trend_period': 20,
                'min_trend_strength': 0.6
            }
            
            swing_strategy = SwingTradingStrategy(strategy_config)
            
            self.print_section("CONFIGURAZIONE STRATEGIA ATTUALE")
            print(f"  📊 Tipo: Swing Trading")
            print(f"  🎯 Profit Target: {strategy_config['profit_target']:.1%}")
            print(f"  🛡️ Stop Loss: {strategy_config['stop_loss']:.1%}")
            print(f"  📈 Trend Period: {strategy_config['trend_period']} periodi")
            print(f"  💪 Min Trend Strength: {strategy_config['min_trend_strength']:.1%}")
            
            # 3. Ottieni dati di mercato recenti
            self.logger.info("📊 Recupero dati mercato BTC...")
            market_data = await data_loader.get_historical_data('BTCUSDT', '7d', '1h')
            
            if market_data is None or market_data.empty:
                self.logger.error("❌ Impossibile ottenere dati di mercato")
                return
            
            self.print_section("DATI MERCATO BTC")
            print(f"  📅 Periodo: Ultimi 7 giorni")
            print(f"  ⏰ Timeframe: 1 ora")
            print(f"  📊 Candele: {len(market_data)}")
            print(f"  💰 Prezzo attuale: ${market_data['Close'].iloc[-1]:,.2f}")
            print(f"  📈 Prezzo max 7d: ${market_data['High'].max():,.2f}")
            print(f"  📉 Prezzo min 7d: ${market_data['Low'].min():,.2f}")
            print(f"  📊 Volatilità 7d: {market_data['Close'].pct_change().std() * 100:.2f}%")
            
            # 4. Analisi tecnica dettagliata
            self.logger.info("🔍 Analisi tecnica dettagliata...")
            
            # Calcola indicatori
            market_data['SMA_20'] = market_data['Close'].rolling(window=20).mean()
            market_data['SMA_50'] = market_data['Close'].rolling(window=50).mean()
            market_data['RSI'] = self.calculate_rsi(market_data['Close'])
            market_data['MACD'], market_data['MACD_Signal'] = self.calculate_macd(market_data['Close'])
            
            # Ultimi valori
            latest = market_data.iloc[-1]
            
            self.print_section("ANALISI TECNICA ATTUALE")
            print(f"  💰 Prezzo: ${latest['Close']:,.2f}")
            print(f"  📊 SMA 20: ${latest['SMA_20']:,.2f}")
            print(f"  📈 SMA 50: ${latest['SMA_50']:,.2f}")
            print(f"  🎯 RSI: {latest['RSI']:.2f}")
            print(f"  📊 MACD: {latest['MACD']:.4f}")
            print(f"  📈 MACD Signal: {latest['MACD_Signal']:.4f}")
            
            # Trend analysis
            trend_direction = "BULLISH" if latest['SMA_20'] > latest['SMA_50'] else "BEARISH"
            trend_strength = abs(latest['SMA_20'] - latest['SMA_50']) / latest['Close']
            
            print(f"  🔄 Trend: {trend_direction}")
            print(f"  💪 Trend Strength: {trend_strength:.3f} ({trend_strength:.1%})")
            
            # 5. Test logica strategia
            self.logger.info("🧠 Test logica strategia...")
            
            # Simula analisi mercato
            market_analysis_data = {
                'market_data': {
                    'price': latest['Close'],
                    'rsi': latest['RSI'],
                    'sma_20': latest['SMA_20'],
                    'sma_50': latest['SMA_50'],
                    'macd': latest['MACD'],
                    'volume': latest['Volume']
                },
                'sentiment': {'sentiment': 'neutral'}
            }
            
            # Test strategia swing trading
            signals = await swing_strategy.analyze_market(market_data, market_analysis_data.get('sentiment'))
            
            self.print_section("RISULTATI STRATEGIA SWING TRADING")
            if signals:
                for i, signal in enumerate(signals, 1):
                    print(f"  🎯 Segnale {i}:")
                    print(f"    📊 Azione: {signal['action'].upper()}")
                    print(f"    🎯 Confidenza: {signal['confidence']:.1%}")
                    print(f"    💰 Prezzo: ${signal['price']:,.2f}")
                    print(f"    📝 Motivo: {signal.get('reason', 'N/A')}")
            else:
                print("  ⚪ Nessun segnale generato")
            
            # 6. Test AI Trading completo
            self.logger.info("🤖 Test AI Trading completo...")
            
            ai_signals = await ai_trading.generate_trading_signals('BTCUSDT')
            
            self.print_section("RISULTATI AI TRADING COMPLETO")
            if ai_signals:
                for i, signal in enumerate(ai_signals, 1):
                    print(f"  🤖 AI Segnale {i}:")
                    print(f"    📊 Azione: {signal['action'].upper()}")
                    print(f"    🎯 Confidenza: {signal['confidence']:.1%}")
                    print(f"    💰 Prezzo: ${signal.get('price', 'N/A')}")
                    print(f"    🧠 Modello: {signal.get('model', 'N/A')}")
            else:
                print("  ⚪ Nessun segnale AI generato")
            
            # 7. Valutazione logica
            self.print_section("VALUTAZIONE LOGICA STRATEGIA")
            
            # Controlli logici
            logic_checks = []
            
            # Check 1: Coerenza trend
            if trend_direction == "BULLISH" and latest['RSI'] < 70:
                logic_checks.append("✅ Trend bullish con RSI non ipercomprato")
            elif trend_direction == "BEARISH" and latest['RSI'] > 30:
                logic_checks.append("✅ Trend bearish con RSI non ipervenduto")
            else:
                logic_checks.append("⚠️ Possibile divergenza trend-RSI")
            
            # Check 2: Forza trend vs soglia
            if trend_strength >= strategy_config['min_trend_strength']:
                logic_checks.append(f"✅ Trend sufficientemente forte ({trend_strength:.1%} >= {strategy_config['min_trend_strength']:.1%})")
            else:
                logic_checks.append(f"⚠️ Trend debole ({trend_strength:.1%} < {strategy_config['min_trend_strength']:.1%})")
            
            # Check 3: Risk/Reward ratio
            risk_reward = strategy_config['profit_target'] / strategy_config['stop_loss']
            if risk_reward >= 1.5:
                logic_checks.append(f"✅ Risk/Reward favorevole ({risk_reward:.1f}:1)")
            else:
                logic_checks.append(f"⚠️ Risk/Reward basso ({risk_reward:.1f}:1)")
            
            # Check 4: Timeframe appropriato
            if strategy_config['trend_period'] >= 14:
                logic_checks.append(f"✅ Periodo trend appropriato ({strategy_config['trend_period']} >= 14)")
            else:
                logic_checks.append(f"⚠️ Periodo trend troppo breve ({strategy_config['trend_period']} < 14)")
            
            for check in logic_checks:
                print(f"  {check}")
            
            # 8. Raccomandazioni
            self.print_section("RACCOMANDAZIONI")
            
            recommendations = []
            
            if trend_strength < strategy_config['min_trend_strength']:
                recommendations.append("🔧 Considerare riduzione min_trend_strength o attendere trend più forte")
            
            if latest['RSI'] > 70:
                recommendations.append("⚠️ RSI ipercomprato - cautela per segnali BUY")
            elif latest['RSI'] < 30:
                recommendations.append("⚠️ RSI ipervenduto - cautela per segnali SELL")
            
            if risk_reward < 1.5:
                recommendations.append("💰 Considerare aumento profit_target o riduzione stop_loss")
            
            if not signals and not ai_signals:
                recommendations.append("📊 Nessun segnale - mercato laterale o condizioni non ottimali")
            
            if not recommendations:
                recommendations.append("✅ Strategia ben configurata per condizioni attuali")
            
            for rec in recommendations:
                print(f"  {rec}")
            
            return {
                'strategy_config': strategy_config,
                'market_analysis': market_analysis_data,
                'swing_signals': signals,
                'ai_signals': ai_signals,
                'logic_checks': logic_checks,
                'recommendations': recommendations
            }
            
        except Exception as e:
            self.logger.error(f"❌ Errore test strategia: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def calculate_rsi(self, prices, period=14):
        """Calcola RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcola MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return macd, macd_signal

async def main():
    """Main del test verifica strategia"""
    tester = StrategyVerificationTest()
    await tester.test_current_strategy_logic()

if __name__ == "__main__":
    asyncio.run(main())

